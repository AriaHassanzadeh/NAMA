"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Check, CornerDownLeft, Plus, RotateCcw, Shirt, Zap } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useMemo, type KeyboardEvent } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { getEntryOptions } from "@/lib/api/entry-options";
import { updateEntryState, useEntryPersistence, useEntryState } from "./entry-store";
import { DiscoveryHeader } from "./discovery-header";
import { ideaSchema, MAX_ANSWER_LENGTH } from "./draft-validation";
import "./idea-discovery.css";

type IdeaForm = z.infer<typeof ideaSchema>;
const persianNumber = new Intl.NumberFormat("fa-IR", { useGrouping: false });

export function IdeaDiscovery() {
  const router = useRouter();
  const draft = useEntryState();
  const persistent = useEntryPersistence();
  const theme = draft.theme === "light" ? "light" : "dark";
  const idea = typeof draft.idea === "string" ? draft.idea.slice(0, MAX_ANSWER_LENGTH) : "";
  const values = useMemo(() => ({ idea }), [idea]);
  const { register, handleSubmit, setValue, setFocus, clearErrors, formState: { errors } } = useForm<IdeaForm>({
    resolver: zodResolver(ideaSchema), values,
    resetOptions: { keepErrors: true },
  });
  const examples = useQuery({ queryKey: ["demo", "entry-options"], queryFn: ({ signal }) => getEntryOptions(signal) });
  const options = examples.data?.idea_examples ?? [];
  const saved = draft.ideaSaved === true && ideaSchema.safeParse({ idea }).success;

  function editIdea(value: string) {
    updateEntryState({ idea: value, ideaSaved: false, customerSaved: false, completed: false });
    clearErrors("idea");
  }
  function chooseExample(text: string) {
    const value = `می‌خواهم یک ${text} راه‌اندازی کنم.`;
    setValue("idea", value, { shouldDirty: true });
    editIdea(value);
    setFocus("idea");
  }
  function saveIdea(data: IdeaForm) {
    updateEntryState({ idea: data.idea, ideaSaved: true });
    router.push("/start/customer");
  }
  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing && event.nativeEvent.keyCode !== 229) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  return <main className="entry-discovery" data-theme={theme} aria-labelledby="entryTitle">
    <DiscoveryHeader step="idea" />

    <section className="entry-question" aria-labelledby="entryTitle">
      <Image className="entry-mini-mark" src="/mark.svg" alt="" width={43} height={43} />
      <p className="entry-eyebrow">کمی بیشتر، کمی روشن‌تر</p>
      <h1 id="entryTitle">اول، از ایده‌ات بگو.</h1>
      <p className="entry-description">قرار است چه چیزی بفروشی یا چه مسئله‌ای را حل کنی؟</p>
      <div className="entry-examples-region" aria-label="مثال‌های نمایشی ایده" aria-busy={examples.isPending}>
        {examples.isPending && <div className="entry-examples-loading" role="status">در حال دریافت مثال‌ها…</div>}
        {examples.isError && <div className="entry-examples-error" role="alert">
          <p>مثال‌ها دریافت نشدند. می‌توانی ایدهٔ خودت را بنویسی.</p>
          <button type="button" className="entry-examples-retry" onClick={() => void examples.refetch()} disabled={examples.isFetching}><RotateCcw aria-hidden="true" /> تلاش دوباره</button>
        </div>}
        {examples.isSuccess && options.length === 0 && <p className="entry-examples-empty" role="status">فعلاً مثالی در دسترس نیست؛ از ایدهٔ خودت بگو.</p>}
        {examples.isSuccess && options.length > 0 && <div className="entry-examples">{options.map((option) => <button key={option.id} type="button" onClick={() => chooseExample(option.text)}>
          {option.icon === "bolt" ? <Zap aria-hidden="true" /> : <Shirt aria-hidden="true" />}{option.text}
        </button>)}</div>}
      </div>
    </section>

    <footer className="entry-footer">
      <form noValidate onSubmit={handleSubmit(saveIdea)} aria-label="ثبت ایده و ادامه به شناخت مشتری">
        <div className="entry-composer">
          <label className="sr-only" htmlFor="entryAnswer">توضیح ایده</label>
          <textarea id="entryAnswer" rows={2} maxLength={MAX_ANSWER_LENGTH} dir="rtl"
            placeholder="مثلاً می‌خواهم یک برند پوشاک مینیمال برای خانم‌های شاغل راه بیندازم…"
            aria-invalid={Boolean(errors.idea)} aria-describedby={`entry-input-help entry-character-count${errors.idea ? " entryError" : ""}`}
            {...register("idea", { onChange: (event) => editIdea(event.target.value) })} onKeyDown={onKeyDown} />
          <div className="entry-composer-actions">
            <div className="entry-composer-tools">
              <button type="button" className="entry-example-shortcut" aria-label="استفاده از یک مثال ایده" disabled={options.length === 0} onClick={() => options[0] && chooseExample(options[0].text)}><Plus aria-hidden="true" /></button>
              <span id="entry-input-help"><CornerDownLeft aria-hidden="true" /><span><bdi>Enter</bdi> برای ادامه <span className="entry-newline-help">· <bdi>Shift + Enter</bdi> خط جدید</span></span></span>
            </div>
            <button className="entry-send" type="submit" aria-label="ادامه به شناخت مشتری"><ArrowLeft aria-hidden="true" /></button>
          </div>
        </div>
        {errors.idea && <p className="entry-error" id="entryError" role="alert">{errors.idea.message}</p>}
        <div className="entry-draft-meta">
          <p id="entry-save-status" role="status" aria-live="polite">{saved && <><Check aria-hidden="true" /> {persistent ? "ایده‌ات ذخیره شد." : "ایده‌ات در این تب ثبت شد."}</>}</p>
          <span id="entry-character-count" aria-label={`${persianNumber.format(idea.length)} از ۲۰۰۰ نویسه`}>{persianNumber.format(idea.length)} / ۲۰۰۰</span>
        </div>
      </form>
      <div className="entry-footer-note">
        <span>{persistent ? "پیش‌نویس فقط در همین مرورگر ذخیره می‌شود." : "ذخیره در مرورگر در دسترس نیست؛ پیش‌نویس فقط در این تب نگه داشته می‌شود."}</span>
        <span className="entry-demo-label"><ArrowLeft aria-hidden="true" /> مثال‌ها نمایشی‌اند؛ بدون اتصال به بازار واقعی</span>
      </div>
    </footer>
  </main>;
}
