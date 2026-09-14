"""Retriever: lọc metadata trước (gender, tuổi) rồi similarity search → list[Source]."""

from __future__ import annotations

from ai_core.rag.ingest import get_collection
from ai_core.schemas import PatientProfile, RiskAssessment, Source


def retrieve_sources(profile: PatientProfile, risk: RiskAssessment | None, k: int = 6) -> list[Source]:
    col = get_collection()
    query = _build_query(profile, risk)
    where = {"$or": [{"gender": profile.gender.value}, {"gender": "any"}]}
    # TODO(Tuyền): thêm điều kiện min_age <= age <= max_age (Chroma hỗ trợ $and/$lte/$gte),
    #              ưu tiên cancer_type có trong risk.factors, dedupe theo doc_id.
    res = col.query(query_texts=[query], n_results=k, where=where)
    sources: list[Source] = []
    for doc, meta in zip(res["documents"][0], res["metadatas"][0], strict=True):
        sources.append(
            Source(
                doc_id=str(meta.get("doc_id")),
                title=str(meta.get("source", meta.get("doc_id"))),
                section=meta.get("section"),
                excerpt=doc[:600],
                url=meta.get("url"),
            )
        )
    return sources


def _build_query(profile: PatientProfile, risk: RiskAssessment | None) -> str:
    parts = [f"tầm soát ung thư cho {profile.gender.value} {profile.age} tuổi"]
    if risk:
        parts += [f"{f.cancer_type.value} nguy cơ {f.level.value}" for f in risk.factors]
    if profile.genetics_history:
        parts.append("tiền sử gia đình: " + ", ".join(profile.genetics_history))
    return "; ".join(parts)
