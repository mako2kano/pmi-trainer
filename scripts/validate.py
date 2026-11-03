"""config/ と questions/ の整合性検証。

JSON Schema（schemas/）が構造の正だが、スキーマでは表現しにくい
ファイル間整合（exams.json ⇔ taxonomy ⇔ 問題バンク）と
SPEC_v2.md の不変条件をここで検証する。

- 外部ライブラリに依存しない純粋Python（MCP・APIにも依存しない）
- テスト（tests/）と生成パイプライン（M2）の両方から使う
- CLI: python -m scripts.validate
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CROSS_TAGS = {"governance", "stakeholder", "benefits_value", "risk"}
DISTRACTOR_TYPES = {"plausible", "cross_perspective"}
# The Standard for Program Management 第5版の8原則（DR-14）
PRINCIPLES = {
    "Stakeholders", "Benefits Realization", "Synergy", "Team of Teams",
    "Change", "Leadership", "Risk", "Governance",
}
NUM_OPTIONS = 4


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_exams(exams: dict) -> list[str]:
    errors = []
    if not isinstance(exams, dict) or not exams:
        return ["exams.json はexam IDをキーとする非空オブジェクトであること"]
    for exam_id, cfg in exams.items():
        prefix = f"exams.json[{exam_id}]"
        for key in ("name", "mock_questions", "mock_minutes", "domains", "theme"):
            if key not in cfg:
                errors.append(f"{prefix}: 必須キー {key} がない")
        if isinstance(cfg.get("mock_questions"), int) and cfg["mock_questions"] < 1:
            errors.append(f"{prefix}: mock_questions は1以上")
        if isinstance(cfg.get("mock_minutes"), int) and cfg["mock_minutes"] < 1:
            errors.append(f"{prefix}: mock_minutes は1以上")
        domains = cfg.get("domains", [])
        if len(domains) != len(set(domains)):
            errors.append(f"{prefix}: domains に重複がある")
    return errors


def validate_taxonomy(taxonomy: dict, exam_id: str, exams: dict) -> list[str]:
    errors = []
    prefix = f"taxonomy.{exam_id}.json"
    if taxonomy.get("exam") != exam_id:
        errors.append(f"{prefix}: exam が {exam_id} でない")

    domains = taxonomy.get("domains", [])
    domain_ids = [d.get("id") for d in domains]
    expected = exams.get(exam_id, {}).get("domains", [])
    if domain_ids != expected:
        errors.append(
            f"{prefix}: ドメインID {domain_ids} が exams.json の {expected} と一致しない"
        )

    total = sum(d.get("weight_percent", 0) for d in domains)
    if abs(total - 100) > 0.01:
        errors.append(f"{prefix}: weight_percent の合計が {total}（100であること）")

    for d in domains:
        task_ids = [t.get("id") for t in d.get("tasks", [])]
        if len(task_ids) != len(set(task_ids)):
            errors.append(f"{prefix}[{d.get('id')}]: タスクIDに重複がある")

    tags = taxonomy.get("cross_tags", [])
    if not set(tags) <= CROSS_TAGS:
        errors.append(f"{prefix}: cross_tags に未知のタグ {set(tags) - CROSS_TAGS}")
    return errors


def validate_question(
    q: dict, exam_id: str, domain_id: str, valid_tasks: set[str] | None = None
) -> list[str]:
    errors = []
    qid = q.get("id", "<no id>")
    prefix = f"{exam_id}/{domain_id} {qid}"

    if q.get("exam") != exam_id:
        errors.append(f"{prefix}: exam がバンクの {exam_id} と不一致")
    if q.get("domain") != domain_id:
        errors.append(f"{prefix}: domain がバンクの {domain_id} と不一致")
    if not str(qid).startswith(f"{exam_id}-{domain_id}-"):
        errors.append(f"{prefix}: id が {exam_id}-{domain_id}-NNNN 形式でない")

    if valid_tasks is not None and q.get("task") not in valid_tasks:
        errors.append(
            f"{prefix}: task {q.get('task')} が taxonomy の {domain_id} に存在しない"
        )

    options = q.get("options", [])
    if len(options) != NUM_OPTIONS:
        errors.append(f"{prefix}: options は{NUM_OPTIONS}択であること")

    answer = q.get("answer_index")
    if not isinstance(answer, int) or not 0 <= answer < NUM_OPTIONS:
        errors.append(f"{prefix}: answer_index が 0..{NUM_OPTIONS - 1} でない")
        answer = None

    dts = q.get("distractor_types", [])
    if len(dts) != NUM_OPTIONS:
        errors.append(f"{prefix}: distractor_types は options と同じ長さであること")
    else:
        if answer is not None and dts[answer] is not None:
            errors.append(f"{prefix}: 正解位置 {answer} の distractor_type は null であること")
        if dts.count(None) != 1:
            errors.append(f"{prefix}: distractor_types の null はちょうど1つ（正解位置のみ）")
        unknown = {t for t in dts if t is not None} - DISTRACTOR_TYPES
        if unknown:
            errors.append(f"{prefix}: 未知の distractor_type {unknown}")
        if dts.count("cross_perspective") > 1:
            errors.append(f"{prefix}: cross_perspective は1問につき最大1つ（SPEC_v2.md §6）")

    if not set(q.get("cross_tags", [])) <= CROSS_TAGS:
        errors.append(f"{prefix}: cross_tags に未知のタグがある")

    for key in ("scenario", "stem", "explanation"):
        if not q.get(key):
            errors.append(f"{prefix}: {key} が空")

    # DR-13: 任意項目。あるなら options と同じ並び・長さであること
    for key in ("options_ja", "option_explanations"):
        if key in q and len(q[key]) != len(options):
            errors.append(f"{prefix}: {key} は options と同じ長さであること")
    for key in ("scenario_ja", "stem_ja"):
        if key in q and not q[key]:
            errors.append(f"{prefix}: {key} が空")
    for i, item in enumerate(q.get("vocab", [])):
        if not (isinstance(item, dict) and item.get("en") and item.get("ja")):
            errors.append(f"{prefix}: vocab[{i}] に en と ja が必要")

    # DR-14: 第5版の原則
    unknown_principles = set(q.get("principles", [])) - PRINCIPLES
    if unknown_principles:
        errors.append(f"{prefix}: principles に未知の原則 {unknown_principles}")

    ev = q.get("evaluator")
    if ev is not None:
        pc = ev.get("perspective_check")
        if pc is not None and not (isinstance(pc, (int, float)) and 0 <= pc <= 1):
            errors.append(f"{prefix}: perspective_check は0〜1であること")
    return errors


def validate_bank(
    bank: dict, exam_id: str, domain_id: str, valid_tasks: set[str] | None = None
) -> list[str]:
    errors = []
    prefix = f"questions/{exam_id}/{domain_id}.json"
    if bank.get("exam") != exam_id:
        errors.append(f"{prefix}: exam がパスと不一致")
    if bank.get("domain") != domain_id:
        errors.append(f"{prefix}: domain がパスと不一致")

    questions = bank.get("questions", [])
    ids = [q.get("id") for q in questions]
    if len(ids) != len(set(ids)):
        errors.append(f"{prefix}: 問題IDに重複がある")
    for q in questions:
        errors.extend(validate_question(q, exam_id, domain_id, valid_tasks))
    return errors


def validate_repo(root: Path = REPO_ROOT) -> list[str]:
    """リポジトリ全体の config/questions を検証し、エラー一覧を返す。"""
    errors = []
    exams = load_json(root / "config" / "exams.json")
    errors.extend(validate_exams(exams))

    for exam_id in exams:
        tax_path = root / "config" / f"taxonomy.{exam_id}.json"
        tasks_by_domain: dict[str, set[str]] = {}
        if not tax_path.exists():
            errors.append(f"config/taxonomy.{exam_id}.json がない")
        else:
            taxonomy = load_json(tax_path)
            errors.extend(validate_taxonomy(taxonomy, exam_id, exams))
            tasks_by_domain = {
                d.get("id"): {t.get("id") for t in d.get("tasks", [])}
                for d in taxonomy.get("domains", [])
            }

        for domain_id in exams[exam_id].get("domains", []):
            bank_path = root / "questions" / exam_id / f"{domain_id}.json"
            if not bank_path.exists():
                errors.append(f"questions/{exam_id}/{domain_id}.json がない")
            else:
                # taxonomyが読めた場合のみtask実在チェックを有効化（空set=チェックしない）
                valid_tasks = tasks_by_domain.get(domain_id) or None
                errors.extend(
                    validate_bank(load_json(bank_path), exam_id, domain_id, valid_tasks)
                )
    return errors


def main() -> int:
    errors = validate_repo()
    if errors:
        for e in errors:
            print(f"NG: {e}")
        return 1
    print("OK: config/ と questions/ の整合性に問題なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
