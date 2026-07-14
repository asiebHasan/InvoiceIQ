from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


REQUIRED_FIELDS = {
    "invoice": ["vendor_name", "invoice_number", "invoice_date", "total_amount"],
    "receipt": ["vendor_name", "total_amount"],
    "purchase_order": ["customer_name", "invoice_number"],
    "bank_statement": ["vendor_name"],
}


def validate_extracted_data(data: dict, document_type: str) -> ValidationResult:
    result = ValidationResult()

    # Required fields check
    required = REQUIRED_FIELDS.get(document_type, REQUIRED_FIELDS["invoice"])
    missing = [f for f in required if not data.get(f)]
    if missing:
        result.errors.append(f"Missing required fields: {', '.join(missing)}")
        result.is_valid = False

    # Date validation
    for date_field in ["invoice_date", "due_date"]:
        val = data.get(date_field)
        if val:
            try:
                parsed = datetime.strptime(str(val), "%Y-%m-%d").date()
                if parsed > date.today():
                    result.warnings.append(f"{date_field} is in the future: {val}")
            except (ValueError, TypeError):
                result.errors.append(f"Invalid date format for {date_field}: {val}")
                result.is_valid = False

    # Amount validation
    for amt_field in ["total_amount", "subtotal", "tax_amount"]:
        val = data.get(amt_field)
        if val is not None:
            try:
                Decimal(str(val))
            except (InvalidOperation, TypeError):
                result.errors.append(f"Invalid amount for {amt_field}: {val}")
                result.is_valid = False

    # Line items arithmetic
    line_items = data.get("line_items", [])
    if line_items:
        for i, item in enumerate(line_items):
            qty = item.get("quantity")
            price = item.get("unit_price")
            total = item.get("total")
            if qty is not None and price is not None and total is not None:
                expected = Decimal(str(qty)) * Decimal(str(price))
                actual = Decimal(str(total))
                if abs(expected - actual) > Decimal("0.02"):
                    result.warnings.append(
                        f"Line item {i}: qty({qty}) * price({price}) = {expected}, but total is {total}"
                    )

    # Subtotal + tax = total
    subtotal = data.get("subtotal")
    tax = data.get("tax_amount")
    total = data.get("total_amount")
    if subtotal is not None and tax is not None and total is not None:
        try:
            expected_total = Decimal(str(subtotal)) + Decimal(str(tax))
            actual_total = Decimal(str(total))
            if abs(expected_total - actual_total) > Decimal("0.02"):
                result.warnings.append(
                    f"Subtotal({subtotal}) + tax({tax}) = {expected_total}, but total is {total}"
                )
        except (InvalidOperation, TypeError):
            pass

    return result
