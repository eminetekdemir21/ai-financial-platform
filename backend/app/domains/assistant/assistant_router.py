import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.assistant import assistant_schemas as schemas
from app.domains.assistant.rag import assistant_service_rag as rag_service
from app.domains.assistant.rag.embedding_service import index_account_transactions
from app.domains.auth.models import User
from app.domains.transactions.service import verify_account_ownership

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/index/{account_id}")
def index_embeddings(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Hesabın tüm işlemlerini embedding'e çevirip pgvector'a kaydeder.
    CSV yüklemesi veya AI analizi sonrası çağrılmalıdır.
    """
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    count = index_account_transactions(db=db, account_id=account_id)
    return {"indexed": count, "message": f"{count} işlem RAG indexine eklendi."}


@router.post("/chat", response_model=schemas.ChatResponse)
def chat(
    payload: schemas.ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    RAG pipeline:
    1. pgvector'dan semantik olarak alakalı işlemleri getir
    2. Genel hesap özeti + alakalı işlemler → LLM context
    3. LLM gerçek veriye dayanarak cevap üretir

    LLM_API_KEY .env'de tanımlı değilse 503 döner.
    """
    account = verify_account_ownership(
        db=db, account_id=payload.account_id, user_id=current_user.id
    )
    try:
        reply = rag_service.ask(
            db=db, account=account, user_message=payload.message
        )
    except rag_service.AssistantNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "AI asistan su an yapilandirilmamis. "
                ".env dosyasina gecerli bir LLM_API_KEY eklenmesi gerekiyor."
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI asistanina ulasilirken hata olustu: {e}",
        )
    return schemas.ChatResponse(reply=reply)