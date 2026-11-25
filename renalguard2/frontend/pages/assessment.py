"""Assessment page — fixed all number_input bugs, modern UI."""
import streamlit as st
import plotly.graph_objects as go
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api_client import get_json, post, handle
from ui import page_intro

RISK_COLORS = {"LOW":"#22c55e","MODERATE":"#f59e0b","HIGH":"#f97316","CRITICAL":"#ef4444"}
SEV_ICON = {"CRITICAL":"🔴","HIGH":"🟠","MODERATE":"🟡","LOW":"🔵","INFORMATIONAL":"⚪"}
SEV_CLASS = {"CRITICAL":"alert-critical","HIGH":"alert-high","MODERATE":"alert-moderate","LOW":"alert-low","INFORMATIONAL":"alert-low"}

def _v(val, minimum=0.01):
    """Convert 0.0 sentinel back to None for the model."""
    try:
        f = float(val)
        return f if f >= minimum else None
    except Exception:
        return None


_FORM_DEFAULTS = {
    "assessment_age": 55,
    "assessment_gender": "Male (1)",
    "assessment_bmi": 0.0,
    "assessment_systolic_bp": 0.0,
    "assessment_diastolic_bp": 0.0,
    "assessment_glucose": 0.0,
    "assessment_hba1c": 0.0,
    "assessment_creatinine": 0.0,
    "assessment_hemoglobin": 0.0,
    "assessment_potassium": 0.0,
    "assessment_sodium": 0.0,
    "assessment_urea": 0.0,
    "assessment_albumin": 0.0,
    "assessment_smoking": False,
    "assessment_fam_htn": False,
    "assessment_fam_dm": False,
    "assessment_fam_ckd": False,
    "assessment_notes": "",
}


def _load_patient_measurements(patient_id: int) -> tuple[bool, str]:
    """Load the newest saved visit into the form before its widgets are drawn."""
    values = dict(_FORM_DEFAULTS)
    try:
        history = get_json(f"/patients/{patient_id}/history")
        visits = history.get("visits", [])
        latest = visits[-1] if visits else None
        if latest:
            def saved(name, fallback):
                value = latest.get(name)
                return fallback if value is None else value

            values.update({
                "assessment_age": int(saved("age", 55)),
                "assessment_gender": "Male (1)" if saved("gender_enc", 1) == 1 else "Female (0)",
                "assessment_bmi": float(saved("bmi", 0.0)),
                "assessment_systolic_bp": float(saved("systolic_bp", 0.0)),
                "assessment_diastolic_bp": float(saved("diastolic_bp", 0.0)),
                "assessment_glucose": float(saved("glucose", 0.0)),
                "assessment_hba1c": float(saved("hba1c", 0.0)),
                "assessment_creatinine": float(saved("creatinine", 0.0)),
                "assessment_hemoglobin": float(saved("hemoglobin", 0.0)),
                "assessment_potassium": float(saved("potassium", 0.0)),
                "assessment_sodium": float(saved("sodium", 0.0)),
                "assessment_urea": float(saved("urea", 0.0)),
                "assessment_albumin": float(saved("albumin", 0.0)),
                "assessment_smoking": bool(saved("smoking", False)),
                "assessment_fam_htn": bool(saved("family_history_hypertension", False)),
                "assessment_fam_dm": bool(saved("family_history_diabetes", False)),
                "assessment_fam_ckd": bool(saved("family_history_ckd", False)),
                "assessment_notes": saved("notes", "") or "",
            })
        else:
            st.session_state.update(values)
            st.session_state.assessment_loaded_patient_id = patient_id
            return False, "No saved visit exists for this patient yet. Run the seed script or save an assessment first."
    except Exception as error:
        # The assessment workflow remains available even if a history request fails.
        st.session_state.update(values)
        st.session_state.assessment_loaded_patient_id = patient_id
        return False, f"Could not load saved values: {error}"
    st.session_state.update(values)
    st.session_state.assessment_loaded_patient_id = patient_id
    return True, "Latest saved measurements loaded into the form."

def show():
    page_intro("SCREENING", "New assessment", "Enter measured values to generate an explainable screening summary.")
    st.markdown('<div class="disclaimer">⚠️ Estimated probabilities are <strong>NOT diagnoses</strong>. Requires review by a qualified clinician. Set any field to 0 if not measured — it will be excluded from the model.</div>', unsafe_allow_html=True)

    # ── Patient selector ───────────────────────────────────────────────────────
    try:
        patients = get_json("/patients")
    except Exception as e:
        st.error(f"Cannot load patients: {e}"); return

    if not patients:
        st.warning("No patients found. Register a patient first.")
        if st.button("➕ Register Patient", type="primary"):
            st.session_state.page = "Patients"; st.rerun()
        return

    options = {f"{p['patient_code']} — {p['full_name']}": p["id"] for p in patients}
    default_idx = 0
    if st.session_state.get("selected_patient_id"):
        for i, pid in enumerate(options.values()):
            if pid == st.session_state.selected_patient_id:
                default_idx = i; break

    selected_label = st.selectbox("👤  Select Patient", list(options.keys()), index=default_idx,
                                  key="assessment_patient_selector")
    patient_id = options[selected_label]

    if st.session_state.get("assessment_loaded_patient_id") != patient_id:
        loaded, message = _load_patient_measurements(patient_id)
        st.session_state.assessment_load_feedback = (loaded, message)
        st.rerun()

    load_col, message_col = st.columns([1, 3])
    if load_col.button("↻ Load latest saved values", use_container_width=True,
                       help="Replace the form with the selected patient's newest saved visit."):
        loaded, message = _load_patient_measurements(patient_id)
        st.session_state.assessment_load_feedback = (loaded, message)
        st.rerun()
    if feedback := st.session_state.pop("assessment_load_feedback", None):
        if feedback[0]:
            message_col.success(feedback[1])
        else:
            message_col.info(feedback[1])

    st.markdown('<div class="section-header">Screening workspace</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        st.markdown("<div class='rg-card'><div class='rg-section-title'>Patient profile</div><div class='rg-section-caption'>Core demographics and clinical context.</div>", unsafe_allow_html=True)
        age          = st.number_input("Age (years) *",      min_value=0,   max_value=120,  step=1,   key="assessment_age")
        gender_enc   = st.selectbox("Gender *",              ["Male (1)","Female (0)"], key="assessment_gender")
        smoking = st.checkbox("Smoking history", key="assessment_smoking")
        family = st.columns(3)
        fam_htn = family[0].checkbox("Family Hx: hypertension", key="assessment_fam_htn")
        fam_dm  = family[1].checkbox("Family Hx: diabetes", key="assessment_fam_dm")
        fam_ckd = family[2].checkbox("Family Hx: CKD", key="assessment_fam_ckd")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='rg-card'><div class='rg-section-title'>Vital signs</div><div class='rg-section-caption'>Current body composition and blood-pressure values.</div>", unsafe_allow_html=True)
        bmi          = st.number_input("BMI (kg/m²)",        min_value=0.0, max_value=80.0,  step=0.1, format="%.1f", key="assessment_bmi")
        bp1, bp2 = st.columns(2)
        systolic_bp  = bp1.number_input("Systolic BP (mmHg)", min_value=0.0, max_value=250.0, step=1.0, format="%.0f", key="assessment_systolic_bp")
        diastolic_bp = bp2.number_input("Diastolic BP (mmHg)",min_value=0.0, max_value=160.0, step=1.0, format="%.0f", key="assessment_diastolic_bp")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='rg-card'><div class='rg-section-title'>Laboratory results</div><div class='rg-section-caption'>Enter measured values; a zero means the value is unavailable.</div>", unsafe_allow_html=True)
        lab1, lab2 = st.columns(2)
        with lab1:
            glucose    = st.number_input("Glucose (mg/dL)",    min_value=0.0, max_value=600.0, step=1.0,  format="%.0f", key="assessment_glucose")
            hba1c      = st.number_input("HbA1c (%)",          min_value=0.0, max_value=20.0,  step=0.1,  format="%.1f", key="assessment_hba1c")
            creatinine = st.number_input("Creatinine (mg/dL)", min_value=0.0, max_value=20.0,  step=0.1,  format="%.1f", key="assessment_creatinine")
            hemoglobin = st.number_input("Hemoglobin (g/dL)",  min_value=0.0, max_value=25.0,  step=0.1,  format="%.1f", key="assessment_hemoglobin")
        with lab2:
            potassium  = st.number_input("Potassium (mEq/L)",  min_value=0.0, max_value=9.0,   step=0.1,  format="%.1f", key="assessment_potassium")
            sodium  = st.number_input("Sodium (mEq/L)",  min_value=0.0, max_value=180.0, step=1.0, format="%.0f", key="assessment_sodium")
            urea    = st.number_input("Urea (mg/dL)",    min_value=0.0, max_value=500.0, step=1.0, format="%.0f", key="assessment_urea")
            albumin = st.number_input("Albumin (g/dL)",  min_value=0.0, max_value=10.0,  step=0.1, format="%.1f", key="assessment_albumin")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='rg-card'><div class='rg-section-title'>Clinical notes</div>", unsafe_allow_html=True)
    notes = st.text_area("Clinical notes", placeholder="Add relevant clinical observations…", key="assessment_notes", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    measurements = {
        "age": float(age),
        "gender_enc": 1 if "1" in gender_enc else 0,
        "bmi":          _v(bmi, 10.0),
        "systolic_bp":  _v(systolic_bp, 60.0),
        "diastolic_bp": _v(diastolic_bp, 40.0),
        "glucose":      _v(glucose, 50.0),
        "hba1c":        _v(hba1c, 3.0),
        "creatinine":   _v(creatinine, 0.1),
        "hemoglobin":   _v(hemoglobin, 3.0),
        "potassium":    _v(potassium, 1.0),
        "sodium":       _v(sodium, 100.0),
        "urea":         _v(urea, 0.1),
        "albumin":      _v(albumin, 0.1),
        "smoking": smoking,
        "family_history_hypertension": fam_htn,
        "family_history_diabetes": fam_dm,
        "family_history_ckd": fam_ckd,
        "notes": notes.strip() or None,
    }

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("▶️  Run Assessment", type="primary", use_container_width=True):
        with st.spinner("Running ML inference + clinical rule engine..."):
            try:
                result = handle(post("/assessments", {"patient_id": patient_id, "measurements": measurements}))
                st.session_state.last_result   = result
                st.session_state.last_visit_id = result["visit_id"]
                st.session_state.selected_patient_id = patient_id
                st.success(f"✅ Assessment complete — Visit ID: {result['visit_id']}")
            except Exception as e:
                st.error(f"Assessment failed: {e}"); return

    if not st.session_state.get("last_result"):
        return

    result = st.session_state.last_result
    if result.get("patient_id") and result["patient_id"] != patient_id:
        st.info("Showing results from last assessment. Select same patient and re-run to refresh.")

    st.markdown("---")

    icrri = result.get("icrri", 0)
    cat   = result.get("risk_category", "LOW")
    color = RISK_COLORS.get(cat, "#6b7280")
    alerts = result.get("alerts", [])
    patient_name = selected_label.split(" — ", 1)[-1]
    risk_copy = {
        "LOW": "The model-estimated screening signals are currently low. Continue routine review as appropriate.",
        "MODERATE": "Some screening signals warrant closer review and follow-up in an appropriate clinical setting.",
        "HIGH": "Multiple screening signals require prompt qualified clinical review. This is not a diagnosis.",
        "CRITICAL": "Urgent qualified clinical review is indicated by this screening result. This is not a diagnosis.",
    }.get(cat, "Review the screening output with a qualified clinician.")

    st.markdown(f"""
    <div class="assessment-hero" style="--risk-color:{color}">
        <div><div class="assessment-kicker">SCREENING SUMMARY · {patient_name}</div>
        <div class="assessment-title">{cat.title()} risk profile</div>
        <div class="assessment-copy">{risk_copy}</div></div>
        <div class="assessment-score"><div class="assessment-score-number">{icrri:.1f}</div>
        <div class="assessment-score-label">ICRRI · 0–100 project score</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="disclaimer">Estimated probabilities support screening only. They are <strong>not diagnoses</strong> and must be reviewed by a qualified clinician.</div>', unsafe_allow_html=True)

    predicted = [p["disease"].title() for p in result.get("predictions", []) if p.get("predicted_class")]
    primary = ", ".join(predicted) if predicted else "No model probability is above its configured threshold"
    contributors = []
    for explanation in result.get("explanations", []):
        contributors.extend(c.get("feature", "").replace("_", " ").title() for c in explanation.get("top_contributors", [])[:2])
    drivers = ", ".join(dict.fromkeys(contributors)) if contributors else "Model explanation unavailable for this result"
    recommendation = "Prompt qualified clinical review" if cat in ("HIGH", "CRITICAL") else "Routine review and monitoring as appropriate"
    st.markdown(f"""<div class='rg-card'><div class='rg-section-title'>Clinical summary</div><div class='rg-section-caption'>A structured screening interpretation, not a diagnosis or treatment plan.</div><div class='rg-summary-grid'><div class='rg-summary-cell'><div class='rg-summary-label'>Overall risk</div><div class='rg-summary-value'>{cat.title()} · ICRRI {icrri:.1f}/100</div></div><div class='rg-summary-cell'><div class='rg-summary-label'>Primary signals</div><div class='rg-summary-value'>{primary}</div></div><div class='rg-summary-cell'><div class='rg-summary-label'>Top risk drivers</div><div class='rg-summary-value'>{drivers}</div></div><div class='rg-summary-cell'><div class='rg-summary-label'>Follow-up priority</div><div class='rg-summary-value'>{recommendation}</div></div></div></div>""", unsafe_allow_html=True)

    # ── Prioritised overview ───────────────────────────────────────────────────
    c1, c2 = st.columns([1, 1.55])
    with c1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=icrri,
            number={"font":{"color":color,"size":36}},
            title={"text":"ICRRI Score","font":{"color":"#94a3b8","size":14}},
            gauge={
                "axis":{"range":[0,100],"tickcolor":"#475569","tickfont":{"color":"#64748b"}},
                "bar":{"color":color,"thickness":0.25},
                "bgcolor":"#1e293b",
                "bordercolor":"#334155",
                "steps":[
                    {"range":[0,34],  "color":"#052e16"},
                    {"range":[34,54], "color":"#1c1500"},
                    {"range":[54,74], "color":"#1c0a00"},
                    {"range":[74,100],"color":"#1c0000"},
                ],
                "threshold":{"line":{"color":color,"width":3},"thickness":0.8,"value":icrri},
            }
        ))
        fig.update_layout(height=235, paper_bgcolor="#11213a",
                          font={"color":"#94a3b8"},
                          margin=dict(t=30,b=10,l=20,r=20))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<div style='text-align:center'><span class='badge-{cat.lower()}'>{cat} RISK</span></div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='section-header' style='font-size:15px'>Disease risk estimates</div>", unsafe_allow_html=True)
        preds = result.get("predictions", [])
        dc = {"CKD":"#3b82f6","DIABETES":"#8b5cf6","HYPERTENSION":"#f97316"}
        cards = []
        for p in preds:
            prob = p["probability"] * 100
            disease_color = dc.get(p["disease"], "#6b7280")
            label = "Above model threshold" if p.get("predicted_class") else "Below model threshold"
            cards.append(f"""<div class='disease-card'><div class='disease-name'>{p['disease']}</div><div class='disease-value' style='color:{disease_color}'>{prob:.1f}%</div><div style='color:#9aabc4;font-size:.7rem;margin-bottom:.5rem'>{label}</div><div class='disease-track'><div class='disease-fill' style='width:{min(prob, 100):.1f}%;background:{disease_color}'></div></div></div>""")
        st.markdown(f"<div class='disease-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)

        if preds:
            fig2 = go.Figure(go.Bar(
                x=[p["disease"] for p in preds],
                y=[round(p["probability"]*100,1) for p in preds],
                marker_color=[dc.get(p["disease"],"#6b7280") for p in preds],
                text=[f"{round(p['probability']*100,1)}%" for p in preds],
                textposition="auto", textfont=dict(color="white"),
            ))
            fig2.update_layout(
                plot_bgcolor="#081321", paper_bgcolor="#11213a",
                font=dict(color="#94a3b8"),
                yaxis=dict(range=[0,100], gridcolor="#334155", title="Est. Risk (%)"),
                xaxis=dict(gridcolor="#334155"),
                height=185, margin=dict(t=5,b=5,l=10,r=10), showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ── Alerts ─────────────────────────────────────────────────────────────────
    if alerts:
        st.markdown("---")
        highest = next((a["severity"] for a in alerts if a["severity"] in ("CRITICAL", "HIGH")), alerts[0]["severity"])
        st.markdown(f'<div class="section-header" style="font-size:15px">🚨 Review queue · {len(alerts)} alert(s) · highest: {highest}</div>', unsafe_allow_html=True)
        for a in alerts:
            css = SEV_CLASS.get(a["severity"], "alert-low")
            icon = SEV_ICON.get(a["severity"], "⚪")
            st.markdown(f"""
            <div class="{css}">
                <div style="font-weight:700;margin-bottom:4px">{icon} [{a['severity']}] {a['title']}</div>
                <div style="color:#cbd5e1;font-size:13px">{a['message']}</div>
                {"<div style='color:#93c5fd;font-size:12px;margin-top:6px'>→ " + a['suggested_action'] + "</div>" if a.get('suggested_action') else ""}
            </div>""", unsafe_allow_html=True)
    else:
        st.success("✅ No clinical alerts triggered for these values.")

    # ── SHAP Explanations ──────────────────────────────────────────────────────
    explanations = result.get("explanations", [])
    valid_expls = [e for e in explanations if e.get("top_contributors")]
    if valid_expls:
        st.markdown("---")
        st.markdown('<div class="section-header" style="font-size:15px">🧠 Model Explanations (SHAP)</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#64748b;font-size:12px;margin-bottom:12px">SHAP values show model contributions — NOT causal medical statements.</div>', unsafe_allow_html=True)
        cols = st.columns(len(valid_expls))
        for col, expl in zip(cols, valid_expls):
            with col:
                contribs = expl["top_contributors"]
                feats  = [c["feature"].replace("_"," ").title() for c in contribs]
                vals   = [c["shap_value"] for c in contribs]
                colors = ["#ef4444" if v > 0 else "#22c55e" for v in vals]
                fig3 = go.Figure(go.Bar(
                    x=vals, y=feats, orientation="h",
                    marker_color=colors,
                    text=[f"{v:+.3f}" for v in vals],
                    textposition="auto", textfont=dict(size=10, color="white"),
                ))
                fig3.update_layout(
                    title=dict(text=f"{expl['disease']}", font=dict(color="#f1f5f9",size=13)),
                    plot_bgcolor="#0f172a", paper_bgcolor="#1e293b",
                    font=dict(color="#94a3b8", size=11),
                    xaxis=dict(gridcolor="#334155", title="SHAP Value"),
                    yaxis=dict(gridcolor="#334155"),
                    height=240, margin=dict(t=30,b=10,l=10,r=10),
                    showlegend=False,
                )
                st.plotly_chart(fig3, use_container_width=True)
        with st.expander("📝 Plain Language Explanation"):
            for expl in valid_expls:
                if expl.get("plain_language"):
                    st.markdown(f"**{expl['disease']}**")
                    st.text(expl["plain_language"])

    # ── Quick nav ──────────────────────────────────────────────────────────────
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    if c1.button("📊 View History", use_container_width=True):
        st.session_state.page = "Clinical Insights"; st.rerun()
    if c2.button("🔮 What-If Simulation", use_container_width=True):
        st.session_state.page = "Simulations"; st.rerun()
    if c3.button("📄 Download PDF Report", use_container_width=True, type="primary"):
        st.session_state.page = "Reports"; st.rerun()
