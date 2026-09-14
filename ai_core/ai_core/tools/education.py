"""Tool: education content theo loại ung thư. TODO(Tuyền): lấy từ data/guidelines (section 'Dấu hiệu cảnh báo')."""

from __future__ import annotations

from ai_core.schemas import CancerType, EducationContent


def get_education_content(cancer_type: CancerType) -> EducationContent:
    raise NotImplementedError("TODO(Tuyền): education.get_education_content")
