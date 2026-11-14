import type { ReactNode } from "react";
import { QueryProvider } from "@/components/query-provider";

export default function StartLayout({ children }: { children: ReactNode }) {
  return <QueryProvider>{children}</QueryProvider>;
}
