import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const vazirmatn = localFont({ src: "../assets/vazirmatn.woff2", variable: "--font-vazirmatn", display: "swap" });
const anton = localFont({ src: "../assets/anton.ttf", variable: "--font-anton", display: "swap" });
const vietnam = localFont({ src: "../assets/be-vietnam-pro-600.ttf", variable: "--font-vietnam", display: "swap" });
export const metadata: Metadata = {
  icons: { icon: "/mark.svg" },
  title: "NAMA Analyze | نما",
  description: "نما؛ شروع یک مسیر روشن برای تحلیل بازار.",
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fa" dir="rtl" className={`${vazirmatn.variable} ${anton.variable} ${vietnam.variable}`}><body>{children}</body></html>;
}
