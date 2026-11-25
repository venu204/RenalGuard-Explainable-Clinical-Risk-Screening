"""All business logic services."""
from __future__ import annotations
from datetime import datetime, date
import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.models import (
    User, Patient, PatientVisit, ClinicalMeasurement,
    Prediction, RiskScore, Alert, Explanation, SimulationRun,
    ModelVersion, AuditLog, UserRole, RiskCategory, AlertSeverity
)
from app.core.security import hash_password
from app.clinical.engines import evaluate_rules, compute_icrri
from app.ml.inference import predict

logger = logging.getLogger(__name__)

_DISEASES = ["CKD", "DIABETES", "HYPERTENSION"]

# ── Audit ──────────────────────────────────────────────────────────────────────
def log_action(db: Session, action: str, user_id: int | None = None,
               patient_id: int | None = None, result: str = "SUCCESS", details: dict | None = None):
    db.add(AuditLog(user_id=user_id, action=action, patient_id=patient_id,
                    result=result, details=details))
    db.commit()

# ── Auth ───────────────────────────────────────────────────────────────────────
def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, email: str, full_name: str, password: str, role: str = "DOCTOR") -> User:
    user = User(email=email, full_name=full_name,
                hashed_password=hash_password(password), role=UserRole(role))
    db.add(user); db.commit(); db.refresh(user)
    return user

# ── Patient ────────────────────────────────────────────────────────────────────
def _gen_code(db: Session) -> str:
    return f"RG-{10001 + db.query(Patient).count()}"

def create_patient(db: Session, data: dict, doctor_id: int) -> Patient:
    p = Patient(patient_code=_gen_code(db), doctor_id=doctor_id, **data)
    db.add(p); db.commit(); db.refresh(p)
    return p

def get_patient(db: Session, patient_id: int) -> Patient | None:
    return db.query(Patient).filter(Patient.id == patient_id, Patient.is_active == True).first()

def list_patients(db: Session, doctor_id: int | None = None) -> list[Patient]:
    q = db.query(Patient).filter(Patient.is_active == True)
    if doctor_id:
        q = q.filter(Patient.doctor_id == doctor_id)
    return q.order_by(Patient.created_at.desc()).all()

def get_patient_history(db: Session, patient_id: int) -> list[dict]:
    visits = (
        db.query(PatientVisit)
        .options(joinedload(PatientVisit.risk_score), joinedload(PatientVisit.measurements))
        .filter(PatientVisit.patient_id == patient_id)
        .order_by(PatientVisit.visit_date.asc())
        .all()
    )
    points = []
    for v in visits:
        rs = v.risk_score; m = v.measurements
        points.append({
            "visit_id": v.id, "visit_date": v.visit_date,
            "icrri": rs.icrri if rs else None,
            "risk_category": rs.risk_category.value if rs else None,
            "ckd": rs.ckd_probability if rs else None,
            "diabetes": rs.diabetes_probability if rs else None,
            "hypertension": rs.hypertension_probability if rs else None,
            "systolic_bp": m.systolic_bp if m else None,
            "diastolic_bp": m.diastolic_bp if m else None,
            "age": m.age if m else None,
            "gender_enc": m.gender_enc if m else None,
            "bmi": m.bmi if m else None,
            "glucose": m.glucose if m else None,
            "creatinine": m.creatinine if m else None,
            "hba1c": m.hba1c if m else None,
            "hemoglobin": m.hemoglobin if m else None,
            "potassium": m.potassium if m else None,
            "sodium": m.sodium if m else None,
            "urea": m.urea if m else None,
            "albumin": m.albumin if m else None,
            "smoking": m.smoking if m else None,
            "family_history_hypertension": m.family_history_hypertension if m else None,
            "family_history_diabetes": m.family_history_diabetes if m else None,
            "family_history_ckd": m.family_history_ckd if m else None,
            "notes": v.notes,
        })
    icrri_vals = [p["icrri"] for p in points if p["icrri"] is not None]
    trend = _trend(icrri_vals)
    return {"visits": points, "trend": trend, "count": len(points)}

def _trend(vals: list[float]) -> str | None:
    if len(vals) < 2: return None
    recent = vals[-3:]
    avg = sum(recent[i+1]-recent[i] for i in range(len(recent)-1)) / (len(recent)-1)
    return "IMPROVING" if avg < -2 else "WORSENING" if avg > 2 else "STABLE"

# ── Assessment ─────────────────────────────────────────────────────────────────
def run_assessment(db: Session, patient_id: int, measurements: dict, doctor_id: int) -> dict:
    notes = measurements.pop("notes", None)
    visit = PatientVisit(patient_id=patient_id, doctor_id=doctor_id,
                         visit_date=datetime.utcnow(), notes=notes)
    db.add(visit); db.flush()

    # Persist measurements
    meas_fields = {k: v for k, v in measurements.items()
                   if hasattr(ClinicalMeasurement, k) and v is not None}
    db.add(ClinicalMeasurement(visit_id=visit.id, **meas_fields)); db.flush()

    probs: dict[str, float] = {}
    predictions_out = []
    explanations_out = []

    for disease in _DISEASES:
        try:
            res = predict(disease, measurements)
            prob = res["probability"]
            probs[disease] = prob
            mv = db.query(ModelVersion).filter(
                ModelVersion.disease == disease, ModelVersion.is_active == True).first()
            pred = Prediction(visit_id=visit.id,
                              model_version_id=mv.id if mv else None,
                              disease=disease, raw_probability=prob,
                              calibrated_probability=prob,
                              threshold_used=res["threshold"],
                              predicted_class=res["predicted_class"])
            db.add(pred); db.flush()
            expl_data = res.get("explanation", {})
            if expl_data.get("top_contributors"):
                db.add(Explanation(prediction_id=pred.id,
                                   shap_values=None,
                                   top_contributors=expl_data["top_contributors"],
                                   plain_language=expl_data["plain_language"]))
            predictions_out.append({"disease": disease, "probability": prob,
                                     "predicted_class": res["predicted_class"]})
            explanations_out.append({"disease": disease, **expl_data})
        except FileNotFoundError:
            logger.warning(f"{disease} model not found — using 0.5 fallback")
            probs[disease] = 0.5
            predictions_out.append({"disease": disease, "probability": 0.5, "predicted_class": 0})
        except Exception as e:
            logger.error(f"Inference error {disease}: {e}")
            probs[disease] = 0.5

    icrri, category, weights = compute_icrri(
        probs.get("CKD", 0.5), probs.get("DIABETES", 0.5), probs.get("HYPERTENSION", 0.5))
    db.add(RiskScore(visit_id=visit.id,
                     ckd_probability=probs.get("CKD"),
                     diabetes_probability=probs.get("DIABETES"),
                     hypertension_probability=probs.get("HYPERTENSION"),
                     icrri=icrri, risk_category=RiskCategory(category),
                     weights_config=weights))

    alert_dicts = evaluate_rules(measurements)
    for a in alert_dicts:
        db.add(Alert(visit_id=visit.id, rule_id=a["rule_id"],
                     severity=AlertSeverity(a["severity"]),
                     title=a["title"], message=a["message"],
                     suggested_action=a.get("suggested_action"),
                     parameter=a.get("parameter"), value=a.get("value")))

    db.commit()
    return {"visit_id": visit.id, "predictions": predictions_out,
            "icrri": icrri, "risk_category": category, "weights": weights,
            "ckd_prob": probs.get("CKD", 0.5),
            "diabetes_prob": probs.get("DIABETES", 0.5),
            "hypertension_prob": probs.get("HYPERTENSION", 0.5),
            "alerts": alert_dicts, "explanations": explanations_out}

# ── Simulation ─────────────────────────────────────────────────────────────────
def run_simulation(db: Session, visit_id: int, scenario: dict, user_id: int) -> dict:
    visit = db.query(PatientVisit).filter(PatientVisit.id == visit_id).first()
    if not visit: raise ValueError("Visit not found")
    baseline_rs = visit.risk_score
    baseline_icrri = baseline_rs.icrri if baseline_rs else 0.0
    baseline_cat = baseline_rs.risk_category.value if baseline_rs else "LOW"

    sim_probs: dict[str, float] = {}
    for disease in _DISEASES:
        try:
            res = predict(disease, scenario)
            sim_probs[disease] = res["probability"]
        except Exception:
            sim_probs[disease] = 0.5

    sim_icrri, sim_cat, _ = compute_icrri(
        sim_probs.get("CKD", 0.5), sim_probs.get("DIABETES", 0.5), sim_probs.get("HYPERTENSION", 0.5))
    delta = round(sim_icrri - baseline_icrri, 2)

    db.add(SimulationRun(visit_id=visit_id, user_id=user_id,
                         scenario_inputs=scenario, baseline_icrri=baseline_icrri,
                         simulated_icrri=sim_icrri, delta_icrri=delta,
                         scenario_predictions=sim_probs))
    db.commit()
    return {"baseline_icrri": baseline_icrri, "simulated_icrri": sim_icrri,
            "delta": delta, "baseline_category": baseline_cat,
            "simulated_category": sim_cat, "scenario_probs": sim_probs}

# ── Dashboard ──────────────────────────────────────────────────────────────────
def get_dashboard_stats(db: Session) -> dict:
    total = db.query(Patient).filter(Patient.is_active == True).count()
    today = db.query(PatientVisit).filter(PatientVisit.visit_date >= date.today()).count()
    high = db.query(RiskScore).filter(
        RiskScore.risk_category.in_([RiskCategory.HIGH, RiskCategory.CRITICAL])).count()
    crits = db.query(Alert).filter(
        Alert.severity == AlertSeverity.CRITICAL, Alert.acknowledged == False).count()
    dist = dict(db.query(RiskScore.risk_category, func.count(RiskScore.id))
                .group_by(RiskScore.risk_category).all())
    return {"total_patients": total, "todays_assessments": today,
            "high_risk_patients": high, "critical_alerts": crits,
            "risk_distribution": {k.value: v for k, v in dist.items()}}
