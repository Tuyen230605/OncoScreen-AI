// 4 kịch bản demo bắt buộc — docs/02_BUSINESS_FLOW.md §"Kịch bản demo".
// Mỗi kịch bản kiểm tra cả luồng nghiệp vụ lẫn quy tắc an toàn hiển thị ở tầng UI (S1, S3, S4, S6).
import assert from "node:assert/strict";

import {
  assertNoText,
  bodyText,
  clickText,
  doctorStartEncounter,
  findByText,
  gotoPath,
  login,
  logout,
  register,
  sendNavigatorMessage,
  setValue,
  submitBooking,
  todayISO,
  uniqueEmail,
  waitForText,
} from "./lib.mjs";

const DOCTOR = process.env.E2E_DOCTOR_EMAIL ?? "doctor@demo.vn";
const DISCLAIMER_MARK = "KHÔNG phải chẩn đoán";

async function assertDisclaimer(page, where) {
  const notes = await page.$$eval('[role="note"]', (els) => els.map((e) => e.innerText));
  assert.ok(notes.length > 0, `${where}: thiếu khối disclaimer (S6)`);
}

/** Kịch bản 1: Nữ 45 tuổi, mẹ ung thư vú → gợi ý → đăng ký → đặt lịch → bác sĩ duyệt → bệnh nhân thấy kết quả. */
async function breastJourney(page, base) {
  const name = `E2E Lan ${Date.now()}`;
  const email = uniqueEmail("lan");
  const conclusion = "Khám vú chưa ghi nhận bất thường. Hẹn chụp nhũ ảnh theo kế hoạch.";
  const internalNote = `GHI-CHU-NOI-BO-${Date.now()}`;

  await logout(page, base);
  await gotoPath(page, base, "/");
  await sendNavigatorMessage(page, "Tôi là nữ 45 tuổi, mẹ tôi bị ung thư vú. Tôi nên tầm soát gì?");
  await findByText(page, "h2", "Gợi ý tầm soát theo hướng dẫn");
  const result = await bodyText(page);
  assert.match(result, /vú/i, "phải gợi ý tầm soát ung thư vú");
  await assertDisclaimer(page, "Navigator");

  await clickText(page, "a", "Tạo tài khoản để đặt lịch");
  await register(page, { name, email });
  assert.match(new URL(page.url()).pathname, /^\/patient\/book/, "đăng ký từ CTA phải chuyển sang đặt lịch");
  await findByText(page, "span", "Được gợi ý");
  await submitBooking(page);

  await login(page, base, DOCTOR);
  const encounterId = await doctorStartEncounter(page, base, name);
  await waitForText(page, "Kế hoạch tầm soát");

  // Hỏi Copilot: câu trả lời phải có trích dẫn
  await setValue(page, 'textarea[placeholder^="Ví dụ: Lần tầm soát"], input[placeholder^="Ví dụ: Lần tầm soát"]',
    "Guideline nhũ ảnh áp dụng cho bệnh nhân này thế nào?");
  await page.click('button[aria-label="Gửi câu hỏi cho Copilot"]');
  await page.waitForFunction(
    () => [...document.querySelectorAll('section[aria-labelledby="copilot-chat-title"] a, section[aria-labelledby="copilot-chat-title"] button')]
      .some((el) => /uspstf|who|nguồn|hồ sơ/i.test(el.textContent ?? "")),
    { timeout: 30_000 },
  );

  // HITL: điền ngày hẹn, kết luận, ghi chú nội bộ → duyệt
  await setValue(page, "#plan-next-due-0", todayISO(30));
  await setValue(page, "#conclusion", conclusion);
  await setValue(page, "#notes", internalNote);
  await clickText(page, "button", "Duyệt và hoàn tất lượt khám");
  await clickText(page, "button", "Xác nhận và gửi bệnh nhân");
  await page.waitForSelector("#final-title", { visible: true, timeout: 30_000 });

  // Bệnh nhân: thấy kết luận + kế hoạch đã duyệt + nhắc lịch; KHÔNG thấy ghi chú nội bộ / brief (S4)
  await login(page, base, email);
  await gotoPath(page, base, `/patient/visits/${encounterId}`);
  await waitForText(page, conclusion);
  await waitForText(page, "Kế hoạch tầm soát đã duyệt");
  await assertNoText(page, internalNote, "ghi chú nội bộ của bác sĩ lộ ra cho bệnh nhân");
  await assertNoText(page, "Câu hỏi nên làm rõ với bệnh nhân", "brief của Copilot lộ ra cho bệnh nhân");
  await assertDisclaimer(page, "Kết quả lượt khám");

  await gotoPath(page, base, "/patient/reminders");
  await waitForText(page, "Nhắc lịch tầm soát");
  const [y, m, d] = todayISO(30).split("-");
  await waitForText(page, `${d}/${m}/${y}`);
}

/** Kịch bản 2: Nam 55 tuổi, 30 gói-năm (bảng hỏi nhanh) → gợi ý phổi; Copilot hỏi thêm thời gian bỏ thuốc. */
async function lungQuickCheck(page, base) {
  const name = `E2E Hung ${Date.now()}`;
  const email = uniqueEmail("hung");
  const answers = {
    "Bạn bao nhiêu tuổi?": { number: 55 },
    "Giới tính của bạn?": { choice: "Nam" },
    "Bạn đang hút thuốc hoặc đã bỏ thuốc trong vòng 15 năm gần đây?": { choice: "Có" },
    "Ước tính số gói-năm (số gói/ngày × số năm hút)?": { number: 30 },
  };

  await logout(page, base);
  await gotoPath(page, base, "/");
  await clickText(page, "button", "Bảng hỏi nhanh");
  const form = 'form[aria-label="Bảng hỏi nhanh"]';
  await page.waitForSelector(`${form} h3`, { visible: true }); // câu hỏi tải bất đồng bộ
  for (let step = 0; step < 20; step += 1) {
    const heading = await page.$(`${form} h3`);
    if (!heading) break;
    const question = (await heading.evaluate((el) => el.innerText)).trim();
    const answer = answers[question];
    const numberInput = await page.$(`${form} input[type=number]`);
    if (answer?.number !== undefined && numberInput) {
      await setValue(page, `${form} input[type=number]`, String(answer.number));
    } else if (answer?.choice) {
      await clickText(page, "label", answer.choice, { within: `//form[@aria-label="Bảng hỏi nhanh"]` });
    } else if (await page.$(`${form} textarea`)) {
      // câu hỏi tự do không bắt buộc → để trống
    } else {
      // Câu không nằm trong kịch bản → trả lời "Không" (boolean / multi-choice có lựa chọn "Không")
      await clickText(page, "label", "Không", { within: `//form[@aria-label="Bảng hỏi nhanh"]` });
    }
    const last = await page.$(`::-p-xpath(//form[@aria-label="Bảng hỏi nhanh"]//button[@type="submit" and contains(., "Gửi câu trả lời")])`);
    await page.click(`${form} button[type=submit]`);
    if (last) break;
    await page.waitForFunction(
      (sel, q) => document.querySelector(`${sel} h3`)?.innerText.trim() !== q,
      { timeout: 10_000 },
      form,
      question,
    );
  }
  await findByText(page, "h2", "Gợi ý tầm soát theo hướng dẫn");
  const result = await bodyText(page);
  assert.match(result, /phổi/i, "nam 55 tuổi, 30 gói-năm phải được gợi ý tầm soát ung thư phổi");
  assert.match(result, /đại trực tràng/i, "phải gợi ý tầm soát đại trực tràng");
  await assertDisclaimer(page, "Navigator (bảng hỏi nhanh)");

  await clickText(page, "a", "Tạo tài khoản để đặt lịch");
  await register(page, { name, email });
  await submitBooking(page);

  await login(page, base, DOCTOR);
  await doctorStartEncounter(page, base, name);
  await waitForText(page, "Câu hỏi nên làm rõ với bệnh nhân");
  // Copilot hỏi thêm thời gian bỏ thuốc (tiêu chí LDCT: còn hút hoặc bỏ ≤ 15 năm)
  await waitForText(page, "Nếu đã bỏ, cách đây bao nhiêu năm");
  await waitForText(page, "≤ 15 năm");
}

/** Kịch bản 3: red-flag → ngắt tư vấn, cảnh báo khám sớm, lịch ưu tiên lên đầu hàng chờ, brief không có kế hoạch. */
async function redFlag(page, base) {
  const name = `E2E Mai ${Date.now()}`;
  const email = uniqueEmail("mai");

  await logout(page, base);
  await gotoPath(page, base, "/");
  await sendNavigatorMessage(page, "Em sờ thấy khối cứng ở vú");
  await page.waitForSelector('[role="alert"]', { visible: true, timeout: 30_000 });
  await waitForText(page, "Bạn nên được bác sĩ khám sớm");
  await assertNoText(page, "Gợi ý tầm soát theo hướng dẫn", "red-flag không được kèm gợi ý tầm soát (S3)");

  await clickText(page, "a", "Tạo tài khoản, đặt lịch ưu tiên");
  await register(page, { name, email });
  await waitForText(page, "Gửi yêu cầu khám ưu tiên");
  const booked = await submitBooking(page);
  assert.match(booked, /Ưu tiên/, "lịch hẹn red-flag phải có mức ưu tiên");

  await login(page, base, DOCTOR);
  await gotoPath(page, base, "/doctor");
  await findByText(page, "a", name);
  const firstPatient = await page.$eval("main li a", (a) => a.textContent?.trim());
  assert.equal(firstPatient, name, "ca red-flag phải đứng đầu hàng chờ");
  await doctorStartEncounter(page, base, name);
  await waitForText(page, "Dấu hiệu cảnh báo cần đánh giá lâm sàng");
  await waitForText(page, "Không đưa gợi ý tầm soát định kỳ khi có dấu hiệu cảnh báo");
  const hasDraftDate = await page.$("#plan-next-due-0");
  assert.equal(hasDraftDate, null, "brief ca red-flag không được có bản nháp kế hoạch tầm soát (S3)");
}

/** Kịch bản 4: hỏi diễn giải kết quả PSA → từ chối chẩn đoán, mời đặt lịch khám (S1). */
async function refuseDiagnosis(page, base) {
  await logout(page, base);
  await gotoPath(page, base, "/");
  await sendNavigatorMessage(page, "Kết quả PSA của tôi là 6, có phải ung thư không?");
  await waitForText(page, "không thể chẩn đoán");
  await waitForText(page, "đặt lịch");
  await assertNoText(page, "Bạn nên được bác sĩ khám sớm", "câu hỏi diễn giải kết quả không phải red-flag");
  const body = await bodyText(page);
  assert.ok(!/bạn (bị|mắc) ung thư|có thể là ung thư/i.test(body), "không được có ngôn ngữ chẩn đoán");
  assert.ok(body.includes(DISCLAIMER_MARK) || (await page.$('[role="note"]')), "thiếu disclaimer (S6)");
}

export const SCENARIOS = [
  ["1. Nữ 45 tuổi, mẹ ung thư vú → bác sĩ duyệt → bệnh nhân thấy kết quả", breastJourney],
  ["2. Nam 55 tuổi, 30 gói-năm (bảng hỏi nhanh) → phổi + Copilot hỏi thời gian bỏ thuốc", lungQuickCheck],
  ["3. Red-flag → ngắt luồng, ưu tiên, brief không có kế hoạch", redFlag],
  ["4. Hỏi diễn giải PSA → từ chối chẩn đoán", refuseDiagnosis],
];
