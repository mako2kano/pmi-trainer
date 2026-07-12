"""config/ と questions/ の実データがSPECの不変条件を満たすことの検証。

受け入れ基準（SPEC_v2.md §10）のうちデータ層で保証できるものをここで担保する。
"""

from scripts.validate import REPO_ROOT, load_json, validate_repo


def test_repo_is_consistent():
    errors = validate_repo(REPO_ROOT)
    assert errors == []


def test_both_exams_defined():
    exams = load_json(REPO_ROOT / "config" / "exams.json")
    assert set(exams) == {"pgmp", "pfmp"}


def test_themes_differ_between_exams():
    """DR-01: 切替時にUIテーマ色が全面的に変わるため、テーマは試験ごとに異なる。"""
    exams = load_json(REPO_ROOT / "config" / "exams.json")
    assert exams["pgmp"]["theme"] != exams["pfmp"]["theme"]


def test_taxonomy_weights_sum_to_100():
    for exam_id in ("pgmp", "pfmp"):
        taxonomy = load_json(REPO_ROOT / "config" / f"taxonomy.{exam_id}.json")
        total = sum(d["weight_percent"] for d in taxonomy["domains"])
        assert abs(total - 100) < 0.01, f"{exam_id}: {total}"


def test_question_banks_exist_for_all_domains():
    """G5: PfMP対応は問題バンク追加のみ。両examのバンクファイルが最初から存在する。"""
    exams = load_json(REPO_ROOT / "config" / "exams.json")
    for exam_id, cfg in exams.items():
        for domain_id in cfg["domains"]:
            path = REPO_ROOT / "questions" / exam_id / f"{domain_id}.json"
            assert path.exists(), path
