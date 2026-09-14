"""CLI: python scripts/ingest.py [--reset]"""

from __future__ import annotations

import argparse

from ai_core.rag.ingest import ingest

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--reset", action="store_true", help="xoá collection trước khi nạp")
    args = p.parse_args()
    n = ingest(reset=args.reset)
    print(f"Đã nạp {n} chunk vào vector store.")
