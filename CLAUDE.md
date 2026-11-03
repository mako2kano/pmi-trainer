# CLAUDE.md

## プロジェクト概要

PMI Adaptive Trainer v2 — PgMP/PfMP両対応のECO準拠シナリオ問題演習PWA
（Phase 1: 個人利用）。仕様の正は **[SPEC_v2.md](./SPEC_v2.md)**。作業前に必ず参照すること。

## 絶対原則（SPEC_v2.md §0）

迷ったらこの3つに立ち返る:

1. **ランタイムAPIコストゼロ** — 問題生成は事前バッチのみ。アプリ本体から
   LLM API・外部サーバーを呼ばない（DR-08）
2. **exam間のデータ完全分離** — マスタリー・SM-2状態・履歴はPgMP/PfMPで
   共有しない。唯一の橋渡しはcross_tagsによる初期出題優先度ヒントのみ（DR-02〜04）
3. **1画面1問**

設計変更が必要になったら、実装より先にSPEC_v2.md §12のDR表に追記すること。
現在の追記済みDR: DR-09（React/Vite/TS → **DR-12で素のJSに置き換え**）・DR-10（問題英語・解説日本語）・
DR-11（ECO転記のソースは作者提供ファイルが正）・DR-12（素のJS PWA）・
DR-13（解答後の日本語訳・選択肢ごとの解説・単語解説）・DR-14（第5版優先、体験記は種として収集、流出問題は対象外）・
DR-15（リポジトリ公開＋GitHub Pages）。

## リポジトリ構成と整合性ルール

- `config/exams.json` — 試験パラメータの唯一の源（DR-06）。模試の問題数・時間・
  配分をコードにハードコードしない（受け入れ基準 §10）
- `config/taxonomy.{pgmp,pfmp}.json` — ECO転記。`verified_against_official_eco` が
  false の間は暫定値。**tasksへの転記はECO原文の複製ではなく要約**とする（§11）
- `questions/<exam>/<domain>.json` — 問題バンク。1問のスキーマは
  `schemas/question.schema.json` が正
- スキーマ（`schemas/`）を変更したら `scripts/validate.py` の対応する
  不変条件チェックも**両方**更新すること（tests/ が整合を検証している）

### distractor_types の解釈（要注意）

SPEC §6の「誤答4択のうち1つ」は、実装上は「4択（正解1＋誤答3）のうち
誤答の最大1つを cross_perspective とする」と解釈している（§7の例
`["plausible", "cross_perspective", "plausible", null]` が4要素・null=正解位置
であることに基づく。実試験も4択）。distractor_types は options と同じ並びで、
null がちょうど1つ・answer_index の位置にあること。

### 言語ポリシー（DR-10）

- `scenario` / `stem` / `options`: 英語（実試験に合わせる）
- `explanation`: 日本語（作者の学習効率優先）
- taxonomy: `name`（英語公式名）＋`name_ja`、task は `summary`（英）＋`summary_ja`（日）
- DR-13の任意項目（解答後に表示）: `scenario_ja` / `stem_ja` / `options_ja`（訳）、
  `option_explanations`（選択肢ごとの解説、日本語）、`vocab`（`en`/`ja`/`note`）
- DR-14の任意項目: `principles`（第5版の8原則）。問題作成の基準は docs/question_guidelines.md、
  種は docs/question_seeds.md。**流出問題（dump）は参照・利用・調査しない**

## 開発時の注意

- Python は最新の安定版（2026-11時点 3.15）を使う。生成パイプラインの anthropic SDK 2.x は 3.10 以上が必要。
  環境作成: `python3.15 -m venv .venv && .venv/bin/pip install pytest jsonschema -r pipeline/requirements.txt`
- バージョンは極力最新に合わせる（作者方針）。GitHub Actions と pipeline の依存は Dependabot（.github/dependabot.yml）が毎週更新PRを出す
- テスト実行: `pytest tests/`（jsonschema未インストールならスキーマ検証のみスキップ）
- 整合チェックCLI: `python -m scripts.validate`
- `scripts/` は外部ライブラリ・API・MCPに依存しない純粋Pythonを保つ
- PWA実装（M3〜）は `app/` にビルド不要の素のJSで置く（DR-12）。npm等のツールチェーンを持ち込まない
- 公開用サイトは `python -m scripts.build_site` で `_site/` に組み立てる（app/＋config/＋questions/）。
  GitHub Actions（.github/workflows/pages.yml）が main へのpushでPagesにデプロイする（DR-15）
- ローカル確認: `python -m scripts.build_site && python -m http.server -d _site 8000`
- 生成パイプライン（M2）のEvaluatorには `perspective_check`（0〜1）を含める（§6）
- ECOファイル（公式PDF）が必要なタイミングでは作者に依頼する。Webの公式公開
  情報での暫定転記は可だが、`verified_against_official_eco` は作者照合まで
  false のまま（DR-11）

## 法務（SPEC_v2.md §11）

PMI実問・公式模擬問題・SPM/SPfM本文の複製不可。ECO構造参照のオリジナル生成のみ。
生成した問題がこれに抵触しないことはM2/M6の作者レビューで確認する。
