from celery import shared_task
from app.database import async_session
from app.services.pipeline import process_document


@shared_task(bind=True, name="process_document")
def process_document_task(self, document_id: str):
    import asyncio

    async def _run():
        async with async_session() as db:
            await process_document(db, document_id)

    asyncio.run(_run())
