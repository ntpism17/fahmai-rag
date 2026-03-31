"use client";

import { Message } from "@/lib/types";
import SourceCard from "./SourceCard";

function BotIcon() {
  return (
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold shadow-sm">
      F
    </div>
  );
}

function UserIcon() {
  return (
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 text-sm font-semibold">
      U
    </div>
  );
}

export default function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      {isUser ? <UserIcon /> : <BotIcon />}

      <div className={`flex flex-col gap-2 max-w-[80%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-blue-600 text-white rounded-tr-sm"
              : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm"
          }`}
        >
          {message.content}
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="w-full">
            <p className="text-xs text-gray-400 mb-1.5 ml-1">แหล่งข้อมูลที่ใช้</p>
            <div className="flex flex-col gap-1.5">
              {message.sources.map((src, i) => (
                <SourceCard key={i} source={src} index={i} />
              ))}
            </div>
          </div>
        )}

        <span className="text-xs text-gray-400 px-1">
          {message.timestamp.toLocaleTimeString("th-TH", { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}
