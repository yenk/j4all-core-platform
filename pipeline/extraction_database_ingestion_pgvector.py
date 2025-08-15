"""
Standalone script for:
- Extracting facts and applicable rules from contract dispute PDFs
- Storing them as vector-embedded chunks in a PostgreSQL + pgvector database
"""

import os
import json
import glob
from typing import TypedDict
from dotenv import load_dotenv

import pymupdf4llm
import psycopg
from pgvector.psycopg import register_vector
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.documents import Document
from langchain_community.embeddings import OpenAIEmbeddings
from tqdm import tqdm

import extraction_prompts as extraction_prompts

is_running_in_spaces: bool = "SPACE_ID" in os.environ
if not is_running_in_spaces:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ModuleNotFoundError:
        print("Warning: python-dotenv not installed. Skipping local .env loading.")


class CitedFact(TypedDict):
    id: int
    specific_fact_cited: str
    relevance_reason: str
    contestability_reason: str


class CitedProceduralRule(TypedDict):
    procedural_rule: str
    effects: str


class CitedSubstantiveRule(TypedDict):
    substantive_law: str
    applicability: str
    relevance: str


class ExtractedFactsAndRules(TypedDict):
    facts: list[CitedFact]
    procedural_rules: list[CitedProceduralRule]
    substantive_rules: list[CitedSubstantiveRule]


model = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), temperature=0)


def legal_reasoning_qa(md_text: str) -> str:
    """Answer a set of questions Judges and courts answer to write their
    opinions or decisions"""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", extraction_prompts.LEGAL_REASONING_QUESTIONS_AND_ANSWERS_PROMPT),
            ("user", "{user_input}"),
        ]
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"user_input": md_text})


def facts_extraction(md_text: str, qa_text: str) -> list[CitedFact]:
    """Extracts facts from a document containing a contract dispute case"""
    prompt = ChatPromptTemplate.from_messages(
        [("system", extraction_prompts.FACTS_EXTRACTION_PROMPT)]
    )
    chain = prompt | model | JsonOutputParser()
    return chain.invoke({"text": md_text, "qa": qa_text})


def procedural_rules_extraction(md_text: str, qa_text: str) -> list[CitedProceduralRule]:
    """Extracts the procedural rules from a document containing a contract dispute case"""
    prompt = ChatPromptTemplate.from_messages(
        [("system", extraction_prompts.PROCEDURAL_RULES_EXTRACTION_PROMPT)]
    )
    chain = prompt | model | JsonOutputParser()
    return chain.invoke({"text": md_text, "qa": qa_text})


def filter_procedural_rules(rules: list[CitedProceduralRule]) -> list[CitedProceduralRule]:
    """Filter out substantive rules from a list of procedural rules"""
    prompt = ChatPromptTemplate.from_messages(
        [("system", extraction_prompts.FILTER_PROCEDURAL_RULES_PROMPT)]
    )
    chain = prompt | model | JsonOutputParser()
    return chain.invoke({"rules": rules})


def substantive_rules_extraction(md_text: str, qa_text: str) -> list[CitedSubstantiveRule]:
    """Extracts substantive rules from a document containing a contract dispute case."""
    prompt = ChatPromptTemplate.from_messages(
        [("system", extraction_prompts.SUBSTANTIVE_RULES_EXTRACTION_PROMPT)]
    )
    chain = prompt | model | JsonOutputParser()
    return chain.invoke({"text": md_text, "qa": qa_text})


def extract_facts_and_rules(doc_path: str) -> ExtractedFactsAndRules:
    """
    Extracts fact patterns, procedural rules, and substantive legal rules from a PDF
    containing a contract dispute decision/order and returns the extracted content.
    """
    md_text = pymupdf4llm.to_markdown(doc_path)
    qa_text = legal_reasoning_qa(md_text)
    procedural_rules = procedural_rules_extraction(md_text, qa_text)
    filtered_procedural_rules = filter_procedural_rules(procedural_rules)
    return {
        "facts": facts_extraction(md_text, qa_text),
        "procedural_rules": filtered_procedural_rules,
        "substantive_rules": substantive_rules_extraction(md_text, qa_text),
    }


def connect_to_db():
    conn = psycopg.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
    )
    register_vector(conn)
    return conn


def initialize_vector_schema():
    with connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS facts_and_rules (
                    id SERIAL PRIMARY KEY,
                    doc_name TEXT,
                    chunk_type TEXT, -- 'facts', 'procedural_rules', or 'substantive_rules'
                    content TEXT,
                    embedding vector(3072),
                    metadata JSONB
                );
            """
            )
            conn.commit()


def prepare_chunks(doc_name: str, extracted: ExtractedFactsAndRules) -> list[Document]:
    return [
        Document(
            page_content=json.dumps(extracted["facts"], indent=2),
            metadata={"doc_name": doc_name, "type": "facts"},
        ),
        Document(
            page_content=json.dumps(extracted["procedural_rules"], indent=2),
            metadata={"doc_name": doc_name, "type": "procedural_rules"},
        ),
        Document(
            page_content=json.dumps(extracted["substantive_rules"], indent=2),
            metadata={"doc_name": doc_name, "type": "substantive_rules"},
        ),
    ]


def store_chunks(chunks: list[Document], embeddings: OpenAIEmbeddings) -> None:
    with connect_to_db() as conn:
        with conn.cursor() as cur:
            for chunk in chunks:
                content = chunk.page_content
                metadata = chunk.metadata
                embedding = embeddings.embed_query(content)
                cur.execute(
                    """
                    INSERT INTO facts_and_rules (doc_name, chunk_type, content, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        metadata["doc_name"],
                        metadata["type"],
                        content,
                        embedding,
                        json.dumps(metadata),
                    ),
                )
        conn.commit()


def main():
    initialize_vector_schema()
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large", api_key=os.getenv("OPENAI_API_KEY")
    )

    base_dir = os.path.join(os.path.dirname(__file__), "../data")
    start_year, end_year = 2025, 2025
    years = [str(y) for y in range(start_year, end_year + 1)]

    for year in years:
        pdf_dir = os.path.join(base_dir, year)
        pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))

        for doc_path in tqdm(pdf_files, desc=f"Processing PDFs for {year}"):
            try:
                doc_name = os.path.splitext(os.path.basename(doc_path))[0]
                extracted = extract_facts_and_rules(doc_path)
                chunks = prepare_chunks(doc_name, extracted)
                store_chunks(chunks, embeddings)
            except Exception as e:
                print(f"Error processing {doc_path}: {e}")


if __name__ == "__main__":
    main()
