import unicodedata

import pytest

from ai_core.schemas import Answer
from ai_core.tools.red_flag_detector import codes_from_text, detect_red_flags, relative_codes_from_text


def test_detects_lump_from_answers():
    r = detect_red_flags([Answer(question_id="symptom_lump", value=True)])
    assert r.detected and r.flags[0].code == "symptom_lump"
    assert r.flags[0].severity.value == "urgent"


def test_string_truthy_values():
    assert detect_red_flags([Answer(question_id="symptom_bleeding", value="yes")]).detected
    assert detect_red_flags([Answer(question_id="symptom_bleeding", value="có")]).detected


def test_no_false_positive_from_answers():
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


def test_free_text_with_and_without_diacritics():
    assert codes_from_text("Mấy hôm nay em sờ thấy một khối cứng ở vú") == ["symptom_lump"]
    assert codes_from_text("toi so thay cuc o co") == ["symptom_lump"]
    assert codes_from_text("Dạo này đi ngoài ra máu") == ["symptom_bleeding"]
    assert "symptom_weight_loss" in codes_from_text("Tôi sụt 6kg trong 2 tháng")


def test_free_text_negation_is_ignored():
    assert codes_from_text("Tôi không sờ thấy khối u nào") == []
    assert codes_from_text("Không bị ho ra máu") == []


def test_free_text_in_other_symptoms_answer():
    r = detect_red_flags([Answer(question_id="other_symptoms", value="Gần đây bị vàng da")])
    assert r.detected and r.flags[0].code == "symptom_jaundice"


# --------------------------------------------------------------------------- hồi quy (review ai_core)


@pytest.mark.parametrize(
    ("text", "code"),
    [
        # "không biết…" không phủ định triệu chứng đứng sau
        ("Không biết đi ngoài ra máu có nguy hiểm không?", "symptom_bleeding"),
        ("Không những ho ra máu mà tôi còn mệt", "symptom_bleeding"),
        ("Tôi 55 tuổi đã mãn kinh nhưng bị chảy máu âm đạo", "symptom_bleeding"),
        ("Ra máu sau mãn kinh", "symptom_bleeding"),
        ("Tôi khạc ra máu mấy ngày nay", "symptom_bleeding"),
        ("Đại tiện ra máu", "symptom_bleeding"),
        ("Tôi thấy có một cục ở vú trái", "symptom_lump"),
        ("Vú trái của tôi có cục, sờ vào hơi cứng", "symptom_lump"),
        ("Tôi bị giảm 7kg trong 2 tháng mà không ăn kiêng", "symptom_weight_loss"),
        ("Đau bụng kéo dài 2 tháng nay", "symptom_persistent_pain"),
        ("ho​ ra máu", "symptom_bleeding"),  # ký tự zero-width
        ("không đau nhưng sờ thấy khối ở vú", "symptom_lump"),
        ("khong dau nhung so thay khoi o vu", "symptom_lump"),
    ],
)
def test_free_text_phrasings_are_detected(text, code):
    assert code in codes_from_text(text)


def test_relative_symptoms_are_not_the_users_red_flag():
    text = "Tôi nữ 45 tuổi, mẹ tôi sờ thấy khối u ở vú"
    assert codes_from_text(text) == []
    assert relative_codes_from_text(text) == ["symptom_lump"]
    assert codes_from_text("Mẹ tôi khoẻ nhưng tôi sờ thấy khối ở vú") == ["symptom_lump"]
    # chủ ngữ bị lược ở mệnh đề sau → coi là chính người nói (an toàn)
    assert codes_from_text("Bố tôi hút thuốc, gần đây ho ra máu") == ["symptom_bleeding"]


def test_homographs_and_generic_questions_are_not_red_flags():
    for text in [
        "Tôi vắng mặt buổi khám trước, nữ 45 tuổi",
        "toi vang mat buoi kham",
        "Nhũ ảnh có thể phát hiện khối u nhỏ không?",
        "Tôi muốn giảm 5kg",
        "Tôi chưa thấy có cục gì",
        "Tôi uống thuốc thấy khỏi hẳn",
        "Tôi là nữ 45 tuổi, không sờ thấy khối u nào, muốn biết nên tầm soát gì",
    ]:
        assert codes_from_text(text) == [], text
    assert codes_from_text("tôi bị vàng mắt") == ["symptom_jaundice"]


def test_nfd_encoded_truthy_answer():
    answer = Answer(question_id="symptom_lump", value=unicodedata.normalize("NFD", "Có"))
    assert detect_red_flags([answer]).detected
