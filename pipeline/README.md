# pipeline/ — 問題生成バッチ

**DR-08**: これはアプリ外の事前バッチ処理。PWA本体はこのコードもLLM APIも
一切呼ばない。作者がローカル/CIで問題バンクを作るときだけ実行する。

## 構成

| ファイル | 役割 | API依存 | テスト |
|---------|------|--------|--------|
| `prompts.py` | Generator/Evaluator用プロンプト組み立て。両ECOの視点対比・言語ポリシー・§11法務ガードを埋め込む | なし | あり |
| `evaluator.py` | 決定的チェック（構造・distractor規則・言語警告・クロス視点有無）＋perspective_checkのマージ | なし | あり |
| `generate.py` | Anthropic SDKを呼ぶオーケストレータ | あり | なし（薄いラッパー） |

ロジックは `prompts.py` / `evaluator.py` に置き、`generate.py` はAPI配線のみ。

## 使い方

```bash
pip install -r pipeline/requirements.txt
export ANTHROPIC_API_KEY=...

# プロンプトだけ確認（APIを呼ばない）
python -m pipeline.generate --exam pgmp --domain D2 --dry-run

# ドメインD2の全タスクを各1問生成
python -m pipeline.generate --exam pgmp --domain D2 --count 1

# 特定タスクを3問
python -m pipeline.generate --exam pgmp --domain D2 --task T13 --count 3
```

生成物は `questions/<exam>/<domain>.json` に追記され、`scripts.validate` の
構造チェックと `evaluator` の perspective_check 閾値（既定0.7、M2で作者較正）を
通過したものだけが残る。`reviewed: false` で入るので、作者レビュー後に true にする。

## 生成の中核設計（SPEC_v2.md §6）

各問題は生成対象試験の視点（PgMP=便益デリバリー責任者 / PfMP=投資判断者）で
解答が一意に定まるよう作る。`cross_perspective_eligible` なタスクでは、誤答の
ちょうど1つを「もう一方の試験の視点では正解になり得る行動」とし、explanationで
なぜ当該視点では誤りかを明示する。これによりクロス視点誤答率（§6・§9）を
訓練項目として集計できる。
