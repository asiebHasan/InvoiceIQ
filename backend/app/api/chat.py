from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document, ExtractedData, ChatSession, ChatMessage

router = APIRouter()


# --- Schemas ---

class CreateSessionRequest(BaseModel):
    document_id: str | None = None
    title: str | None = None


class SendMessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: list[dict] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: str
    title: str
    document_id: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class SessionDetailResponse(BaseModel):
    id: str
    title: str
    document_id: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}


# --- Endpoints ---

@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession).order_by(desc(ChatSession.updated_at))
    )
    sessions = result.scalars().all()

    out = []
    for s in sessions:
        msg_result = await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == s.id)
        )
        count = len(msg_result.scalars().all())
        out.append(SessionResponse(
            id=s.id,
            title=s.title,
            document_id=s.document_id,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=count,
        ))
    return out


@router.post("/sessions", response_model=SessionDetailResponse)
async def create_session(body: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    title = body.title or "New Chat"
    if not title or title == "New Chat":
        if body.document_id:
            doc = await db.get(Document, body.document_id)
            if doc:
                title = doc.filename

    session = ChatSession(
        title=title,
        document_id=body.document_id,
    )
    db.add(session)
    await db.commit()

    return SessionDetailResponse(
        id=session.id,
        title=session.title,
        document_id=session.document_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[],
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = msg_result.scalars().all()

    return SessionDetailResponse(
        id=session.id,
        title=session.title,
        document_id=session.document_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()
    return {"message": "Session deleted"}


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(session_id: str, body: SendMessageRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    session.updated_at = datetime.utcnow()

    # Update title from first message
    msg_count_result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    )
    if len(msg_count_result.scalars().all()) == 0:
        session.title = body.message[:100]

    await db.flush()

    # Build context from documents
    context_parts = []
    sources = []

    if session.document_id:
        doc_result = await db.execute(select(Document).where(Document.id == session.document_id))
        doc = doc_result.scalars().first()
        if doc:
            ed_result = await db.execute(select(ExtractedData).where(ExtractedData.document_id == doc.id))
            ed = ed_result.scalars().first()
            if ed and ed.raw_text:
                context_parts.append(f"Document: {doc.filename}\n{ed.raw_text}")
                sources.append({"filename": doc.filename, "doc_id": doc.id})
    else:
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

    # Build conversation history (last 10 messages)
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(10)
    )
    history = list(reversed(history_result.scalars().all()))

    # Build prompts
    system_prompt = """You are InvoiceIQ, an intelligent document assistant. You answer questions about uploaded documents (invoices, receipts, purchase orders, bank statements).

Rules:
- Answer based ONLY on the provided document context
- If the information is not in the documents, say so clearly
- Be concise and specific
- When mentioning amounts, include the currency
- If multiple documents are relevant, reference them by filename
- Format numbers with commas for readability"""

    context_text = "\n\n---\n\n".join(context_parts) if context_parts else "No documents loaded."

    conversation = ""
    for msg in history:
        if msg.role == "user":
            conversation += f"User: {msg.content}\n"
        else:
            conversation += f"Assistant: {msg.content}\n"

    user_prompt = f"""Document Context:
{context_text}

Conversation History:
{conversation}User: {body.message}

Answer the question based on the document context above. Be concise and accurate."""

    # Get LLM response
    answer = await _chat_with_huggingface(system_prompt, user_prompt)
    if not answer:
        answer = await _chat_with_gemini(system_prompt, user_prompt)
    if not answer:
        answer = "I'm unable to process your question right now. Please try again later."

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer,
        sources=sources,
    )
    db.add(assistant_msg)
    session.updated_at = datetime.utcnow()
    await db.commit()

    return MessageResponse(
        id=assistant_msg.id,
        role="assistant",
        content=answer,
        sources=sources,
        created_at=assistant_msg.created_at,
    )


# --- LLM providers ---

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
