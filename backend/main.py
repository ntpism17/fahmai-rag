from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag.pipeline import RAGPipeline

rag: RAGPipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag
    rag = RAGPipeline()
    yield


app = FastAPI(title="FahMai RAG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str


class SourceItem(BaseModel):
    title: str
    section_header: str
    category: str
    product_code: str
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]


@app.get("/api/health")
def health():
    return {"status": "ok", "model": rag.model_name if rag else None}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question is empty")
    if not rag:
        raise HTTPException(status_code=503, detail="RAG pipeline not ready")

    answer_text, sources = rag.answer(req.question)

    return ChatResponse(
        answer=answer_text,
        sources=[
            SourceItem(
                title=s["title"],
                section_header=s.get("section_header", ""),
                category=s["category"],
                product_code=s["product_code"],
                text=s["text"][:400],
            )
            for s in sources
        ],
    )
