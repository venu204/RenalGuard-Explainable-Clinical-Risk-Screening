"""ML inference service. Loads .joblib models and produces SHAP explanations."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import logging
import numpy as np
import joblib
import shap
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_DISEASE_CFG: dict[str, dict] = {
    "CKD": {
        "model": "ckd_model.joblib",
        "preprocessor": "ckd_preprocessor.joblib",
        "threshold": 0.5,
        "features": ["age","gender_enc","bmi","systolic_bp","diastolic_bp",
                     "glucose","creatinine","hemoglobin","potassium","sodium","urea","albumin"],
    },
    "DIABETES": {
        "model": "diabetes_model.joblib",
        "preprocessor": "diabetes_preprocessor.joblib",
        "threshold": 0.5,
        "features": ["age","gender_enc","bmi","hba1c","glucose","systolic_bp",
                     "smoking","family_history_diabetes"],
    },
    "HYPERTENSION": {
        "model": "hypertension_model.joblib",
        "preprocessor": "hypertension_preprocessor.joblib",
        "threshold": 0.5,
        "features": ["age","gender_enc","bmi","systolic_bp","diastolic_bp",
                     "glucose","smoking","family_history_hypertension"],
    },
}

_cache: dict[str, Any] = {}

def _get(disease: str) -> tuple[Any, Any]:
    if disease not in _cache:
        cfg = _DISEASE_CFG[disease]
        base = Path(settings.MODEL_DIR)
        _cache[f"{disease}_model"] = joblib.load(base / cfg["model"])
        _cache[f"{disease}_prep"] = joblib.load(base / cfg["preprocessor"])
    return _cache[f"{disease}_model"], _cache[f"{disease}_prep"]

def predict(disease: str, measurements: dict[str, Any]) -> dict[str, Any]:
    cfg = _DISEASE_CFG[disease]
    model, prep = _get(disease)
    features = cfg["features"]
    raw = np.array([
        float(measurements.get(f, np.nan)) if not isinstance(measurements.get(f), bool)
        else int(measurements.get(f))
        for f in features
    ], dtype=float).reshape(1, -1)
    X = prep.transform(raw)
    prob = float(model.predict_proba(X)[0, 1])
    predicted = int(prob >= cfg["threshold"])
    explanation = _explain(model, X, features, raw[0])
    return {
        "disease": disease,
        "probability": round(prob, 4),
        "predicted_class": predicted,
        "threshold": cfg["threshold"],
        "explanation": explanation,
    }

def _explain(model: Any, X: np.ndarray, features: list[str], raw_vals: np.ndarray) -> dict:
    try:
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X)
        sv = sv[1][0] if isinstance(sv, list) else sv[0]
        contribs = sorted([
            {"feature": f, "shap_value": round(float(v), 4),
             "raw_value": None if np.isnan(raw_vals[i]) else round(float(raw_vals[i]), 3),
             "direction": "positive" if v > 0 else "negative"}
            for i, (f, v) in enumerate(zip(features, sv))
        ], key=lambda x: abs(x["shap_value"]), reverse=True)
        plain = _plain(contribs[:5])
        return {"top_contributors": contribs[:5], "plain_language": plain}
    except Exception as e:
        logger.warning("SHAP explanation failed: %s", e)
        return {"top_contributors": [], "plain_language": "Explanation unavailable."}

def _plain(contribs: list[dict]) -> str:
    lines = ["Top model contributors (not causal statements):"]
    for c in contribs:
        d = "increased" if c["direction"] == "positive" else "decreased"
        v = f" = {c['raw_value']}" if c["raw_value"] is not None else ""
        lines.append(f"  • {c['feature'].replace('_',' ').title()}{v} → {d} estimated risk")
    return "\n".join(lines)
