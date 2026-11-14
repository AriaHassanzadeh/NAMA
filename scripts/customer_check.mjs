// Real Customer question behavior using installed Chrome/CDP; no test packages.
// Browser profiles and screenshots stay in the OS temporary directory.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const artifacts = await mkdtemp(path.join(tmpdir(), "nama-analyze-customer-"));
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

async function waitForIdea() {
  await waitFor(() => evaluate("location.pathname.replace(/\\/$/, '') === '/start/idea' && !!document.querySelector('#entryAnswer')"), "Idea route");
  await waitFor(() => evaluate("document.querySelectorAll('.entry-examples button').length === 3 || !!document.querySelector('.entry-examples-error')"), "mounted Idea form");
  await evaluate("document.fonts.ready.then(() => true)");
}

async function waitForCustomer() {
  await waitFor(() => evaluate("location.pathname.replace(/\\/$/, '') === '/start/customer' && !!document.querySelector('#entryMarket') && document.querySelectorAll('.entry-choice').length === 3"), "Customer route and fields");
  await evaluate("document.fonts.ready.then(() => true)");
  await delay(150);
}

async function fill(selector, text) {
  await evaluate(`document.querySelector(${JSON.stringify(selector)}).focus(); document.querySelector(${JSON.stringify(selector)}).select()`);
  await send("Input.insertText", { text });
  await waitFor(() => evaluate(`document.querySelector(${JSON.stringify(selector)}).value === ${JSON.stringify(text)}`), "field input");
}

async function enter(modifiers = 0) {
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", modifiers, windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13, text: "\r", unmodifiedText: "\r" });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", modifiers, windowsVirtualKeyCode: 13 });
}

async function screenshot(name) {
  const result = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  await writeFile(path.join(artifacts, `${name}.png`), Buffer.from(result.data, "base64"));
}

const state = (field) => evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)}))?.[${JSON.stringify(field)}]`);
const clickAudience = (value) => evaluate(`document.querySelector('.entry-choice[data-audience=${value}]').click()`);
async function waitSaved() {
  await waitFor(() => evaluate("!!document.querySelector('#entry-save-status')?.textContent.trim()"), "Customer saved acknowledgement");
}

async function changeIdeaInAnotherTab(port) {
  const tab = await (await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(origin + "/")}`, { method: "PUT" })).json();
  const other = new WebSocket(tab.webSocketDebuggerUrl);
  let id = 0;
  await new Promise((resolve, reject) => {
    other.addEventListener("open", resolve, { once: true });
    other.addEventListener("error", reject, { once: true });
  });
  const run = (expression) => new Promise((resolve, reject) => {
    const requestId = ++id;
    const timer = setTimeout(() => { other.removeEventListener("message", receive); reject(new Error("Second-tab CDP timeout")); }, 15000);
    function receive({ data }) {
      const message = JSON.parse(data);
      if (message.id !== requestId) return;
      clearTimeout(timer);
      other.removeEventListener("message", receive);
      if (message.error || message.result?.exceptionDetails) reject(new Error("Second-tab draft update failed"));
      else resolve(message.result.result.value);
    }
    other.addEventListener("message", receive);
    other.send(JSON.stringify({ id: requestId, method: "Runtime.evaluate", params: { expression, returnByValue: true } }));
  });
  try {
    await waitFor(() => run(`location.origin === ${JSON.stringify(origin)}`), "same-origin second tab");
    await run(`localStorage.setItem(${JSON.stringify(store)}, JSON.stringify({...JSON.parse(localStorage.getItem(${JSON.stringify(store)})),idea:''}))`);
  } finally {
    other.close();
    await fetch(`http://127.0.0.1:${port}/json/close/${tab.id}`);
    await send("Page.bringToFront");
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
    }
  });
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Page.bringToFront");
  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: origin + "/start/customer" });
  await waitForIdea();
  assert.equal(await evaluate("!!document.querySelector('#entryMarket')"), false);
  console.log("PASS direct Customer access without an Idea returns to the first incomplete step");

  const idea = "برند پوشاک ساده برای مشتری‌های روزمره";
  await fill("#entryAnswer", idea);
  await enter();
  await waitForCustomer();
  assert.equal(await state("idea"), idea);
  assert.equal(await state("ideaSaved"), true);
  assert.equal(await evaluate("document.querySelectorAll('.entry-progress button:disabled').length"), 1);
  assert.equal(await evaluate("document.querySelector('#entryAnswer').maxLength"), 2000);
  assert.equal(await evaluate("document.querySelector('#entryMarket').maxLength"), 100);
  assert.equal(await evaluate("['entryAnswer','entryMarket','entryBudget'].every(id => !!document.querySelector('label[for='+id+']'))"), true);
  assert.equal(await evaluate("document.querySelectorAll('.entry-choice[aria-pressed=false]').length"), 3);
  await evaluate(`localStorage.setItem(${JSON.stringify(store)}, JSON.stringify({...JSON.parse(localStorage.getItem(${JSON.stringify(store)})),workspaceName:'نام دستی فضای من'}))`);
  console.log("PASS valid Idea continues to Customer with labels, limits and only Goal unavailable");

  await evaluate("document.querySelector('.entry-example-shortcut').click()");
  await waitFor(() => evaluate("document.querySelector('#entryAnswer').value.length > 3 && document.activeElement.id === 'entryAnswer'"), "Customer example populates and focuses text");
  await fill("#entryAnswer", "");
  await evaluate("document.querySelector('.entry-send').click()");
  await waitFor(() => evaluate("!!document.querySelector('#entryError')?.textContent.trim()"), "empty Customer validation");
  await fill("#entryAnswer", "کم");
  await enter();
  await waitFor(() => evaluate("!!document.querySelector('#entryError')?.textContent.trim()"), "short Customer validation");
  await fill("#entryAnswer", "");
  await clickAudience("consumer");
  await evaluate("document.querySelector('.entry-send').click()");
  await waitSaved();
  assert.equal(await state("customerSaved"), true);
  assert.equal(await state("audience"), "consumer");
  assert.equal(await evaluate("location.pathname.replace(/\\/$/, '')"), "/start/customer");
  assert.equal(await evaluate("location.search"), "");
  console.log("PASS audience alone is valid; empty/short text without audience is rejected; save stays on the review page");

  for (const audience of ["business", "both", "consumer"]) {
    if (audience === "business") {
      await evaluate("document.querySelector('.entry-choice[data-audience=business]').focus()");
      await enter();
    } else await clickAudience(audience);
    await waitFor(() => evaluate(`document.querySelector('.entry-choice[data-audience=${audience}]').getAttribute('aria-pressed') === 'true'`), "selected audience");
    assert.equal(await evaluate("document.querySelectorAll('.entry-choice[aria-pressed=true]').length"), 1);
    assert.equal(await state("audience"), audience);
  }
  await clickAudience("consumer");
  assert.equal(await evaluate("document.querySelectorAll('.entry-choice[aria-pressed=true]').length"), 0);
  assert.equal(await state("audience"), "");
  const customer = "خانم‌های شاغل که پوشاک ساده و باکیفیت می‌خواهند";
  await fill("#entryAnswer", customer);
  await evaluate("document.querySelector('#entryAnswer').setSelectionRange(document.querySelector('#entryAnswer').value.length, document.querySelector('#entryAnswer').value.length)");
  await enter(8);
  assert.equal(await evaluate("document.querySelector('#entryAnswer').value.endsWith('\\n')"), true);
  await evaluate("document.querySelector('#entryAnswer').dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',code:'Enter',bubbles:true,cancelable:true,isComposing:true}))");
  await delay(100);
  assert.equal(await state("customerSaved"), false);
  await enter();
  await waitSaved();
  await waitFor(() => evaluate(`document.querySelector('#entryAnswer').value === ${JSON.stringify(customer)}`), "normalized Customer text");
  assert.equal(await state("customer"), customer);
  console.log("PASS exclusive/toggleable choices, free-text alternative, Enter/Shift+Enter and IME-safe input");

  await fill("#entryMarket", "تهران و سراسر ایران");
  const budget = await evaluate("(() => {const select=document.querySelector('#entryBudget');select.value=select.options[1].value;select.dispatchEvent(new Event('change',{bubbles:true}));return select.value;})()");
  await waitFor(() => state("budget").then((value) => value === budget), "budget draft saved");
  assert.equal(await state("customerSaved"), false);
  assert.equal(await evaluate("document.querySelector('#entry-save-status').textContent.trim()"), "");
  await clickAudience("both");
  await evaluate("document.querySelector('.entry-send').click()");
  await waitSaved();
  await evaluate("document.querySelector('.theme-toggle').click()");
  await waitFor(() => evaluate("document.querySelector('.entry-discovery').dataset.theme === 'light'"), "light theme");
  await send("Page.reload");
  await waitForCustomer();
  await waitFor(() => evaluate(`document.querySelector('#entryAnswer').value === ${JSON.stringify(customer)}`), "Customer reload restoration");
  assert.equal(await evaluate("document.querySelector('#entryMarket').value"), "تهران و سراسر ایران");
  assert.equal(await evaluate("document.querySelector('#entryBudget').value"), budget);
  assert.equal(await evaluate("document.querySelector('.entry-choice[data-audience=both]').getAttribute('aria-pressed')"), "true");
  assert.equal(await evaluate("document.querySelector('.entry-discovery').dataset.theme"), "light");

  await evaluate("document.querySelector('.entry-back').click()");
  await waitForIdea();
  assert.equal(await evaluate("document.querySelector('#entryAnswer').value"), idea);
  await evaluate("history.back()");
  await waitForCustomer();
  assert.equal(await evaluate("document.querySelector('#entryAnswer').value"), customer);
  await evaluate("history.forward()");
  await waitForIdea();
  await fill("#entryAnswer", "ایدهٔ ویرایش‌شده برای همان برند پوشاک");
  await enter();
  await waitForCustomer();
  assert.equal(await evaluate("document.querySelector('#entryAnswer').value"), customer);
  assert.equal(await evaluate("document.querySelector('#entryMarket').value"), "تهران و سراسر ایران");
  await evaluate("document.querySelector('.entry-progress [data-step=idea]').click()");
  await waitForIdea();
  await evaluate("document.querySelector('#entryAnswer').focus()");
  await enter();
  await waitForCustomer();
  assert.equal(await state("workspaceName"), "نام دستی فضای من");
  console.log("PASS optional market/budget, saved-state invalidation, reload/back/forward and progress navigation preserve answers/theme");

  for (const theme of ["light", "dark"]) {
    if (await evaluate("document.querySelector('.entry-discovery').dataset.theme") !== theme) await evaluate("document.querySelector('.theme-toggle').click()");
    for (const [name, width, height] of [["desktop",1440,1000],["desktop-1280",1280,900],["tablet",768,1024],["mobile",390,844],["landscape",844,390]]) {
      await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
      await evaluate("window.scrollTo(0,0)");
      await delay(200);
      const layout = await evaluate(`(() => {
        const root=document.documentElement.getBoundingClientRect();
        const main=document.querySelector('.entry-discovery').getBoundingClientRect();
        const header=document.querySelector('.entry-header').getBoundingClientRect();
        const question=document.querySelector('.entry-question').getBoundingClientRect();
        const composer=document.querySelector('.entry-composer').getBoundingClientRect();
        const center=root.left+document.documentElement.clientWidth/2;
        return {lang:document.documentElement.lang,dir:document.documentElement.dir,
          fits:document.documentElement.scrollWidth<=innerWidth,
          aligned:Math.abs(main.left-root.left)<1&&Math.abs(main.right-root.right)<1&&scrollX===0,
          centered:Math.abs((question.left+question.right)/2-center)<1&&Math.abs((composer.left+composer.right)/2-center)<1,
          separate:header.bottom<=question.top+1&&question.bottom<=composer.top+1,
          fieldsFit:['entryAnswer','entryMarket','entryBudget'].every(id=>{const r=document.querySelector('#'+id).getBoundingClientRect();return r.left>=root.left&&r.right<=root.right}),
          fonts:document.fonts.status==='loaded'};
      })()`);
      assert.deepEqual(layout, {lang:"fa",dir:"rtl",fits:true,aligned:true,centered:true,separate:true,fieldsFit:true,fonts:true}, `${theme} ${name}`);
      if (name === "desktop" || name === "mobile") await screenshot(`${theme}-${name}`);
      if (name === "mobile") {
        await evaluate("window.scrollTo(0,document.documentElement.scrollHeight)");
        await delay(150);
        await screenshot(`${theme}-mobile-bottom`);
      }
      console.log(`PASS ${theme} ${width}x${height}: RTL/fonts, centered content and no horizontal overflow or form overlap`);
    }
  }
  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  assert.equal(await evaluate("document.querySelector('.entry-question').getAnimations({subtree:true}).every(animation=>animation.playState!=='running')"), true);

  await changeIdeaInAnotherTab(port);
  await waitForIdea();
  assert.equal(await evaluate("document.querySelector('#entryAnswer').value"), "");
  assert.equal(await state("customer"), customer);
  await evaluate(`localStorage.setItem(${JSON.stringify(store)}, '{broken json')`);
  await send("Page.navigate", { url: origin + "/start/customer" });
  await waitForIdea();
  assert.equal(await evaluate("!!document.querySelector('#entryMarket')"), false);
  console.log("PASS live Idea invalidation from another tab and malformed storage return to Idea without erasing Customer answers");

  const injected = await send("Page.addScriptToEvaluateOnNewDocument", { source: "Object.defineProperty(Storage.prototype,'getItem',{value(){throw new DOMException('Storage blocked','SecurityError')}});Object.defineProperty(Storage.prototype,'setItem',{value(){throw new DOMException('Storage blocked','SecurityError')}});" });
  await send("Page.reload");
  await waitForIdea();
  await fill("#entryAnswer", "ایدهٔ آزمایشی با ذخیره‌سازی مسدود");
  await enter();
  await waitForCustomer();
  const memoryCustomer = "مشتری‌های آزمایشی در همین تب";
  await fill("#entryAnswer", memoryCustomer);
  await clickAudience("business");
  await evaluate("document.querySelector('.entry-send').click()");
  await waitSaved();
  assert.equal(await evaluate("document.querySelector('.entry-footer-note').textContent.includes('فقط در این تب')"), true);
  await evaluate("document.querySelector('.entry-back').click()");
  await waitForIdea();
  await evaluate("document.querySelector('#entryAnswer').focus()");
  await enter();
  await waitForCustomer();
  assert.equal(await evaluate("document.querySelector('#entryAnswer').value"), memoryCustomer);
  assert.equal(await evaluate("document.querySelector('.entry-choice[data-audience=business]').getAttribute('aria-pressed')"), "true");
  await send("Page.removeScriptToEvaluateOnNewDocument", { identifier: injected.identifier });
  assert.deepEqual(pageErrors, [], "no uncaught browser exceptions");
  console.log("PASS blocked storage retains Idea and Customer across client navigation; no browser exceptions");

  if (process.env.REFERENCE_ORIGIN) {
    const referenceOrigin = new URL(process.env.REFERENCE_ORIGIN).origin;
    await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });
    await send("Emulation.setDeviceMetricsOverride", { width:1440,height:1000,deviceScaleFactor:1,mobile:false });
    await send("Page.navigate", { url: referenceOrigin + "/#/start/idea" });
    await waitFor(() => evaluate("!!document.querySelector('.entry-discovery') && !!document.querySelector('#entryAnswer')"), "read-only reference Idea");
    await fill("#entryAnswer", "ایدهٔ مرجع برای مشاهدهٔ مشتری‌ها");
    await enter();
    await waitFor(() => evaluate("!!document.querySelector('#entryMarket')"), "read-only reference Customer");
    await evaluate("document.fonts.ready.then(()=>true)");
    await delay(400);
    await screenshot("reference-dark-desktop");
    await send("Emulation.setDeviceMetricsOverride", { width:390,height:844,deviceScaleFactor:1,mobile:false });
    await delay(200);
    await screenshot("reference-dark-mobile");
    await evaluate("window.scrollTo(0,document.documentElement.scrollHeight)");
    await delay(150);
    await screenshot("reference-dark-mobile-bottom");
    console.log("Captured read-only reference Customer at desktop/mobile for visual comparison");
  }
  console.log("Screenshots:", artifacts);
} catch (error) {
  if (socket?.readyState === WebSocket.OPEN) {
    console.error("Browser state:", await evaluate("({url:location.href,ready:document.readyState,theme:document.querySelector('.entry-discovery')?.dataset.theme,errors:[...document.querySelectorAll('[role=alert]')].map(node=>node.textContent),statuses:[...document.querySelectorAll('[role=status]')].map(node=>node.textContent)})").catch(() => null));
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
