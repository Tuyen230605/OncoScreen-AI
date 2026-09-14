"""Tool: recall reminder — sinh nội dung nhắc lịch (backend scheduler gọi khi reminder đến hạn)."""

from __future__ import annotations

from datetime import date

from ai_core.schemas import CancerType

_LABEL = {
    CancerType.breast: "ung thư vú",
    CancerType.cervical: "ung thư cổ tử cung",
    CancerType.colorectal: "ung thư đại trực tràng",
    CancerType.liver: "ung thư gan",
    CancerType.lung: "ung thư phổi",
    CancerType.prostate: "ung thư tuyến tiền liệt",
    CancerType.other: "sức khoẻ tổng quát",
}


def build_reminder_message(
    cancer_type: CancerType, method: str, due_date: date, patient_name: str | None = None
) -> str:
    who = f"{patient_name}, " if patient_name else ""
    return (
        f"{who}đã đến lịch tầm soát {_LABEL.get(cancer_type, cancer_type.value)} "
        f"({method}) — dự kiến {due_date:%d/%m/%Y}. Hãy liên hệ cơ sở y tế để đặt lịch. "
        "Đây là nhắc nhở theo kế hoạch bác sĩ đã duyệt, không phải chẩn đoán."
    )
