// Browser smoke check with installed Chrome and Node's built-in WebSocket; no npm packages.
import { spawn } from "node:child_process";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import assert from "node:assert/strict";

const artifacts = await mkdtemp(path.join(tmpdir(), "nama-analyze-browser-"));
const profile = path.join(artifacts, "chrome-profile");
const chrome = spawn(process.env.CHROME_PATH ?? "C:/Program Files/Google/Chrome/Application/chrome.exe", [
  "--headless=new", "--disable-gpu", "--no-proxy-server", "--no-first-run", "--disable-extensions",
  "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank",
], { windowsHide: true, stdio: "ignore" });
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
let socket;
let sequence = 0;
const pending = new Map();
const pageErrors = [];
let interception = "hold";
let heldRequest;
function send(method, params = {}) {
  const id = ++sequence;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 15000);
    pending.set(id, { resolve: (value) => { clearTimeout(timer); resolve(value); }, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function waitFor(fn, label) {
  for (let index = 0; index < 100; index++) {
    const value = await fn();
    if (value) return value;
    await delay(150);
  }
  throw new Error(`Timed out: ${label}`);
}
async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error("Browser evaluation failed");
  return result.result.value;
}
const ready = "اتصال فرانت‌اند، بک‌اند و پایگاه داده برقرار است.";
async function waitStatus(text) {
  await waitFor(() => evaluate(`document.querySelector('[role="status"]')?.textContent.includes(${JSON.stringify(text)})`), text);
}
async function screenshot(name) {
  const result = await send("Page.captureScreenshot", { format: "png" });
  await writeFile(path.join(artifacts, name + ".png"), Buffer.from(result.data, "base64"));
}
try {
  const port = await waitFor(async () => {
    try { return (await readFile(path.join(profile, "DevToolsActivePort"), "utf8")).split("\n")[0]; } catch { return false; }
  }, "Chrome startup");
  const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  socket = new WebSocket(pages.find((page) => page.type === "page").webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.addEventListener("open", resolve, { once: true }); socket.addEventListener("error", reject, { once: true }); });
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
      const requestId = message.params.requestId;
      if (interception === "hold") heldRequest = requestId;
      else if (interception === "error") void send("Fetch.fulfillRequest", { requestId, responseCode: 503, responseHeaders: [{ name: "Content-Type", value: "application/json" }], body: Buffer.from('{"status":"unavailable","database":"unavailable"}').toString("base64") });
      else void send("Fetch.continueRequest", { requestId });
    }
  });
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send("Fetch.enable", { patterns: [{ urlPattern: "*/api/v1/health/*", requestStage: "Request" }] });
  await send("Page.navigate", { url: process.env.APP_ORIGIN ?? "http://127.0.0.1:3000/" });
    try { await waitFor(() => heldRequest, "client health request"); } catch (error) {
    console.log("Browser errors:", pageErrors);
    console.log("Browser state:", await evaluate("({ ready: document.readyState, status: document.querySelector('[role=status]')?.textContent, scripts: [...document.scripts].filter(s=>s.src).map(s=>s.src), resources: performance.getEntriesByType('resource').map(r=>({url:r.name, size:r.transferSize})) })"));
    await screenshot("failure");
    console.log("Failure screenshot:", artifacts);
    throw error;
  }
  assert.equal(await evaluate("document.querySelector('button').disabled"), true);
  console.log("PASS pending state and disabled retry while request is in flight");
  interception = "pass";
  await send("Fetch.continueRequest", { requestId: heldRequest });
  await waitStatus(ready);
  for (const [name, width, height] of [["desktop", 1440, 1000], ["mobile", 390, 844]]) {
    await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
    await delay(250);
    const layout = await evaluate("({ lang: document.documentElement.lang, dir: document.documentElement.dir, fits: document.documentElement.scrollWidth <= innerWidth, fontLoaded: document.fonts.status === 'loaded' })");
    assert.deepEqual(layout, { lang: "fa", dir: "rtl", fits: true, fontLoaded: true });
    await screenshot(name);
    console.log(`PASS ${name} ${width}px: client ready, Persian RTL, local font loaded, no horizontal overflow`);
  }
  interception = "error";
  await evaluate("document.querySelector('button').click()");
  await waitStatus("اتصال کامل برقرار نشد.");
  assert.equal(await evaluate("document.querySelector('button').disabled"), false);
  await screenshot("error");
  console.log("PASS HTTP 503 renders error and enables retry");
  interception = "pass";
  await send("Page.bringToFront");
  await evaluate("document.querySelector('button').focus()");
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13, text: "\r", unmodifiedText: "\r" });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
  await waitStatus(ready);
  assert.deepEqual(pageErrors, []);
  console.log("PASS keyboard Enter retry recovers; no uncaught browser exceptions");
  console.log("Screenshots:", artifacts);
} finally {
  if (socket?.readyState === WebSocket.OPEN) {
    await send("Browser.close").catch(() => {});
    socket.close();
  }
  chrome.kill();
}
