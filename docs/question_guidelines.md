# 問題作成ガイドライン

本試験に近い「傾向」の問題を作るための基準。調査日：2026-11-03。

## 0. 基本ルール
1. **流出問題（いわゆるdump、「本試験の問題」をうたう販売物）は対象外とする。** 参照も、言い換えての利用もしない。そうしたサイトを情報源として調べることもしない
2. 市販の問題集の問題も写さない。作る問題はすべてオリジナルにする
3. **第5版（The Standard for Program Management – Fifth Edition、2024年）の用語と考え方を優先する**（→ 2章）
4. 体験記などの情報は、英語の情報も含めて集め、[question_seeds.md](question_seeds.md) に「種」として整理してから問題にする

## 1. 本試験の事実（一次情報）
出典：PMI「PgMP Examination Content Outline（March 2024）」、「PgMP Certification Handbook（revised 11 March 2024）」

| 項目 | 内容 |
|---|---|
| 問題数 | 170問（採点150問＋採点されない試行問題20問。どれが試行問題かはわからない） |
| 時間 | 240分（1問あたり約85秒） |
| 形式 | 多肢選択式。「状況（situational）・シナリオ型」の問題 |
| 言語 | **英語のみ。言語補助なし**（このアプリを作る理由） |
| 問題の根拠 | 各問題は**少なくとも2冊の文献**に紐づけられている。PMIの標準に限らない |
| 試験範囲 | ECO（2024年3月に第5版の用語に合わせて軽微な改訂）。ECOとThe Standard for Program Managementは一致しない部分がある |

### ドメインの比率（問題作成時はこの比率に近づける）
| # | ドメイン | 比率 | タスク数 |
|---|---|---|---|
| I | Strategic Program Alignment | 15% | 11 |
| II | Program Life Cycle Management | 44% | 35 |
| III | Benefits Management | 11% | 8 |
| IV | Stakeholder Engagement | 16% | 7 |
| V | Governance | 14% | 11 |

ECOのドメイン一覧表では、IIIは「Benefits Alignment」と表記されている。本文の見出しとハンドブックは「Benefits Management」で、このアプリは後者を使う。

## 2. 第5版を優先する
ネットの情報は第4版以前のものが多い。問題と解説は第5版に合わせる。
ECO（試験範囲）は2024年3月に、第5版の用語に合わせて改訂された。試験のドメインはECOの5つのまま（1章）。

### 第5版の構成（PMI日本支部、P3Mオフィスの解説で確認）
- **8つの原則**：Stakeholders（ステークホルダー）／Benefits Realization（ベネフィット実現）／Synergy（シナジー）／Team of Teams（チームのチーム）／Change（変化）／Leadership（リーダーシップ）／Risk（リスク）／Governance（ガバナンス）
- **6つのパフォーマンス・ドメイン**：Strategic Alignment／Benefits Management／Stakeholder Engagement／Governance Framework／**Collaboration（新設）**／Life Cycle Management
- **ライフサイクル**：Definition（定義。Formulation〈構想〉とPlanning〈計画〉のサブフェーズ）→ Delivery（提供）→ Closure（終結）
- **プログラム活動**：プログラム統合マネジメントは、第4版ではライフサイクルのドメインの一部だったが、第5版ではプログラム活動の1つになった
- 第4版の「プロセスベース」から「**原則ベース**」の標準に変わった。PMBOKガイド第7版と用語・考え方をそろえている

### 問題を作るときの扱い
- 各問題に、関係する第5版の原則を付ける（`principles`）。解説画面にも表示する
- 第5版で新しく入った考え方（シナジー、チームのチーム、コラボレーション、原則にもとづく判断）を、問題に意識して入れる
- 古い情報（第2〜4版の体験記、ITTOの暗記など）は、第5版の考え方に置き換えてから使う。プロセスやITTOの暗記を問う問題は作らない
- ドメイン名はECOの表記を使う（試験はECOに沿って作られるため）

## 3. 出題傾向（合格者の体験記・対策サイトより。二次情報）
詳しくは [question_seeds.md](question_seeds.md)。
- **問題文が長い。** PMPより問題数が少ないのは1問が長いため。本番では練習より時間がかかったという声がある
- 問われやすいもの
  - **出来事の順序、および「なぜその文書を作るのか」**（チャーターの位置づけ、リスク登録の手順、クローズの手順）
  - **コンポーネントのクローズとプログラムのクローズ**
  - **プログラム憲章**
  - PMP範囲の知識（**EVM**、クリティカルパス、品質ツール、リスクツール）も出る
- **プロジェクト視点の答えは誤答になりやすい**（戦略的な視点が求められる）
- 別の問題に答えのヒントが含まれていることや、似た答えの問題が続くこともある

## 4. 問題の書き方
- **ECOのタスクに1つ紐づける**（`domain`＋`task`。例：`D2`＋`T29`。タスクの一覧は config/taxonomy.pgmp.json）。ECOのタスク文を作問の起点にする
- 問題文
  - 3〜5文程度のシナリオにする。**判断に関係のない情報（業界、人数、予算額など）を1つ以上入れる**
  - 問い方は `FIRST` / `NEXT` / `BEST` / `MOST appropriate` / `PRIMARILY` を使い分ける
  - 業界はIT以外も入れる（インフラ、水道、製造、公共、医療など）
  - 長い問題と短い問題を混ぜる（体験記では「長い問題が多い」という声と「75%は短い」という声の両方がある）
- 選択肢
  - 4択。どれも「現場でやりそう」と思える、もっともらしいものにする
  - 正解は「分析・評価 → 計画やガバナンスに沿って対応 → 適切な相手に伝える」の形が基本
  - 誤答は**視点の取り違え**で作る。スキーマ上は `distractor_types` で、もう一方の試験（PfMP）の視点では正解になりうる誤答を `cross_perspective`（最大1つ。cross_perspective_eligible なタスクではちょうど1つ）、それ以外を `plausible` とする（SPEC_v2.md §6）。下の分類は誤答を考えるときの観点
    - プロジェクト視点：成果物・自分の担当範囲・計画どおりを優先する（ベネフィットやコンポーネント間への影響を見ていない）
    - ポートフォリオ視点（`cross_perspective` にする）：投資判断・資金配分・中止判断へ飛ぶ（プログラムマネージャーの権限を超える）
    - 運用視点：機能部門や運用の都合で決める
    - プログラム視点：プログラム視点だが、順序が違う、独断である、ガバナンスを飛ばしている、など
  - 長さと具体性を選択肢間でそろえる（正解だけが長いと見抜けてしまう）。テスト（tests/test_question_bank_quality.py）で、正解が2番目に長い選択肢より4文字以上長い問題がバンクの1割以上になると失敗する
- 計算問題（EVMなど）は全体の1割程度。計算結果の解釈と、その後の行動まで問う
- 解答後の表示用に、`scenario_ja` / `stem_ja` / `options_ja`（訳）、`option_explanations`（選択肢ごとの解説）、`vocab`（単語）を付ける（DR-13）。`explanation` では選択肢を「A」「（D）」のような**記号で呼ばない**（アプリが選択肢を並べ替えるため。選択肢ごとの説明は `option_explanations` に書く）

## 5. やってはいけないこと
- 流出問題（dump）を参照・利用すること（0章の1）。PMIの試験規約違反・著作権侵害になる。公開する予定があるので特に厳守
- 市販問題集の問題を写す、または言い換えて使うこと
- PMIの標準書の文章を長く引用すること。用語と概念を使うのはよい
- 非公式にアップロードされた標準書のPDFを情報源にすること

## 6. 参考
- [PgMP Examination Content Outline (PMI)](https://www.pmi.org/-/media/pmi/documents/public/pdf/certifications/pgmp-exam-content-outline.pdf)
- [PgMP Certification Handbook (PMI)](https://www.pmi.org/-/media/pmi/documents/public/pdf/certifications/program-management-professional-handbook.pdf)
- [PgMP Approach and Lessons Learned (LinkedIn)](https://www.linkedin.com/pulse/pgmp-approach-lessons-learned-joseph-iannetta-pgmp)
- [The Standard for Program Management – Fifth Edition (PMI)](https://www.pmi.org/standards/program-management-fifth-edition)
- [PMI日本支部：The Standard for Program Management 紹介](https://www.pmi-japan.org/post-19775/) — 第5版の8原則と6ドメイン
- [P3Mオフィス：プログラムマネジメント標準の最新版（Fifth Edition）クイックレビュー](https://p3moffice.com/2024/04/pgm-standard-fifth-quickreview/) — 原則ベースへの変更、シナジーとチームのチーム、コラボレーション、3フェーズ
- [The Standard for Program Management Fifth Edition: What's new? (hama-co.net)](https://hama-co.net/2024/03/17/the-standard-for-program-management-fifth-edition-whats-new/) — コラボレーションの内容、統合マネジメントの位置づけの変更
