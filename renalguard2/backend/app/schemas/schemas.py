from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class DoctorRegistrationRequest(BaseModel):
    """Public registration payload.  This route can create doctors only."""
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    role: str
    full_name: str

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2)
    password: str = Field(min_length=8)
    role: str = "DOCTOR"

class UserOut(BaseModel):
    id: int; email: str; full_name: str; role: str; is_active: bool; created_at: datetime
    model_config = {"from_attributes": True}

class PatientCreate(BaseModel):
    full_name: str = Field(min_length=2)
    date_of_birth: datetime
    gender: str
    contact_number: str | None = None

class PatientOut(BaseModel):
    id: int; patient_code: str; full_name: str; date_of_birth: datetime
    gender: str; contact_number: str | None; doctor_id: int; created_at: datetime
    model_config = {"from_attributes": True}

class MeasurementInput(BaseModel):
    age: float = Field(ge=0, le=120)
    gender_enc: int = Field(ge=0, le=1)
    bmi: float | None = Field(default=None, ge=10, le=80)
    systolic_bp: float | None = Field(default=None, ge=60, le=250)
    diastolic_bp: float | None = Field(default=None, ge=40, le=160)
    glucose: float | None = Field(default=None, ge=50, le=600)
    hba1c: float | None = Field(default=None, ge=3, le=20)
    creatinine: float | None = Field(default=None, ge=0.1, le=20)
    hemoglobin: float | None = Field(default=None, ge=3, le=25)
    potassium: float | None = Field(default=None, ge=1, le=9)
    sodium: float | None = Field(default=None, ge=100, le=180)
    urea: float | None = Field(default=None, ge=0, le=500)
    albumin: float | None = Field(default=None, ge=0, le=10)
    smoking: bool | None = None
    family_history_hypertension: bool | None = None
    family_history_diabetes: bool | None = None
    family_history_ckd: bool | None = None
    notes: str | None = None

class AssessmentRequest(BaseModel):
    patient_id: int
    measurements: MeasurementInput

class SimulationRequest(BaseModel):
    visit_id: int
    scenario_inputs: MeasurementInput

class DashboardStats(BaseModel):
    total_patients: int
    todays_assessments: int
    high_risk_patients: int
    critical_alerts: int
    risk_distribution: dict[str, int]
