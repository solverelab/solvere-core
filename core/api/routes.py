from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
import uuid

from core.models.case import Case
from core.engine.norm_engine import NormEngine

app = FastAPI(title="Solvere Core API")

norm_engine = NormEngine(rules_path="rules")


class EvaluationRequest(BaseModel):
    domain: str
    jurisdiction: str
    facts: dict
    audience: str = "general"


class ViolationOut(BaseModel):
    rule_id: str
    severity: str
    message: str
    remedy: str | None = None


class EvaluationResponse(BaseModel):
    case_id: str
    valid: bool
    confidence: float
    violations: list[ViolationOut]
    citations: list[str]
    reasoning: str


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest):
    case = Case(
        case_id=str(uuid.uuid4()),
        domain=request.domain,
        jurisdiction=request.jurisdiction,
        evaluation_date=date.today(),
        facts=request.facts,
        applicable_rules=[],
    )

    outcome = norm_engine.evaluate(case)

    return EvaluationResponse(
        case_id=case.case_id,
        valid=outcome.valid,
        confidence=outcome.confidence,
        violations=[
            ViolationOut(
                rule_id=v.rule_id,
                severity=v.severity.value,
                message=v.message,
                remedy=v.remedy,
            )
            for v in outcome.violations
        ],
        citations=outcome.citations,
        reasoning=outcome.reasoning,
    )


@app.get("/health")
async def health():
    return {"status": "ok", "rules_loaded": len(norm_engine.rules)}