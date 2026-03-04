"""Document CRUD endpoints — upload, list, get, delete."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.user import User
from app.services import knowledge, storage

router = APIRouter()


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    filename: str
    mime_type: str | None
    file_size: int | None
    doc_type: DocumentType
    status: DocumentStatus
    tags: list[str] | None
    error_message: str | None

    model_config = {"from_attributes": True}


class DocumentList(BaseModel):
    items: list[DocumentResponse]
    total: int


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file_data = await file.read()
    storage_path = await storage.upload_file(file_data, file.filename, file.content_type)

    doc = Document(
        title=file.filename,
        filename=file.filename,
        mime_type=file.content_type,
        file_size=len(file_data),
        storage_path=storage_path,
        uploaded_by=user.id,
        status=DocumentStatus.PROCESSING,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Process with Cognee in background
    try:
        local_path = await storage.get_local_path(storage_path)
        await knowledge.add_and_cognify(local_path)
        doc.status = DocumentStatus.READY
    except Exception as e:
        doc.status = DocumentStatus.ERROR
        doc.error_message = str(e)

    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
    )
    docs = result.scalars().all()

    count_result = await db.execute(select(Document))
    total = len(count_result.scalars().all())

    return DocumentList(items=docs, total=total)


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()
