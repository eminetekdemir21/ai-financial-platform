"""
Kural tabanli fraud (dolandiricilik) tespiti.
Her fonksiyon bir "sinyal" hesaplar: 0.0 (supheli degil) ile 1.0
(cok supheli) arasinda bir skor doner. fraud_service, bu sinyalleri
birlestirerek her islem icin nihai fraud_score'u hesaplar.

Neden tamamen kural tabanli (ML modeli degil):
- Fraud tespiti icin etiketli veri (gercek dolandiricilik ornekleri)
  gerekir, bu asamada elimizde yok.
- Kural tabanli sinyaller aciklanabilir ("neden supheli isaretlendi"
  sorusuna net cevap verir) - bankacilik/finans alaninda bu, kara
  kutu bir modelden cok daha degerlidir.
- Ileride yeterli etiketli veri biriktikce, bu kurallarin yanina/
  yerine denetimli bir ML modeli (orn. Isolation Forest, XGBoost)
  eklenebilir; kural sinyalleri o zaman ozellik (feature) olarak
  kullanilabilir.
"""
from __future__ import annotations

from datetime import datetime, timedelta


def signal_large_amount(amount: float, mean: float, stdev: float) -> float:
    """
    Islem tutari, hesabin ortalama islem tutarindan ne kadar sapiyor
    (z-score / standart sapma cinsinden uzaklik). 3 std'nin uzerindeki
    sapmalar supheli sayilir.
    """
    if stdev == 0:
        return 0.0
    z = abs(amount - mean) / stdev
    if z < 3:
        return 0.0
    # z=3 -> 0.5, z=6 ve uzeri -> 1.0 (dogrusal olcekleme, tavanli)
    return min((z - 3) / 6 + 0.5, 1.0)


def signal_odd_hour(transaction_date: datetime) -> float:
    """
    Gece 00:00 - 05:00 arasi yapilan islemler, normal harcama
    saatlerinin disinda oldugu icin hafif supheli sayilir.
    Not: Saat bilgisi olmayan (sadece tarih iceren) CSV/Excel
    kayitlarinda saat varsayilan olarak 00:00 kabul edilir - bu
    durumda bu sinyal her zaman tetiklenir, bu beklenen bir durumdur.
    """
    if transaction_date.hour < 5:
        return 0.4
    return 0.0


def signal_duplicate(
    amount: float,
    transaction_date: datetime,
    other_transactions: list[tuple[float, datetime]],
    window_minutes: int = 5,
) -> float:
    """
    Ayni tutarda, kisa bir zaman penceresi icinde (varsayilan 5 dk)
    baska bir islem varsa, kopya/mukerrer odeme suphesi sayilir
    (orn. yanlislikla iki kez odeme, ya da test amacli kucuk
    dolandiricilik denemeleri).
    """
    window = timedelta(minutes=window_minutes)
    for other_amount, other_date in other_transactions:
        if other_amount == amount and abs(other_date - transaction_date) <= window:
            return 0.7
    return 0.0


def signal_high_frequency(
    transaction_date: datetime,
    other_dates: list[datetime],
    window_minutes: int = 10,
    threshold: int = 5,
) -> float:
    """
    Kisa bir zaman penceresinde (varsayilan 10 dk) belirli bir sayidan
    (varsayilan 5) fazla islem varsa, hesap ele gecirilmis veya
    otomatik (bot) bir saldiri olabilecegi icin supheli sayilir.
    """
    window = timedelta(minutes=window_minutes)
    count = sum(1 for d in other_dates if abs(d - transaction_date) <= window)
    if count >= threshold:
        return min(count / (threshold * 2), 1.0)
    return 0.0
