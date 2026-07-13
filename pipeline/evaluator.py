"""Evaluator: 生成問題の自動評価（純粋Python・テスト対象）。

2層構成:
1. 決定的チェック（本モジュール）— 構造・distractor規則・言語ポリシー・
   クロス視点distractorの有無。API非依存。
2. perspective_check（0〜1）— LLM採点。generate.py が
   prompts.build_perspective_check_prompt を使って実施し、
   attach_perspective_check() で結果をマージする。

決定的チェックは scripts.validate の不変条件を再利用し、Evaluator固有の
較正指標（合否・警告）を足す。SPEC_v2.md §6。
"""

from __future__ import annotations

from scripts.validate import validate_question

# perspective_check の合格閾値（M2で作者較正）。暫定値。
PERSPECTIVE_CHECK_THRESHOLD = 0.7


def _has_cjk(text: str) -> bool:
    return any(
        "぀" <= c <= "ヿ"  # ひらがな・カタカナ
        or "一" <= c <= "鿿"  # 漢字
        for c in text
    )


def _mostly_ascii(text: str, threshold: float = 0.9) -> bool:
    if not text:
        return False
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return ascii_count / len(text) >= threshold


def language_warnings(q: dict) -> list[str]:
    """DR-10: scenario/stem/options=英語、explanation=日本語。

    決定的に断定できないためエラーではなく警告（作者判断に委ねる）。
    """
    warnings = []
    for key in ("scenario", "stem"):
        if q.get(key) and not _mostly_ascii(q[key]):
            warnings.append(f"{key} は英語のはず（非ASCII比率が高い）")
    for i, opt in enumerate(q.get("options", [])):
        if opt and not _mostly_ascii(opt):
            warnings.append(f"options[{i}] は英語のはず")
    if q.get("explanation") and not _has_cjk(q["explanation"]):
        warnings.append("explanation は日本語のはず（CJK文字がない）")
    return warnings


def cross_perspective_count(q: dict) -> int:
    return q.get("distractor_types", []).count("cross_perspective")


def evaluate_question(
    q: dict,
    exam: str,
    domain_id: str,
    valid_tasks: set[str] | None = None,
    require_cross_perspective: bool = False,
) -> dict:
    """1問を評価し、レポート dict を返す。

    passed_structural: 決定的チェックに全て合格したか
    errors: 構造・規則違反（合否を左右する）
    warnings: 言語ポリシー等の要目視項目
    """
    errors = list(validate_question(q, exam, domain_id, valid_tasks))

    cp = cross_perspective_count(q)
    if require_cross_perspective and cp != 1:
        errors.append(
            "このタスクは cross_perspective_eligible。"
            f"cross_perspective distractor をちょうど1つ持つこと（現在 {cp}）"
        )

    return {
        "id": q.get("id"),
        "passed_structural": not errors,
        "errors": errors,
        "warnings": language_warnings(q),
        "cross_perspective_count": cp,
        "perspective_check": (q.get("evaluator") or {}).get("perspective_check"),
    }


def attach_perspective_check(
    q: dict, score: float, model: str, evaluated_at: str
) -> dict:
    """LLM採点結果を question.evaluator に書き込む（schemaの evaluator 準拠）。"""
    ev = dict(q.get("evaluator") or {})
    ev["perspective_check"] = score
    ev["model"] = model
    ev["evaluated_at"] = evaluated_at
    q["evaluator"] = ev
    return q


def perspective_check_passed(q: dict, threshold: float = PERSPECTIVE_CHECK_THRESHOLD) -> bool:
    score = (q.get("evaluator") or {}).get("perspective_check")
    return isinstance(score, (int, float)) and score >= threshold
