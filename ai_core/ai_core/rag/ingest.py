"""Ingest: data/guidelines/*.md (frontmatter metadata) → chunk → Chroma collection `guidelines`.

TODO(Tuyền): chunk theo heading (## ...), ~500 token; giữ metadata frontmatter + `section` + `doc_id` (= tên file).
"""

from __future__ import annotations

from pathlib import Path

import chromadb
import frontmatter

from ai_core.config import DATA_DIR, settings
from ai_core.rag.embeddings import get_embedding_function

COLLECTION = "guidelines"


def get_collection(reset: bool = False):
    client = chromadb.PersistentClient(path=str(settings.vector_store_dir))
    if reset:
        try:
            client.delete_collection(COLLECTION)
        except Exception:  # noqa: BLE001
            pass
    return client.get_or_create_collection(COLLECTION, embedding_function=get_embedding_function())


def chunk_markdown(doc_id: str, meta: dict, body: str) -> list[tuple[str, str, dict]]:
    """Trả list (chunk_id, text, metadata). Tạm thời: 1 chunk / heading cấp 2."""
    chunks: list[tuple[str, str, dict]] = []
    section = "intro"
    buf: list[str] = []

    def flush() -> None:
        text = "\n".join(buf).strip()
        if text:
            chunks.append((f"{doc_id}::{len(chunks)}", text, {**meta, "doc_id": doc_id, "section": section}))

    for line in body.splitlines():
        if line.startswith("## "):
            flush()
            buf = []
            section = line[3:].strip()
        buf.append(line)
    flush()
    return chunks


def ingest(guidelines_dir: Path | None = None, reset: bool = False) -> int:
    guidelines_dir = guidelines_dir or DATA_DIR / "guidelines"
    col = get_collection(reset=reset)
    total = 0
    for path in sorted(guidelines_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        post = frontmatter.load(path, encoding="utf-8")
        meta = {k: (v if isinstance(v, (str, int, float, bool)) else str(v)) for k, v in post.metadata.items()}
        chunks = chunk_markdown(path.stem, meta, post.content)
        if chunks:
            col.upsert(ids=[c[0] for c in chunks], documents=[c[1] for c in chunks], metadatas=[c[2] for c in chunks])
            total += len(chunks)
    return total
