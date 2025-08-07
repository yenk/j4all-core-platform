import logging
from fastapi import APIRouter

from api.core.logging import setup_logging
from api.config import Settings, get_settings
from api.legal_analysis import llm_analysis
from api.legal_analysis.pydantic_schemas import (
    FactsAndRulesOutput,
    FactsExtractionOutput,
    ProceduralRulesOutput,
    SubstantiveRulesOutput,
    AdmissibilityScoringOutput,
    RelevanceScoringOutput,
    CombinedScoreSummary,
)


setup_logging()
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/reasoning_qa", response_model=str)
async def reasoning_qa(md_text: str) -> str:
    """
    Generates structured legal reasoning by answering key pre-appeal questions that a
    court or Board would consider in evaluating the case.

    Parameters:

        md_text (str): Markdown-formatted text describing the contract dispute before any appeal decision.

    Returns:

        str: A structured Q&A answering jurisdiction, procedural posture, legal theories, and relevant legal context.

    Example Input:

        CBCA 7451
        QUALITY TRUST, INC.,
        Appellant,
        v.
        DEPARTMENT OF THE INTERIOR,
        Respondent.

        Lawrence M. Ruiz, President of Quality Trust, Inc., Junction City, KS, appearing for Appellant.
        Rachel Grabenstein, Office of the Solicitor, Department of the Interior, Albuquerque, NM, counsel for Respondent.

        Before Board Judges RUSSELL, SULLIVAN, and CHADWICK.

        SULLIVAN, Board Judge.

        Quality Trust, Inc. (QTI) appealed the decision of a contracting officer for the Department of the Interior (DOI or respondent) denying QTI’s claim for lack of support.

        Statement of Undisputed Facts

        I. Claim to the Contracting Officer

        In September 2020, DOI entered into a contract with QTI for bridge and road repair. Appeal File, Exhibit 7 at 2-4. The period of performance was September 23, 2020, to February 26, 2021. Id. at 4. The contract incorporated Federal Acquisition Regulation (FAR) clause 52.242-14, Suspension of Work (APR 1984) (48 CFR 52.242-14 (2020)). Exhibit 7 at 81. That clause stipulates that a contractor shall receive an economic adjustment for any increase in contract performance costs “necessarily caused by the unreasonable suspension, delay, or interruption” of work by the contracting officer. To ensure that nesting birds were not disturbed, the contract prohibited QTI from performing masonry work on the bridge to be repaired between March 15 and September 1. Exhibit 7 at 75.

        There are two suspensions of work documented in the appeal file. On December 28, 2020, the contracting officer issued a unilateral modification, partially suspending work to address QTI’s mistake in price. Exhibit 33 at 2 (modification 1); see also Exhibits 25, 28 at 2. DOI lifted the suspension on January 21, 2021. Exhibit 42 at 2. On February 4, 2021, the contracting officer issued another suspension and a cure notice, directing QTI to address several failures and deficiencies in its performance. Exhibit 53 (modification 3). After receiving several additional cure notices, QTI made the necessary adjustments, and the contracting officer lifted this second suspension on March 30, 2021. Exhibit 70 at 3 (modification 4). In the modification lifting the second suspension, the contracting officer extended the completion date to September 30, 2021. Id.

        In April 2021, the parties executed a bilateral modification to address “a mutual mistake in the contract price after award,” adding approximately $52,000 to the contract price. Exhibit 76 at 2 (modification 5). On January 4, 2022, the contracting officer issued two unilateral modifications. The first extended the contract completion dated to January 31, 2022. Exhibit 121 at 2 (modification 8). The second partially terminated work for convenience, listing five areas of terminated contract work. Id. at 4-11 (modification 9).

        By letter dated January 10, 2022, QTI submitted a “time and cost modification request,” seeking payment of $2000 per day for the period from March through November 2021, during which QTI alleged it was on standby due to “latent conditions and changes” in a project that was “not classified correctly.” Exhibit 129 at 3.

        In April 2022, QTI submitted a claim to the contracting officer pursuant to the contract’s Disputes clause, FAR 52.233-1, seeking payment of $481,109.75. Exhibit 146 at 3-8. QTI did not explain how it arrived at its claim amount or identify what “[l]ost [a]djustment expenses” remained to be incurred. See id. at 3. QTI certified that the supporting data it provided “are accurate and complete” and that the “amount requested accurately reflects the contract adjustment for which the contractor believes the Government is liable.” Id.

        On May 23, 2022, the contracting officer requested via email that QTI clarify the amount of its claim and provide documentation showing “how [QTI] arrived at the amount claimed and explain to the Government why [QTI is] entitled to the sum amount claimed.” Exhibit 148 at 1. In its email reply the same day, QTI described a series of purported problems on the contract:

        “[T]his contract is royally messed up in many specific areas. Let me reiterate[.] When we had the problems on the bridge, a time and cost modification was sent to you, of which you never responded to over a year ago[.] QTI had taken into account that we must be ready and willing to [mobilize] and [demobilize] two more times[,] [w]hich alone would easily add another $100,000.00[.] Because of all the changes, and a contract that never said, we were working on a Department of Natural Resources (DNR) project was very deceiving from the specifications and drawings. Please note: the project was out ofscope and full of differing site conditions and latent conditions to mention a few. The more I think about this . . . QTI could easily justify the $481,109.75.” Exhibit 150 at 2. QTI also stated that “we estimated $2,000.00 a day based on [this contract] being our only project.” Id. QTI also submitted a new additional payment request for $75,840.25. Exhibit 149 at 3. QTI complained about a “unilateral Partial Termination . . . due to latent and differing site conditions” and that modification 5 “was never honored in good faith in the Amount of $51,921.00 plus interest and penalties.” Id. at 3.

        The following day, the contracting officer and QTI exchanged a series of emails seeking to clarify the basis of QTI’s claim and the payment request for $75,840.25. See Exhibits 151, 152. In its replies, QTI asserted that the nearly $52,000 modification to the contract value (modification 5) formed the basis of its claim but did not explain how. See Exhibit 152. On June 8, 2022, QTI sent the contracting officer three emails, the last of which offered to “justify the $481,109.75.” Exhibit 153 at 4. QTI asserted that it could support its claim with the use of the Eichleay formula. See id. (“For the larger amount[,] QTI will claim under the EIKLAY [sic] Formula.”).

        On June 14, 2022, the contracting officer denied the claim, concluding that QTI had not provided support for its claim. Exhibit 154 at 4.
    """
    return await llm_analysis.legal_reasoning_qa(md_text)


@router.post("/facts_extraction", response_model=FactsExtractionOutput)
async def facts_extraction_endpoint(
    md_text: str, qa_text: str
) -> FactsExtractionOutput:
    """
    Extract factual assertions from a document + legal Q&A contex.

    The following fields are identified which each fact:
    - "id": A zero-based index indicating the order in which the fact appears in the source text (starting from 0)
    - "specific_fact_cited": Exact sentence copied verbatim from the document
    - "relevancy_reason": Why would the fact be relevant; explain how this fact could bear on jurisdiction, procedural posture, responsibility, or any legal issue the court might later address
    - "contestability_reason": Why might the fact be contested; explain why the fact might be challenged, dismissed, or considered immaterial; leave empty if clearly reliable and material

    Parameters:

        md_text (str): Markdown-formatted source document containing factual and procedural history.
        qa_text (str): Structured Q&A providing contextual legal framing.

    Returns:

        FactsExtractionOutput: A list of extracted facts with associated relevance and contestability justifications.

    Example Input:

    md_text:

        CBCA 7451
        QUALITY TRUST, INC.,
        Appellant,
        v.
        DEPARTMENT OF THE INTERIOR,
        Respondent.

        Lawrence M. Ruiz, President of Quality Trust, Inc., Junction City, KS, appearing for Appellant.
        Rachel Grabenstein, Office of the Solicitor, Department of the Interior, Albuquerque, NM, counsel for Respondent.

        Before Board Judges RUSSELL, SULLIVAN, and CHADWICK.

        SULLIVAN, Board Judge.

        Quality Trust, Inc. (QTI) appealed the decision of a contracting officer for the Department of the Interior (DOI or respondent) denying QTI’s claim for lack of support.

        Statement of Undisputed Facts

        I. Claim to the Contracting Officer

        In September 2020, DOI entered into a contract with QTI for bridge and road repair. Appeal File, Exhibit 7 at 2-4. The period of performance was September 23, 2020, to February 26, 2021. Id. at 4. The contract incorporated Federal Acquisition Regulation (FAR) clause 52.242-14, Suspension of Work (APR 1984) (48 CFR 52.242-14 (2020)). Exhibit 7 at 81. That clause stipulates that a contractor shall receive an economic adjustment for any increase in contract performance costs “necessarily caused by the unreasonable suspension, delay, or interruption” of work by the contracting officer. To ensure that nesting birds were not disturbed, the contract prohibited QTI from performing masonry work on the bridge to be repaired between March 15 and September 1. Exhibit 7 at 75.

        There are two suspensions of work documented in the appeal file. On December 28, 2020, the contracting officer issued a unilateral modification, partially suspending work to address QTI’s mistake in price. Exhibit 33 at 2 (modification 1); see also Exhibits 25, 28 at 2. DOI lifted the suspension on January 21, 2021. Exhibit 42 at 2. On February 4, 2021, the contracting officer issued another suspension and a cure notice, directing QTI to address several failures and deficiencies in its performance. Exhibit 53 (modification 3). After receiving several additional cure notices, QTI made the necessary adjustments, and the contracting officer lifted this second suspension on March 30, 2021. Exhibit 70 at 3 (modification 4). In the modification lifting the second suspension, the contracting officer extended the completion date to September 30, 2021. Id.

        In April 2021, the parties executed a bilateral modification to address “a mutual mistake in the contract price after award,” adding approximately $52,000 to the contract price. Exhibit 76 at 2 (modification 5). On January 4, 2022, the contracting officer issued two unilateral modifications. The first extended the contract completion dated to January 31, 2022. Exhibit 121 at 2 (modification 8). The second partially terminated work for convenience, listing five areas of terminated contract work. Id. at 4-11 (modification 9).

        By letter dated January 10, 2022, QTI submitted a “time and cost modification request,” seeking payment of $2000 per day for the period from March through November 2021, during which QTI alleged it was on standby due to “latent conditions and changes” in a project that was “not classified correctly.” Exhibit 129 at 3.

        In April 2022, QTI submitted a claim to the contracting officer pursuant to the contract’s Disputes clause, FAR 52.233-1, seeking payment of $481,109.75. Exhibit 146 at 3-8. QTI did not explain how it arrived at its claim amount or identify what “[l]ost [a]djustment expenses” remained to be incurred. See id. at 3. QTI certified that the supporting data it provided “are accurate and complete” and that the “amount requested accurately reflects the contract adjustment for which the contractor believes the Government is liable.” Id.

        On May 23, 2022, the contracting officer requested via email that QTI clarify the amount of its claim and provide documentation showing “how [QTI] arrived at the amount claimed and explain to the Government why [QTI is] entitled to the sum amount claimed.” Exhibit 148 at 1. In its email reply the same day, QTI described a series of purported problems on the contract:

        “[T]his contract is royally messed up in many specific areas. Let me reiterate[.] When we had the problems on the bridge, a time and cost modification was sent to you, of which you never responded to over a year ago[.] QTI had taken into account that we must be ready and willing to [mobilize] and [demobilize] two more times[,] [w]hich alone would easily add another $100,000.00[.] Because of all the changes, and a contract that never said, we were working on a Department of Natural Resources (DNR) project was very deceiving from the specifications and drawings. Please note: the project was out ofscope and full of differing site conditions and latent conditions to mention a few. The more I think about this . . . QTI could easily justify the $481,109.75.” Exhibit 150 at 2. QTI also stated that “we estimated $2,000.00 a day based on [this contract] being our only project.” Id. QTI also submitted a new additional payment request for $75,840.25. Exhibit 149 at 3. QTI complained about a “unilateral Partial Termination . . . due to latent and differing site conditions” and that modification 5 “was never honored in good faith in the Amount of $51,921.00 plus interest and penalties.” Id. at 3.

        The following day, the contracting officer and QTI exchanged a series of emails seeking to clarify the basis of QTI’s claim and the payment request for $75,840.25. See Exhibits 151, 152. In its replies, QTI asserted that the nearly $52,000 modification to the contract value (modification 5) formed the basis of its claim but did not explain how. See Exhibit 152. On June 8, 2022, QTI sent the contracting officer three emails, the last of which offered to “justify the $481,109.75.” Exhibit 153 at 4. QTI asserted that it could support its claim with the use of the Eichleay formula. See id. (“For the larger amount[,] QTI will claim under the EIKLAY [sic] Formula.”).

        On June 14, 2022, the contracting officer denied the claim, concluding that QTI had not provided support for its claim. Exhibit 154 at 4.

    qa_text:

        1. Does this court have proper jurisdiction of the parties and the subject matter of the case, if so, why?:
        Yes, the court has proper jurisdiction because it involves a contract dispute between Quality Trust, Inc. and the Department of the Interior, which falls under the jurisdiction of the Board of Contract Appeals as per federal contracting laws.

        2. What is the procedural posture of the case? If this is an appeal from a lower court, what was the decision of that court, and which litigant is appealing it?:
        This is an appeal from a decision made by a contracting officer for the Department of the Interior, who denied Quality Trust, Inc.'s claim for lack of support. Quality Trust, Inc. is the appellant.

        3. What is the basis for the appeal? In other words, what does the appellant claim the lower court wrongly decided? For instance, did that court exclude key evidence or misinterpret applicable law?:
        The basis for the appeal is that the contracting officer wrongly denied Quality Trust, Inc.'s claim by concluding that QTI had not provided sufficient support for its claim amount of $481,109.75.

        4. What other procedural grounds exist to dismiss the case or to return it for a revised hearing and decision to the lower court?:
        Procedural grounds that could exist include failure to exhaust administrative remedies, lack of jurisdiction if the claim was not properly submitted, or insufficient evidence to support the claim.

        5. What are the facts introduced in the case? What facts are undisputed and what facts are disputed?:
        Undisputed facts include the existence of a contract between DOI and QTI, the timeline of contract modifications, and the suspensions of work. Disputed facts include the justification for the claim amount of $481,109.75 and whether QTI provided adequate support for its claim.

        6. What claims or causes of action were brought and argued by the litigants?:
        Quality Trust, Inc. brought a claim for payment under the contract's Disputes clause, seeking compensation for alleged costs incurred due to delays and changes in the project.

        7. What is the substantive law that actually applies to the facts of this case?:
        The substantive law that applies includes the Federal Acquisition Regulation (FAR), specifically FAR clause 52.242-14 regarding the suspension of work and the Disputes clause, FAR 52.233-1.

        8. How have prior courts dealt with the procedural and substantive issues?:
        Prior courts have typically required contractors to provide adequate documentation and justification for claims made under contract disputes, emphasizing the need for clear evidence of incurred costs and the basis for claims.

        9. Would there be “urgency” or other reason for this court to issue a temporary injunction or order if the case were to proceed?:
        There may be urgency if Quality Trust, Inc. can demonstrate that delays in resolving the claim could lead to significant financial harm or operational disruptions, warranting a temporary injunction.

        10. What issues of fact or law would this court likely ask the parties to submit briefs (memoranda) on if it were to proceed to decision?:
        The court would likely ask for briefs on the adequacy of the evidence provided by QTI to support its claim, the interpretation of the contract terms regarding suspensions and delays, and the application of the Eichleay formula for calculating damages.

        11. What facts, law, and precedent would the court likely cite if it were to issue a decision based on the current record?:
        The court would likely cite the specific provisions of the FAR relevant to contract modifications and claims, the timeline of events leading to the claim, and precedents regarding the necessity of providing detailed support for claims in contract disputes.

    """
    return await llm_analysis.facts_extraction(md_text, qa_text)


@router.post("/procedural_rules_extraction", response_model=ProceduralRulesOutput)
async def procedural_rules_endpoint(
    md_text: str, qa_text: str
) -> ProceduralRulesOutput:
    """
    Extracts the procedural rules from a document document + legal Q&A.

    The following fields are identified which each rule:
    - "procedural_rule": The specific procedural rule, doctrine, or principle that might shape how the claim is handled before or during appeal (quoted if possible)
    - "effects": Effect on courts decision or case handling; explain how this rule might influence the handling, outcome, or viability of the case if it were later reviewed by a court or board

    Parameters:

        md_text (str): Markdown-formatted document describing the factual and legal history of the dispute.
        qa_text (str): Structured legal reasoning that informs identification of applicable doctrines.

    Returns:

        SubstantiveRulesOutput: A list of substantive legal rules, each with an explanation of applicability and legal relevance.

    Example Input:

    md_text:

        CBCA 7451
        QUALITY TRUST, INC.,
        Appellant,
        v.
        DEPARTMENT OF THE INTERIOR,
        Respondent.

        Lawrence M. Ruiz, President of Quality Trust, Inc., Junction City, KS, appearing for Appellant.
        Rachel Grabenstein, Office of the Solicitor, Department of the Interior, Albuquerque, NM, counsel for Respondent.

        Before Board Judges RUSSELL, SULLIVAN, and CHADWICK.

        SULLIVAN, Board Judge.

        Quality Trust, Inc. (QTI) appealed the decision of a contracting officer for the Department of the Interior (DOI or respondent) denying QTI’s claim for lack of support.

        Statement of Undisputed Facts

        I. Claim to the Contracting Officer

        In September 2020, DOI entered into a contract with QTI for bridge and road repair. Appeal File, Exhibit 7 at 2-4. The period of performance was September 23, 2020, to February 26, 2021. Id. at 4. The contract incorporated Federal Acquisition Regulation (FAR) clause 52.242-14, Suspension of Work (APR 1984) (48 CFR 52.242-14 (2020)). Exhibit 7 at 81. That clause stipulates that a contractor shall receive an economic adjustment for any increase in contract performance costs “necessarily caused by the unreasonable suspension, delay, or interruption” of work by the contracting officer. To ensure that nesting birds were not disturbed, the contract prohibited QTI from performing masonry work on the bridge to be repaired between March 15 and September 1. Exhibit 7 at 75.

        There are two suspensions of work documented in the appeal file. On December 28, 2020, the contracting officer issued a unilateral modification, partially suspending work to address QTI’s mistake in price. Exhibit 33 at 2 (modification 1); see also Exhibits 25, 28 at 2. DOI lifted the suspension on January 21, 2021. Exhibit 42 at 2. On February 4, 2021, the contracting officer issued another suspension and a cure notice, directing QTI to address several failures and deficiencies in its performance. Exhibit 53 (modification 3). After receiving several additional cure notices, QTI made the necessary adjustments, and the contracting officer lifted this second suspension on March 30, 2021. Exhibit 70 at 3 (modification 4). In the modification lifting the second suspension, the contracting officer extended the completion date to September 30, 2021. Id.

        In April 2021, the parties executed a bilateral modification to address “a mutual mistake in the contract price after award,” adding approximately $52,000 to the contract price. Exhibit 76 at 2 (modification 5). On January 4, 2022, the contracting officer issued two unilateral modifications. The first extended the contract completion dated to January 31, 2022. Exhibit 121 at 2 (modification 8). The second partially terminated work for convenience, listing five areas of terminated contract work. Id. at 4-11 (modification 9).

        By letter dated January 10, 2022, QTI submitted a “time and cost modification request,” seeking payment of $2000 per day for the period from March through November 2021, during which QTI alleged it was on standby due to “latent conditions and changes” in a project that was “not classified correctly.” Exhibit 129 at 3.

        In April 2022, QTI submitted a claim to the contracting officer pursuant to the contract’s Disputes clause, FAR 52.233-1, seeking payment of $481,109.75. Exhibit 146 at 3-8. QTI did not explain how it arrived at its claim amount or identify what “[l]ost [a]djustment expenses” remained to be incurred. See id. at 3. QTI certified that the supporting data it provided “are accurate and complete” and that the “amount requested accurately reflects the contract adjustment for which the contractor believes the Government is liable.” Id.

        On May 23, 2022, the contracting officer requested via email that QTI clarify the amount of its claim and provide documentation showing “how [QTI] arrived at the amount claimed and explain to the Government why [QTI is] entitled to the sum amount claimed.” Exhibit 148 at 1. In its email reply the same day, QTI described a series of purported problems on the contract:

        “[T]his contract is royally messed up in many specific areas. Let me reiterate[.] When we had the problems on the bridge, a time and cost modification was sent to you, of which you never responded to over a year ago[.] QTI had taken into account that we must be ready and willing to [mobilize] and [demobilize] two more times[,] [w]hich alone would easily add another $100,000.00[.] Because of all the changes, and a contract that never said, we were working on a Department of Natural Resources (DNR) project was very deceiving from the specifications and drawings. Please note: the project was out ofscope and full of differing site conditions and latent conditions to mention a few. The more I think about this . . . QTI could easily justify the $481,109.75.” Exhibit 150 at 2. QTI also stated that “we estimated $2,000.00 a day based on [this contract] being our only project.” Id. QTI also submitted a new additional payment request for $75,840.25. Exhibit 149 at 3. QTI complained about a “unilateral Partial Termination . . . due to latent and differing site conditions” and that modification 5 “was never honored in good faith in the Amount of $51,921.00 plus interest and penalties.” Id. at 3.

        The following day, the contracting officer and QTI exchanged a series of emails seeking to clarify the basis of QTI’s claim and the payment request for $75,840.25. See Exhibits 151, 152. In its replies, QTI asserted that the nearly $52,000 modification to the contract value (modification 5) formed the basis of its claim but did not explain how. See Exhibit 152. On June 8, 2022, QTI sent the contracting officer three emails, the last of which offered to “justify the $481,109.75.” Exhibit 153 at 4. QTI asserted that it could support its claim with the use of the Eichleay formula. See id. (“For the larger amount[,] QTI will claim under the EIKLAY [sic] Formula.”).

        On June 14, 2022, the contracting officer denied the claim, concluding that QTI had not provided support for its claim. Exhibit 154 at 4.

    qa_text:

        1. Does this court have proper jurisdiction of the parties and the subject matter of the case, if so, why?:
        Yes, the court has proper jurisdiction because it involves a contract dispute between Quality Trust, Inc. and the Department of the Interior, which falls under the jurisdiction of the Board of Contract Appeals as per federal contracting laws.

        2. What is the procedural posture of the case? If this is an appeal from a lower court, what was the decision of that court, and which litigant is appealing it?:
        This is an appeal from a decision made by a contracting officer for the Department of the Interior, who denied Quality Trust, Inc.'s claim for lack of support. Quality Trust, Inc. is the appellant.

        3. What is the basis for the appeal? In other words, what does the appellant claim the lower court wrongly decided? For instance, did that court exclude key evidence or misinterpret applicable law?:
        The basis for the appeal is that the contracting officer wrongly denied Quality Trust, Inc.'s claim by concluding that QTI had not provided sufficient support for its claim amount of $481,109.75.

        4. What other procedural grounds exist to dismiss the case or to return it for a revised hearing and decision to the lower court?:
        Procedural grounds that could exist include failure to exhaust administrative remedies, lack of jurisdiction if the claim was not properly submitted, or insufficient evidence to support the claim.

        5. What are the facts introduced in the case? What facts are undisputed and what facts are disputed?:
        Undisputed facts include the existence of a contract between DOI and QTI, the timeline of contract modifications, and the suspensions of work. Disputed facts include the justification for the claim amount of $481,109.75 and whether QTI provided adequate support for its claim.

        6. What claims or causes of action were brought and argued by the litigants?:
        Quality Trust, Inc. brought a claim for payment under the contract's Disputes clause, seeking compensation for alleged costs incurred due to delays and changes in the project.

        7. What is the substantive law that actually applies to the facts of this case?:
        The substantive law that applies includes the Federal Acquisition Regulation (FAR), specifically FAR clause 52.242-14 regarding the suspension of work and the Disputes clause, FAR 52.233-1.

        8. How have prior courts dealt with the procedural and substantive issues?:
        Prior courts have typically required contractors to provide adequate documentation and justification for claims made under contract disputes, emphasizing the need for clear evidence of incurred costs and the basis for claims.

        9. Would there be “urgency” or other reason for this court to issue a temporary injunction or order if the case were to proceed?:
        There may be urgency if Quality Trust, Inc. can demonstrate that delays in resolving the claim could lead to significant financial harm or operational disruptions, warranting a temporary injunction.

        10. What issues of fact or law would this court likely ask the parties to submit briefs (memoranda) on if it were to proceed to decision?:
        The court would likely ask for briefs on the adequacy of the evidence provided by QTI to support its claim, the interpretation of the contract terms regarding suspensions and delays, and the application of the Eichleay formula for calculating damages.

        11. What facts, law, and precedent would the court likely cite if it were to issue a decision based on the current record?:
        The court would likely cite the specific provisions of the FAR relevant to contract modifications and claims, the timeline of events leading to the claim, and precedents regarding the necessity of providing detailed support for claims in contract disputes.

    """
    return await llm_analysis.procedural_rules_extraction(md_text, qa_text)


@router.post("/substantive_rules_extraction", response_model=SubstantiveRulesOutput)
async def substantive_rules_endpoint(
    md_text: str, qa_text: str
) -> SubstantiveRulesOutput:
    """
    Extracts the substantive rules from a document document + legal Q&A.

    The following fields are identified which each rule:
    - "substantive_law": Principle of substantive law; a concise statement of the rule, clause, or doctrine at issue (e.g., "Suspension of Work clause", "Constructive Suspension Doctrine", "Eichleay Formula")
    - "applicability": Facts making principle applicable; the specific events or allegations in the document that might cause this principle to apply
    - "relevance": How this rule might affect the outcome if later analyzed by a court or Board (How this principle might be crucial to the decision).

    Parameters:

        md_text (str): Full pre-appeal text of the document to analyze.

    Returns:

        FactsAndRulesOutput: A structured bundle containing facts, procedural rules, and substantive rules.

    Example Input:

    md_text:

        CBCA 7451
        QUALITY TRUST, INC.,
        Appellant,
        v.
        DEPARTMENT OF THE INTERIOR,
        Respondent.

        Lawrence M. Ruiz, President of Quality Trust, Inc., Junction City, KS, appearing for Appellant.
        Rachel Grabenstein, Office of the Solicitor, Department of the Interior, Albuquerque, NM, counsel for Respondent.

        Before Board Judges RUSSELL, SULLIVAN, and CHADWICK.

        SULLIVAN, Board Judge.

        Quality Trust, Inc. (QTI) appealed the decision of a contracting officer for the Department of the Interior (DOI or respondent) denying QTI’s claim for lack of support.

        Statement of Undisputed Facts

        I. Claim to the Contracting Officer

        In September 2020, DOI entered into a contract with QTI for bridge and road repair. Appeal File, Exhibit 7 at 2-4. The period of performance was September 23, 2020, to February 26, 2021. Id. at 4. The contract incorporated Federal Acquisition Regulation (FAR) clause 52.242-14, Suspension of Work (APR 1984) (48 CFR 52.242-14 (2020)). Exhibit 7 at 81. That clause stipulates that a contractor shall receive an economic adjustment for any increase in contract performance costs “necessarily caused by the unreasonable suspension, delay, or interruption” of work by the contracting officer. To ensure that nesting birds were not disturbed, the contract prohibited QTI from performing masonry work on the bridge to be repaired between March 15 and September 1. Exhibit 7 at 75.

        There are two suspensions of work documented in the appeal file. On December 28, 2020, the contracting officer issued a unilateral modification, partially suspending work to address QTI’s mistake in price. Exhibit 33 at 2 (modification 1); see also Exhibits 25, 28 at 2. DOI lifted the suspension on January 21, 2021. Exhibit 42 at 2. On February 4, 2021, the contracting officer issued another suspension and a cure notice, directing QTI to address several failures and deficiencies in its performance. Exhibit 53 (modification 3). After receiving several additional cure notices, QTI made the necessary adjustments, and the contracting officer lifted this second suspension on March 30, 2021. Exhibit 70 at 3 (modification 4). In the modification lifting the second suspension, the contracting officer extended the completion date to September 30, 2021. Id.

        In April 2021, the parties executed a bilateral modification to address “a mutual mistake in the contract price after award,” adding approximately $52,000 to the contract price. Exhibit 76 at 2 (modification 5). On January 4, 2022, the contracting officer issued two unilateral modifications. The first extended the contract completion dated to January 31, 2022. Exhibit 121 at 2 (modification 8). The second partially terminated work for convenience, listing five areas of terminated contract work. Id. at 4-11 (modification 9).

        By letter dated January 10, 2022, QTI submitted a “time and cost modification request,” seeking payment of $2000 per day for the period from March through November 2021, during which QTI alleged it was on standby due to “latent conditions and changes” in a project that was “not classified correctly.” Exhibit 129 at 3.

        In April 2022, QTI submitted a claim to the contracting officer pursuant to the contract’s Disputes clause, FAR 52.233-1, seeking payment of $481,109.75. Exhibit 146 at 3-8. QTI did not explain how it arrived at its claim amount or identify what “[l]ost [a]djustment expenses” remained to be incurred. See id. at 3. QTI certified that the supporting data it provided “are accurate and complete” and that the “amount requested accurately reflects the contract adjustment for which the contractor believes the Government is liable.” Id.

        On May 23, 2022, the contracting officer requested via email that QTI clarify the amount of its claim and provide documentation showing “how [QTI] arrived at the amount claimed and explain to the Government why [QTI is] entitled to the sum amount claimed.” Exhibit 148 at 1. In its email reply the same day, QTI described a series of purported problems on the contract:

        “[T]his contract is royally messed up in many specific areas. Let me reiterate[.] When we had the problems on the bridge, a time and cost modification was sent to you, of which you never responded to over a year ago[.] QTI had taken into account that we must be ready and willing to [mobilize] and [demobilize] two more times[,] [w]hich alone would easily add another $100,000.00[.] Because of all the changes, and a contract that never said, we were working on a Department of Natural Resources (DNR) project was very deceiving from the specifications and drawings. Please note: the project was out ofscope and full of differing site conditions and latent conditions to mention a few. The more I think about this . . . QTI could easily justify the $481,109.75.” Exhibit 150 at 2. QTI also stated that “we estimated $2,000.00 a day based on [this contract] being our only project.” Id. QTI also submitted a new additional payment request for $75,840.25. Exhibit 149 at 3. QTI complained about a “unilateral Partial Termination . . . due to latent and differing site conditions” and that modification 5 “was never honored in good faith in the Amount of $51,921.00 plus interest and penalties.” Id. at 3.

        The following day, the contracting officer and QTI exchanged a series of emails seeking to clarify the basis of QTI’s claim and the payment request for $75,840.25. See Exhibits 151, 152. In its replies, QTI asserted that the nearly $52,000 modification to the contract value (modification 5) formed the basis of its claim but did not explain how. See Exhibit 152. On June 8, 2022, QTI sent the contracting officer three emails, the last of which offered to “justify the $481,109.75.” Exhibit 153 at 4. QTI asserted that it could support its claim with the use of the Eichleay formula. See id. (“For the larger amount[,] QTI will claim under the EIKLAY [sic] Formula.”).

        On June 14, 2022, the contracting officer denied the claim, concluding that QTI had not provided support for its claim. Exhibit 154 at 4.

    qa_text:

        1. Does this court have proper jurisdiction of the parties and the subject matter of the case, if so, why?:
        Yes, the court has proper jurisdiction because it involves a contract dispute between Quality Trust, Inc. and the Department of the Interior, which falls under the jurisdiction of the Board of Contract Appeals as per federal contracting laws.

        2. What is the procedural posture of the case? If this is an appeal from a lower court, what was the decision of that court, and which litigant is appealing it?:
        This is an appeal from a decision made by a contracting officer for the Department of the Interior, who denied Quality Trust, Inc.'s claim for lack of support. Quality Trust, Inc. is the appellant.

        3. What is the basis for the appeal? In other words, what does the appellant claim the lower court wrongly decided? For instance, did that court exclude key evidence or misinterpret applicable law?:
        The basis for the appeal is that the contracting officer wrongly denied Quality Trust, Inc.'s claim by concluding that QTI had not provided sufficient support for its claim amount of $481,109.75.

        4. What other procedural grounds exist to dismiss the case or to return it for a revised hearing and decision to the lower court?:
        Procedural grounds that could exist include failure to exhaust administrative remedies, lack of jurisdiction if the claim was not properly submitted, or insufficient evidence to support the claim.

        5. What are the facts introduced in the case? What facts are undisputed and what facts are disputed?:
        Undisputed facts include the existence of a contract between DOI and QTI, the timeline of contract modifications, and the suspensions of work. Disputed facts include the justification for the claim amount of $481,109.75 and whether QTI provided adequate support for its claim.

        6. What claims or causes of action were brought and argued by the litigants?:
        Quality Trust, Inc. brought a claim for payment under the contract's Disputes clause, seeking compensation for alleged costs incurred due to delays and changes in the project.

        7. What is the substantive law that actually applies to the facts of this case?:
        The substantive law that applies includes the Federal Acquisition Regulation (FAR), specifically FAR clause 52.242-14 regarding the suspension of work and the Disputes clause, FAR 52.233-1.

        8. How have prior courts dealt with the procedural and substantive issues?:
        Prior courts have typically required contractors to provide adequate documentation and justification for claims made under contract disputes, emphasizing the need for clear evidence of incurred costs and the basis for claims.

        9. Would there be “urgency” or other reason for this court to issue a temporary injunction or order if the case were to proceed?:
        There may be urgency if Quality Trust, Inc. can demonstrate that delays in resolving the claim could lead to significant financial harm or operational disruptions, warranting a temporary injunction.

        10. What issues of fact or law would this court likely ask the parties to submit briefs (memoranda) on if it were to proceed to decision?:
        The court would likely ask for briefs on the adequacy of the evidence provided by QTI to support its claim, the interpretation of the contract terms regarding suspensions and delays, and the application of the Eichleay formula for calculating damages.

        11. What facts, law, and precedent would the court likely cite if it were to issue a decision based on the current record?:
        The court would likely cite the specific provisions of the FAR relevant to contract modifications and claims, the timeline of events leading to the claim, and precedents regarding the necessity of providing detailed support for claims in contract disputes.

    """
    extracted_rules = llm_analysis.substantive_rules_extraction(md_text, qa_text)
    return await llm_analysis.filter_procedural_rules(extracted_rules)


@router.post("/rules_extraction", response_model=FactsAndRulesOutput)
async def facts_and_rules_extraction(md_text: str) -> FactsAndRulesOutput:
    """
    Extracts fact patterns, procedural rules, and substantive legal rules from text
    containing a contract dispute decision/order and returns the extracted content.

    Example Input:

        CBCA 7451
        QUALITY TRUST, INC.,
        Appellant,
        v.
        DEPARTMENT OF THE INTERIOR,
        Respondent.

        Lawrence M. Ruiz, President of Quality Trust, Inc., Junction City, KS, appearing for Appellant.
        Rachel Grabenstein, Office of the Solicitor, Department of the Interior, Albuquerque, NM, counsel for Respondent.

        Before Board Judges RUSSELL, SULLIVAN, and CHADWICK.

        SULLIVAN, Board Judge.

        Quality Trust, Inc. (QTI) appealed the decision of a contracting officer for the Department of the Interior (DOI or respondent) denying QTI’s claim for lack of support.

        Statement of Undisputed Facts

        I. Claim to the Contracting Officer

        In September 2020, DOI entered into a contract with QTI for bridge and road repair. Appeal File, Exhibit 7 at 2-4. The period of performance was September 23, 2020, to February 26, 2021. Id. at 4. The contract incorporated Federal Acquisition Regulation (FAR) clause 52.242-14, Suspension of Work (APR 1984) (48 CFR 52.242-14 (2020)). Exhibit 7 at 81. That clause stipulates that a contractor shall receive an economic adjustment for any increase in contract performance costs “necessarily caused by the unreasonable suspension, delay, or interruption” of work by the contracting officer. To ensure that nesting birds were not disturbed, the contract prohibited QTI from performing masonry work on the bridge to be repaired between March 15 and September 1. Exhibit 7 at 75.

        There are two suspensions of work documented in the appeal file. On December 28, 2020, the contracting officer issued a unilateral modification, partially suspending work to address QTI’s mistake in price. Exhibit 33 at 2 (modification 1); see also Exhibits 25, 28 at 2. DOI lifted the suspension on January 21, 2021. Exhibit 42 at 2. On February 4, 2021, the contracting officer issued another suspension and a cure notice, directing QTI to address several failures and deficiencies in its performance. Exhibit 53 (modification 3). After receiving several additional cure notices, QTI made the necessary adjustments, and the contracting officer lifted this second suspension on March 30, 2021. Exhibit 70 at 3 (modification 4). In the modification lifting the second suspension, the contracting officer extended the completion date to September 30, 2021. Id.

        In April 2021, the parties executed a bilateral modification to address “a mutual mistake in the contract price after award,” adding approximately $52,000 to the contract price. Exhibit 76 at 2 (modification 5). On January 4, 2022, the contracting officer issued two unilateral modifications. The first extended the contract completion dated to January 31, 2022. Exhibit 121 at 2 (modification 8). The second partially terminated work for convenience, listing five areas of terminated contract work. Id. at 4-11 (modification 9).

        By letter dated January 10, 2022, QTI submitted a “time and cost modification request,” seeking payment of $2000 per day for the period from March through November 2021, during which QTI alleged it was on standby due to “latent conditions and changes” in a project that was “not classified correctly.” Exhibit 129 at 3.

        In April 2022, QTI submitted a claim to the contracting officer pursuant to the contract’s Disputes clause, FAR 52.233-1, seeking payment of $481,109.75. Exhibit 146 at 3-8. QTI did not explain how it arrived at its claim amount or identify what “[l]ost [a]djustment expenses” remained to be incurred. See id. at 3. QTI certified that the supporting data it provided “are accurate and complete” and that the “amount requested accurately reflects the contract adjustment for which the contractor believes the Government is liable.” Id.

        On May 23, 2022, the contracting officer requested via email that QTI clarify the amount of its claim and provide documentation showing “how [QTI] arrived at the amount claimed and explain to the Government why [QTI is] entitled to the sum amount claimed.” Exhibit 148 at 1. In its email reply the same day, QTI described a series of purported problems on the contract:

        “[T]his contract is royally messed up in many specific areas. Let me reiterate[.] When we had the problems on the bridge, a time and cost modification was sent to you, of which you never responded to over a year ago[.] QTI had taken into account that we must be ready and willing to [mobilize] and [demobilize] two more times[,] [w]hich alone would easily add another $100,000.00[.] Because of all the changes, and a contract that never said, we were working on a Department of Natural Resources (DNR) project was very deceiving from the specifications and drawings. Please note: the project was out ofscope and full of differing site conditions and latent conditions to mention a few. The more I think about this . . . QTI could easily justify the $481,109.75.” Exhibit 150 at 2. QTI also stated that “we estimated $2,000.00 a day based on [this contract] being our only project.” Id. QTI also submitted a new additional payment request for $75,840.25. Exhibit 149 at 3. QTI complained about a “unilateral Partial Termination . . . due to latent and differing site conditions” and that modification 5 “was never honored in good faith in the Amount of $51,921.00 plus interest and penalties.” Id. at 3.

        The following day, the contracting officer and QTI exchanged a series of emails seeking to clarify the basis of QTI’s claim and the payment request for $75,840.25. See Exhibits 151, 152. In its replies, QTI asserted that the nearly $52,000 modification to the contract value (modification 5) formed the basis of its claim but did not explain how. See Exhibit 152. On June 8, 2022, QTI sent the contracting officer three emails, the last of which offered to “justify the $481,109.75.” Exhibit 153 at 4. QTI asserted that it could support its claim with the use of the Eichleay formula. See id. (“For the larger amount[,] QTI will claim under the EIKLAY [sic] Formula.”).

        On June 14, 2022, the contracting officer denied the claim, concluding that QTI had not provided support for its claim. Exhibit 154 at 4.
    """
    return await llm_analysis.extract_facts_and_rules(md_text)


@router.post("/admissibility_scoring", response_model=AdmissibilityScoringOutput)
async def visualize_admissibility_scoring(md_text: str) -> AdmissibilityScoringOutput:
    """
    This endpoint accepts a text input describing the factual and procedural history of a case
    (prior to litigation) and returns a list of procedural rules scored on four dimensions: doctrinal fit, fact match,
    party assertion, and precedent alignment.

    Scoring procedural rules involves evaluating how likely each cited or implied rule is to affect whether a contract claim will be heard or dismissed before an appeal is considered on the merits.
    This score reflects how well each procedural rule is supported by the case record before the appeal begins, and whether it aligns with legal standards that determine claim admissibility. It does not predict outcomes, but rather assesses which procedural requirements are legally triggered, contested, or determinative at the threshold stage.

    The scoring contains:
    - Procedural Rule: The specific procedural rule, doctrine, or principle that might shape how the claim is handled before or during appeal.
    - Rationale: A short rationale justifying your scoring.

    The scoring contains four factors scored independently (on a 0–5 scale):

    - Doctrinal Fit – Does the rule align with known procedural doctrines applicable to federal contract disputes?
    - Fact Match – How well do the facts in the document support or trigger the use of this procedural rule?
    - Party Assertion – Have either party (contractor or government) clearly invoked, referenced, or implied this rule?
    - Precedent Alignment – Does this rule align with how similar cases have been handled historically?


    Parameters:

        md_text (str): Source document containing pre-appeal case content.

    Returns:

        AdmissibilityScoringOutput:
        {
            "scores": [
                {
                "procedural_rule": str,
                "doctrinal_fit": int,
                "fact_match": int,
                "party_assertion": int,
                "precedent_alignment": int,
                "rationale": str
                },
                ...
            ]
        }

    Example Input:

        CBCA 7451
        QUALITY TRUST, INC.,
        Appellant,
        v.
        DEPARTMENT OF THE INTERIOR,
        Respondent.

        Lawrence M. Ruiz, President of Quality Trust, Inc., Junction City, KS, appearing for Appellant.
        Rachel Grabenstein, Office of the Solicitor, Department of the Interior, Albuquerque, NM, counsel for Respondent.

        Before Board Judges RUSSELL, SULLIVAN, and CHADWICK.

        SULLIVAN, Board Judge.

        Quality Trust, Inc. (QTI) appealed the decision of a contracting officer for the Department of the Interior (DOI or respondent) denying QTI’s claim for lack of support.

        Statement of Undisputed Facts

        I. Claim to the Contracting Officer

        In September 2020, DOI entered into a contract with QTI for bridge and road repair. Appeal File, Exhibit 7 at 2-4. The period of performance was September 23, 2020, to February 26, 2021. Id. at 4. The contract incorporated Federal Acquisition Regulation (FAR) clause 52.242-14, Suspension of Work (APR 1984) (48 CFR 52.242-14 (2020)). Exhibit 7 at 81. That clause stipulates that a contractor shall receive an economic adjustment for any increase in contract performance costs “necessarily caused by the unreasonable suspension, delay, or interruption” of work by the contracting officer. To ensure that nesting birds were not disturbed, the contract prohibited QTI from performing masonry work on the bridge to be repaired between March 15 and September 1. Exhibit 7 at 75.

        There are two suspensions of work documented in the appeal file. On December 28, 2020, the contracting officer issued a unilateral modification, partially suspending work to address QTI’s mistake in price. Exhibit 33 at 2 (modification 1); see also Exhibits 25, 28 at 2. DOI lifted the suspension on January 21, 2021. Exhibit 42 at 2. On February 4, 2021, the contracting officer issued another suspension and a cure notice, directing QTI to address several failures and deficiencies in its performance. Exhibit 53 (modification 3). After receiving several additional cure notices, QTI made the necessary adjustments, and the contracting officer lifted this second suspension on March 30, 2021. Exhibit 70 at 3 (modification 4). In the modification lifting the second suspension, the contracting officer extended the completion date to September 30, 2021. Id.

        In April 2021, the parties executed a bilateral modification to address “a mutual mistake in the contract price after award,” adding approximately $52,000 to the contract price. Exhibit 76 at 2 (modification 5). On January 4, 2022, the contracting officer issued two unilateral modifications. The first extended the contract completion dated to January 31, 2022. Exhibit 121 at 2 (modification 8). The second partially terminated work for convenience, listing five areas of terminated contract work. Id. at 4-11 (modification 9).

        By letter dated January 10, 2022, QTI submitted a “time and cost modification request,” seeking payment of $2000 per day for the period from March through November 2021, during which QTI alleged it was on standby due to “latent conditions and changes” in a project that was “not classified correctly.” Exhibit 129 at 3.

        In April 2022, QTI submitted a claim to the contracting officer pursuant to the contract’s Disputes clause, FAR 52.233-1, seeking payment of $481,109.75. Exhibit 146 at 3-8. QTI did not explain how it arrived at its claim amount or identify what “[l]ost [a]djustment expenses” remained to be incurred. See id. at 3. QTI certified that the supporting data it provided “are accurate and complete” and that the “amount requested accurately reflects the contract adjustment for which the contractor believes the Government is liable.” Id.

        On May 23, 2022, the contracting officer requested via email that QTI clarify the amount of its claim and provide documentation showing “how [QTI] arrived at the amount claimed and explain to the Government why [QTI is] entitled to the sum amount claimed.” Exhibit 148 at 1. In its email reply the same day, QTI described a series of purported problems on the contract:

        “[T]his contract is royally messed up in many specific areas. Let me reiterate[.] When we had the problems on the bridge, a time and cost modification was sent to you, of which you never responded to over a year ago[.] QTI had taken into account that we must be ready and willing to [mobilize] and [demobilize] two more times[,] [w]hich alone would easily add another $100,000.00[.] Because of all the changes, and a contract that never said, we were working on a Department of Natural Resources (DNR) project was very deceiving from the specifications and drawings. Please note: the project was out ofscope and full of differing site conditions and latent conditions to mention a few. The more I think about this . . . QTI could easily justify the $481,109.75.” Exhibit 150 at 2. QTI also stated that “we estimated $2,000.00 a day based on [this contract] being our only project.” Id. QTI also submitted a new additional payment request for $75,840.25. Exhibit 149 at 3. QTI complained about a “unilateral Partial Termination . . . due to latent and differing site conditions” and that modification 5 “was never honored in good faith in the Amount of $51,921.00 plus interest and penalties.” Id. at 3.

        The following day, the contracting officer and QTI exchanged a series of emails seeking to clarify the basis of QTI’s claim and the payment request for $75,840.25. See Exhibits 151, 152. In its replies, QTI asserted that the nearly $52,000 modification to the contract value (modification 5) formed the basis of its claim but did not explain how. See Exhibit 152. On June 8, 2022, QTI sent the contracting officer three emails, the last of which offered to “justify the $481,109.75.” Exhibit 153 at 4. QTI asserted that it could support its claim with the use of the Eichleay formula. See id. (“For the larger amount[,] QTI will claim under the EIKLAY [sic] Formula.”).

        On June 14, 2022, the contracting officer denied the claim, concluding that QTI had not provided support for its claim. Exhibit 154 at 4.
    """
    return await llm_analysis.admissibility_scoring_results(md_text)


@router.post("/relevance_scoring", response_model=RelevanceScoringOutput)
async def visualize_relevance_scoring(md_text: str) -> RelevanceScoringOutput:
    """
    This endpoint accepts a text input describing the factual and legal background of a contract dispute
    (prior to litigation) and returns a list of substantive rules scored on four dimensions: doctrinal fit, fact match,
    party assertion, and precedent alignment.

    Scoring substantive rules involves evaluating how likely each identified legal or contractual doctrine is to influence
    the outcome of a case if it proceeds to appeal. This score reflects the legal and factual strength of the rule before
    the appeal begins and helps determine how central each doctrine may be to the Board’s eventual analysis.

    The scoring contains:
    - Substantive Rule: The specific legal principle, contract clause, or doctrine that may impact the merits of the claim.
    - Rationale: A short rationale justifying your scoring.

    The scoring contains four factors scored independently (on a 0–5 scale):

    - Doctrinal Fit – How closely the rule matches the core legal questions raised in the case.
    - Fact Match – Whether the factual record supports applying this rule.
    - Party Assertion – Whether either party has actively invoked or disputed the rule.
    - Precedent Alignment – How courts have treated similar rules in analogous contexts.

    Parameters:

        md_text (str): Source document containing pre-appeal case content.

    Returns:

        RelevanceScoringOutput:
        {
            "scores": [
                {
                "substantive_rule": str,
                "doctrinal_fit": int,
                "fact_match": int,
                "party_assertion": int,
                "precedent_alignment": int,
                "rationale": str
                },
                ...
            ]
        }

    Example Input:

        CBCA 7451
        QUALITY TRUST, INC.,
        Appellant,
        v.
        DEPARTMENT OF THE INTERIOR,
        Respondent.

        Lawrence M. Ruiz, President of Quality Trust, Inc., Junction City, KS, appearing for Appellant.
        Rachel Grabenstein, Office of the Solicitor, Department of the Interior, Albuquerque, NM, counsel for Respondent.

        Before Board Judges RUSSELL, SULLIVAN, and CHADWICK.

        SULLIVAN, Board Judge.

        Quality Trust, Inc. (QTI) appealed the decision of a contracting officer for the Department of the Interior (DOI or respondent) denying QTI’s claim for lack of support.

        Statement of Undisputed Facts

        I. Claim to the Contracting Officer

        In September 2020, DOI entered into a contract with QTI for bridge and road repair. Appeal File, Exhibit 7 at 2-4. The period of performance was September 23, 2020, to February 26, 2021. Id. at 4. The contract incorporated Federal Acquisition Regulation (FAR) clause 52.242-14, Suspension of Work (APR 1984) (48 CFR 52.242-14 (2020)). Exhibit 7 at 81. That clause stipulates that a contractor shall receive an economic adjustment for any increase in contract performance costs “necessarily caused by the unreasonable suspension, delay, or interruption” of work by the contracting officer. To ensure that nesting birds were not disturbed, the contract prohibited QTI from performing masonry work on the bridge to be repaired between March 15 and September 1. Exhibit 7 at 75.

        There are two suspensions of work documented in the appeal file. On December 28, 2020, the contracting officer issued a unilateral modification, partially suspending work to address QTI’s mistake in price. Exhibit 33 at 2 (modification 1); see also Exhibits 25, 28 at 2. DOI lifted the suspension on January 21, 2021. Exhibit 42 at 2. On February 4, 2021, the contracting officer issued another suspension and a cure notice, directing QTI to address several failures and deficiencies in its performance. Exhibit 53 (modification 3). After receiving several additional cure notices, QTI made the necessary adjustments, and the contracting officer lifted this second suspension on March 30, 2021. Exhibit 70 at 3 (modification 4). In the modification lifting the second suspension, the contracting officer extended the completion date to September 30, 2021. Id.

        In April 2021, the parties executed a bilateral modification to address “a mutual mistake in the contract price after award,” adding approximately $52,000 to the contract price. Exhibit 76 at 2 (modification 5). On January 4, 2022, the contracting officer issued two unilateral modifications. The first extended the contract completion dated to January 31, 2022. Exhibit 121 at 2 (modification 8). The second partially terminated work for convenience, listing five areas of terminated contract work. Id. at 4-11 (modification 9).

        By letter dated January 10, 2022, QTI submitted a “time and cost modification request,” seeking payment of $2000 per day for the period from March through November 2021, during which QTI alleged it was on standby due to “latent conditions and changes” in a project that was “not classified correctly.” Exhibit 129 at 3.

        In April 2022, QTI submitted a claim to the contracting officer pursuant to the contract’s Disputes clause, FAR 52.233-1, seeking payment of $481,109.75. Exhibit 146 at 3-8. QTI did not explain how it arrived at its claim amount or identify what “[l]ost [a]djustment expenses” remained to be incurred. See id. at 3. QTI certified that the supporting data it provided “are accurate and complete” and that the “amount requested accurately reflects the contract adjustment for which the contractor believes the Government is liable.” Id.

        On May 23, 2022, the contracting officer requested via email that QTI clarify the amount of its claim and provide documentation showing “how [QTI] arrived at the amount claimed and explain to the Government why [QTI is] entitled to the sum amount claimed.” Exhibit 148 at 1. In its email reply the same day, QTI described a series of purported problems on the contract:

        “[T]his contract is royally messed up in many specific areas. Let me reiterate[.] When we had the problems on the bridge, a time and cost modification was sent to you, of which you never responded to over a year ago[.] QTI had taken into account that we must be ready and willing to [mobilize] and [demobilize] two more times[,] [w]hich alone would easily add another $100,000.00[.] Because of all the changes, and a contract that never said, we were working on a Department of Natural Resources (DNR) project was very deceiving from the specifications and drawings. Please note: the project was out ofscope and full of differing site conditions and latent conditions to mention a few. The more I think about this . . . QTI could easily justify the $481,109.75.” Exhibit 150 at 2. QTI also stated that “we estimated $2,000.00 a day based on [this contract] being our only project.” Id. QTI also submitted a new additional payment request for $75,840.25. Exhibit 149 at 3. QTI complained about a “unilateral Partial Termination . . . due to latent and differing site conditions” and that modification 5 “was never honored in good faith in the Amount of $51,921.00 plus interest and penalties.” Id. at 3.

        The following day, the contracting officer and QTI exchanged a series of emails seeking to clarify the basis of QTI’s claim and the payment request for $75,840.25. See Exhibits 151, 152. In its replies, QTI asserted that the nearly $52,000 modification to the contract value (modification 5) formed the basis of its claim but did not explain how. See Exhibit 152. On June 8, 2022, QTI sent the contracting officer three emails, the last of which offered to “justify the $481,109.75.” Exhibit 153 at 4. QTI asserted that it could support its claim with the use of the Eichleay formula. See id. (“For the larger amount[,] QTI will claim under the EIKLAY [sic] Formula.”).

        On June 14, 2022, the contracting officer denied the claim, concluding that QTI had not provided support for its claim. Exhibit 154 at 4.
    """
    return await llm_analysis.relevance_scoring_results(md_text)


@router.post("/scoring_results", response_model=CombinedScoreSummary)
async def visualize_scoring(md_text: str) -> CombinedScoreSummary:
    """
    Evaluate potential judicial reasoning by scoring procedural and substantive rules in a pre-decision legal document.

    This endpoint takes a legal text and simulates how a judges and courts might analyze it prior to writing an opinion.

    It uses a language model to:

    1. Extract legally relevant **facts**.
    2. Identify **procedural rules** and **substantive rules** invoked or implied in the text.
    3. Score each rule across four pillars of legal reasoning:
       - **Doctrinal Fit**: Alignment with established legal principles.
       - **Fact Match**: Applicability to the facts at hand.
       - **Party Assertion**: Degree to which parties rely on or contest the rule.
       - **Precedent Alignment**: Support from prior cases or rulings.

    Each rule receives a normalized score from 0.0 to 1.0, and the final output includes:
    - A detailed list of procedural rules with admissibility scores and rationales.
    - A detailed list of substantive rules with relevance scores and rationales.
    - Overall average scores for procedural and substantive rule strength.

    This allows users to preview and visualize how a judicial actor might weigh the legal materials **before reaching a decision**.

    Parameters:

        md_text (str): A pre-decision legal document in Markdown format.


    Returns:

        CombinedScoreSummary: A structured scoring breakdown of extracted rules and their legal strength


    Example Input:

        CBCA 7451
        QUALITY TRUST, INC.,
        Appellant,
        v.
        DEPARTMENT OF THE INTERIOR,
        Respondent.

        Lawrence M. Ruiz, President of Quality Trust, Inc., Junction City, KS, appearing for Appellant.
        Rachel Grabenstein, Office of the Solicitor, Department of the Interior, Albuquerque, NM, counsel for Respondent.

        Before Board Judges RUSSELL, SULLIVAN, and CHADWICK.

        SULLIVAN, Board Judge.

        Quality Trust, Inc. (QTI) appealed the decision of a contracting officer for the Department of the Interior (DOI or respondent) denying QTI’s claim for lack of support.

        Statement of Undisputed Facts

        I. Claim to the Contracting Officer

        In September 2020, DOI entered into a contract with QTI for bridge and road repair. Appeal File, Exhibit 7 at 2-4. The period of performance was September 23, 2020, to February 26, 2021. Id. at 4. The contract incorporated Federal Acquisition Regulation (FAR) clause 52.242-14, Suspension of Work (APR 1984) (48 CFR 52.242-14 (2020)). Exhibit 7 at 81. That clause stipulates that a contractor shall receive an economic adjustment for any increase in contract performance costs “necessarily caused by the unreasonable suspension, delay, or interruption” of work by the contracting officer. To ensure that nesting birds were not disturbed, the contract prohibited QTI from performing masonry work on the bridge to be repaired between March 15 and September 1. Exhibit 7 at 75.

        There are two suspensions of work documented in the appeal file. On December 28, 2020, the contracting officer issued a unilateral modification, partially suspending work to address QTI’s mistake in price. Exhibit 33 at 2 (modification 1); see also Exhibits 25, 28 at 2. DOI lifted the suspension on January 21, 2021. Exhibit 42 at 2. On February 4, 2021, the contracting officer issued another suspension and a cure notice, directing QTI to address several failures and deficiencies in its performance. Exhibit 53 (modification 3). After receiving several additional cure notices, QTI made the necessary adjustments, and the contracting officer lifted this second suspension on March 30, 2021. Exhibit 70 at 3 (modification 4). In the modification lifting the second suspension, the contracting officer extended the completion date to September 30, 2021. Id.

        In April 2021, the parties executed a bilateral modification to address “a mutual mistake in the contract price after award,” adding approximately $52,000 to the contract price. Exhibit 76 at 2 (modification 5). On January 4, 2022, the contracting officer issued two unilateral modifications. The first extended the contract completion dated to January 31, 2022. Exhibit 121 at 2 (modification 8). The second partially terminated work for convenience, listing five areas of terminated contract work. Id. at 4-11 (modification 9).

        By letter dated January 10, 2022, QTI submitted a “time and cost modification request,” seeking payment of $2000 per day for the period from March through November 2021, during which QTI alleged it was on standby due to “latent conditions and changes” in a project that was “not classified correctly.” Exhibit 129 at 3.

        In April 2022, QTI submitted a claim to the contracting officer pursuant to the contract’s Disputes clause, FAR 52.233-1, seeking payment of $481,109.75. Exhibit 146 at 3-8. QTI did not explain how it arrived at its claim amount or identify what “[l]ost [a]djustment expenses” remained to be incurred. See id. at 3. QTI certified that the supporting data it provided “are accurate and complete” and that the “amount requested accurately reflects the contract adjustment for which the contractor believes the Government is liable.” Id.

        On May 23, 2022, the contracting officer requested via email that QTI clarify the amount of its claim and provide documentation showing “how [QTI] arrived at the amount claimed and explain to the Government why [QTI is] entitled to the sum amount claimed.” Exhibit 148 at 1. In its email reply the same day, QTI described a series of purported problems on the contract:

        “[T]his contract is royally messed up in many specific areas. Let me reiterate[.] When we had the problems on the bridge, a time and cost modification was sent to you, of which you never responded to over a year ago[.] QTI had taken into account that we must be ready and willing to [mobilize] and [demobilize] two more times[,] [w]hich alone would easily add another $100,000.00[.] Because of all the changes, and a contract that never said, we were working on a Department of Natural Resources (DNR) project was very deceiving from the specifications and drawings. Please note: the project was out ofscope and full of differing site conditions and latent conditions to mention a few. The more I think about this . . . QTI could easily justify the $481,109.75.” Exhibit 150 at 2. QTI also stated that “we estimated $2,000.00 a day based on [this contract] being our only project.” Id. QTI also submitted a new additional payment request for $75,840.25. Exhibit 149 at 3. QTI complained about a “unilateral Partial Termination . . . due to latent and differing site conditions” and that modification 5 “was never honored in good faith in the Amount of $51,921.00 plus interest and penalties.” Id. at 3.

        The following day, the contracting officer and QTI exchanged a series of emails seeking to clarify the basis of QTI’s claim and the payment request for $75,840.25. See Exhibits 151, 152. In its replies, QTI asserted that the nearly $52,000 modification to the contract value (modification 5) formed the basis of its claim but did not explain how. See Exhibit 152. On June 8, 2022, QTI sent the contracting officer three emails, the last of which offered to “justify the $481,109.75.” Exhibit 153 at 4. QTI asserted that it could support its claim with the use of the Eichleay formula. See id. (“For the larger amount[,] QTI will claim under the EIKLAY [sic] Formula.”).

        On June 14, 2022, the contracting officer denied the claim, concluding that QTI had not provided support for its claim. Exhibit 154 at 4.
    """
    return await llm_analysis.scoring_results(md_text)
