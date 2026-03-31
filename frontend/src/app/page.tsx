"use client";

import ChatInput from "@/components/ChatInput";
import ChatMessage from "@/components/ChatMessage";
import TypingIndicator from "@/components/TypingIndicator";
import { ChatResponse, Message } from "@/lib/types";
import { useEffect, useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SUGGESTED_QUESTIONS = [
  "โน้ตบุ๊ค DaoNuea AirBook 15 สเปคเป็นยังไงบ้าง?",
  "นโยบายการคืนสินค้าของร้านเป็นยังไง?",
  "ร้านฟ้าใหม่มีสาขาที่ไหนบ้าง?",
  "ประกันสินค้าครอบคลุมอะไรบ้าง?",
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendQuestion = async (question: string) => {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: ChatResponse = await res.json();

      const botMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "ขออภัยครับ เกิดข้อผิดพลาดในการเชื่อมต่อ กรุณาลองใหม่อีกครั้ง",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto">
      {/* Header */}
      <header className="flex items-center gap-3 px-5 py-4 bg-white border-b border-gray-200 shadow-sm">
        <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
          F
        </div>
        <div>
          <h1 className="font-semibold text-gray-900 leading-tight">FahMai AI</h1>
          <p className="text-xs text-gray-400">ผู้ช่วยอัจฉริยะร้านฟ้าใหม่</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-gray-400">ออนไลน์</span>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto scrollbar-thin px-4 py-6 space-y-5">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
            <div>
              <div className="w-16 h-16 rounded-2xl bg-blue-600 flex items-center justify-center text-white text-3xl font-bold mx-auto mb-3 shadow-md">
                F
              </div>
              <h2 className="text-xl font-semibold text-gray-800">ยินดีต้อนรับสู่ FahMai AI</h2>
              <p className="text-sm text-gray-500 mt-1">
                ถามเกี่ยวกับสินค้า นโยบาย และบริการของร้านฟ้าใหม่ได้เลยครับ
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendQuestion(q)}
                  disabled={loading}
                  className="text-left text-sm text-gray-600 bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 transition-all shadow-sm disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </main>

      {/* Input */}
      <footer className="px-4 py-4 bg-gray-50 border-t border-gray-200">
        <ChatInput onSend={sendQuestion} disabled={loading} />
        <p className="text-center text-xs text-gray-400 mt-2">
          ข้อมูลจาก Knowledge Base ของร้านฟ้าใหม่ — Powered by Hybrid RAG (BM25 + FAISS)
        </p>
      </footer>
    </div>
  );
}
