import pdfplumber
from dataclasses import dataclass, field


@dataclass
class ExtractionResult:
    text: str = ""
    tables: list[list[list[str]]] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    page_count: int = 0
    method: str = "pdfplumber"


def extract_text_from_pdf(file_path: str) -> ExtractionResult:
    result = ExtractionResult()
    full_text = []

    with pdfplumber.open(file_path) as pdf:
        result.page_count = len(pdf.pages)
        result.metadata = pdf.metadata or {}

        for page in pdf.pages:
            page_text = page.extract_text() or ""
            full_text.append(page_text)

            page_tables = page.extract_tables()
            if page_tables:
                result.tables.extend(page_tables)

    result.text = "\n\n".join(full_text).strip()

    if not result.text or len(result.text) < 50:
        result.method = "needs_ocr"

    return result
