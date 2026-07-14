import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document, ExtractedData

router = APIRouter()


@router.get("/csv")
async def export_csv(
    doc_type: str | None = Query(None, alias="type"),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Document, ExtractedData).join(
        ExtractedData, Document.id == ExtractedData.document_id, isouter=True
    ).where(Document.status == "completed")

    if doc_type:
        query = query.where(Document.document_type == doc_type)

    result = await db.execute(query)
    rows = result.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "filename", "document_type", "vendor_name", "invoice_number",
        "invoice_date", "due_date", "total_amount", "subtotal", "tax_amount",
        "currency", "line_items", "anomalies",
    ])

    for doc, ed in rows:
        writer.writerow([
            doc.filename,
            doc.document_type,
            ed.vendor_name if ed else "",
            ed.invoice_number if ed else "",
            ed.invoice_date if ed else "",
            ed.due_date if ed else "",
            ed.total_amount if ed else "",
            ed.subtotal if ed else "",
            ed.tax_amount if ed else "",
            ed.currency if ed else "",
            str(ed.line_items) if ed and ed.line_items else "",
            "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoiceiq_export.csv"},
    )


@router.get("/excel")
async def export_excel(
    doc_type: str | None = Query(None, alias="type"),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    from openpyxl import Workbook

    query = select(Document, ExtractedData).join(
        ExtractedData, Document.id == ExtractedData.document_id, isouter=True
    ).where(Document.status == "completed")

    if doc_type:
        query = query.where(Document.document_type == doc_type)

    result = await db.execute(query)
    rows = result.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "InvoiceIQ Export"

    headers = [
        "Filename", "Document Type", "Vendor Name", "Invoice Number",
        "Invoice Date", "Due Date", "Total Amount", "Subtotal", "Tax Amount",
        "Currency", "Payment Terms",
    ]
    ws.append(headers)

    for doc, ed in rows:
        ws.append([
            doc.filename,
            doc.document_type,
            ed.vendor_name if ed else "",
            ed.invoice_number if ed else "",
            str(ed.invoice_date) if ed and ed.invoice_date else "",
            str(ed.due_date) if ed and ed.due_date else "",
            float(ed.total_amount) if ed and ed.total_amount else 0,
            float(ed.subtotal) if ed and ed.subtotal else 0,
            float(ed.tax_amount) if ed and ed.tax_amount else 0,
            ed.currency if ed else "",
            ed.payment_terms if ed else "",
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=invoiceiq_export.xlsx"},
    )
