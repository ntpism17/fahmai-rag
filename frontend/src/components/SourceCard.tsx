"use client";

import { Source } from "@/lib/types";
import { useState } from "react";

const categoryLabel: Record<string, string> = {
  product: "สินค้า",
  policy: "นโยบาย",
  store_info: "ข้อมูลร้าน",
};

const categoryColor: Record<string, string> = {
  product: "bg-blue-100 text-blue-700",
  policy: "bg-amber-100 text-amber-700",
  store_info: "bg-green-100 text-green-700",
};

export default function SourceCard({ source, index }: { source: Source; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const label = categoryLabel[source.category] ?? source.category;
  const color = categoryColor[source.category] ?? "bg-gray-100 text-gray-700";

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-3 text-sm shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-100 text-gray-500 text-xs font-semibold flex items-center justify-center">
            {index + 1}
          </span>
          <div className="min-w-0">
            <p className="font-medium text-gray-800 truncate">{source.title}</p>
            {source.section_header && (
              <p className="text-gray-400 text-xs truncate">{source.section_header}</p>
            )}
          </div>
        </div>
        <span className={`flex-shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${color}`}>
          {label}
        </span>
      </div>

      {expanded && (
        <p className="mt-2 text-gray-600 text-xs leading-relaxed whitespace-pre-wrap border-t border-gray-100 pt-2">
          {source.text}
        </p>
      )}

      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-1.5 text-xs text-blue-500 hover:text-blue-700 transition-colors"
      >
        {expanded ? "ย่อ ▲" : "ดูเนื้อหา ▼"}
      </button>
    </div>
  );
}
