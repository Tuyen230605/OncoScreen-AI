import math
import unicodedata
from datetime import date

import pytest

from ai_core.schemas import Answer, CancerType, Gender, IntakeProfile, PatientProfile
from ai_core.tools.intake import from_answers, from_profile, from_text, merge, missing_info


def test_extracts_age_gender_family_history():
    intake = from_text(IntakeProfile(), "Tôi là nữ 45 tuổi, mẹ tôi bị ung thư vú")
    assert intake.age == 45 and intake.gender == Gender.female
    assert intake.family_history == [CancerType.breast]
    assert intake.personal_cancer_history is None


def test_relative_age_is_not_user_age():
    intake = from_text(IntakeProfile(), "Mẹ tôi 70 tuổi bị ung thư đại tràng")
    assert intake.age is None
    assert intake.family_history == [CancerType.colorectal]


def test_relative_age_in_other_clause_is_not_user_age():
    intake = from_text(IntakeProfile(), "Bố tôi mất năm 60 tuổi vì ung thư phổi")
    assert intake.age is None and intake.family_history == [CancerType.lung]
    intake = from_text(IntakeProfile(), "Mẹ 70 tuổi bị ung thư vú, tôi là nữ 40 tuổi")
    assert intake.age == 40 and intake.gender == Gender.female
    assert from_text(IntakeProfile(), "Tôi đã bỏ thuốc lá và năm nay 62 tuổi").age == 62


def test_personal_history_and_birth_year():
    intake = from_text(IntakeProfile(), "Sinh năm 1976, nữ, đã từng bị ung thư vú", today=date(2026, 10, 27))
    assert intake.age == 50 and intake.personal_cancer_history is True


def test_smoking_pack_years_and_hepatitis():
    intake = from_text(IntakeProfile(), "Tôi nam 55 tuổi, hút thuốc 1 gói mỗi ngày trong 30 năm, bị viêm gan B")
    assert intake.gender == Gender.male and intake.smoking is True
    assert intake.pack_years == 30 and intake.hepatitis_b_or_c is True
    assert from_text(IntakeProfile(), "Tôi không hút thuốc").smoking is False


def test_answers_map_to_intake_and_keep_red_flag_codes():
    intake = from_answers(
        IntakeProfile(symptom_codes=["symptom_lump"]),
        [
            Answer(question_id="age", value="52"),
            Answer(question_id="gender", value="Nam"),
            Answer(question_id="family_history", value=["Ung thư phổi", "Khác"]),
            Answer(question_id="symptom_lump", value=False),
        ],
    )
    assert intake.age == 52 and intake.gender == Gender.male
    assert intake.family_history == [CancerType.lung, CancerType.other]
    assert intake.symptom_codes == ["symptom_lump"]  # cờ đã ghi nhận không bị gỡ


def test_missing_info_and_merge():
    assert missing_info(IntakeProfile()) == ["age", "gender"]
    assert "pack_years" in missing_info(IntakeProfile(age=60, gender=Gender.male, smoking=True))
    merged = merge(
        IntakeProfile(age=40), IntakeProfile(age=50, gender=Gender.female, family_history=[CancerType.breast])
    )
    assert merged.age == 40 and merged.gender == Gender.female and merged.family_history == [CancerType.breast]


def test_profile_codes_map_to_family_history():
    intake = from_profile(PatientProfile(age=45, gender=Gender.female, genetics_history=["breast_cancer_mother"]))
    assert intake.family_history == [CancerType.breast]


# --------------------------------------------------------------------------- hồi quy (review ai_core)


@pytest.mark.parametrize(
    "text",
    [
        "Tôi nữ 45 tuổi, tôi sợ bị ung thư vú",
        "Tôi lo mình mắc ung thư",
        "Tôi nam 60 tuổi, có nguy cơ mắc ung thư phổi không?",
        "Tôi nữ 50 tuổi. Tôi có bị ung thư vú không?",
    ],
)
def test_worry_or_question_is_not_personal_cancer_history(text):
    assert from_text(IntakeProfile(), text).personal_cancer_history is None


def test_explicit_negation_resets_personal_history():
    reset = from_text(IntakeProfile(personal_cancer_history=True), "Tôi chưa từng bị ung thư")
    assert reset.personal_cancer_history is False
    assert from_text(IntakeProfile(), "Tôi đã từng được chẩn đoán ung thư tuyến giáp").personal_cancer_history is True


@pytest.mark.parametrize(
    "text",
    [
        "Tôi nữ 45 tuổi. Tầm soát ung thư vú có cần thiết không?",
        "Tôi nam 50 tuổi, muốn đi tầm soát ung thư đại trực tràng",
        "Gia đình tôi không ai bị ung thư gan",
    ],
)
def test_generic_cancer_mentions_are_not_family_history(text):
    assert from_text(IntakeProfile(), text).family_history == []


def test_family_history_requires_a_relative_subject():
    assert from_text(IntakeProfile(), "Tôi có mẹ bị ung thư vú").family_history == [CancerType.breast]
    intake = from_text(IntakeProfile(), "Tôi không bị ung thư nhưng mẹ tôi bị ung thư vú")
    assert intake.family_history == [CancerType.breast] and intake.personal_cancer_history is False


def test_generic_question_does_not_overwrite_known_age_or_gender():
    base = IntakeProfile(age=55, gender=Gender.female)
    assert from_text(base, "Phụ nữ trên 21 tuổi có cần làm Pap không?").age == 55
    assert from_text(base, "Nam giới có cần tầm soát ung thư vú không?").gender == Gender.female
    assert from_text(IntakeProfile(age=60), "Tầm soát đại trực tràng bắt đầu từ 45 tuổi phải không?").age == 60
    assert from_text(IntakeProfile(age=45), "Xin lỗi, tôi 46 tuổi").age == 46  # tự nêu → được sửa


def test_unaccented_gender_and_relative_age():
    intake = from_text(IntakeProfile(), "toi la nam, 60 tuoi")
    assert intake.gender == Gender.male and intake.age == 60
    assert from_text(IntakeProfile(), "toi nam nay 60 tuoi").gender is None  # "năm nay", không phải "nam"
    intake = from_text(IntakeProfile(), "Con gái tôi 25 tuổi có nên tầm soát cổ tử cung không, tôi là nữ")
    assert intake.age is None and intake.gender == Gender.female


def test_relatives_risk_factors_are_not_the_users():
    intake = from_text(IntakeProfile(), "Tôi nữ 55 tuổi, chồng tôi hút thuốc 1 gói mỗi ngày đã 30 năm")
    assert intake.smoking is None and intake.pack_years is None
    assert from_text(IntakeProfile(), "Tôi nam 30 tuổi, mẹ tôi bị viêm gan B").hepatitis_b_or_c is None
    assert from_text(IntakeProfile(), "Bố tôi bị xơ gan").cirrhosis is None
    assert from_text(IntakeProfile(), "Tôi bị xơ gan").cirrhosis is True
    assert from_text(IntakeProfile(), "Tôi hút thuốc thụ động ở công ty").smoking is None


def test_vaccination_or_uncertainty_is_not_hepatitis():
    assert from_text(IntakeProfile(), "Tôi nam 30 tuổi, đã tiêm vắc xin viêm gan B đầy đủ").hepatitis_b_or_c is None
    assert from_text(IntakeProfile(), "Tôi không biết có bị viêm gan B không").hepatitis_b_or_c is None
    assert from_text(IntakeProfile(), "Tôi chưa được tiêm HPV").hpv_vaccinated is False


def test_quit_more_than_15_years_is_not_current_smoking():
    intake = from_text(IntakeProfile(), "Tôi nam 65 tuổi, đã cai thuốc 25 năm, trước đây hút 30 gói-năm")
    assert intake.smoking is False and intake.pack_years == 30
    assert from_text(IntakeProfile(), "Tôi bỏ thuốc lá được 10 năm, trước hút 30 gói-năm").smoking is True


@pytest.mark.parametrize("value", [-5, "nan", "inf", float("nan"), "abc"])
def test_invalid_numeric_answers_are_ignored(value):
    intake = from_answers(IntakeProfile(pack_years=12), [Answer(question_id="pack_years", value=value)])
    assert intake.pack_years == 12 and not math.isnan(intake.pack_years)


def test_answers_are_nfc_normalized():
    intake = from_answers(
        IntakeProfile(),
        [
            Answer(question_id="gender", value=unicodedata.normalize("NFD", "Nữ")),
            Answer(question_id="family_history", value=[unicodedata.normalize("NFD", "Ung thư vú")]),
        ],
    )
    assert intake.gender == Gender.female and intake.family_history == [CancerType.breast]
