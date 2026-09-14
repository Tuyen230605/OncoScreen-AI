from ai_core.schemas import Answer
from ai_core.tools.red_flag_detector import detect_red_flags


def test_detects_lump():
    r = detect_red_flags([Answer(question_id="symptom_lump", value=True)])
    assert r.detected and r.flags[0].code == "symptom_lump"
    assert r.flags[0].severity.value == "urgent"


def test_string_truthy_values():
    assert detect_red_flags([Answer(question_id="symptom_bleeding", value="yes")]).detected
    assert detect_red_flags([Answer(question_id="symptom_bleeding", value="có")]).detected


def test_no_false_positive():
    answers = [
        Answer(question_id="symptom_lump", value=False),
        Answer(question_id="symptom_bleeding", value="no"),
        Answer(question_id="smoking", value=True),
    ]
    assert not detect_red_flags(answers).detected


def test_urgent_sorted_first():
    r = detect_red_flags(
        [Answer(question_id="symptom_weight_loss", value=True), Answer(question_id="symptom_lump", value=True)]
    )
    assert [f.severity.value for f in r.flags] == ["urgent", "soon"]
