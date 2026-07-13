"""
Demo Open Banking veri ureticisi.
Gercek bir banka API'sine baglanmak resmi lisans/ortaklik gerektirdigi
icin (BDDK Acik Bankacilik duzenlemeleri), bu modul ayni kullanici
deneyimini simule eder: kullanici bir banka secip "baglan" dedigin de,
gercekci gorunumlu 6 aylik bir islem gecmisi otomatik olusturulur.

Uretilen veri, gercek bir hesap ekstresine benzer sekilde cesitli
kategorilerde (market, yemek, ulasim, fatura, abonelik vb.) rastgele
ama makul tutarlarda islemler icerir - boylece kategorilendirme,
fraud detection, health score ve forecasting ozellikleri gercekci
bir veriyle hemen calisir.
"""
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

MARKET_VENDORS = ["Migros Market", "A101 Market", "Carrefour", "Bim Market", "Sok Market"]
YEMEK_VENDORS = ["Restoran Yemek", "Starbucks Kahve", "Yemeksepeti Siparis", "Kebapci Yemek"]
ULASIM_VENDORS = ["Shell Benzin", "Otopark Ucreti", "Taksi", "Istanbulkart Dolum"]
ALISVERIS_VENDORS = ["Trendyol Alisverisi", "Hepsiburada Siparis", "Zara Giyim"]
FATURA_VENDORS = ["Elektrik Faturasi", "Su Faturasi", "Internet Faturasi", "Telefon Faturasi"]
SAGLIK_VENDORS = ["Eczane", "Hastane Muayene"]

SUBSCRIPTIONS = {
    "Netflix Abonelik": Decimal("-99.90"),
    "Spotify Abonelik": Decimal("-59.99"),
    "Youtube Premium": Decimal("-79.99"),
}


def _rand_amount(low: float, high: float) -> Decimal:
    return Decimal(str(round(random.uniform(low, high), 2)))


def generate_demo_transactions(months: int = 6, base_salary: float = 22000) -> list[dict]:
    """
    'months' ay geriye giden, gercekci bir islem listesi uretir.
    Her ogenin alanlari: transaction_date (datetime), description (str),
    amount (Decimal).
    """
    today = date.today()
    rows: list[dict] = []

    # Ayları, en eskiden en yeniye dogru sirala
    month_starts = []
    year, month = today.year, today.month
    for _ in range(months):
        month_starts.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    month_starts.reverse()

    for i, (year, month) in enumerate(month_starts):
        salary = base_salary + i * 400  # hafif artan trend

        def safe_day(d: int) -> int:
            return min(d, 28)

        rows.append({
            "transaction_date": datetime(year, month, safe_day(3)),
            "description": "Maas Yatti",
            "amount": Decimal(str(round(salary, 2))),
        })

        for _ in range(random.randint(5, 7)):
            rows.append({
                "transaction_date": datetime(year, month, safe_day(random.randint(1, 28))),
                "description": random.choice(MARKET_VENDORS),
                "amount": -_rand_amount(150, 650),
            })

        for _ in range(random.randint(4, 6)):
            rows.append({
                "transaction_date": datetime(year, month, safe_day(random.randint(1, 28))),
                "description": random.choice(YEMEK_VENDORS),
                "amount": -_rand_amount(80, 450),
            })

        for _ in range(random.randint(3, 5)):
            rows.append({
                "transaction_date": datetime(year, month, safe_day(random.randint(1, 28))),
                "description": random.choice(ULASIM_VENDORS),
                "amount": -_rand_amount(100, 900),
            })

        for _ in range(random.randint(0, 2)):
            rows.append({
                "transaction_date": datetime(year, month, safe_day(random.randint(1, 28))),
                "description": random.choice(ALISVERIS_VENDORS),
                "amount": -_rand_amount(300, 1800),
            })

        for vendor in FATURA_VENDORS:
            rows.append({
                "transaction_date": datetime(year, month, safe_day(random.randint(1, 10))),
                "description": vendor,
                "amount": -_rand_amount(250, 750),
            })

        for vendor, amt in SUBSCRIPTIONS.items():
            rows.append({
                "transaction_date": datetime(year, month, safe_day(random.randint(1, 5))),
                "description": vendor,
                "amount": amt,
            })

        if random.random() < 0.6:
            rows.append({
                "transaction_date": datetime(year, month, safe_day(random.randint(1, 28))),
                "description": random.choice(SAGLIK_VENDORS),
                "amount": -_rand_amount(80, 600),
            })

    rows.sort(key=lambda r: r["transaction_date"])
    return rows
