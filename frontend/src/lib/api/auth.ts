import { z } from "zod";

const userSchema = z.object({ id: z.number(), username: z.string(), display_name: z.string(), email: z.string() });
const sessionSchema = z.object({ user: userSchema, csrfToken: z.string() });
const detailSchema = z.object({ detail: z.string() });
const pendingSchema = detailSchema.extend({ delivery_mode: z.enum(["local", "smtp"]) });
export type SessionUser = z.infer<typeof userSchema>;

export class AuthError extends Error {
  constructor(public status: number, public passwordRejected = false) { super("Authentication request failed."); }
}

async function post(path: string, payload: object) {
  const csrf = await fetch("/api/v1/auth/csrf/", { credentials: "same-origin", cache: "no-store" });
  if (!csrf.ok) throw new AuthError(csrf.status);
  const { csrfToken } = z.object({ csrfToken: z.string().min(1) }).parse(await csrf.json());
  const response = await fetch(`/api/v1/auth/${path}/`, {
    method: "POST", credentials: "same-origin", cache: "no-store",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken }, body: JSON.stringify(payload),
  });
  const data: unknown = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw new AuthError(response.status, typeof data === "object" && data !== null && "password" in data);
  return data;
}

export const signIn = async ({ email, password }: { email: string; password: string }) => sessionSchema.parse(await post("login", { email, password }));
export const signUp = async ({ email, password, display_name }: { email: string; password: string; display_name: string }) => pendingSchema.parse(await post("signup", { email, password, display_name }));
export const resendVerification = async (email: string) => pendingSchema.parse(await post("verification/resend", { email }));
export const confirmVerification = async (token: string) => detailSchema.parse(await post("verification/confirm", { token }));
export const signOut = async () => { await post("logout", {}); };

export async function getCurrentUser(signal: AbortSignal): Promise<SessionUser | null> {
  const response = await fetch("/api/v1/auth/me/", { signal, credentials: "same-origin", cache: "no-store" });
  if (response.status === 403) return null;
  if (!response.ok) throw new AuthError(response.status);
  return z.object({ user: userSchema }).parse(await response.json()).user;
}

export function authErrorMessage(error: unknown, login = false) {
  if (error instanceof AuthError) {
    if (error.status === 429) return "درخواست‌های زیادی فرستاده‌ای؛ کمی صبر کن و دوباره تلاش کن.";
    if (error.status === 403) return "صفحه را تازه‌سازی کن و دوباره تلاش کن.";
    if (login && error.status === 400) return "ایمیل یا رمز عبور درست نیست، یا ایمیل هنوز تأیید نشده است.";
    if (error.passwordRejected) return "رمز عبور قوی‌تری انتخاب کن؛ از رمزهای رایج یا شبیه به اطلاعات حساب استفاده نکن.";
  }
  return "ارتباط با نما برقرار نشد. دوباره تلاش کن.";
}
