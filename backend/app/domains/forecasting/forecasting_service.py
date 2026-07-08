"""
Time series forecasting domain service.
Islemleri aylara gore gruplayip, gelecek ayin net nakit akisini
(gelir - gider) tahmin eder. Yeterli veri (en az 2 farkli ay) varsa
basit bir dogrusal trend (en kucuk kareler) kullanilir; degilse,
mevcut tek ay verisinin ortalamasi "duz projeksiyon" olarak kullanilir
ve bu durum yanitta acikca belirtilir (confidence: low).

Neden agir bir model (ARIMA, Prophet vb.) degil:
- Elimizdeki veri hacmi (bir kullanicinin birkac aylik ekstre verisi)
  bu modelleri anlamli kilacak kadar buyuk degil.
- Dogrusal trend + ortalama fallback, az veriyle bile aciklanabilir
  ve makul bir ilk tahmin verir - gercek fintech MVP'lerinin bu
  asamada tercih ettigi yaklasim budur.

Not: Account.current_balance alani su an baska hicbir akista
guncellenmiyor (her zaman 0). Bu yuzden "mevcut bakiye" burada,
hesabin tum islemlerinin toplami uzerinden turetilir - gercege
daha yakin bir tahmin sunar.
"""
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.domains.transactions.models import Account, Transaction


def _month_key(d: datetime) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _monthly_net_cashflow(transactions: list[Transaction]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for tx in transactions:
        key = _month_key(tx.transaction_date)
        totals[key] += float(tx.amount)
    return dict(sorted(totals.items()))


def _linear_forecast(values: list[float]) -> float:
    """
    En kucuk kareler (least squares) ile basit dogrusal trend.
    x = 0, 1, 2... (ay sirasi), y = o ayin net nakit akisi.
    Bir sonraki x icin y tahmini dondurulur.
    """
    n = len(values)
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    numerator = sum((xs[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((xs[i] - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return y_mean
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    next_x = n
    return slope * next_x + intercept


def forecast_next_month(db: Session, account: Account) -> dict:
    """
    Hesabin gecmis islemlerinden gelecek ayin net nakit akisini ve
    projekte edilen bakiyesini tahmin eder.
    """
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account.id)
        .order_by(Transaction.transaction_date.asc())
        .all()
    )

    current_balance_estimate = sum(float(tx.amount) for tx in transactions)

    if not transactions:
        return {
            "method": "insufficient_data",
            "confidence": "none",
            "predicted_next_month_net": 0.0,
            "current_balance_estimate": 0.0,
            "projected_balance": 0.0,
            "monthly_history": {},
            "message": "Tahmin yapmak icin yeterli islem verisi yok.",
        }

    monthly = _monthly_net_cashflow(transactions)
    months = list(monthly.keys())
    values = list(monthly.values())

    if len(months) >= 2:
        predicted = _linear_forecast(values)
        method = "linear_trend"
        confidence = "medium" if len(months) < 4 else "high"
        message = f"Son {len(months)} ayin trendine gore hesaplandi."
    else:
        predicted = values[0]
        method = "average_fallback"
        confidence = "low"
        message = (
            "Sadece 1 aylik veri mevcut, bu ayin net nakit akisi duz "
            "projeksiyon olarak kullanildi. Daha fazla veri biriktikce "
            "tahmin dogrulugu artacaktir."
        )

    projected_balance = current_balance_estimate + predicted

    return {
        "method": method,
        "confidence": confidence,
        "predicted_next_month_net": round(predicted, 2),
        "current_balance_estimate": round(current_balance_estimate, 2),
        "projected_balance": round(projected_balance, 2),
        "monthly_history": {k: round(v, 2) for k, v in monthly.items()},
        "message": message,
    }
