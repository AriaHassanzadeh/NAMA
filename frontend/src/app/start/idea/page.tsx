import type { Metadata } from "next";
import { IdeaDiscovery } from "@/components/entry/idea-discovery";

export const metadata: Metadata = { title: "ایدهٔ پروژه | NAMA Analyze" };

export default function IdeaPage() {
  return <IdeaDiscovery />;
}
