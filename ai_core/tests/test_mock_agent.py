from ai_core.api import get_agent
from ai_core.schemas import Answer, Gender, PatientContext, PatientProfile, ScreeningResult


def _ctx(**profile_kw):
    profile = PatientProfile(**{"age": 45, "gender": Gender.female, **profile_kw})
    return PatientContext(session_id="s1", profile=profile, answers=[])


def test_mock_returns_pending_review_with_plan():
    agent = get_agent(force_mock=True)
    res = agent.run_screening(_ctx(genetics_history=["breast_cancer_mother"]))
    assert isinstance(res, ScreeningResult)
    assert res.status == "pending_review"
    assert res.draft_plan and res.draft_plan.items
    assert all(item.sources for item in res.draft_plan.items)
    assert res.disclaimer


def test_mock_red_flag_stops_flow():
    agent = get_agent(force_mock=True)
    ctx = _ctx()
    ctx.answers.append(Answer(question_id="symptom_lump", value=True))
    res = agent.run_screening(ctx)
    assert res.status == "red_flag" and res.draft_plan is None and res.red_flag and res.red_flag.detected


def test_questionnaire_filters_gender():
    agent = get_agent(force_mock=True)
    male = agent.get_questionnaire(PatientProfile(age=50, gender=Gender.male))
    assert all(not q.id.startswith("f_") for q in male.questions)


def test_missing_questions_respects_depends_on():
    agent = get_agent(force_mock=True)
    profile = PatientProfile(age=50, gender=Gender.male)
    missing = agent.missing_questions(profile, [Answer(question_id="smoking", value=False)])
    assert "pack_years" not in missing
    missing2 = agent.missing_questions(profile, [Answer(question_id="smoking", value=True)])
    assert "pack_years" in missing2
