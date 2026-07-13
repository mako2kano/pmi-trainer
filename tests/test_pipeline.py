"""pipeline の純粋ロジック（prompts / evaluator）のテスト。

generate.py（Anthropic SDKラッパー）はテスト対象外。
"""

import copy
import json

import pytest

from pipeline import evaluator, prompts
from scripts.validate import REPO_ROOT, load_json

EXAMPLE = load_json(REPO_ROOT / "schemas" / "examples" / "question.example.json")


@pytest.fixture
def pgmp_d1():
    tax = load_json(REPO_ROOT / "config" / "taxonomy.pgmp.json")
    return tax["domains"][0]  # D1


# ---- prompts ----

def test_generation_prompt_includes_task_and_perspective(pgmp_d1):
    task = next(t for t in pgmp_d1["tasks"] if t.get("cross_perspective_eligible"))
    p = prompts.build_generation_prompt("pgmp", pgmp_d1, task, count=2)
    assert task["summary"] in p["user"]
    assert "program manager" in p["system"]
    assert "portfolio manager" in p["system"]  # 対比視点
    assert p["cross_perspective_required"] is True
    assert "cross_perspective" in p["user"]


def test_generation_prompt_non_eligible_forbids_cross(pgmp_d1):
    task = next(
        t for t in pgmp_d1["tasks"] if not t.get("cross_perspective_eligible")
    )
    p = prompts.build_generation_prompt("pgmp", pgmp_d1, task)
    assert p["cross_perspective_required"] is False
    assert "no `cross_perspective`" in p["user"]


def test_generation_prompt_has_language_and_legal(pgmp_d1):
    p = prompts.build_generation_prompt("pgmp", pgmp_d1, pgmp_d1["tasks"][0])
    assert "ENGLISH" in p["system"] and "JAPANESE" in p["system"]
    assert "Do NOT reproduce" in p["system"]


def test_other_exam():
    assert prompts.other_exam("pgmp") == "pfmp"
    assert prompts.other_exam("pfmp") == "pgmp"


def test_unknown_exam_raises(pgmp_d1):
    with pytest.raises(ValueError):
        prompts.build_generation_prompt("xxxx", pgmp_d1, pgmp_d1["tasks"][0])


def test_perspective_check_prompt_shape():
    p = prompts.build_perspective_check_prompt(EXAMPLE, "pgmp")
    assert "perspective_check" in p["system"]
    assert "PGMP" in p["user"]


# ---- evaluator ----

def test_example_passes_structural():
    report = evaluator.evaluate_question(EXAMPLE, "pgmp", "D1", valid_tasks={"T1"})
    assert report["passed_structural"], report["errors"]
    assert report["warnings"] == []


def test_language_warning_when_explanation_not_japanese():
    q = copy.deepcopy(EXAMPLE)
    q["explanation"] = "This explanation is in English only."
    warnings = evaluator.language_warnings(q)
    assert any("explanation" in w for w in warnings)


def test_language_warning_when_scenario_not_english():
    q = copy.deepcopy(EXAMPLE)
    q["scenario"] = "これは日本語のシナリオで英語ではありません。" * 3
    warnings = evaluator.language_warnings(q)
    assert any("scenario" in w for w in warnings)


def test_require_cross_perspective_flags_missing():
    q = copy.deepcopy(EXAMPLE)
    q["distractor_types"] = [None, "plausible", "plausible", "plausible"]
    report = evaluator.evaluate_question(
        q, "pgmp", "D1", valid_tasks={"T1"}, require_cross_perspective=True
    )
    assert not report["passed_structural"]


def test_attach_and_check_perspective():
    q = copy.deepcopy(EXAMPLE)
    evaluator.attach_perspective_check(q, 0.85, "m", "2026-07-12T00:00:00Z")
    assert q["evaluator"]["perspective_check"] == 0.85
    assert evaluator.perspective_check_passed(q)
    evaluator.attach_perspective_check(q, 0.3, "m", "2026-07-12T00:00:00Z")
    assert not evaluator.perspective_check_passed(q)
