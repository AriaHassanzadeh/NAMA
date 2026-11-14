"use client";

import Image from "next/image";
import Link from "next/link";
import { ChevronRight, Moon, Sun } from "lucide-react";
import type { ReactNode } from "react";
import { updateEntryState, useEntryState } from "@/components/entry/entry-store";
import "./auth.css";

export function AuthFrame({ children }: { children: ReactNode }) {
  const theme = useEntryState().theme === "light" ? "light" : "dark";
  return <main className="auth-portal" data-theme={theme}>
    <header className="auth-header">
      <Link className="auth-brand" href="/" aria-label="بازگشت به منظومهٔ نما"><Image src="/mark.svg" alt="" width={33} height={33} priority /><span lang="en">NAMA</span></Link>
      <div className="auth-header-actions">
        <button type="button" className="theme-toggle" aria-label={`تغییر به حالت ${theme === "dark" ? "روشن" : "تاریک"}`} aria-pressed={theme === "dark"} onClick={() => updateEntryState({ theme: theme === "dark" ? "light" : "dark" })}>{theme === "dark" ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}</button>
        <Link href="/" className="auth-back">بازگشت <ChevronRight aria-hidden="true" /></Link>
      </div>
    </header>
    <div className="auth-content"><section className="auth-card" aria-labelledby="authTitle"><Image className="auth-mark" src="/mark.svg" alt="نشان نما" width={40} height={40} />{children}</section></div>
    <footer className="auth-footer">نما؛ شروع یک مسیر روشن برای تحلیل بازار.</footer>
  </main>;
}
