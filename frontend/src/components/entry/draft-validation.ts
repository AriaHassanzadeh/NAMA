import { z } from "zod";

export const MAX_ANSWER_LENGTH = 2000;
export const MAX_MARKET_LENGTH = 100;
export const audienceValues = ["consumer", "business", "both"] as const;
export const budgetOptions = [
  "هنوز مشخص نیست",
  "کمتر از ۲۰ میلیون تومان",
  "۲۰ تا ۵۰ میلیون تومان",
  "۵۰ تا ۱۰۰ میلیون تومان",
  "بیشتر از ۱۰۰ میلیون تومان",
] as const;

export const ideaSchema = z.object({
  idea: z.string().trim()
    .min(5, "ایده‌ات را در یک جملهٔ کوتاه بنویس؛ حداقل ۵ نویسه.")
    .max(MAX_ANSWER_LENGTH, "توضیح ایده باید حداکثر ۲۰۰۰ نویسه باشد."),
});

export const customerSchema = z.object({
  customer: z.string().trim().max(MAX_ANSWER_LENGTH, "توضیح مشتری باید حداکثر ۲۰۰۰ نویسه باشد."),
  audience: z.enum(["", ...audienceValues]),
  market: z.string().trim().max(MAX_MARKET_LENGTH, "بازار اولیه باید حداکثر ۱۰۰ نویسه باشد."),
  budget: z.enum(budgetOptions),
}).refine((value) => Boolean(value.audience) || value.customer.length >= 3, {
  path: ["customer"], message: "نوع مشتری را انتخاب کن یا کمی درباره‌اش بنویس.",
});

export function isValidIdea(value: unknown): boolean {
  return ideaSchema.safeParse({ idea: value }).success;
}
