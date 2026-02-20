from dataclasses import dataclass, field
from datetime import date
from typing import Any
from enum import Enum


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKING = "blocking"


@dataclass
class Violation:
    rule_id: str
    severity: Severity
    message: str
    remedy: str | None = None


@dataclass
class DecisionStep:
    step_number: int
    rule_id: str
    rule_title: str
    facts_used: dict[str, Any]
    result: bool
    calculated: dict[str, Any]
    violations: list[Violation] = field(default_factory=list)


@dataclass
class CaseOutcome:
    valid: bool
    confidence: float
    violations: list[Violation]
    steps: list[DecisionStep]
    reasoning: str
    citations: list[str]


@dataclass
class Case:
    case_id: str
    domain: str
    jurisdiction: str
    evaluation_date: date
    facts: dict[str, Any]
    applicable_rules: list[str]
    outcome: CaseOutcome | None = None