import re
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    method: str


KEYWORDS = {
    "invoice": [
        "invoice", "bill to", "ship to", "payment terms", "due date",
        "invoice number", "invoice date", "amount due", "bill from",
    ],
    "receipt": [
        "receipt", "thank you", "cash register", "transaction",
        "subtotal", "change due", "payment method", "card ending",
    ],
    "purchase_order": [
        "purchase order", "po number", "authorized by", "delivery date",
        "ship to", "bill to", "quotation", "order date",
    ],
    "bank_statement": [
        "bank statement", "account number", "routing number",
        "opening balance", "closing balance", "statement period",
        "debit", "credit", "transaction date",
    ],
}


def classify_document(text: str, confidence_threshold: float = 0.7) -> ClassificationResult:
    text_lower = text.lower()
    scores = {}

    for doc_type, keywords in KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[doc_type] = score

    max_score = max(scores.values()) if scores else 0
    if max_score == 0:
        return ClassificationResult(document_type="unknown", confidence=0.0, method="heuristic")

    best_type = max(scores, key=scores.get)
    total_keywords = len(KEYWORDS[best_type])
    confidence = min(scores[best_type] / max(total_keywords * 0.3, 1), 1.0)

    if confidence >= confidence_threshold:
        return ClassificationResult(document_type=best_type, confidence=round(confidence, 2), method="heuristic")

    return ClassificationResult(document_type=best_type, confidence=round(confidence, 2), method="heuristic_low_confidence")
