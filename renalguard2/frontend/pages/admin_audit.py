"""Admin — Audit Logs page."""
import streamlit as st
from datetime import datetime
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api_client import get, handle
from ui import page_intro

ACTION_ICONS = {
    "LOGIN":"🔑","LOGOUT":"🚪","CREATE_PATIENT":"👤","RUN_ASSESSMENT":"🔬",
    "RUN_SIMULATION":"🔮","GENERATE_REPORT":"📄","VIEW_HISTORY":"📊","FAILED":"❌",
}

def show():
    page_intro("ADMINISTRATION", "Audit activity", "Review recorded application actions without exposing sensitive credentials.")
    st.markdown("<div style='color:#64748b;font-size:13px;margin-bottom:16px'>Every significant system action is recorded. Passwords and tokens are never logged.</div>", unsafe_allow_html=True)

    try:
        logs = handle(get("/admin/audit-logs", {"limit": 200}))
    except Exception as e:
        st.error(f"Failed to load audit logs: {e}"); return

    if not logs:
        st.info("No audit logs yet."); return

    # Summary
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Entries", len(logs))
    success = sum(1 for l in logs if l.get("result") == "SUCCESS")
    c2.metric("✅ Successful", success)
    c3.metric("❌ Failed", len(logs) - success)

    st.markdown("<br>", unsafe_allow_html=True)

    # Filters
    col1, col2 = st.columns(2)
    actions = sorted(set(l["action"] for l in logs))
    filter_action = col1.selectbox("Filter by Action", ["All"] + actions)
    filter_result = col2.selectbox("Filter by Result", ["All","SUCCESS","FAILED"])

    filtered = logs
    if filter_action != "All":
        filtered = [l for l in filtered if l["action"] == filter_action]
    if filter_result != "All":
        filtered = [l for l in filtered if l.get("result") == filter_result]

    st.markdown(f"<div style='color:#64748b;font-size:12px;margin:8px 0'>{len(filtered)} entries</div>", unsafe_allow_html=True)

    rows = []
    for l in filtered:
        ts = datetime.fromisoformat(l["timestamp"]).strftime("%d %b %Y %H:%M:%S")
        icon = ACTION_ICONS.get(l["action"], "📌")
        result_badge = "✅" if l.get("result") == "SUCCESS" else "❌"
        rows.append({
            "Timestamp":  ts,
            "Action":     f"{icon} {l['action']}",
            "User ID":    str(l.get("user_id") or "—"),
            "Patient ID": str(l.get("patient_id") or "—"),
            "Result":     f"{result_badge} {l.get('result') or '—'}",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
