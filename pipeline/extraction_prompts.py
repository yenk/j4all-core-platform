FACTS_EXTRACTION_PROMPT = """
From the following document (which may be a court decision, order, or dismissal), extract only the most important factual assertions that the Board either relied on or explicitly rejected in its reasoning.

Return a valid JSON array of objects. Each object must follow this structure:
{{
  "id": int,  // A zero-based index indicating the order in which the fact appears in the source text (starting from 0)
  "specific_fact_cited": str,  // Exact sentence copied verbatim from the document
  "why_was_the_fact_relevant": str,  // If the Board relied on this fact, explain how it supported the reasoning or outcome
  "why_was_the_fact_not_relevant": str  // If the Board rejected or discounted this fact, explain why; leave this empty ONLY if the fact was clearly relied upon
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
"""


PROCEDURAL_RULES_EXTRACTION_PROMPT = """
From the following document (which may be a court decision, order, or dismissal), extract all procedural rules or doctrines that the Board cited, applied, or relied on in reaching its decision or shaping the case handling.

Return a valid JSON array of objects. Each object must follow this structure:

{{
  "procedural_rule_cited": str,  // The specific procedural rule, doctrine, or principle mentioned (quoted if possible)
  "effect_on_courts_decision_or_case_handling": str,  // Describe how the Board applied this rule or why it mattered procedurally
}}

Guidelines:
- Include only procedural rules — i.e., those governing how the case is handled, not what the outcome should be based on the facts or law.
- DO include: rules about burdens of proof, timeliness, jurisdiction, claim sufficiency, standards for summary judgment, requirements for documentation, appeal scope, or evidence admissibility if procedural in nature.
- DO NOT include: substantive contract doctrines, FAR economic adjustment clauses, or damages formulas like the Eichleay formula (those belong in the substantive rules section).
- If a procedural rule is cited with reference to a regulation (e.g., “Board Rule 26”), include the citation in `procedural_rule_cited`.
- If the rule is procedural but mentioned only in passing and not applied by the Board, exclude it.

Return only valid JSON — no notes or commentary outside the array.
"""


SUBSTANTIVE_RULES_EXTRACTION_PROMPT= """
From the following document (which may be a court decision, order, or dismissal), extract all substantive rules of law or contract principles that the Board relied on—explicitly or implicitly—to decide the case.

Return a valid JSON array of objects. Each object must follow this structure:
{{
  "principle_of_substantive_law": str,  // A concise restatement of the rule or doctrine (e.g., "Constructive Suspension Doctrine", "FAR 52.242-14 Suspension of Work clause", or "Eichleay Formula for Damages")
  "facts_making_principle_applicable": str,  // The specific facts or circumstances in this case that made this principle relevant or triggered its application
  "how_principle_and_facts_were_crucial_to_the_decision": str  // How the Board applied the principle to those facts, including whether it supported or defeated a claim
}}

Guidelines:
- Include all **contract doctrines** the Board relied on, including interpretations of **contract clauses**, **scope of work**, and **agreed limitations** (e.g., bird nesting restrictions).
- Include all **legal standards** used to evaluate entitlement, damages, causation, concurrency, or burden of proof (e.g., Eichleay formula, constructive suspension).
- Include principles even if **not labeled as legal rules** in the text — if the Board applied the logic of a rule or doctrine, extract it.
- DO NOT include **procedural rules** (e.g., summary judgment standards, motion deadlines, burden-shifting rules) — these belong in a separate extraction.
- If the same rule appears in multiple forms (e.g., FAR clause + constructive suspension), extract each application distinctly if they involve different reasoning.

Be concise but complete. Return only valid JSON — no explanations or commentary outside the array.
"""



