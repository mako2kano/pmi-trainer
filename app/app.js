'use strict';

// PMI Adaptive Trainer — M3 ドリル画面（SPEC_v2.md、DR-12: 素のJS）
// データは config/ と questions/ をそのまま読む（scripts/build_site.py が _site/ に同梱する）

// exam切替（DR-01）はPfMPバンク投入時（M6〜M7）に実装する。M3はPgMP固定
const EXAM = 'pgmp';
// DR-02/03: 成績はexamごとに独立したキーで保存する
const STORAGE_KEY = `pmi-trainer:${EXAM}:history:v1`;

// 第5版の8原則（DR-14）
const PRINCIPLE_LABEL = {
  'Stakeholders': 'ステークホルダー',
  'Benefits Realization': 'ベネフィット実現',
  'Synergy': 'シナジー',
  'Team of Teams': 'チームのチーム',
  'Change': '変化',
  'Leadership': 'リーダーシップ',
  'Risk': 'リスク',
  'Governance': 'ガバナンス',
};
const CROSS_PERSPECTIVE_LABEL = {
  pgmp: 'ポートフォリオ視点（PfMPなら正解になりうる）',
  pfmp: 'プログラム視点（PgMPなら正解になりうる）',
};

const $ = (id) => document.getElementById(id);
const letter = (i) => String.fromCharCode(65 + i);

let exam = null;
let domains = [];      // taxonomy.domains
let questions = [];
let current = null;
let history = loadHistory();

// history: { [questionId]: { attempts, correct, lastCorrect, streak, crossMisses } }
function loadHistory() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; }
  catch { return {}; }
}
function saveHistory() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

// 未回答・直近誤答ほど出やすく、連続正解するほど出にくくする簡易な適応出題（SM-2はM4）
function weight(q) {
  const h = history[q.id];
  if (!h) return 3;
  if (!h.lastCorrect) return 4;
  return h.streak >= 2 ? 0.3 : 1;
}

function pool() {
  const domain = $('sel-domain').value;
  const mode = $('sel-mode').value;
  let list = questions.filter((q) => domain === 'all' || q.domain === domain);
  if (mode === 'wrong') list = list.filter((q) => history[q.id] && !history[q.id].lastCorrect);
  if (list.length > 1 && current) list = list.filter((q) => q.id !== current.id);
  return list;
}

function pickNext() {
  const list = pool();
  if (list.length === 0) return null;
  if ($('sel-mode').value === 'random') return list[Math.floor(Math.random() * list.length)];
  const weights = list.map(weight);
  let r = Math.random() * weights.reduce((a, b) => a + b, 0);
  for (let i = 0; i < list.length; i++) {
    r -= weights[i];
    if (r <= 0) return list[i];
  }
  return list[list.length - 1];
}

// 正解の位置を覚えてしまわないよう、出題のたびに選択肢を並べ替える。
// ただし選択肢ごとの解説（option_explanations）がない問題は、explanation が
// 「（D）」「Aは〜」のように元の並びの記号で書かれているので並べ替えない
// （バンク側で正解位置が均等になるよう調整済み）
function shuffled(q) {
  if (!q.option_explanations) return q;
  const order = q.options.map((_, i) => i);
  for (let i = order.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  const pick = (arr) => (arr ? order.map((i) => arr[i]) : null);
  return {
    ...q,
    options: pick(q.options),
    options_ja: pick(q.options_ja),
    option_explanations: pick(q.option_explanations),
    distractor_types: pick(q.distractor_types),
    answer_index: order.indexOf(q.answer_index),
  };
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  Object.assign(node, attrs);
  for (const c of children) node.append(c);
  return node;
}

function domainOf(id) {
  return domains.find((d) => d.id === id);
}
function taskOf(q) {
  return domainOf(q.domain)?.tasks.find((t) => t.id === q.task);
}

function renderVocab(target, vocab) {
  target.replaceChildren(...(vocab || []).map((v) => el('li', {},
    el('span', { className: 'en', lang: 'en', textContent: v.en }),
    el('span', { className: 'ja', textContent: v.ja }),
    v.note ? el('span', { className: 'note', textContent: v.note }) : '',
  )));
}

function showQuestion() {
  const next = pickNext();
  current = next && shuffled(next);
  $('result').classList.add('hidden');
  $('btn-next').classList.add('hidden');
  $('hint').classList.add('hidden');
  $('empty').classList.toggle('hidden', !!current);
  $('question-card').classList.toggle('hidden', !current);
  if (!current) return;

  const d = domainOf(current.domain);
  $('q-domain').textContent = d ? `${d.id} ${d.name_ja}` : current.domain;
  $('q-id').textContent = `${current.id} · ECO ${current.domain}-${current.task}`;
  $('q-scenario').textContent = current.scenario;
  $('q-stem').textContent = current.stem;
  $('btn-hint').classList.toggle('hidden', !current.vocab?.length);
  renderVocab($('hint'), current.vocab);

  $('choices').replaceChildren(...current.options.map((text, i) => {
    const btn = el('button', {},
      el('span', { className: 'label', textContent: letter(i) }),
      el('span', { textContent: text }));
    btn.addEventListener('click', () => answer(i));
    return el('li', {}, btn);
  }));
  window.scrollTo(0, 0);
}

function answer(index) {
  const ok = index === current.answer_index;
  const h = history[current.id] || { attempts: 0, correct: 0, streak: 0, crossMisses: 0 };
  h.attempts += 1;
  if (ok) h.correct += 1;
  h.streak = ok ? h.streak + 1 : 0;
  h.lastCorrect = ok;
  // クロス視点誤答率（SPEC §6）の集計用
  if (!ok && current.distractor_types[index] === 'cross_perspective') h.crossMisses = (h.crossMisses || 0) + 1;
  history[current.id] = h;
  saveHistory();

  document.querySelectorAll('#choices button').forEach((btn, i) => {
    btn.disabled = true;
    if (i === current.answer_index) btn.classList.add('correct');
    else if (i === index) btn.classList.add('wrong');
  });

  $('verdict').textContent = ok ? '正解！' : `不正解（正解は ${letter(current.answer_index)}）`;
  $('verdict').className = `verdict ${ok ? 'ok' : 'ng'}`;

  const ja = [current.scenario_ja, current.stem_ja].filter(Boolean).join('');
  $('sec-translation').classList.toggle('hidden', !ja);
  $('question-ja').textContent = ja;

  $('explanation').textContent = current.explanation;
  const principles = current.principles || [];
  $('principles').replaceChildren(...(principles.length
    ? [el('span', { className: 'principles-label', textContent: '関連する原則（第5版）' }),
       ...principles.map((p) => el('span', { className: 'chip', textContent: `${PRINCIPLE_LABEL[p] || p} ${p}` }))]
    : []));
  const task = taskOf(current);
  $('eco-task').textContent = task ? `ECOタスク ${current.domain}-${current.task}：${task.summary_ja}` : '';

  const hasNotes = current.options_ja || current.option_explanations;
  $('sec-notes').classList.toggle('hidden', !hasNotes);
  if (hasNotes) {
    $('choice-notes').replaceChildren(...current.options.map((_, i) => {
      const isAnswer = i === current.answer_index;
      const head = el('div', { className: 'head' }, `${letter(i)} ${isAnswer ? '◯' : '×'}`);
      if (current.distractor_types[i] === 'cross_perspective') {
        head.append(el('span', { className: 'persp', textContent: CROSS_PERSPECTIVE_LABEL[EXAM] }));
      }
      return el('li', { className: isAnswer ? 'ok' : '' },
        head,
        current.options_ja ? el('div', { className: 'translation', textContent: `訳：${current.options_ja[i]}` }) : '',
        current.option_explanations ? el('div', { textContent: current.option_explanations[i] }) : '');
    }));
  }
  $('sec-vocab').classList.toggle('hidden', !current.vocab?.length);
  renderVocab($('vocab'), current.vocab);

  $('result').classList.remove('hidden');
  $('btn-next').classList.remove('hidden');
  $('result').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderStats() {
  const rows = domains.map((d) => {
    const qs = questions.filter((q) => q.domain === d.id);
    const hs = qs.map((q) => history[q.id]).filter(Boolean);
    return {
      label: `${d.id} ${d.name_ja}`,
      total: qs.length,
      seen: hs.length,
      attempts: hs.reduce((a, h) => a + h.attempts, 0),
      correct: hs.reduce((a, h) => a + h.correct, 0),
    };
  });
  const sum = (k) => rows.reduce((a, r) => a + r[k], 0);
  rows.push({ label: '合計', total: sum('total'), seen: sum('seen'), attempts: sum('attempts'), correct: sum('correct') });

  const pct = (r) => (r.attempts ? `${Math.round((r.correct / r.attempts) * 100)}%` : '-');
  $('stats-table').innerHTML =
    '<tr><th>ドメイン</th><th class="num">既出/全</th><th class="num">正答率</th></tr>';
  for (const r of rows) {
    $('stats-table').append(el('tr', {},
      el('td', { textContent: r.label }),
      el('td', { className: 'num', textContent: `${r.seen}/${r.total}` }),
      el('td', { className: 'num', textContent: pct(r) })));
  }
}

function showView(name) {
  $('view-quiz').classList.toggle('hidden', name !== 'quiz');
  $('filters').classList.toggle('hidden', name !== 'quiz');
  $('view-stats').classList.toggle('hidden', name !== 'stats');
  if (name === 'stats') renderStats();
}

async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

async function init() {
  // 試験パラメータ・ドメイン構成は設定ファイル駆動（DR-06）
  const exams = await fetchJson('config/exams.json');
  exam = exams[EXAM];
  domains = (await fetchJson(`config/taxonomy.${EXAM}.json`)).domains;
  const banks = await Promise.all(exam.domains.map((d) => fetchJson(`questions/${EXAM}/${d}.json`)));
  questions = banks.flatMap((b) => b.questions);

  document.body.dataset.theme = exam.theme;
  $('exam-badge').textContent = exam.name;
  $('sel-domain').replaceChildren(
    el('option', { value: 'all', textContent: 'すべて' }),
    ...domains.map((d) => el('option', { value: d.id, textContent: `${d.id} ${d.name_ja}` })));

  $('sel-domain').addEventListener('change', showQuestion);
  $('sel-mode').addEventListener('change', showQuestion);
  $('btn-next').addEventListener('click', showQuestion);
  $('btn-hint').addEventListener('click', () => $('hint').classList.toggle('hidden'));
  $('btn-stats').addEventListener('click', () => showView('stats'));
  $('btn-back').addEventListener('click', () => showView('quiz'));
  $('btn-reset').addEventListener('click', () => {
    if (!confirm(`${exam.name}の成績をすべて消去します。よろしいですか？`)) return;
    history = {};
    saveHistory();
    renderStats();
  });

  showQuestion();
}

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js');
}
init().catch((err) => {
  $('empty').textContent = `読み込みに失敗しました：${err.message}`;
  $('empty').classList.remove('hidden');
});
