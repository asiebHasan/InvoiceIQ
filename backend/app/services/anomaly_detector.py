from datetime import date, datetime
from decimal import Decimal
from dataclasses import dataclass, field

import numpy as np
from thefuzz import fuzz

from app.config import settings


@dataclass
class Anomaly:
    anomaly_type: str
    severity: str
    description: str
    details: dict | None = None


def detect_duplicates(file_hash: str, existing_hashes: list[str]) -> Anomaly | None:
    if file_hash in existing_hashes:
        return Anomaly(
            anomaly_type="duplicate",
            severity="high",
            description="Exact duplicate document detected (identical file hash)",
            details={"matched_hash": file_hash},
        )
    return None


def detect_near_duplicates(vendor_name: str | None, total_amount, existing_docs: list[dict]) -> Anomaly | None:
    if not vendor_name or total_amount is None:
        return None

    for doc in existing_docs:
        if not doc.get("vendor_name"):
            continue
        vendor_score = fuzz.ratio(vendor_name.lower(), doc["vendor_name"].lower())
        amount_match = abs(Decimal(str(total_amount)) - Decimal(str(doc.get("total_amount", 0)))) < Decimal("0.01")

        if vendor_score > 90 and amount_match:
            return Anomaly(
                anomaly_type="near_duplicate",
                severity="high",
                description=f"Near-duplicate of document with vendor '{doc['vendor_name']}' (similarity: {vendor_score}%)",
                details={"matched_doc_id": doc.get("id"), "vendor_similarity": vendor_score},
            )
    return None


def detect_unusual_amount(amounts: list[float], current_amount: float) -> Anomaly | None:
    if len(amounts) < 5 or current_amount is None:
        return None

    arr = np.array(amounts)
    mean = arr.mean()
    std = arr.std()

    if std == 0:
        return None

    z_score = (current_amount - mean) / std
    if abs(z_score) > settings.ANOMALY_Z_SCORE_THRESHOLD:
        return Anomaly(
            anomaly_type="unusual_amount",
            severity="medium",
            description=f"Amount ${current_amount:.2f} is a statistical outlier (z-score: {z_score:.2f})",
            details={"z_score": round(z_score, 2), "mean": round(mean, 2), "std": round(std, 2)},
        )
    return None


def detect_missing_fields(data: dict, document_type: str) -> Anomaly | None:
    critical_fields = {
        "invoice": ["vendor_name", "total_amount", "invoice_number"],
        "receipt": ["vendor_name", "total_amount"],
        "purchase_order": ["customer_name"],
        "bank_statement": ["vendor_name"],
    }
    required = critical_fields.get(document_type, [])
    missing = [f for f in required if not data.get(f)]

    if missing:
        return Anomaly(
            anomaly_type="missing_field",
            severity="high" if len(missing) >= 2 else "medium",
            description=f"Missing critical fields: {', '.join(missing)}",
            details={"missing_fields": missing},
        )
    return None


def detect_future_dates(data: dict) -> Anomaly | None:
    today = date.today()
    for date_field in ["invoice_date", "due_date"]:
        val = data.get(date_field)
        if val:
            try:
                parsed = datetime.strptime(str(val), "%Y-%m-%d").date()
                if parsed > today:
                    return Anomaly(
                        anomaly_type="future_date",
                        severity="medium",
                        description=f"{date_field} is in the future: {val}",
                        details={"field": date_field, "value": str(val)},
                    )
            except (ValueError, TypeError):
                pass
    return None


def detect_arithmetic_errors(data: dict) -> Anomaly | None:
    line_items = data.get("line_items", [])
    if not line_items:
        return None

    line_sum = Decimal("0")
    for item in line_items:
        total = item.get("total")
        if total is not None:
            line_sum += Decimal(str(total))

    subtotal = data.get("subtotal")
    if subtotal is not None:
        expected = Decimal(str(subtotal))
        if abs(line_sum - expected) > Decimal("0.02"):
            return Anomaly(
                anomaly_type="arithmetic_error",
                severity="medium",
                description=f"Line items sum ({line_sum}) does not match subtotal ({subtotal})",
                details={"line_items_sum": str(line_sum), "subtotal": str(subtotal)},
            )
    return None


def run_anomaly_detection(
    file_hash: str,
    data: dict,
    document_type: str,
    existing_hashes: list[str],
    existing_docs: list[dict],
    historical_amounts: list[float],
) -> list[Anomaly]:
    anomalies = []

    dup = detect_duplicates(file_hash, existing_hashes)
    if dup:
        anomalies.append(dup)

    near_dup = detect_near_duplicates(
        data.get("vendor_name"), data.get("total_amount"), existing_docs
    )
    if near_dup:
        anomalies.append(near_dup)

    amount = data.get("total_amount")
    if amount is not None:
        outlier = detect_unusual_amount(historical_amounts, float(amount))
        if outlier:
            anomalies.append(outlier)

    missing = detect_missing_fields(data, document_type)
    if missing:
        anomalies.append(missing)

    future = detect_future_dates(data)
    if future:
        anomalies.append(future)

    arith = detect_arithmetic_errors(data)
    if arith:
        anomalies.append(arith)

    return anomalies
