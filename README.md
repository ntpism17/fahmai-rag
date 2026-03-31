# FahMai RAG System

ระบบ **Retrieval-Augmented Generation (RAG)** สำหรับตอบคำถามเกี่ยวกับร้านฟ้าใหม่ ร้านจำหน่ายสินค้าอิเล็กทรอนิกส์

> **Hackathon Result:** Super AI Engineer Season 6 — Hack3 | Score: **0.88 / 1.00**

---
##ตัวอย่างการใช้งานจริง
<img width="1178" height="1017" alt="image" src="https://github.com/user-attachments/assets/5755fae8-760c-4030-857f-61db178616ca" />
<img width="1218" height="1018" alt="image" src="https://github.com/user-attachments/assets/d4648584-8bd5-49e0-95fe-02ba3b22c5b2" />



## Architecture

```
User Question
     │
     ▼
┌─────────────────────────────────────────┐
│           Hybrid Retrieval              │
│                                         │
│  BM25 (PyThaiNLP)  +  FAISS (bge-m3)  │
│         └──────── RRF ────────┘         │
│              Top-5 Chunks               │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│         ThaiLLM (kbtg / typhoon)        │
│     Answer Generation (Thai NLP)        │
└─────────────────────────────────────────┘
     │
     ▼
  Answer + Sources
```

**Knowledge Base:** 118 markdown files → 888 chunks
- 110 product docs (laptops, phones, tablets, audio, accessories)
- 5 policy docs (warranty, returns, shipping, membership)
- 3 store info docs (about, FAQ, buying guide)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Sparse Retrieval | BM25 (rank-bm25) + PyThaiNLP tokenization |
| Dense Retrieval | FAISS + BAAI/bge-m3 embeddings |
| Fusion | Reciprocal Rank Fusion (RRF) |
| LLM | ThaiLLM API (kbtg / typhoon / openthaigpt) |

---

## Project Structure

```
├── Rag1.ipynb           # Original hackathon notebook
├── knowledge_base/      # Markdown knowledge base
│   ├── products/        # 110 product files
│   ├── policies/        # 5 policy files
│   └── store_info/      # 3 store info files
├── backend/             # FastAPI backend
│   ├── main.py
│   ├── rag/
│   │   └── pipeline.py  # RAG pipeline
│   └── requirements.txt
└── frontend/            # Next.js frontend
    └── src/
        ├── app/         # App router pages
        └── components/  # Chat UI components
```

---

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# แก้ไข .env ใส่ THAILLM_API_KEY และ KB_DIR

uvicorn main:app --reload
# → http://localhost:8000
```

### 2. Frontend

```bash
cd frontend
npm install

cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
# → http://localhost:3000
```

---

## API

```
POST /api/chat
Body: { "question": "โน้ตบุ๊ค DaoNuea AirBook 15 ราคาเท่าไหร่?" }

Response:
{
  "answer": "...",
  "sources": [{ "title": "...", "category": "product", ... }]
}
```

---

## How It Works

1. **Chunking** — แบ่ง markdown ตาม section headers (`##`, `###`) สูงสุด 1,200 ตัวอักษร/chunk
2. **BM25** — Tokenize ด้วย PyThaiNLP `newmm` engine แล้ว index ด้วย BM25Okapi
3. **Dense** — Encode ด้วย `BAAI/bge-m3` (multilingual, 1024-dim) เก็บใน FAISS `IndexFlatIP`
4. **RRF** — รวม ranked lists ทั้งสองด้วย Reciprocal Rank Fusion (k=60)
5. **Generate** — ส่ง top-5 chunks เป็น context ให้ ThaiLLM ตอบคำถามเป็นภาษาไทย
