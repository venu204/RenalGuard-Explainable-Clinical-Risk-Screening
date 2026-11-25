"""Clinical Rule Engine + ICRRI Risk Engine."""
from __future__ import annotations
import operator as op_module
from pathlib import Path
from typing import Any
import yaml

_RULE_FILE = Path(__file__).parent / "clinical_rules.yaml"
_OPS = {">": op_module.gt, ">=": op_module.ge, "<": op_module.lt, "<=": op_module.le, "==": op_module.eq}

def _load_rules() -> list[dict]:
    with _RULE_FILE.open() as f:
        return [r for r in yaml.safe_load(f).get("rules", []) if r.get("enabled", True)]

_RULES = _load_rules()

def evaluate_rules(measurements: dict[str, Any]) -> list[dict]:
    """Returns list of triggered alert dicts sorted by severity."""
    order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "LOW": 3, "INFORMATIONAL": 4}
    triggered = []
    for rule in _RULES:
        val = measurements.get(rule["parameter"])
        if val is None:
            continue
        try:
            val_f = float(val)
        except (TypeError, ValueError):
            continue
        fn = _OPS.get(rule["operator"])
        if fn and fn(val_f, rule["threshold"]):
            triggered.append({
                "rule_id": rule["rule_id"],
                "severity": rule["severity"],
                "title": rule["title"],
                "message": rule["message"],
                "suggested_action": rule.get("suggested_action", ""),
                "parameter": rule["parameter"],
                "value": val_f,
            })
    triggered.sort(key=lambda a: order.get(a["severity"], 99))
    return triggered


# ── ICRRI Risk Engine ──────────────────────────────────────────────────────────
WEIGHTS = {"ckd": 0.40, "diabetes": 0.30, "hypertension": 0.30}
INTERACTION = {"ckd_diabetes": 0.05, "ckd_hypertension": 0.05, "diabetes_hypertension": 0.03}
MAX_POSSIBLE = sum(WEIGHTS.values()) + sum(INTERACTION.values())

def compute_icrri(ckd: float, diabetes: float, hypertension: float) -> tuple[float, str, dict]:
    """Returns (icrri 0-100, risk_category, weights_used)."""
    base = WEIGHTS["ckd"] * ckd + WEIGHTS["diabetes"] * diabetes + WEIGHTS["hypertension"] * hypertension
    interaction = 0.0
    if ckd > 0.5 and diabetes > 0.5:
        interaction += INTERACTION["ckd_diabetes"]
    if ckd > 0.5 and hypertension > 0.5:
        interaction += INTERACTION["ckd_hypertension"]
    if diabetes > 0.5 and hypertension > 0.5:
        interaction += INTERACTION["diabetes_hypertension"]
    icrri = round(min((base + interaction) / MAX_POSSIBLE, 1.0) * 100, 2)
    if icrri <= 34:
        category = "LOW"
    elif icrri <= 54:
        category = "MODERATE"
    elif icrri <= 74:
        category = "HIGH"
    else:
        category = "CRITICAL"
    return icrri, category, {"weights": WEIGHTS, "interaction": INTERACTION}
