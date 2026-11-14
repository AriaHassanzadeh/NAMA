import { z } from "zod";
import type { components } from "./generated";

type EntryOptions = components["schemas"]["EntryOptionsResponse"];

const entryOptionsSchema = z.object({
  source_kind: z.literal("demo"),
  label: z.string().min(1).max(200),
  idea_examples: z.array(z.object({
    id: z.string().min(1).max(100),
    text: z.string().min(1).max(200),
    icon: z.enum(["shirt", "bolt"]),
  })).max(12),
});

export async function getEntryOptions(signal: AbortSignal): Promise<EntryOptions> {
  const response = await fetch("/api/v1/demo/entry-options/", {
    signal, cache: "no-store", credentials: "same-origin",
  });
  if (!response.ok) throw new Error("Example ideas are unavailable.");
  return entryOptionsSchema.parse(await response.json());
}
