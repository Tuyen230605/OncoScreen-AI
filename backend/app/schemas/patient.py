from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from ai_core.schemas import Gender
from pydantic import BaseModel, Field


class Lifestyle(BaseModel):
    """Mirror `Lifestyle` (frontend/src/types/api.ts): trường đã biết được kiểm tra kiểu/miền giá trị
    (đầu vào cho Navigator/Copilot), trường khác giữ nguyên."""

    model_config = {"extra": "allow"}

    smoking: bool | None = None
    pack_years: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    hepatitis_b_or_c: bool | None = None
    cirrhosis: bool | None = None
    alcohol: Literal["none", "light", "heavy"] | None = None
    height_cm: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    weight_kg: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    bmi: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    exercise: Literal["none", "light", "regular"] | None = None


class PatientProfileIn(BaseModel):
    age: int = Field(ge=0, le=120)
    gender: Gender
    genetics_history: list[str] = Field(default_factory=list)
    lifestyle: Lifestyle = Field(default_factory=Lifestyle)


class PatientProfileOut(PatientProfileIn):
    user_id: str
    lifestyle: dict[str, Any] = Field(default_factory=dict)  # dữ liệu đã lưu, trả nguyên dạng
    lifestyle_score: float | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}
