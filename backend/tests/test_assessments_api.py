"""Assessments through the HTTP API: listing, attempts, answering, finishing,
history, statistics, language handling and the no-answer-leak guarantee."""

import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentKind, Question, QuestionDifficulty, QuestionType
from tests.factories import API, make_assessment, make_competency, make_question, register


def _start(client: TestClient, headers: dict[str, str], assessment, **params):
    return client.post(
        f"{API}/assessments/{assessment.id}/attempts", headers=headers, params=params
    )


def _answer(client: TestClient, headers, attempt_id, question_id, option_ids, **extra):
    return client.patch(
        f"{API}/attempts/{attempt_id}/responses/{question_id}",
        headers=headers,
        json={"option_ids": option_ids, **extra},
    )


def _finish(client: TestClient, headers, attempt_id, **params):
    return client.post(f"{API}/attempts/{attempt_id}/finish", headers=headers, params=params)


def _play(
    client: TestClient,
    headers: dict[str, str],
    assessment,
    questions: list[Question],
    n_correct: int,
):
    """Start, answer the first `n_correct` questions right (option b) and the
    rest wrong (option a), finish; returns the finished attempt body."""
    attempt = _start(client, headers, assessment).json()
    for index, item in enumerate(attempt["questions"]):
        _answer(client, headers, attempt["id"], item["id"], ["b"] if index < n_correct else ["a"])
    finished = _finish(client, headers, attempt["id"])
    assert finished.status_code == 200
    return finished.json()


def _profile(client: TestClient, headers: dict[str, str]) -> dict:
    return client.get(f"{API}/gamification/profile", headers=headers).json()


def _bank(db: Session, n: int = 4, **assessment_kwargs):
    competency, _ = make_competency(db, challenge_xp=[])
    questions = [make_question(db, competency, pt_br=True) for _ in range(n)]
    assessment = make_assessment(db, competency, questions, **assessment_kwargs)
    return competency, questions, assessment


class TestListing:
    def test_requires_authentication(self, client: TestClient):
        assert client.get(f"{API}/assessments").status_code == 401

    def test_lists_active_assessments_with_progress_fields(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, _, assessment = _bank(db, 3)
        make_assessment(db, competency, [], is_active=False)

        response = client.get(f"{API}/assessments", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["X-Total-Count"] == "1"
        (item,) = response.json()
        assert item["id"] == str(assessment.id)
        assert item["question_count"] == 3
        assert item["pass_threshold"] == 70
        assert item["competency_name"] == "Competency"
        assert item["attempts_completed"] == 0
        assert item["best_score_percent"] is None
        assert item["passed"] is False
        assert item["open_attempt_id"] is None

    def test_question_count_ignores_inactive_questions(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, questions, _ = _bank(db, 2)
        retired = make_question(db, competency, is_active=False)
        make_assessment(db, competency, [*questions, retired])
        counts = [
            i["question_count"]
            for i in client.get(f"{API}/assessments", headers=auth_headers).json()
        ]
        assert sorted(counts) == [2, 2]

    def test_filters_by_competency_and_both_routes_agree(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, _, assessment = _bank(db)
        _bank(db)
        by_filter = client.get(
            f"{API}/assessments", headers=auth_headers, params={"competency_id": str(competency.id)}
        ).json()
        by_path = client.get(
            f"{API}/competencies/{competency.id}/assessments", headers=auth_headers
        ).json()
        assert [a["id"] for a in by_filter] == [str(assessment.id)] == [a["id"] for a in by_path]

    def test_unknown_competency_is_404(self, client: TestClient, auth_headers: dict[str, str]):
        response = client.get(
            f"{API}/competencies/{uuid.uuid4()}/assessments", headers=auth_headers
        )
        assert response.status_code == 404

    def test_pagination(self, client: TestClient, auth_headers: dict[str, str], db: Session):
        competency, _ = make_competency(db, challenge_xp=[])
        for _ in range(5):
            make_assessment(db, competency, [make_question(db, competency)])
        page = client.get(
            f"{API}/assessments", headers=auth_headers, params={"limit": 2, "offset": 4}
        )
        assert page.status_code == 200
        assert len(page.json()) == 1
        assert page.headers["X-Total-Count"] == "5"
        assert (
            client.get(f"{API}/assessments", headers=auth_headers, params={"limit": 0}).status_code
            == 422
        )

    def test_title_follows_the_language(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, _ = make_competency(db, challenge_xp=[])
        make_assessment(
            db,
            competency,
            [make_question(db, competency)],
            translations={"pt-BR": {"title": "Questionário"}},
        )
        english = client.get(f"{API}/assessments", headers=auth_headers).json()[0]
        portuguese = client.get(
            f"{API}/assessments", headers=auth_headers, params={"lang": "pt-BR"}
        ).json()[0]
        assert (english["title"], portuguese["title"]) == ("Quiz", "Questionário")

    def test_unsupported_lang_is_422(self, client: TestClient, auth_headers: dict[str, str]):
        response = client.get(f"{API}/assessments", headers=auth_headers, params={"lang": "fr"})
        assert response.status_code == 422


class TestStartAndLanguage:
    def test_start_serves_questions_without_any_answer_material(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 3)
        response = _start(client, auth_headers, assessment)
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "in_progress"
        assert body["total_questions"] == 3
        assert [q["id"] for q in body["questions"]] == [str(q.id) for q in questions]
        assert [q["position"] for q in body["questions"]] == [1, 2, 3]
        for item in body["questions"]:
            assert item["review"] is None
            assert item["answer"] is None
            assert [o["id"] for o in item["options"]] == ["a", "b", "c"]

        raw = response.text
        assert "correct_option_ids" not in raw
        assert "explanation" not in raw
        for question in questions:
            assert f"EN explanation {question.code}" not in raw

    def test_resuming_returns_the_open_attempt(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, _, assessment = _bank(db)
        first = _start(client, auth_headers, assessment)
        second = _start(client, auth_headers, assessment)
        assert (first.status_code, second.status_code) == (201, 200)
        assert first.json()["id"] == second.json()["id"]

    def test_new_attempt_after_finishing(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db)
        first = _play(client, auth_headers, assessment, questions, 4)
        second = _start(client, auth_headers, assessment)
        assert second.status_code == 201
        assert second.json()["id"] != first["id"]

    def test_unknown_inactive_or_empty_assessment(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, _ = make_competency(db, challenge_xp=[])
        empty = make_assessment(db, competency, [])
        inactive = make_assessment(db, competency, [make_question(db, competency)], is_active=False)
        assert _start(client, auth_headers, empty).status_code == 409
        assert _start(client, auth_headers, inactive).status_code == 404
        missing = client.post(f"{API}/assessments/{uuid.uuid4()}/attempts", headers=auth_headers)
        assert missing.status_code == 404

    def test_inactive_questions_are_not_served(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, questions, _ = _bank(db, 2)
        retired = make_question(db, competency, is_active=False)
        assessment = make_assessment(db, competency, [*questions, retired])
        body = _start(client, auth_headers, assessment).json()
        assert body["total_questions"] == 2

    def test_default_language_is_english(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 1)
        item = _start(client, auth_headers, assessment).json()["questions"][0]
        assert item["language"] == "en"
        assert item["prompt"] == f"EN prompt {questions[0].code}"

    def test_user_preference_selects_the_language(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 1)
        client.patch(f"{API}/users/me", headers=auth_headers, json={"preferred_language": "pt-BR"})
        item = _start(client, auth_headers, assessment).json()["questions"][0]
        assert item["language"] == "pt-BR"
        assert item["prompt"] == f"PT prompt {questions[0].code}"
        assert item["options"][0]["text"].startswith("PT")

    def test_lang_query_overrides_the_preference(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 1)
        client.patch(f"{API}/users/me", headers=auth_headers, json={"preferred_language": "pt-BR"})
        attempt = _start(client, auth_headers, assessment, lang="en").json()
        assert attempt["questions"][0]["language"] == "en"
        # Reading the same attempt in the other language works too.
        again = client.get(
            f"{API}/attempts/{attempt['id']}", headers=auth_headers, params={"lang": "pt-BR"}
        ).json()
        assert again["questions"][0]["language"] == "pt-BR"

    def test_missing_translation_falls_back_to_english_per_question(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, _ = make_competency(db, challenge_xp=[])
        translated = make_question(db, competency, pt_br=True)
        english_only = make_question(db, competency, pt_br=False)
        assessment = make_assessment(db, competency, [translated, english_only])
        client.patch(f"{API}/users/me", headers=auth_headers, json={"preferred_language": "pt-BR"})
        first, second = _start(client, auth_headers, assessment).json()["questions"]
        assert (first["language"], second["language"]) == ("pt-BR", "en")
        assert second["prompt"] == f"EN prompt {english_only.code}"

    def test_grading_does_not_depend_on_the_language(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 2)
        attempt = _start(client, auth_headers, assessment, lang="pt-BR").json()
        for item in attempt["questions"]:
            _answer(client, auth_headers, attempt["id"], item["id"], ["b"])
        result = _finish(client, auth_headers, attempt["id"], lang="en").json()
        assert result["correct_count"] == 2
        assert result["questions"][0]["language"] == "en"


class TestAnswering:
    def test_answer_does_not_reveal_correctness(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 2)
        attempt = _start(client, auth_headers, assessment).json()
        right = _answer(client, auth_headers, attempt["id"], str(questions[0].id), ["b"])
        wrong = _answer(client, auth_headers, attempt["id"], str(questions[1].id), ["a"])
        assert right.status_code == wrong.status_code == 200
        assert right.json() == wrong.json() | {"question_id": str(questions[0].id)}
        assert right.json()["is_correct"] is None
        assert right.json()["model_answer"] is None
        assert "correct" not in right.text.replace("is_correct", "")

    def test_open_attempt_never_exposes_review_data(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 2)
        attempt = _start(client, auth_headers, assessment).json()
        _answer(client, auth_headers, attempt["id"], str(questions[0].id), ["b"])
        read = client.get(f"{API}/attempts/{attempt['id']}", headers=auth_headers)
        assert read.status_code == 200
        body = read.json()
        assert body["answered_count"] == 1
        assert body["questions"][0]["answer"]["option_ids"] == ["b"]
        assert all(q["review"] is None for q in body["questions"])
        assert "correct_option_ids" not in read.text

    def test_changing_an_answer_replaces_it(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 1)
        attempt = _start(client, auth_headers, assessment).json()
        _answer(client, auth_headers, attempt["id"], str(questions[0].id), ["a"])
        _answer(client, auth_headers, attempt["id"], str(questions[0].id), ["b"])
        result = _finish(client, auth_headers, attempt["id"]).json()
        assert result["correct_count"] == 1
        assert result["answered_count"] == 1

    def test_validation(self, client: TestClient, auth_headers: dict[str, str], db: Session):
        competency, _ = make_competency(db, challenge_xp=[])
        single = make_question(db, competency)
        multi = make_question(db, competency, type=QuestionType.MULTI_SELECT)
        short = make_question(db, competency, type=QuestionType.SHORT_ANSWER)
        assessment = make_assessment(db, competency, [single, multi, short])
        attempt = _start(client, auth_headers, assessment).json()
        aid = attempt["id"]

        assert _answer(client, auth_headers, aid, single.id, []).status_code == 422
        assert _answer(client, auth_headers, aid, single.id, ["a", "b"]).status_code == 422
        assert _answer(client, auth_headers, aid, single.id, ["zzz"]).status_code == 422
        assert _answer(client, auth_headers, aid, multi.id, ["b", "c"]).status_code == 200
        assert _answer(client, auth_headers, aid, multi.id, ["b", "nope"]).status_code == 422
        no_text = client.patch(
            f"{API}/attempts/{aid}/responses/{short.id}", headers=auth_headers, json={"text": "  "}
        )
        assert no_text.status_code == 422
        bad_time = _answer(client, auth_headers, aid, single.id, ["a"], time_spent_seconds=-1)
        assert bad_time.status_code == 422

    def test_question_outside_the_attempt_is_404(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, questions, assessment = _bank(db, 1)
        stranger = make_question(db, competency)
        attempt = _start(client, auth_headers, assessment).json()
        assert _answer(client, auth_headers, attempt["id"], stranger.id, ["b"]).status_code == 404
        assert _answer(client, auth_headers, attempt["id"], uuid.uuid4(), ["b"]).status_code == 404

    def test_cannot_answer_a_finished_attempt(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 1)
        finished = _play(client, auth_headers, assessment, questions, 1)
        response = _answer(client, auth_headers, finished["id"], str(questions[0].id), ["a"])
        assert response.status_code == 409

    def test_multi_select_is_all_or_nothing(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, _ = make_competency(db, challenge_xp=[])
        exact = make_question(db, competency, type=QuestionType.MULTI_SELECT)
        partial = make_question(db, competency, type=QuestionType.MULTI_SELECT)
        extra = make_question(db, competency, type=QuestionType.MULTI_SELECT)
        assessment = make_assessment(db, competency, [exact, partial, extra])
        attempt = _start(client, auth_headers, assessment).json()
        _answer(client, auth_headers, attempt["id"], exact.id, ["c", "b"])
        _answer(client, auth_headers, attempt["id"], partial.id, ["b"])
        _answer(client, auth_headers, attempt["id"], extra.id, ["a", "b", "c"])
        result = _finish(client, auth_headers, attempt["id"]).json()
        verdicts = [q["review"]["is_correct"] for q in result["questions"]]
        assert verdicts == [True, False, False]

    def test_code_reading_is_graded_like_multiple_choice(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, _ = make_competency(db, challenge_xp=[])
        question = make_question(db, competency, type=QuestionType.CODE_READING)
        assessment = make_assessment(db, competency, [question], threshold=100)
        attempt = _start(client, auth_headers, assessment).json()
        _answer(client, auth_headers, attempt["id"], question.id, ["b"])
        assert _finish(client, auth_headers, attempt["id"]).json()["passed"] is True


class TestFinish:
    def test_result_reveals_answers_and_explanations(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 2)
        result = _play(client, auth_headers, assessment, questions, 1)
        assert result["status"] == "completed"
        assert result["correct_count"] == 1
        assert result["score_percent"] == 50.0
        assert result["passed"] is False
        first, second = result["questions"]
        assert first["review"]["correct_option_ids"] == ["b"]
        assert first["review"]["is_correct"] is True
        assert first["review"]["explanation"] == f"EN explanation {questions[0].code}"
        assert second["review"]["is_correct"] is False
        assert second["answer"]["option_ids"] == ["a"]

    def test_unanswered_questions_count_as_wrong(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, _, assessment = _bank(db, 4)
        attempt = _start(client, auth_headers, assessment).json()
        _answer(client, auth_headers, attempt["id"], attempt["questions"][0]["id"], ["b"])
        result = _finish(client, auth_headers, attempt["id"]).json()
        assert (result["correct_count"], result["total_questions"]) == (1, 4)
        assert result["score_percent"] == 25.0
        assert result["questions"][3]["review"]["is_correct"] is False

    def test_threshold_is_inclusive(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 10)
        result = _play(client, auth_headers, assessment, questions, 7)
        assert result["score_percent"] == 70.0
        assert result["passed"] is True

    def test_passing_pays_question_xp_plus_completion_bonus(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 4, bonus=25)
        result = _play(client, auth_headers, assessment, questions, 4)
        assert result["passed"] is True
        assert (result["xp_questions"], result["xp_bonus"], result["xp_awarded"]) == (40, 25, 65)
        assert _profile(client, auth_headers)["total_xp"] == 65
        assert all(q["review"]["xp_awarded"] == 10 for q in result["questions"])
        assert all(q["review"]["is_first_correct"] for q in result["questions"])

    def test_xp_follows_each_questions_difficulty(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, _ = make_competency(db, challenge_xp=[])
        questions = [
            make_question(db, competency, difficulty=QuestionDifficulty.EASY),
            make_question(db, competency, difficulty=QuestionDifficulty.MEDIUM),
            make_question(db, competency, difficulty=QuestionDifficulty.HARD),
        ]
        assessment = make_assessment(db, competency, questions, bonus=0)
        result = _play(client, auth_headers, assessment, questions, 3)
        assert result["xp_awarded"] == 10 + 20 + 30

    def test_failing_pays_nothing_even_for_correct_answers(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 4)
        result = _play(client, auth_headers, assessment, questions, 2)
        assert result["passed"] is False
        assert result["xp_awarded"] == 0
        assert _profile(client, auth_headers)["total_xp"] == 0

    def test_ledger_entry_references_the_attempt(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        from app.models.gamification import XPAward, XPSource

        _, questions, assessment = _bank(db, 2, bonus=10)
        result = _play(client, auth_headers, assessment, questions, 2)
        awards = db.query(XPAward).filter(XPAward.source == XPSource.ASSESSMENT).all()
        assert len(awards) == 1
        assert awards[0].amount == 30
        assert str(awards[0].reference_id) == result["id"]

    def test_finish_is_idempotent_and_pays_once(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 2)
        first = _play(client, auth_headers, assessment, questions, 2)
        again = _finish(client, auth_headers, first["id"])
        assert again.status_code == 200
        assert again.json()["xp_awarded"] == first["xp_awarded"]
        assert _profile(client, auth_headers)["total_xp"] == first["xp_awarded"]

    def test_finishing_updates_the_streak_with_xp(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 2)
        _play(client, auth_headers, assessment, questions, 2)
        assert _profile(client, auth_headers)["current_streak_days"] == 1


class TestAntiFarm:
    def test_repeating_a_passed_assessment_pays_nothing(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 4)
        first = _play(client, auth_headers, assessment, questions, 4)
        second = _play(client, auth_headers, assessment, questions, 4)
        third = _play(client, auth_headers, assessment, questions, 4)
        assert first["xp_awarded"] == 65
        assert second["xp_awarded"] == third["xp_awarded"] == 0
        assert (second["xp_bonus"], second["xp_questions"]) == (0, 0)
        assert _profile(client, auth_headers)["total_xp"] == 65
        # Still real practice: correct, scored, and not first-time anymore.
        assert second["passed"] is True
        assert all(not q["review"]["is_first_correct"] for q in second["questions"])

    def test_failed_attempt_leaves_questions_unpaid_for_a_later_pass(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 4, threshold=75, bonus=25)
        failed = _play(client, auth_headers, assessment, questions, 2)
        assert failed["xp_awarded"] == 0
        passed = _play(client, auth_headers, assessment, questions, 4)
        assert passed["xp_awarded"] == 40 + 25
        # First pass of the assessment, even though it was the second try.
        assert passed["xp_bonus"] == 25

    def test_questions_paid_in_one_assessment_do_not_pay_again_in_another(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, questions, first_assessment = _bank(db, 4)
        mixed = make_assessment(
            db,
            None,
            [*questions[:2], make_question(db, competency)],
            kind=AssessmentKind.MIXED,
            bonus=5,
        )
        first = _play(client, auth_headers, first_assessment, questions, 4)
        assert first["xp_awarded"] == 65
        second = _play(client, auth_headers, mixed, questions, 3)
        # Only the one brand-new question (10) + the mixed assessment's own bonus.
        assert second["xp_questions"] == 10
        assert second["xp_bonus"] == 5

    def test_a_pass_after_a_pass_pays_only_newly_added_questions(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        from app.models.assessment import AssessmentQuestion

        competency, questions, assessment = _bank(db, 2, bonus=10)
        assert _play(client, auth_headers, assessment, questions, 2)["xp_awarded"] == 30
        new_question = make_question(db, competency, difficulty=QuestionDifficulty.HARD)
        db.add(
            AssessmentQuestion(
                assessment_id=assessment.id, question_id=new_question.id, sort_order=9
            )
        )
        db.commit()
        result = _play(client, auth_headers, assessment, questions, 3)
        assert result["xp_questions"] == 30
        assert result["xp_bonus"] == 0

    def test_xp_is_per_user(self, client: TestClient, auth_headers: dict[str, str], db: Session):
        _, questions, assessment = _bank(db, 2)
        other, _ = register(client, "other@example.com")
        assert _play(client, auth_headers, assessment, questions, 2)["xp_awarded"] == 45
        assert _play(client, other, assessment, questions, 2)["xp_awarded"] == 45

    def test_no_xp_is_ever_refunded(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 4)
        _play(client, auth_headers, assessment, questions, 4)
        _play(client, auth_headers, assessment, questions, 0)
        assert _profile(client, auth_headers)["total_xp"] == 65


class TestShortAnswer:
    def _setup(self, db: Session):
        competency, _ = make_competency(db, challenge_xp=[])
        short = make_question(db, competency, type=QuestionType.SHORT_ANSWER)
        choice = make_question(db, competency)
        return short, choice, make_assessment(db, competency, [short, choice], threshold=50)

    def test_save_returns_the_model_answer_for_self_grading(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        short, _, assessment = self._setup(db)
        attempt = _start(client, auth_headers, assessment).json()
        item = attempt["questions"][0]
        assert item["options"] is None
        response = client.patch(
            f"{API}/attempts/{attempt['id']}/responses/{short.id}",
            headers=auth_headers,
            json={"text": "my answer"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["grading_status"] == "pending_review"
        assert body["model_answer"] == f"EN model answer {short.code}"
        assert body["is_correct"] is None

    def test_self_graded_right_answer_counts_and_pays(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        short, choice, assessment = self._setup(db)
        attempt = _start(client, auth_headers, assessment).json()
        client.patch(
            f"{API}/attempts/{attempt['id']}/responses/{short.id}",
            headers=auth_headers,
            json={"text": "my answer"},
        )
        graded = client.post(
            f"{API}/attempts/{attempt['id']}/responses/{short.id}/self-grade",
            headers=auth_headers,
            json={"is_correct": True},
        )
        assert graded.status_code == 200
        assert graded.json()["grading_status"] == "self_graded"
        assert graded.json()["is_correct"] is True
        result = _finish(client, auth_headers, attempt["id"]).json()
        assert result["correct_count"] == 1
        assert result["passed"] is True  # 1/2 >= 50%
        assert result["pending_review_count"] == 0
        assert result["questions"][0]["review"]["model_answer"] == f"EN model answer {short.code}"

    def test_ungraded_short_answer_counts_as_wrong_and_is_flagged(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        short, choice, assessment = self._setup(db)
        attempt = _start(client, auth_headers, assessment).json()
        client.patch(
            f"{API}/attempts/{attempt['id']}/responses/{short.id}",
            headers=auth_headers,
            json={"text": "my answer"},
        )
        result = _finish(client, auth_headers, attempt["id"]).json()
        assert result["correct_count"] == 0
        assert result["pending_review_count"] == 1
        review = result["questions"][0]["review"]
        assert review["is_correct"] is None
        assert review["grading_status"] == "pending_review"

    def test_self_grade_rules(self, client: TestClient, auth_headers: dict[str, str], db: Session):
        short, choice, assessment = self._setup(db)
        attempt = _start(client, auth_headers, assessment).json()
        grade = lambda qid, ok: client.post(  # noqa: E731
            f"{API}/attempts/{attempt['id']}/responses/{qid}/self-grade",
            headers=auth_headers,
            json={"is_correct": ok},
        )
        assert grade(short.id, True).status_code == 422  # nothing saved yet
        _answer(client, auth_headers, attempt["id"], choice.id, ["a"])
        assert grade(choice.id, True).status_code == 422  # deterministic questions
        client.patch(
            f"{API}/attempts/{attempt['id']}/responses/{short.id}",
            headers=auth_headers,
            json={"text": "x"},
        )
        _finish(client, auth_headers, attempt["id"])
        assert grade(short.id, True).status_code == 409  # XP is settled at finish

    def test_re_answering_resets_the_self_grade(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        short, _, assessment = self._setup(db)
        attempt = _start(client, auth_headers, assessment).json()
        base = f"{API}/attempts/{attempt['id']}/responses/{short.id}"
        client.patch(base, headers=auth_headers, json={"text": "v1"})
        client.post(f"{base}/self-grade", headers=auth_headers, json={"is_correct": True})
        again = client.patch(base, headers=auth_headers, json={"text": "v2"})
        assert again.json()["grading_status"] == "pending_review"


class TestHistory:
    def test_history_is_newest_first_paginated_and_filterable(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 2)
        _, other_questions, other_assessment = _bank(db, 2)
        ids = [_play(client, auth_headers, assessment, questions, n)["id"] for n in (0, 1, 2)]
        _play(client, auth_headers, other_assessment, other_questions, 2)

        everything = client.get(f"{API}/attempts", headers=auth_headers)
        assert everything.headers["X-Total-Count"] == "4"
        filtered = client.get(
            f"{API}/attempts", headers=auth_headers, params={"assessment_id": str(assessment.id)}
        )
        assert [a["id"] for a in filtered.json()] == list(reversed(ids))
        assert filtered.headers["X-Total-Count"] == "3"
        page = client.get(
            f"{API}/attempts",
            headers=auth_headers,
            params={"assessment_id": str(assessment.id), "limit": 2, "offset": 2},
        )
        assert [a["id"] for a in page.json()] == [ids[0]]
        assert page.headers["X-Total-Count"] == "3"
        summary = filtered.json()[0]
        assert summary["score_percent"] == 100.0
        assert summary["assessment_title"] == "Quiz"
        assert "questions" not in summary

    def test_listing_shows_best_score_and_open_attempt(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 2)
        _play(client, auth_headers, assessment, questions, 1)
        _play(client, auth_headers, assessment, questions, 2)
        open_attempt = _start(client, auth_headers, assessment).json()
        (item,) = client.get(f"{API}/assessments", headers=auth_headers).json()
        assert item["attempts_completed"] == 2
        assert item["best_score_percent"] == 100.0
        assert item["passed"] is True
        assert item["open_attempt_id"] == open_attempt["id"]


class TestAuthorization:
    def test_other_users_cannot_touch_my_attempt(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 2)
        other, _ = register(client, "intruder@example.com")
        attempt = _start(client, auth_headers, assessment).json()
        qid = attempt["questions"][0]["id"]

        assert client.get(f"{API}/attempts/{attempt['id']}", headers=other).status_code == 404
        assert _answer(client, other, attempt["id"], qid, ["b"]).status_code == 404
        self_grade = client.post(
            f"{API}/attempts/{attempt['id']}/responses/{qid}/self-grade",
            headers=other,
            json={"is_correct": True},
        )
        assert self_grade.status_code == 404
        assert _finish(client, other, attempt["id"]).status_code == 404
        # ...and my attempt is untouched.
        assert (
            client.get(f"{API}/attempts/{attempt['id']}", headers=auth_headers).json()[
                "answered_count"
            ]
            == 0
        )

    def test_history_and_stats_only_include_my_data(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 2)
        other, _ = register(client, "other@example.com")
        _play(client, other, assessment, questions, 2)
        assert client.get(f"{API}/attempts", headers=auth_headers).json() == []
        assert (
            client.get(f"{API}/assessments/stats/by-competency", headers=auth_headers).json() == []
        )

    def test_every_endpoint_requires_authentication(self, client: TestClient):
        some = uuid.uuid4()
        for method, path in [
            ("post", f"/assessments/{some}/attempts"),
            ("get", "/attempts"),
            ("get", f"/attempts/{some}"),
            ("patch", f"/attempts/{some}/responses/{some}"),
            ("post", f"/attempts/{some}/responses/{some}/self-grade"),
            ("post", f"/attempts/{some}/finish"),
            ("get", "/assessments/stats/by-competency"),
            ("get", f"/competencies/{some}/assessments"),
        ]:
            assert client.request(method, f"{API}{path}").status_code == 401, path

    def test_unknown_attempt_is_404(self, client: TestClient, auth_headers: dict[str, str]):
        assert client.get(f"{API}/attempts/{uuid.uuid4()}", headers=auth_headers).status_code == 404


class TestStatistics:
    def test_per_competency_stats(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, questions, assessment = _bank(db, 4)
        _play(client, auth_headers, assessment, questions, 2)  # 2/4 right
        _play(client, auth_headers, assessment, questions, 4)  # latest: all 4 right

        response = client.get(f"{API}/assessments/stats/by-competency", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["X-Total-Count"] == "1"
        (stats,) = response.json()
        assert stats["competency_id"] == str(competency.id)
        assert stats["questions_total"] == 4
        assert stats["questions_answered"] == 4
        assert stats["questions_correct"] == 4
        assert stats["coverage_percent"] == 100.0
        assert stats["attempts_completed"] == 2
        assert stats["responses_graded"] == 8
        assert stats["responses_correct"] == 6
        assert stats["accuracy_percent"] == 75.0
        assert stats["xp_earned"] == 40  # the second attempt passed and paid the 4 questions

    def test_open_attempts_do_not_count(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, questions, assessment = _bank(db, 2)
        attempt = _start(client, auth_headers, assessment).json()
        _answer(client, auth_headers, attempt["id"], questions[0].id, ["b"])
        assert (
            client.get(f"{API}/assessments/stats/by-competency", headers=auth_headers).json() == []
        )

    def test_stats_are_paginated(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        for _ in range(3):
            _, questions, assessment = _bank(db, 1)
            _play(client, auth_headers, assessment, questions, 1)
        page = client.get(
            f"{API}/assessments/stats/by-competency",
            headers=auth_headers,
            params={"limit": 2, "offset": 2},
        )
        assert len(page.json()) == 1
        assert page.headers["X-Total-Count"] == "3"


def test_responses_never_contain_the_correct_option_while_open(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    """Belt and braces: scan every payload of an open attempt for answer fields."""
    competency, _ = make_competency(db, challenge_xp=[])
    questions = [
        make_question(db, competency),
        make_question(db, competency, type=QuestionType.MULTI_SELECT),
        make_question(db, competency, type=QuestionType.SHORT_ANSWER),
    ]
    assessment = make_assessment(db, competency, questions)
    attempt = _start(client, auth_headers, assessment).json()
    payloads = [attempt]
    payloads.append(client.get(f"{API}/attempts/{attempt['id']}", headers=auth_headers).json())
    payloads.append(_answer(client, auth_headers, attempt["id"], questions[0].id, ["b"]).json())
    payloads.append(
        _answer(client, auth_headers, attempt["id"], questions[1].id, ["b", "c"]).json()
    )
    payloads.append(client.get(f"{API}/attempts", headers=auth_headers).json())
    payloads.append(client.get(f"{API}/assessments", headers=auth_headers).json())
    blob = json.dumps(payloads)
    for forbidden in ("correct_option_ids", 'explanation": "EN', "is_first_correct"):
        assert forbidden not in blob
