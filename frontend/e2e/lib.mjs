// Tiện ích chung cho E2E (Puppeteer): chờ text, click theo nhãn, điền input React, đăng nhập.
import assert from "node:assert/strict";

export const TIMEOUT = Number(process.env.E2E_TIMEOUT_MS ?? 30_000);

export function todayISO(offsetDays = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function uniqueEmail(prefix) {
  return `${prefix}.${Date.now()}.${Math.floor(Math.random() * 1e6)}@e2e-test.vn`; // không dùng TLD .test: email-validator coi là tên miền dành riêng
}

/** Chuỗi XPath an toàn cho text tiếng Việt có dấu nháy. */
function xpathLiteral(s) {
  if (!s.includes("'")) return `'${s}'`;
  if (!s.includes('"')) return `"${s}"`;
  return `concat('${s.replaceAll("'", `', "'", '`)}')`;
}

/** Phần tử nhỏ nhất (tag cho trước) có text chứa `text`, đang hiển thị. */
export async function findByText(page, tag, text, { timeout = TIMEOUT, within = "" } = {}) {
  const xp = `${within}//${tag}[contains(normalize-space(.), ${xpathLiteral(text)})]`;
  return page.waitForSelector(`::-p-xpath(${xp})`, { visible: true, timeout });
}

export async function clickText(page, tag, text, opts) {
  const el = await findByText(page, tag, text, opts);
  await el.click();
  return el;
}

export async function waitForText(page, text, timeout = TIMEOUT) {
  await page.waitForFunction((t) => document.body?.innerText.includes(t), { timeout }, text);
}

export async function bodyText(page) {
  return page.evaluate(() => document.body.innerText);
}

export async function assertNoText(page, text, message) {
  const body = await bodyText(page);
  assert.ok(!body.includes(text), message ?? `Không được hiển thị: "${text}"`);
}

/** Đặt giá trị cho input/textarea do React quản lý (kể cả type=date, không phụ thuộc locale trình duyệt). */
export async function setValue(page, selector, value) {
  await page.waitForSelector(selector, { visible: true, timeout: TIMEOUT });
  await page.$eval(
    selector,
    (el, v) => {
      const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      Object.getOwnPropertyDescriptor(proto, "value").set.call(el, v);
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
    },
    value,
  );
}

export async function gotoPath(page, base, path) {
  await page.goto(new URL(path, base).toString(), { waitUntil: "networkidle0", timeout: TIMEOUT * 2 });
}

export async function logout(page, base) {
  await gotoPath(page, base, "/");
  await page.evaluate(() => window.localStorage.clear());
}

export async function login(page, base, email, password = "123456") {
  await logout(page, base);
  await gotoPath(page, base, "/login");
  await setValue(page, "#login-email", email);
  await setValue(page, "#login-password", password);
  await Promise.all([
    page.waitForNavigation({ waitUntil: "networkidle0", timeout: TIMEOUT }).catch(() => undefined),
    page.click("form button[type=submit]"),
  ]);
  await page.waitForFunction(() => !location.pathname.startsWith("/login"), { timeout: TIMEOUT });
}

/** Gửi một tin nhắn cho Navigator ở trang chủ và chờ trợ lý trả lời xong. */
export async function sendNavigatorMessage(page, message) {
  const input = 'textarea[placeholder^="Ví dụ: Tôi 50 tuổi"], input[placeholder^="Ví dụ: Tôi 50 tuổi"]';
  await setValue(page, input, message);
  await page.click('button[aria-label="Gửi tin nhắn"]');
  await page.waitForSelector('[aria-label="Trợ lý đang soạn trả lời"]', { hidden: true, timeout: TIMEOUT });
  await page.waitForFunction(
    (m) => document.body.innerText.includes(m) && !document.querySelector('[aria-label="Trợ lý đang soạn trả lời"]'),
    { timeout: TIMEOUT },
    message,
  );
}

/** Điền form đăng ký (giữ tuỳ chọn gắn phiên tư vấn mặc định) và chờ chuyển trang. */
export async function register(page, { name, email, password = "123456" }) {
  await page.waitForSelector("#reg-name", { visible: true, timeout: TIMEOUT });
  await setValue(page, "#reg-name", name);
  await setValue(page, "#reg-email", email);
  await setValue(page, "#reg-password", password);
  await setValue(page, "#reg-confirm", password);
  await page.click("form button[type=submit]");
  await page.waitForFunction(() => !location.pathname.startsWith("/register"), { timeout: TIMEOUT });
}

/** Trên trang đặt lịch: dùng dịch vụ đã được gợi ý sẵn, đặt ngày, gửi. Trả về text vùng xác nhận. */
export async function submitBooking(page, { date = todayISO() } = {}) {
  await page.waitForSelector("#book-date", { visible: true, timeout: TIMEOUT });
  await setValue(page, "#book-date", date);
  await page.click("form button[type=submit]");
  await waitForText(page, "Đã gửi yêu cầu đặt lịch");
  return bodyText(page);
}

/** Thẻ lịch hẹn của bệnh nhân trong hàng chờ bác sĩ (XPath tới <li>). */
export function queueItemXPath(patientName) {
  return `//li[.//a[normalize-space(.)=${xpathLiteral(patientName)}]]`;
}

/** Bác sĩ: xác nhận (nếu cần) rồi bắt đầu khám lịch hẹn của `patientName`; trả về encounter id. */
export async function doctorStartEncounter(page, base, patientName) {
  await gotoPath(page, base, "/doctor");
  // Một bệnh nhân có thể có nhiều lịch hẹn (mỗi dịch vụ gợi ý một lịch) → luôn thao tác trên thẻ đầu tiên.
  const item = `(${queueItemXPath(patientName)})[1]`;
  await page.waitForSelector(`::-p-xpath(${item})`, { visible: true, timeout: TIMEOUT });
  const confirm = await page.$(`::-p-xpath(${item}//button[contains(., 'Xác nhận lịch')])`);
  if (confirm) {
    await confirm.click();
    // Đã xác nhận: thẻ hiển thị "Lịch khám <ngày>" thay cho "Mong muốn <ngày>"
    await page.waitForSelector(`::-p-xpath(${item}//span[starts-with(normalize-space(.), 'Lịch khám ')])`, {
      visible: true,
      timeout: TIMEOUT,
    });
  }
  await clickText(page, "button", "Bắt đầu khám", { within: item });
  await page.waitForFunction(() => /^\/doctor\/encounters\/[^/]+$/.test(location.pathname), { timeout: TIMEOUT * 2 });
  await page.waitForSelector("h1.page-title", { visible: true, timeout: TIMEOUT });
  return page.evaluate(() => location.pathname.split("/").pop());
}

