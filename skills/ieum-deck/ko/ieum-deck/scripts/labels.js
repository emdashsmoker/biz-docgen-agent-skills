"use strict";
// labels.js
// 템플릿과 블록의 고정 라벨 조회. 해석 순서는 슬라이드 슬롯 값, meta.labels[템플릿 또는 블록][슬롯], 기본값(assets/labels.json)
// 기본값 표는 assets/labels.json 한 곳에 두고 lint.py(키 검증)와 finalize.py(언어 태그)도 같은 표를 읽음
// build.js 가 덱마다 useDeck(meta) 로 meta.labels 를 등록 (빌드 1회에 덱 1개)

const fs = require("fs");
const path = require("path");

const DEFAULTS = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "assets", "labels.json"), "utf8"));

let deck = {}; // 빌드 중인 덱의 meta.labels
let notePattern = null; // meta.labels.notation.source 로 추가한 주석 토큰 패턴

/** 빌드할 덱의 meta.labels 등록 */
function useDeck(meta) {
  deck = (meta && meta.labels && typeof meta.labels === "object") ? meta.labels : {};
  const escape = (t) => t.replace(/[.*+?^$()|[\]{}\\]/g, "\\$&");
  const extra = [].concat((deck.notation && deck.notation.source) || []).map((t) => escape(String(t).trim())).filter(Boolean);
  notePattern = extra.length ? new RegExp("^\\s*(?:" + extra.join("|") + ")\\s*[:：]") : null;
}
function fallback(group, key) {
  const g = DEFAULTS[group];
  if (!g || !(key in g)) throw new Error(`라벨 기본값 없음 ${group}.${key} (assets/labels.json)`);
  return g[key];
}
/** 라벨 1개. own 은 슬라이드 슬롯 값. 빈 값(빈 문자열, null)은 다음 단계로 넘어감 (기존 || 기본값 규칙과 같음) */
function label(group, key, own) {
  if (own) return own;
  const m = deck[group];
  if (m && m[key]) return m[key];
  return fallback(group, key);
}
/** 빈 문자열과 null 도 값으로 쓰는 라벨 (stepLabel "" 은 접두어 없이 제목만 표시) */
function labelKeep(group, key, own) {
  if (own !== undefined) return own;
  const m = deck[group];
  if (m && m[key] !== undefined) return m[key];
  return fallback(group, key);
}
/** 객체형 라벨(swot.labels 등). 기본값 위에 meta.labels(빈 값 제외), 그 위에 슬라이드 값을 키 단위로 병합 */
function labels(group, key, own) {
  const m = deck[group] && deck[group][key];
  const set = m && typeof m === "object" ? Object.fromEntries(Object.entries(m).filter(([, v]) => v)) : {};
  return { ...fallback(group, key), ...set, ...(own || {}) };
}
/** 형식 문자열의 {n}, {t} 치환 */
function format(tpl, vars) {
  return String(tpl).replace(/\{(\w+)\}/g, (all, k) => (vars[k] !== undefined ? String(vars[k]) : all));
}
/** PPTX 에 기록할 언어 태그 (build.json 으로 finalize.py 에 전달) */
function language() {
  return { latin: label("language", "latin"), east_asia: label("language", "east_asia") };
}
/** meta.labels.notation.source 로 추가한 주석 토큰("토큰:" 형태)으로 시작하는지 여부. 기본 토큰(※, 출처:, 자료:, Source:, Note:)은 각 조판 규칙이 판정 */
function isExtraNote(text) {
  return !!notePattern && notePattern.test(String(text));
}

module.exports = { DEFAULTS, useDeck, label, labelKeep, labels, format, language, isExtraNote };
