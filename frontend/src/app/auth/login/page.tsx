import type { Metadata } from "next";
import { AccountForm } from "@/components/auth/account-form";
export const metadata: Metadata = { title: "ورود به نما | NAMA Analyze", robots: { index: false, follow: false } };
export default function LoginPage() { return <AccountForm mode="login" />; }
