import type { Metadata } from "next";
import { AccountForm } from "@/components/auth/account-form";
export const metadata: Metadata = { title: "ساخت حساب نما | NAMA Analyze", robots: { index: false, follow: false } };
export default function SignupPage() { return <AccountForm mode="signup" />; }
