LEGAL_REASONING_QUESTIONS_AND_ANSWERS_PROMPT = """
From the following document (which may be a court decision, order, or dismissal), answer the following questions judges and courts must answer to write their opinions or decisions.

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

9. Is there “urgency” or other reason for this court to issue a temporary injunction or order while the case proceeds in this court?:  
[Answer]

10. What issues of fact or law would this court ask the parties to submit briefs (memoranda) on so as to inform the court before a decision?:  
[Answer]

11. The court issues its decision, citing relevant facts, law and precedent to explain its decision:  
[Answer]
"""


FACTS_EXTRACTION_PROMPT = """
From the following document (which may be a court decision, order, or dismissal), extract only the most important factual assertions that the Board either relied on or explicitly rejected in its reasoning.

You are provided with two inputs:
1. The full text of the decision
2. A Q&A summary that outlines the court's reasoning, facts, and conclusions

Use both inputs to identify core facts, especially those that were cited, relied on, or explicitly addressed and rejected.

Return a valid JSON array of objects. Each object must follow this structure:
{{
  "id": int,  // A zero-based index indicating the order in which the fact appears in the source text (starting from 0)
  "specific_fact_cited": str,  // Exact sentence copied verbatim from the document
  "relevance_reason": str,  // Why was the fact relevant; if the Board relied on this fact, explain how it supported the reasoning or outcome
  "contestability_reason": str  // Why was the fact not relevant; if the Board rejected or discounted this fact, explain why; leave this empty ONLY if the fact was clearly relied upon
}}

Guidelines:
- Extract only **core facts** that shaped the Board’s analysis or were explicitly considered and rejected.
- Do NOT include procedural housekeeping like deadlines, discovery schedules, or routine motions unless the Board relied on them in its reasoning.
- DO include: facts about contract terms, suspensions, delays, claim filings, amounts, and factual disputes discussed by the Board.
- DO include facts asserted by the appellant **if** the Board addressed or rejected them — explain this in why_was_the_fact_not_relevant.
- Avoid quoting legal conclusions, rules, or the Board’s final holdings — only extract factual events or claims.
- Eliminate redundancy: group together facts if the Board discussed them together (e.g., both suspensions in one fact if possible).
- Return only valid JSON. Do not include explanations or notes outside the array.

Note: If some facts were discussed but ultimately found irrelevant or unpersuasive, reflect this in why_was_the_fact_not_relevant. It’s okay if all entries were relevant, but be careful not to omit dismissed facts that were addressed.

Inputs:
DOCUMENT TEXT:
{text}

LEGAL REASONING Q&A:
{qa}
"""


PROCEDURAL_RULES_EXTRACTION_PROMPT = """
From the following document (which may be a court decision, order, or dismissal), extract all procedural rules or doctrines that the Board cited, applied, or relied on in reaching its decision or shaping the case handling.

You are provided with two inputs:
1. The full text of the decision
2. A Q&A summary outlining the court's reasoning, findings, and conclusions

Use both sources to identify procedural rules that were actually applied by the Board — but quote rules and reasoning only from the source document.

Return a valid JSON array of objects. Each object must follow this structure:

{{
  "procedural_rule": str,  // A short plain-language description in 1 or 2 sentences (≤40 words) of the specific procedural rule, doctrine, or principle mentioned, append at the end the citation or short name if possible.
  "effects": str,  // Effect on courts decision or case handling; describe how the Board applied this rule or why it mattered procedurally
}}

Guidelines:
- Include only procedural rules — i.e., those governing how the case is handled, not what the outcome should be based on the facts or law.
- DO include: rules about burdens of proof, timeliness, jurisdiction, claim sufficiency, standards for summary judgment, requirements for documentation, appeal scope, or evidence admissibility if procedural in nature.
- DO NOT include: substantive contract doctrines, FAR economic adjustment clauses, or damages formulas like the Eichleay formula (those belong in the substantive rules section).
- If a procedural rule is cited with reference to a regulation (e.g., “Board Rule 26”), include the citation in `procedural_rule`.
- If the rule is procedural but mentioned only in passing and not applied by the Board, exclude it.

Return only valid JSON — no notes or commentary outside the array.

Inputs:
DOCUMENT TEXT:
{text}

LEGAL REASONING Q&A:
{qa}
"""

FILTER_PROCEDURAL_RULES_PROMPT = """
You are given a list of rules or doctrines extracted from a court or board decision.

Your task is to filter out any rule that is **substantive** (i.e., related to what legal rights or entitlements the parties have under the law), and retain only those that are **procedural** (i.e., related to how the case is handled, processed, or decided).

Keep rules that relate to:
- Jurisdiction
- Burdens of proof or persuasion
- Timeliness of claims, motions, or appeals
- Standards for summary judgment or dismissal
- Filing or response requirements
- Procedural consequences of failing to meet deadlines or requirements
- Scope of appeal or issues preserved for review
- Admissibility or sufficiency of evidence (if discussed procedurally)

Remove rules that relate to:
- Legal tests used to determine liability, entitlement, or damages
- Standards for granting or denying monetary claims
- Doctrines defining contract rights or obligations
- Economic adjustment clauses, compensation formulas, or entitlement frameworks

Return a new JSON array that includes only the procedural rules with this structure:

[
  {{
    "procedural_rule": str,
    "effects": str
  }},
  ...
]

Here is the original list:

{rules}
"""


SUBSTANTIVE_RULES_EXTRACTION_PROMPT= """
From the following document (which may be a court decision, order, or dismissal), extract all substantive rules of law or contract principles that the Board relied on—explicitly or implicitly—to decide the case.

You are provided with two inputs:
1. The full text of the decision
2. A structured Q&A outlining the court’s reasoning, facts, and conclusions

Use both inputs to accurately identify the substantive rules applied by the Board, and explain how they were triggered by the facts and used in the decision.

Return a valid JSON array of objects. Each object must follow this structure:
{{
  "substantive_law": str,  // Principle of substantive law; a concise restatement of the rule or doctrine (e.g., "Constructive Suspension Doctrine", "FAR 52.242-14 Suspension of Work clause", or "Eichleay Formula for Damages").
  "applicability": str,  // Facts making the principle applicable; the specific facts or circumstances in this case that made this principle relevant or triggered its application.
  "relevance": str  // How this principle and facts were crucial to the decision; i.e. how the Board applied the principle to those facts, including whether it supported or defeated a claim.
}}

Guidelines:
- Include all **contract doctrines** the Board relied on, including interpretations of **contract clauses**, **scope of work**, and **agreed limitations** (e.g., bird nesting restrictions).
- Include all **legal standards** used to evaluate entitlement, damages, causation, concurrency, or burden of proof (e.g., Eichleay formula, constructive suspension).
- Include principles even if **not labeled as legal rules** in the text — if the Board applied the logic of a rule or doctrine, extract it.
- DO NOT include **procedural rules** (e.g., summary judgment standards, motion deadlines, burden-shifting rules) — these belong in a separate extraction.
- If the same rule appears in multiple forms (e.g., FAR clause + constructive suspension), extract each application distinctly if they involve different reasoning.

Be concise but complete. Return only valid JSON — no explanations or commentary outside the array.

Inputs:
DOCUMENT TEXT:
{text}

LEGAL REASONING Q&A:
{qa}
"""



