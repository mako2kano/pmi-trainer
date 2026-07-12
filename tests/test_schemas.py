"""JSON Schema（schemas/）と基準データ（schemas/examples/・config/）の整合検証。

jsonschema ライブラリ未インストール時はスキップする
（scripts/validate.py による整合チェックは test_repo_consistency.py で常に走る）。
"""

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
referencing = pytest.importorskip("referencing")

from scripts.validate import REPO_ROOT, load_json

SCHEMAS = REPO_ROOT / "schemas"


def _validator(schema_name):
    registry = referencing.Registry().with_resources(
        (load_json(p)["$id"], referencing.Resource.from_contents(load_json(p)))
        for p in SCHEMAS.glob("*.schema.json")
    )
    return jsonschema.Draft202012Validator(
        load_json(SCHEMAS / schema_name), registry=registry
    )


def test_exams_json_matches_schema():
    _validator("exams.schema.json").validate(load_json(REPO_ROOT / "config" / "exams.json"))


@pytest.mark.parametrize("exam_id", ["pgmp", "pfmp"])
def test_taxonomy_matches_schema(exam_id):
    _validator("taxonomy.schema.json").validate(
        load_json(REPO_ROOT / "config" / f"taxonomy.{exam_id}.json")
    )


def test_example_question_matches_schema():
    _validator("question.schema.json").validate(
        load_json(SCHEMAS / "examples" / "question.example.json")
    )


def test_example_attempt_matches_schema():
    _validator("attempt.schema.json").validate(
        load_json(SCHEMAS / "examples" / "attempt.example.json")
    )


@pytest.mark.parametrize("exam_id", ["pgmp", "pfmp"])
@pytest.mark.parametrize("domain_id", ["D1", "D2", "D3", "D4", "D5"])
def test_question_banks_match_schema(exam_id, domain_id):
    _validator("question_bank.schema.json").validate(
        load_json(REPO_ROOT / "questions" / exam_id / f"{domain_id}.json")
    )
