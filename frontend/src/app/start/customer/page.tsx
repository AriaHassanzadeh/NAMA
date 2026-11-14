import type { Metadata } from "next";
import { CustomerDiscovery } from "@/components/entry/customer-discovery";

export const metadata: Metadata = { title: "شناخت مشتری | NAMA Analyze" };

export default function CustomerPage() {
  return <CustomerDiscovery />;
}
