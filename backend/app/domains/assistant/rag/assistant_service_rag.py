from collections import defaultdict
import time
from sqlalchemy.orm import Session
from app.core.config import settings
from app.domains.assistant.rag.embedding_service import retrieve_similar
from app.domains.transactions.models import Account, Transaction

SYSTEM_PROMPT = """Sen bir kisisel finans asistanisin. Kullanicinin banka islem verilerine dayanarak Turkce, net ve yardimci cevaplar veriyorsun.

Kurallar:
- SADECE sana verilen islem verisine dayan, uydurma rakam kullanma.
- Veri yetersizse bunu acikca belirt.
- Kisa, anlasilir ve samimi bir dil kullan.
- Kesin yatirim tavsiyesi verme.
- Supheli (fraud) isaretli islemler varsa dikkat cek.
"""

class AssistantNotConfiguredError(Exception):
    pass

def is_configured() -> bool:
    return bool(settings.LLM_API_KEY)

def build_full_context(db: Session, account: Account) -> str:
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account.id)
        .order_by(Transaction.transaction_date.desc())
        .limit(500)
        .all()
    )

    if not transactions:
        return f"Hesap: {account.bank_name}. Henuz islem yok."

    total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    total_expense = sum(abs(float(t.amount)) for t in transactions if float(t.amount) < 0)

    category_totals: dict[str, float] = defaultdict(float)
    category_counts: dict[str, int] = defaultdict(int)
    for t in transactions:
        if float(t.amount) < 0:
            cat = t.category or "kategorisiz"
            category_totals[cat] += abs(float(t.amount))
            category_counts[cat] += 1

    monthly: dict[str, dict] = defaultdict(lambda: {"gelir": 0.0, "gider": 0.0, "count": 0})
    for t in transactions:
        ay = t.transaction_date.strftime("%Y-%m")
        amt = float(t.amount)
        if amt > 0:
            monthly[ay]["gelir"] += amt
        else:
            monthly[ay]["gider"] += abs(amt)
        monthly[ay]["count"] += 1

    lines = [
        f"=== HESAP: {account.bank_name} ({account.account_number_masked}) ===",
        f"Toplam islem: {len(transactions)}",
        f"Toplam gelir: {total_income:.2f} TRY",
        f"Toplam gider: {total_expense:.2f} TRY",
        f"Net: {(total_income - total_expense):.2f} TRY",
        "",
        "=== KATEGORI OZETI ===",
    ]
    for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  {cat}: {amt:.2f} TRY ({category_counts[cat]} islem)")

    lines.append("")
    lines.append("=== AY BAZLI OZET ===")
    for ay in sorted(monthly.keys(), reverse=True):
        m = monthly[ay]
        lines.append(f"  {ay}: Gelir {m['gelir']:.2f} TRY | Gider {m['gider']:.2f} TRY | {m['count']} islem")

    lines.append("")
    lines.append("=== TUM ISLEMLER ===")
    for t in transactions:
        flag = " [SUPHELI]" if t.is_flagged else ""
        lines.append(
            f"  {t.transaction_date.date()} | {t.description} | "
            f"{float(t.amount):.2f} TRY | {t.category or 'kategorisiz'}{flag}"
        )

    return "\n".join(lines)


def ask(db: Session, account: Account, user_message: str) -> str:
    if not is_configured():
        raise AssistantNotConfiguredError()

    from google import genai
    from google.genai import types

    full_context = build_full_context(db, account)
    client = genai.Client(api_key=settings.LLM_API_KEY)
    prompt = f"Kullanicinin finansal verileri:\n{full_context}\n\nKullanicinin sorusu: {user_message}"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.3)
        )
        return response.text
    except Exception as e:
        error_message = str(e)
        if "503" in error_message or "UNAVAILABLE" in error_message:
            for _ in range(2):
                time.sleep(2)
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.3)
                    )
                    return response.text
                except Exception:
                    pass
            return "Yapay zeka servisi su an yogun. Lutfen tekrar deneyin."
        return f"Hata: {error_message}"
