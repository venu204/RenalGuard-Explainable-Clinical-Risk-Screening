"""What-If Simulation page."""
import streamlit as st
import plotly.graph_objects as go
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api_client import get, post, handle
from ui import page_intro, render_kpi_card, render_risk_badge

RISK_COLORS = {"LOW":"#22c55e","MODERATE":"#f59e0b","HIGH":"#f97316","CRITICAL":"#ef4444"}

def show():
    page_intro("SCENARIO EXPLORER", "What-if simulation", "Compare a hypothetical measurement set with the latest screening visit.")
    st.markdown('<div class="disclaimer">Model-based scenario exploration only. Does <strong>NOT</strong> modify patient records and is <strong>NOT</strong> a treatment prediction or guaranteed clinical outcome.</div>', unsafe_allow_html=True)

    if not st.session_state.get("last_visit_id"):
        st.markdown("""
        <div style='text-align:center;padding:48px;background:#1e293b;border-radius:12px;border:1px solid #334155'>
            <div style='font-size:48px'>🔮</div>
            <h3 style='color:#f1f5f9'>No Assessment Available</h3>
            <div style='color:#64748b'>Run an assessment first, then return here to simulate scenarios.</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔬 Go to Assessment", type="primary", use_container_width=True):
            st.session_state.page = "Screening Queue"; st.rerun()
        return

    visit_id = st.session_state.last_visit_id
    st.markdown(f"<div class='rg-card'><div class='rg-section-title'>Digital twin scenario</div><div class='rg-section-caption'>Baseline visit {visit_id} remains unchanged. Adjust the simulated values to compare model-estimated screening signals.</div></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-header">Simulated values</div>', unsafe_allow_html=True)
    st.caption("Change one or more values to explore a hypothetical scenario. This does not predict treatment outcomes.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div style='color:#3b82f6;font-weight:600;margin-bottom:8px'>Demographics & Vitals</div>", unsafe_allow_html=True)
        age          = st.number_input("Age (years)",         min_value=0,   max_value=120,  value=55,   step=1)
        gender_enc   = st.selectbox("Gender",                 ["Male (1)","Female (0)"])
        bmi          = st.number_input("BMI (kg/m²)",         min_value=10.0,max_value=80.0,  value=25.0, step=0.1, format="%.1f")
        systolic_bp  = st.number_input("Systolic BP (mmHg)",  min_value=60.0,max_value=250.0, value=120.0,step=1.0, format="%.0f")
        diastolic_bp = st.number_input("Diastolic BP (mmHg)", min_value=40.0,max_value=160.0, value=80.0, step=1.0, format="%.0f")

    with col2:
        st.markdown("<div style='color:#8b5cf6;font-weight:600;margin-bottom:8px'>Laboratory Values</div>", unsafe_allow_html=True)
        glucose    = st.number_input("Glucose (mg/dL)",    min_value=50.0, max_value=600.0, value=90.0,  step=1.0, format="%.0f")
        hba1c      = st.number_input("HbA1c (%)",          min_value=3.0,  max_value=20.0,  value=5.5,   step=0.1, format="%.1f")
        creatinine = st.number_input("Creatinine (mg/dL)", min_value=0.1,  max_value=20.0,  value=1.0,   step=0.1, format="%.1f")
        hemoglobin = st.number_input("Hemoglobin (g/dL)",  min_value=3.0,  max_value=25.0,  value=13.0,  step=0.1, format="%.1f")
        potassium  = st.number_input("Potassium (mEq/L)",  min_value=1.0,  max_value=9.0,   value=4.0,   step=0.1, format="%.1f")

    with col3:
        st.markdown("<div style='color:#f97316;font-weight:600;margin-bottom:8px'>Additional Labs</div>", unsafe_allow_html=True)
        sodium  = st.number_input("Sodium (mEq/L)",  min_value=100.0,max_value=180.0,value=140.0,step=1.0, format="%.0f")
        urea    = st.number_input("Urea (mg/dL)",    min_value=0.0,  max_value=500.0,value=30.0, step=1.0, format="%.0f")
        st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
        smoking = st.checkbox("🚬 Smoking")
        fam_htn = st.checkbox("🧬 Family Hx: HTN")
        fam_dm  = st.checkbox("🧬 Family Hx: DM")

    scenario = {
        "age": float(age),
        "gender_enc": 1 if "1" in gender_enc else 0,
        "bmi": bmi, "systolic_bp": systolic_bp, "diastolic_bp": diastolic_bp,
        "glucose": glucose, "hba1c": hba1c, "creatinine": creatinine,
        "hemoglobin": hemoglobin, "potassium": potassium,
        "sodium": sodium, "urea": urea,
        "smoking": smoking,
        "family_history_hypertension": fam_htn,
        "family_history_diabetes": fam_dm,
    }

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("▶️  Run Simulation", type="primary", use_container_width=True):
        with st.spinner("Running what-if simulation..."):
            try:
                result = handle(post("/simulations", {"visit_id": visit_id, "scenario_inputs": scenario}))
                st.session_state["sim_result"] = result
            except Exception as e:
                st.error(f"Simulation failed: {e}"); return

    if not st.session_state.get("sim_result"):
        return

    result = st.session_state["sim_result"]
    st.markdown('<div class="section-header">Risk comparison</div>', unsafe_allow_html=True)

    baseline   = result["baseline_icrri"]
    simulated  = result["simulated_icrri"]
    delta      = result["delta"]
    base_cat   = result["baseline_category"]
    sim_cat    = result["simulated_category"]
    bc         = RISK_COLORS.get(base_cat, "#6b7280")
    sc         = RISK_COLORS.get(sim_cat, "#6b7280")

    c1, c2, c3 = st.columns(3)
    delta_label = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}"
    with c1: render_kpi_card("Current ICRRI", f"{baseline:.1f}", "◉", base_cat.title() + " profile", bc)
    with c2: render_kpi_card("Projected ICRRI", f"{simulated:.1f}", "◈", sim_cat.title() + " profile", sc)
    with c3: render_kpi_card("Scenario delta", delta_label, "↗" if delta > 0 else "↘" if delta < 0 else "—", "Lower score is not a clinical outcome", "#EF4444" if delta > 0 else "#22C55E" if delta < 0 else "#94A3B8")

    st.markdown(f"""
    <div style='display:flex;gap:24px;margin-top:12px'>
        <div style='background:#1e293b;border:1px solid #334155;border-radius:8px;padding:12px 24px;flex:1;text-align:center'>
            <div style='color:#64748b;font-size:12px'>Baseline Category</div>
            <div style='color:{bc};font-size:20px;font-weight:700;margin-top:4px'>{render_risk_badge(base_cat)}</div>
        </div>
        <div style='background:#1e293b;border:1px solid #334155;border-radius:8px;padding:12px 24px;flex:1;text-align:center'>
            <div style='color:#64748b;font-size:12px'>Simulated Category</div>
            <div style='color:{sc};font-size:20px;font-weight:700;margin-top:4px'>{render_risk_badge(sim_cat)}</div>
        </div>
        <div style='background:#1e293b;border:1px solid {"#22c55e" if delta < 0 else "#ef4444" if delta > 0 else "#334155"};
             border-radius:8px;padding:12px 24px;flex:1;text-align:center'>
            <div style='color:#64748b;font-size:12px'>ICRRI Change</div>
            <div style='color:{"#22c55e" if delta < 0 else "#ef4444" if delta > 0 else "#94a3b8"};font-size:20px;font-weight:700;margin-top:4px'>
                {delta_label}
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Comparison gauge chart
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    for col, val, cat, label in [(col1, baseline, base_cat, "Baseline"), (col2, simulated, sim_cat, "Simulated")]:
        with col:
            color = RISK_COLORS.get(cat, "#6b7280")
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=val,
                number={"font":{"color":color,"size":32}},
                title={"text":label,"font":{"color":"#94a3b8","size":13}},
                gauge={
                    "axis":{"range":[0,100],"tickfont":{"color":"#64748b"}},
                    "bar":{"color":color,"thickness":0.25},
                    "bgcolor":"#1e293b","bordercolor":"#334155",
                    "steps":[
                        {"range":[0,34],"color":"#052e16"},{"range":[34,54],"color":"#1c1500"},
                        {"range":[54,74],"color":"#1c0a00"},{"range":[74,100],"color":"#1c0000"},
                    ],
                }
            ))
            fig.update_layout(height=220, paper_bgcolor="#1e293b",
                              font={"color":"#94a3b8"}, margin=dict(t=30,b=10,l=20,r=20))
            st.plotly_chart(fig, use_container_width=True)

    # Disease probs
    probs = result.get("scenario_probs", {})
    if probs:
        st.markdown('<div class="section-header" style="font-size:15px">Disease Probabilities (Simulated)</div>', unsafe_allow_html=True)
        dc = {"CKD":"#3b82f6","DIABETES":"#8b5cf6","HYPERTENSION":"#f97316"}
        for d, p in probs.items():
            c = dc.get(d,"#6b7280")
            pct = p * 100
            st.markdown(f"<div style='display:flex;justify-content:space-between;margin-bottom:4px'><span style='color:#94a3b8;font-size:13px'>{d}</span><span style='color:{c};font-weight:700'>{pct:.1f}%</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#334155;border-radius:4px;height:6px;margin-bottom:10px'><div style='background:{c};width:{min(pct,100):.1f}%;height:6px;border-radius:4px'></div></div>", unsafe_allow_html=True)

    st.markdown("<div style='color:#475569;font-size:11px;margin-top:16px;font-style:italic'>⚠️ This is a model-based scenario exploration tool. Not a treatment outcome predictor. Not a clinical recommendation.</div>", unsafe_allow_html=True)
