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


async def extract_with_huggingface(text: str, document_type: str) -> dict | None:
    if not settings.HF_API_KEY:
        return None

    prompt = EXTRACTION_PROMPTS.get(document_type, EXTRACTION_PROMPTS["invoice"])
    full_prompt = f"{prompt}\n\nDocument text:\n{text[:8000]}"

    try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(token=settings.HF_API_KEY)
        response = client.chat_completion(
            model=settings.HF_MODEL,
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=2048,
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()

        # Extract JSON from response (may be wrapped in markdown)
        if "```json" in raw:
            raw = raw.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in raw:
            raw = raw.split("```", 1)[1].split("```", 1)[0]

        # Find JSON object in the response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])

        return None
    except Exception as e:
        print(f"HuggingFace extraction failed: {e}")
        return None


async def extract_with_gemini(text: str, document_type: str) -> dict | None:
    if not settings.GEMINI_API_KEY:
        return None

    try:
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = EXTRACTION_PROMPTS.get(document_type, EXTRACTION_PROMPTS["invoice"])
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=f"{prompt}\n\nDocument text:\n{text[:8000]}",
        )

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

        return json.loads(raw)
    except Exception as e:
        print(f"Gemini extraction failed: {e}")
        return None


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


async def extract_structured_data(text: str, document_type: str) -> dict | None:
    # HuggingFace first — free Inference API, no local resources needed
    result = await extract_with_huggingface(text, document_type)
    if result:
        return result

    # Gemini fallback
    result = await extract_with_gemini(text, document_type)
    if result:
        return result

    # Ollama fallback — for machines with enough RAM or when offline
    result = await extract_with_ollama(text, document_type)
    if result:
        return result

    return None
