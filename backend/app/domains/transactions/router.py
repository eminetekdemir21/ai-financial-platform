"""
Transactions domain router.
GUNCELLEME: Dosya yuklendikten sonra kategorilendirme otomatik
tetikleniyor - kullanicinin ekstra bir istek yapmasina gerek yok.

GUNCELLEME 2: Parser'dan gelen ValueError artik 500 degil, kullaniciya
anlamli bir mesajla 400 Bad Request olarak donuyor.

GUNCELLEME 3: DELETE /accounts/{account_id} endpoint'i eklendi - hesap
sahipligi dogrulanip hesap (ve cascade ile tum islemleri) silinir.
"""
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.categorization import categorization_service
from app.domains.transactions import schemas, service
router = APIRouter(prefix="/transactions", tags=["transactions"])
# ---------------------------------------------------------------------------
# ACCOUNTS
# ---------------------------------------------------------------------------
@router.post(
    "/accounts",
    response_model=schemas.AccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_account(
    payload: schemas.AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Yeni banka hesabi olusturur. user_id token'dan otomatik alinir."""
    return service.create_account(db=db, user_id=current_user.id, payload=payload)
@router.get("/accounts", response_model=list[schemas.AccountResponse])
def list_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Giris yapan kullanicinin tum hesaplarini listeler."""
    return service.list_accounts(db=db, user_id=current_user.id)
@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Bir hesabi ve ona bagli tum islemleri siler. Hesap sahipligi once
    dogrulanir - baska bir kullanicinin hesabini silmeye calismak 404
    ile sonuclanir.
    """
    account = service.verify_account_ownership(
        db=db, account_id=account_id, user_id=current_user.id
    )
    service.delete_account(db=db, account=account)
# ---------------------------------------------------------------------------
# TRANSACTIONS - UPLOAD
# ---------------------------------------------------------------------------
@router.post("/upload/csv", response_model=schemas.UploadResult)
def upload_csv(
    account_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    CSV dosyasi yukler, ardindan yeni islemleri otomatik kategorilendirir.
    account_id'nin bu kullaniciya ait oldugu once dogrulanir.
    """
    service.verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    content = file.file.read()
    try:
        result = service.import_csv(db=db, account_id=account_id, file_bytes=content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    cat_stats = categorization_service.categorize_account_transactions(db=db, account_id=account_id)
    result.categorized_count = cat_stats["total_categorized"]
    return result
@router.post("/upload/excel", response_model=schemas.UploadResult)
def upload_excel(
    account_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Excel (.xlsx) dosyasi yukler, ardindan otomatik kategorilendirir."""
    service.verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    content = file.file.read()
    try:
        result = service.import_excel(db=db, account_id=account_id, file_bytes=content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    cat_stats = categorization_service.categorize_account_transactions(db=db, account_id=account_id)
    result.categorized_count = cat_stats["total_categorized"]
    return result
# ---------------------------------------------------------------------------
# TRANSACTIONS - LIST
# ---------------------------------------------------------------------------
@router.get("/list", response_model=list[schemas.TransactionResponse])
def list_transactions(
    account_id: uuid.UUID,
    limit: int = Query(default=500, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Belirtilen hesabin islemlerini listeler."""
    service.verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    return service.list_transactions(db=db, account_id=account_id, limit=limit, offset=offset)

