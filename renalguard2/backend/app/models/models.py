from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum

class UserRole(str, enum.Enum):
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"

class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class RiskCategory(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AlertSeverity(str, enum.Enum):
    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

def _now(): return datetime.utcnow()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.DOCTOR)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)
    patients = relationship("Patient", back_populates="doctor")
    audit_logs = relationship("AuditLog", back_populates="user")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(SAEnum(Gender), nullable=False)
    contact_number = Column(String(20))
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)
    doctor = relationship("User", back_populates="patients")
    visits = relationship("PatientVisit", back_populates="patient", order_by="PatientVisit.visit_date.desc()")

class PatientVisit(Base):
    __tablename__ = "patient_visits"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    visit_date = Column(DateTime, default=_now, nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=_now)
    patient = relationship("Patient", back_populates="visits")
    measurements = relationship("ClinicalMeasurement", back_populates="visit", uselist=False)
    predictions = relationship("Prediction", back_populates="visit")
    risk_score = relationship("RiskScore", back_populates="visit", uselist=False)
    alerts = relationship("Alert", back_populates="visit")

class ClinicalMeasurement(Base):
    __tablename__ = "clinical_measurements"
    id = Column(Integer, primary_key=True)
    visit_id = Column(Integer, ForeignKey("patient_visits.id"), unique=True, nullable=False)
    age = Column(Float)
    gender_enc = Column(Integer)
    bmi = Column(Float)
    systolic_bp = Column(Float)
    diastolic_bp = Column(Float)
    glucose = Column(Float)
    hba1c = Column(Float)
    creatinine = Column(Float)
    hemoglobin = Column(Float)
    potassium = Column(Float)
    sodium = Column(Float)
    urea = Column(Float)
    albumin = Column(Float)
    specific_gravity = Column(Float)
    smoking = Column(Boolean)
    family_history_hypertension = Column(Boolean)
    family_history_diabetes = Column(Boolean)
    family_history_ckd = Column(Boolean)
    visit = relationship("PatientVisit", back_populates="measurements")

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True)
    disease = Column(String(50), nullable=False)
    algorithm = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    training_dataset = Column(String(255))
    feature_list = Column(JSON)
    metrics = Column(JSON)
    artifact_path = Column(String(500))
    is_active = Column(Boolean, default=True)
    trained_at = Column(DateTime, default=_now)

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    visit_id = Column(Integer, ForeignKey("patient_visits.id"), nullable=False)
    model_version_id = Column(Integer, ForeignKey("model_versions.id"), nullable=True)
    disease = Column(String(50), nullable=False)
    raw_probability = Column(Float, nullable=False)
    calibrated_probability = Column(Float)
    threshold_used = Column(Float)
    predicted_class = Column(Integer)
    created_at = Column(DateTime, default=_now)
    visit = relationship("PatientVisit", back_populates="predictions")
    explanation = relationship("Explanation", back_populates="prediction", uselist=False)

class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True)
    visit_id = Column(Integer, ForeignKey("patient_visits.id"), unique=True, nullable=False)
    ckd_probability = Column(Float)
    diabetes_probability = Column(Float)
    hypertension_probability = Column(Float)
    icrri = Column(Float, nullable=False)
    risk_category = Column(SAEnum(RiskCategory), nullable=False)
    weights_config = Column(JSON)
    created_at = Column(DateTime, default=_now)
    visit = relationship("PatientVisit", back_populates="risk_score")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    visit_id = Column(Integer, ForeignKey("patient_visits.id"), nullable=False)
    rule_id = Column(String(50), nullable=False)
    severity = Column(SAEnum(AlertSeverity), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    suggested_action = Column(Text)
    parameter = Column(String(100))
    value = Column(Float)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now)
    visit = relationship("PatientVisit", back_populates="alerts")

class Explanation(Base):
    __tablename__ = "explanations"
    id = Column(Integer, primary_key=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), unique=True)
    shap_values = Column(JSON)
    top_contributors = Column(JSON)
    plain_language = Column(Text)
    created_at = Column(DateTime, default=_now)
    prediction = relationship("Prediction", back_populates="explanation")

class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    id = Column(Integer, primary_key=True)
    visit_id = Column(Integer, ForeignKey("patient_visits.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scenario_inputs = Column(JSON, nullable=False)
    baseline_icrri = Column(Float)
    simulated_icrri = Column(Float)
    delta_icrri = Column(Float)
    scenario_predictions = Column(JSON)
    created_at = Column(DateTime, default=_now)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    patient_id = Column(Integer, nullable=True)
    resource = Column(String(255))
    result = Column(String(20))
    details = Column(JSON)
    timestamp = Column(DateTime, default=_now, nullable=False)
    user = relationship("User", back_populates="audit_logs")
