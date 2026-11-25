"""Executive clinical intelligence overview."""
from __future__ import annotations

from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api_client import get_json
from ui import RISK_COLORS, close_chart_card, page_intro, render_ai_insights, render_chart_card, render_kpi_card


def show():
    name = (st.session_state.get("user") or "Clinician").replace("Dr. ", "")
    greeting = "Good morning" if datetime.now().hour < 12 else "Good afternoon" if datetime.now().hour < 18 else "Good evening"
    page_intro("CLINICAL INTELLIGENCE", f"{greeting}, Dr. {name}", "AI-powered screening operations for CKD, diabetes, and hypertension.")

    try:
        # One cached dashboard request replaces the previous request-per-patient
        # history loop, making this screen responsive as the directory grows.
        stats = get_json("/dashboard")
    except Exception as error:
        st.error(f"Cannot connect to the clinical workspace: {error}")
        st.caption("Confirm that the FastAPI backend is running on port 8000.")
        return

    total_patients = int(stats.get("total_patients", 0))
    this_month = int(stats.get("todays_assessments", 0))
    high_cases = int(stats.get("high_risk_patients", 0))
    pending = high_cases + int(stats.get("critical_alerts", 0))

    first, second, third = st.columns(3)
    with first: render_kpi_card("Total patients", total_patients, "◉", "Active clinical records", "#3B82F6")
    with second: render_kpi_card("Screenings today", this_month, "⌁", "Saved assessment visits", "#8B5CF6")
    with third: render_kpi_card("High-risk cases", high_cases, "!", "High + critical visit profiles", "#F97316")
    fourth, fifth, sixth = st.columns(3)
    with fourth: render_kpi_card("Critical cases", stats.get("critical_alerts", 0), "▲", "Unacknowledged critical alerts", "#EF4444")
    with fifth: render_kpi_card("Pending reviews", pending, "◌", "Requires clinical attention", "#F59E0B")
    with sixth: render_kpi_card("Risk coverage", f"{sum(stats.get('risk_distribution', {}).values())}", "≈", "Scored screening visits", "#22C55E")

    left, right = st.columns([1.15, .85])
    with left:
        render_ai_insights([
            ("!", f"{high_cases} patient visit(s) need closer review", "High and critical profiles are prioritized in the screening queue."),
            ("⌁", f"{sum(stats.get('risk_distribution', {}).values())} risk-scored visit(s) are available", "Open Clinical Insights for a patient-level longitudinal view."),
            ("↗", "Disease models are ready for screening", "CKD, diabetes, and hypertension estimates appear after an assessment is run."),
        ])
    with right:
        render_chart_card("Clinical command center", "Move from population view to individual screening workflows.")
        a, b = st.columns(2)
        if a.button("Open screening queue", key="overview_queue", type="primary", use_container_width=True):
            st.session_state.page = "Screening Queue"; st.rerun()
        if b.button("View patients", key="overview_patients", use_container_width=True):
            st.session_state.page = "Patients"; st.rerun()
        st.caption("Academic prototype — outputs support screening only and are not clinical diagnoses.")
        close_chart_card()

    distribution = stats.get("risk_distribution", {})
    cats = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    values = [distribution.get(cat, 0) for cat in cats]
    chart_left, chart_right = st.columns(2)
    with chart_left:
        render_chart_card("Risk distribution", "Portfolio view by most recent saved risk category.")
        fig = go.Figure(go.Pie(labels=[c.title() for c in cats], values=values, hole=.68,
                               marker=dict(colors=[RISK_COLORS[c] for c in cats], line=dict(color="#111827", width=3)),
                               textinfo="label+value", textfont=dict(color="#E2E8F0", size=11)))
        fig.update_layout(showlegend=False, paper_bgcolor="#111827", font=dict(color="#94A3B8"), height=270, margin=dict(t=8, b=8, l=8, r=8),
                          annotations=[dict(text=f"{sum(values)}<br>scores", x=.5, y=.5, font=dict(size=16, color="#F8FAFC"), showarrow=False)])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        close_chart_card()
    with chart_right:
        render_chart_card("Screening model coverage", "Active models used by the clinical intelligence workflow.")
        disease = [("CKD", "ckd", "#3B82F6"), ("Diabetes", "diabetes", "#8B5CF6"), ("Hypertension", "hypertension", "#F97316")]
        means = [100, 100, 100]
        fig = go.Figure(go.Bar(y=[label for label, _, _ in disease], x=means, orientation="h", marker_color=[color for _, _, color in disease], text=[f"{value:.1f}%" for value in means], textposition="auto", textfont=dict(color="#F8FAFC")))
        fig.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827", font=dict(color="#94A3B8"), height=270, margin=dict(t=10, b=20, l=10, r=10), showlegend=False,
                          xaxis=dict(range=[0, 100], gridcolor="#1E293B", title="Estimated probability (%)"), yaxis=dict(gridcolor="#1E293B"))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        close_chart_card()
