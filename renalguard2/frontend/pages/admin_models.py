"""Admin — Model Versions page."""
import streamlit as st
from datetime import datetime
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api_client import get, handle
from ui import page_intro

DISEASE_COLORS = {"CKD":"#3b82f6","DIABETES":"#8b5cf6","HYPERTENSION":"#f97316"}

def show():
    page_intro("MODEL GOVERNANCE", "Model registry", "Inspect the registered screening models and their evaluation metrics.")
    st.markdown("<div style='color:#64748b;font-size:13px;margin-bottom:16px'>Trained ML model registry. Run <code>python ml/pipelines/train_models.py</code> to train and then <code>python scripts/seed_db.py</code> to register.</div>", unsafe_allow_html=True)

    try:
        versions = handle(get("/admin/model-versions"))
    except Exception as e:
        st.error(f"Failed to load model versions: {e}"); return

    if not versions:
        st.markdown("""
        <div style='text-align:center;padding:48px;background:#1e293b;border-radius:12px;border:1px solid #334155'>
            <div style='font-size:48px'>🤖</div>
            <h3 style='color:#f1f5f9'>No Models Registered</h3>
            <div style='color:#64748b'>Train models and run the seed script.</div>
        </div>""", unsafe_allow_html=True)
        st.code("python ml\\pipelines\\train_models.py\npython scripts\\seed_db.py")
        return

    for mv in versions:
        color  = DISEASE_COLORS.get(mv["disease"], "#6b7280")
        status = "✅ Active" if mv["is_active"] else "⚪ Inactive"
        trained = datetime.fromisoformat(mv["trained_at"]).strftime("%d %b %Y %H:%M")
        metrics = mv.get("metrics") or {}

        st.markdown(f"""
        <div class="rg-card" style="border-left:4px solid {color}">
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:12px'>
                <div>
                    <span style='font-size:18px;font-weight:700;color:{color}'>{mv['disease']}</span>
                    <span style='margin-left:12px;color:#64748b;font-size:13px'>{mv['algorithm']} · v{mv['version']}</span>
                </div>
                <div style='display:flex;gap:12px;align-items:center'>
                    <span style='color:#64748b;font-size:12px'>Trained: {trained}</span>
                    <span style='background:#1e3a5f;color:#93c5fd;padding:2px 10px;border-radius:20px;font-size:12px'>{status}</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        if metrics:
            cols = st.columns(min(len(metrics), 6))
            for col, (k, v) in zip(cols, metrics.items()):
                with col:
                    st.markdown(f"""
                    <div style='background:#0f172a;border:1px solid #334155;border-radius:8px;padding:10px;text-align:center'>
                        <div style='color:#64748b;font-size:11px'>{k.upper()}</div>
                        <div style='color:#f1f5f9;font-size:16px;font-weight:700'>{f"{v:.4f}" if isinstance(v, float) else v}</div>
                    </div>""", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    st.markdown("<div style='color:#475569;font-size:11px;margin-top:16px'>⚠️ Model metrics computed on held-out test sets. ICRRI is project-specific — not a clinically validated score.</div>", unsafe_allow_html=True)
