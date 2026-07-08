from collections import defaultdict
import time
from sqlalchemy.orm import Session
from app.core.config import settings
from app.domains.assistant.rag.embedding_service import retrieve_similar
from app.domains.transactions.models import Account, Transaction

SYSTEM_PROMPT = "Sen bir kisisel finans asistanisin. Kullanicinin banka islem verilerine dayanarak Turkce, net ve yardimci cevaplar veriyorsun."

class AssistantNotConfiguredError(Exception): pass
def is_configured() -> bool: return bool(settings.LLM_API_KEY)

def build_summary_context(db: Session, account: Account) -> str:
    transactions = db.query(Transaction).filter(Transaction.account_id == account.id).all()
    if not transactions: return f"Hesap: {account.bank_name}. Henuz islem yok."
    total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    total_expense = sum(float(t.amount) for t in transactions if float(t.amount) < 0)
    category_totals = defaultdict(float)
    for t in transactions:
        if float(t.amount) < 0: category_totals[t.category or "kategorisiz"] += float(t.amount)
    lines = ["=== HESAP OZETI ===", f"Toplam gelir: {total_income:.2f} TRY", f"Toplam gider: {abs(total_expense):.2f} TRY", "Kategori bazinda giderler:"]
    for cat, amt in sorted(category_totals.items(), key=lambda x: x[1]): lines.append(f"  - {cat}: {abs(amt):.2f} TRY")
    return "\n".join(lines)

def build_retrieved_context(retrieved: list[Transaction]) -> str:
    if not retrieved: return ""
    lines = ["\n=== SORUYLA ALAKALI ISLEMLER ==="]
    for t in retrieved: lines.append(f"  - {t.transaction_date.date()} | {t.description} | {float(t.amount):.2f} TRY")
    return "\n".join(lines)

def ask(db: Session, account: Account, user_message: str) -> str:
    if not is_configured(): raise AssistantNotConfiguredError()
    from google import genai
    from google.genai import types

    retrieved = retrieve_similar(db=db, account_id=account.id, query=user_message, top_k=8)
    summary = build_summary_context(db, account)
    full_context = summary + build_retrieved_context(retrieved)

    client = genai.Client(api_key=settings.LLM_API_KEY)
    model_name = "gemini-2.5-flash"

    prompt = f"Kullanicinin finansal verileri:\n{full_context}\n\nKullanicinin sorusu: {user_message}"
    try:
        response = client.models.generate_content(
            model=model_name,
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
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.3
                        )
                    )
                    return response.text
                except Exception:
                    pass

            return "Yapay zekâ servisi şu anda yoğun olduğu için isteğiniz işlenemedi. Lütfen birkaç saniye sonra tekrar deneyiniz."

        return f"Gemini RAG API hatası oluştu: {error_message}"

