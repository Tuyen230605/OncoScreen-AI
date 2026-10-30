from datetime import UTC, datetime

from ai_core.agents.copilot import ClinicalCopilot
from ai_core.mock import MockAgent
from ai_core.schemas import CancerType, Gender, IntakeProfile, PatientProfile, PatientRecord, RecordEvent

NOW = datetime(2026, 10, 1, tzinfo=UTC)


def _record(**kw) -> PatientRecord:
    events = [
        RecordEvent(id="ev-consult", at=NOW, kind="consult.summary", summary="Tư vấn: nữ 45 tuổi, mẹ mắc ung thư vú."),
        RecordEvent(id="ev-appt", at=NOW, kind="appointment.requested", summary="Đặt lịch tầm soát ung thư vú."),
    ]
    base = dict(
        patient_id="p1",
        full_name="Trần Thị Lan",
        profile=PatientProfile(age=45, gender=Gender.female, genetics_history=["breast_cancer_mother"]),
        reason_for_visit="Tầm soát ung thư vú",
        events=events,
    )
    return PatientRecord(**{**base, **kw})


class _Model:
    def __init__(self, output):
        self.output = output

    def with_structured_output(self, _schema):
        model = self

        class _S:
            def invoke(self, _messages):
                return model.output

        return _S()


def test_brief_has_traceable_facts_suggestions_and_draft_plan():
    brief = MockAgent().build_brief(_record())
    assert {i for f in brief.key_facts for i in f.event_ids} <= {"ev-consult", "ev-appt"}
    assert {s.cancer_type for s in brief.guideline_suggestions} == {
        CancerType.breast,
        CancerType.cervical,
        CancerType.colorectal,
    }
    assert brief.draft_plan and all(item.sources and item.next_due is None for item in brief.draft_plan.items)
    assert any("gần nhất" in gap for gap in brief.data_gaps)
    assert [e["node"] for e in brief.trace_events] == [
        "load_record",
        "eligibility",
        "retrieve",
        "draft_brief",
        "draft_plan",
    ]


def test_red_flag_in_record_blocks_screening_plan():
    record = _record(intake=IntakeProfile(symptom_codes=["symptom_lump"]))
    brief = MockAgent().build_brief(record)
    assert brief.red_flags and brief.draft_plan is None


def test_llm_facts_with_unknown_event_ids_are_dropped(monkeypatch):
    monkeypatch.setattr(
        "ai_core.llm.get_chat_model",
        lambda: _Model(
            {
                "summary": "Bệnh nhân nữ 45 tuổi, mẹ mắc ung thư vú, đến tầm soát.",
                "key_facts": [
                    {"text": "Mẹ mắc ung thư vú", "event_ids": ["ev-consult"]},
                    {"text": "Có đột biến BRCA1", "event_ids": ["ev-invented"]},
                ],
                "questions_to_clarify": ["Mẹ phát hiện bệnh ở tuổi nào?"],
            }
        ),
    )
    brief = ClinicalCopilot(use_llm=True, dense=False).build_brief(_record())
    assert [f.text for f in brief.key_facts] == ["Mẹ mắc ung thư vú"]
    assert brief.questions_to_clarify[0] == "Mẹ phát hiện bệnh ở tuổi nào?"


def test_llm_summary_with_diagnosis_falls_back(monkeypatch):
    monkeypatch.setattr(
        "ai_core.llm.get_chat_model",
        lambda: _Model({"summary": "Bệnh nhân bị ung thư vú.", "key_facts": [], "questions_to_clarify": []}),
    )
    brief = ClinicalCopilot(use_llm=True, dense=False).build_brief(_record())
    assert "bị ung thư" not in brief.summary and brief.trace_events[3]["generator"] == "template_fallback"


def test_copilot_qa_cites_record_and_guidelines_and_refuses_diagnosis():
    agent = MockAgent()
    answer = agent.ask_copilot("Guideline nhũ ảnh cho phụ nữ 45 tuổi?", _record(), [])
    assert answer.sources and not answer.insufficient_evidence
    refused = agent.ask_copilot("Bệnh nhân có bị ung thư không?", _record(), [])
    assert refused.insufficient_evidence and not refused.sources


# --------------------------------------------------------------------------- hồi quy (review ai_core)


def test_llm_facts_and_questions_go_through_output_guards(monkeypatch):
    monkeypatch.setattr(
        "ai_core.llm.get_chat_model",
        lambda: _Model(
            {
                "summary": "Bệnh nhân nữ 45 tuổi, mẹ mắc ung thư vú, đến tầm soát.",
                "key_facts": [
                    {"text": "Mẹ mắc ung thư vú", "event_ids": ["ev-consult"]},
                    {"text": "PSA 12 ng/mL ngày 2024-03-01, tăng cao", "event_ids": ["ev-consult"]},  # số bịa
                ],
                "questions_to_clarify": [
                    "Mẹ phát hiện bệnh ở tuổi nào?",
                    "Khả năng cao là ung thư vú, cần hoá trị không?",  # chẩn đoán + điều trị
                    "Nên phẫu thuật cắt bỏ trước không?",  # tư vấn điều trị
                ],
            }
        ),
    )
    brief = ClinicalCopilot(use_llm=True, dense=False).build_brief(_record())
    assert [f.text for f in brief.key_facts] == ["Mẹ mắc ung thư vú"]
    assert "Mẹ phát hiện bệnh ở tuổi nào?" in brief.questions_to_clarify
    assert not any("hoá trị" in q or "phẫu thuật" in q for q in brief.questions_to_clarify)
    draft_brief = next(e for e in brief.trace_events if e["node"] == "draft_brief")
    assert draft_brief["facts_dropped"] == 1 and draft_brief["questions_dropped"] == 2


def test_red_flag_in_reason_or_record_text_blocks_routine_plan():
    by_reason = MockAgent().build_brief(_record(reason_for_visit="Sờ thấy khối u ở vú trái 2 tuần nay"))
    assert [f.code for f in by_reason.red_flags] == ["symptom_lump"] and by_reason.draft_plan is None
    assert any("dấu hiệu cảnh báo" in gap for gap in by_reason.data_gaps)
    events = [RecordEvent(id="ev-c", at=NOW, kind="consult.summary", summary="Người bệnh kể đi ngoài ra máu 1 tháng")]
    by_event = MockAgent().build_brief(_record(events=events))
    assert by_event.red_flags and by_event.draft_plan is None


def test_copilot_qa_insufficient_evidence_does_not_return_llm_text(monkeypatch):
    text = "Có lẽ nên làm thêm MRI vú."
    monkeypatch.setattr(
        "ai_core.llm.get_chat_model", lambda: _Model({"answer": text, "insufficient_evidence": True})
    )
    answer = ClinicalCopilot(use_llm=True, dense=False).ask("Guideline nhũ ảnh cho phụ nữ 45 tuổi?", _record(), [])
    assert answer.insufficient_evidence and text not in answer.answer
