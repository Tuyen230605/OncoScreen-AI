#!/usr/bin/env node
// E2E FE ↔ BE cho 4 kịch bản demo (MockAgent, không gọi LLM).
//
//   npm run e2e                       # tự dựng backend (SQLite tạm + seed) + frontend (build riêng .next-e2e)
//   E2E_BASE_URL=http://localhost:3000 npm run e2e   # dùng hệ thống đang chạy sẵn (đã seed, USE_MOCK_AGENT=true)
//
// Biến môi trường: E2E_PYTHON (python có cài backend + ai_core), E2E_SKIP_BUILD=1, E2E_HEADFUL=1,
// E2E_ONLY=<số kịch bản, vd "1,3">, E2E_BACKEND_PORT (8100), E2E_FRONTEND_PORT (3100).
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import puppeteer from "puppeteer";

import { SCENARIOS } from "./scenarios.mjs";

const FRONTEND_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const REPO_ROOT = path.resolve(FRONTEND_DIR, "..");
const BACKEND_DIR = path.join(REPO_ROOT, "backend");
const ARTIFACTS = path.join(FRONTEND_DIR, "e2e", "artifacts");
const IS_WIN = process.platform === "win32";
const BACKEND_PORT = Number(process.env.E2E_BACKEND_PORT ?? 8100);
const FRONTEND_PORT = Number(process.env.E2E_FRONTEND_PORT ?? 3100);

const children = [];

function log(msg) {
  process.stdout.write(`[e2e] ${msg}\n`);
}

function pythonExe() {
  if (process.env.E2E_PYTHON) return process.env.E2E_PYTHON;
  const venv = path.join(REPO_ROOT, ".venv", IS_WIN ? "Scripts/python.exe" : "bin/python");
  return existsSync(venv) ? venv : "python";
}

function run(cmd, args, opts) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, args, { stdio: "inherit", shell: IS_WIN && cmd === "npx", ...opts });
    p.on("error", reject);
    p.on("exit", (code) => (code === 0 ? resolve() : reject(new Error(`${cmd} ${args.join(" ")} → exit ${code}`))));
  });
}

function startDaemon(name, cmd, args, opts) {
  const p = spawn(cmd, args, { stdio: ["ignore", "pipe", "pipe"], shell: IS_WIN && cmd === "npx", ...opts });
  const tail = [];
  const keep = (chunk) => {
    tail.push(...chunk.toString().split("\n"));
    tail.splice(0, Math.max(0, tail.length - 40));
  };
  p.stdout.on("data", keep);
  p.stderr.on("data", keep);
  p.on("exit", (code) => {
    if (!p.stopping) log(`${name} dừng bất thường (exit ${code}). Log cuối:\n${tail.join("\n")}`);
  });
  children.push(p);
  return p;
}

async function waitForUrl(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url);
      if (res.ok) return res;
    } catch {
      /* chưa lên */
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`Hết thời gian chờ ${url}`);
}

function stopAll() {
  for (const p of children) {
    if (p.exitCode !== null) continue;
    p.stopping = true;
    if (IS_WIN) spawn("taskkill", ["/pid", String(p.pid), "/T", "/F"], { stdio: "ignore" });
    else p.kill("SIGTERM");
  }
}

async function startStack() {
  const tmp = mkdtempSync(path.join(tmpdir(), "oncoscreen-e2e-"));
  const apiBase = `http://localhost:${BACKEND_PORT}/api/v1`;
  const backendEnv = {
    ...process.env,
    DATABASE_URL: `sqlite:///${path.join(tmp, "e2e.db").replaceAll("\\", "/")}`,
    USE_MOCK_AGENT: "true",
    LLM_API_KEY: "",
    SECRET_KEY: "e2e-only-secret",
    CORS_ORIGINS: `http://localhost:${FRONTEND_PORT}`,
    REMINDER_TICK_SECONDS: "3600",
    PYTHONIOENCODING: "utf-8",
  };
  const py = pythonExe();
  log(`seed backend (python: ${py})`);
  await run(py, ["scripts/seed.py"], { cwd: BACKEND_DIR, env: backendEnv });
  startDaemon("backend", py, ["-m", "uvicorn", "app.main:app", "--port", String(BACKEND_PORT)], {
    cwd: BACKEND_DIR,
    env: backendEnv,
  });
  const health = await (await waitForUrl(`${apiBase}/health`, 60_000)).json();
  if (health.agent !== "mock") throw new Error(`Backend E2E phải chạy MockAgent, nhận: ${JSON.stringify(health)}`);

  const feEnv = {
    ...process.env,
    NEXT_DIST_DIR: ".next-e2e",
    NEXT_PUBLIC_API_BASE_URL: apiBase,
    NEXT_PUBLIC_USE_MOCK_API: "false",
    NEXT_TELEMETRY_DISABLED: "1",
  };
  if (process.env.E2E_SKIP_BUILD !== "1" || !existsSync(path.join(FRONTEND_DIR, ".next-e2e"))) {
    log("build frontend → .next-e2e");
    await run("npx", ["next", "build"], { cwd: FRONTEND_DIR, env: feEnv });
  }
  startDaemon("frontend", "npx", ["next", "start", "-p", String(FRONTEND_PORT)], { cwd: FRONTEND_DIR, env: feEnv });
  const base = `http://localhost:${FRONTEND_PORT}`;
  await waitForUrl(base, 60_000);
  return { base, cleanup: () => rmSync(tmp, { recursive: true, force: true }) };
}

async function main() {
  let stack = null;
  const base = process.env.E2E_BASE_URL ?? (stack = await startStack()).base;
  const only = process.env.E2E_ONLY?.split(",").map((s) => s.trim());
  const selected = SCENARIOS.filter(([title]) => !only || only.includes(title.split(".")[0]));
  mkdirSync(ARTIFACTS, { recursive: true });

  const browser = await puppeteer.launch({
    headless: process.env.E2E_HEADFUL !== "1",
    // Runner Ubuntu 24.04 của CI chặn user namespace → sandbox Chrome không khởi động được.
    args: process.env.CI ? ["--no-sandbox", "--disable-setuid-sandbox"] : [],
  });
  const results = [];
  try {
    for (const [title, fn] of selected) {
      const context = await browser.createBrowserContext(); // localStorage/cookie riêng mỗi kịch bản
      const page = await context.newPage();
      page.setDefaultTimeout(30_000);
      await page.setViewport({ width: 1366, height: 900 });
      const consoleErrors = [];
      page.on("pageerror", (err) => consoleErrors.push(String(err)));
      const started = Date.now();
      try {
        await fn(page, base);
        results.push({ title, ok: true, ms: Date.now() - started });
        log(`PASS ${title} (${((Date.now() - started) / 1000).toFixed(1)} s)`);
      } catch (err) {
        const shot = path.join(ARTIFACTS, `fail-${title.split(".")[0]}.png`);
        await page.screenshot({ path: shot, fullPage: true }).catch(() => undefined);
        results.push({ title, ok: false, ms: Date.now() - started, error: err });
        log(`FAIL ${title}\n  ${err?.stack ?? err}\n  url: ${page.url()}\n  screenshot: ${shot}`);
        if (consoleErrors.length) log(`  lỗi JS trên trang: ${consoleErrors.join(" | ")}`);
      } finally {
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
  const failed = results.filter((r) => !r.ok);
  log(`${results.length - failed.length}/${results.length} kịch bản pass`);
  return { failed: failed.length, stack };
}

let exitCode = 1;
let stackRef = null;
try {
  const { failed, stack } = await main();
  stackRef = stack;
  exitCode = failed ? 1 : 0;
} catch (err) {
  log(`Lỗi dựng môi trường E2E: ${err?.stack ?? err}`);
} finally {
  stopAll();
  setTimeout(() => {
    stackRef?.cleanup();
    process.exit(exitCode);
  }, 1500);
}
