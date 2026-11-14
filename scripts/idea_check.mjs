// Real Idea-page behavior checks using installed Chrome, without browser-test packages.
// Profiles and screenshots are written only to the OS temporary directory.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const artifacts = await mkdtemp(path.join(tmpdir(), "nama-analyze-idea-"));
const profile = path.join(artifacts, "chrome-profile");
const origin = new URL(process.env.APP_ORIGIN ?? "http://127.0.0.1:3000/").origin;
const store = "nama-analyze-entry-v1";
const chrome = spawn(process.env.CHROME_PATH ?? "C:/Program Files/Google/Chrome/Application/chrome.exe", [
  "--headless=new", "--disable-gpu", "--no-proxy-server", "--no-first-run", "--disable-extensions",
  "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank",
], { windowsHide: true, stdio: "ignore" });
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const pending = new Map();
const pageErrors = [];
let sequence = 0;
let socket;
let launchError;
let apiMode = "hold";
let heldRequests = [];
chrome.on("error", (error) => { launchError = error; });

function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 15000);
    pending.set(id, {
      resolve(value) { clearTimeout(timer); resolve(value); },
      reject(error) { clearTimeout(timer); reject(error); },
    });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text);
  return result.result.value;
}

async function waitFor(fn, label) {
  for (let index = 0; index < 240; index++) {
    if (launchError) throw launchError;
    const value = await fn();
    if (value) return value;
    await delay(125);
  }
  throw new Error(`Timed out: ${label}`);
}

async function screenshot(name) {
  // Full-page capture shifts RTL pages in this Chrome build; viewport capture
  // matches the measured on-screen layout without introducing a false offset.
  const result = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  await writeFile(path.join(artifacts, `${name}.png`), Buffer.from(result.data, "base64"));
}

async function waitForIdea() {
  await waitFor(() => evaluate("location.pathname.replace(/\\/$/, '') === '/start/idea' && !!document.querySelector('#entryAnswer')"), "Idea route and textarea");
  await evaluate("document.fonts.ready.then(() => true)");
  await delay(150);
}

async function waitForCustomer() {
  await waitFor(() => evaluate("location.pathname.replace(/\\/$/, '') === '/start/customer' && !!document.querySelector('#entryMarket')"), "Customer route and fields");
  await evaluate("document.fonts.ready.then(() => true)");
  await delay(150);
}

async function returnToIdea() {
  await evaluate("document.querySelector('.entry-back').click()");
  await waitForIdea();
}

async function fill(text) {
  await evaluate("document.querySelector('#entryAnswer').focus(); document.querySelector('#entryAnswer').select()");
  await send("Input.insertText", { text });
  await waitFor(() => evaluate(`document.querySelector('#entryAnswer').value === ${JSON.stringify(text)}`), "textarea input");
}

async function enter(modifiers = 0) {
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", modifiers, windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13, text: "\r", unmodifiedText: "\r" });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", modifiers, windowsVirtualKeyCode: 13 });
}

async function intercept(requestId) {
  if (apiMode === "hold") { heldRequests.push(requestId); return; }
  try {
    if (apiMode === "pass") { await send("Fetch.continueRequest", { requestId }); return; }
    const empty = apiMode === "empty";
    await send("Fetch.fulfillRequest", {
      requestId, responseCode: empty ? 200 : 503,
      responseHeaders: [{ name: "Content-Type", value: "application/json" }, { name: "Cache-Control", value: "no-store" }],
      body: Buffer.from(JSON.stringify(empty ? { source_kind: "demo", label: "داده‌های نمایشی", idea_examples: [] } : { detail: "Temporarily unavailable" })).toString("base64"),
    });
  } catch (error) {
    // React Strict Mode may abort its first development fetch while it is held.
    if (!error.message.includes("Invalid InterceptionId")) throw error;
  }
}

try {
  const port = await waitFor(async () => {
    try { return (await readFile(path.join(profile, "DevToolsActivePort"), "utf8")).split("\n")[0]; }
    catch { return false; }
  }, "Chrome startup");
  const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  socket = new WebSocket(pages.find((page) => page.type === "page").webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });
  socket.addEventListener("message", ({ data }) => {
    const message = JSON.parse(data);
    if (message.id) {
      const callback = pending.get(message.id);
      if (!callback) return;
      pending.delete(message.id);
      if (message.error) callback.reject(new Error(message.error.message)); else callback.resolve(message.result);
    } else if (message.method === "Runtime.exceptionThrown") {
      pageErrors.push(message.params.exceptionDetails.exception?.description ?? message.params.exceptionDetails.text);
    } else if (message.method === "Fetch.requestPaused") {
      void intercept(message.params.requestId).catch((error) => pageErrors.push(error.message));
    }
  });
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Page.bringToFront");
  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send("Fetch.enable", { patterns: [{ urlPattern: "*/api/v1/demo/entry-options/*", requestStage: "Request" }] });
  await send("Page.navigate", { url: origin + "/" });
  await waitFor(() => evaluate("document.querySelectorAll('.solar-planet').length === 10"), "landing");
  await waitFor(() => evaluate("document.querySelector('.solar-motion-toggle')?.disabled === false"), "hydrated landing controls");
  await evaluate("document.querySelector('.solar-planet').click()");
  await waitForIdea();
  await waitFor(() => heldRequests.length > 0, "same-origin example API request");
  await waitFor(() => evaluate("!!document.querySelector('.entry-examples-loading')"), "example loading state");
  assert.equal(await evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)})).source`), "instagram");
  assert.equal(await evaluate("document.querySelector('.entry-discovery').dataset.theme"), "dark");
  assert.equal(await evaluate("document.querySelectorAll('.entry-progress button:disabled').length"), 2);
  assert.equal(await evaluate("document.querySelector('#entryAnswer').maxLength"), 2000);
  assert.equal(await evaluate("!!document.querySelector('label[for=entryAnswer]')"), true);
  await fill("ایدهٔ من برای یک فروشگاه کوچک");
  await waitFor(() => evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)})).idea === 'ایدهٔ من برای یک فروشگاه کوچک'`), "draft saved while examples load");
  apiMode = "pass";
  for (const requestId of heldRequests.splice(0)) await intercept(requestId);
  await waitFor(() => evaluate("document.querySelectorAll('.entry-examples button').length === 3"), "real mock examples");
  console.log("PASS landing→Idea preserves source; mock API loading leaves free-text input usable");

  await evaluate("document.querySelector('.entry-examples button').click()");
  const example = "می‌خواهم یک پوشاک مینیمال زنانه راه‌اندازی کنم.";
  await waitFor(() => evaluate(`document.querySelector('#entryAnswer').value === ${JSON.stringify(example)}`), "example selection");
  assert.equal(await evaluate("document.activeElement.id"), "entryAnswer");
  await evaluate("document.querySelector('.entry-example-shortcut').click()");
  assert.equal(await evaluate("document.activeElement.id"), "entryAnswer");
  console.log("PASS API example chips and example shortcut populate the composer and focus it");

  await fill("   ");
  await enter();
  await waitFor(() => evaluate("document.querySelector('#entryError')?.textContent.includes('۵')"), "empty-idea validation");
  assert.equal(await evaluate("document.querySelector('#entryAnswer').getAttribute('aria-invalid')"), "true");
  await fill("کوت");
  await evaluate("document.querySelector('.entry-send').click()");
  await waitFor(() => evaluate("document.querySelector('#entryError')?.textContent.includes('۵')"), "short-idea validation");
  await fill("ایدهٔ آزمایشی من");
  await evaluate("document.querySelector('#entryAnswer').setSelectionRange(document.querySelector('#entryAnswer').value.length, document.querySelector('#entryAnswer').value.length)");
  await enter(8);
  assert.equal(await evaluate("document.querySelector('#entryAnswer').value.endsWith('\\n')"), true, "Shift+Enter inserts a newline");
  assert.equal(await evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)})).ideaSaved === true`), false);
  await evaluate("document.querySelector('#entryAnswer').dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', bubbles: true, cancelable: true, isComposing: true }))");
  await delay(100);
  assert.equal(await evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)})).ideaSaved === true`), false, "IME Enter must not submit");
  await enter();
  await waitForCustomer();
  assert.equal(await evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)})).ideaSaved`), true);
  await returnToIdea();
  await waitFor(() => evaluate(`document.querySelector('#entryAnswer').value === JSON.parse(localStorage.getItem(${JSON.stringify(store)})).idea`), "normalized saved value displayed");
  assert.equal(await evaluate("location.pathname.replace(/\\/$/, '')"), "/start/idea");
  assert.equal(await evaluate("location.search"), "");
  const savedIdea = await evaluate("document.querySelector('#entryAnswer').value");
  assert.equal(await evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)})).ideaSaved`), true);
  console.log("PASS trimmed minimum length, Enter continues to Customer, Shift+Enter newline and IME guard; back restores Idea without answer URLs");

  await evaluate("document.querySelector('.theme-toggle').click()");
  await waitFor(() => evaluate("document.querySelector('.entry-discovery').dataset.theme === 'light'"), "light theme");
  await send("Page.reload");
  await waitForIdea();
  await waitFor(() => evaluate(`document.querySelector('#entryAnswer').value === ${JSON.stringify(savedIdea)}`), "draft reload restoration");
  assert.equal(await evaluate("document.querySelector('.entry-discovery').dataset.theme"), "light");
  await evaluate("document.querySelector('.entry-back').click()");
  await waitFor(() => evaluate("!!document.querySelector('.solar-portal')"), "back to landing");
  assert.equal(await evaluate("document.querySelector('.solar-portal').dataset.theme"), "light");
  await evaluate("history.back()");
  await waitForIdea();
  await waitFor(() => evaluate(`document.querySelector('#entryAnswer').value === ${JSON.stringify(savedIdea)}`), "browser back draft");
  await evaluate("history.forward()");
  await waitFor(() => evaluate("!!document.querySelector('.solar-portal')"), "browser forward landing");
  await evaluate("document.querySelector('.solar-core').click()");
  await waitForIdea();
  assert.equal(await evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)})).source`), "nama");
  await fill("ویرایش تازهٔ ایده برای بررسی بازار");
  await waitFor(() => evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)})).ideaSaved === false`), "edit invalidates saved state");
  assert.equal(await evaluate("document.querySelector('#entry-save-status')?.textContent.includes('ایده‌ات ذخیره شد.') ?? false"), false);
  console.log("PASS typing/reload/back/forward preserves draft and shared theme; editing invalidates prior saved state");

  for (const theme of ["light", "dark"]) {
    if (await evaluate("document.querySelector('.entry-discovery').dataset.theme") !== theme) {
      await evaluate("document.querySelector('.theme-toggle').click()");
    }
    for (const [name, width, height] of [["desktop", 1440, 1000], ["desktop-1280", 1280, 900], ["tablet", 768, 1024], ["mobile", 390, 844], ["landscape", 844, 390]]) {
      await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
      await evaluate("window.scrollTo(0, 0)");
      await delay(200);
      const layout = await evaluate(`(() => {
        const header = document.querySelector('.entry-header').getBoundingClientRect();
        const question = document.querySelector('.entry-question').getBoundingClientRect();
        const composer = document.querySelector('.entry-composer').getBoundingClientRect();
        const footer = document.querySelector('.entry-footer').getBoundingClientRect();
        const main = document.querySelector('.entry-discovery').getBoundingClientRect();
        const root = document.documentElement.getBoundingClientRect();
        const center = root.left + document.documentElement.clientWidth / 2;
        return { lang: document.documentElement.lang, dir: document.documentElement.dir,
          fits: document.documentElement.scrollWidth <= innerWidth,
          fontLoaded: document.fonts.status === 'loaded',
          mainAligned: Math.abs(main.left - root.left) < 1 && Math.abs(main.right - root.right) < 1 && scrollX === 0,
          contentCentered: Math.abs((question.left + question.right) / 2 - center) < 1
            && Math.abs((composer.left + composer.right) / 2 - center) < 1,
          sectionsSeparate: header.bottom <= question.top + 1 && question.bottom <= composer.top + 1,
          composerInPage: composer.left >= 0 && composer.right <= innerWidth && footer.bottom <= document.documentElement.scrollHeight + 1 };
      })()`);
      if (!layout.mainAligned || !layout.contentCentered) console.log("Layout measurements:", await evaluate("({innerWidth,scrollX,clientWidth:document.documentElement.clientWidth,clientLeft:document.documentElement.clientLeft,html:document.documentElement.getBoundingClientRect().toJSON(),main:document.querySelector('main').getBoundingClientRect().toJSON(),question:document.querySelector('.entry-question').getBoundingClientRect().toJSON(),composer:document.querySelector('.entry-composer').getBoundingClientRect().toJSON()})"));
      assert.deepEqual(layout, { lang: "fa", dir: "rtl", fits: true, fontLoaded: true, mainAligned: true, contentCentered: true, sectionsSeparate: true, composerInPage: true }, `${theme} ${name}`);
      if (name === "desktop" || name === "mobile") await screenshot(`${theme}-${name}`);
      console.log(`PASS ${theme} ${width}x${height}: RTL/fonts, no horizontal overflow or form overlap`);
    }
  }
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  const reduced = await evaluate("document.querySelector('.entry-question').getAnimations({ subtree: true }).every(animation => animation.playState !== 'running')");
  assert.equal(reduced, true, "reduced motion suppresses question reveal");

  apiMode = "error";
  await send("Page.reload");
  await waitForIdea();
  await waitFor(() => evaluate("!!document.querySelector('.entry-examples-error')"), "API error state");
  await fill("ورودی آزاد هنگام قطع مثال‌ها هم کار می‌کند");
  await enter();
  await waitForCustomer();
  await returnToIdea();
  await waitFor(() => evaluate("!!document.querySelector('.entry-examples-error')"), "example failure after returning from Customer");
  await screenshot("api-error");
  apiMode = "pass";
  await evaluate("document.querySelector('.entry-examples-retry').click()");
  await waitFor(() => evaluate("document.querySelectorAll('.entry-examples button').length === 3"), "retry succeeds");
  console.log("PASS API failure displays retry while writing/saving remains usable; retry restores examples");

  apiMode = "empty";
  await send("Page.reload");
  await waitForIdea();
  await waitFor(() => evaluate("!!document.querySelector('.entry-examples-empty')"), "empty examples");
  assert.equal(await evaluate("document.querySelector('#entryAnswer').disabled"), false);
  console.log("PASS empty example response has an explicit state and leaves the composer enabled");

  apiMode = "pass";
  await evaluate(`localStorage.setItem(${JSON.stringify(store)}, '{broken json')`);
  await send("Page.reload");
  await waitForIdea();
  assert.equal(await evaluate("document.querySelector('#entryAnswer').value"), "");
  await fill("بازیابی پس از تنظیمات نامعتبر");
  await waitFor(() => evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)})).idea === 'بازیابی پس از تنظیمات نامعتبر'`), "malformed-storage recovery");
  const injected = await send("Page.addScriptToEvaluateOnNewDocument", { source: "Object.defineProperty(Storage.prototype, 'getItem', { value() { throw new DOMException('Storage blocked', 'SecurityError'); } }); Object.defineProperty(Storage.prototype, 'setItem', { value() { throw new DOMException('Storage blocked', 'SecurityError'); } });" });
  await send("Page.reload");
  await waitForIdea();
  await fill("ایده با ذخیره‌سازی مسدود مرورگر");
  await enter();
  await waitForCustomer();
  await returnToIdea();
  await waitFor(() => evaluate("document.querySelector('#entryAnswer').value === 'ایده با ذخیره‌سازی مسدود مرورگر'"), "in-memory Idea survives Customer navigation");
  assert.equal(await evaluate("document.querySelector('.entry-footer-note').textContent.includes('فقط در این تب')"), true, "memory-only persistence is described honestly");
  await evaluate("document.querySelector('.entry-back').click()");
  await waitFor(() => evaluate("!!document.querySelector('.solar-portal')"), "memory-mode return to landing");
  await evaluate("document.querySelector('.solar-core').click()");
  await waitForIdea();
  assert.equal(await evaluate("document.querySelector('#entryAnswer').value"), "ایده با ذخیره‌سازی مسدود مرورگر");
  await send("Page.removeScriptToEvaluateOnNewDocument", { identifier: injected.identifier });
  assert.deepEqual(pageErrors, [], "no uncaught browser exceptions");
  console.log("PASS malformed storage recovers; denied storage retains the draft in memory during navigation; no browser exceptions");
  if (process.env.REFERENCE_ORIGIN) {
    const referenceOrigin = new URL(process.env.REFERENCE_ORIGIN).origin;
    await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });
    await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
    await send("Page.navigate", { url: referenceOrigin + "/#/start/idea" });
    await waitFor(() => evaluate("!!document.querySelector('.entry-discovery') && !!document.querySelector('#entryAnswer')"), "read-only reference Idea page");
    await evaluate("document.fonts.ready.then(() => true)");
    await delay(400);
    await screenshot("reference-dark-desktop");
    await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: false });
    await delay(200);
    await screenshot("reference-dark-mobile");
    console.log("Captured read-only reference Idea at desktop/mobile for visual comparison");
  }
  console.log("Screenshots:", artifacts);
} catch (error) {
  if (socket?.readyState === WebSocket.OPEN) {
    console.error("Browser state:", await evaluate("({ url: location.href, ready: document.readyState, theme: document.querySelector('.entry-discovery')?.dataset.theme, answer: document.querySelector('#entryAnswer')?.value, errors: [...document.querySelectorAll('[role=alert]')].map(node => node.textContent), statuses: [...document.querySelectorAll('[role=status]')].map(node => node.textContent) })").catch(() => null));
    await screenshot("failure").catch(() => {});
  }
  console.error("Browser exceptions:", pageErrors);
  console.error("Artifacts:", artifacts);
  throw error;
} finally {
  if (socket?.readyState === WebSocket.OPEN) {
    await send("Browser.close").catch(() => {});
    socket.close();
  }
  chrome.kill();
}
