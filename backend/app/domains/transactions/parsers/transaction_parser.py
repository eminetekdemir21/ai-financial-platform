import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

import pandas as pd


@dataclass
class ParsedTransaction:
    """Parser'dan cikan ham, temizlenmis islem verisi."""
    amount: Decimal
    description: str
    merchant: str | None
    transaction_date: datetime
    source: str


class TransactionParser:
    """
    CSV ve Excel banka ekstrelerini standart formata donusturur.

    Desteklenen sutun adlari (buyuk/kucuk harf fark etmez):
    - Tutar: amount, tutar, miktar, borc, alacak, debit, credit
    - Aciklama: description, aciklama, islem, narration
    - Tarih: date, tarih, transaction_date, islem_tarihi
    - Satici: merchant, satici, karsi_taraf (opsiyonel)
    """

    AMOUNT_COLS = ["amount", "tutar", "miktar", "borc", "alacak", "debit", "credit"]
    DESC_COLS = ["description", "aciklama", "islem", "narration", "detail"]
    DATE_COLS = ["date", "tarih", "transaction_date", "islem_tarihi", "valuedate"]
    MERCHANT_COLS = ["merchant", "satici", "karsi_taraf", "alici", "recipient"]

    def parse_csv(self, content: bytes) -> list[ParsedTransaction]:
        """
        CSV dosyasini parse eder. Pandas'in firlattigi dusuk seviyeli
        hatalar (bos dosya, bozuk format vb.) burada yakalanip kullanici
        icin anlamli Turkce mesajlara cevrilir.
        """
        if not content or not content.strip():
            raise ValueError(
                "Yuklenen dosya bos gorunuyor. Lutfen icinde veri olan "
                "bir CSV dosyasi secin."
            )
        try:
            df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding="latin-1")
            except Exception:
                raise ValueError(
                    "Dosyanin karakter kodlamasi taninamadi. Dosyayi UTF-8 "
                    "formatinda kaydedip tekrar deneyin."
                )
        except pd.errors.EmptyDataError:
            raise ValueError(
                "Dosyada okunacak sutun/veri bulunamadi. Dosyanin ilk "
                "satirinda sutun basliklari (orn. tarih, aciklama, tutar) "
                "oldugundan emin olun."
            )
        except pd.errors.ParserError:
            raise ValueError(
                "CSV dosyasi okunurken bir format hatasi olustu. Dosyanin "
                "gecerli bir CSV (virgulle ayrilmis) dosyasi oldugundan "
                "emin olun."
            )
        return self._parse_dataframe(df, source="csv")

    def parse_excel(self, content: bytes) -> list[ParsedTransaction]:
        """
        Excel dosyasini parse eder. Bozuk/desteklenmeyen dosyalarda
        anlamli bir Turkce hata mesaji dondurur.
        """
        if not content:
            raise ValueError(
                "Yuklenen dosya bos gorunuyor. Lutfen icinde veri olan "
                "bir Excel dosyasi secin."
            )
        try:
            df = pd.read_excel(io.BytesIO(content))
        except ValueError as e:
            # openpyxl/pandas bozuk veya .xlsx olmayan dosyalarda
            # genelde ValueError firlatir (orn. "File is not a zip file")
            raise ValueError(
                "Excel dosyasi okunamadi. Dosyanin gecerli bir .xlsx "
                "dosyasi oldugundan emin olun (eski .xls formati "
                "desteklenmiyor)."
            ) from e
        if df.empty:
            raise ValueError(
                "Excel dosyasinda okunacak veri bulunamadi. Dosyada en "
                "az bir baslik satiri ve bir veri satiri olmali."
            )
        return self._parse_dataframe(df, source="excel")

    def _parse_dataframe(self, df: pd.DataFrame, source: str) -> list[ParsedTransaction]:
        """DataFrame'i standart formata donusturur."""
        df.columns = [str(c).lower().strip() for c in df.columns]

        amount_col = self._find_column(df, self.AMOUNT_COLS)
        desc_col = self._find_column(df, self.DESC_COLS)
        date_col = self._find_column(df, self.DATE_COLS)
        merchant_col = self._find_column(df, self.MERCHANT_COLS)

        if not all([amount_col, desc_col, date_col]):
            raise ValueError(
                "Dosyada gerekli sutunlar taninamadi. Dosyanizda su "
                "sutunlardan en az birer tane olmali: "
                "Tutar icin (amount, tutar, miktar, borc, alacak gibi), "
                "Aciklama icin (description, aciklama, islem gibi), "
                "Tarih icin (date, tarih, transaction_date gibi). "
                "Sutun basliklarini kontrol edip tekrar deneyin."
            )

        transactions = []
        for _, row in df.iterrows():
            try:
                amount = self._parse_amount(row[amount_col])
                date = self._parse_date(row[date_col])
                description = str(row[desc_col]).strip()
                merchant = str(row[merchant_col]).strip() if merchant_col else None

                if not description or description == "nan":
                    continue

                transactions.append(ParsedTransaction(
                    amount=amount,
                    description=description,
                    merchant=merchant if merchant and merchant != "nan" else None,
                    transaction_date=date,
                    source=source,
                ))
            except (ValueError, InvalidOperation):
                # Hatali satiri atla, digerlerine devam et
                continue

        if not transactions:
            raise ValueError(
                "Dosyadaki sutunlar taninsa da, gecerli hicbir satir "
                "islenemedi. Tarih ve tutar formatlarini kontrol edin."
            )

        return transactions

    def _find_column(self, df: pd.DataFrame, candidates: list[str]) -> str | None:
        """Olasi sutun adlarindan birini bulur."""
        for col in candidates:
            if col in df.columns:
                return col
        return None

    def _parse_amount(self, value) -> Decimal:
        """Turkce ve Ingilizce format destegiyle tutar parse eder."""
        cleaned = str(value).strip()
        cleaned = cleaned.replace("TL", "").replace("₺", "").replace("$", "")
        cleaned = cleaned.replace(" ", "")
        # Turkce format: 1.234,56 -> 1234.56
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        return Decimal(cleaned)

    def _parse_date(self, value) -> datetime:
        """Farkli tarih formatlarini parse eder."""
        if isinstance(value, datetime):
            return value
        if hasattr(value, "to_pydatetime"):
            return value.to_pydatetime()

        date_str = str(value).strip()
        formats = [
            "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d",
            "%d.%m.%Y %H:%M", "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Tarih formati taninamadi: {date_str}")
