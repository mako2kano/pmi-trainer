# PMI Adaptive Trainer v2

PgMP/PfMP受験者向けの、ECO準拠シナリオ問題演習PWA（Phase 1: 個人利用）。
スキマ時間の演習で苦手ドメイン/タスクを定量特定し、合格到達度を可視化する。

仕様は **[SPEC_v2.md](./SPEC_v2.md)** が正。開発ガイドは [CLAUDE.md](./CLAUDE.md)。

**アプリ：https://mako2kano.github.io/pmi-trainer/** （iPhoneのSafariで開き、共有メニュー →「ホーム画面に追加」でオフラインでも使える）

## 設計の核

- **視点混線の防止**: PgMP（便益デリバリー責任者）とPfMP（投資判断者）は
  シナリオが酷似するが正解を導く視点が異なる。exam間でマスタリー・履歴を
  完全分離し、切替はアプリ最上位の明示操作のみ（DR-01〜04）
- **クロス視点distractor**: 誤答のうち1つを「もう一方の試験の視点では正解に
  なり得る行動」とし、視点の切り替え進捗そのものを定量化する（DR-05）
- **ランタイムAPIコストゼロ**: 問題は事前バッチ生成、採点・分析は全てローカル（DR-08）
- 技術スタック: ビルド不要の素のJS PWA（DR-12。DR-09のReactを置き換え）。GitHub Pagesで配信（DR-15）
- 言語: 問題文・選択肢は英語（実試験準拠）、解説は日本語（DR-10）。解答後に問題文・選択肢の日本語訳、選択肢ごとの解説、英単語の解説を表示（DR-13）
- 問題作成: 第5版の用語・原則を優先し、体験記は種として整理。流出問題（dump）は対象外（DR-14、[docs/question_guidelines.md](./docs/question_guidelines.md)）

## リポジトリ構成

```
SPEC_v2.md          仕様書（正）。設計変更はDR（§12）追記が先
app/                PWA本体（素のJS、DR-12）。config/・questions/ を読んで動く
docs/               問題作成ガイドライン（question_guidelines.md）・問題の種（question_seeds.md）
config/
  exams.json        試験パラメータ（模試問題数・時間・ドメイン・テーマ色）
  taxonomy.pgmp.json / taxonomy.pfmp.json
                    ECO転記（ドメイン・タスク・出題比率）
questions/
  pgmp/D1..D5.json  ドメイン別問題バンク（80問：パイロット50問＋訳・単語解説つき30問。M4で500問へ）
  pfmp/D1..D5.json  （M6で生成）
schemas/            上記JSONのスキーマ定義（構造の正）＋examples/（テスト基準データ）
scripts/validate.py config/questions のファイル間整合チェック（純粋Python・CLI兼用）
scripts/build_site.py  GitHub Pages用に app/＋config/＋questions/ を _site/ に組み立てる
.github/workflows/   main へのpushでテスト → Pagesへデプロイ（DR-15）
pipeline/           問題生成バッチ（DR-08: アプリ外）。prompts/evaluator（純粋Python）
                    ＋generate（Anthropic SDKラッパー）。詳細は pipeline/README.md
tests/              pytest（jsonschemaはoptional）
```

## 開発

```bash
# 初回のみ（Python 3.15）
python3.15 -m venv .venv && .venv/bin/pip install pytest jsonschema -r pipeline/requirements.txt
source .venv/bin/activate

pytest tests/                 # テスト
python -m scripts.validate    # config/・questions/ の整合チェック

# アプリをローカルで確認
python -m scripts.build_site && python -m http.server -d _site 8000
```

## ステータス（マイルストーン）

- [x] M1: リポジトリ初期化＋exams.json/taxonomy整備（両ECO転記完了: PgMP 72タスク/PfMP 35タスク）
- [~] M2: 生成パイプライン（`pipeline/`）完成。PgMP 80問投入済み・全問Evaluator通過（作者レビュー待ち）。パイロット50問は訳・単語解説（DR-13）が未付与
- [~] M3: PWA骨格。ドリル画面（素のJS）とGitHub Pagesへのデプロイまで完了。exam切替機構はPfMPバンク投入時に実装
- [ ] M4: PgMPフルバンク500問＋適応出題
- [ ] M5: ダッシュボード＋模試モード
- [ ] M6: PfMPバンク生成（クロス視点distractor込み）
- [ ] M7: クロス視点誤答率カード＋ロック解除

## 成績の保存について

- 成績は端末のブラウザ内（localStorage、examごとに別キー）にだけ保存し、サーバーには送らない
- **端末をまたいだ記録・同期はされない。** 同じiPhoneでも、Safariとホーム画面に追加したアプリでは別々に記録される
- アプリの削除やSafariのWebサイトデータ消去で成績も消える。Safariで開いて使う場合は、しばらく使わないとiOSが自動削除することがある（ホーム画面のアプリは対象外）

## 法務上の注意

PMI実問・公式模擬問題・SPM/SPfM本文の複製は不可。本リポジトリの問題は
ECO構造を参照したオリジナル生成に限る（SPEC_v2.md §11）。
PgMP®・PfMP® はProject Management Institute, Inc. の登録商標。本ツールはPMI非公認。
