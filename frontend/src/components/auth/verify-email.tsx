"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, Mail } from "lucide-react";
import Link from "next/link";
import { useSyncExternalStore } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AuthError, authErrorMessage, confirmVerification, resendVerification } from "@/lib/api/auth";

function subscribeHash(callback: () => void) {
  window.addEventListener("hashchange", callback);
  return () => window.removeEventListener("hashchange", callback);
}
const getHash = () => window.location.hash;
const schema = z.object({ email: z.string().trim().email("یک ایمیل معتبر وارد کن.").max(254).toLowerCase() });

export function VerifyEmail() {
  const hash = useSyncExternalStore(subscribeHash, getHash, () => "");
  const token = new URLSearchParams(hash.slice(1)).get("token") ?? "";
  const { register, handleSubmit, formState: { errors } } = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema), defaultValues: { email: "" } });
  const confirmation = useMutation({ mutationFn: confirmVerification, gcTime: 0 });
  const resend = useMutation({ mutationFn: resendVerification });

  async function confirm() {
    if (confirmation.isPending) return;
    try { await confirmation.mutateAsync(token); } catch { /* Render the safe, localized result. */ }
    finally {
      window.history.replaceState(window.history.state, "", window.location.pathname);
      window.dispatchEvent(new Event("hashchange"));
    }
  }

  if (confirmation.isSuccess) return <>
    <CheckCircle2 className="auth-state-icon" aria-hidden="true" />
    <h1 id="authTitle">ایمیلت تأیید شد.</h1>
    <p id="authStatus" className="auth-status" role="status">حالا می‌توانی با ایمیل و رمز عبورت وارد نما شوی.</p>
    <Link className="auth-primary-link" href="/auth/login">ورود به نما <ArrowLeft aria-hidden="true" /></Link>
  </>;

  const invalid = confirmation.isError && confirmation.error instanceof AuthError && confirmation.error.status === 400;
  return <>
    <Mail className="auth-state-icon" aria-hidden="true" />
    <h1 id="authTitle">ایمیلت را تأیید کن.</h1>
    <p className="auth-description">{token ? "برای تأیید این ایمیل و فعال کردن حسابت، دکمهٔ زیر را بزن. لینک تا ۲۴ ساعت معتبر است." : "لینک داخل پیام تأیید را باز کن؛ یا برای دریافت دوباره، ایمیلت را بنویس."}</p>
    {token && <button type="button" className="auth-submit auth-verify-confirm" onClick={() => void confirm()} disabled={confirmation.isPending}>{confirmation.isPending ? "در حال تأیید…" : "تأیید ایمیل"}</button>}
    {confirmation.isError && <p id="authError" className="auth-error" role="alert">{invalid ? "این لینک نامعتبر است، منقضی شده یا قبلاً استفاده شده است. یک پیام تازه درخواست کن." : authErrorMessage(confirmation.error)}</p>}
    {!confirmation.isPending && <form className="auth-form auth-resend-form" noValidate onSubmit={handleSubmit(({ email }) => { if (!resend.isPending) resend.mutate(email); })}>
      <div className="auth-field"><label htmlFor="authEmail">ایمیل</label>
        <input id="authEmail" type="email" dir="ltr" autoComplete="email" inputMode="email" autoCapitalize="none" spellCheck={false} maxLength={254} placeholder="you@example.com" aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? "resendEmailError" : undefined} {...register("email")} />
        {errors.email && <p id="resendEmailError" className="auth-field-error" role="alert">{errors.email.message}</p>}
      </div>
      <button type="submit" className="auth-secondary auth-resend-submit" disabled={resend.isPending}>{resend.isPending ? "کمی صبر کن…" : "ارسال دوبارهٔ ایمیل تأیید"}</button>
      {resend.isSuccess && <p id="authStatus" className="auth-status" role="status">اگر ایمیل نیاز به تأیید داشته باشد، پیام برایش آماده می‌شود.</p>}
      {resend.data?.delivery_mode === "local" && <p className="auth-help auth-local-notice">محیط محلی: پیام در صندوق ایمیل محلی پروژه آماده می‌شود و به صندوق واقعی ایمیل فرستاده نمی‌شود.</p>}
      {resend.isError && <p className="auth-error" role="alert">{authErrorMessage(resend.error)}</p>}
    </form>}
    <Link className="auth-verification-link" href="/auth/login">بازگشت به ورود</Link>
  </>;
}
