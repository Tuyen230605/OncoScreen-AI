"""CLI tiện ích.

python -m ai_core.cli demo [--real] [--case breast|lung|red-flag|ask]
python -m ai_core.cli eval [--real]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime

from ai_core.api import get_agent
from ai_core.schemas import Answer, IntakeProfile, PatientRecord, RecordEvent

CASES: dict[str, dict] = {
    "breast": {"message": "Tôi là nữ 45 tuổi, mẹ tôi bị ung thư vú. Tôi nên tầm soát gì?"},
    "lung": {
        "message": None,
        "answers": [
            Answer(question_id="age", value=55),
            Answer(question_id="gender", value="Nam"),
            Answer(question_id="smoking", value=True),
            Answer(question_id="pack_years", value=30),
        ],
    },
    "red-flag": {"message": "Em 38 tuổi, mấy hôm nay sờ thấy một khối cứng ở vú trái."},
    "ask": {"message": "Chụp nhũ ảnh bao lâu một lần?"},
}


def demo(real: bool, case: str) -> None:
    agent = get_agent(force_mock=not real)
    spec = CASES[case]
    reply = agent.navigate(
        message=spec.get("message"), answers=spec.get("answers", []), intake=IntakeProfile(), history=[]
    )
    print(f"agent = {agent.name}")
    print("=== Navigator ===")
    print(json.dumps(reply.model_dump(mode="json"), ensure_ascii=False, indent=2))
    if reply.next_action.value == "continue_chat":
        return
    now = datetime.now(UTC)
    record = PatientRecord(
        patient_id="demo",
        full_name="Bệnh nhân demo",
        intake=reply.intake,
        reason_for_visit=reply.booking_hint.reason if reply.booking_hint else None,
        events=[RecordEvent(id="e1", at=now, kind="consult.summary", summary=reply.reply.split("\n")[0])],
    )
    print("=== Clinical Copilot brief ===")
    print(json.dumps(agent.build_brief(record).model_dump(mode="json"), ensure_ascii=False, indent=2))


def ensure_utf8_output() -> None:
    """Console Windows mặc định là cp1252/cp437 → in tiếng Việt sẽ UnicodeEncodeError."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure") and (stream.encoding or "").lower().replace("-", "") != "utf8":
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    ensure_utf8_output()
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo")
    d.add_argument("--real", action="store_true")
    d.add_argument("--case", choices=tuple(CASES), default="breast")
    e = sub.add_parser("eval")
    e.add_argument("--real", action="store_true")
    args = parser.parse_args()
    if args.cmd == "demo":
        demo(args.real, args.case)
    else:
        from ai_core.evaluation import print_report, run_navigator_eval

        print_report(run_navigator_eval(get_agent(force_mock=not args.real)))
