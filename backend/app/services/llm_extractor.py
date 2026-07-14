import json
import httpx
from app.config import settings


EXTRACTION_PROMPTS = {
    "invoice": """Extract the following fields from this invoice and return ONLY a valid JSON object:
{
  "vendor_name": "string or null",
  "vendor_address": "string or null",
  "customer_name": "string or null",
  "customer_address": "string or null",
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "total_amount": number or null,
  "subtotal": number or null,
  "tax_amount": number or null,
  "currency": "string or null",
  "line_items": [{"description": "string", "quantity": number, "unit_price": number, "total": number}],
  "payment_terms": "string or null"
}
Return ONLY the JSON object, no markdown, no explanation.""",

    "receipt": """Extract the following fields from this receipt and return ONLY a valid JSON object:
{
  "vendor_name": "string or null",
  "vendor_address": "string or null",
  "customer_name": null,
  "customer_address": null,
  "invoice_number": "transaction id or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": null,
  "total_amount": number or null,
  "subtotal": number or null,
  "tax_amount": number or null,
  "currency": "string or null",
  "line_items": [{"description": "string", "quantity": number, "unit_price": number, "total": number}],
  "payment_terms": "string or null"
}
Return ONLY the JSON object, no markdown, no explanation.""",

    "purchase_order": """Extract the following fields from this purchase order and return ONLY a valid JSON object:
{
  "vendor_name": "string or null",
  "vendor_address": "string or null",
  "customer_name": "string or null",
  "customer_address": "string or null",
  "invoice_number": "PO number or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "delivery date or null",
  "total_amount": number or null,
  "subtotal": number or null,
  "tax_amount": number or null,
  "currency": "string or null",
  "line_items": [{"description": "string", "quantity": number, "unit_price": number, "total": number}],
  "payment_terms": "string or null"
}
Return ONLY the JSON object, no markdown, no explanation.""",

    "bank_statement": """Extract the following fields from this bank statement and return ONLY a valid JSON object:
{
  "vendor_name": "bank name or null",
  "vendor_address": "string or null",
  "customer_name": "account holder or null",
  "customer_address": "string or null",
  "invoice_number": "statement number or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": null,
  "total_amount": "closing balance or null",
  "subtotal": "opening balance or null",
  "tax_amount": null,
  "currency": "string or null",
  "line_items": [{"description": "transaction description", "quantity": 1, "unit_price": 0, "total": number}],
  "payment_terms": null
}
Return ONLY the JSON object, no markdown, no explanation.""",
}


async def extract_with_ollama(text: str, document_type: str) -> dict | None:
    prompt = EXTRACTION_PROMPTS.get(document_type, EXTRACTION_PROMPTS["invoice"])
    full_prompt = f"{prompt}\n\nDocument text:\n{text[:8000]}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": full_prompt,
                    "stream": False,
                    "format": "json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            response_text = data.get("response", "")
            return json.loads(response_text)
    except Exception as e:
        print(f"Ollama extraction failed: {e}")
        return None


async def extract_with_gemini(text: str, document_type: str) -> dict | None:
    if not settings.GEMINI_API_KEY:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = EXTRACTION_PROMPTS.get(document_type, EXTRACTION_PROMPTS["invoice"])
        response = await model.generate_content_async(f"{prompt}\n\nDocument text:\n{text[:8000]}")

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

        return json.loads(raw)
    except Exception as e:
        print(f"Gemini extraction failed: {e}")
        return None


async def extract_structured_data(text: str, document_type: str) -> dict | None:
    # Gemini first — zero local resources, works on any machine
    result = await extract_with_gemini(text, document_type)
    if result:
        return result

    # Ollama fallback — for machines with enough RAM or when offline
    result = await extract_with_ollama(text, document_type)
    if result:
        return result

    return None
