// Local authentication UI checks with Chrome/CDP; no external mailbox or SMTP.
// Test credentials and verification links never appear in console diagnostics.
import assert from "node:assert/strict";
import { execFile, spawn } from "node:child_process";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const execFileAsync = promisify(execFile);
const artifacts = await mkdtemp(path.join(tmpdir(), "nama-analyze-auth-"));
const profile = path.join(artifacts, "chrome-profile");
const origin = new URL(process.env.APP_ORIGIN ?? "http://localhost:3000/").origin;
const email = `nama-browser-${Date.now().toString(36)}@example.test`;
const password = "NAMA-browser-check-9!Forest";
const chrome = spawn(process.env.CHROME_PATH ?? "C:/Program Files/Google/Chrome/Application/chrome.exe", [
  "--headless=new", "--disable-gpu", "--no-proxy-server", "--no-first-run", "--disable-extensions",
  "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank",
], { windowsHide: true, stdio: "ignore" });
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const pending = new Map();
const pageErrors = [];
const requests = [];
let sequence = 0;
let socket;
let launchError;
let loginMode = "pass";
let heldLogin;
chrome.on("error", (error) => { launchError = error; });

function redact(value) {
  return String(value).replaceAll(password, "[redacted]").replace(/#token=[A-Za-z0-9_-]+/g, "#token=[redacted]");
}

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
  if (result.exceptionDetails) throw new Error(redact(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text));
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

async function navigate(route) {
  const before = requests.length;
  const pathname = new URL(route, origin).pathname.replace(/\/$/, "");
  await send("Page.navigate", { url: origin + route });
  await waitFor(() => evaluate(`location.pathname.replace(/\\/$/, '') === ${JSON.stringify(pathname)} && document.readyState === 'complete' && !!document.querySelector('.auth-portal')`), "authentication route and shell");
  if (pathname === "/auth/login" || pathname === "/auth/signup") {
    await waitFor(() => requests.slice(before).some((request) => request.path === "/api/v1/auth/me/"), "mounted session-aware form");
  }
  await evaluate("document.fonts.ready.then(() => true)");
  await delay(150);
}

async function fill(selector, text) {
  await evaluate(`document.querySelector(${JSON.stringify(selector)}).focus(); document.querySelector(${JSON.stringify(selector)}).select()`);
  await send("Input.insertText", { text });
  // A boolean assertion prevents test passwords from entering assertion output.
  await waitFor(() => evaluate(`document.querySelector(${JSON.stringify(selector)}).value === ${JSON.stringify(text)}`), "field input");
}

async function screenshot(name) {
  assert.equal(await evaluate("[...document.querySelectorAll('input')].filter(input => input.id.toLowerCase().includes('password')).every(input => !input.value || input.type === 'password')"), true, "passwords must be empty or masked in screenshots");
  const result = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  await writeFile(path.join(artifacts, `${name}.png`), Buffer.from(result.data, "base64"));
}

async function loginInterception(requestId) {
  if (loginMode === "hold") { heldLogin = requestId; return; }
  if (loginMode === "network") { await send("Fetch.failRequest", { requestId, errorReason: "ConnectionFailed" }); return; }
  if (loginMode === "rate") {
    await send("Fetch.fulfillRequest", {
      requestId, responseCode: 429,
      responseHeaders: [{ name: "Content-Type", value: "application/json" }, { name: "Retry-After", value: "60" }],
      body: Buffer.from(JSON.stringify({ detail: "Request was throttled. Expected available in 60 seconds." })).toString("base64"),
    });
    return;
  }
  await send("Fetch.continueRequest", { requestId });
}

async function waitError(expectedText = "") {
  await waitFor(() => evaluate(`!!document.querySelector('#authError')?.textContent.trim() && document.querySelector('#authError').textContent.includes(${JSON.stringify(expectedText)}) && document.querySelector('.auth-submit')?.disabled === false`), "authentication error feedback");
}

async function readVerificationURL() {
  try {
    const result = await execFileAsync("python", [path.join(root, "scripts", "read_local_email.py"), "--recipient", email, "--json"], { cwd: root, windowsHide: true, encoding: "utf8" });
    const value = JSON.parse(result.stdout);
    const url = new URL(value.verification_url);
    assert.equal(url.pathname, "/auth/verify");
    assert.equal(/^#token=[A-Za-z0-9_-]{43}$/.test(url.hash), true, "verification token has the expected random shape");
    return url;
  } catch {
    // execFile errors may include stdout containing a private link.
    throw new Error("Local verification email could not be read; check local file email delivery.");
  }
}

async function checkLayout(mode, theme, width, height) {
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
  await evaluate("window.scrollTo(0, 0)");
  await delay(150);
  const layout = await evaluate(`(() => {
    const root = document.documentElement.getBoundingClientRect();
    const main = document.querySelector('.auth-portal').getBoundingClientRect();
    const header = document.querySelector('.auth-header').getBoundingClientRect();
    const card = document.querySelector('.auth-card').getBoundingClientRect();
    return { lang:document.documentElement.lang, dir:document.documentElement.dir,
      fits:document.documentElement.scrollWidth <= innerWidth,
      aligned:Math.abs(main.left-root.left)<1 && Math.abs(main.right-root.right)<1 && scrollX===0,
      cardFits:card.left>=root.left && card.right<=root.right,
      sectionsSeparate:header.bottom <= card.top+1,
      inputsFit:[...document.querySelectorAll('.auth-card input')].every(input=>{const r=input.getBoundingClientRect();return r.left>=card.left && r.right<=card.right}),
      fonts:document.fonts.status==='loaded' };
  })()`);
  assert.deepEqual(layout, { lang: "fa", dir: "rtl", fits: true, aligned: true, cardFits: true, sectionsSeparate: true, inputsFit: true, fonts: true }, `${mode} ${theme} ${width}`);
  await screenshot(`${mode}-${theme}-${width}`);
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
      pageErrors.push(redact(message.params.exceptionDetails.exception?.description ?? message.params.exceptionDetails.text));
    } else if (message.method === "Network.requestWillBeSent") {
      const request = message.params.request;
      const url = new URL(request.url);
      if (url.pathname.startsWith("/api/v1/auth/")) requests.push({ path: url.pathname, method: request.method, csrf: Object.keys(request.headers).some((name) => name.toLowerCase() === "x-csrftoken") });
    } else if (message.method === "Fetch.requestPaused") {
      void loginInterception(message.params.requestId).catch((error) => pageErrors.push(redact(error.message)));
    }
  });
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Network.enable");
  await send("Page.bringToFront");
  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: origin + "/" });
  await waitFor(() => evaluate("!!document.querySelector('.solar-auth-link') && document.querySelector('.solar-motion-toggle')?.disabled === false"), "hydrated solar sign-in link");
  assert.equal(await evaluate("document.querySelector('.solar-auth-link').textContent.includes('Sign in / Sign up')"), true);
  await evaluate("document.querySelector('.solar-auth-link').click()");
  await waitFor(() => evaluate("location.pathname.replace(/\\/$/, '') === '/auth/login' && !!document.querySelector('#authEmail')"), "login navigation");
  console.log("PASS solar Sign in / Sign up opens the real login route");

  for (const mode of ["login", "signup"]) {
    await navigate(`/auth/${mode}/`);
    await waitFor(() => evaluate("!!document.querySelector('#authEmail') && !!document.querySelector('#authPassword')"), `${mode} fields`);
    assert.equal(await evaluate("!!document.querySelector('label[for=authEmail]') && !!document.querySelector('label[for=authPassword]')"), true);
    assert.equal(await evaluate("getComputedStyle(document.querySelector('#authEmail')).direction === 'ltr' && getComputedStyle(document.querySelector('#authPassword')).direction === 'ltr'"), true);
    for (const theme of ["dark", "light"]) {
      if (await evaluate("document.querySelector('.auth-portal').dataset.theme") !== theme) await evaluate("document.querySelector('.theme-toggle').click()");
      for (const [width, height] of [[1440, 1000], [390, 844]]) await checkLayout(mode, theme, width, height);
    }
  }
  console.log("PASS login/signup dark/light desktop/mobile layouts, labels, LTR credentials and RTL page");

  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await navigate("/auth/signup/");
  await fill("#authDisplayName", "Browser Check");
  await fill("#authEmail", email);
  await fill("#authPassword", password);
  await fill("#authConfirmPassword", password + "mismatch");
  await evaluate("document.querySelector('.auth-submit').click()");
  await waitFor(() => evaluate("document.querySelector('#authConfirmPassword').getAttribute('aria-invalid') === 'true'"), "password mismatch validation");
  assert.equal(await evaluate("!!document.querySelector('#auth-pending')"), false);
  await evaluate("document.querySelector('.auth-password-toggle').click()");
  assert.equal(await evaluate("document.querySelector('#authPassword').type"), "text");
  await evaluate("document.querySelector('.auth-password-toggle').click()");
  assert.equal(await evaluate("document.querySelector('#authPassword').type"), "password");
  await fill("#authConfirmPassword", password);
  await evaluate("document.querySelector('.auth-submit').click()");
  await waitFor(() => evaluate("!!document.querySelector('#auth-pending')"), "signup generic email acknowledgement");
  await screenshot("signup-pending");
  console.log("PASS signup validates confirmation, toggles password visibility and requests local verification email");

  await navigate("/auth/login/");
  await fill("#authEmail", email);
  await fill("#authPassword", password);
  await send("Fetch.enable", { patterns: [{ urlPattern: "*/api/v1/auth/login/*", requestStage: "Request" }] });
  loginMode = "hold";
  await evaluate("document.querySelector('.auth-submit').click()");
  await waitFor(() => heldLogin, "pending login request");
  assert.equal(await evaluate("document.querySelector('.auth-submit').disabled"), true);
  loginMode = "pass";
  await loginInterception(heldLogin);
  heldLogin = undefined;
  await waitError();
  assert.equal(await evaluate("location.pathname.replace(/\\/$/, '')"), "/auth/login");
  assert.equal(await evaluate("fetch('/api/v1/auth/me/', {credentials:'same-origin'}).then(response=>response.status)"), 403);
  console.log("PASS pending submit is disabled; an unverified account cannot sign in");

  const verification = await readVerificationURL();
  assert.equal(verification.origin, origin, "test origin matches the configured verification origin");
  const confirmationCount = requests.filter((request) => request.path === "/api/v1/auth/verification/confirm/" && request.method === "POST").length;
  await send("Page.navigate", { url: verification.href });
  await waitFor(() => evaluate("!!document.querySelector('.auth-verify-confirm')"), "explicit verification confirmation");
  await delay(200);
  assert.equal(requests.filter((request) => request.path === "/api/v1/auth/verification/confirm/" && request.method === "POST").length, confirmationCount, "opening a link must not consume it");
  await evaluate("document.querySelector('.auth-verify-confirm').click()");
  await waitFor(() => evaluate("!!document.querySelector('#authStatus')?.textContent.trim()"), "email verified acknowledgement");
  assert.equal(await evaluate("location.hash"), "", "verification fragment removed after confirmation");
  await screenshot("verified");
  console.log("PASS verification requires an explicit action and removes the private fragment after success");

  await send("Page.navigate", { url: verification.href });
  await waitFor(() => evaluate("!!document.querySelector('.auth-verify-confirm')"), "replay confirmation");
  await evaluate("document.querySelector('.auth-verify-confirm').click()");
  await waitFor(() => evaluate("!!document.querySelector('#authError')?.textContent.trim()"), "used verification link rejected");
  assert.equal(await evaluate("location.hash"), "", "fragment also removed after a failed confirmation");
  await navigate("/auth/verify/");
  await waitFor(() => evaluate("!!document.querySelector('.auth-resend-form') && !document.querySelector('.auth-verify-confirm')"), "missing verification link recovery form");
  console.log("PASS used links show an error; missing links offer a resend form");

  await navigate("/auth/login/");
  await fill("#authEmail", email);
  await fill("#authPassword", password);
  loginMode = "rate";
  await evaluate("document.querySelector('.auth-submit').click()");
  await waitError("درخواست‌های زیادی");
  await screenshot("login-rate-limit");
  loginMode = "network";
  await evaluate("document.querySelector('.auth-submit').click()");
  await waitError("ارتباط");
  loginMode = "pass";
  await evaluate("document.querySelector('#authPassword').focus()");
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13, text: "\r", unmodifiedText: "\r" });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
  await waitFor(() => evaluate("location.pathname.replace(/\\/$/, '') === '/start/idea'"), "verified account keyboard login");
  assert.equal(await evaluate(`fetch('/api/v1/auth/me/',{credentials:'same-origin'}).then(async response=>response.status===200&&(await response.json()).user.email===${JSON.stringify(email)})`), true);
  const cookies = await send("Network.getCookies", { urls: [origin + "/"] });
  assert.equal(cookies.cookies.some((cookie) => cookie.name === "sessionid" && cookie.httpOnly), true, "session cookie is HttpOnly");
  assert.equal(await evaluate(`Object.values(localStorage).some(value=>value.includes(${JSON.stringify(password)})||value.includes(${JSON.stringify(verification.hash.slice(7))}))`), false, "passwords and verification tokens are absent from localStorage");
  assert.equal(requests.filter((request) => request.method === "POST" && request.path !== "/api/v1/auth/me/").every((request) => request.csrf), true, "unsafe authentication requests carry CSRF tokens");
  assert.deepEqual(pageErrors, [], "no uncaught browser exceptions");
  console.log("PASS rate/network errors recover; Enter login works after verification; session/CSRF and credential storage checks pass");
  console.log("Screenshots:", artifacts);
} catch (error) {
  if (socket?.readyState === WebSocket.OPEN) {
    console.error("Browser state:", await evaluate("({route:location.origin+location.pathname,ready:document.readyState,theme:document.querySelector('.auth-portal')?.dataset.theme,errors:[...document.querySelectorAll('[role=alert]')].map(node=>node.textContent),statuses:[...document.querySelectorAll('[role=status]')].map(node=>node.textContent)})").catch(() => null));
    await screenshot("failure").catch(() => {});
  }
  console.error("Browser exceptions:", pageErrors.map(redact));
  console.error("Artifacts:", artifacts);
  throw new Error(redact(error.message));
} finally {
  if (socket?.readyState === WebSocket.OPEN) {
    await send("Browser.close").catch(() => {});
    socket.close();
  }
  chrome.kill();
}
