// Solar entrance checks using installed Chrome and Node's built-in WebSocket.
// Browser profiles and screenshots stay in the OS temp directory.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const artifacts = await mkdtemp(path.join(tmpdir(), "nama-analyze-landing-"));
const profile = path.join(artifacts, "chrome-profile");
const origin = process.env.APP_ORIGIN ?? "http://127.0.0.1:3000/";
const store = "nama-analyze-entry-v1";
const chrome = spawn(process.env.CHROME_PATH ?? "C:/Program Files/Google/Chrome/Application/chrome.exe", [
  "--headless=new", "--disable-gpu", "--no-proxy-server", "--no-first-run", "--disable-extensions",
  "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank",
], { windowsHide: true, stdio: "ignore" });

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const pending = new Map();
const pageErrors = [];
const networkErrors = [];
let sequence = 0;
let socket;
let launchError;
chrome.on("error", (error) => { launchError = error; });

function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`CDP timeout: ${method}`));
    }, 15000);
    pending.set(id, {
      resolve(value) { clearTimeout(timer); resolve(value); },
      reject(error) { clearTimeout(timer); reject(error); },
    });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text);
  }
  return result.result.value;
}

async function waitFor(fn, label) {
  for (let index = 0; index < 120; index++) {
    if (launchError) throw launchError;
    const value = await fn();
    if (value) return value;
    await delay(125);
  }
  throw new Error(`Timed out: ${label}`);
}

async function screenshot(name) {
  const result = await send("Page.captureScreenshot", { format: "png" });
  await writeFile(path.join(artifacts, `${name}.png`), Buffer.from(result.data, "base64"));
}

async function waitForLanding() {
  await waitFor(() => evaluate("document.readyState === 'complete' && document.querySelectorAll('.solar-planet').length === 10"), "solar entrance");
  await evaluate("document.fonts.ready.then(() => true)");
  await delay(300);
}

async function press(key, code, keyCode) {
  await send("Input.dispatchKeyEvent", { type: "keyDown", key, code, windowsVirtualKeyCode: keyCode, nativeVirtualKeyCode: keyCode, ...(key === "Enter" ? { text: "\r", unmodifiedText: "\r" } : {}) });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key, code, windowsVirtualKeyCode: keyCode });
}

async function clearPlanetInteraction() {
  await evaluate("document.activeElement?.blur()");
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: 2, y: 2 });
}

async function waitForOrbitState(state) {
  await waitFor(() => evaluate(`(() => {
    const nodes = [...document.querySelectorAll('.solar-rotor, .solar-counter')];
    return nodes.length === 20 && nodes.every(node => getComputedStyle(node).animationPlayState === ${JSON.stringify(state)});
  })()`), `all orbits ${state}`);
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
      if (message.error) callback.reject(new Error(message.error.message));
      else callback.resolve(message.result);
    } else if (message.method === "Runtime.exceptionThrown") {
      pageErrors.push(message.params.exceptionDetails.exception?.description ?? message.params.exceptionDetails.text);
    } else if (message.method === "Log.entryAdded" && message.params.entry.level === "error") {
      networkErrors.push(message.params.entry.text);
    }
  });
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Log.enable");
  await send("Page.bringToFront");
  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: origin });
  await waitForLanding();
  assert.equal(await evaluate("document.querySelector('.solar-portal').dataset.theme"), "dark");
  assert.equal(await evaluate("document.querySelectorAll('.solar-planet[aria-label]').length"), 10);
  await delay(1000);

  for (const [name, width, height] of [
    ["desktop", 1440, 1000], ["desktop-1280", 1280, 900], ["tablet", 768, 1024],
    ["mobile", 390, 844], ["landscape", 844, 390],
  ]) {
    await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
    await delay(200);
    const layout = await evaluate(`({
      lang: document.documentElement.lang,
      dir: document.documentElement.dir,
      fits: document.documentElement.scrollWidth <= innerWidth,
      heightFits: document.documentElement.scrollHeight <= innerHeight,
      fontLoaded: document.fonts.status === 'loaded',
      hintCentered: (() => { const box = document.querySelector('.solar-enter-hint').getBoundingClientRect(); return box.left >= 0 && box.right <= innerWidth && Math.abs(box.left + box.width / 2 - innerWidth / 2) < 2; })(),
    })`);
    assert.deepEqual(layout, { lang: "fa", dir: "rtl", fits: true, heightFits: true, fontLoaded: true, hintCentered: true }, name);
    if (name === "desktop" || name === "mobile") await screenshot(name);
    console.log(`PASS ${name} ${width}x${height}: Persian RTL, fonts loaded, no page overflow`);
  }

  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await clearPlanetInteraction();
  await evaluate("document.querySelector('.solar-motion-toggle').click()");
  await waitFor(() => evaluate("document.querySelector('.solar-motion-toggle').getAttribute('aria-pressed') === 'true'"), "pause button");
  await waitForOrbitState("paused");
  await waitFor(() => evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)}))?.paused === true`), "persisted pause");
  await send("Page.reload");
  await waitForLanding();
  await waitForOrbitState("paused");
  await evaluate("document.querySelector('.solar-motion-toggle').click()");
  await waitForOrbitState("running");
  console.log("PASS pause persists across reload; resume restarts all orbits");

  const planet = await evaluate(`(() => {
    const rect = document.querySelector('.solar-planet').getBoundingClientRect();
    return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
  })()`);
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", ...planet });
  await waitForOrbitState("paused");
  await clearPlanetInteraction();
  await waitForOrbitState("running");
  await press("Tab", "Tab", 9);
  await evaluate("document.querySelector('.solar-planet').focus()");
  await waitForOrbitState("paused");
  console.log("PASS hovering or focusing a media button pauses orbit movement");

  const initialUrl = await evaluate("location.href");
  await press("Enter", "Enter", 13);
  await waitFor(() => evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)}))?.source === 'instagram'`), "keyboard source selection");
  await waitFor(() => evaluate("[...document.querySelectorAll('[role=status]')].some(node => node.textContent.includes('Instagram'))"), "start feedback");
  assert.equal(await evaluate("location.href"), initialUrl);
  await clearPlanetInteraction();
  await evaluate("document.querySelector('.solar-core').click()");
  await delay(150);
  assert.equal(await evaluate("location.href"), initialUrl);
  const selectedSource = await evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)})).source`);
  assert.equal(typeof selectedSource, "string");
  console.log("PASS keyboard start stores selected media locally, provides feedback and keeps the URL unchanged");

  await evaluate("document.querySelector('.theme-toggle').click()");
  await waitFor(() => evaluate("document.querySelector('.solar-portal').dataset.theme === 'light'"), "light theme");
  await waitFor(() => evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)}))?.theme === 'light'`), "persisted theme");
  await screenshot("light");
  await send("Page.reload");
  await waitForLanding();
  await waitFor(() => evaluate("document.querySelector('.solar-portal').dataset.theme === 'light'"), "restored light theme");
  const restored = await evaluate(`JSON.parse(localStorage.getItem(${JSON.stringify(store)}))`);
  assert.equal(restored.source, selectedSource);
  assert.equal(restored.paused, false);
  await evaluate("document.querySelector('.theme-toggle').click()");
  await waitFor(() => evaluate("document.querySelector('.solar-portal').dataset.theme === 'dark'"), "dark theme toggle");
  console.log("PASS both themes work; reload preserves theme and other stored selections");

  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  await waitFor(() => evaluate("document.querySelector('.solar-motion-toggle').disabled"), "reduced motion control");
  const reduced = await evaluate(`(() => {
    const nodes = [...document.querySelectorAll('.solar-system, .solar-rotor, .solar-counter, .solar-star--shimmer')];
    return nodes.length > 20 && nodes.every(node => getComputedStyle(node).animationName === 'none')
      && document.querySelector('.solar-portal').getAnimations({ subtree: true }).every(animation => animation.playState !== 'running');
  })()`);
  assert.equal(reduced, true, "reduced motion disables all entrance animations");
  assert.deepEqual(pageErrors, [], "no uncaught browser exceptions");
  console.log("PASS reduced motion disables animations and its motion button; no uncaught browser exceptions");
  console.log("Screenshots:", artifacts);
} catch (error) {
  if (socket?.readyState === WebSocket.OPEN) {
    console.error("Browser state:", await evaluate("({ url: location.href, ready: document.readyState, theme: document.querySelector('.solar-portal')?.dataset.theme, status: [...document.querySelectorAll('[role=status]')].map(node => node.textContent), media: document.querySelectorAll('.solar-planet').length })").catch(() => null));
    await screenshot("failure").catch(() => {});
  }
  console.error("Browser exceptions:", pageErrors);
  console.error("Browser network errors:", networkErrors);
  console.error("Artifacts:", artifacts);
  throw error;
} finally {
  if (socket?.readyState === WebSocket.OPEN) {
    await send("Browser.close").catch(() => {});
    socket.close();
  }
  chrome.kill();
}
