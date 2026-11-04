"""Hybrid retriever: lọc metadata → BM25 (từ khoá) + vector (Chroma) → Reciprocal Rank Fusion → list[Source].

Vector store là tuỳ chọn: thiếu index/embedding thì tự hạ cấp về BM25 trên cùng kho chunk (graceful degradation),
trace ghi `mode=lexical` để quan sát được.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ai_core.config import settings
from ai_core.rag.corpus import Chunk, load_chunks
from ai_core.rag.lexical import BM25, tokenize
from ai_core.schemas import CancerType, Gender, Source

logger = logging.getLogger(__name__)
RRF_K = 60


@dataclass
class RetrievalResult:
    sources: list[Source]
    mode: str  # hybrid | lexical | empty
    dense_status: str  # ok | skipped | unavailable


def rrf(rankings: list[list[str]], k: int = RRF_K) -> dict[str, float]:
    """Reciprocal Rank Fusion: score(d) = Σ 1/(k + rank)."""
    fused: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            fused[item] = fused.get(item, 0.0) + 1.0 / (k + rank)
    return fused


def _age_applies(meta: dict, age: int) -> bool:
    return int(meta.get("min_age", 0)) <= age <= int(meta.get("max_age", 120))


def excluded_by_age(doc_id: str, age: int) -> bool:
    """True nếu guideline `doc_id` tồn tại nhưng nằm ngoài khoảng tuổi áp dụng."""
    meta = next((c.meta for c in load_chunks() if c.doc_id == doc_id), None)
    return meta is not None and not _age_applies(meta, age)


def _matches(chunk: Chunk, gender: Gender | None, age: int | None, cancer_types: set[CancerType] | None) -> bool:
    meta = chunk.meta
    if gender is not None and meta.get("gender") not in {gender.value, "any"}:
        return False
    if age is not None and not _age_applies(meta, age):
        return False
    if cancer_types and meta.get("cancer_type") not in {c.value for c in cancer_types} | {"other"}:
        return False
    return True


def gender_filter(gender: Gender | None) -> Gender | None:
    """Chỉ lọc theo giới khi biết rõ nam/nữ; `other` không loại nguồn nào (tránh bỏ sót nguồn áp dụng được)."""
    return gender if gender in {Gender.female, Gender.male} else None


def _dense_ids(query: str, gender: Gender | None, n: int) -> list[str]:
    import chromadb

    from ai_core.rag.embeddings import get_embedding_function
    from ai_core.rag.ingest import COLLECTION

    client = chromadb.PersistentClient(path=str(settings.vector_store_dir))
    if COLLECTION not in {c.name for c in client.list_collections()}:
        raise LookupError("collection chưa được ingest")
    col = client.get_collection(COLLECTION, embedding_function=get_embedding_function())
    count = col.count()
    if count == 0:
        raise LookupError("collection rỗng")
    where = {"$or": [{"gender": gender.value}, {"gender": "any"}]} if gender else None
    res = col.query(query_texts=[query], n_results=min(count, n), where=where)
    return list(res["ids"][0])


def retrieve(
    query: str,
    *,
    gender: Gender | None = None,
    age: int | None = None,
    cancer_types: set[CancerType] | None = None,
    k: int | None = None,
    dense: bool = True,
) -> RetrievalResult:
    k = k or settings.rag_top_k
    pool = [c for c in load_chunks() if _matches(c, gender, age, cancer_types)]
    if not pool or not query.strip():
        return RetrievalResult(sources=[], mode="empty", dense_status="skipped")
    by_id = {c.id: c for c in pool}

    bm25 = BM25([tokenize(c.text) for c in pool])
    scores = bm25.scores(tokenize(query))
    lexical = [c.id for c, s in sorted(zip(pool, scores, strict=True), key=lambda x: -x[1]) if s > 0][: k * 3]

    dense_ids: list[str] = []
    dense_status = "skipped"
    if dense:
        try:
            dense_ids = [i for i in _dense_ids(query, gender, k * 4) if i in by_id]
            dense_status = "ok"
        except Exception as exc:  # noqa: BLE001 — thiếu index/model: vẫn trả kết quả từ khoá
            logger.info("dense_retrieval_unavailable error_type=%s", type(exc).__name__)
            dense_status = "unavailable"

    fused = rrf([lexical, dense_ids] if dense_ids else [lexical])
    ranked = sorted(fused, key=lambda cid: -fused[cid])
    sources: list[Source] = []
    seen: set[tuple[str, str]] = set()
    for cid in ranked:
        chunk = by_id[cid]
        key = (chunk.doc_id, chunk.section)
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            Source(
                doc_id=chunk.doc_id,
                title=str(chunk.meta.get("source", chunk.doc_id)),
                section=chunk.section,
                excerpt=chunk.content[:800],
                url=chunk.meta.get("url"),
            )
        )
        if len(sources) >= k:
            break
    mode = "empty" if not sources else ("hybrid" if dense_ids else "lexical")
    return RetrievalResult(sources=sources, mode=mode, dense_status=dense_status)
