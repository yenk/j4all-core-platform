from pydantic import BaseModel


class Fact(BaseModel):
    id: int
    specific_fact_cited: str
    relevancy_reason: str
    contestability_reason: str


class ProceduralRule(BaseModel):
    procedural_rule: str
    effects: str


class SubstantiveRule(BaseModel):
    substantive_law: str
    applicability: str
    relevance: str


class FactsExtractionOutput(BaseModel):
    facts: list[Fact]


class ProceduralRulesOutput(BaseModel):
    rules: list[ProceduralRule]


class SubstantiveRulesOutput(BaseModel):
    rules: list[SubstantiveRule]


class FactsAndRulesOutput(BaseModel):
    facts: FactsExtractionOutput
    procedural_rules: ProceduralRulesOutput
    substantive_rules: SubstantiveRulesOutput


class ProceduralRuleScore(BaseModel):
    procedural_rule: str
    doctrinal_fit: int
    fact_match: int
    party_assertion: int
    precedent_alignment: int
    rationale: str


class AdmissibilityScoringInput(BaseModel):
    facts: FactsExtractionOutput
    procedural_rules: ProceduralRulesOutput
    qa: str


class AdmissibilityScoringOutput(BaseModel):
    scores: list[ProceduralRuleScore]


class SubstantiveRuleScore(BaseModel):
    substantive_law: str
    doctrinal_fit: int
    fact_match: int
    party_assertion: int
    precedent_alignment: int
    rationale: str


class RelevanceScoringOutput(BaseModel):
    scores: list[SubstantiveRuleScore]


class RelevanceScoringInput(BaseModel):
    facts: FactsExtractionOutput
    substantive_rules: SubstantiveRulesOutput
    qa: str


class RuleScoreSummary(BaseModel):
    rule: str
    rule_score: float
    rationale: str


class CombinedScoreSummary(BaseModel):
    admissible_rules_summary: list[RuleScoreSummary]
    relevance_rules_summary: list[RuleScoreSummary]
    total_admissibility_score: float
    total_relevance_score: float
