"""CLI tiện ích: `python -m ai_core.cli demo [--real]`."""

from __future__ import annotations

import argparse
import json

from ai_core.api import get_agent
from ai_core.schemas import Answer, Gender, PatientContext, PatientProfile


def demo(real: bool) -> None:
    agent = get_agent(force_mock=not real)
    profile = PatientProfile(age=45, gender=Gender.female, genetics_history=["breast_cancer_mother"])
    answers = [Answer(question_id="smoking", value=False), Answer(question_id="symptom_lump", value=False)]
    ctx = PatientContext(session_id="demo", profile=profile, answers=answers)
    print(f"agent = {agent.name}")
    print(json.dumps(agent.run_screening(ctx).model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo")
    d.add_argument("--real", action="store_true")
    args = parser.parse_args()
    if args.cmd == "demo":
        demo(args.real)
