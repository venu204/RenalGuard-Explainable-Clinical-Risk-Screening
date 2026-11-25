"""RenalGuard — explainable clinical risk screening workspace."""
import streamlit as st

st.set_page_config(
    page_title="RenalGuard | Clinical Screening",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from api_client import post, handle
from ui import apply_theme

apply_theme()

# ── Session defaults ───────────────────────────────────────────────────────────
for k, v in [("token",None),("user",None),("role",None),("page","Overview"),
              ("last_result",None),("last_visit_id",None),("selected_patient_id",None),
              ("auth_view","login")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Login ──────────────────────────────────────────────────────────────────────
def login_page():
    # The authentication flow has no sidebar content, so present a focused login view.
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 18% 12%, rgba(14, 165, 233, 0.14), transparent 30%),
            radial-gradient(circle at 82% 86%, rgba(30, 64, 175, 0.18), transparent 32%),
            #0b1220;
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 1180px;
        padding-top: 2.25rem;
        padding-bottom: 2.25rem;
    }
    .login-eyebrow {
        color: #7dd3fc;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.16em;
        text-align: center;
        margin-bottom: 0.8rem;
    }
    .login-hero {
        background: linear-gradient(145deg, rgba(30, 58, 95, 0.96), rgba(19, 37, 64, 0.96));
        border: 1px solid rgba(125, 211, 252, 0.22);
        border-radius: 22px;
        box-shadow: 0 24px 54px rgba(0, 0, 0, 0.28);
        padding: 1.5rem 1.8rem 1.3rem;
        text-align: center;
    }
    .login-icon {
        width: 58px;
        height: 58px;
        margin: 0 auto 0.85rem;
        display: grid;
        place-items: center;
        border-radius: 18px;
        background: linear-gradient(135deg, #0ea5e9, #2563eb);
        box-shadow: 0 10px 26px rgba(14, 165, 233, 0.28);
        font-size: 1.85rem;
    }
    .login-title {
        color: #f8fafc;
        font-size: clamp(1.24rem, 2.1vw, 1.62rem);
        font-weight: 760;
        line-height: 1.28;
        letter-spacing: -0.025em;
        margin: 0;
    }
    .login-title span { color: #bae6fd; }
    .login-subtitle {
        color: #a8b7cd;
        font-size: 0.9rem;
        line-height: 1.55;
        margin: 0.72rem 0 0;
    }
    .login-form-title {
        color: #e2e8f0;
        font-size: 1rem;
        font-weight: 700;
        margin: 1.2rem 0 0.12rem;
    }
    .login-form-caption {
        color: #718096;
        font-size: 0.78rem;
        margin: 0 0 0.85rem;
    }
    [data-testid="stTextInput"] { margin-bottom: 0.25rem; }
    [data-testid="stTextInput"] label { color: #cbd5e1 !important; font-size: 0.78rem !important; font-weight: 700 !important; }
    [data-testid="stTextInput"] input {
        background: rgba(15, 23, 42, 0.82) !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        color: #f8fafc !important;
        min-height: 2.85rem !important;
        transition: border-color 160ms ease, box-shadow 160ms ease;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.14) !important;
    }
    [data-testid="stButton"] > button[kind="primary"] {
        min-height: 2.9rem;
        border: 0;
        border-radius: 10px;
        background: linear-gradient(90deg, #0284c7, #2563eb);
        box-shadow: 0 10px 20px rgba(37, 99, 235, 0.22);
        font-size: 0.9rem;
        font-weight: 750;
        letter-spacing: 0.01em;
        transition: transform 160ms ease, box-shadow 160ms ease;
    }
    [data-testid="stButton"] > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 13px 24px rgba(37, 99, 235, 0.30);
    }
    .login-disclaimer {
        display: flex;
        gap: 0.55rem;
        align-items: flex-start;
        margin: 1rem 0 0.35rem;
        padding: 0.72rem 0.85rem;
        border: 1px solid rgba(251, 191, 36, 0.28);
        border-radius: 10px;
        background: rgba(120, 53, 15, 0.18);
        color: #fcd34d;
        font-size: 0.75rem;
        line-height: 1.45;
    }
    .login-demo {
        margin-top: 0.9rem;
        padding: 0.72rem 0.9rem;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.48);
    }
    .login-demo summary {
        display: flex;
        align-items: center;
        justify-content: space-between;
        cursor: pointer;
        color: #e2e8f0;
        font-size: 0.75rem;
        font-weight: 750;
        letter-spacing: 0.04em;
        list-style: none;
        text-transform: uppercase;
    }
    .login-demo summary::-webkit-details-marker { display: none; }
    .login-demo summary span:last-child { color: #7dd3fc; font-size: 0.67rem; letter-spacing: 0; text-transform: none; }
    .login-demo[open] summary { margin-bottom: 0.65rem; }
    .login-demo-row {
        display: flex;
        justify-content: space-between;
        gap: 0.8rem;
        color: #94a3b8;
        font-size: 0.76rem;
    }
    .login-demo-row code { color: #7dd3fc; font-size: 0.72rem; }
    .registration-divider {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin: 0.9rem 0 0.6rem;
        color: #64748b;
        font-size: 0.7rem;
        text-align: center;
    }
    .registration-divider::before, .registration-divider::after {
        content: "";
        flex: 1;
        height: 1px;
        background: rgba(148, 163, 184, 0.2);
    }
    .registration-note {
        color: #94a3b8;
        font-size: 0.72rem;
        line-height: 1.45;
        text-align: center;
        margin: 0 0 0.6rem;
    }
    .registration-card {
        padding: 1.15rem 1.2rem;
        border: 1px solid rgba(125, 211, 252, 0.2);
        border-radius: 14px;
        background: rgba(15, 35, 60, 0.72);
    }
    .registration-card h2 {
        color: #f8fafc;
        font-size: 1.25rem;
        margin: 0 0 0.35rem;
    }
    .registration-card p {
        color: #94a3b8;
        font-size: 0.78rem;
        line-height: 1.45;
        margin: 0;
    }
    @media (max-height: 800px) {
        [data-testid="stMainBlockContainer"] { padding-top: 0.7rem; padding-bottom: 0.5rem; }
        .login-eyebrow { font-size: 0.6rem; margin-bottom: 0.35rem; }
        .login-hero { padding: 0.85rem 1.35rem 0.7rem; border-radius: 16px; }
        .login-icon { width: 42px; height: 42px; margin-bottom: 0.5rem; border-radius: 13px; font-size: 1.35rem; }
        .login-title { font-size: 1.08rem; line-height: 1.18; }
        .login-subtitle { font-size: 0.7rem; line-height: 1.35; margin-top: 0.45rem; }
        .login-form-title { font-size: 0.88rem; margin-top: 0.55rem; }
        .login-form-caption { font-size: 0.68rem; margin-bottom: 0.35rem; }
        [data-testid="stTextInput"] { margin-bottom: 0; }
        [data-testid="stTextInput"] label { font-size: 0.68rem !important; }
        [data-testid="stTextInput"] input { min-height: 2.15rem !important; border-radius: 8px !important; }
        [data-testid="stButton"] > button[kind="primary"] { min-height: 2.25rem; border-radius: 8px; font-size: 0.78rem; }
        .login-disclaimer { margin-top: 0.55rem; padding: 0.45rem 0.6rem; border-radius: 8px; font-size: 0.62rem; }
        .login-demo { gap: 0.32rem; margin-top: 0.55rem; padding: 0.55rem 0.7rem; border-radius: 9px; }
        .login-demo-heading { font-size: 0.62rem; }
        .login-demo-row { font-size: 0.62rem; }
        .login-demo-row code { font-size: 0.58rem; }
        .registration-divider { margin: 0.55rem 0 0.4rem; font-size: 0.58rem; }
        .registration-note { font-size: 0.6rem; margin-bottom: 0.4rem; }
        .registration-card { padding: 0.8rem 0.9rem; }
        .registration-card h2 { font-size: 1.05rem; }
        .registration-card p { font-size: 0.68rem; }
    }
    </style>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([0.8, 1.4, 0.8])
    with col:
        st.markdown("<div class='login-eyebrow'>EXPLAINABLE CLINICAL INTELLIGENCE</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='login-hero'>
            <div class='login-icon'>🫀</div>
            <h1 class='login-title'>RenalGuard <span>Clinical Intelligence</span></h1>
            <p class='login-subtitle'>Clear, explainable risk screening for kidney, diabetes, and hypertension workflows.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div class='login-form-title'>Sign in to your workspace</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-form-caption'>Use your assigned clinician or administrator account.</div>", unsafe_allow_html=True)

        if st.session_state.get("account_registered"):
            st.success("Account created. Sign in with your new doctor account.")
            st.session_state.account_registered = False

        email = st.text_input("Email address", placeholder="doctor@renalguard.dev", key="login_email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        if st.button("Sign in securely  →", use_container_width=True, type="primary"):
            if not email or not password:
                st.error("Please enter your email address and password.")
            else:
                try:
                    r = post("/auth/login", {"email": email, "password": password})
                    data = handle(r)
                    st.session_state.token = data["access_token"]
                    st.session_state.role = data["role"]
                    st.session_state.user = data["full_name"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

        st.markdown("<div class='registration-divider'>OR</div>", unsafe_allow_html=True)
        st.markdown("<p class='registration-note'>New to the system? Create a doctor account to begin using the academic screening platform.</p>", unsafe_allow_html=True)
        if st.button("Register as a new doctor", use_container_width=True, key="open_doctor_registration"):
            st.session_state.auth_view = "register"
            st.rerun()

        st.markdown("""
        <div class='login-disclaimer'><span>⚠️</span><span><strong>Academic prototype.</strong> This system supports screening only and is not a clinical diagnostic tool.</span></div>
        <details class='login-demo'>
            <summary><span>Demo access</span><span>View test credentials</span></summary>
            <div class='login-demo-row'><span>Clinician</span><code>doctor@renalguard.dev · Doctor@1234</code></div>
            <div class='login-demo-row'><span>Administrator</span><code>admin@renalguard.dev · Admin@1234</code></div>
        </details>
        """, unsafe_allow_html=True)
def registration_page():
    """Public sign-up for doctor accounts; administrator accounts cannot be self-registered."""
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 18% 12%, rgba(14, 165, 233, 0.14), transparent 30%),
            radial-gradient(circle at 82% 86%, rgba(30, 64, 175, 0.18), transparent 32%),
            #0b1220;
    }
    [data-testid="stMainBlockContainer"] { max-width: 700px; padding-top: 3rem; }
    .registration-page-heading { color: #7dd3fc; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.16em; text-align: center; margin-bottom: 0.7rem; }
    .registration-card { margin-bottom: 1rem; }
    @media (max-height: 800px) {
        [data-testid="stMainBlockContainer"] { padding-top: 0.8rem; padding-bottom: 0.5rem; }
        .registration-page-heading { margin-bottom: 0.35rem; font-size: 0.6rem; }
        .registration-card { padding: 0.75rem 0.9rem; margin-bottom: 0.45rem; }
    }
    </style>
    """, unsafe_allow_html=True)
    _, col, _ = st.columns([0.55, 1.5, 0.55])
    with col:
        st.markdown("<div class='registration-page-heading'>CLINICIAN ACCOUNT REGISTRATION</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='registration-card'>
            <h2>Register as a new doctor</h2>
            <p>Create a doctor account for this academic screening system. Administrator accounts must be created by an existing administrator.</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("doctor_registration_form", clear_on_submit=False):
            full_name = st.text_input("Full name", placeholder="Dr. Your Name")
            email = st.text_input("Email address", placeholder="doctor@example.com")
            password = st.text_input("Password", type="password", help="Use at least 8 characters.")
            confirm_password = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create doctor account", type="primary", use_container_width=True)

        if submitted:
            errors = []
            if len(full_name.strip()) < 2:
                errors.append("Enter your full name.")
            if not email.strip():
                errors.append("Enter your email address.")
            if len(password) < 8:
                errors.append("Password must contain at least 8 characters.")
            if password != confirm_password:
                errors.append("Passwords do not match.")
            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    handle(post("/auth/register", {
                        "full_name": full_name.strip(),
                        "email": email.strip(),
                        "password": password,
                    }))
                    st.session_state.login_email = email.strip()
                    st.session_state.account_registered = True
                    st.session_state.auth_view = "login"
                    st.rerun()
                except Exception as error:
                    st.error(f"Registration failed: {error}")

        if st.button("← Back to sign in", use_container_width=True):
            st.session_state.auth_view = "login"
            st.rerun()


# ── Sidebar ────────────────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:16px 0 8px; text-align:center;'>
            <div style='font-size:25px'>✦</div>
            <div style='font-size:17px; font-weight:800; color:#f1f5f9'>RenalGuard</div>
            <div style='font-size:10px; color:#94a3b8;letter-spacing:.1em'>CLINICAL INTELLIGENCE</div>
        </div>
        <hr style='border-color:#334155; margin:8px 0 16px'>
        <div style='background:#0f2440; border-radius:8px; padding:10px 12px; margin-bottom:16px;'>
            <div style='font-size:13px; font-weight:600; color:#f1f5f9'>👤 {st.session_state.user}</div>
            <div style='font-size:11px; color:#64748b'>{st.session_state.role}</div>
        </div>
        """, unsafe_allow_html=True)

        nav_doctor = [("◉", "Overview"), ("⌁", "Screening Queue"), ("◌", "Patients"),
                      ("↗", "Clinical Insights"), ("◈", "Simulations"), ("▤", "Reports")]
        nav_admin  = nav_doctor + [("⚙", "Admin — Users"),
                                   ("◫", "Admin — Audit Logs"),
                                   ("◉", "Admin — Model Registry")]
        nav = nav_admin if st.session_state.role == "ADMIN" else nav_doctor

        current = st.session_state.page
        for icon, label in nav:
            active = label in current
            btn_style = "primary" if active else "secondary"
            if st.button(f"{icon}  {label}", use_container_width=True,
                         type=btn_style, key=f"nav_{label}"):
                st.session_state.page = label
                st.rerun()

        st.markdown("<hr style='border-color:#1e293b; margin:16px 0'>", unsafe_allow_html=True)
        if st.button("Sign out", use_container_width=True):
            for k in ["token","user","role","last_result","last_visit_id","selected_patient_id"]:
                st.session_state[k] = None
            st.session_state.page = "Overview"
            st.rerun()
        st.markdown("<div style='font-size:10px;color:#64748b;text-align:center;margin-top:8px'>Academic prototype<br>Not for clinical use</div>", unsafe_allow_html=True)

# ── Router ─────────────────────────────────────────────────────────────────────
def router():
    from pages import (dashboard, patients, assessment, history,
                       simulation, reports, admin_users, admin_audit, admin_models)
    p = st.session_state.page
    if   p in ("Overview", "Dashboard"):  dashboard.show()
    elif "Patients"  in p:  patients.show()
    elif p in ("Screening Queue", "Assessment"):  assessment.show()
    elif p in ("Clinical Insights", "History"):  history.show()
    elif p in ("Simulations", "Simulation"):  simulation.show()
    elif "Reports"   in p:  reports.show()
    elif "Users"     in p:  admin_users.show()
    elif "Audit"     in p:  admin_audit.show()
    elif "Model"     in p:  admin_models.show()
    else:                   dashboard.show()

# ── Main ───────────────────────────────────────────────────────────────────────
if not st.session_state.token:
    registration_page() if st.session_state.auth_view == "register" else login_page()
else:
    sidebar()
    router()
