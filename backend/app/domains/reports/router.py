import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.reports.pdf_service import generate_pdf
from app.domains.transactions.service import verify_account_ownership

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{account_id}/pdf")
def download_pdf_report(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Hesabin tam finansal analizini PDF olarak indirir.
    Genel ozet, kategori dokumu, fraud raporu ve son islemleri icerir.
    """
    account = verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    try:
        pdf_bytes = generate_pdf(db=db, account=account)
        filename = f"finansal_rapor_{account.bank_name.replace(' ', '_')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF olusturulamadi: {e}")
