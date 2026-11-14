"use client";

import { ChevronRight, Moon, Sun } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Fragment } from "react";
import { isValidIdea } from "./draft-validation";
import { updateEntryState, useEntryState } from "./entry-store";

const steps = [
  { key: "idea", label: "ایده", route: "/start/idea", number: "۰۱" },
  { key: "customer", label: "مشتری", route: "/start/customer", number: "۰۲" },
  { key: "goal", label: "هدف", route: null, number: "۰۳" },
] as const;

export function DiscoveryHeader({ step }: { step: "idea" | "customer" }) {
  const draft = useEntryState();
  const router = useRouter();
  const theme = draft.theme === "light" ? "light" : "dark";
  const current = step === "idea" ? 0 : 1;
  return <header className="entry-header">
    <Link className="entry-brand" href="/" aria-label="بازگشت به منظومهٔ نما"><Image src="/mark.svg" alt="" width={33} height={33} priority /><span lang="en">NAMA</span></Link>
    <nav className="entry-progress" aria-label="مراحل شروع پروژه">
      {steps.map((item, index) => <Fragment key={item.key}>
        {index > 0 && <span className={index <= current ? "done" : undefined} aria-hidden="true" />}
        <button type="button" data-step={item.key} className={index === current ? "current" : index < current ? "complete" : undefined}
          aria-current={index === current ? "step" : undefined} disabled={item.route === null || (item.key === "customer" && !isValidIdea(draft.idea))}
          onClick={() => { if (item.key === step) document.getElementById("entryAnswer")?.focus(); else if (item.route) router.push(item.route); }}>
          <b>{item.number}</b> {item.label}
        </button>
      </Fragment>)}
    </nav>
    <div className="entry-header-actions">
      <button type="button" className="theme-toggle" aria-label={`تغییر به حالت ${theme === "dark" ? "روشن" : "تاریک"}`} aria-pressed={theme === "dark"} onClick={() => updateEntryState({ theme: theme === "dark" ? "light" : "dark" })}>
        {theme === "dark" ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
      </button>
      <Link className="entry-back" href={step === "customer" ? "/start/idea" : "/"}>بازگشت <ChevronRight aria-hidden="true" /></Link>
    </div>
  </header>;
}
