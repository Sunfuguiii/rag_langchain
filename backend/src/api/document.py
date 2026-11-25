from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.deps import get_admin_user, get_current_user, get_db
from src.db.models import User

from src.schemas.document import (
    DocumentItem,
    DocumentListResponse,
    DocumentReindexResponse,
    DocumentUploadResponse,
)

from src.services.document import (
    list_documents,
    upload_document,
    delete_document
)

router = APIRouter()

@router.get("", response_model=DocumentListResponse)
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):

    docs =await list_documents(db)

    return DocumentListResponse(
        documents=[
            DocumentItem(
                id=str(d.id),
                name=d.filename,
                status=d.status,
                chunk_count=d.chunk_count,
                file_size=d.file_size,
                created_at=d.created_at,
            )
            for d in docs
        ]
    )


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload(
    file: UploadFile = File(...), # 文件上传， ... 表示多个文件上传
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """上传文档"""

     # ---------- 文件类型校验 ----------
    if not file.filename.endswith((".md",".txt")):
        raise HTTPException(
                            status_code=400, 
                            detail="Only .md and .txt files are supported"
                            )
    # ---------- 文件大小校验 ----------
    if file.size > 1024 * 1024 * 10:
        raise HTTPException(
                            status_code=400, 
                            detail="File size must be less than 10MB"
                            )
    
    content = await file.read()
    

    try:
        doc =await upload_document(
            filename=file.filename,
            content=content,
            user_id=str(current_user.id),
            db=db,
        )
    except ConnectionError:
        raise HTTPException(
                            status_code=503, 
                            detail="Database connection error"
                            )
    except Exception as e:
        raise HTTPException(
                            status_code=500, 
                            detail=f"Upload document error: {str(e)}"
                            )
    return DocumentUploadResponse(
        id=str(doc.id),
        name=doc.filename,
        status=doc.status,
        chunk_count=doc.chunk_count,
    )


@router.delete("/{document_id}")
async def delete(
    document_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    
    await delete_document(document_id, db)
    return {"message": "delete ok"}