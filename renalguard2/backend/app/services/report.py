"""PDF report generator using ReportLab."""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

DISCLAIMER = (
    "DISCLAIMER: An Explainable AI-Based Clinical Risk Screening System for CKD, Diabetes and Hypertension is an academic prototype. It does NOT diagnose disease, "
    "prescribe treatment, or replace professional medical judgment. All findings "
    "require review by a qualified healthcare professional."
)
RISK_COLORS = {"LOW": colors.green, "MODERATE": colors.orange,
               "HIGH": colors.darkorange, "CRITICAL": colors.red}

def generate_pdf(data: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []

    # Header
    story += [
        Paragraph("An Explainable AI-Based Clinical Risk Screening System for CKD, Diabetes and Hypertension", ParagraphStyle("t", parent=styles["Title"],
                  fontSize=14, leading=17, textColor=colors.HexColor("#1e40af"))),
        Paragraph("Clinical Screening & Decision-Support Report",
                  ParagraphStyle("s", parent=styles["Normal"], fontSize=10, textColor=colors.grey)),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e40af")),
        Spacer(1, 5*mm),
    ]

    # Patient info
    story.append(Paragraph("Patient Information",
                            ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12)))
    t = Table([
        ["Patient ID", data.get("patient_code","—"), "Date", data.get("date","—")],
        ["Name", data.get("patient_name","—"), "Doctor", data.get("doctor","—")],
    ], colWidths=[40*mm, 60*mm, 30*mm, 70*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,-1), colors.HexColor("#eff6ff")),
        ("BACKGROUND", (2,0),(2,-1), colors.HexColor("#eff6ff")),
        ("FONTSIZE",(0,0),(-1,-1),9), ("BOX",(0,0),(-1,-1),.5,colors.grey),
        ("INNERGRID",(0,0),(-1,-1),.25,colors.lightgrey),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story += [t, Spacer(1, 5*mm)]

    # Risk scores
    story.append(Paragraph("Integrated Risk Assessment",
                            ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12)))
    cat = data.get("risk_category", "LOW")
    t2 = Table([
        ["CKD Est. Risk", f"{data.get('ckd_prob',0):.1%}",
         "Diabetes Est. Risk", f"{data.get('diabetes_prob',0):.1%}"],
        ["Hypertension Est. Risk", f"{data.get('hypertension_prob',0):.1%}",
         "ICRRI Score", f"{data.get('icrri',0):.1f} / 100"],
    ], colWidths=[50*mm,50*mm,50*mm,50*mm])
    t2.setStyle(TableStyle([
        ("FONTSIZE",(0,0),(-1,-1),9), ("BOX",(0,0),(-1,-1),.5,colors.grey),
        ("INNERGRID",(0,0),(-1,-1),.25,colors.lightgrey),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story += [t2, Spacer(1,3*mm),
              Paragraph(f"Risk Category: {cat}",
                        ParagraphStyle("cat", parent=styles["Normal"],
                                       fontSize=14, fontName="Helvetica-Bold",
                                       textColor=RISK_COLORS.get(cat, colors.black))),
              Spacer(1,5*mm)]

    # Alerts
    alerts = data.get("alerts", [])
    if alerts:
        story.append(Paragraph(f"Clinical Alerts ({len(alerts)})",
                               ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12)))
        for a in alerts:
            ac = {"CRITICAL": colors.red, "HIGH": colors.orange,
                  "MODERATE": colors.goldenrod}.get(a.get("severity",""), colors.black)
            story.append(Paragraph(
                f"[{a.get('severity')}] {a.get('title')}: {a.get('message')}",
                ParagraphStyle("al", parent=styles["Normal"], fontSize=8, textColor=ac)))
            if a.get("suggested_action"):
                story.append(Paragraph(f"→ {a['suggested_action']}",
                                       ParagraphStyle("sa", parent=styles["Normal"],
                                                      fontSize=7, textColor=colors.blue)))
            story.append(Spacer(1,2*mm))

    # Disclaimer
    story += [
        HRFlowable(width="100%", thickness=.5, color=colors.grey), Spacer(1,3*mm),
        Paragraph(DISCLAIMER, ParagraphStyle("d", parent=styles["Normal"],
                                             fontSize=7, textColor=colors.grey)),
        Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC | An Explainable AI-Based Clinical Risk Screening System for CKD, Diabetes and Hypertension Academic Prototype",
                  ParagraphStyle("f", parent=styles["Normal"], fontSize=6,
                                 textColor=colors.grey)),
    ]
    doc.build(story)
    return buf.getvalue()
