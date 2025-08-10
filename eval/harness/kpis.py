# eval/harness/kpis.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class KPIResult:
    total_checks: int
    passed_checks: int
    factual_failures: int
    compliance_failures: int
    rfi: float
    edr: float
    ncs: float

def compute_kpis(check_results: list[dict], risk_weight: float = 1.0) -> KPIResult:
    """
    Heurística mínima:
    - factual_failures: checks de tipo equals / approx_equals / not_null / regex fallidos
    - compliance_failures: contains/contains_if fallidos y cualquier required_if fallido
    - RFI ~ (factual_failures * risk_weight) / total_checks
    - EDR ~ 1 - (required_if_fails / max(1, required_if_total))  (proxy)
    - NCS ~ compliance_passes - compliance_failures (proxy simple)
    """
    total = len(check_results)
    passed = sum(1 for r in check_results if r["passed"])

    factual_types = {"equals", "approx_equals", "not_null", "regex"}
    compliance_types = {"contains", "contains_if", "required_if"}

    factual_fail = sum(1 for r in check_results if (r["type"] in factual_types and not r["passed"]))
    compliance_fail = sum(1 for r in check_results if (r["type"] in compliance_types and not r["passed"]))

    req_total = sum(1 for r in check_results if r["type"] == "required_if")
    req_fail = sum(1 for r in check_results if r["type"] == "required_if" and not r["passed"])

    rfi = (factual_fail * risk_weight) / total if total else 0.0
    edr = 1.0 - (req_fail / req_total) if req_total else 1.0
    ncs = (sum(1 for r in check_results if r["type"] in compliance_types and r["passed"])) - compliance_fail

    return KPIResult(total, passed, factual_fail, compliance_fail, rfi, edr, ncs)

