"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSyncExternalStore, type CSSProperties, type ReactNode } from "react";
import { updateEntryState, useEntryState } from "./entry-store";
import "./solar-entrance.css";

function subscribeMotion(callback: () => void) {
  const query = window.matchMedia("(prefers-reduced-motion: reduce)");
  query.addEventListener("change", callback);
  return () => query.removeEventListener("change", callback);
}
const motionSnapshot = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const media = [
  { key: "instagram", name: "Instagram", label: "آغاز بررسی بازار", accent: "#e87da9" },
  { key: "telegram", name: "Telegram", label: "آغاز بررسی بازار", accent: "#79b9e8" },
  { key: "youtube", name: "YouTube", label: "کشف تبلیغات", accent: "#ff727b" },
  { key: "tiktok", name: "TikTok", label: "آغاز بررسی بازار", accent: "#7edbd9" },
  { key: "linkedin", name: "LinkedIn", label: "آغاز بررسی بازار", accent: "#8baee8" },
  { key: "x", name: "X", label: "آغاز بررسی بازار", accent: "#ddd8e9" },
  { key: "podcast", name: "Podcasts", label: "کشف تبلیغات", accent: "#baa2ec" },
  { key: "news", name: "News", label: "روندها و فرصت‌ها", accent: "#e4bd9b" },
  { key: "rss", name: "RSS", label: "روندها و فرصت‌ها", accent: "#dda779" },
  { key: "search", name: "Search", label: "نمای کلی بازار", accent: "#91b8ad" },
] as const;
type MediaKey = (typeof media)[number]["key"];
const marks: Record<MediaKey, ReactNode> = {
  instagram: <><rect x="4" y="4" width="16" height="16" rx="5" stroke="currentColor" strokeWidth="1.65" /><circle cx="12" cy="12" r="3.6" stroke="currentColor" strokeWidth="1.65" /><circle cx="17.1" cy="6.9" r="1" fill="currentColor" /></>,
  telegram: <path fill="currentColor" d="m20.7 4.3-3.2 15.1c-.2 1-1 1.3-1.8.7l-4.8-3.5-2.3 2.2c-.3.3-.5.5-1 .5l.4-4.9L17 6.1c.4-.4-.1-.6-.6-.3L5.2 12.9.4 11.4c-1-.3-1.1-1 .2-1.5L19.4 2.7c.9-.3 1.7.2 1.3 1.6Z" transform="translate(1 1) scale(.96)" />,
  youtube: <><rect x="2.5" y="5.3" width="19" height="13.4" rx="4.1" fill="currentColor" /><path d="m10 9 5.3 3-5.3 3V9Z" fill="var(--planet-fill)" /></>,
  tiktok: <path fill="currentColor" d="M14.1 3h3.2c.2 1.7 1.2 3.1 2.7 3.8.6.3 1.3.4 2 .5v3.2a9.2 9.2 0 0 1-4.7-1.4v7.2a6 6 0 1 1-6.8-5.9v3.3a2.7 2.7 0 1 0 3.6 2.6V3Z" transform="translate(-1 0)" />,
  linkedin: <><rect x="3" y="3" width="18" height="18" rx="3" stroke="currentColor" strokeWidth="1.4" /><circle cx="7.4" cy="7.6" r="1.3" fill="currentColor" /><path d="M7.4 11v6.5M11.6 17.5V11m0 2.6c0-3.6 5-3.6 5 0v3.9" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" /></>,
  x: <path fill="currentColor" d="M17.5 3H21l-7.6 8.7L22.3 21h-6.9L10 15.1 4.8 21H1.3l7-8L.7 3h7.1l4.9 5.4L17.5 3Zm-1.3 16h2L6.6 4.9H4.5L16.2 19Z" />,
  podcast: <><rect x="9" y="3.5" width="6" height="12" rx="3" stroke="currentColor" strokeWidth="1.6" /><path d="M6 11a6 6 0 0 0 12 0M12 17v4m-3 0h6M3.3 7a11 11 0 0 0 0 8M20.7 7a11 11 0 0 1 0 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></>,
  news: <path d="M5 4h15v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9h2m0-5v14m3-10h8m-8 4h3v4H8v-4Zm6 0h3m-3 4h3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />,
  rss: <><circle cx="5.4" cy="18.6" r="1.9" fill="currentColor" /><path d="M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" /></>,
  search: <><path fill="currentColor" d="M21.6 12.2c0-.7-.1-1.4-.2-2.1H12v4h5.4a4.6 4.6 0 0 1-2 3.1v2.6h3.3c2-1.8 2.9-4.4 2.9-7.6Z" /><path fill="currentColor" d="M12 22c2.7 0 5-.9 6.7-2.4l-3.3-2.6a6.1 6.1 0 0 1-9.2-3.2H2.8v2.7A10 10 0 0 0 12 22Zm-5.8-8.2a6.2 6.2 0 0 1 0-3.6V7.5H2.8a10 10 0 0 0 0 9l3.4-2.7ZM12 6a5.5 5.5 0 0 1 3.9 1.5l2.9-2.8A9.7 9.7 0 0 0 12 2a10 10 0 0 0-9.2 5.5l3.4 2.7A6 6 0 0 1 12 6Z" /></>,
};
const rings = [
  { diameter: 43, duration: 58, planets: [[0, 17], [1, 197]] },
  { diameter: 70, duration: 90, planets: [[2, 83], [3, 203], [4, 323]] },
  { diameter: 100, duration: 128, planets: [[5, 47], [6, 119], [7, 191], [8, 263], [9, 335]] },
] as const;
const stars = (() => {
  let seed = 291127;
  const random = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
  return Array.from({ length: 172 }, (_, index) => ({
    index, style: { insetInlineStart: `${(random() * 100).toFixed(3)}%`, insetBlockStart: `${(random() * 100).toFixed(3)}%`,
      "--star-size": `${(random() * .95 + .7).toFixed(2)}px`, "--star-opacity": (random() * .27 + .14).toFixed(2), "--star-delay": `-${(random() * 9).toFixed(2)}s` } as CSSProperties,
  }));
})();
function ControlIcon({ children }: { children: ReactNode }) {
  return <svg className="icon solar-control-mark" viewBox="0 0 24 24" fill="none" aria-hidden="true">{children}</svg>;
}
const arrow = <path d="M18 12H6m6 6-6-6 6-6" />;

export function SolarEntrance() {
  const router = useRouter();
  const preferences = useEntryState();
  const theme = preferences.theme === "light" ? "light" : "dark";
  const reducedMotion = useSyncExternalStore(subscribeMotion, motionSnapshot, () => true);
  const paused = preferences.paused === true;
  function selectSource(source: string) {
    updateEntryState({ source });
    router.push("/start/idea");
  }
  const motionLabel = reducedMotion ? "حرکت مطابق تنظیم کاهش انیمیشن غیرفعال است" : paused ? "ادامهٔ حرکت مدارها" : "توقف حرکت مدارها";
  return (
    <main className={`solar-portal ${paused || reducedMotion ? "is-paused" : ""}`} data-theme={theme} aria-label="منظومهٔ رسانه‌ای نما">
      <h1 className="sr-only">نما؛ شروع یک مسیر روشن برای تحلیل بازار</h1>
      <div className="solar-stars" aria-hidden="true">{stars.map(({ index, style }) => <i key={index} className={`solar-star ${index % 17 === 0 ? "solar-star--shimmer" : ""} ${index % 43 === 0 ? "solar-star--cross" : ""}`} style={style} />)}</div>
      <div className="solar-atmosphere" aria-hidden="true" />
      <div className="solar-tools">
        <button type="button" className="theme-toggle" aria-label={`تغییر به حالت ${theme === "dark" ? "روشن" : "تاریک"}`} aria-pressed={theme === "dark"} onClick={() => updateEntryState({ theme: theme === "dark" ? "light" : "dark" })}>
          <ControlIcon>{theme === "dark" ? <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1" /></> : <path d="M20 14A8 8 0 0 1 10 4a8 8 0 1 0 10 10Z" />}</ControlIcon>
        </button>
        <button type="button" className="solar-motion-toggle" aria-label={motionLabel} title={motionLabel} aria-pressed={paused || reducedMotion} disabled={reducedMotion} onClick={() => updateEntryState({ paused: !paused })}>
          <ControlIcon>{paused || reducedMotion ? <path d="m9 5 10 7-10 7V5Z" /> : <path d="M8 5v14M16 5v14" />}</ControlIcon>
        </button>
        <Link className="solar-auth-link" href="/auth/login" lang="en" dir="ltr">Sign in / Sign up</Link>
      </div>
      <div className="solar-edition" aria-hidden="true"><span /><span>NAMA UNIVERSE</span></div>
      <section className="solar-system" aria-label="رسانه‌ها در مدار نما">
        <div className="solar-aura" aria-hidden="true" />
        {rings.map((ring, ringIndex) => <div key={ringIndex} className={`solar-orbit solar-orbit--${ringIndex + 1}`} style={{ "--orbit-diameter": `${ring.diameter}%`, "--orbit-duration": `${ring.duration}s` } as CSSProperties}>
          <div className="solar-orbit-track" aria-hidden="true" />
          {ring.planets.map(([index, phase]) => {
            const item = media[index];
            return <div key={item.key} className="solar-rotor" style={{ "--phase": `${phase}deg` } as CSSProperties}><div className="solar-distance"><div className="solar-counter">
              <button type="button" className={`solar-planet solar-planet--${item.key}`} style={{ "--planet-accent": item.accent } as CSSProperties} aria-label={`${item.name} — ${item.label}`} aria-pressed={preferences.source === item.key} onClick={() => selectSource(item.key)}>
                <svg className="solar-media-mark" viewBox="0 0 24 24" fill="none" aria-hidden="true">{marks[item.key]}</svg>
                <span className="solar-planet-tooltip"><strong lang="en">{item.name}</strong><small>{item.label}</small></span>
              </button>
            </div></div></div>;
          })}
        </div>)}
        <div className="solar-center"><button type="button" className="solar-core" aria-label="شروع با نما" onClick={() => selectSource("nama")}>
          <span className="solar-core-halo" aria-hidden="true" /><Image src="/mark.svg" alt="" width={91} height={91} priority /><span className="nama-logotype">NAMA</span><span className="solar-core-enter" aria-hidden="true"><ControlIcon>{arrow}</ControlIcon></span>
        </button></div>
      </section>
      <footer className="solar-footer">
        <span className="solar-signature" lang="en" dir="ltr">INTELLIGENCE. IN ORBIT.</span>
        <button type="button" className="solar-enter-hint" onClick={() => selectSource("nama")}><span /><span>برای شروع، روی نما کلیک کن</span><ControlIcon>{arrow}</ControlIcon></button>
        <span className="solar-index" aria-hidden="true">01 <i /> NAMA</span>
      </footer>
    </main>
  );
}
