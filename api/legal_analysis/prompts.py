CREATE_PRE_APPEAL_DOCUMENT_PROMPT = """
From the following document (which may be a court decision, order, or dismissal), generate a new version that contains only the content that was available before the appeal was filed.

Preserve the original content exactly as written, including formatting, names, dates, quotations, and structure. Do not rewrite, summarize, or paraphrase any portion of the text.

Your only task is to remove content that falls into any of the following categories:

- Legal reasoning, analysis, findings, or citations by the Board or court
- Procedural history or developments that occurred after the appeal was filed
- Statements, footnotes, or narrative from the Board describing or resolving the appeal
- Any label, heading, or caption that states or summarizes the result of the appeal or any procedural rulings made during the appeal. This includes, but is not limited to:
  - “DENIED: [date]”
  - “DISMISSED WITH PREJUDICE: [date]”
  - “DISMISSED IN PART FOR LACK OF JURISDICTION: [date]”
  - “GRANTED IN PART: [date]”
  - “APPELLANT’S MOTION FOR SUMMARY JUDGMENT DENIED; RESPONDENT’S MOTION FOR SUMMARY JUDGMENT GRANTED IN PART: [date]”
  - Any similar summary or caption reflecting a Board or court decision, procedural disposition, or ruling on motions
- Any content that was introduced during or after the litigation or decision-making process

The output must read as a complete, self-contained document that existed prior to litigation, reflecting only the parties’ claims, the contracting officer’s actions and decisions, and related correspondence.

Do not include any commentary, explanations to the reader, or editorial statements.

Input:
DOCUMENT TEXT:
{text}
"""

LEGAL_REASONING_QUESTIONS_AND_ANSWERS_PROMPT = """
From the following document (which describes the status of a contract claim prior to any appeal or court decision), answer the following questions that a court or Board would need to consider if evaluating this case.

For each item, reproduce the full question first, then immediately provide the answer below it. Do not include any introductory text, summaries, explanations, or closing remarks.

1. Does this court have proper jurisdiction of the parties and the subject matter of the case, if so, why?:  
[Answer]

2. What is the procedural posture of the case? If this is an appeal from a lower court, what was the decision of that court, and which litigant is appealing it?:  
[Answer]

3. What is the basis for the appeal? In other words, what does the appellant claim the lower court wrongly decided? For instance, did that court exclude key evidence or misinterpret applicable law?:  
[Answer]

4. What other procedural grounds exist to dismiss the case or to return it for a revised hearing and decision to the lower court?:  
[Answer]

5. What are the facts introduced in the case? What facts are undisputed and what facts are disputed?:  
[Answer]

6. What claims or causes of action were brought and argued by the litigants?:  
[Answer]

7. What is the substantive law that actually applies to the facts of this case?:  
[Answer]

8. How have prior courts dealt with the procedural and substantive issues?:  
[Answer]

9. Would there be “urgency” or other reason for this court to issue a temporary injunction or order if the case were to proceed?:  
[Answer]

10. What issues of fact or law would this court likely ask the parties to submit briefs (memoranda) on if it were to proceed to decision?:  
[Answer]

11. What facts, law, and precedent would the court likely cite if it were to issue a decision based on the current record?:  
[Answer]
"""


FACTS_EXTRACTION_PROMPT = """
From the following document (which describes the factual and procedural history before any court or Board decision), extract factual assertions that appear in the text and could be relevant to how a court might later evaluate the case.

You are provided with two inputs:
1. The full text of the pre-appeal document
2. A structured Q&A containing preliminary legal reasoning, claims, and procedural summaries

Use both sources to identify and assess facts — always quote directly from the document text, but feel free to use the Q&A to help clarify how facts may be framed, interpreted, or contested.

Return a valid JSON object with this structure:

{{
  "facts": [
    {{
      "id": int,  
      "specific_fact_cited": str,  
      "relevancy_reason: str,  
      "contestability_reason": str  
    }},
    ...
  ]
}}

Where:
- "id": A zero-based index indicating the order in which the fact appears in the source text (starting from 0)
- "specific_fact_cited": Exact sentence copied verbatim from the document
- "relevancy_reason": Why would the fact be relevant; explain how this fact could bear on jurisdiction, procedural posture, responsibility, or any legal issue the court might later address
- "contestability_reason": Why might the fact be contested; explain why the fact might be challenged, dismissed, or considered immaterial; leave empty if clearly reliable and material

Guidelines:
- Extract factual statements, events, or allegations found in the document.
- Include contract terms, communications, suspensions, delays, modifications, claim amounts, procedural actions, and factual allegations made by any party.
- Do not assume whether a fact is important — instead, explain its possible relevance or contestability in the corresponding fields.
- Do not include legal conclusions, citations, or rules — extract facts only.
- Return only valid JSON. Do not include commentary outside the array.

Inputs:
DOCUMENT TEXT:
{text}

LEGAL REASONING Q&A:
{qa}
"""


PROCEDURAL_RULES_EXTRACTION_PROMPT = """
From the following document (which describes the procedural and factual history of a case before it reaches a court or Board decision), extract any procedural rules, requirements, or practices that are cited, implied, or suggested by the parties or the contracting officer — especially those that might later be relevant if the case were appealed.

You are provided with two inputs:
1. The full text of the pre-appeal document
2. A structured Q&A summary outlining the background and legal context of the dispute

Use both sources to identify procedural doctrines or references — but quote procedural content only from the document itself.

Return a valid JSON object with this structure:

{{
  "rules": [
    {{
      "procedural_rule": str,  
      "effects": str 
    }},
    ...
  ]
}}

Where:
- "procedural_rule": The specific procedural rule, doctrine, or principle that might shape how the claim is handled before or during appeal (quoted if possible)
- "effects": Effect on courts decision or case handling; explain how this rule might influence the handling, outcome, or viability of the case if it were later reviewed by a court or board

Guidelines:
- Include only procedural rules — i.e., rules about how the claim was filed, evaluated, or handled prior to an appeal.
- DO include: documentation requirements, certification standards, claim format requirements, deadlines, jurisdictional prerequisites, and contracting officer duties.
- DO NOT include: substantive doctrines or entitlement standards like the Eichleay formula or FAR economic adjustment clauses — those belong in substantive rule extraction.
- Return only valid JSON. Do not include commentary outside the array.

Inputs:
DOCUMENT TEXT:
{text}

LEGAL REASONING Q&A:
{qa}
"""


FILTER_PROCEDURAL_RULES_PROMPT = """
You are given a list of rules or doctrines mentioned in a pre-appeal document, such as a claim, denial, or related correspondence.

Your task is to filter out any rule that is **substantive** (i.e., related to what legal rights or entitlements the parties have under the law), and retain only those that are **procedural** (i.e., related to how the contract claim is processed, reviewed, or evaluated before any appeal is filed).

Keep rules that relate to:
- Jurisdiction or authority of the contracting officer
- Requirements for submitting a claim (e.g., certification, format, deadlines)
- Standards for what constitutes a valid claim under the Disputes clause
- Documentation or evidentiary requirements for initial claim review
- Procedures for modifying a contract or issuing a termination
- Timeliness or sufficiency of communications between parties
- Administrative steps required before appeal (e.g., final decision issuance)

Remove rules that relate to:
- Legal tests for entitlement to damages or equitable adjustment
- Standards for determining suspension, delay, or standby compensation
- Contract doctrines like constructive suspension or differing site conditions
- Use of the Eichleay formula or any other damage computation frameworks
- Interpretations of contract clauses that determine substantive rights

Return a **valid JSON object** with this structure:

{{
  "rules": [
    {{
      "procedural_rule": str,
      "effects": str
    }},
    ...
  ]
}}

Here is the original list:

{rules}
"""


SUBSTANTIVE_RULES_EXTRACTION_PROMPT = """
From the following document (which describes the factual and procedural history before any formal appeal ruling), extract all references to **substantive rules of law or contract principles** that are cited, implied, or suggested by the claimant or contracting officer — especially those that might become relevant if the dispute were reviewed by a court or board.

You are provided with two inputs:
1. The full text of the pre-appeal document
2. A structured Q&A summarizing legal theories, issues raised, and potential claims

Use both inputs to identify which legal or contractual doctrines were at stake — but quote only from the source document.

Return a valid JSON object with this structure:

{{
  "rules": [
    {{
      "substantive_law": string,
      "applicability": string,
      "relevance": string
    }},
    ...
  ]
}}

Where:
- "substantive_law": Principle of substantive law; a concise statement of the rule, clause, or doctrine at issue (e.g., "Suspension of Work clause", "Constructive Suspension Doctrine", "Eichleay Formula")
- "applicability": Facts making principle applicable; the specific events or allegations in the document that might cause this principle to apply
- "relevance": How this rule might affect the outcome if later analyzed by a court or Board (How this principle might be crucial to the decision).

Guidelines:
- Focus on rules governing rights, obligations, or entitlement to compensation under contracts or law.
- DO include FAR clauses, contract doctrines (e.g., changes, delays, latent conditions), and any legal formulas for calculating damages.
- DO NOT include procedural handling or summary judgment standards — those belong in the procedural rule extraction.
- Use the Q&A to clarify how parties are framing the law — but always extract principles from the document itself.
- Return only valid JSON. No commentary outside the array.

Inputs:
DOCUMENT TEXT:
{text}

LEGAL REASONING Q&A:
{qa}
"""


ADMISSIBILITY_SCORING_PROMPT = """
You are given:
1. A set of procedural rules extracted from a pre-appeal document
2. A list of facts from the same document
3. A summary of legal reasoning relevant to the claim

Your task is to assign an admissibility score to each procedural rule based on how likely it is to be invoked, relied on, or contested during future litigation or appeal.

Use the following four criteria to assign a score from 0 (low) to 5 (high) for each rule:

- doctrinal_fit: Does the rule align with known procedural doctrines applicable to federal contract disputes?
- fact_match: How well do the facts in the document support or trigger the use of this procedural rule?
- party_assertion: Have either party (contractor or government) clearly invoked, referenced, or implied this rule?
- precedent_alignment: Does this rule align with how similar cases have been handled historically?

For each procedural rule, include a short rationale justifying your scoring.

Return a **valid JSON object** matching this structure:

{{
  "scores": [
    {{
      "procedural_rule": str,
      "doctrinal_fit": int,
      "fact_match": int,
      "party_assertion": int,
      "precedent_alignment": int,
      "rationale": str
    }},
    ...
  ]
}}

Inputs:

FACTS:
{facts}

PROCEDURAL RULES:
{procedural_rules}

LEGAL REASONING Q&A:
{qa}
"""


RELEVANCE_SCORING_PROMPT = """
You are given:
1. A set of substantive rules (legal or contractual doctrines) extracted from a pre-appeal document
2. A list of facts from the same document
3. A summary of legal reasoning relevant to the claim

Your task is to assign a relevance score to each **substantive rule** based on how likely it is to shape the legal outcome if the case proceeds to appeal.

Use the following four criteria to assign a score from 0 (low) to 5 (high) for each rule:

- doctrinal_fit: How directly the rule aligns with legal standards or entitlements under federal contract law.
- fact_match: To what extent the factual record supports applying this rule.
- party_assertion: Whether either party (contractor or government) has referenced, relied upon, or disputed the rule before the appeal.
- precedent_alignment: How consistently courts or boards have treated this rule in analogous contexts.

For each substantive rule, include a short rationale justifying your scoring.

Return a **valid JSON object** matching this structure:

{{
  "scores": [
    {{
      "substantive_law": str,
      "doctrinal_fit": int,
      "fact_match": int,
      "party_assertion": int,
      "precedent_alignment": int,
      "rationale": str
    }},
    ...
  ]
}}

Inputs:

FACTS:
{facts}

SUBSTANTIVE RULES:
{substantive_rules}

LEGAL REASONING Q&A:
{qa}
"""
