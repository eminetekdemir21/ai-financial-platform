"""
PDF Report Generator.
Kullanicinin finansal analizini tek bir PDF raporuna toplar.
"""
import io
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.domains.transactions.models import Account, Transaction

# Renkler
DARK_BG = colors.HexColor("#1a1d27")
BLUE = colors.HexColor("#5b8dee")
GREEN = colors.HexColor("#00d68f")
RED = colors.HexColor("#ff6b6b")
AMBER = colors.HexColor("#ffa940")
LIGHT_GRAY = colors.HexColor("#f8fafc")
MID_GRAY = colors.HexColor("#64748b")
DARK_TEXT = colors.HexColor("#1e293b")
BORDER = colors.HexColor("#e2e8f0")


def generate_pdf(db: Session, account: Account) -> bytes:
    """
    Hesabın tüm finansal analizini PDF olarak üretir.
    """
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account.id)
        .order_by(Transaction.transaction_date.desc())
        .all()
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f"Finansal Rapor - {account.bank_name}",
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Özel stiller ---
    title_style = ParagraphStyle("title", fontSize=18, textColor=DARK_TEXT, spaceAfter=12, spaceBefore=4, fontName="Helvetica-Bold", leading=24)
    subtitle_style = ParagraphStyle("subtitle", fontSize=10, textColor=MID_GRAY, spaceAfter=8, leading=14)
    section_style = ParagraphStyle("section", fontSize=13, textColor=DARK_TEXT, spaceBefore=16, spaceAfter=8, fontName="Helvetica-Bold")
    body_style = ParagraphStyle("body", fontSize=10, textColor=DARK_TEXT, spaceAfter=4, leading=14)
    small_style = ParagraphStyle("small", fontSize=9, textColor=MID_GRAY, spaceAfter=2)

    # === BAŞLIK ===
    story.append(Paragraph("Finansal Analiz Raporu", title_style))
    story.append(Paragraph(
        f"{account.bank_name} ({account.account_number_masked}) - Olusturulma: {(datetime.now(timezone.utc) + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M')}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 0.4*cm))

    if not transactions:
        story.append(Paragraph("Bu hesapta henuz islem bulunmamaktadir.", body_style))
        doc.build(story)
        return buffer.getvalue()

    # === GENEL ÖZET ===
    total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    total_expense = sum(abs(float(t.amount)) for t in transactions if float(t.amount) < 0)
    net = total_income - total_expense
    tx_count = len(transactions)
    flagged_count = sum(1 for t in transactions if t.is_flagged)

    dates = [t.transaction_date for t in transactions]
    date_range = f"{min(dates).strftime('%d.%m.%Y')} - {max(dates).strftime('%d.%m.%Y')}"

    story.append(Paragraph("Genel Ozet", section_style))

    summary_data = [
        ["Metrik", "Deger"],
        ["Toplam Islem Sayisi", str(tx_count)],
        ["Analiz Donemi", date_range],
        ["Toplam Gelir", f"{total_income:,.2f} TL"],
        ["Toplam Gider", f"{total_expense:,.2f} TL"],
        ["Net Nakit Akisi", f"{net:,.2f} TL"],
        ["Tasarruf Orani", f"%{(net/total_income*100):.1f}" if total_income > 0 else "-"],
        ["Supheli Islem", f"{flagged_count} adet"],
    ]

    summary_table = Table(summary_data, colWidths=[8*cm, 8*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
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
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.4*cm))

    # === KATEGORİ DÖKÜMÜ ===
    story.append(Paragraph("Kategori Bazli Gider Analizi", section_style))

    category_totals: dict[str, float] = defaultdict(float)
    category_counts: dict[str, int] = defaultdict(int)
    for t in transactions:
        if float(t.amount) < 0:
            cat = t.category or "kategorisiz"
            category_totals[cat] += abs(float(t.amount))
            category_counts[cat] += 1

    cat_data = [["Kategori", "Islem Sayisi", "Toplam Gider", "Oran"]]
    for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        pct = amt / total_expense * 100 if total_expense > 0 else 0
        cat_data.append([
            cat.capitalize(),
            str(category_counts[cat]),
            f"{amt:,.2f} TL",
            f"%{pct:.1f}",
        ])

    cat_table = Table(cat_data, colWidths=[5*cm, 3*cm, 5*cm, 3*cm])
    cat_table.setStyle(TableStyle([
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
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 0.4*cm))

    # === FRAUD RAPORU ===
    if flagged_count > 0:
        story.append(Paragraph("Supheli Islem Raporu", section_style))
        story.append(Paragraph(
            f"Toplam {flagged_count} adet supheli islem tespit edildi. Asagida detaylar listelenmistir.",
            body_style
        ))

        fraud_data = [["Tarih", "Aciklama", "Tutar", "Fraud Skoru"]]
        flagged = [t for t in transactions if t.is_flagged]
        for t in flagged[:20]:
            fraud_data.append([
                t.transaction_date.strftime("%d.%m.%Y"),
                t.description[:35] + ("..." if len(t.description) > 35 else ""),
                f"{float(t.amount):,.2f} TL",
                str(t.fraud_score or "-"),
            ])

        fraud_table = Table(fraud_data, colWidths=[3*cm, 7*cm, 4*cm, 2*cm])
        fraud_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), RED),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fff5f5"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TEXTCOLOR", (0, 1), (-1, -1), DARK_TEXT),
        ]))
        story.append(fraud_table)
        story.append(Spacer(1, 0.4*cm))

    # === SON İŞLEMLER ===
    story.append(Paragraph("Son 20 Islem", section_style))

    tx_data = [["Tarih", "Aciklama", "Kategori", "Tutar"]]
    for t in transactions[:20]:
        amt = float(t.amount)
        tx_data.append([
            t.transaction_date.strftime("%d.%m.%Y"),
            t.description[:30] + ("..." if len(t.description) > 30 else ""),
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
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
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
        ParagraphStyle("footer", fontSize=8, textColor=MID_GRAY, alignment=TA_CENTER)
    ))

    doc.build(story)
    return buffer.getvalue()
