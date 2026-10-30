"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { errorMessage, isStatus } from "@/lib/errors";
import { CANCER_LABEL, geneticsLabel, RELATIVE_LABEL as RELATIVES } from "@/lib/labels";
import type { CancerType, Gender, Lifestyle, PatientProfileIn } from "@/types/api";
import { InlineError } from "@/components/ui";
import { Activity, CheckCircle2, HeartPulse, Plus, User, X } from "@/components/icons";

/** Thông tin sức khoẻ cơ bản (PUT /patients/me/profile). Được điền sẵn khi đăng ký kèm cuộc trò chuyện. */
export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const [age, setAge] = useState<number | "">("");
  const [gender, setGender] = useState<Gender | "">("");
  const [genetics, setGenetics] = useState<string[]>([]);
  const [newCancer, setNewCancer] = useState<CancerType>("breast");
  const [newRelative, setNewRelative] = useState("mother");
  const [lifestyle, setLifestyle] = useState<Lifestyle>({});

  useEffect(() => {
    api
      .getProfile()
      .then((p) => {
        setAge(p.age);
        setGender(p.gender);
        setGenetics(p.genetics_history ?? []);
        setLifestyle(p.lifestyle ?? {});
      })
      .catch((err) => {
        if (!isStatus(err, 404)) setError(errorMessage(err, "Chưa tải được hồ sơ."));
      })
      .finally(() => setLoading(false));
  }, []);

  function addGenetics() {
    const code = `${newCancer}_cancer_${newRelative}`;
    if (!genetics.includes(code)) setGenetics([...genetics, code]);
  }

  const setBool = (key: "smoking" | "hepatitis_b_or_c" | "cirrhosis", value: boolean) =>
    setLifestyle((prev) => ({ ...prev, [key]: value, ...(key === "smoking" && !value ? { pack_years: undefined } : {}) }));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (age === "" || age < 1 || age > 120) {
      setError("Vui lòng nhập tuổi từ 1 đến 120.");
      return;
    }
    if (!gender) {
      setError("Vui lòng chọn giới tính.");
      return;
    }
    let bmi = lifestyle.bmi;
    if (lifestyle.height_cm && lifestyle.weight_kg) {
      const h = lifestyle.height_cm / 100;
      bmi = Number((lifestyle.weight_kg / (h * h)).toFixed(1));
    }
    const payload: PatientProfileIn = { age: Number(age), gender, genetics_history: genetics, lifestyle: { ...lifestyle, bmi } };
    try {
      setSaving(true);
      await api.putProfile(payload);
      setSuccess(true);
      setTimeout(() => router.push("/patient"), 900);
    } catch (err) {
      setError(errorMessage(err, "Lưu hồ sơ thất bại. Vui lòng thử lại."));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-2xl space-y-4" aria-busy="true">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-40 rounded-xl" />
        <div className="skeleton h-40 rounded-xl" />
      </div>
    );
  }

  const boolField = (key: "smoking" | "hepatitis_b_or_c" | "cirrhosis", legend: string) => (
    <fieldset className="sm:col-span-2">
      <legend className="label">{legend}</legend>
      <div className="flex flex-wrap gap-2 text-sm">
        {[
          { label: "Có", value: true },
          { label: "Không", value: false },
        ].map((opt) => (
          <label
            key={opt.label}
            className={`flex cursor-pointer items-center gap-2 rounded-lg border px-4 py-2 transition-colors ${
              lifestyle[key] === opt.value ? "border-teal-500 bg-teal-50" : "border-slate-200 hover:bg-slate-50"
            }`}
          >
            <input
              type="radio"
              name={key}
              checked={lifestyle[key] === opt.value}
              onChange={() => setBool(key, opt.value)}
              className="accent-teal-700"
            />
            <span>{opt.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="page-title">Thông tin sức khoẻ cơ bản</h1>
        <p className="page-subtitle">Giúp bác sĩ và trợ lý đối chiếu đúng hướng dẫn tầm soát. Bạn có thể cập nhật bất cứ lúc nào.</p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        <section className="card-padded space-y-4">
          <h2 className="flex items-center gap-2 border-b border-slate-100 pb-2.5 text-base font-semibold text-slate-900">
            <User className="h-5 w-5 text-teal-700" aria-hidden="true" />
            Thông tin chung
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="profile-age" className="label">
                Tuổi
              </label>
              <input
                id="profile-age"
                type="number"
                min={1}
                max={120}
                required
                value={age}
                onChange={(e) => setAge(e.target.value === "" ? "" : Number(e.target.value))}
                className="input"
              />
            </div>
            <div>
              <label htmlFor="profile-gender" className="label">
                Giới tính
              </label>
              <select
                id="profile-gender"
                value={gender}
                onChange={(e) => setGender(e.target.value as Gender)}
                className="input"
                required
              >
                <option value="" disabled>
                  Chọn giới tính
                </option>
                <option value="female">Nữ</option>
                <option value="male">Nam</option>
                <option value="other">Khác</option>
              </select>
            </div>
          </div>
        </section>

        <section className="card-padded space-y-4">
          <div className="border-b border-slate-100 pb-2.5">
            <h2 className="flex items-center gap-2 text-base font-semibold text-slate-900">
              <HeartPulse className="h-5 w-5 text-teal-700" aria-hidden="true" />
              Tiền sử gia đình
            </h2>
            <p className="mt-0.5 text-sm text-slate-500">Người thân ruột thịt từng mắc ung thư.</p>
          </div>
          <div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
            <div>
              <label htmlFor="profile-gen-cancer" className="label">
                Loại ung thư
              </label>
              <select
                id="profile-gen-cancer"
                className="input"
                value={newCancer}
                onChange={(e) => setNewCancer(e.target.value as CancerType)}
              >
                {(Object.keys(CANCER_LABEL) as CancerType[]).map((t) => (
                  <option key={t} value={t}>
                    {CANCER_LABEL[t]}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="profile-gen-relative" className="label">
                Người thân
              </label>
              <select
                id="profile-gen-relative"
                className="input"
                value={newRelative}
                onChange={(e) => setNewRelative(e.target.value)}
              >
                {Object.entries(RELATIVES).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
            <button type="button" onClick={addGenetics} className="btn-secondary">
              <Plus className="h-4 w-4" aria-hidden="true" />
              Thêm
            </button>
          </div>
          {genetics.length > 0 ? (
            <ul className="flex flex-wrap gap-2">
              {genetics.map((g) => (
                <li key={g} className="badge gap-1.5 border border-teal-200 bg-teal-50 py-1 text-teal-800">
                  <span>{geneticsLabel(g)}</span>
                  <button
                    type="button"
                    onClick={() => setGenetics(genetics.filter((x) => x !== g))}
                    className="cursor-pointer rounded text-teal-700 hover:text-teal-900"
                    aria-label={`Xoá ${geneticsLabel(g)}`}
                  >
                    <X className="h-3.5 w-3.5" aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">Chưa ghi nhận tiền sử gia đình.</p>
          )}
        </section>

        <section className="card-padded space-y-4">
          <h2 className="flex items-center gap-2 border-b border-slate-100 pb-2.5 text-base font-semibold text-slate-900">
            <Activity className="h-5 w-5 text-teal-700" aria-hidden="true" />
            Lối sống và bệnh nền
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {boolField("smoking", "Đang hút thuốc hoặc bỏ thuốc chưa quá 15 năm")}
            {lifestyle.smoking === true && (
              <div className="sm:col-span-2">
                <label htmlFor="profile-pack-years" className="label">
                  Số gói-năm (số gói/ngày × số năm hút)
                </label>
                <input
                  id="profile-pack-years"
                  type="number"
                  min={0}
                  max={200}
                  value={lifestyle.pack_years ?? ""}
                  onChange={(e) =>
                    setLifestyle({ ...lifestyle, pack_years: e.target.value === "" ? undefined : Number(e.target.value) })
                  }
                  className="input max-w-xs"
                />
              </div>
            )}
            {boolField("hepatitis_b_or_c", "Viêm gan B hoặc C mạn tính")}
            {boolField("cirrhosis", "Có tiền sử xơ gan (theo thông tin bác sĩ từng cho biết)")}
            <div>
              <label htmlFor="profile-height" className="label">
                Chiều cao (cm)
              </label>
              <input
                id="profile-height"
                type="number"
                min={50}
                max={250}
                value={lifestyle.height_cm ?? ""}
                onChange={(e) =>
                  setLifestyle({ ...lifestyle, height_cm: e.target.value === "" ? undefined : Number(e.target.value) })
                }
                className="input"
              />
            </div>
            <div>
              <label htmlFor="profile-weight" className="label">
                Cân nặng (kg)
              </label>
              <input
                id="profile-weight"
                type="number"
                step="0.1"
                min={10}
                max={300}
                value={lifestyle.weight_kg ?? ""}
                onChange={(e) =>
                  setLifestyle({ ...lifestyle, weight_kg: e.target.value === "" ? undefined : Number(e.target.value) })
                }
                className="input"
              />
            </div>
            <div>
              <label htmlFor="profile-alcohol" className="label">
                Rượu bia
              </label>
              <select
                id="profile-alcohol"
                value={lifestyle.alcohol ?? ""}
                onChange={(e) => setLifestyle({ ...lifestyle, alcohol: (e.target.value || undefined) as Lifestyle["alcohol"] })}
                className="input"
              >
                <option value="">Chưa cung cấp</option>
                <option value="none">Không uống</option>
                <option value="light">Ít (dưới 1 ly tiêu chuẩn/ngày)</option>
                <option value="heavy">Thường xuyên (từ 2 ly/ngày)</option>
              </select>
            </div>
            <div>
              <label htmlFor="profile-exercise" className="label">
                Vận động
              </label>
              <select
                id="profile-exercise"
                value={lifestyle.exercise ?? ""}
                onChange={(e) =>
                  setLifestyle({ ...lifestyle, exercise: (e.target.value || undefined) as Lifestyle["exercise"] })
                }
                className="input"
              >
                <option value="">Chưa cung cấp</option>
                <option value="none">Ít vận động</option>
                <option value="light">Nhẹ (dưới 3 buổi/tuần)</option>
                <option value="regular">Đều đặn (từ 150 phút/tuần)</option>
              </select>
            </div>
          </div>
        </section>

        {error && <InlineError message={error} />}
        {success && (
          <p role="status" className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
            <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden="true" />
            Đã lưu thông tin. Đang về trang tổng quan…
          </p>
        )}

        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" onClick={() => router.back()} className="btn-ghost">
            Huỷ
          </button>
          <button type="submit" disabled={saving || success} className="btn-primary">
            {saving ? (
              <>
                <span className="spinner" aria-hidden="true" />
                Đang lưu…
              </>
            ) : (
              "Lưu thông tin"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
