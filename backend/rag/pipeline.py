import os
import re
import glob
import pickle
import time
import requests
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple

from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import faiss
from pythainlp.tokenize import word_tokenize

KB_DIR = Path(os.getenv("KB_DIR", "../knowledge_base"))
EMBED_MODEL_NAME = "BAAI/bge-m3"
TOP_K_RETRIEVE = 20
TOP_K_CONTEXT = 5
RRF_K = 60
CACHE_PATH = Path(os.getenv("CACHE_PATH", "./_embed_cache.pkl"))

SYSTEM_PROMPT = """คุณคือ FahMai AI ผู้ช่วยของร้านฟ้าใหม่ ร้านจำหน่ายสินค้าอิเล็กทรอนิกส์ชั้นนำ

กฎการตอบ:
- ตอบเป็นภาษาไทย กระชับ ชัดเจน และเป็นมิตร
- ใช้ข้อมูลจาก Context ที่ให้มาเท่านั้น
- ถ้าไม่มีข้อมูลใน Context ให้บอกว่า "ขออภัยครับ ไม่พบข้อมูลในส่วนนี้ กรุณาติดต่อพนักงานเพื่อข้อมูลเพิ่มเติมครับ"
- ห้ามเดาหรือสร้างข้อมูลที่ไม่มีใน Context
- ตอบให้ตรงประเด็น ไม่ต้องยาวเกินไป"""


def tokenize_thai(text: str) -> List[str]:
    tokens = word_tokenize(text, engine="newmm", keep_whitespace=False)
    return [t.lower().strip() for t in tokens if t.strip()]


def split_by_sections(text: str, max_chars: int = 1200) -> List[Tuple[str, str]]:
    header_pattern = re.compile(r"(?m)^(#{1,3} .+)$")
    parts = header_pattern.split(text)

    sections = []
    current_header = ""
    current_body = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if header_pattern.match(part):
            if current_body.strip():
                sections.append((current_header, current_body.strip()))
            current_header = part
            current_body = ""
        else:
            current_body += "\n" + part

    if current_body.strip():
        sections.append((current_header, current_body.strip()))

    if not sections:
        sections = [("", text.strip())]

    final_sections = []
    for header, body in sections:
        if len(body) <= max_chars:
            final_sections.append((header, body))
        else:
            paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
            buffer = ""
            for para in paragraphs:
                if len(buffer) + len(para) + 2 <= max_chars:
                    buffer += ("\n\n" if buffer else "") + para
                else:
                    if buffer:
                        final_sections.append((header, buffer))
                    buffer = para
            if buffer:
                final_sections.append((header, buffer))

    return final_sections


class RAGPipeline:
    def __init__(self):
        print("🚀 Initializing RAG Pipeline...")
        self.api_key = os.getenv("THAILLM_API_KEY", "")
        self.model_name = os.getenv("THAILLM_MODEL", "kbtg")
        self.chunks: List[Dict] = []
        self.bm25_index: BM25Okapi = None
        self.faiss_index: faiss.Index = None
        self.embed_model: SentenceTransformer = None
        self._build()
        print("✅ RAG Pipeline ready")

    def _load_documents(self) -> List[Dict]:
        docs = []
        patterns = [
            KB_DIR / "products" / "*.md",
            KB_DIR / "policies" / "*.md",
            KB_DIR / "store_info" / "*.md",
        ]
        category_map = {
            "products": "product",
            "policies": "policy",
            "store_info": "store_info",
        }
        for pattern in patterns:
            files = sorted(glob.glob(str(pattern)))
            category = pattern.parent.name
            for fpath in files:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                filename = Path(fpath).stem
                product_code = filename.split("_")[0] if "_" in filename else filename
                docs.append(
                    {
                        "content": content,
                        "source": fpath,
                        "filename": filename,
                        "category": category_map.get(category, category),
                        "product_code": product_code,
                    }
                )
        print(f"📚 Loaded {len(docs)} documents")
        return docs

    def _chunk_documents(self, docs: List[Dict]) -> List[Dict]:
        chunks = []
        for doc in docs:
            content = doc["content"]
            lines = content.strip().split("\n")
            title = (
                lines[0].lstrip("#").strip()
                if lines and lines[0].startswith("#")
                else doc["filename"]
            )
            sections = split_by_sections(content)
            for i, (section_header, section_body) in enumerate(sections):
                chunk_parts = [f"[ที่มา: {title}]"]
                if section_header:
                    chunk_parts.append(section_header)
                chunk_parts.append(section_body)
                chunks.append(
                    {
                        "text": "\n".join(chunk_parts),
                        "title": title,
                        "section_header": section_header,
                        "category": doc["category"],
                        "product_code": doc["product_code"],
                        "filename": doc["filename"],
                        "chunk_index": i,
                    }
                )
        print(f"✂️  Created {len(chunks)} chunks")
        return chunks

    def _build_bm25(self, texts: List[str]) -> BM25Okapi:
        print("🔨 Building BM25 index...")
        tokenized = [tokenize_thai(t) for t in texts]
        return BM25Okapi(tokenized)

    def _build_faiss(self, texts: List[str]):
        if CACHE_PATH.exists():
            with open(CACHE_PATH, "rb") as f:
                cached = pickle.load(f)
            if cached.get("model") == EMBED_MODEL_NAME and cached.get("num_chunks") == len(texts):
                print(f"📂 Loaded embeddings from cache")
                embeddings = cached["embeddings"]
                model = SentenceTransformer(EMBED_MODEL_NAME)
                index = faiss.IndexFlatIP(embeddings.shape[1])
                index.add(embeddings)
                return index, model

        print(f"🔨 Encoding {len(texts)} chunks with {EMBED_MODEL_NAME}...")
        model = SentenceTransformer(EMBED_MODEL_NAME)
        embeddings = model.encode(
            texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True
        ).astype("float32")

        with open(CACHE_PATH, "wb") as f:
            pickle.dump({"model": EMBED_MODEL_NAME, "num_chunks": len(texts), "embeddings": embeddings}, f)

        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        print(f"✅ FAISS index ready: {index.ntotal} vectors")
        return index, model

    def _build(self):
        docs = self._load_documents()
        self.chunks = self._chunk_documents(docs)
        texts = [c["text"] for c in self.chunks]
        self.bm25_index = self._build_bm25(texts)
        self.faiss_index, self.embed_model = self._build_faiss(texts)

    def _bm25_retrieve(self, query: str, top_k: int) -> List[int]:
        scores = self.bm25_index.get_scores(tokenize_thai(query))
        return np.argsort(scores)[::-1][:top_k].tolist()

    def _dense_retrieve(self, query: str, top_k: int) -> List[int]:
        q_embed = self.embed_model.encode([query], normalize_embeddings=True).astype("float32")
        _, indices = self.faiss_index.search(q_embed, top_k)
        return indices[0].tolist()

    def _rrf(self, ranked_lists: List[List[int]], k: int = RRF_K) -> List[int]:
        scores: Dict[int, float] = {}
        for ranked in ranked_lists:
            for rank, doc_idx in enumerate(ranked):
                scores[doc_idx] = scores.get(doc_idx, 0.0) + 1.0 / (k + rank + 1)
        return [idx for idx, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]

    def retrieve(self, query: str, top_k: int = TOP_K_CONTEXT) -> List[Dict]:
        bm25_res = self._bm25_retrieve(query, TOP_K_RETRIEVE)
        dense_res = self._dense_retrieve(query, TOP_K_RETRIEVE)
        fused = self._rrf([bm25_res, dense_res])
        return [self.chunks[i] for i in fused[:top_k]]

    def _call_llm(self, question: str, context_chunks: List[Dict]) -> str:
        context_str = "\n\n".join(
            f"--- เอกสาร {i+1} ({c['title']}) ---\n{c['text']}"
            for i, c in enumerate(context_chunks)
        )
        user_prompt = f"Context:\n{context_str}\n\n---\nคำถาม: {question}"

        url = f"http://thaillm.or.th/api/{self.model_name}/v1/chat/completions"
        headers = {"Content-Type": "application/json", "apikey": self.api_key}
        payload = {
            "model": "/model",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 512,
            "temperature": 0.3,
        }

        for attempt in range(4):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=60)
                if resp.status_code == 429:
                    time.sleep(min(2**attempt, 15))
                    continue
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"].strip()
                # ลบ <think>...</think> (chain-of-thought models)
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                return content
            except Exception as e:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)

        return "ขออภัยครับ ระบบมีปัญหาชั่วคราว กรุณาลองใหม่อีกครั้ง"

    def answer(self, question: str) -> Tuple[str, List[Dict]]:
        sources = self.retrieve(question)
        answer_text = self._call_llm(question, sources)
        return answer_text, sources
