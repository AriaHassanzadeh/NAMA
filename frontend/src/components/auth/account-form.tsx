"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Eye, EyeOff, LoaderCircle, Mail } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { authErrorMessage, getCurrentUser, resendVerification, signIn, signOut, signUp } from "@/lib/api/auth";

const email = z.string().trim().min(1, "ایمیلت را بنویس.").email("یک ایمیل معتبر وارد کن.").max(254).toLowerCase();
const baseSchema = z.object({
  email, password: z.string().min(1, "رمز عبور را بنویس.").max(1024, "رمز عبور بیش از حد طولانی است."),
  display_name: z.string().trim().max(150, "نام باید حداکثر ۱۵۰ نویسه باشد."), confirm_password: z.string(),
});
const signupSchema = baseSchema.extend({ password: z.string().min(8, "رمز عبور باید دست‌کم ۸ نویسه باشد.").max(128, "رمز عبور باید حداکثر ۱۲۸ نویسه باشد.") })
  .refine((values) => values.password === values.confirm_password, { path: ["confirm_password"], message: "تکرار رمز عبور یکسان نیست." });
type FormValues = z.infer<typeof baseSchema>;
const empty = { email: "", password: "", display_name: "", confirm_password: "" };

export function AccountForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const client = useQueryClient();
  const [visiblePassword, setVisiblePassword] = useState(false);
  const [pendingEmail, setPendingEmail] = useState("");
  const [localDelivery, setLocalDelivery] = useState(false);
  const signup = mode === "signup";
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(signup ? signupSchema : baseSchema), defaultValues: empty,
  });
  const session = useQuery({ queryKey: ["session"], queryFn: ({ signal }) => getCurrentUser(signal) });
  const mutation = useMutation({ mutationFn: async (values: FormValues) => signup ? await signUp(values) : await signIn(values), gcTime: 0 });
  const resend = useMutation({ mutationFn: resendVerification });
  const logout = useMutation({ mutationFn: signOut, onSuccess: () => client.setQueryData(["session"], null) });

  async function submit(values: FormValues) {
    if (mutation.isPending) return;
    try {
      const data = await mutation.mutateAsync(values);
      reset({ ...empty, email: values.email });
      mutation.reset();
      if ("user" in data) {
        client.setQueryData(["session"], data.user);
        router.replace("/start/idea");
      } else {
        setPendingEmail(values.email);
        setLocalDelivery(data.delivery_mode === "local");
      }
    } catch { /* The mutation renders a localized error below the form. */ }
  }

  if (session.data) return <>
    <h1 id="authTitle">خوش آمدی، {session.data.display_name}.</h1>
    <p className="auth-description">وارد حساب نما شده‌ای.</p>
    <p className="auth-account-email" dir="ltr">{session.data.email || session.data.username}</p>
    <Link className="auth-primary-link" href="/start/idea">شروع بررسی <ArrowLeft aria-hidden="true" /></Link>
    <button type="button" className="auth-text-button" onClick={() => logout.mutate()} disabled={logout.isPending}>خروج از حساب</button>
    {logout.isError && <p className="auth-error" role="alert">{authErrorMessage(logout.error)}</p>}
  </>;

  if (pendingEmail) return <div id="auth-pending">
    <Mail className="auth-state-icon" aria-hidden="true" />
    <h1 id="authTitle">{localDelivery ? "درخواست تأیید ثبت شد." : "ایمیلت را بررسی کن."}</h1>
    <p className="auth-description">اگر این آدرس برای ثبت‌نام قابل استفاده باشد، پیام تأیید برایش آماده می‌شود. برای ورود، ابتدا ایمیلت را تأیید کن.</p>
    <p className="auth-account-email" dir="ltr">{pendingEmail}</p>
    {localDelivery && <p className="auth-help auth-local-notice">محیط محلی: پیام تأیید در صندوق ایمیل محلی پروژه آماده می‌شود و به صندوق واقعی ایمیل فرستاده نمی‌شود.</p>}
    <p id="authStatus" className="auth-status" role="status">درخواست ثبت‌نام دریافت شد.</p>
    <button type="button" className="auth-secondary" onClick={() => resend.mutate(pendingEmail)} disabled={resend.isPending}>ارسال دوبارهٔ ایمیل تأیید</button>
    {resend.isSuccess && <p className="auth-status" role="status">اگر ایمیل نیاز به تأیید داشته باشد، پیام برایش آماده می‌شود.</p>}
    {resend.isError && <p id="authError" className="auth-error" role="alert">{authErrorMessage(resend.error)}</p>}
    <Link className="auth-primary-link" href="/auth/login">بازگشت به ورود <ArrowLeft aria-hidden="true" /></Link>
  </div>;

  return <>
    <p className="auth-eyebrow">مسیرت با نما شروع می‌شود</p>
    <h1 id="authTitle">{signup ? "حساب نما را بساز." : "خوش برگشتی."}</h1>
    <p className="auth-description">{signup ? "با ایمیل و رمز عبور ثبت‌نام کن؛ سپس ایمیلت را تأیید کن." : "با ایمیل و رمز عبورت وارد شو."}</p>
    <form className="auth-form" noValidate onSubmit={handleSubmit(submit)}>
      {signup && <div className="auth-field"><label htmlFor="authDisplayName">نام نمایشی <small>اختیاری</small></label>
        <input id="authDisplayName" autoComplete="name" maxLength={150} aria-invalid={Boolean(errors.display_name)} aria-describedby={errors.display_name ? "nameError" : undefined} {...register("display_name")} />
        {errors.display_name && <p id="nameError" className="auth-field-error" role="alert">{errors.display_name.message}</p>}
      </div>}
      <div className="auth-field"><label htmlFor="authEmail">ایمیل</label>
        <input id="authEmail" type="email" dir="ltr" inputMode="email" autoComplete={signup ? "email" : "username"} autoCapitalize="none" spellCheck={false} maxLength={254} placeholder="you@example.com" aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? "emailError" : undefined} {...register("email")} />
        {errors.email && <p id="emailError" className="auth-field-error" role="alert">{errors.email.message}</p>}
      </div>
      <div className="auth-field"><label htmlFor="authPassword">رمز عبور</label>
        <div className="auth-password-field"><input id="authPassword" type={visiblePassword ? "text" : "password"} dir="ltr" autoComplete={signup ? "new-password" : "current-password"} maxLength={signup ? 128 : 1024} aria-invalid={Boolean(errors.password)} aria-describedby={`${signup ? "passwordHelp" : ""}${errors.password ? " passwordError" : ""}`.trim() || undefined} {...register("password")} />
          <button type="button" className="auth-password-toggle" aria-label={visiblePassword ? "پنهان کردن رمز عبور" : "نمایش رمز عبور"} aria-pressed={visiblePassword} onClick={() => setVisiblePassword(!visiblePassword)}>{visiblePassword ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}</button>
        </div>
        {signup && <p id="passwordHelp" className="auth-help">دست‌کم ۸ نویسه؛ از رمزهای رایج استفاده نکن.</p>}
        {errors.password && <p id="passwordError" className="auth-field-error" role="alert">{errors.password.message}</p>}
      </div>
      {signup && <div className="auth-field"><label htmlFor="authConfirmPassword">تکرار رمز عبور</label>
        <input id="authConfirmPassword" type="password" dir="ltr" autoComplete="new-password" maxLength={128} aria-invalid={Boolean(errors.confirm_password)} aria-describedby={errors.confirm_password ? "confirmError" : undefined} {...register("confirm_password")} />
        {errors.confirm_password && <p id="confirmError" className="auth-field-error" role="alert">{errors.confirm_password.message}</p>}
      </div>}
      {mutation.isError && <p id="authError" className="auth-error" role="alert">{authErrorMessage(mutation.error, !signup)}</p>}
      <button className="auth-submit" type="submit" disabled={mutation.isPending}>{mutation.isPending ? <><LoaderCircle className="auth-spinner" aria-hidden="true" /> کمی صبر کن…</> : <>{signup ? "ساخت حساب" : "ورود به نما"}<ArrowLeft aria-hidden="true" /></>}</button>
    </form>
    {!signup && <Link className="auth-verification-link" href="/auth/verify">ایمیلت را تأیید نکرده‌ای؟ ارسال دوباره</Link>}
    <p className="auth-switch">{signup ? "حساب داری؟" : "هنوز حساب نداری؟"} <Link href={signup ? "/auth/login" : "/auth/signup"}>{signup ? "وارد شو" : "ثبت‌نام کن"}</Link></p>
  </>;
}
