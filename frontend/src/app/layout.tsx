import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const vazirmatn = localFont({ src: "../assets/vazirmatn.woff2", variable: "--font-vazirmatn", display: "swap" });
export const metadata: Metadata = {
  icons: { icon: "/mark.svg" },
  title: "NAMA Analyze | بررسی اتصال",
  description: "محیط توسعهٔ محلی NAMA Analyze؛ بررسی اتصال فرانت‌اند، بک‌اند و پایگاه داده.",
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fa" dir="rtl" className={vazirmatn.variable}><body>{children}</body></html>;
}
