import Image from "next/image";
import { HealthStatus } from "@/components/health-status";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-3xl flex-col justify-center gap-8 px-5 py-12 sm:px-8">
      <header className="flex items-center gap-3">
        <Image src="/mark.svg" alt="نشان نما" width={40} height={40} priority />
        <div><p className="text-xl font-bold tracking-wide" dir="ltr">NAMA Analyze</p><p className="mt-1 text-sm text-[#666571]">محیط توسعهٔ محلی</p></div>
      </header>
      <section aria-labelledby="page-title" className="rounded-3xl border border-[#e7e7ec] bg-white p-6 shadow-sm sm:p-10">
        <span className="inline-block rounded-full bg-[#fff0f1] px-3 py-1 text-xs font-medium text-primary">مرحلهٔ ۰۱ · زیرساخت</span>
        <h1 id="page-title" className="mt-5 text-2xl leading-relaxed font-bold sm:text-3xl">بررسی اتصال سرویس‌ها</h1>
        <p className="mt-3 text-sm leading-8 text-[#666571]">این صفحه ارتباط Next.js با Django و PostgreSQL را از مسیر مشترک برنامه بررسی می‌کند.</p>
        <HealthStatus />
      </section>
      <footer className="text-sm leading-7 text-[#666571]">این نسخه فقط زیرساخت اولیه است. صفحه‌های محصول و داده‌های نمایشی در مراحل بعد اضافه می‌شوند.</footer>
    </main>
  );
}
