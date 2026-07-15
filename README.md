# PMI Adaptive Trainer v2

PgMP/PfMP受験者向けの、ECO準拠シナリオ問題演習PWA（Phase 1: 個人利用）。
スキマ時間の演習で苦手ドメイン/タスクを定量特定し、合格到達度を可視化する。

仕様は **[SPEC_v2.md](./SPEC_v2.md)** が正。開発ガイドは [CLAUDE.md](./CLAUDE.md)。

## 設計の核

- **視点混線の防止**: PgMP（便益デリバリー責任者）とPfMP（投資判断者）は
  シナリオが酷似するが正解を導く視点が異なる。exam間でマスタリー・履歴を
  完全分離し、切替はアプリ最上位の明示操作のみ（DR-01〜04）
- **クロス視点distractor**: 誤答のうち1つを「もう一方の試験の視点では正解に
  なり得る行動」とし、視点の切り替え進捗そのものを定量化する（DR-05）
- **ランタイムAPIコストゼロ**: 問題は事前バッチ生成、採点・分析は全てローカル（DR-08）
- 技術スタック: React（Vite＋TypeScript）PWA・IndexedDB（DR-09）
- 言語: 問題文・選択肢は英語（実試験準拠）、解説は日本語（DR-10）

## リポジトリ構成

```
SPEC_v2.md          仕様書（正）。設計変更はDR（§12）追記が先
config/
  exams.json        試験パラメータ（模試問題数・時間・ドメイン・テーマ色）
  taxonomy.pgmp.json / taxonomy.pfmp.json
                    ECO転記（ドメイン・タスク・出題比率）
questions/
  pgmp/D1..D5.json  ドメイン別問題バンク（M2パイロット50問投入済み・M4で500問へ）
  pfmp/D1..D5.json  （M6で生成）
schemas/            上記JSONのスキーマ定義（構造の正）＋examples/（テスト基準データ）
scripts/validate.py config/questions のファイル間整合チェック（純粋Python・CLI兼用）
pipeline/           問題生成バッチ（DR-08: アプリ外）。prompts/evaluator（純粋Python）
                    ＋generate（Anthropic SDKラッパー）。詳細は pipeline/README.md
tests/              pytest（jsonschemaはoptional）
```

## 開発

```bash
pytest tests/                 # テスト
python -m scripts.validate    # config/・questions/ の整合チェック
```

## ステータス（マイルストーン）

- [x] M1: リポジトリ初期化＋exams.json/taxonomy整備（両ECO転記完了: PgMP 72タスク/PfMP 35タスク）
- [~] M2: 生成パイプライン（`pipeline/`）完成。PgMPパイロット50問投入済み・全問Evaluator通過（作者レビュー待ち）
- [ ] M3: PWA骨格（ドリル・exam切替機構）
- [ ] M4: PgMPフルバンク500問＋適応出題
- [ ] M5: ダッシュボード＋模試モード
- [ ] M6: PfMPバンク生成（クロス視点distractor込み）
- [ ] M7: クロス視点誤答率カード＋ロック解除

## 法務上の注意

PMI実問・公式模擬問題・SPM/SPfM本文の複製は不可。本リポジトリの問題は
ECO構造を参照したオリジナル生成に限る（SPEC_v2.md §11）。
PgMP®・PfMP® はProject Management Institute, Inc. の登録商標。本ツールはPMI非公認。
