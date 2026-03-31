import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FahMai AI — ผู้ช่วยร้านฟ้าใหม่",
  description: "ถามเกี่ยวกับสินค้า นโยบาย และบริการของร้านฟ้าใหม่",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="th">
      <body>{children}</body>
    </html>
  );
}
