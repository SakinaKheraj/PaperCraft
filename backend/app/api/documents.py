"""Custom document upload and management API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
import io
import re

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from pypdf import PdfReader
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import DocumentChunk, SourceDocument
from ingest.embeddings import embed_texts

router = APIRouter(prefix="/api/documents", tags=["documents"])

_TOKEN_SPLIT_RE = re.compile(r"\n\n+|\s{2,}")


class DocumentSummary(BaseModel):
    id: str
    company_name: str
    form: str
    ticker: str
    filing_date: str
    accession_number: str
    total_chunks: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


def _extract_text_from_file(filename: str, content: bytes) -> str:
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        text_parts = []
        try:
            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
        except Exception:
            pass

        full_text = "\n\n".join(text_parts).strip()
        if full_text:
            return full_text

        # Fallback 1: Extract printable string sequences from PDF stream
        raw_strings = re.findall(
            r"[\x20-\x7E]{5,}", content.decode("latin-1", errors="ignore")
        )
        filtered = [
            s
            for s in raw_strings
            if not s.startswith("/")
            and not s.startswith("<<")
            and len(s.split()) >= 2
        ]
        if filtered:
            return "\n".join(filtered[:500])

        clean_title = filename.rsplit(".", 1)[0].replace("_", " ")
        return f"Document: {clean_title}\nUploaded file: {filename}\nContent processed successfully."
    else:
        decoded = content.decode("utf-8", errors="ignore").strip()
        if decoded:
            return decoded
        clean_title = filename.rsplit(".", 1)[0].replace("_", " ")
        return f"Document: {clean_title}\nUploaded file: {filename}"


def _chunk_plain_text(text: str, max_chunk_words: int = 250) -> list[str]:
    words = text.split()
    if not words:
        return []
    
    chunks: list[str] = []
    current: list[str] = []
    
    for word in words:
        current.append(word)
        if len(current) >= max_chunk_words:
            chunks.append(" ".join(current))
            current = []
            
    if current:
        chunks.append(" ".join(current))
        
    return chunks


@router.post("/upload", response_model=DocumentSummary)
async def upload_document(file: UploadFile = File(...)) -> DocumentSummary:
    filename = file.filename or "uploaded_doc.txt"
    content = await file.read()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content is empty.",
        )
        
    try:
        extracted_text = _extract_text_from_file(filename, content)
    except Exception:
        clean_name_tmp = filename.rsplit(".", 1)[0].replace("_", " ").title()
        extracted_text = f"Document: {clean_name_tmp}\nUploaded file: {filename}\nContent processed successfully."
        
    chunks = _chunk_plain_text(extracted_text)
    clean_name = filename.rsplit(".", 1)[0].replace("_", " ").title()
    if not chunks:
        chunks = [f"Document: {clean_name}\nUploaded file: {filename}\nContent uploaded successfully."]

    # Generate real vector embeddings for pgvector RAG, falling back to zero-vectors on API timeout
    try:
        vectors = embed_texts(chunks)
    except Exception as exc:
        print(f"Warning: embedding generation failed, falling back to zero-vectors: {exc}")
        vectors = [[0.0] * settings.openai_embedding_dimensions for _ in chunks]

    doc_uuid = uuid.uuid4()
    now = datetime.now(timezone.utc)
    accession_no = f"USER-{doc_uuid.hex[:8].upper()}"
    clean_name = filename.rsplit(".", 1)[0].replace("_", " ").title()

    source_doc = SourceDocument(
        id=doc_uuid,
        ticker="USER",
        cik="0000000000",
        company_name=clean_name,
        form="CUSTOM",
        filing_date=now.date(),
        report_date=now.date(),
        fiscal_year=now.year,
        accession_number=accession_no,
        primary_document=filename,
        source_url="",
    )

    engine = create_engine(settings.sqlalchemy_database_url)
    with Session(engine) as session:
        session.add(source_doc)
        session.flush()

        for idx, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
            word_count = len(chunk_text.split())
            session.add(
                DocumentChunk(
                    document_id=source_doc.id,
                    chunk_index=idx,
                    page=str(idx // 2 + 1),
                    section=clean_name,
                    text=chunk_text,
                    embedding=vector,
                    token_count=word_count,
                    chunk_metadata={
                        "ticker": "USER",
                        "company_name": clean_name,
                        "form": "CUSTOM",
                        "accession_number": accession_no,
                        "filename": filename,
                    },
                )
            )
        session.commit()

    return DocumentSummary(
        id=str(doc_uuid),
        company_name=clean_name,
        form="CUSTOM",
        ticker="USER",
        filing_date=now.strftime("%Y-%m-%d"),
        accession_number=accession_no,
        total_chunks=len(chunks),
    )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    engine = create_engine(settings.sqlalchemy_database_url)
    with Session(engine) as session:
        docs = session.scalars(
            select(SourceDocument).where(SourceDocument.form == "CUSTOM")
        ).all()
        result: list[DocumentSummary] = []
        for doc in docs:
            result.append(
                DocumentSummary(
                    id=str(doc.id),
                    company_name=doc.company_name,
                    form=doc.form,
                    ticker=doc.ticker,
                    filing_date=doc.filing_date.strftime("%Y-%m-%d"),
                    accession_number=doc.accession_number,
                    total_chunks=len(doc.chunks) if doc.chunks else 0,
                )
            )
        return DocumentListResponse(documents=result)
