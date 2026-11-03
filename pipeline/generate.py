"""問題生成オーケストレータ（薄いラッパー・テスト対象外）。

DR-08に従い、これは作者がローカル/CIで実行する事前バッチ処理。
アプリ（PWA）はこのコードを一切呼ばない。

依存: anthropic SDK（`pip install -r pipeline/requirements.txt`）と
環境変数 ANTHROPIC_API_KEY。ロジックは prompts.py / evaluator.py 側にあり、
本モジュールはAPI呼び出しと入出力の配線のみを担う。

使い方:
    python -m pipeline.generate --exam pgmp --domain D2 --count 10
    python -m pipeline.generate --exam pgmp --domain D2 --task T13 --count 3
    python -m pipeline.generate --exam pgmp --domain D2 --dry-run   # プロンプト確認のみ

生成物は questions/<exam>/<domain>.json に追記され、
scripts.validate と pipeline.evaluator を通過したものだけが残る。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

from pipeline import evaluator, prompts
from scripts.validate import REPO_ROOT, load_json

GEN_MODEL_DEFAULT = "claude-sonnet-5-5"  # SPEC「実装予定モデル: Claude Sonnet系」の最新
EVAL_MODEL_DEFAULT = "claude-sonnet-5-5"
# Sonnet 5.5は既定で思考（adaptive thinking）し、思考もmax_tokensに数えられる
MAX_TOKENS = 16000
# 安全分類器が断った（stop_reason="refusal"）ときに、API推奨のモデルで自動的に再実行する
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class RefusalError(RuntimeError):
    """フォールバック先も含めてモデルが応答を断った。"""


def _load_taxonomy(exam: str) -> dict:
    return load_json(REPO_ROOT / "config" / f"taxonomy.{exam}.json")


def _domain(taxonomy: dict, domain_id: str) -> dict:
    for d in taxonomy["domains"]:
        if d["id"] == domain_id:
            return d
    raise SystemExit(f"domain {domain_id} が taxonomy.{taxonomy['exam']} にない")


def _client():
    try:
        import anthropic
    except ImportError:
        raise SystemExit(
            "anthropic SDK 未インストール。pip install -r pipeline/requirements.txt"
        )
    return anthropic.Anthropic()  # ANTHROPIC_API_KEY を環境から読む


def _ask_json(client, model, system, user):
    msg = client.beta.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
        betas=[FALLBACK_BETA],
        fallbacks="default",
    )
    if msg.stop_reason == "refusal":
        category = getattr(msg.stop_details, "category", None)
        raise RefusalError(f"{model} が応答を断った（category={category}）")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError(f"max_tokens（{MAX_TOKENS}）に達して出力が途中で切れた")
    # 思考ブロック（thinking）などは除き、textブロックだけを読む
    text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
    # ```json フェンスを剥がす
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1].removeprefix("json").strip()
    return json.loads(text)


def _next_seq(bank: dict) -> int:
    seqs = [int(q["id"].rsplit("-", 1)[1]) for q in bank["questions"] if q.get("id")]
    return (max(seqs) + 1) if seqs else 1


def generate_for_task(client, exam, domain, task, count, gen_model, eval_model):
    """1タスクぶきを生成→perspective_check採点。生成問題のリストを返す。"""
    p = prompts.build_generation_prompt(exam, domain, task, count)
    drafts = _ask_json(client, gen_model, p["system"], p["user"])
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    out = []
    for q in drafts:
        q.setdefault("exam", exam)
        q.setdefault("domain", domain["id"])
        q.setdefault("task", task["id"])
        pc = prompts.build_perspective_check_prompt(q, exam)
        score = _ask_json(client, eval_model, pc["system"], pc["user"])
        evaluator.attach_perspective_check(
            q, float(score.get("perspective_check", 0)), eval_model, now
        )
        q["reviewed"] = False
        out.append(q)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="PMI Trainer 問題生成バッチ（DR-08: アプリ外）")
    ap.add_argument("--exam", required=True, choices=["pgmp", "pfmp"])
    ap.add_argument("--domain", required=True)
    ap.add_argument("--task", help="省略時はドメイン内の全タスクを対象")
    ap.add_argument("--count", type=int, default=1, help="タスクあたり生成数")
    ap.add_argument("--gen-model", default=GEN_MODEL_DEFAULT)
    ap.add_argument("--eval-model", default=EVAL_MODEL_DEFAULT)
    ap.add_argument("--dry-run", action="store_true", help="プロンプトを表示するだけ")
    args = ap.parse_args(argv)

    taxonomy = _load_taxonomy(args.exam)
    domain = _domain(taxonomy, args.domain)
    tasks = [t for t in domain["tasks"] if not args.task or t["id"] == args.task]
    if not tasks:
        raise SystemExit(f"task {args.task} が {args.domain} にない")

    if args.dry_run:
        for t in tasks:
            p = prompts.build_generation_prompt(args.exam, domain, t, args.count)
            print(f"\n===== {args.exam} {domain['id']} {t['id']} =====")
            print("[SYSTEM]\n", p["system"])
            print("[USER]\n", p["user"])
        return 0

    client = _client()
    valid_tasks = {t["id"] for t in domain["tasks"]}
    bank_path = REPO_ROOT / "questions" / args.exam / f"{args.domain}.json"
    bank = load_json(bank_path)

    accepted, rejected = [], []
    for t in tasks:
        try:
            generated = generate_for_task(
                client, args.exam, domain, t, args.count, args.gen_model, args.eval_model
            )
        except RefusalError as e:
            print(f"  スキップ {domain['id']}-{t['id']}: {e}")
            continue
        for q in generated:
            q["id"] = f"{args.exam}-{args.domain}-{_next_seq(bank):04d}"
            report = evaluator.evaluate_question(
                q, args.exam, args.domain, valid_tasks,
                require_cross_perspective=t.get("cross_perspective_eligible", False),
            )
            if report["passed_structural"] and evaluator.perspective_check_passed(q):
                bank["questions"].append(q)
                accepted.append(report)
            else:
                rejected.append(report)

    bank_path.write_text(
        json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"採用 {len(accepted)} / 却下 {len(rejected)} → {bank_path}")
    for r in rejected:
        print("  却下:", r["errors"] or f"perspective_check={r['perspective_check']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
