"""
Standalone script for:
- Extracting facts and applicables rules from a PDF of contract disputes
- Create a Chroma database to store the extracted facts and rules
"""

import os
import json
import glob
from typing import TypedDict

import pandas as pd
import pymupdf4llm
import psycopg
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm

import extraction_prompts as extraction_prompts

# Global configuration
BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "../data")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../extraction_chroma_db")
COLLECTION_NAME = "contract_disputes_chunks"

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
    why_was_the_fact_relevant: str
    why_was_the_fact_not_relevant: str


class CitedProceduralRule(TypedDict):
    procedural_rule_cited: str
    effect_on_courts_decision_or_case_handling: str


class CitedSubstantiveRule(TypedDict):
    principle_of_substantive_law: str
    facts_making_principle_applicable: str
    how_principle_and_facts_were_crucial_to_the_decision: str


class ExtractedFactsAndRules(TypedDict):
    facts: list[CitedFact]
    procedural_rules: list[CitedProceduralRule]
    substantive_rules: list[CitedSubstantiveRule]


model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
output_parser = JsonOutputParser()


def facts_extraction(md_text: str) -> list[CitedFact]:
    """Extracts facts from a document containing a contract dispute case"""
    facts_extraction_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", extraction_prompts.FACTS_EXTRACTION_PROMPT),
            ("user", "{user_input}"),
        ]
    )
    facts_extraction_chain = facts_extraction_prompt | model | output_parser
    facts_extraction_input_params = {"user_input": md_text}
    facts_extraction_response = facts_extraction_chain.invoke(
        facts_extraction_input_params
    )
    return facts_extraction_response


def procedural_rules_extraction(md_text: str) -> list[CitedProceduralRule]:
    """Extracts the procedural rules from a document containing a contract dispute case"""
    procedural_rules_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                extraction_prompts.PROCEDURAL_RULES_EXTRACTION_PROMPT,
            ),
            ("user", "{user_input}"),
        ]
    )
    procedural_rules_extraction_chain = procedural_rules_prompt | model | output_parser
    procedural_rules_extraction_input_params = {"user_input": md_text}
    procedural_rules_extraction_response = procedural_rules_extraction_chain.invoke(
        procedural_rules_extraction_input_params
    )
    return procedural_rules_extraction_response


def sustantive_rules_extraction(md_text: str) -> list[CitedSubstantiveRule]:
    """Extracts substantive rules from a document containing a contract dispute case."""
    substantive_rules_extraction_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", extraction_prompts.SUBSTANTIVE_RULES_EXTRACTION_PROMPT),
            ("user", "{user_input}"),
        ]
    )
    substantive_rules_extraction_chain = (
        substantive_rules_extraction_prompt | model | output_parser
    )
    substantive_rules_exctraction_input_params = {"user_input": md_text}
    substantive_rules_exctraction_response = substantive_rules_extraction_chain.invoke(
        substantive_rules_exctraction_input_params
    )
    return substantive_rules_exctraction_response


def extract_facts_and_rules(doc_path: str) -> ExtractedFactsAndRules:
    """
    Extracts fact patterns, procedural rules, and substantive legal rules from a PDF
    containing a contract dispute decision/order and returns the extracted content.
    """
    # Parse PDF to Markdown
    md_text = pymupdf4llm.to_markdown(doc_path)

    # Extract facts and rules
    facts_extraction_response: list[CitedFact] = facts_extraction(md_text)

    procedural_rules_extraction_response: list[CitedProceduralRule] = (
        procedural_rules_extraction(md_text)
    )
    substantive_rules_extraction_response: list[CitedSubstantiveRule] = (
        sustantive_rules_extraction(md_text)
    )
    facts_and_rules: ExtractedFactsAndRules = {
        "facts": facts_extraction_response,
        "procedural_rules": procedural_rules_extraction_response,
        "substantive_rules": substantive_rules_extraction_response,
    }

    return facts_and_rules


def save_extraction_as_json(results: dict, doc_path: str, output_path: str) -> None:
    json_path = f"{output_path}/{os.path.splitext(os.path.basename(doc_path))[0]}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)


def save_extraction_as_excel(facts_and_rules, doc_path: str, output_path: str) -> None:
    excel_path = f"{output_path}/{os.path.splitext(os.path.basename(doc_path))[0]}.xlsx"

    facts_df = pd.DataFrame(
        {
            "id": list(range(len(facts_and_rules["facts"]))),
            "Fact": facts_and_rules["facts"],
        }
    )
    procedural_df = pd.DataFrame(facts_and_rules["procedural_rules"])
    substantive_rules_df = pd.DataFrame(facts_and_rules["substantive_rules"])

    with pd.ExcelWriter(excel_path) as writer:
        facts_df.to_excel(writer, sheet_name="Fact Pattern", index=False)
        procedural_df.to_excel(writer, sheet_name="Procedural Rules", index=False)
        substantive_rules_df.to_excel(
            writer, sheet_name="Substantive Rules", index=False
        )


def create_or_load_vector_store() -> Chroma:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in the environment.")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=api_key)

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
    )


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


def main():
    vector_store = create_or_load_vector_store()

    # Define year range to process
    start_year = 2025
    end_year = 2025
    years = [str(year) for year in range(start_year, end_year + 1)]

    for year in years:
        year_folder = os.path.join(BASE_DATA_PATH, year)
        pdf_files = glob.glob(os.path.join(year_folder, "*.pdf"))
        for doc_path in tqdm(pdf_files, desc=f"Processing PDFs for {year}"):
            try:
                doc_name = os.path.splitext(os.path.basename(doc_path))[0]
                extracted = extract_facts_and_rules(doc_path)
                chunks = prepare_chunks(doc_name, extracted)
                vector_store.add_documents(chunks)
                vector_store.persist()
            except Exception as e:
                print(f"Error processing {doc_path}: {e}")


if __name__ == "__main__":
    main()
