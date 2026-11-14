"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Check, CornerDownLeft, Globe, Plus, Store, Users } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, type KeyboardEvent } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { DiscoveryHeader } from "./discovery-header";
import { audienceValues, budgetOptions, customerSchema, isValidIdea, MAX_ANSWER_LENGTH, MAX_MARKET_LENGTH } from "./draft-validation";
import { updateEntryState, useEntryPersistence, useEntryReady, useEntryState } from "./entry-store";
import "./idea-discovery.css";

type CustomerForm = z.infer<typeof customerSchema>;
const audiences = [
  { value: "consumer", label: "خریدار نهایی", icon: Users },
  { value: "business", label: "کسب‌وکارها", icon: Store },
  { value: "both", label: "هر دو گروه", icon: Globe },
] as const;
const sample = "خانم‌های شاغل ۲۵ تا ۳۵ سال که برای خرید لباس روزمره، کیفیت و سادگی برایشان مهم است.";
const persianNumber = new Intl.NumberFormat("fa-IR", { useGrouping: false });

export function CustomerDiscovery() {
  const router = useRouter();
  const draft = useEntryState();
  const ready = useEntryReady();
  const persistent = useEntryPersistence();
  const theme = draft.theme === "light" ? "light" : "dark";
  const ideaValid = isValidIdea(draft.idea);
  const customer = typeof draft.customer === "string" ? draft.customer.slice(0, MAX_ANSWER_LENGTH) : "";
  const audience: CustomerForm["audience"] = audienceValues.find((value) => value === draft.audience) ?? "";
  const market = typeof draft.market === "string" ? draft.market.slice(0, MAX_MARKET_LENGTH) : "";
  const budget = budgetOptions.find((value) => value === draft.budget) ?? budgetOptions[0];
  const values = useMemo(() => ({ customer, audience, market, budget }), [customer, audience, market, budget]);
  const { register, handleSubmit, setValue, setFocus, clearErrors, formState: { errors } } = useForm<CustomerForm>({
    resolver: zodResolver(customerSchema), values, resetOptions: { keepErrors: true },
  });
  const saved = draft.customerSaved === true && customerSchema.safeParse(values).success;

  useEffect(() => {
    if (ready && !ideaValid) router.replace("/start/idea");
  }, [ready, ideaValid, router]);

  function edit(patch: Partial<CustomerForm>) {
    updateEntryState({ ...patch, customerSaved: false, completed: false });
    clearErrors();
  }
  function chooseAudience(value: CustomerForm["audience"]) {
    const next = audience === value ? "" : value;
    setValue("audience", next, { shouldDirty: true });
    edit({ audience: next });
  }
  function useExample() {
    setValue("customer", sample, { shouldDirty: true });
    edit({ customer: sample });
    setFocus("customer");
  }
  function saveCustomer(data: CustomerForm) {
    updateEntryState({ ...data, customerSaved: true });
  }
  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing && event.nativeEvent.keyCode !== 229) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  if (!ready || !ideaValid) return <main className="entry-discovery" data-theme={theme}><div className="entry-route-loading" role="status">در حال بازیابی پیش‌نویس…</div></main>;

  return <main className="entry-discovery" data-theme={theme} aria-labelledby="entryTitle">
    <DiscoveryHeader step="customer" />
    <form className="entry-step-form" id="customer-form" noValidate onSubmit={handleSubmit(saveCustomer)} aria-label="شناخت و ثبت مشتری">
      <section className="entry-question" aria-labelledby="entryTitle">
        <Image className="entry-mini-mark" src="/mark.svg" alt="" width={43} height={43} />
        <p className="entry-eyebrow">کمی بیشتر، کمی روشن‌تر</p>
        <h1 id="entryTitle">مشتری تو چه کسی است؟</h1>
        <p className="entry-description">برای چه کسی ارزش می‌سازی؟ از اولین مشتری‌های احتمالی‌ات بگو.</p>
        <div className="entry-choices" role="group" aria-label="نوع مشتری" aria-describedby={`entry-audience-help${errors.customer ? " entryError" : ""}`}>
          {audiences.map(({ value, label, icon: Icon }) => <button type="button" key={value} data-audience={value} className={`entry-choice${audience === value ? " selected" : ""}`} aria-pressed={audience === value} onClick={() => chooseAudience(value)}>
            <Icon aria-hidden="true" /><strong>{label}</strong><span className="entry-choice-check"><Check aria-hidden="true" /></span>
          </button>)}
        </div>
        <p id="entry-audience-help" className="entry-audience-help">نوع مشتری را انتخاب کن یا در کادر پایین درباره‌اش بنویس.</p>
        <div className="entry-fields">
          <div className="entry-field"><label htmlFor="entryMarket">بازار اولیه <small>اختیاری</small></label>
            <input id="entryMarket" maxLength={MAX_MARKET_LENGTH} placeholder="مثلاً تهران یا سراسر ایران" aria-invalid={Boolean(errors.market)} aria-describedby={errors.market ? "marketError" : undefined} {...register("market", { onChange: (event) => edit({ market: event.target.value }) })} />
            {errors.market && <p className="entry-error" id="marketError" role="alert">{errors.market.message}</p>}
          </div>
          <div className="entry-field"><label htmlFor="entryBudget">بودجهٔ آزمایش اولیه <small>اختیاری</small></label>
            <select id="entryBudget" aria-invalid={Boolean(errors.budget)} aria-describedby={errors.budget ? "budgetError" : undefined} {...register("budget", { onChange: (event) => edit({ budget: event.target.value }) })}>{budgetOptions.map((option) => <option key={option} value={option}>{option}</option>)}</select>
            {errors.budget && <p className="entry-error" id="budgetError" role="alert">{errors.budget.message}</p>}
          </div>
        </div>
      </section>

      <footer className="entry-footer">
        <div className="entry-composer">
          <label className="sr-only" htmlFor="entryAnswer">توضیح مشتری</label>
          <textarea id="entryAnswer" rows={2} maxLength={MAX_ANSWER_LENGTH} dir="rtl" placeholder="مثلاً خانم‌های شاغل ۲۵ تا ۳۵ سال در تهران که لباس ساده و باکیفیت می‌خواهند…"
            aria-invalid={Boolean(errors.customer)} aria-describedby={`entry-input-help entry-character-count${errors.customer ? " entryError" : ""}`}
            {...register("customer", { onChange: (event) => edit({ customer: event.target.value }) })} onKeyDown={onKeyDown} />
          <div className="entry-composer-actions">
            <div className="entry-composer-tools">
              <button type="button" className="entry-example-shortcut" aria-label="استفاده از یک نمونهٔ مشتری" onClick={useExample}><Plus aria-hidden="true" /></button>
              <span id="entry-input-help"><CornerDownLeft aria-hidden="true" /><span><bdi>Enter</bdi> برای ثبت <span className="entry-newline-help">· <bdi>Shift + Enter</bdi> خط جدید</span></span></span>
            </div>
            <button className="entry-send" type="submit" aria-label="ثبت مشتری"><ArrowLeft aria-hidden="true" /></button>
          </div>
        </div>
        {errors.customer && <p className="entry-error" id="entryError" role="alert">{errors.customer.message}</p>}
        <div className="entry-draft-meta">
          <p id="entry-save-status" role="status" aria-live="polite">{saved && <><Check aria-hidden="true" /> {persistent ? "مشتری‌هایت ذخیره شدند." : "مشتری‌هایت در این تب ثبت شدند."}</>}</p>
          <span id="entry-character-count" aria-label={`${persianNumber.format(customer.length)} از ۲۰۰۰ نویسه`}>{persianNumber.format(customer.length)} / ۲۰۰۰</span>
        </div>
        <div className="entry-footer-note">
          <span>{persistent ? "پیش‌نویس فقط در همین مرورگر ذخیره می‌شود." : "ذخیره در مرورگر در دسترس نیست؛ پیش‌نویس فقط در این تب نگه داشته می‌شود."}</span>
          <span>نمونهٔ مشتری نمایشی است؛ اطلاعات اولیه را خودت وارد کن.</span>
        </div>
      </footer>
    </form>
  </main>;
}
