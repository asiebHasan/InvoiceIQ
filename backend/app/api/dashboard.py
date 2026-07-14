from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document, ExtractedData, Anomaly
from app.schemas.document import DashboardStats, DocumentListItem, DashboardRecent, DashboardTimeline, TimelinePoint

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Document.id)))).scalar() or 0
    processed = (await db.execute(select(func.count(Document.id)).where(Document.status == "completed"))).scalar() or 0
    processing = (await db.execute(select(func.count(Document.id)).where(Document.status == "processing"))).scalar() or 0
    failed = (await db.execute(select(func.count(Document.id)).where(Document.status == "failed"))).scalar() or 0
    anomalies = (await db.execute(select(func.count(Anomaly.id)))).scalar() or 0

    type_result = await db.execute(
        select(Document.document_type, func.count(Document.id)).group_by(Document.document_type)
    )
    by_type = {r[0]: r[1] for r in type_result.all()}

    return DashboardStats(
        total_documents=total,
        processed_count=processed,
        processing_count=processing,
        failed_count=failed,
        anomaly_count=anomalies,
        by_type=by_type,
    )


@router.get("/recent", response_model=DashboardRecent)
async def get_recent(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc()).limit(10)
    )
    docs = result.scalars().all()

    items = []
    for doc in docs:
        ed_result = await db.execute(
            select(ExtractedData.total_amount).where(ExtractedData.document_id == doc.id)
        )
        total_amount = ed_result.scalar_one_or_none()

        anomaly_count_result = await db.execute(
            select(func.count()).where(Anomaly.document_id == doc.id)
        )
        anomaly_count = anomaly_count_result.scalar() or 0

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

    return DashboardRecent(documents=items)


@router.get("/timeline", response_model=DashboardTimeline)
async def get_timeline(days: int = 30, db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(func.date(Document.created_at), func.count(Document.id))
        .where(Document.created_at >= since)
        .group_by(func.date(Document.created_at))
        .order_by(func.date(Document.created_at))
    )
    rows = result.all()

    return DashboardTimeline(
        timeline=[TimelinePoint(date=str(r[0]), count=r[1]) for r in rows]
    )
