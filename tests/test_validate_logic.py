"""scripts/validate.py の検証ロジック自体のユニットテスト。

基準データは schemas/examples/ に置き、そこから壊したデータが
正しく検出されることを確認する。
"""

import copy
import json
from pathlib import Path

import pytest

from scripts.validate import (
    REPO_ROOT,
    validate_bank,
    validate_exams,
    validate_question,
    validate_taxonomy,
)

EXAMPLES = REPO_ROOT / "schemas" / "examples"


@pytest.fixture
def question():
    with open(EXAMPLES / "question.example.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def exams():
    with open(REPO_ROOT / "config" / "exams.json", encoding="utf-8") as f:
        return json.load(f)


def test_example_question_is_valid(question):
    assert validate_question(question, "pgmp", "D1") == []


def test_correct_option_must_have_null_distractor_type(question):
    q = copy.deepcopy(question)
    q["distractor_types"] = ["plausible", None, "plausible", "plausible"]
    # answer_index=0 なのに null が位置1にある
    assert validate_question(q, "pgmp", "D1")


def test_exactly_one_null_in_distractor_types(question):
    q = copy.deepcopy(question)
    q["distractor_types"] = [None, None, "plausible", "plausible"]
    assert validate_question(q, "pgmp", "D1")


def test_at_most_one_cross_perspective(question):
    q = copy.deepcopy(question)
    q["distractor_types"] = [None, "cross_perspective", "cross_perspective", "plausible"]
    assert validate_question(q, "pgmp", "D1")


def test_exam_mismatch_detected(question):
    assert validate_question(question, "pfmp", "D1")


def test_task_must_exist_in_taxonomy(question):
    assert validate_question(question, "pgmp", "D1", valid_tasks={"T1", "T2"}) == []
    errors = validate_question(question, "pgmp", "D1", valid_tasks={"T2", "T3"})
    assert any("taxonomy" in e for e in errors)


def test_unknown_cross_tag_detected(question):
    q = copy.deepcopy(question)
    q["cross_tags"] = ["governance", "schedule"]
    assert validate_question(q, "pgmp", "D1")


def test_duplicate_question_ids_detected(question):
    bank = {"exam": "pgmp", "domain": "D1", "questions": [question, copy.deepcopy(question)]}
    errors = validate_bank(bank, "pgmp", "D1")
    assert any("重複" in e for e in errors)


def test_taxonomy_domain_mismatch_detected(exams):
    taxonomy = {
        "exam": "pgmp",
        "domains": [
            {"id": "D1", "name": "X", "weight_percent": 100, "tasks": []}
        ],
        "cross_tags": [],
    }
    errors = validate_taxonomy(taxonomy, "pgmp", exams)
    assert any("exams.json" in e for e in errors)


def test_exams_missing_key_detected():
    errors = validate_exams({"pgmp": {"name": "PgMP"}})
    assert errors


def test_dr13_optional_fields_are_valid_when_consistent(question):
    q = copy.deepcopy(question)
    q["scenario_ja"] = "シナリオの訳"
    q["stem_ja"] = "問いの訳"
    q["options_ja"] = ["訳A", "訳B", "訳C", "訳D"]
    q["option_explanations"] = ["解説A", "解説B", "解説C", "解説D"]
    q["vocab"] = [{"en": "benefit", "ja": "ベネフィット"}]
    q["principles"] = ["Benefits Realization"]
    assert validate_question(q, "pgmp", "D1") == []


@pytest.mark.parametrize("key", ["options_ja", "option_explanations"])
def test_dr13_per_option_fields_must_match_options_length(question, key):
    q = copy.deepcopy(question)
    q[key] = ["A", "B", "C"]
    assert any(key in e for e in validate_question(q, "pgmp", "D1"))


def test_dr13_vocab_requires_en_and_ja(question):
    q = copy.deepcopy(question)
    q["vocab"] = [{"en": "benefit"}]
    assert any("vocab" in e for e in validate_question(q, "pgmp", "D1"))


def test_dr14_unknown_principle_detected(question):
    q = copy.deepcopy(question)
    q["principles"] = ["Synergy", "Agility"]
    assert any("principles" in e for e in validate_question(q, "pgmp", "D1"))
