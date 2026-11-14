import type { ReactNode } from "react";
import { AuthFrame } from "@/components/auth/auth-frame";
import { QueryProvider } from "@/components/query-provider";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return <QueryProvider><AuthFrame>{children}</AuthFrame></QueryProvider>;
}
