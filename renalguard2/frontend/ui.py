"""Reusable presentation components for the RenalGuard clinical intelligence UI."""
from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Iterable

import streamlit as st

RISK_COLORS = {"LOW": "#22C55E", "MODERATE": "#F59E0B", "HIGH": "#F97316", "CRITICAL": "#EF4444"}


def _safe(value: object) -> str:
    return escape(str(value))


def apply_theme() -> None:
    """Apply the intentional, compact RenalGuard SaaS visual system."""
    st.markdown("""
    <style>
    :root { --bg:#020817; --surface:#0f172a; --card:#111827; --line:#1e293b; --ink:#f8fafc; --muted:#94a3b8; --blue:#3b82f6; --green:#22c55e; --amber:#f59e0b; --red:#ef4444; }
    .stApp { background:radial-gradient(circle at 92% -15%,rgba(59,130,246,.15),transparent 28rem),radial-gradient(circle at 12% 4%,rgba(30,41,59,.65),transparent 34rem),var(--bg); color:var(--ink); }
    [data-testid="stHeader"] { background:transparent; } [data-testid="stMainBlockContainer"] { max-width:1480px; padding:1.55rem 2rem 3rem; }
    [data-testid="stSidebar"] { min-width:16.4rem !important; max-width:16.4rem !important; background:linear-gradient(180deg,#091428,#020817); border-right:1px solid var(--line); } [data-testid="stSidebar"] * { color:#d7e1f1 !important; } [data-testid="stSidebarNav"] { display:none; }
    [data-testid="stSidebar"] .stButton button { min-height:2.55rem; border:1px solid transparent; background:transparent; border-radius:11px; text-align:left; font-size:.84rem; font-weight:600; } [data-testid="stSidebar"] .stButton button:hover { background:rgba(59,130,246,.10); border-color:rgba(96,165,250,.18); color:#fff !important; } [data-testid="stSidebar"] .stButton button[kind="primary"] { background:linear-gradient(90deg,rgba(37,99,235,.76),rgba(30,64,175,.60)); border-color:rgba(147,197,253,.22); box-shadow:0 8px 18px rgba(15,23,42,.45); }
    [data-testid="metric-container"] { background:linear-gradient(145deg,rgba(17,24,39,.98),rgba(15,23,42,.96)); border:1px solid var(--line); border-radius:18px; padding:1rem 1.05rem; box-shadow:0 14px 32px rgba(0,0,0,.17); } [data-testid="metric-container"] label { color:var(--muted) !important; font-size:.72rem !important; font-weight:750 !important; letter-spacing:.03em; } [data-testid="stMetricValue"] { color:var(--ink) !important; }
    .rg-page-eyebrow { color:#93c5fd; font-size:.68rem; letter-spacing:.13em; font-weight:800; } .rg-page-title { color:var(--ink); font-size:1.82rem; letter-spacing:-.04em; line-height:1.1; font-weight:800; margin:.28rem 0 .38rem; } .rg-page-detail { color:var(--muted); font-size:.9rem; }
    .rg-card { background:linear-gradient(145deg,rgba(17,24,39,.98),rgba(12,20,35,.97)); border:1px solid var(--line); border-radius:20px; padding:1.15rem 1.2rem; margin-bottom:.85rem; box-shadow:0 16px 36px rgba(0,0,0,.13); } .rg-card:hover { border-color:rgba(96,165,250,.28); transform:translateY(-1px); transition:all .16s ease; }
    .rg-section-title { color:var(--ink); font-size:1rem; font-weight:760; letter-spacing:-.015em; margin:0; } .rg-section-caption { color:var(--muted); font-size:.77rem; margin:.23rem 0 .75rem; } .section-header { color:var(--ink); font-size:1.02rem; font-weight:780; border:0; padding:0; margin:1rem 0 .6rem; } .section-header::after { content:""; display:block; width:32px; height:3px; margin-top:.42rem; border-radius:99px; background:linear-gradient(90deg,#3b82f6,#60a5fa); }
    .rg-kpi { position:relative; min-height:112px; padding:1rem; border:1px solid var(--line); border-radius:18px; overflow:hidden; background:linear-gradient(145deg,rgba(17,24,39,.98),rgba(12,20,35,.98)); box-shadow:0 14px 32px rgba(0,0,0,.14); } .rg-kpi::before { content:""; position:absolute; inset:0 auto 0 0; width:3px; background:var(--accent); } .rg-kpi-icon { color:var(--accent); float:right; font-size:1.25rem; } .rg-kpi-label { color:var(--muted); font-size:.7rem; font-weight:750; letter-spacing:.065em; text-transform:uppercase; } .rg-kpi-value { color:var(--ink); font-size:1.8rem; font-weight:800; letter-spacing:-.05em; margin:.28rem 0; } .rg-kpi-trend { color:#9cb0c9; font-size:.72rem; }
    .rg-badge { display:inline-block; border:1px solid rgba(148,163,184,.2); background:rgba(148,163,184,.08); color:var(--risk); border-radius:999px; padding:.23rem .55rem; font-size:.66rem; font-weight:800; letter-spacing:.065em; }
    .rg-insight { display:flex; gap:.75rem; align-items:flex-start; padding:.78rem .2rem; border-bottom:1px solid rgba(30,41,59,.84); } .rg-insight:last-child { border-bottom:0; padding-bottom:.05rem; } .rg-insight-icon { display:grid; place-items:center; width:1.9rem; height:1.9rem; border-radius:9px; background:rgba(59,130,246,.13); color:#93c5fd; flex:0 0 auto; } .rg-insight-title { color:var(--ink); font-size:.83rem; font-weight:700; } .rg-insight-detail { color:var(--muted); font-size:.73rem; line-height:1.4; margin-top:.12rem; }
    .rg-patient { padding:1rem; border:1px solid var(--line); border-radius:18px; background:linear-gradient(145deg,rgba(17,24,39,.96),rgba(9,18,32,.94)); margin-bottom:.72rem; } .rg-patient:hover { border-color:rgba(96,165,250,.3); box-shadow:0 15px 30px rgba(0,0,0,.13); transition:all .16s ease; } .rg-avatar { display:inline-grid; place-items:center; width:2.35rem; height:2.35rem; margin-right:.65rem; border-radius:50%; background:linear-gradient(135deg,#2563eb,#0ea5e9); color:#eff6ff; font-size:.78rem; font-weight:800; } .rg-patient-name { color:var(--ink); font-size:.95rem; font-weight:780; } .rg-patient-meta { color:var(--muted); font-size:.72rem; margin-top:.15rem; } .rg-indicators { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.45rem; margin-top:.85rem; } .rg-indicator { padding:.52rem .6rem; background:rgba(2,8,23,.55); border:1px solid rgba(30,41,59,.92); border-radius:10px; } .rg-indicator-label { color:var(--muted); font-size:.63rem; text-transform:uppercase; letter-spacing:.05em; } .rg-indicator-value { color:#e7eef9; font-size:.8rem; font-weight:740; margin-top:.13rem; } .rg-progress { height:6px; background:#1e293b; border-radius:99px; overflow:hidden; margin-top:.48rem; } .rg-progress > i { display:block; height:100%; border-radius:inherit; background:var(--risk); }
    .rg-summary-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.7rem; } .rg-summary-cell { background:rgba(2,8,23,.48); border:1px solid rgba(30,41,59,.9); border-radius:12px; padding:.7rem .75rem; } .rg-summary-label { color:var(--muted); font-size:.67rem; font-weight:750; text-transform:uppercase; letter-spacing:.06em; } .rg-summary-value { color:var(--ink); font-size:.82rem; line-height:1.4; margin-top:.25rem; }
    .disclaimer { background:rgba(120,83,18,.14); border:1px solid rgba(245,158,11,.34); border-left:3px solid var(--amber); border-radius:12px; padding:.72rem .85rem; color:#fde68a; font-size:.78rem; margin:.8rem 0 1rem; }
    .badge-low,.badge-moderate,.badge-high,.badge-critical { display:inline-block; padding:.24rem .6rem; border-radius:99px; font-size:.67rem; font-weight:800; letter-spacing:.05em; } .badge-low { background:rgba(34,197,94,.14); color:#86efac; } .badge-moderate { background:rgba(245,158,11,.14); color:#fcd34d; } .badge-high { background:rgba(249,115,22,.15); color:#fdba74; } .badge-critical { background:rgba(239,68,68,.15); color:#fca5a5; }
    .alert-critical,.alert-high,.alert-moderate,.alert-low { border-radius:13px; padding:.85rem .95rem; margin:.55rem 0; background:rgba(17,24,39,.9); } .alert-critical { border-left:3px solid #ef4444; } .alert-high { border-left:3px solid #f97316; } .alert-moderate { border-left:3px solid #f59e0b; } .alert-low { border-left:3px solid #3b82f6; }
    [data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stNumberInput"] input,[data-testid="stSelectbox"] [data-baseweb="select"] > div { background:#0b1424 !important; border-color:#243247 !important; border-radius:11px !important; color:#f8fafc !important; } [data-testid="stTextInput"] input:focus,[data-testid="stNumberInput"] input:focus { border-color:#3b82f6 !important; box-shadow:0 0 0 3px rgba(59,130,246,.12) !important; }
    [data-testid="stButton"] > button[kind="primary"] { background:linear-gradient(90deg,#2563eb,#3b82f6); border:0; border-radius:11px; font-weight:740; box-shadow:0 9px 18px rgba(37,99,235,.2); } [data-testid="stButton"] > button:not([kind="primary"]) { border-color:#2a3a52; border-radius:11px; } [data-testid="stTabs"] [data-baseweb="tab-list"] { gap:.45rem; border-bottom:1px solid var(--line); } [data-testid="stTabs"] button { border-radius:10px 10px 0 0; } [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:14px; overflow:hidden; }
    #MainMenu, footer { visibility:hidden; } @media (max-width:760px) { [data-testid="stMainBlockContainer"] { padding:1.05rem .9rem 2rem; } .rg-indicators { grid-template-columns:repeat(2,minmax(0,1fr)); } .rg-summary-grid { grid-template-columns:1fr; } [data-testid="stSidebar"] { min-width:15.5rem !important; max-width:15.5rem !important; } }
    </style>
    """, unsafe_allow_html=True)


def page_intro(eyebrow: str, title: str, detail: str) -> None:
    st.markdown(f"<div style='margin-bottom:1.1rem'><div class='rg-page-eyebrow'>{_safe(eyebrow)}</div><div class='rg-page-title'>{_safe(title)}</div><div class='rg-page-detail'>{_safe(detail)}</div></div>", unsafe_allow_html=True)


def render_glass_card(title: str, detail: str = "", icon: str = "") -> None:
    """Render a compact static glass card for status, empty-state, or workflow context."""
    prefix = f"<span style='color:#93c5fd;margin-right:.35rem'>{_safe(icon)}</span>" if icon else ""
    st.markdown(f"<div class='rg-card'><div class='rg-section-title'>{prefix}{_safe(title)}</div><div class='rg-section-caption'>{_safe(detail)}</div></div>", unsafe_allow_html=True)


def render_kpi_card(label: str, value: object, icon: str, trend: str, tone: str = "#3B82F6") -> None:
    st.markdown(f"<div class='rg-kpi' style='--accent:{_safe(tone)}'><span class='rg-kpi-icon'>{_safe(icon)}</span><div class='rg-kpi-label'>{_safe(label)}</div><div class='rg-kpi-value'>{_safe(value)}</div><div class='rg-kpi-trend'>{_safe(trend)}</div></div>", unsafe_allow_html=True)


def render_risk_badge(category: str) -> str:
    category = (category or "LOW").upper()
    color = RISK_COLORS.get(category, "#94A3B8")
    return f"<span class='rg-badge' style='--risk:{color}'>● {_safe(category)} RISK</span>"


def render_ai_insights(items: Iterable[tuple[str, str, str]]) -> None:
    rows = [f"<div class='rg-insight'><div class='rg-insight-icon'>{_safe(icon)}</div><div><div class='rg-insight-title'>{_safe(title)}</div><div class='rg-insight-detail'>{_safe(detail)}</div></div></div>" for icon, title, detail in items]
    st.markdown("<div class='rg-card'><div class='rg-section-title'>🧠 AI clinical insights</div><div class='rg-section-caption'>Signals from saved screening activity — for qualified clinical review.</div>" + "".join(rows) + "</div>", unsafe_allow_html=True)


def render_chart_card(title: str, detail: str = "") -> None:
    st.markdown(f"<div class='rg-card'><div class='rg-section-title'>{_safe(title)}</div><div class='rg-section-caption'>{_safe(detail)}</div>", unsafe_allow_html=True)


def close_chart_card() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_patient_card(patient: dict, latest: dict | None = None) -> None:
    """Render a patient intelligence card; call native actions immediately after it."""
    latest = latest or {}
    name = patient.get("full_name", "Unknown patient")
    initials = "".join(piece[0] for piece in name.replace("[SYNTHETIC]", "").split()[:2]).upper() or "PT"
    try:
        age = max(0, datetime.now().year - datetime.fromisoformat(patient.get("date_of_birth", "")).year)
    except Exception:
        age = "—"
    category = latest.get("risk_category") or "UNASSESSED"
    score = latest.get("icrri")
    color = RISK_COLORS.get(category, "#94A3B8")
    def value(key: str, suffix: str = "") -> str:
        data = latest.get(key)
        return "—" if data is None else f"{data}{suffix}"
    score_label = "Open History to load" if score is None else f"{float(score):.1f}/100"
    progress = 0 if score is None else min(max(float(score), 0), 100)
    st.markdown(f"<div class='rg-patient' style='--risk:{color}'><div style='display:flex;justify-content:space-between;align-items:flex-start'><div><span class='rg-avatar'>{_safe(initials)}</span><span class='rg-patient-name'>{_safe(name)}</span><div class='rg-patient-meta'>{_safe(patient.get('patient_code', '—'))} · {_safe(patient.get('gender', '—')).title()} · {_safe(age)} yrs</div></div><div>{render_risk_badge(category)}</div></div><div class='rg-indicators'><div class='rg-indicator'><div class='rg-indicator-label'>Creatinine</div><div class='rg-indicator-value'>{_safe(value('creatinine', ' mg/dL'))}</div></div><div class='rg-indicator'><div class='rg-indicator-label'>HbA1c</div><div class='rg-indicator-value'>{_safe(value('hba1c', '%'))}</div></div><div class='rg-indicator'><div class='rg-indicator-label'>BP</div><div class='rg-indicator-value'>{_safe(value('systolic_bp'))}/{_safe(value('diastolic_bp'))}</div></div><div class='rg-indicator'><div class='rg-indicator-label'>BMI</div><div class='rg-indicator-value'>{_safe(value('bmi'))}</div></div></div><div style='display:flex;justify-content:space-between;margin-top:.72rem'><span class='rg-indicator-label'>Risk score</span><span style='font-size:.75rem;color:{color};font-weight:780'>{_safe(score_label)}</span></div><div class='rg-progress'><i style='width:{progress:.1f}%'></i></div></div>", unsafe_allow_html=True)
