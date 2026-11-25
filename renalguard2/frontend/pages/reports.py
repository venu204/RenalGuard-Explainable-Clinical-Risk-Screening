"""Reports page."""
import streamlit as st
import requests
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api_client import get, handle
from ui import page_intro, render_risk_badge

def show():
    page_intro("REPORTING", "Assessment reports", "Generate a shareable summary for the latest screening visit.")
    st.markdown('<div class="disclaimer">Reports include a full clinical screening summary, alerts, SHAP explanations, and a mandatory medical disclaimer.</div>', unsafe_allow_html=True)

    if not st.session_state.get("last_visit_id"):
        st.markdown("""
        <div style='text-align:center;padding:48px;background:#1e293b;border-radius:12px;border:1px solid #334155'>
            <div style='font-size:48px'>📭</div>
            <h3 style='color:#f1f5f9'>No Assessment Yet</h3>
            <div style='color:#64748b'>Run an assessment first to generate a PDF report.</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔬 Go to Assessment", type="primary", use_container_width=True):
            st.session_state.page = "Screening Queue"; st.rerun()
        return

    visit_id = st.session_state.last_visit_id
    result   = st.session_state.get("last_result", {})
    icrri    = result.get("icrri", "—")
    cat      = result.get("risk_category", "—")

    RISK_COLORS = {"LOW":"#22c55e","MODERATE":"#f59e0b","HIGH":"#f97316","CRITICAL":"#ef4444"}
    color = RISK_COLORS.get(cat, "#94a3b8")

    st.markdown(f"""
    <div class="rg-card" style='min-height:190px'>
        <div style='display:flex;justify-content:space-between;align-items:flex-start'>
            <div>
                <div style='color:#93c5fd;font-size:11px;font-weight:800;letter-spacing:.1em'>CLINICAL SCREENING REPORT</div>
                <div style='color:#f1f5f9;font-size:20px;font-weight:800;margin-top:8px'>Latest assessment summary</div>
                <div style='color:#94a3b8;font-size:13px;margin-top:6px'>Visit ID: {visit_id} · Includes risk scores, alerts, and model explanations.</div>
            </div>
            <div style='text-align:right'>
                <div style='color:#94a3b8;font-size:12px'>ICRRI score</div>
                <div style='color:{color};font-size:24px;font-weight:700'>{f"{icrri:.1f}" if isinstance(icrri, float) else icrri}</div>
                {render_risk_badge(cat)}
            </div>
        </div>
        <div style='height:1px;background:#1e293b;margin:20px 0 12px'></div>
        <div style='color:#94a3b8;font-size:12px'>Prepared for qualified clinical review · Academic prototype only</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Included in this report</div>', unsafe_allow_html=True)
    for item in ["Patient information & assessment date",
                 "CKD, Diabetes, Hypertension estimated probabilities",
                 "ICRRI score & risk category",
                 "Clinical alerts (rule engine findings)",
                 "SHAP model explanation summary",
                 "Medical disclaimer (mandatory)"]:
        st.markdown(f"<div style='color:#94a3b8;font-size:13px;padding:4px 0'>✓ {item}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📄  Generate & Download PDF Report", type="primary", use_container_width=True):
        with st.spinner("Generating PDF..."):
            token = st.session_state.get("token", "")
            try:
                r = requests.post(
                    f"http://localhost:8000/reports/{visit_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30,
                )
                if r.status_code == 200:
                    st.download_button(
                        label="⬇️  Click Here to Download PDF",
                        data=r.content,
                        file_name=f"CKD_Diabetes_Hypertension_Risk_Screening_Visit_{visit_id}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                    st.success("✅ PDF generated successfully!")
                else:
                    try:
                        detail = r.json().get("detail", r.text)
                    except Exception:
                        detail = r.text
                    st.error(f"Report generation failed: {detail}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Make sure FastAPI is running on port 8000.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
