from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# --- Line Item ---
class LineItem(BaseModel):
    description: str | None = None
    quantity: float | None = None
    unit_price: Decimal | None = None
    total: Decimal | None = None


# --- Extracted Data ---
class ExtractedDataBase(BaseModel):
    vendor_name: str | None = None
    vendor_address: str | None = None
    customer_name: str | None = None
    customer_address: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    total_amount: Decimal | None = None
    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    currency: str | None = None
    line_items: list[LineItem] | None = None
    payment_terms: str | None = None


class ExtractedDataResponse(ExtractedDataBase):
    id: str
    raw_text: str | None = None
    extraction_method: str | None = None
    extraction_confidence: float | None = None

    model_config = {"from_attributes": True}


# --- Anomaly ---
class AnomalyResponse(BaseModel):
    id: str
    anomaly_type: str
    severity: str
    description: str
    details: dict | None = None
    is_resolved: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Document ---
class DocumentBase(BaseModel):
    filename: str
    document_type: str = "unknown"
    status: str = "uploading"


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    id: str
    filename: str
    document_type: str
    classification_confidence: float | None = None
    status: str
    file_size: int
    created_at: datetime
    processed_at: datetime | None = None
    total_amount: Decimal | None = None
    anomaly_count: int = 0

    model_config = {"from_attributes": True}


class DocumentDetail(BaseModel):
    id: str
    filename: str
    file_hash: str
    file_size: int
    document_type: str
    classification_confidence: float | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None = None
    extracted_data: ExtractedDataResponse | None = None
    anomalies: list[AnomalyResponse] = []

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentListItem]
    total: int
    page: int
    pages: int


# --- Processing Job ---
class ProcessingJobResponse(BaseModel):
    id: str
    document_id: str
    status: str
    current_step: str | None = None
    progress: float = 0.0
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Dashboard ---
class DashboardStats(BaseModel):
    total_documents: int
    processed_count: int
    processing_count: int
    failed_count: int
    anomaly_count: int
    by_type: dict[str, int]


class DashboardRecent(BaseModel):
    documents: list[DocumentListItem]


class TimelinePoint(BaseModel):
    date: str
    count: int


class DashboardTimeline(BaseModel):
    timeline: list[TimelinePoint]
