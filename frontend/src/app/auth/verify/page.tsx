import type { Metadata } from "next";
import { VerifyEmail } from "@/components/auth/verify-email";
export const metadata: Metadata = { title: "تأیید ایمیل | NAMA Analyze", robots: { index: false, follow: false } };
export default function VerifyPage() { return <VerifyEmail />; }
