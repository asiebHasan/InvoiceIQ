from datetime import datetime, date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, ExtractedData, Anomaly, ProcessingJob
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.ocr_engine import extract_text_from_scanned_pdf
from app.services.classifier import classify_document
from app.services.llm_extractor import extract_structured_data
from app.services.validator import validate_extracted_data
from app.services.anomaly_detector import run_anomaly_detection
from app.config import settings


async def process_document(db: AsyncSession, document_id: str):
    def parse_date(val):
        if not val or not isinstance(val, str):
            return None
        try:
            return date.fromisoformat(val.strip())
        except (ValueError, AttributeError):
            return None

    job = ProcessingJob(document_id=document_id, status="running", started_at=datetime.utcnow())
    db.add(job)
    await db.flush()

    doc = await db.get(Document, document_id)
    if not doc:
        job.status = "failed"
        job.error_message = "Document not found"
        await db.commit()
        return

    doc.status = "processing"
    await db.flush()

    try:
        # Step 1: PDF text extraction
        job.current_step = "extraction"
        job.progress = 0.1
        await db.flush()

        extraction = extract_text_from_pdf(doc.file_path)
        raw_text = extraction.text
        extraction_method = extraction.method

        # Step 2: OCR if needed
        if extraction_method == "needs_ocr":
            job.current_step = "ocr"
            job.progress = 0.2
            await db.flush()

            ocr_result = extract_text_from_scanned_pdf(doc.file_path)
            raw_text = ocr_result.text
            extraction_method = ocr_result.method

        if not raw_text:
            raise ValueError("No text could be extracted from the document")

        # Step 3: Classification
        job.current_step = "classification"
        job.progress = 0.4
        await db.flush()

        classification = classify_document(raw_text, settings.CLASSIFICATION_CONFIDENCE_THRESHOLD)
        doc.document_type = classification.document_type
        doc.classification_confidence = classification.confidence

        # Step 4: Structured extraction
        job.current_step = "extraction"
        job.progress = 0.5
        await db.flush()

        extracted = await extract_structured_data(raw_text, doc.document_type)
        if not extracted:
            raise ValueError("LLM extraction failed for all providers")

        # Step 5: Validation
        job.current_step = "validation"
        job.progress = 0.7
        await db.flush()

        validation = validate_extracted_data(extracted, doc.document_type)

        # Step 6: Anomaly detection
        job.current_step = "anomaly_detection"
        job.progress = 0.8
        await db.flush()

        existing_hashes_result = await db.execute(select(Document.file_hash).where(Document.id != document_id))
        existing_hashes = [r[0] for r in existing_hashes_result.all()]

        existing_docs_result = await db.execute(
            select(Document.id, Document.document_type)
            .join(ExtractedData, Document.id == ExtractedData.document_id)
            .where(Document.id != document_id)
            .limit(100)
        )
        existing_docs = [{"id": r[0], "vendor_name": None, "total_amount": None} for r in existing_docs_result.all()]

        amounts_result = await db.execute(
            select(ExtractedData.total_amount).where(ExtractedData.total_amount.isnot(None))
        )
        historical_amounts = [float(r[0]) for r in amounts_result.all() if r[0] is not None]

        anomalies = run_anomaly_detection(
            file_hash=doc.file_hash,
            data=extracted,
            document_type=doc.document_type,
            existing_hashes=existing_hashes,
            existing_docs=existing_docs,
            historical_amounts=historical_amounts,
        )

        # Step 7: Store results
        job.current_step = "storing"
        job.progress = 0.9
        await db.flush()

        ed = ExtractedData(
            document_id=document_id,
            vendor_name=extracted.get("vendor_name"),
            vendor_address=extracted.get("vendor_address"),
            customer_name=extracted.get("customer_name"),
            customer_address=extracted.get("customer_address"),
            invoice_number=extracted.get("invoice_number"),
            invoice_date=parse_date(extracted.get("invoice_date")),
            due_date=parse_date(extracted.get("due_date")),
            total_amount=extracted.get("total_amount"),
            subtotal=extracted.get("subtotal"),
            tax_amount=extracted.get("tax_amount"),
            currency=extracted.get("currency"),
            line_items=extracted.get("line_items"),
            payment_terms=extracted.get("payment_terms"),
            raw_text=raw_text,
            raw_llm_response=extracted,
            extraction_method=extraction_method,
            extraction_confidence=classification.confidence,
        )
        db.add(ed)

        for anomaly in anomalies:
            a = Anomaly(
                document_id=document_id,
                anomaly_type=anomaly.anomaly_type,
                severity=anomaly.severity,
                description=anomaly.description,
                details=anomaly.details,
            )
            db.add(a)

        doc.status = "completed"
        doc.processed_at = datetime.utcnow()
        doc.updated_at = datetime.utcnow()

        job.status = "completed"
        job.progress = 1.0
        job.completed_at = datetime.utcnow()

    except Exception as e:
        doc.status = "failed"
        doc.updated_at = datetime.utcnow()
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()

    await db.commit()
