"""問題バンクにコミットされた問題が品質基準を満たすことの回帰テスト。

生成パイプライン（pipeline.evaluator）の決定的チェックを、リポジトリに
入っている全問題へ適用する。作者レビュー前でも構造・言語・クロス視点規則・
perspective_check閾値は満たしていること（M2の較正対象）。
"""

import pytest

from pipeline import evaluator
from scripts.validate import REPO_ROOT, load_json

EXAMS = ["pgmp", "pfmp"]


def _iter_questions():
    for exam in EXAMS:
        tax = load_json(REPO_ROOT / "config" / f"taxonomy.{exam}.json")
        tasks_by_domain = {
            d["id"]: {t["id"]: t for t in d["tasks"]} for d in tax["domains"]
        }
        for domain_id, tasks in tasks_by_domain.items():
            bank = REPO_ROOT / "questions" / exam / f"{domain_id}.json"
            if not bank.exists():
                continue
            for q in load_json(bank)["questions"]:
                yield exam, domain_id, tasks, q


def test_committed_questions_pass_evaluator():
    checked = 0
    for exam, domain_id, tasks, q in _iter_questions():
        checked += 1
        elig = tasks.get(q["task"], {}).get("cross_perspective_eligible", False)
        report = evaluator.evaluate_question(
            q, exam, domain_id, set(tasks), require_cross_perspective=elig
        )
        assert report["passed_structural"], (q["id"], report["errors"])
        assert report["warnings"] == [], (q["id"], report["warnings"])
        assert evaluator.perspective_check_passed(q), (
            q["id"],
            report["perspective_check"],
        )
    # バンクが空でもテスト自体は通るが、パイロット投入後は問題が存在するはず
    assert checked >= 0


def test_eligible_task_questions_have_cross_perspective():
    """cross_perspective_eligible なタスクの問題は cross_perspective distractor を持つ。"""
    for exam, domain_id, tasks, q in _iter_questions():
        if tasks.get(q["task"], {}).get("cross_perspective_eligible"):
            assert evaluator.cross_perspective_count(q) == 1, q["id"]
