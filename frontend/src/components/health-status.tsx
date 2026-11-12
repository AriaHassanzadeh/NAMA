"use client";
import { useEffect, useState } from "react";

type HealthState = "pending" | "ready" | "error";
const messages: Record<HealthState, string> = {
  pending: "در حال بررسی اتصال…",
  ready: "اتصال فرانت‌اند، بک‌اند و پایگاه داده برقرار است.",
  error: "اتصال کامل برقرار نشد. سرویس‌ها را بررسی کنید و دوباره تلاش کنید.",
};
async function fetchHealth(signal: AbortSignal): Promise<"ready" | "error"> {
  try {
    const response = await fetch("/api/v1/health/", {
      cache: "no-store", signal: AbortSignal.any([signal, AbortSignal.timeout(8000)]),
    });
    const data: unknown = await response.json();
    return response.ok && typeof data === "object" && data !== null && "status" in data && "database" in data && data.status === "ok" && data.database === "ok" ? "ready" : "error";
  } catch {
    return "error";
  }
}
export function HealthStatus() {
  const [state, setState] = useState<HealthState>("pending");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void fetchHealth(controller.signal).then((result) => {
      if (!controller.signal.aborted) setState(result);
    });
    return () => controller.abort();
  }, [attempt]);
  const color = state === "ready" ? "bg-[#16865c]" : state === "error" ? "bg-primary" : "bg-[#81808b]";
  return (
    <div className="mt-7 border-t border-[#e7e7ec] pt-6">
      <div role="status" aria-live="polite" aria-atomic="true" aria-busy={state === "pending"} className="flex items-start gap-3 rounded-2xl bg-[#f8f9fb] p-4">
        <span aria-hidden="true" className={`mt-2 size-2.5 shrink-0 rounded-full ${color}`} />
        <p className="text-sm leading-7">{messages[state]}</p>
      </div>
      <div className="mt-5 flex flex-wrap items-center gap-5">
        <button type="button" disabled={state === "pending"} onClick={() => { setState("pending"); setAttempt((value) => value + 1); }} className="rounded-xl bg-primary px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-[#c5222b] disabled:opacity-60">
          {state === "pending" ? "کمی صبر کنید" : "بررسی دوباره"}
        </button>
        <a className="max-w-full text-sm text-[#666571] underline decoration-[#d0cfd6] underline-offset-4" href="/api/v1/health/" dir="ltr">/api/v1/health/</a>
      </div>
    </div>
  );
}
