"""
Seed script — creates demo accounts, synthetic patients, visits, and model records.

Run from project root:
    python scripts/seed_db.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from datetime import datetime, timedelta
from app.db.session import SessionLocal, engine
from app.models.models import (
    Base, User, UserRole, Patient, Gender, ModelVersion, PatientVisit,
    ClinicalMeasurement, RiskScore, Alert, RiskCategory, AlertSeverity,
)
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

USERS = [
    {"email": "admin@renalguard.dev",  "password": "Admin@1234",  "full_name": "RG Admin",        "role": UserRole.ADMIN},
    {"email": "doctor@renalguard.dev", "password": "Doctor@1234", "full_name": "Dr. Priya Sharma", "role": UserRole.DOCTOR},
]

MODEL_VERSIONS = [
    {"disease": "CKD",          "algorithm": "XGBoost", "version": "1.0.0",
     "training_dataset": "Kaggle Kidney Disease Dataset",
     "metrics": {"roc_auc": 0.97, "f1": 0.95, "accuracy": 0.97}},
    {"disease": "DIABETES",     "algorithm": "XGBoost", "version": "1.0.0",
     "training_dataset": "Kaggle Diabetes Prediction Dataset",
     "metrics": {"roc_auc": 0.96, "f1": 0.93, "accuracy": 0.96}},
    {"disease": "HYPERTENSION", "algorithm": "XGBoost", "version": "1.0.0",
     "training_dataset": "Kaggle Hypertension Risk Prediction Dataset",
     "metrics": {"roc_auc": 0.94, "f1": 0.91, "accuracy": 0.94}},
]


# Synthetic classroom data only. It is deliberately labelled and does not
# represent real people or clinical records.
SYNTHETIC_PATIENTS = [
    {
        "code": "DEMO-LOW-001", "name": "[SYNTHETIC] Kavya N. — Stable low risk",
        "dob": datetime(1994, 4, 18), "gender": Gender.FEMALE,
        "visits": [
            {"days": 60, "icrri": 18.1, "category": RiskCategory.LOW, "probs": (0.10, 0.14, 0.18),
             "m": {"age": 32, "gender_enc": 0, "bmi": 22.4, "systolic_bp": 112, "diastolic_bp": 72, "glucose": 88, "hba1c": 5.1, "creatinine": 0.8, "hemoglobin": 12.9, "potassium": 4.1, "sodium": 140, "urea": 22, "albumin": 4.2, "smoking": False}},
            {"days": 30, "icrri": 18.7, "category": RiskCategory.LOW, "probs": (0.11, 0.15, 0.18),
             "m": {"age": 32, "gender_enc": 0, "bmi": 22.5, "systolic_bp": 114, "diastolic_bp": 73, "glucose": 90, "hba1c": 5.2, "creatinine": 0.8, "hemoglobin": 12.8, "potassium": 4.2, "sodium": 140, "urea": 23, "albumin": 4.2, "smoking": False}},
            {"days": 0, "icrri": 18.4, "category": RiskCategory.LOW, "probs": (0.10, 0.15, 0.18),
             "m": {"age": 32, "gender_enc": 0, "bmi": 22.5, "systolic_bp": 113, "diastolic_bp": 72, "glucose": 89, "hba1c": 5.1, "creatinine": 0.8, "hemoglobin": 12.9, "potassium": 4.1, "sodium": 140, "urea": 22, "albumin": 4.2, "smoking": False}},
        ],
    },
    {
        "code": "DEMO-MOD-001", "name": "[SYNTHETIC] Rohan P. — Moderate risk",
        "dob": datetime(1978, 11, 5), "gender": Gender.MALE,
        "visits": [
            {"days": 28, "icrri": 47.2, "category": RiskCategory.MODERATE, "probs": (0.34, 0.42, 0.51),
             "m": {"age": 47, "gender_enc": 1, "bmi": 28.7, "systolic_bp": 136, "diastolic_bp": 87, "glucose": 119, "hba1c": 6.0, "creatinine": 1.1, "hemoglobin": 13.5, "potassium": 4.4, "sodium": 139, "urea": 31, "albumin": 3.9, "smoking": False}},
            {"days": 0, "icrri": 48.4, "category": RiskCategory.MODERATE, "probs": (0.35, 0.43, 0.52),
             "m": {"age": 47, "gender_enc": 1, "bmi": 28.9, "systolic_bp": 138, "diastolic_bp": 88, "glucose": 121, "hba1c": 6.1, "creatinine": 1.1, "hemoglobin": 13.5, "potassium": 4.4, "sodium": 139, "urea": 32, "albumin": 3.9, "smoking": False}},
        ],
    },
    {
        "code": "DEMO-HIGH-001", "name": "[SYNTHETIC] Meera S. — High risk",
        "dob": datetime(1963, 2, 27), "gender": Gender.FEMALE,
        "visits": [
            {"days": 56, "icrri": 60.5, "category": RiskCategory.HIGH, "probs": (0.58, 0.63, 0.61),
             "m": {"age": 63, "gender_enc": 0, "bmi": 31.2, "systolic_bp": 154, "diastolic_bp": 94, "glucose": 168, "hba1c": 7.7, "creatinine": 1.6, "hemoglobin": 11.2, "potassium": 4.7, "sodium": 137, "urea": 48, "albumin": 3.5, "smoking": False}},
            {"days": 21, "icrri": 66.8, "category": RiskCategory.HIGH, "probs": (0.64, 0.69, 0.67),
             "m": {"age": 63, "gender_enc": 0, "bmi": 31.4, "systolic_bp": 164, "diastolic_bp": 98, "glucose": 184, "hba1c": 8.1, "creatinine": 1.8, "hemoglobin": 10.9, "potassium": 5.0, "sodium": 136, "urea": 57, "albumin": 3.4, "smoking": False}},
            {"days": 0, "icrri": 72.1, "category": RiskCategory.HIGH, "probs": (0.70, 0.73, 0.72),
             "m": {"age": 63, "gender_enc": 0, "bmi": 31.5, "systolic_bp": 172, "diastolic_bp": 102, "glucose": 196, "hba1c": 8.6, "creatinine": 2.0, "hemoglobin": 10.5, "potassium": 5.2, "sodium": 135, "urea": 68, "albumin": 3.3, "smoking": False},
             "alerts": [("HTN_001", AlertSeverity.HIGH, "High blood pressure", "Blood pressure is elevated in this synthetic example.", "Review promptly in an appropriate clinical setting.", "systolic_bp", 172.0)]},
        ],
    },
]


# Larger synthetic portfolio for classroom demonstrations. Every generated
# patient has exactly five visits with a clearly defined trajectory.
DEMO_DOCTORS = [
    {"email": f"doctor{number:02d}@renalguard.dev", "password": f"Doctor{number:02d}@1234",
     "full_name": f"Dr. {name}", "role": UserRole.DOCTOR}
    for number, name in enumerate([
        "Aarav Mehta", "Ananya Rao", "Vikram Iyer", "Nisha Kapoor", "Arjun Nair",
        "Sneha Patel", "Rahul Menon", "Divya Shah", "Kiran Joshi", "Maya Reddy",
    ], start=1)
]
FIRST_NAMES = ["Aditi", "Ravi", "Neha", "Sanjay", "Isha", "Karthik", "Pooja", "Manoj", "Anika", "Vivek", "Tara", "Rohan", "Meera", "Aditya", "Kavya", "Nikhil", "Priya", "Arun", "Sana", "Dev"]
LAST_NAMES = ["Sharma", "Verma", "Singh", "Kumar", "Gupta", "Das", "Bose", "Malik", "Jain", "Khanna"]
TRAJECTORIES = {
    "WORSENING": [31.0, 42.0, 55.0, 68.0, 81.0],
    "IMPROVING": [79.0, 65.0, 52.0, 41.0, 29.0],
    "STABLE": [46.0, 47.5, 45.5, 46.8, 47.0],
}


def risk_category(score: float) -> RiskCategory:
    if score <= 34: return RiskCategory.LOW
    if score <= 54: return RiskCategory.MODERATE
    if score <= 74: return RiskCategory.HIGH
    return RiskCategory.CRITICAL


def synthetic_measurements(score: float, age: int, gender_enc: int, visit_index: int) -> dict:
    """Derive clinically plausible *synthetic* measurements from a demo score."""
    variation = (visit_index - 2) * 0.35
    return {
        "age": age, "gender_enc": gender_enc,
        "bmi": round(21.5 + score * 0.12 + variation, 1),
        "systolic_bp": round(108 + score * 0.78 + variation),
        "diastolic_bp": round(68 + score * 0.38 + variation),
        "glucose": round(82 + score * 1.38 + variation),
        "hba1c": round(4.9 + score * 0.048, 1),
        "creatinine": round(0.65 + score * 0.018, 1),
        "hemoglobin": round(14.4 - score * 0.045, 1),
        "potassium": round(3.9 + score * 0.016, 1),
        "sodium": round(141 - score * 0.065),
        "urea": round(18 + score * 0.75),
        "albumin": round(4.5 - score * 0.016, 1),
        "smoking": score >= 68 and gender_enc == 1,
        "family_history_hypertension": score >= 45,
        "family_history_diabetes": score >= 52,
        "family_history_ckd": score >= 62,
    }


def seed_portfolio_patients(db, doctor, doctor_number: int):
    """Create 20 synthetic patients, each with five fixed historical visits."""
    now = datetime.utcnow()
    for patient_number in range(1, 21):
        code = f"RGD{doctor_number:02d}-P{patient_number:03d}"
        trajectory = ("WORSENING", "IMPROVING", "STABLE")[(patient_number - 1) % 3]
        patient = db.query(Patient).filter(Patient.patient_code == code).first()
        gender = Gender.FEMALE if patient_number % 2 else Gender.MALE
        gender_enc = 0 if gender == Gender.FEMALE else 1
        age = 28 + ((doctor_number * 7 + patient_number * 3) % 46)
        if not patient:
            patient = Patient(
                patient_code=code,
                full_name=f"[SYNTHETIC] {FIRST_NAMES[(doctor_number + patient_number) % len(FIRST_NAMES)]} {LAST_NAMES[(doctor_number * 2 + patient_number) % len(LAST_NAMES)]} — {trajectory.title()}",
                date_of_birth=now - timedelta(days=age * 365 + patient_number * 13),
                gender=gender,
                doctor_id=doctor.id,
                contact_number=f"900{doctor_number:02d}{patient_number:05d}",
            )
            db.add(patient)
            db.flush()

        # Idempotent: an existing generated patient never receives duplicate visits.
        if db.query(PatientVisit).filter(PatientVisit.patient_id == patient.id).count() > 0:
            continue
        for visit_index, score in enumerate(TRAJECTORIES[trajectory]):
            visit = PatientVisit(
                patient_id=patient.id, doctor_id=doctor.id,
                visit_date=now - timedelta(days=(4 - visit_index) * 28),
                notes=f"Synthetic {trajectory.lower()} trajectory, visit {visit_index + 1} of 5 — academic demo only.",
            )
            db.add(visit)
            db.flush()
            db.add(ClinicalMeasurement(
                visit_id=visit.id,
                **synthetic_measurements(score, age, gender_enc, visit_index),
            ))
            ckd = round(min(0.94, score / 100 * 0.96), 3)
            diabetes = round(min(0.94, score / 100 * 0.91), 3)
            hypertension = round(min(0.94, score / 100 * 0.98), 3)
            db.add(RiskScore(
                visit_id=visit.id, ckd_probability=ckd, diabetes_probability=diabetes,
                hypertension_probability=hypertension, icrri=score,
                risk_category=risk_category(score),
                weights_config={"source": "synthetic-portfolio", "trajectory": trajectory},
            ))
            if score >= 75:
                db.add(Alert(
                    visit_id=visit.id, rule_id="SYNTHETIC_RISK_REVIEW",
                    severity=AlertSeverity.CRITICAL, title="Synthetic high-risk review",
                    message="Synthetic training record flagged for qualified review.",
                    suggested_action="Use this demonstration profile only for academic workflow testing.",
                    parameter="icrri", value=score,
                ))


def seed_synthetic_patients(db, doctor):
    """Add idempotent, clearly labelled data for dashboard and history demos."""
    now = datetime.utcnow()
    for item in SYNTHETIC_PATIENTS:
        patient = db.query(Patient).filter(Patient.patient_code == item["code"]).first()
        if not patient:
            patient = Patient(patient_code=item["code"], full_name=item["name"],
                              date_of_birth=item["dob"], gender=item["gender"], doctor_id=doctor.id)
            db.add(patient)
            db.flush()
        if db.query(PatientVisit).filter(PatientVisit.patient_id == patient.id).first():
            continue
        for data in item["visits"]:
            visit = PatientVisit(patient_id=patient.id, doctor_id=doctor.id,
                                 visit_date=now - timedelta(days=data["days"]),
                                 notes="Synthetic demonstration record — not clinical data.")
            db.add(visit)
            db.flush()
            db.add(ClinicalMeasurement(visit_id=visit.id, **data["m"]))
            ckd, diabetes, hypertension = data["probs"]
            db.add(RiskScore(visit_id=visit.id, ckd_probability=ckd,
                             diabetes_probability=diabetes, hypertension_probability=hypertension,
                             icrri=data["icrri"], risk_category=data["category"],
                             weights_config={"source": "synthetic-demo"}))
            for alert in data.get("alerts", []):
                rule_id, severity, title, message, action, parameter, value = alert
                db.add(Alert(visit_id=visit.id, rule_id=rule_id, severity=severity,
                             title=title, message=message, suggested_action=action,
                             parameter=parameter, value=value))

def seed():
    db = SessionLocal()
    try:
        # Users
        for u in USERS:
            if not db.query(User).filter(User.email == u["email"]).first():
                db.add(User(email=u["email"], full_name=u["full_name"],
                            hashed_password=hash_password(u["password"]),
                            role=u["role"]))
        for doctor_data in DEMO_DOCTORS:
            if not db.query(User).filter(User.email == doctor_data["email"]).first():
                db.add(User(email=doctor_data["email"], full_name=doctor_data["full_name"],
                            hashed_password=hash_password(doctor_data["password"]),
                            role=doctor_data["role"]))
        db.flush()

        # Demo patient
        doctor = db.query(User).filter(User.email == "doctor@renalguard.dev").first()
        if doctor and not db.query(Patient).filter(Patient.patient_code == "DEMO-001").first():
            db.add(Patient(
                patient_code="DEMO-001",
                full_name="[SYNTHETIC] Demo Patient",
                date_of_birth=datetime(1969, 6, 15),
                gender=Gender.MALE,
                doctor_id=doctor.id,
            ))

        if doctor:
            seed_synthetic_patients(db, doctor)

        for number, doctor_data in enumerate(DEMO_DOCTORS, start=1):
            portfolio_doctor = db.query(User).filter(User.email == doctor_data["email"]).first()
            if portfolio_doctor:
                seed_portfolio_patients(db, portfolio_doctor, number)

        # Model versions
        for mv in MODEL_VERSIONS:
            if not db.query(ModelVersion).filter(
                ModelVersion.disease == mv["disease"],
                ModelVersion.version == mv["version"]
            ).first():
                db.add(ModelVersion(
                    disease=mv["disease"], algorithm=mv["algorithm"],
                    version=mv["version"], training_dataset=mv["training_dataset"],
                    metrics=mv["metrics"],
                    artifact_path=f"ml/models/{mv['disease'].lower()}_model.joblib",
                    is_active=True, trained_at=datetime.utcnow(),
                ))

        db.commit()
        print("\nDatabase seeded successfully with 10 synthetic doctors, 200 patients, and 1,000 five-visit histories.")
        print("   Admin:  admin@renalguard.dev  /  Admin@1234")
        print("   Doctor: doctor@renalguard.dev /  Doctor@1234\n")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
