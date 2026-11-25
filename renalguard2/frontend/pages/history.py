"""Longitudinal clinical insights for individual patients."""
from __future__ import annotations

from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api_client import get_json
from ui import RISK_COLORS, close_chart_card, page_intro, render_chart_card, render_kpi_card, render_risk_badge


def show():
    page_intro("CLINICAL INSIGHTS", "Longitudinal patient view", "Switch between the chronological care timeline and risk analytics for an individual patient.")
    try:
        patients = get_json("/patients")
    except Exception as error:
        st.error(f"Unable to load patients: {error}")
        return
    if not patients:
        st.info("No patient profiles are available yet.")
        return
    options = {f"{p['patient_code']} — {p['full_name']}": p["id"] for p in patients}
    index = next((i for i, item in enumerate(options.values()) if item == st.session_state.get("selected_patient_id")), 0)
    selected = st.selectbox("Select patient", list(options), index=index, key="history_patient")
    patient_id = options[selected]
    st.session_state.selected_patient_id = patient_id
    try:
        history = get_json(f"/patients/{patient_id}/history")
    except Exception as error:
        st.error(f"Unable to load clinical history: {error}")
        return
    visits = history.get("visits", [])
    if not visits:
        st.info("No saved screening visits exist for this patient.")
        if st.button("Start assessment", type="primary"):
            st.session_state.page = "Screening Queue"; st.rerun()
        return
    latest = visits[-1]
    trend = history.get("trend") or "STABLE"
    trend_text = {"IMPROVING": "Improving trend", "WORSENING": "Worsening trend", "STABLE": "Stable trend"}.get(trend, "Trend unavailable")
    first, second, third = st.columns(3)
    with first: render_kpi_card("Saved visits", history.get("count", len(visits)), "◌", "Longitudinal screening record", "#3B82F6")
    with second: render_kpi_card("Latest ICRRI", f"{float(latest.get('icrri') or 0):.1f}", "≈", latest.get("risk_category", "LOW").title() + " risk profile", RISK_COLORS.get(latest.get("risk_category", "LOW"), "#3B82F6"))
    with third: render_kpi_card("Risk trajectory", trend.title(), "↗", trend_text, "#22C55E" if trend == "IMPROVING" else "#EF4444" if trend == "WORSENING" else "#F59E0B")

    timeline, analytics = st.tabs(["Timeline view", "Analytics view"])
    with timeline:
        st.markdown("<div class='rg-card'><div class='rg-section-title'>Screening timeline</div><div class='rg-section-caption'>Most recent screening visits are shown first.</div>", unsafe_allow_html=True)
        for visit in reversed(visits):
            date = datetime.fromisoformat(visit["visit_date"]).strftime("%d %b %Y · %H:%M")
            category = visit.get("risk_category", "LOW")
            st.markdown(f"<div class='rg-insight'><div class='rg-insight-icon'>◌</div><div style='flex:1'><div class='rg-insight-title'>{date} &nbsp; {render_risk_badge(category)}</div><div class='rg-insight-detail'>ICRRI {float(visit.get('icrri') or 0):.1f} · CKD {float(visit.get('ckd') or 0)*100:.1f}% · Diabetes {float(visit.get('diabetes') or 0)*100:.1f}% · Hypertension {float(visit.get('hypertension') or 0)*100:.1f}%</div></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with analytics:
        dates = [datetime.fromisoformat(v["visit_date"]).strftime("%d %b") for v in visits]
        left, right = st.columns(2)
        with left:
            render_chart_card("ICRRI trend", "Risk score over saved visits.")
            fig = go.Figure(go.Scatter(x=dates, y=[v.get("icrri") for v in visits], mode="lines+markers", line=dict(color="#60A5FA", width=3), marker=dict(size=9, color=[RISK_COLORS.get(v.get("risk_category", "LOW")) for v in visits])))
            fig.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827", font=dict(color="#94A3B8"), height=280, margin=dict(t=10,b=20,l=20,r=10), showlegend=False, yaxis=dict(range=[0,100], gridcolor="#1E293B", title="ICRRI"), xaxis=dict(gridcolor="#1E293B"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            close_chart_card()
        with right:
            render_chart_card("Disease probability trend", "Model-estimated probabilities, not diagnoses.")
            fig = go.Figure()
            for key, label, color in [("ckd", "CKD", "#3B82F6"), ("diabetes", "Diabetes", "#8B5CF6"), ("hypertension", "Hypertension", "#F97316")]:
                fig.add_trace(go.Scatter(x=dates, y=[float(v.get(key) or 0)*100 for v in visits], name=label, mode="lines+markers", line=dict(color=color, width=2)))
            fig.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827", font=dict(color="#94A3B8"), height=280, margin=dict(t=10,b=20,l=20,r=10), legend=dict(orientation="h", y=1.12), yaxis=dict(range=[0,100], gridcolor="#1E293B", title="Probability (%)"), xaxis=dict(gridcolor="#1E293B"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            close_chart_card()
