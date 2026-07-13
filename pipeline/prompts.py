"""Generator/Evaluator用プロンプト生成（純粋Python・テスト対象）。

M1で両ECOのtaxonomyを揃えたのは、この視点ガードを両ECOの対比で
精密にするため（SPEC_v2.md §13）。生成対象試験の視点だけでなく、
「もう一方の試験の視点」を明示してクロス視点distractorを成立させる。
"""

from __future__ import annotations

import json

# 各試験の「正解を導く視点」。SPEC_v2.md §1・§5・§6 の中核。
PERSPECTIVES = {
    "pgmp": {
        "role": "program manager",
        "role_ja": "プログラムマネジャー",
        "lens": (
            "the accountable owner of BENEFITS DELIVERY. The program manager "
            "integrates constituent projects to realize and sustain benefits "
            "aligned to strategy. The correct action is the one that best "
            "protects benefits realization within the program's mandate."
        ),
        "lens_ja": "便益デリバリーの責任者（プログラム全体の便益実現・維持に責任を持つ）",
    },
    "pfmp": {
        "role": "portfolio manager",
        "role_ja": "ポートフォリオマネジャー",
        "lens": (
            "the INVESTMENT DECISION maker. The portfolio manager selects, "
            "prioritizes, and balances components to maximize the value of the "
            "whole portfolio against strategy and constraints. The correct "
            "action is the one that best optimizes the portfolio-level "
            "investment decision, not the delivery of any single component."
        ),
        "lens_ja": "投資判断者（ポートフォリオ全体の価値最大化のため構成要素を選定・優先順位付け・バランスする）",
    },
}

# 言語ポリシー（DR-10）
LANGUAGE_POLICY = (
    "LANGUAGE POLICY (strict): `scenario`, `stem`, and every string in "
    "`options` MUST be written in ENGLISH (the real exam is in English). "
    "`explanation` MUST be written in JAPANESE (日本語) for the author's "
    "study efficiency."
)

# 法務（SPEC_v2.md §11）
LEGAL_GUARD = (
    "LEGAL (mandatory): Do NOT reproduce, paraphrase closely, or memorize any "
    "real PMI exam item, official practice question, or verbatim text from The "
    "Standard for Program/Portfolio Management. Generate ORIGINAL scenarios "
    "that only reference the ECO domain/task STRUCTURE."
)


def other_exam(exam: str) -> str:
    return "pfmp" if exam == "pgmp" else "pgmp"


def build_generation_prompt(
    exam: str,
    domain: dict,
    task: dict,
    count: int = 1,
) -> dict:
    """1タスクぶんの生成プロンプト（system/user）を組み立てて返す。

    domain: taxonomy の domains[] の1要素
    task:   その domain の tasks[] の1要素
    """
    if exam not in PERSPECTIVES:
        raise ValueError(f"unknown exam: {exam}")

    me = PERSPECTIVES[exam]
    other = PERSPECTIVES[other_exam(exam)]
    eligible = task.get("cross_perspective_eligible", False)

    system = (
        f"You are an expert item writer for the PMI {exam.upper()} certification "
        f"exam. You write scenario-based, single-best-answer multiple-choice "
        f"questions with exactly four options. The candidate must answer AS the "
        f"{me['role']}: {me['lens']}\n\n"
        f"For contrast, the other credential ({other_exam(exam).upper()}) is "
        f"answered as the {other['role']}: {other['lens']}\n\n"
        f"{LANGUAGE_POLICY}\n\n{LEGAL_GUARD}"
    )

    cross_instr = (
        "CROSS-PERSPECTIVE DISTRACTOR (required for this task): make EXACTLY ONE "
        f"of the three distractors an action that would be CORRECT for a "
        f"{other['role']} ({other['lens_ja']}) but is WRONG for the "
        f"{me['role']} here. Tag it `cross_perspective` in `distractor_types`. "
        "In `explanation`, state explicitly why it is wrong from the "
        f"{me['role_ja']}視点."
        if eligible
        else (
            "This task is not marked cross_perspective_eligible; use only "
            "`plausible` distractors (no `cross_perspective`)."
        )
    )

    schema_hint = {
        "id": f"{exam}-{domain['id']}-NNNN",
        "exam": exam,
        "domain": domain["id"],
        "task": task["id"],
        "cross_tags": ["governance | stakeholder | benefits_value | risk (0..n)"],
        "scenario": "English scenario",
        "stem": "English question stem",
        "options": ["English A", "English B", "English C", "English D"],
        "answer_index": "0..3 (index of the correct option)",
        "distractor_types": [
            "one null at answer_index; others 'plausible' or (<=1) 'cross_perspective'"
        ],
        "explanation": "日本語の解説（なぜ正解か・各誤答がなぜ誤りか）",
    }

    user = (
        f"Write {count} original {exam.upper()} question(s) for:\n"
        f"Domain {domain['id']} — {domain['name']}\n"
        f"Task {task['id']}: {task['summary']}\n\n"
        f"{cross_instr}\n\n"
        f"Set `cross_tags` from {{governance, stakeholder, benefits_value, risk}} "
        f"reflecting the theme (used only as a cross-exam priority hint, DR-04).\n\n"
        f"Return STRICT JSON: a list of objects with this shape (no prose):\n"
        f"{json.dumps(schema_hint, ensure_ascii=False, indent=2)}"
    )

    return {"system": system, "user": user, "cross_perspective_required": eligible}


def build_perspective_check_prompt(question: dict, exam: str) -> dict:
    """Evaluatorのperspective_check用プロンプト（SPEC_v2.md §6）。

    「正解が当該試験の視点で一意に定まるか。もう一方の視点の正解と
    紛らわしすぎないか」を0〜1で採点させる。
    """
    me = PERSPECTIVES[exam]
    other = PERSPECTIVES[other_exam(exam)]
    system = (
        "You are a strict psychometric reviewer for PMI exam items. "
        "Return ONLY JSON: {\"perspective_check\": <float 0..1>, \"reason\": <str>}."
    )
    user = (
        f"Target credential: {exam.upper()} — answered as the {me['role']} "
        f"({me['lens']}).\n"
        f"Other credential: {other_exam(exam).upper()} — the {other['role']} "
        f"({other['lens']}).\n\n"
        "Score 0..1: is the keyed answer UNIQUELY correct from the target "
        "perspective, and NOT overly confusable with what the other "
        "perspective would choose? 1.0 = crisp single best answer; "
        "0.0 = ambiguous or the other perspective's answer is equally valid.\n\n"
        f"QUESTION JSON:\n{json.dumps(question, ensure_ascii=False, indent=2)}"
    )
    return {"system": system, "user": user}
