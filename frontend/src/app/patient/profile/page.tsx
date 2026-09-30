"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Gender, Lifestyle, PatientProfileIn, PatientProfileOut } from "@/types/api";

/** Màn nhập / cập nhật hồ sơ bệnh nhân. Gọi PUT /patients/me/profile khi submit. */
export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  // Form state — khởi tạo từ profile hiện tại
  const [age, setAge] = useState<number | "">(0);
  const [gender, setGender] = useState<Gender>("female");
  const [geneticsHistory, setGeneticsHistory] = useState<string[]>([]);
  const [geneticsInput, setGeneticsInput] = useState("");
  const [lifestyle, setLifestyle] = useState<Lifestyle>({});

  useEffect(() => {
    api
      .getProfile()
      .then((p: PatientProfileOut) => {
        setAge(p.age ?? "");
        setGender(p.gender ?? "female");
        setGeneticsHistory(p.genetics_history ?? []);
        setLifestyle(p.lifestyle ?? {});
      })
      .catch(() => {
        // Hồ sơ chưa có — form trống, không báo lỗi
      })
      .finally(() => setLoading(false));
  }, []);

  function addGenetics() {
    const val = geneticsInput.trim();
    if (val && !geneticsHistory.includes(val)) {
      setGeneticsHistory([...geneticsHistory, val]);
    }
    setGeneticsInput("");
  }

  function removeGenetics(item: string) {
    setGeneticsHistory(geneticsHistory.filter((g) => g !== item));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!age || age < 18 || age > 120) {
      setError("Tuổi phải từ 18 đến 120.");
      return;
    }
    
    let computedBmi = lifestyle.bmi;
    if (lifestyle.height_cm && lifestyle.weight_kg) {
      const h = lifestyle.height_cm / 100;
      computedBmi = Number((lifestyle.weight_kg / (h * h)).toFixed(1));
    }

    const payload: PatientProfileIn = {
      age: Number(age),
      gender,
      genetics_history: geneticsHistory,
      lifestyle: {
        ...lifestyle,
        bmi: computedBmi
      },
    };
    try {
      setSaving(true);
      setError("");
      await api.putProfile(payload);
      setSuccess(true);
      setTimeout(() => router.push("/patient"), 1200);
    } catch {
      setError("Lưu hồ sơ thất bại. Vui lòng thử lại.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <span className="spinner h-6 w-6 text-blue-500" aria-label="Đang tải…" />
      </div>
    );
  }

  return (
    <div className="fade-in mx-auto max-w-2xl">
      <header className="mb-6">
        <h1 className="page-title">Hồ sơ sức khỏe</h1>
        <p className="page-subtitle">Thông tin này giúp hệ thống đề xuất kế hoạch tầm soát phù hợp với bạn.</p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        {/* ===== Thông tin cơ bản ===== */}
        <section className="card-padded space-y-4">
          <h2 className="font-semibold text-slate-800">Thông tin cơ bản</h2>

          <div className="grid gap-4 sm:grid-cols-2">
            {/* Tuổi */}
            <div>
              <label htmlFor="profile-age" className="label">
                Tuổi <span className="text-red-500">*</span>
              </label>
              <input
                id="profile-age"
                type="number"
                min={18}
                max={120}
                required
                value={age}
                onChange={(e) => setAge(e.target.value === "" ? "" : Number(e.target.value))}
                className="input"
                placeholder="Ví dụ: 45"
              />
            </div>

            {/* Giới tính */}
            <div>
              <label htmlFor="profile-gender" className="label">
                Giới tính <span className="text-red-500">*</span>
              </label>
              <select
                id="profile-gender"
                value={gender}
                onChange={(e) => setGender(e.target.value as Gender)}
                className="input"
              >
                <option value="female">Nữ</option>
                <option value="male">Nam</option>
                <option value="other">Khác</option>
              </select>
            </div>
          </div>
        </section>

        {/* ===== Tiền sử gia đình ===== */}
        <section className="card-padded space-y-3">
          <h2 className="font-semibold text-slate-800">Tiền sử gia đình</h2>
          <p className="text-sm text-slate-500">Thêm các loại ung thư mà người thân trong gia đình từng mắc.</p>

          {/* Input thêm mới */}
          <div className="flex gap-2">
            <input
              id="profile-genetics-input"
              type="text"
              value={geneticsInput}
              onChange={(e) => setGeneticsInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addGenetics(); } }}
              className="input flex-1"
              placeholder="Ví dụ: breast_cancer_mother"
            />
            <button type="button" onClick={addGenetics} className="btn-secondary shrink-0">
              Thêm
            </button>
          </div>

          {/* Tags đã thêm */}
          {geneticsHistory.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {geneticsHistory.map((g) => (
                <span
                  key={g}
                  className="badge bg-blue-100 text-blue-800"
                >
                  {g}
                  <button
                    type="button"
                    onClick={() => removeGenetics(g)}
                    className="ml-1.5 text-blue-600 hover:text-blue-900"
                    aria-label={`Xóa ${g}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
          {geneticsHistory.length === 0 && (
            <p className="text-sm text-slate-400">Chưa có thông tin tiền sử gia đình.</p>
          )}
        </section>

        {/* ===== Lối sống ===== */}
        <section className="card-padded space-y-4">
          <h2 className="font-semibold text-slate-800">Lối sống</h2>

          <div className="grid gap-4 sm:grid-cols-2">
            {/* Hút thuốc */}
            <div>
              <p className="label">Hút thuốc lá</p>
              <div className="mt-1 flex gap-4 text-sm">
                <label className="flex cursor-pointer items-center gap-1.5">
                  <input
                    type="radio"
                    name="smoking"
                    checked={lifestyle.smoking === true}
                    onChange={() => setLifestyle({ ...lifestyle, smoking: true })}
                    className="accent-blue-600"
                  />
                  Có
                </label>
                <label className="flex cursor-pointer items-center gap-1.5">
                  <input
                    type="radio"
                    name="smoking"
                    checked={lifestyle.smoking === false}
                    onChange={() => setLifestyle({ ...lifestyle, smoking: false, pack_years: undefined })}
                    className="accent-blue-600"
                  />
                  Không
                </label>
              </div>
            </div>

            {/* Số gói-năm — chỉ hiện khi có hút thuốc */}
            {lifestyle.smoking === true && (
              <div>
                <label htmlFor="profile-pack-years" className="label">
                  Số gói-năm ước tính
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
                  className="input"
                  placeholder="Ví dụ: 20"
                />
              </div>
            )}

            {/* Chiều cao & Cân nặng */}
            <div className="grid grid-cols-2 gap-4">
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
                  placeholder="Ví dụ: 165"
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
                  placeholder="Ví dụ: 60"
                />
              </div>
            </div>

            {/* Uống rượu */}
            <div>
              <label htmlFor="profile-alcohol" className="label">
                Mức độ uống rượu/bia
              </label>
              <select
                id="profile-alcohol"
                value={lifestyle.alcohol ?? ""}
                onChange={(e) =>
                  setLifestyle({ ...lifestyle, alcohol: (e.target.value || undefined) as Lifestyle["alcohol"] })
                }
                className="input"
              >
                <option value="">Chưa cung cấp</option>
                <option value="none">Không uống</option>
                <option value="light">Nhẹ (≤ 1 ly/ngày)</option>
                <option value="heavy">Nặng (≥ 2 ly/ngày)</option>
              </select>
            </div>

            {/* Vận động */}
            <div>
              <label htmlFor="profile-exercise" className="label">
                Mức độ vận động
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
                <option value="none">Không vận động</option>
                <option value="light">Nhẹ (đi bộ, &lt; 3 buổi/tuần)</option>
                <option value="regular">Đều đặn (≥ 3 buổi/tuần)</option>
              </select>
            </div>
          </div>
        </section>

        {/* Lỗi / Thành công */}
        {error && (
          <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}
        {success && (
          <p role="status" className="rounded-lg bg-green-50 p-3 text-sm text-green-700">
            ✓ Đã lưu hồ sơ thành công! Đang chuyển hướng…
          </p>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => router.back()} className="btn-secondary">
            Hủy
          </button>
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? <span className="spinner h-4 w-4" /> : null}
            {saving ? "Đang lưu…" : "Lưu hồ sơ"}
          </button>
        </div>
      </form>
    </div>
  );
}
