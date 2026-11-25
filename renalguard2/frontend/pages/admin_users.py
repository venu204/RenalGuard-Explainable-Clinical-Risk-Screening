"""Admin — Users page."""
import streamlit as st
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api_client import get, post, handle
from ui import page_intro

def show():
    page_intro("ADMINISTRATION", "User management", "Review accounts and create access for your clinical workspace.")
    tab1, tab2 = st.tabs(["👥  All Users", "➕  Create User"])

    with tab1:
        try:
            users = handle(get("/admin/users"))
        except Exception as e:
            st.error(f"Failed to load users: {e}"); return

        if not users:
            st.info("No users found."); return

        st.markdown(f"<div style='color:#64748b;font-size:13px;margin-bottom:12px'>{len(users)} user(s) registered</div>", unsafe_allow_html=True)
        for u in users:
            role_color = "#a78bfa" if u["role"] == "ADMIN" else "#60a5fa"
            status_color = "#22c55e" if u["is_active"] else "#ef4444"
            status_label = "Active" if u["is_active"] else "Inactive"
            st.markdown(f"""
            <div class="rg-card" style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <div style='font-size:15px;font-weight:600;color:#f1f5f9'>{u['full_name']}</div>
                    <div style='font-size:13px;color:#64748b;margin-top:2px'>{u['email']}</div>
                </div>
                <div style='display:flex;gap:10px;align-items:center'>
                    <span style='background:#1a1040;color:{role_color};padding:3px 12px;
                          border-radius:20px;font-size:12px;font-weight:600'>● {u['role']}</span>
                    <span style='color:{status_color};font-size:12px;font-weight:600'>● {status_label}</span>
                </div>
            </div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div style='color:#94a3b8;font-size:14px;margin-bottom:16px'>Create a new Doctor or Admin account.</div>", unsafe_allow_html=True)
        with st.form("create_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            full_name = col1.text_input("Full Name *")
            email     = col2.text_input("Email Address *")
            col3, col4 = st.columns(2)
            password  = col3.text_input("Password *", type="password", help="Minimum 8 characters")
            role      = col4.selectbox("Role *", ["DOCTOR","ADMIN"])
            submitted = st.form_submit_button("✅  Create User", type="primary", use_container_width=True)

        if submitted:
            errors = []
            if not full_name.strip(): errors.append("Full name is required.")
            if not email.strip():     errors.append("Email is required.")
            if len(password) < 8:     errors.append("Password must be at least 8 characters.")
            if errors:
                for err in errors: st.error(err)
            else:
                try:
                    result = handle(post("/admin/users", {
                        "email": email.strip(),
                        "full_name": full_name.strip(),
                        "password": password,
                        "role": role,
                    }))
                    st.success(f"✅ User created: **{result['full_name']}** ({result['role']})")
                except Exception as e:
                    st.error(f"Failed to create user: {e}")
