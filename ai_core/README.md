# ai_core — Module 1: AI Core & Data

Owner: **Tuyền**. Hướng dẫn chi tiết: [docs/guides/GUIDE_AI_CORE.md](../docs/guides/GUIDE_AI_CORE.md).
Contract: [docs/protocols/AI_CORE_CONTRACT.md](../docs/protocols/AI_CORE_CONTRACT.md) ⇄ `ai_core/schemas.py`.
Bản đồ từng file, node, use case và extension IDE: [FILE_MAP.md](FILE_MAP.md).

```bash
pip install -e ".[dev,local-embed]"
pytest -q
python -m ai_core.cli demo          # MockAgent
python scripts/ingest.py            # nạp data/guidelines → Chroma
python -m ai_core.cli demo --real   # agent thật (cần LLM key + đã ingest)
```

Backend chỉ import: `ai_core.api`, `ai_core.schemas`.
