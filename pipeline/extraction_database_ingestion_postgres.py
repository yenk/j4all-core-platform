"""
Standalone script for:
- Extracting facts and applicables rules from a PDF of contract disputes
- Create a PostgreSQL database to store the extracted facts and rules
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


def connect_to_db() -> None:
    return psycopg.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
    )


def initialize_schema() -> None:
    with connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    id SERIAL PRIMARY KEY,
                    doc_name TEXT,
                    fact_id_per_doc INTEGER,
                    specific_fact_cited TEXT,
                    why_was_the_fact_relevant TEXT,
                    why_was_the_fact_not_relevant TEXT
                );
                
                CREATE TABLE IF NOT EXISTS procedural_rules (
                    id SERIAL PRIMARY KEY,
                    doc_name TEXT,
                    procedural_rule_cited TEXT,
                    effect_on_courts_decision_or_case_handling TEXT
                );

                CREATE TABLE IF NOT EXISTS substantive_rules (
                    id SERIAL PRIMARY KEY,
                    doc_name TEXT,
                    principle_of_substantive_law TEXT,
                    facts_making_principle_applicable TEXT,
                    how_principle_and_facts_were_crucial_to_the_decision TEXT
                );
            """
            )
            conn.commit()


def insert_to_database(
    doc_name: str,
    facts: list[CitedFact],
    procedural_rules: list[CitedProceduralRule],
    substantive_rules: list[CitedSubstantiveRule],
) -> None:
    with connect_to_db() as conn:
        with conn.cursor() as cur:
            # Clear any existing records for this document
            cur.execute("DELETE FROM facts WHERE doc_name = %s", (doc_name,))
            cur.execute("DELETE FROM procedural_rules WHERE doc_name = %s", (doc_name,))
            cur.execute("DELETE FROM substantive_rules WHERE doc_name = %s", (doc_name,))
            
            # Insert facts
            for fact in facts:
                cur.execute(
                    """
                    INSERT INTO facts (
                        doc_name, fact_id_per_doc, specific_fact_cited,
                        why_was_the_fact_relevant, why_was_the_fact_not_relevant
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        doc_name,
                        fact["id"],
                        fact["specific_fact_cited"],
                        fact["why_was_the_fact_relevant"],
                        fact["why_was_the_fact_not_relevant"],
                    ),
                )

            # Insert procedural rules
            for rule in procedural_rules:
                cur.execute(
                    """
                    INSERT INTO procedural_rules (
                        doc_name, procedural_rule_cited,
                        effect_on_courts_decision_or_case_handling
                    ) VALUES (%s, %s, %s)
                    """,
                    (
                        doc_name,
                        rule["procedural_rule_cited"],
                        rule["effect_on_courts_decision_or_case_handling"],
                    ),
                )

            # Insert substantive rules
            for rule in substantive_rules:
                cur.execute(
                    """
                    INSERT INTO substantive_rules (
                        doc_name, principle_of_substantive_law,
                        facts_making_principle_applicable,
                        how_principle_and_facts_were_crucial_to_the_decision
                    ) VALUES (%s, %s, %s, %s)
                    """,
                    (
                        doc_name,
                        rule["principle_of_substantive_law"],
                        rule["facts_making_principle_applicable"],
                        rule["how_principle_and_facts_were_crucial_to_the_decision"],
                    ),
                )

        conn.commit()


def main():
    # Add the base directory where the PDFs are stored
    base_dir = os.path.join(os.path.dirname(__file__), "../data")

    # Initialize the schema
    initialize_schema()
    
    # Select which years will be uploaded/updated
    start_year, end_year = 2025, 2025
    years = [str(year) for year in range(start_year, end_year + 1)]

    for year in years:
        input_pdf_folder = f"{base_dir}/{year}"
        pdf_files_list = glob.glob(os.path.join(input_pdf_folder, "*.pdf"))

        for doc_path in tqdm(pdf_files_list, desc="Processing PDFs"):
            try:
                doc_name = os.path.splitext(os.path.basename(doc_path))[0]
                facts_and_rules = extract_facts_and_rules(doc_path)
                insert_to_database(
                    doc_name=doc_name,
                    facts=facts_and_rules["facts"],
                    procedural_rules=facts_and_rules["procedural_rules"],
                    substantive_rules=facts_and_rules["substantive_rules"],
                )
            except Exception as e:
                print(f"Error processing {doc_path}: {e}")


if __name__ == "__main__":
    main()
