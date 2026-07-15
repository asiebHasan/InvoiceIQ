from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document, ExtractedData

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    document_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    # Get relevant document context
    context_parts = []
    sources = []

    if req.document_id:
        # Chat about a specific document
        doc_result = await db.execute(select(Document).where(Document.id == req.document_id))
        doc = doc_result.scalars().first()
        if doc:
            ed_result = await db.execute(select(ExtractedData).where(ExtractedData.document_id == doc.id))
            ed = ed_result.scalars().first()
            if ed and ed.raw_text:
                context_parts.append(f"Document: {doc.filename}\n{ed.raw_text}")
                sources.append({"filename": doc.filename, "doc_id": doc.id})
    else:
        # Chat about all completed documents
        docs_result = await db.execute(
            select(Document)
            .where(Document.status == "completed")
            .order_by(Document.created_at.desc())
            .limit(10)
        )
        docs = docs_result.scalars().all()
        for doc in docs:
            ed_result = await db.execute(select(ExtractedData).where(ExtractedData.document_id == doc.id))
            ed = ed_result.scalars().first()
            if ed and ed.raw_text:
                context_parts.append(f"Document: {doc.filename}\n{ed.raw_text}")
                sources.append({"filename": doc.filename, "doc_id": doc.id})

    if not context_parts:
        return ChatResponse(
            answer="No document data available. Please upload and process documents first.",
            sources=[],
        )

    context = "\n\n---\n\n".join(context_parts)

    # Build the prompt
    system_prompt = """You are InvoiceIQ, an intelligent document assistant. You answer questions about uploaded documents (invoices, receipts, purchase orders, bank statements).

Rules:
- Answer based ONLY on the provided document context
- If the information is not in the documents, say so clearly
- Be concise and specific
- When mentioning amounts, include the currency
- If multiple documents are relevant, reference them by filename
- Format numbers with commas for readability"""

    user_prompt = f"""Document Context:
{context}

Question: {req.message}

Answer the question based on the document context above. Be concise and accurate."""

    # Try HuggingFace first, then Gemini
    answer = await _chat_with_huggingface(system_prompt, user_prompt)
    if not answer:
        answer = await _chat_with_gemini(system_prompt, user_prompt)
    if not answer:
        answer = "I'm unable to process your question right now. Please try again later."

    return ChatResponse(answer=answer, sources=sources)


async def _chat_with_huggingface(system_prompt: str, user_prompt: str) -> str | None:
    from app.config import settings
    if not settings.HF_API_KEY:
        return None

    try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(token=settings.HF_API_KEY)
        response = client.chat_completion(
            model=settings.HF_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1024,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"HuggingFace chat failed: {e}")
        return None


async def _chat_with_gemini(system_prompt: str, user_prompt: str) -> str | None:
    from app.config import settings
    if not settings.GEMINI_API_KEY:
        return None

    try:
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=f"{system_prompt}\n\n{user_prompt}",
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini chat failed: {e}")
        return None
