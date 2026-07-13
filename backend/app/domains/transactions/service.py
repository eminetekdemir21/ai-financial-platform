"""
Transactions domain service.
GUVENLIK DUZELTMESI: verify_account_ownership fonksiyonu eklendi.
Bir hesaba (account) veya onun islemlerine erismeden once, o hesabin
gercekten istekte bulunan kullaniciya ait oldugu burada kontrol edilir.
Kontrolden gecmezse 403/404 donulur, baska kullanicinin verisine
erisim engellenir.

MUKERRER ISLEM KONTROLU: _save_transactions artik her satiri eklemeden
once, ayni hesapta ayni (tutar, aciklama, tarih) uclusune sahip bir
islem olup olmadigini kontrol ediyor. Varsa, o satir atlanir.

HESAP SILME: delete_account fonksiyonu eklendi. Account modelindeki
cascade="all, delete-orphan" iliskisi sayesinde, bir hesap silindiginde
ona bagli tum islemler de otomatik silinir.

BANKAMI BAGLA (DEMO OPEN BANKING): connect_bank fonksiyonu eklendi.
Gercek bir banka API'sine baglanmak resmi lisans gerektirdigi icin,
bu fonksiyon ayni kullanici deneyimini simule eder: yeni bir hesap
olusturur ve gercekci, otomatik uretilmis 6 aylik bir islem gecmisini
dogrudan ekler - kullanicinin dosya secmesine gerek kalmaz.
"""

import random
import uuid
from typing import BinaryIO

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domains.transactions import schemas
from app.domains.transactions.demo_data_generator import generate_demo_transactions
from app.domains.transactions.models import Account, Transaction
from app.domains.transactions.parsers.transaction_parser import TransactionParser

_parser = TransactionParser()


# ---------------------------------------------------------------------------
# ACCOUNTS
# ---------------------------------------------------------------------------

def create_account(db: Session, user_id: uuid.UUID, payload: schemas.AccountCreate) -> Account:
    account = Account(
        user_id=user_id,
        bank_name=payload.bank_name,
        account_number_masked=payload.account_number_masked,
        currency=payload.currency,
        current_balance=0,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_accounts(db: Session, user_id: uuid.UUID) -> list[Account]:
    return db.query(Account).filter(Account.user_id == user_id).all()


def delete_account(db: Session, account: Account) -> None:
    """
    Hesabi ve (cascade sayesinde) ona bagli tum islemleri siler.
    Cagiran taraf, bu fonksiyonu cagirmadan once verify_account_ownership
    ile hesabin gercekten istekte bulunan kullaniciya ait oldugunu
    dogrulamis olmali.
    """
    db.delete(account)
    db.commit()


def verify_account_ownership(db: Session, account_id: uuid.UUID, user_id: uuid.UUID) -> Account:
    """
    Hesabin var oldugunu VE giris yapan kullaniciya ait oldugunu dogrular.
    Bu, guvenlik acisinda en kritik fonksiyon - her transactions
    endpoint'i bunu cagirmadan islem yapmamali.
    """
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.user_id == user_id)
        .first()
    )
    if account is None:
        # Bilerek 404 donuyoruz (403 degil) - hesabin var olup olmadigini
        # bile disariya sizdirmiyoruz, bu bir guvenlik pratigi.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hesap bulunamadi.",
        )
    return account


def connect_bank(db: Session, user_id: uuid.UUID, bank_name: str) -> tuple[Account, int, int]:
    """
    'Bankami Bagla' akisi: yeni bir hesap olusturur, gercekci 6 aylik
    demo islem verisi uretip dogrudan ekler, ardindan otomatik olarak
    kategorilendirir. Kullanici hicbir dosya secmez.
    """
    masked_number = f"**** {random.randint(1000, 9999)}"
    account = Account(
        user_id=user_id,
        bank_name=bank_name,
        account_number_masked=masked_number,
        currency="TRY",
        current_balance=0,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    demo_rows = generate_demo_transactions(months=6)
    for row in demo_rows:
        tx = Transaction(
            account_id=account.id,
            amount=row["amount"],
            description=row["description"],
            merchant=None,
            transaction_date=row["transaction_date"],
            source="open_banking_demo",
        )
        db.add(tx)
    db.commit()

    from app.domains.categorization import categorization_service
    cat_stats = categorization_service.categorize_account_transactions(
        db=db, account_id=account.id
    )

    return account, len(demo_rows), cat_stats["total_categorized"]


# ---------------------------------------------------------------------------
# TRANSACTIONS - IMPORT
# ---------------------------------------------------------------------------

def import_csv(db: Session, account_id: uuid.UUID, file_bytes: bytes) -> schemas.UploadResult:
    parsed_rows = _parser.parse_csv(file_bytes)
    return _save_transactions(db, account_id, parsed_rows, source="csv")


def import_excel(db: Session, account_id: uuid.UUID, file_bytes: bytes) -> schemas.UploadResult:
    parsed_rows = _parser.parse_excel(file_bytes)
    return _save_transactions(db, account_id, parsed_rows, source="excel")


def _is_duplicate(db: Session, account_id: uuid.UUID, row) -> bool:
    existing = (
        db.query(Transaction)
        .filter(
            Transaction.account_id == account_id,
            Transaction.amount == row.amount,
            Transaction.description == row.description,
            Transaction.transaction_date == row.transaction_date,
        )
        .first()
    )
    return existing is not None


def _save_transactions(db: Session, account_id: uuid.UUID, parsed_rows: list, source: str) -> schemas.UploadResult:
    created = 0
    skipped_duplicates = 0
    for row in parsed_rows:
        if _is_duplicate(db, account_id, row):
            skipped_duplicates += 1
            continue
        tx = Transaction(
            account_id=account_id,
            amount=row.amount,
            description=row.description,
            merchant=row.merchant,
            transaction_date=row.transaction_date,
            source=row.source,
        )
        db.add(tx)
        created += 1
    db.commit()
    return schemas.UploadResult(
        imported_count=created,
        source=source,
        skipped_duplicates=skipped_duplicates,
    )


# ---------------------------------------------------------------------------
# TRANSACTIONS - LIST
# ---------------------------------------------------------------------------

def list_transactions(db: Session, account_id: uuid.UUID, limit: int, offset: int) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .order_by(Transaction.transaction_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
