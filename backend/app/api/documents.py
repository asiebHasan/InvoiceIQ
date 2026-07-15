import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.document import Document, ExtractedData, Anomaly, ProcessingJob
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentDetail,
    ExtractedDataResponse,
    AnomalyResponse,
    ProcessingJobResponse,
)
from app.utils.file_utils import compute_file_hash, safe_filename

router = APIRouter()


@router.post("/upload", response_model=list[DocumentUploadResponse])
async def upload_documents(files: list[UploadFile] = File(...), db: AsyncSession = Depends(get_db)):
    results = []

    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            continue

        contents = await file.read()
        if len(contents) > settings.max_upload_bytes:
            continue

        # Save file
        filename = safe_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = settings.upload_path / unique_name

        with open(file_path, "wb") as f:
            f.write(contents)

        file_hash = compute_file_hash(str(file_path))

        doc = Document(
            filename=file.filename,
            file_path=str(file_path),
            file_hash=file_hash,
            file_size=len(contents),
            status="processing",
        )
        db.add(doc)
        await db.flush()

        # Dispatch Celery task
        from celery_worker import celery_app
        celery_app.send_task("process_document", args=[doc.id])

        results.append(DocumentUploadResponse(
            id=doc.id,
            filename=doc.filename,
            status=doc.status,
            created_at=doc.created_at,
        ))

    await db.commit()
    return results


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    doc_type: str | None = Query(None, alias="type"),
    status: str | None = None,
    has_anomalies: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Document)

    if doc_type:
        query = query.where(Document.document_type == doc_type)
    if status:
        query = query.where(Document.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    docs = result.scalars().all()

    items = []
    for doc in docs:
        # Get extracted data amount
        ed_result = await db.execute(
            select(ExtractedData.total_amount).where(ExtractedData.document_id == doc.id)
        )
        total_amount = ed_result.scalar_one_or_none()

        # Count anomalies
        anomaly_count_result = await db.execute(
            select(func.count()).where(Anomaly.document_id == doc.id)
        )
        anomaly_count = anomaly_count_result.scalar() or 0

        if has_anomalies is True and anomaly_count == 0:
            continue
        if has_anomalies is False and anomaly_count > 0:
            continue

        items.append(DocumentListItem(
            id=doc.id,
            filename=doc.filename,
            document_type=doc.document_type,
            classification_confidence=doc.classification_confidence,
            status=doc.status,
            file_size=doc.file_size,
            created_at=doc.created_at,
            processed_at=doc.processed_at,
            total_amount=total_amount,
            anomaly_count=anomaly_count,
        ))

    pages = (total + size - 1) // size
    return DocumentListResponse(documents=items, total=total, page=page, pages=pages)


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    ed_result = await db.execute(
        select(ExtractedData).where(ExtractedData.document_id == doc_id)
    )
    extracted_data = ed_result.scalar_one_or_none()

    anomaly_result = await db.execute(
        select(Anomaly).where(Anomaly.document_id == doc_id).order_by(Anomaly.created_at.desc())
    )
    anomalies = anomaly_result.scalars().all()

    extracted_data_resp = None
    if extracted_data:
        extracted_data_resp = ExtractedDataResponse.model_validate(extracted_data)

    return DocumentDetail(
        id=doc.id,
        filename=doc.filename,
        file_hash=doc.file_hash,
        file_size=doc.file_size,
        document_type=doc.document_type,
        classification_confidence=doc.classification_confidence,
        status=doc.status,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        processed_at=doc.processed_at,
        extracted_data=extracted_data_resp,
        anomalies=[AnomalyResponse.model_validate(a) for a in anomalies],
    )


@router.get("/{doc_id}/download")
async def download_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type="application/pdf",
    )


class ResolveAnomalyRequest(BaseModel):
    is_resolved: bool


@router.patch("/{doc_id}/anomalies/{anomaly_id}")
async def resolve_anomaly(
    doc_id: str,
    anomaly_id: str,
    body: ResolveAnomalyRequest,
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    result = await db.execute(
        select(Anomaly).where(Anomaly.id == anomaly_id, Anomaly.document_id == doc_id)
    )
    anomaly = result.scalar_one_or_none()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    anomaly.is_resolved = body.is_resolved
    await db.commit()

    return AnomalyResponse.model_validate(anomaly)


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from disk
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}


@router.post("/{doc_id}/reprocess", response_model=ProcessingJobResponse)
async def reprocess_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete old extracted data and anomalies
    old_ed = await db.execute(select(ExtractedData).where(ExtractedData.document_id == doc_id))
    for ed in old_ed.scalars().all():
        await db.delete(ed)

    old_anomalies = await db.execute(select(Anomaly).where(Anomaly.document_id == doc_id))
    for a in old_anomalies.scalars().all():
        await db.delete(a)

    doc.status = "processing"
    doc.updated_at = datetime.utcnow()
    await db.commit()

    from celery_worker import celery_app
    celery_app.send_task("process_document", args=[doc_id])

    return ProcessingJobResponse(
        id=uuid.uuid4().hex,
        document_id=doc_id,
        status="pending",
    )


@router.get("/{doc_id}/status", response_model=ProcessingJobResponse)
async def get_processing_status(doc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.document_id == doc_id)
        .order_by(ProcessingJob.created_at.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="No processing job found")

    return ProcessingJobResponse.model_validate(job)
