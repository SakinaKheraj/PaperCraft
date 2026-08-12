"""FastAPI routes for chat threads and direct document Q&A streaming."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import select

from app.auth.dependencies import CurrentUser, get_access_token, get_current_user
from app.chat.messages import (
    DEFAULT_THREAD_TITLE,
    extract_last_user_message,
    title_from_user_message,
    ui_message_to_insert,
)
from app.config import settings
from app.chat.orchestrator import run_turn
from app.retrieval.retriever import DocumentRetriever
from app.database.chats import (
    create_thread,
    delete_thread,
    get_next_sequence,
    list_threads,
    load_messages,
    require_thread_access,
)
from app.database.models import DocumentChunk, SourceDocument
from app.database.session import get_session
from app.database.supabase import create_user_client
from app.database.users import ensure_user
from app.schemas.chat import (
    CreateThreadRequest,
    MessageHistoryResponse,
    StreamRequest,
    TextPart,
    ThreadListResponse,
    ThreadResponse,
    UIMessage,
)

router = APIRouter(prefix="/chat", tags=["chat"])

# ── Helpers ──────────────────────────────────────────────────────────────

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, separators=(',', ':'), default=str)}\n\n"


def _get_latest_document_name() -> str | None:
    """Get the name of the most recently uploaded document."""
    with get_session() as session:
        doc = session.scalars(
            select(SourceDocument)
            .where(SourceDocument.form == "CUSTOM")
            .order_by(SourceDocument.created_at.desc())
        ).first()
        return doc.company_name if doc else None


def _load_document_text_by_title(thread_title: str) -> str:
    """Load only the document chunks that belong to the active document of this thread."""
    with get_session() as session:
        # 1. Try to find the document whose company name matches the thread_title
        chunks = session.scalars(
            select(DocumentChunk)
            .join(SourceDocument)
            .where(SourceDocument.company_name == thread_title)
            .order_by(DocumentChunk.chunk_index)
        ).all()

        # 2. If no chunks found, fall back to the most recently uploaded document
        if not chunks:
            latest_doc = session.scalars(
                select(SourceDocument)
                .where(SourceDocument.form == "CUSTOM")
                .order_by(SourceDocument.created_at.desc())
            ).first()
            if latest_doc:
                chunks = session.scalars(
                    select(DocumentChunk)
                    .where(DocumentChunk.document_id == latest_doc.id)
                    .order_by(DocumentChunk.chunk_index)
                ).all()

        if not chunks:
            return ""

        return "\n".join(chunk.text for chunk in chunks)


def _extract_user_query(messages: list[UIMessage]) -> str:
    """Extract the last user message text from the messages list."""
    for msg in reversed(messages):
        if msg.role == "user":
            for part in msg.parts:
                if isinstance(part, TextPart):
                    return part.text.strip()
    return ""


async def _stream_direct_answer(
    query: str,
    thread_id: uuid.UUID,
    user: CurrentUser,
    access_token: str,
    user_message: UIMessage,
    thread_title: str,
):
    """Stream an answer directly from Gemini using uploaded document context."""
    # Status: analyzing
    yield _sse({"type": "data-status", "data": {"stage": "analyzing", "message": "Analyzing your question…"}})

    # Load document text from DB (filtered by document name)
    doc_text = await run_in_threadpool(_load_document_text_by_title, thread_title)

    if not doc_text.strip():
        yield _sse({"type": "data-status", "data": {"stage": "streaming", "message": "No documents found. Answering from general knowledge…"}})
        system_prompt = (
            "You are Paper Craft, a helpful AI assistant. "
            "The user has not uploaded any documents yet. "
            "Let them know they should upload a PDF or TXT file first, "
            "then answer their question to the best of your ability."
        )
    else:
        yield _sse({"type": "data-status", "data": {"stage": "searching", "message": "Reading your documents…"}})
        # Trim to ~100k chars to stay within context window
        trimmed = doc_text[:100_000]
        system_prompt = (
            "You are Paper Craft, a helpful AI assistant that answers questions "
            "using the user's uploaded documents as primary context, but you are also "
            "free to use your own knowledge to elaborate, explain, or answer related questions.\n\n"
            "## Uploaded Document Content\n\n"
            f"{trimmed}\n\n"
            "## Instructions\n"
            "- Use the uploaded document content above as the primary source of truth.\n"
            "- If the question is related to the document but the details are not explicitly "
            "present, use your general knowledge to provide a helpful, accurate, and comprehensive answer.\n"
            "- Structure your response cleanly using Markdown headings, bullet points, and bold highlights.\n"
            "- Do NOT output raw LaTeX math syntax like $\\rightarrow$ or $k$. Use plain text or Unicode arrows (→, ⇒) instead.\n"
            "- Be concise, thorough, and smart."
        )

    yield _sse({"type": "data-status", "data": {"stage": "streaming", "message": "Generating answer…"}})

    # Call Gemini directly
    try:
        client_kwargs = {"api_key": settings.openai_api_key}
        if settings.effective_openai_base_url:
            client_kwargs["base_url"] = settings.effective_openai_base_url
        llm = AsyncOpenAI(**client_kwargs)

        message_id = str(uuid.uuid4())
        yield _sse({"type": "start", "messageId": message_id})

        response = await llm.chat.completions.create(
            model=settings.openai_chat_model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            stream=True,
        )

        full_answer = ""
        yield _sse({"type": "text-start", "id": message_id})

        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                full_answer += delta.content
                yield _sse({"type": "text-delta", "id": message_id, "delta": delta.content})

        yield _sse({"type": "text-end", "id": message_id})
        yield _sse({"type": "finish"})

        # Persist messages to Supabase
        try:
            client = await create_user_client(access_token)
            assistant_message = UIMessage(
                id=message_id,
                role="assistant",
                parts=[TextPart(text=full_answer)],
            )
            next_seq = await get_next_sequence(client, thread_id)
            rows = [
                ui_message_to_insert(user_message, thread_id=thread_id, sequence=next_seq),
                ui_message_to_insert(
                    assistant_message, thread_id=thread_id, sequence=next_seq + 1,
                    message_id=uuid.UUID(message_id),
                ),
            ]
            await client.table("chat_messages").insert(rows).execute()

            updates: dict = {"updated_at": datetime.now(UTC).isoformat()}
            if thread_title in (DEFAULT_THREAD_TITLE, "New chat", "New conversation") or thread_title.startswith("Uploading "):
                doc_name = _get_latest_document_name()
                updates["title"] = doc_name if doc_name else title_from_user_message(user_message)
            await client.table("chat_threads").update(updates).eq("id", str(thread_id)).execute()
        except Exception:
            pass  # Don't fail the response if persistence fails

    except Exception as exc:
        yield _sse({"type": "error", "errorText": f"Failed to generate answer: {exc}"})


# ── Thread CRUD ──────────────────────────────────────────────────────────

@router.get("/threads")
async def get_threads(
    user: CurrentUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> ThreadListResponse:
    await ensure_user(user)
    client = await create_user_client(access_token)
    threads = await list_threads(client, user)
    return ThreadListResponse(threads=threads)


@router.post("/threads")
async def post_thread(
    body: CreateThreadRequest,
    user: CurrentUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> ThreadResponse:
    await ensure_user(user)
    client = await create_user_client(access_token)
    return await create_thread(client, user, title=body.title)


class UpdateThreadRequest(BaseModel):
    title: str


@router.patch("/threads/{thread_id}")
async def patch_thread(
    thread_id: uuid.UUID,
    body: UpdateThreadRequest,
) -> ThreadResponse:
    try:
        client = await get_service_role_client()
        response = await (
            client.table("chat_threads")
            .update({"title": body.title})
            .eq("id", str(thread_id))
            .select("id,title,created_at,updated_at")
            .execute()
        )
        if response.data:
            return thread_row_to_response(response.data[0])
    except Exception:
        pass

    return ThreadResponse(
        id=thread_id,
        title=body.title,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> MessageHistoryResponse:
    await require_thread_access(thread_id, user)
    client = await create_user_client(access_token)
    messages = await load_messages(client, thread_id)
    return MessageHistoryResponse(messages=messages)


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread_route(
    thread_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> None:
    await require_thread_access(thread_id, user)
    client = await create_user_client(access_token)
    await delete_thread(client, thread_id)


# ── Stream (Direct Gemini Q&A) ───────────────────────────────────────────

@router.post("/stream")
async def post_stream(
    body: StreamRequest,
    user: CurrentUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> StreamingResponse:
    await ensure_user(user)
    thread = await require_thread_access(body.thread_id, user)
    
    query = _extract_user_query(body.messages)
    if not query:
        async def empty_error():
            yield _sse({"type": "error", "errorText": "Please enter a message."})
        return StreamingResponse(empty_error(), media_type="text/event-stream")

    user_message = extract_last_user_message(body.messages)
    return StreamingResponse(
        _stream_direct_answer(
            query=query,
            thread_id=body.thread_id,
            user=user,
            access_token=access_token,
            user_message=user_message,
            thread_title=thread.title,
        ),
        media_type="text/event-stream",
    )
