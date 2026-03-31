export interface Source {
  title: string;
  section_header: string;
  category: "product" | "policy" | "store_info";
  product_code: string;
  text: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp: Date;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}
