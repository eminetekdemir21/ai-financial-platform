"""
AI Financial Assistant domain service.
Kullanicinin banka islem verilerinden bir metin ozeti (context)
olusturur, bunu bir sistem promptuyla birlikte LLM'e (Google Gemini)
gonderip, kullanicinin sorusuna kendi verisine dayanan bir cevap uretir.

Neden RAG/embedding degil, duz metin context: Tek bir hesabin islem
hacmi (onlarca-yuzlerce satir) bir LLM'in context penceresine kolayca
sigar - bu olcekte vektor veritabani/embedding aramasi gereksiz
karmasiklik katar. Veri hacmi buyudukce (binlerce islem) bu yaklasim
RAG'a evrilebilir.
"""
from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.transactions.models import Account, Transaction

SYSTEM_PROMPT = """Sen bir kisisel finans asistanisin. Kullanicinin banka
islem verilerine dayanarak Turkce, net ve yardimci cevaplar veriyorsun.

Kurallar:
- SADECE sana asagida verilen islem verisine dayan, uydurma rakam kullanma.
- Veri yetersizse bunu acikca belirt.
- Kisa, anlasilir ve samimi bir dil kullan.
- Kesin yatirim tavsiyesi verme; genel bilgilendirme ve gozlem sun.
- Supheli (fraud) isaretli islemler varsa, sorulmasa bile kisaca dikkat
  cek.
"""


class AssistantNotConfiguredError(Exception):
    """LLM_API_KEY .env dosyasinda tanimlanmamis oldugunda firlatilir."""


def is_configured() -> bool:
    return bool(settings.LLM_API_KEY)


def build_context(db: Session, account: Account) -> str:
    """
    Hesabin islemlerinden LLM'e verilecek duz metin ozetini olusturur:
    toplam gelir/gider, kategori kirilimi, fraud isaretli islemler ve
    son islemlerin listesi.
    """
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account.id)
        .order_by(Transaction.transaction_date.desc())
        .limit(200)
        .all()
    )

    if not transactions:
        return f"Hesap: {account.bank_name} ({account.account_number_masked}). Bu hesapta henuz hic islem yok."

    total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    total_expense = sum(float(t.amount) for t in transactions if float(t.amount) < 0)

    category_totals: dict[str, float] = defaultdict(float)
    for t in transactions:
        if float(t.amount) < 0:
            category_totals[t.category or "kategorisiz"] += float(t.amount)

    flagged = [t for t in transactions if t.is_flagged]

    lines = [
        f"Hesap: {account.bank_name} ({account.account_number_masked})",
        f"Toplam islem sayisi: {len(transactions)}",
        f"Toplam gelir: {total_income:.2f} TRY",
        f"Toplam gider: {abs(total_expense):.2f} TRY",
        "",
        "Kategori bazinda giderler:",
    ]
    for cat, amt in sorted(category_totals.items(), key=lambda x: x[1]):
        lines.append(f"  - {cat}: {abs(amt):.2f} TRY")

    if flagged:
        lines.append("")
        lines.append(f"Supheli (fraud) isaretli {len(flagged)} islem var:")
        for t in flagged[:5]:
            lines.append(
                f"  - {t.transaction_date.date()} | {t.description} | "
                f"{float(t.amount):.2f} TRY | fraud_score: {t.fraud_score}"
            )

    lines.append("")
    lines.append("Son islemler (en yeniden eskiye):")
    for t in transactions[:15]:
        lines.append(
            f"  - {t.transaction_date.date()} | {t.description} | "
            f"{float(t.amount):.2f} TRY | kategori: {t.category or '-'}"
        )

    return "\n".join(lines)


def ask(db: Session, account: Account, user_message: str) -> str:
    """
    Kullanicinin sorusunu, hesabin islem ozetiyle birlikte Gemini'ye
    gonderir, cevabi metin olarak dondurur.
    """
    if not is_configured():
        raise AssistantNotConfiguredError()

    import google.generativeai as genai

    context = build_context(db, account)

    genai.configure(api_key=settings.LLM_API_KEY)
    model = genai.GenerativeModel(
        model_name=settings.LLM_MODEL,
        system_instruction=SYSTEM_PROMPT,
    )
    response = model.generate_content(
        f"Kullanicinin finansal verileri:\n{context}\n\n"
        f"Kullanicinin sorusu: {user_message}"
    )
    return response.text
