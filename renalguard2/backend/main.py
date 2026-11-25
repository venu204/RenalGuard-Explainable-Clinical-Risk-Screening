"""An Explainable AI-Based Clinical Risk Screening System for CKD, Diabetes and Hypertension FastAPI Backend — all routes."""
from __future__ import annotations
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db, Base, engine
from app.models.models import User, UserRole, AuditLog, ModelVersion, PatientVisit
from app.core.security import verify_password, create_access_token, decode_token
from app.schemas.schemas import (
    DoctorRegistrationRequest, LoginRequest, TokenResponse, UserCreate, UserOut,
    PatientCreate, AssessmentRequest, SimulationRequest
)
from app.services.services import (
    get_user_by_email, get_user_by_id, create_user,
    create_patient, get_patient, list_patients, get_patient_history,
    run_assessment, run_simulation, get_dashboard_stats, log_action
)
from app.services.report import generate_pdf

app = FastAPI(
    title="An Explainable AI-Based Clinical Risk Screening System for CKD, Diabetes and Hypertension API",
    description="Academic clinical screening prototype — NOT for clinical use.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

# ── Auth dependency ────────────────────────────────────────────────────────────
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_id(db, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive")
    return user

def doctor_only(user: User = Depends(current_user)) -> User:
    if user.role not in (UserRole.DOCTOR, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Doctor role required")
    return user

def admin_only(user: User = Depends(current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required")
    return user

# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "An Explainable AI-Based Clinical Risk Screening System for CKD, Diabetes and Hypertension", "version": "1.0.0"}

# ── Auth ───────────────────────────────────────────────────────────────────────
@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, req.email)
    if not user or not verify_password(req.password, user.hashed_password):
        log_action(db, "LOGIN", result="FAILED", details={"email": req.email})
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    log_action(db, "LOGIN", user_id=user.id, result="SUCCESS")
    return TokenResponse(access_token=token, role=user.role.value, full_name=user.full_name)

@app.post("/auth/register", status_code=201)
def register_doctor(req: DoctorRegistrationRequest, db: Session = Depends(get_db)):
    """Create a self-registered doctor account; administrator creation remains protected."""
    if get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    doctor = create_user(db, req.email, req.full_name.strip(), req.password, UserRole.DOCTOR.value)
    log_action(db, "REGISTER_DOCTOR", user_id=doctor.id, details={"email": doctor.email})
    return {"id": doctor.id, "email": doctor.email, "full_name": doctor.full_name,
            "role": doctor.role.value, "message": "Doctor account created successfully"}

@app.get("/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role.value}

# ── Patients ────────────────────────────────────────────────────────────────────
@app.post("/patients", status_code=201)
def add_patient(data: PatientCreate, db: Session = Depends(get_db),
                user: User = Depends(doctor_only)):
    p = create_patient(db, data.model_dump(), user.id)
    log_action(db, "CREATE_PATIENT", user_id=user.id, patient_id=p.id)
    return {"id": p.id, "patient_code": p.patient_code, "full_name": p.full_name,
            "gender": p.gender.value, "date_of_birth": p.date_of_birth.isoformat(),
            "contact_number": p.contact_number, "created_at": p.created_at.isoformat()}

@app.get("/patients")
def patients(db: Session = Depends(get_db), user: User = Depends(doctor_only)):
    doctor_id = None if user.role == UserRole.ADMIN else user.id
    return [{"id": p.id, "patient_code": p.patient_code, "full_name": p.full_name,
             "gender": p.gender.value, "date_of_birth": p.date_of_birth.isoformat(),
             "contact_number": p.contact_number, "created_at": p.created_at.isoformat()}
            for p in list_patients(db, doctor_id)]

@app.get("/patients/{patient_id}")
def patient(patient_id: int, db: Session = Depends(get_db),
            user: User = Depends(doctor_only)):
    p = get_patient(db, patient_id)
    if not p: raise HTTPException(404, "Patient not found")
    return {"id": p.id, "patient_code": p.patient_code, "full_name": p.full_name,
            "gender": p.gender.value, "date_of_birth": p.date_of_birth.isoformat(),
            "contact_number": p.contact_number, "created_at": p.created_at.isoformat()}

@app.get("/patients/{patient_id}/history")
def patient_history(patient_id: int, db: Session = Depends(get_db),
                    user: User = Depends(doctor_only)):
    log_action(db, "VIEW_HISTORY", user_id=user.id, patient_id=patient_id)
    return get_patient_history(db, patient_id)

# ── Assessment ─────────────────────────────────────────────────────────────────
@app.post("/assessments")
def assessment(req: AssessmentRequest, db: Session = Depends(get_db),
               user: User = Depends(doctor_only)):
    result = run_assessment(db, req.patient_id, req.measurements.model_dump(), user.id)
    log_action(db, "RUN_ASSESSMENT", user_id=user.id, patient_id=req.patient_id,
               details={"icrri": result["icrri"], "category": result["risk_category"]})
    return result

# ── Simulation ─────────────────────────────────────────────────────────────────
@app.post("/simulations")
def simulation(req: SimulationRequest, db: Session = Depends(get_db),
               user: User = Depends(doctor_only)):
    result = run_simulation(db, req.visit_id, req.scenario_inputs.model_dump(), user.id)
    log_action(db, "RUN_SIMULATION", user_id=user.id, details={"visit_id": req.visit_id})
    return result

# ── Report ─────────────────────────────────────────────────────────────────────
@app.post("/reports/{visit_id}")
def report(visit_id: int, db: Session = Depends(get_db),
           user: User = Depends(doctor_only)):
    visit = db.query(PatientVisit).filter(PatientVisit.id == visit_id).first()
    if not visit: raise HTTPException(404, "Visit not found")
    p = visit.patient; rs = visit.risk_score
    mv = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()
    pdf_bytes = generate_pdf({
        "patient_code": p.patient_code, "patient_name": p.full_name,
        "date": visit.visit_date.strftime("%Y-%m-%d"), "doctor": user.full_name,
        "icrri": rs.icrri if rs else 0, "risk_category": rs.risk_category.value if rs else "LOW",
        "ckd_prob": rs.ckd_probability if rs else 0,
        "diabetes_prob": rs.diabetes_probability if rs else 0,
        "hypertension_prob": rs.hypertension_probability if rs else 0,
        "alerts": [{"severity": a.severity.value, "title": a.title,
                    "message": a.message, "suggested_action": a.suggested_action}
                   for a in visit.alerts],
        "model_version": mv.version if mv else "N/A",
    })
    log_action(db, "GENERATE_REPORT", user_id=user.id, patient_id=p.id)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=CKD_Diabetes_Hypertension_Risk_Screening_{p.patient_code}.pdf"})

# ── Dashboard ──────────────────────────────────────────────────────────────────
@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(doctor_only)):
    return get_dashboard_stats(db)

# ── Admin ──────────────────────────────────────────────────────────────────────
@app.get("/admin/audit-logs")
def audit_logs(skip: int = 0, limit: int = 100,
               db: Session = Depends(get_db), user: User = Depends(admin_only)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return [{"id": l.id, "user_id": l.user_id, "action": l.action,
             "patient_id": l.patient_id, "result": l.result,
             "timestamp": l.timestamp.isoformat(), "details": l.details}
            for l in logs]

@app.get("/admin/model-versions")
def model_versions(db: Session = Depends(get_db), user: User = Depends(admin_only)):
    mvs = db.query(ModelVersion).order_by(ModelVersion.trained_at.desc()).all()
    return [{"id": m.id, "disease": m.disease, "algorithm": m.algorithm,
             "version": m.version, "metrics": m.metrics, "is_active": m.is_active,
             "trained_at": m.trained_at.isoformat()}
            for m in mvs]

@app.get("/admin/users")
def users(db: Session = Depends(get_db), user: User = Depends(admin_only)):
    all_users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name,
             "role": u.role.value, "is_active": u.is_active}
            for u in all_users]

@app.post("/admin/users", status_code=201)
def add_user(data: UserCreate, db: Session = Depends(get_db),
             user: User = Depends(admin_only)):
    if get_user_by_email(db, data.email):
        raise HTTPException(400, "Email already registered")
    u = create_user(db, data.email, data.full_name, data.password, data.role)
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role.value}
