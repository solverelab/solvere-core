import yaml
import os
from datetime import date
from core.models.case import (
    Case, CaseOutcome, DecisionStep, Violation, Severity
)


class NormEngine:

    def __init__(self, rules_path: str):
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, rules_path: str) -> list[dict]:
        rules = []
        for root, dirs, files in os.walk(rules_path):
            for file in files:
                if file.endswith(".yaml"):
                    with open(os.path.join(root, file), encoding="utf-8") as f:
                        rules.append(yaml.safe_load(f))
        return rules

    def evaluate(self, case: Case) -> CaseOutcome:
        applicable = self._select_applicable_rules(case)
        steps = []
        all_violations = []

        for i, rule in enumerate(applicable):
            step = self._evaluate_rule(rule, case.facts)
            step.step_number = i + 1
            steps.append(step)
            all_violations.extend(step.violations)

        valid = not any(
            v.severity in [Severity.ERROR, Severity.BLOCKING]
            for v in all_violations
        )

        return CaseOutcome(
            valid=valid,
            confidence=1.0,
            violations=all_violations,
            steps=steps,
            reasoning="",
            citations=self._extract_citations(applicable)
        )

    def _select_applicable_rules(self, case: Case) -> list[dict]:
        result = []
        for rule in self.rules:
            conditions = rule.get("applicability", {}).get("conditions", [])
            match = True
            for cond in conditions:
                fact_val = case.facts.get(cond["fact"])
                if cond["operator"] == "equals":
                    if fact_val != cond["value"]:
                        match = False
            if match:
                result.append(rule)
        return result

    def _evaluate_rule(self, rule: dict, facts: dict) -> DecisionStep:
        violations = []
        calculated = {}

        for obligation in rule.get("obligations", []):
            ob_type = obligation.get("type")

            if ob_type == "minimum_balance":
                minimum = self._eval_formula(obligation["formula"], facts)
                calculated["minimum"] = minimum
                target_value = facts.get(obligation["target"], 0)
                if (target_value or 0) < minimum:
                    violations.append(Violation(
                        rule_id=rule["id"],
                        severity=Severity(rule["violation"]["severity"]),
                        message=rule["violation"]["message_et"],
                        remedy=rule["violation"].get("remedy_et")
                    ))

            elif ob_type == "area_sum_positive":
                total_area = facts.get("total_area_included", 0)
                if (total_area or 0) <= 0:
                    violations.append(Violation(
                        rule_id=rule["id"],
                        severity=Severity(rule["violation"]["severity"]),
                        message=rule["violation"]["message_et"],
                        remedy=rule["violation"].get("remedy_et")
                    ))

            elif ob_type == "balance_check":
                running = facts.get("running_costs_planned", 0)
                invest = facts.get("invest_costs_planned", 0)
                income = facts.get("total_income", 0)
                result = (income or 0) - (running or 0) - (invest or 0)
                calculated["budget_result"] = result
                if result < 0:
                    violations.append(Violation(
                        rule_id=rule["id"],
                        severity=Severity(rule["violation"]["severity"]),
                        message=rule["violation"]["message_et"],
                        remedy=rule["violation"].get("remedy_et")
                    ))

        return DecisionStep(
            step_number=0,
            rule_id=rule["id"],
            rule_title=rule.get("title", ""),
            facts_used=facts,
            result=len(violations) == 0,
            calculated=calculated,
            violations=violations
        )

    def _eval_formula(self, formula: str, facts: dict) -> float:
        try:
            return eval(formula, {"__builtins__": {}}, facts)
        except Exception:
            return 0.0

    def _extract_citations(self, rules: list[dict]) -> list[str]:
        return [rule.get("source_text", "") for rule in rules if rule.get("source_text")]