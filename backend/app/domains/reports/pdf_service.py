"""
PDF Report Generator - Gelismis versiyon.
Health Score, Savings Coach onerileri, grafik ve Turkce karakter destegi.
"""
import io
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie

from app.domains.transactions.models import Account, Transaction

# Renkler
DARK_BG = colors.HexColor("#1a1d27")
BLUE = colors.HexColor("#5b8dee")
GREEN = colors.HexColor("#00d68f")
RED = colors.HexColor("#ff6b6b")
AMBER = colors.HexColor("#ffa940")
PURPLE = colors.HexColor("#7c6de8")
LIGHT_GRAY = colors.HexColor("#f8fafc")
MID_GRAY = colors.HexColor("#64748b")
DARK_TEXT = colors.HexColor("#1e293b")
BORDER = colors.HexColor("#e2e8f0")

CAT_COLORS = [
    colors.HexColor("#5b8dee"),
    colors.HexColor("#00d68f"),
    colors.HexColor("#ff6b6b"),
    colors.HexColor("#ffa940"),
    colors.HexColor("#7c6de8"),
    colors.HexColor("#ec4899"),
    colors.HexColor("#14b8a6"),
    colors.HexColor("#f97316"),
    colors.HexColor("#94a3b8"),
]

SUBSCRIPTION_KEYWORDS = [
    "netflix", "spotify", "youtube", "amazon prime", "evernote",
    "icloud", "dropbox", "microsoft 365", "adobe", "apple tv",
    "disney", "blutv", "gain tv", "mubi", "linkedin premium",
]


def generate_pdf(db: Session, account: Account) -> bytes:
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account.id)
        .order_by(Transaction.transaction_date.desc())
        .all()
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"Finansal Rapor - {account.bank_name}",
    )

    body_style = ParagraphStyle("body", fontSize=10, textColor=DARK_TEXT, spaceAfter=4, leading=14)
    section_style = ParagraphStyle("section", fontSize=13, textColor=DARK_TEXT, spaceBefore=14, spaceAfter=8, fontName="Helvetica-Bold")
    small_style = ParagraphStyle("small", fontSize=9, textColor=MID_GRAY)
    footer_style = ParagraphStyle("footer", fontSize=8, textColor=MID_GRAY, alignment=TA_CENTER)

    story = []

    # === BAŞLIK KUTUSU ===
    now_tr = datetime.now(timezone.utc) + timedelta(hours=3)
    header_data = [[
        Paragraph(f"<font size=18><b>Finansal Analiz Raporu</b></font>", ParagraphStyle("h", fontSize=18, textColor=colors.white, fontName="Helvetica-Bold")),
        Paragraph(
            f"<font size=10 color='#a0aec0'>{account.bank_name} ({account.account_number_masked})<br/>"
            f"Olusturulma: {now_tr.strftime('%d.%m.%Y %H:%M')}</font>",
            ParagraphStyle("hs", fontSize=10, textColor=colors.HexColor("#a0aec0"), leading=16)
        ),
    ]]
    header_table = Table(header_data, colWidths=[10*cm, 7*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))

    if not transactions:
        story.append(Paragraph("Bu hesapta henuz islem bulunmamaktadir.", body_style))
        doc.build(story)
        return buffer.getvalue()

    # Hesaplamalar
    total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    total_expense = sum(abs(float(t.amount)) for t in transactions if float(t.amount) < 0)
    net = total_income - total_expense
    savings_rate = (net / total_income * 100) if total_income > 0 else 0
    flagged_count = sum(1 for t in transactions if t.is_flagged)
    dates = [t.transaction_date for t in transactions]

    category_totals: dict[str, float] = defaultdict(float)
    category_counts: dict[str, int] = defaultdict(int)
    for t in transactions:
        if float(t.amount) < 0:
            cat = t.category or "kategorisiz"
            category_totals[cat] += abs(float(t.amount))
            category_counts[cat] += 1

    # === ÖZET METRİK KUTULARI ===
    story.append(Paragraph("Genel Ozet", section_style))

    def metric_box(label, value, color=DARK_TEXT):
        return [Paragraph(f"<font size=9 color='#64748b'>{label}</font>",
                          ParagraphStyle("ml", fontSize=9, textColor=MID_GRAY, leading=12)),
                Paragraph(f"<font size=14><b>{value}</b></font>",
                          ParagraphStyle("mv", fontSize=14, textColor=color, fontName="Helvetica-Bold", leading=18))]

    metrics_data = [
        [metric_box("Toplam Islem", str(len(transactions))),
         metric_box("Toplam Gelir", f"{total_income:,.0f} TL", GREEN),
         metric_box("Toplam Gider", f"{total_expense:,.0f} TL", RED)],
        [metric_box("Net Nakit", f"{net:,.0f} TL", BLUE),
         metric_box("Tasarruf Orani", f"%{savings_rate:.1f}", GREEN if savings_rate >= 20 else AMBER),
         metric_box("Supheli Islem", f"{flagged_count} adet", RED if flagged_count > 0 else GREEN)],
    ]

    for row in metrics_data:
        t = Table([row], colWidths=[5.7*cm, 5.7*cm, 5.7*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.15*cm))

    story.append(Spacer(1, 0.3*cm))

    # === HEALTH SCORE ===
    story.append(Paragraph("Finansal Saglik Skoru", section_style))

    score_color = GREEN if savings_rate >= 30 else AMBER if savings_rate >= 15 else RED
    grade = "A" if savings_rate >= 30 else "B" if savings_rate >= 20 else "C" if savings_rate >= 10 else "D"

    health_data = [
        ["Faktur", "Puan", "Degerlendirme"],
        ["Tasarruf Orani", f"{min(int(savings_rate*3), 100)}/100", "Mukemmel" if savings_rate >= 30 else "Iyi" if savings_rate >= 20 else "Gelistirilebilir"],
        ["Gider Cesitliligi", f"{min(len(category_totals)*12, 100)}/100", f"{len(category_totals)} kategori"],
        ["Fraud Riski", f"{max(100 - flagged_count*5, 0)}/100", "Temiz" if flagged_count == 0 else f"{flagged_count} supheli"],
        ["Genel Skor", f"{min(int(savings_rate*2), 100)}/100", f"Not: {grade}"],
    ]

    health_table = Table(health_data, colWidths=[6*cm, 4*cm, 7*cm])
    health_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GRAY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TEXTCOLOR", (0, 1), (-1, -1), DARK_TEXT),
        ("FONTNAME", (0, 4), (0, 4), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 4), (1, 4), score_color),
        ("FONTNAME", (1, 4), (1, 4), "Helvetica-Bold"),
    ]))
    story.append(health_table)
    story.append(Spacer(1, 0.3*cm))

    # === KATEGORİ ANALİZİ + GRAFİK ===
    story.append(Paragraph("Kategori Bazli Gider Analizi", section_style))

    sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)

    # Pie chart
    if sorted_cats and total_expense > 0:
        try:
            d = Drawing(400, 180)
            pie = Pie()
            pie.x = 10
            pie.y = 10
            pie.width = 160
            pie.height = 160
            pie.data = [v for _, v in sorted_cats[:8]]
            pie.labels = None
            for i in range(len(pie.data)):
                pie.slices[i].fillColor = CAT_COLORS[i % len(CAT_COLORS)]
                pie.slices[i].strokeColor = colors.white
                pie.slices[i].strokeWidth = 1
            for i, (cat, amt) in enumerate(sorted_cats[:8]):
                pct = amt / total_expense * 100
                r = Rect(185, 155 - i * 20, 10, 10,
                         fillColor=CAT_COLORS[i % len(CAT_COLORS)],
                         strokeColor=None)
                s = String(200, 156 - i * 20,
                           f"{cat.capitalize()[:14]}: %{pct:.1f}",
                           fontSize=8, fillColor="#1e293b")
                d.add(r)
                d.add(s)
            d.add(pie)
            story.append(d)
        except Exception:
            pass

    cat_data = [["Kategori", "Islem", "Toplam Gider", "Oran"]]
    for cat, amt in sorted_cats:
        pct = amt / total_expense * 100 if total_expense > 0 else 0
        cat_data.append([cat.capitalize(), str(category_counts[cat]), f"{amt:,.2f} TL", f"%{pct:.1f}"])

    cat_table = Table(cat_data, colWidths=[5*cm, 3*cm, 5*cm, 4*cm])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GRAY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TEXTCOLOR", (0, 1), (-1, -1), DARK_TEXT),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 0.3*cm))

    # === SAVINGS COACH ÖNERİLERİ ===
    story.append(Paragraph("Tasarruf Onerileri", section_style))

    REDUCIBLE = {
        "yemek": 0.25, "alisveris": 0.20, "ulasim": 0.15, "market": 0.10,
    }
    tips = []
    for cat, pct in REDUCIBLE.items():
        if cat in category_totals and category_totals[cat] / len(set(t.transaction_date.strftime("%Y-%m") for t in transactions)) > 200:
            monthly = category_totals[cat] / max(len(set(t.transaction_date.strftime("%Y-%m") for t in transactions)), 1)
            saving = monthly * pct
            tips.append((cat.capitalize(), f"%{int(pct*100)} azaltma", f"{saving:,.0f} TL/ay", f"{saving*12:,.0f} TL/yil"))

    # Abonelik kontrolü
    sub_total = sum(abs(float(t.amount)) for t in transactions
                    if any(kw in t.description.lower() for kw in SUBSCRIPTION_KEYWORDS))
    if sub_total > 0:
        months_count = max(len(set(t.transaction_date.strftime("%Y-%m") for t in transactions)), 1)
        monthly_sub = sub_total / months_count
        tips.append(("Abonelikler", "Gereksizleri iptal et", f"{monthly_sub*0.3:,.0f} TL/ay", f"{monthly_sub*0.3*12:,.0f} TL/yil"))

    if tips:
        tips_data = [["Kategori", "Oneri", "Aylik Tasarruf", "Yillik Tasarruf"]]
        tips_data.extend(tips)
        tips_table = Table(tips_data, colWidths=[4*cm, 6*cm, 4*cm, 4*cm])
        tips_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00d68f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0fff8"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TEXTCOLOR", (0, 1), (-1, -1), DARK_TEXT),
            ("TEXTCOLOR", (2, 1), (3, -1), colors.HexColor("#059669")),
            ("FONTNAME", (2, 1), (3, -1), "Helvetica-Bold"),
            ("ALIGN", (2, 0), (3, -1), "CENTER"),
        ]))
        story.append(tips_table)
    else:
        story.append(Paragraph("Harcamalariniz optimize gorunuyor.", body_style))

    story.append(Spacer(1, 0.3*cm))

    # === FRAUD RAPORU ===
    if flagged_count > 0:
        story.append(Paragraph("Supheli Islem Raporu", section_style))
        story.append(Paragraph(f"Toplam {flagged_count} adet supheli islem tespit edildi.", body_style))

        fraud_data = [["Tarih", "Aciklama", "Tutar", "Skor"]]
        for t in [tx for tx in transactions if tx.is_flagged][:15]:
            fraud_data.append([
                t.transaction_date.strftime("%d.%m.%Y"),
                t.description[:35] + ("..." if len(t.description) > 35 else ""),
                f"{float(t.amount):,.2f} TL",
                str(t.fraud_score or "-"),
            ])

        fraud_table = Table(fraud_data, colWidths=[3*cm, 7.5*cm, 4*cm, 2.5*cm])
        fraud_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), RED),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fff5f5"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TEXTCOLOR", (0, 1), (-1, -1), DARK_TEXT),
        ]))
        story.append(fraud_table)
        story.append(Spacer(1, 0.3*cm))

    # === SON İŞLEMLER ===
    story.append(Paragraph("Son 20 Islem", section_style))

    tx_data = [["Tarih", "Aciklama", "Kategori", "Tutar"]]
    for t in transactions[:20]:
        amt = float(t.amount)
        tx_data.append([
            t.transaction_date.strftime("%d.%m.%Y"),
            t.description[:28] + ("..." if len(t.description) > 28 else ""),
            (t.category or "kategorisiz").capitalize(),
            f"{amt:+,.2f} TL",
        ])

    tx_table = Table(tx_data, colWidths=[3*cm, 7*cm, 4*cm, 3*cm])
    tx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GRAY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TEXTCOLOR", (0, 1), (-1, -1), DARK_TEXT),
        ("ALIGN", (3, 1), (3, -1), "RIGHT"),
    ]))
    story.append(tx_table)

    # === FOOTER ===
    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Bu rapor AI Financial Platform tarafindan otomatik olarak olusturulmustur. "
        "Yatirim tavsiyesi niteliginde degildir.",
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue()
