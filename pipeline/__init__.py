"""問題生成パイプライン（M2〜）。

DR-08: これはアプリ外の事前バッチ処理である。アプリ本体（PWA）は
LLM APIを一切呼ばない。本パッケージは作者がローカル/CIで問題バンクを
生成・評価するときにのみ実行する。

- prompts.py / evaluator.py: 純粋Python（API非依存・テスト対象）
- generate.py: Anthropic SDKを呼ぶ薄いオーケストレータ（テスト対象外）
"""
