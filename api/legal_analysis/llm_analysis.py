import os
import asyncio
import pymupdf4llm
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from api.legal_analysis import prompts as extraction_prompts
from api.legal_analysis.pydantic_schemas import (
    FactsExtractionOutput,
    ProceduralRulesOutput,
    SubstantiveRulesOutput,
    FactsAndRulesOutput,
    AdmissibilityScoringOutput,
    AdmissibilityScoringInput,
    RelevanceScoringOutput,
    RelevanceScoringInput,
    RuleScoreSummary,
    CombinedScoreSummary,
)


is_running_in_spaces: bool = "SPACE_ID" in os.environ
if not is_running_in_spaces:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ModuleNotFoundError:
        print("Warning: python-dotenv not installed. Skipping local .env loading.")


model = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), temperature=0)


async def legal_reasoning_qa(md_text: str) -> str:
    """Answer a set of questions Judges and courts answer to write their
    opinions or decisions"""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", extraction_prompts.LEGAL_REASONING_QUESTIONS_AND_ANSWERS_PROMPT),
            ("user", "{user_input}"),
        ]
    )
    chain = prompt | model | StrOutputParser()
    qa_text = await chain.ainvoke({"user_input": md_text})
    return qa_text


async def facts_extraction(md_text: str, qa_text: str) -> FactsExtractionOutput:
    """Extract factual assertions from document + legal Q&A."""
    prompt = ChatPromptTemplate.from_messages(
        [("system", extraction_prompts.FACTS_EXTRACTION_PROMPT)]
    )
    output_parser = PydanticOutputParser(pydantic_object=FactsExtractionOutput)
    chain = prompt | model | output_parser
    return await chain.ainvoke({"text": md_text, "qa": qa_text})


async def procedural_rules_extraction(
    md_text: str, qa_text: str
) -> ProceduralRulesOutput:
    """
    Extract any procedural rules, requirements, or practices that are cited, implied, 
    or suggested by the parties or the contracting officer — especially those that might 
    later be relevant if the case were appealed.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", extraction_prompts.PROCEDURAL_RULES_EXTRACTION_PROMPT),
        ]
    )
    output_parser = PydanticOutputParser(pydantic_object=ProceduralRulesOutput)
    chain = prompt | model | output_parser
    return await chain.ainvoke({"text": md_text, "qa": qa_text})


async def filter_procedural_rules(
    extracted_rules: ProceduralRulesOutput,
) -> ProceduralRulesOutput:
    """Filters out substantive rules, keeping only procedural ones."""
    prompt = ChatPromptTemplate.from_messages(
        [("system", extraction_prompts.FILTER_PROCEDURAL_RULES_PROMPT)]
    )
    output_parser = PydanticOutputParser(pydantic_object=ProceduralRulesOutput)
    chain = prompt | model | output_parser
    return await chain.ainvoke(extracted_rules)


async def substantive_rules_extraction(
    md_text: str, qa_text: str
) -> SubstantiveRulesOutput:
    """
    Extract all references to **substantive rules of law or contract principles** that 
    are cited, implied, or suggested by the claimant or contracting officer — especially 
    those that might become relevant if the dispute were reviewed by a court or board.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", extraction_prompts.SUBSTANTIVE_RULES_EXTRACTION_PROMPT),
        ]
    )
    output_parser = PydanticOutputParser(pydantic_object=SubstantiveRulesOutput)
    chain = prompt | model | output_parser
    return await chain.ainvoke({"text": md_text, "qa": qa_text})


async def extract_facts_and_rules(md_text: str) -> FactsAndRulesOutput:
    """
    Extracts:
    - Factual assertions from document + legal Q&A.
    - Procedural rules.
    - References to substantive rules of law or contract principles.

    """
    qa_text = await legal_reasoning_qa(md_text)
    facts_task = asyncio.create_task(facts_extraction(md_text, qa_text))
    procedural_task = asyncio.create_task(procedural_rules_extraction(md_text, qa_text))
    substantive_task = asyncio.create_task(
        substantive_rules_extraction(md_text, qa_text)
    )
    facts, procedural, substantive = await asyncio.gather(
        facts_task, procedural_task, substantive_task
    )
    return FactsAndRulesOutput(
        facts=facts,
        procedural_rules=procedural,
        substantive_rules=substantive,
    )


async def admissibility_scoring(
    data: AdmissibilityScoringInput,
) -> AdmissibilityScoringOutput:
    """Scores admissibility of procedural rules based on facts and Q&A legal context."""
    prompt = ChatPromptTemplate.from_messages(
        [("system", extraction_prompts.ADMISSIBILITY_SCORING_PROMPT)]
    )
    output_parser = PydanticOutputParser(pydantic_object=AdmissibilityScoringOutput)
    chain = prompt | model | output_parser
    return await chain.ainvoke(
        {
            "facts": data.facts.facts,
            "procedural_rules": data.procedural_rules.rules,
            "qa": data.qa,
        }
    )


async def admissibility_scoring_results(md_text: str) -> AdmissibilityScoringOutput:
    """Scores admissibility of procedural rules from a legal document"""
    qa_text = await legal_reasoning_qa(md_text)
    facts = await facts_extraction(md_text, qa_text)
    procedural = await procedural_rules_extraction(md_text, qa_text)
    scoring_input = AdmissibilityScoringInput(
        facts=facts, procedural_rules=procedural, qa=qa_text
    )
    return await admissibility_scoring(scoring_input)


async def relevance_scoring(data: RelevanceScoringInput) -> RelevanceScoringOutput:
    """Scores relevance of substantive rules based on facts and Q&A legal context."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", extraction_prompts.RELEVANCE_SCORING_PROMPT),
        ]
    )
    output_parser = PydanticOutputParser(pydantic_object=RelevanceScoringOutput)
    chain = prompt | model | output_parser
    return await chain.ainvoke(
        {
            "facts": data.facts.facts,
            "substantive_rules": data.substantive_rules.rules,
            "qa": data.qa,
        }
    )


async def relevance_scoring_results(md_text: str) -> RelevanceScoringOutput:
    """Scores relevance of procedural rules from a legal document."""
    qa_text = await legal_reasoning_qa(md_text)
    facts = await facts_extraction(md_text, qa_text)
    substantive = await substantive_rules_extraction(md_text, qa_text)
    scoring_input = RelevanceScoringInput(
        facts=facts, substantive_rules=substantive, qa=qa_text
    )
    return await relevance_scoring(scoring_input)


async def pdf_to_markdown(doc_path: str) -> str:
    return await asyncio.to_thread(pymupdf4llm.to_markdown, doc_path)


async def process_admissibility_scores(
    data: AdmissibilityScoringOutput,
) -> list[RuleScoreSummary]:
    """Processes procedural rule scores into summarized rule scores."""
    return [
        RuleScoreSummary(
            rule=item.procedural_rule,
            rule_score=(
                item.doctrinal_fit
                + item.fact_match
                + item.party_assertion
                + item.precedent_alignment
            )
            / 20,
            rationale=item.rationale,
        )
        for item in data.scores
    ]


async def process_relevance_scores(
    data: RelevanceScoringOutput,
) -> list[RuleScoreSummary]:
    """Processes substantive rule scores into summarized rule scores."""
    return [
        RuleScoreSummary(
            rule=item.substantive_law,
            rule_score=(
                item.doctrinal_fit
                + item.fact_match
                + item.party_assertion
                + item.precedent_alignment
            )
            / 20,
            rationale=item.rationale,
        )
        for item in data.scores
    ]


async def summarize_all_scores(
    admissibility_data: AdmissibilityScoringOutput,
    relevance_data: RelevanceScoringOutput,
) -> CombinedScoreSummary:
    """Summarizes all rule scores and calculates the overall scores."""
    procedural = await process_admissibility_scores(admissibility_data)
    substantive = await process_relevance_scores(relevance_data)
    total_admissible_score = sum(rule.rule_score for rule in procedural) / len(
        procedural
    )
    total_relevance_score = sum(rule.rule_score for rule in substantive) / len(
        substantive
    )
    return CombinedScoreSummary(
        admissible_rules_summary=procedural,
        relevance_rules_summary=substantive,
        total_admissibility_score=round(total_admissible_score, 3),
        total_relevance_score=round(total_relevance_score, 3),
    )


async def scoring_results(md_text: str) -> CombinedScoreSummary:
    """Scores rules based on on a legal document."""
    qa_text = await legal_reasoning_qa(md_text)
    facts = await facts_extraction(md_text, qa_text)
    procedural = await procedural_rules_extraction(md_text, qa_text)
    substantive = await substantive_rules_extraction(md_text, qa_text)

    admissibility_scoring_input = AdmissibilityScoringInput(
        facts=facts, procedural_rules=procedural, qa=qa_text
    )
    admissibility_data = await admissibility_scoring(admissibility_scoring_input)

    relevance_scoring_input = RelevanceScoringInput(
        facts=facts, substantive_rules=substantive, qa=qa_text
    )
    relevance_data = await relevance_scoring(relevance_scoring_input)

    return await summarize_all_scores(admissibility_data, relevance_data)
