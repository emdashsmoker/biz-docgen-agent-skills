"use strict";
// labels.js
// Lookup of the fixed labels of templates and blocks. Resolution order: slide slot value, then meta.labels[template or block][slot], then the default (assets/labels.json)
// The default table lives only in assets/labels.json, and lint.py (key validation) and finalize.py (language tags) read the same table
// build.js registers meta.labels per deck with useDeck(meta) (one deck per build)

const fs = require("fs");
const path = require("path");

const DEFAULTS = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "assets", "labels.json"), "utf8"));

let deck = {}; // meta.labels of the deck being built
let notePattern = null; // pattern of the note tokens added with meta.labels.notation.source

/** Registers the meta.labels of the deck to build */
function useDeck(meta) {
  deck = (meta && meta.labels && typeof meta.labels === "object") ? meta.labels : {};
  const escape = (t) => t.replace(/[.*+?^$()|[\]{}\\]/g, "\\$&");
  const extra = [].concat((deck.notation && deck.notation.source) || []).map((t) => escape(String(t).trim())).filter(Boolean);
  notePattern = extra.length ? new RegExp("^\\s*(?:" + extra.join("|") + ")\\s*[:：]") : null;
}
function fallback(group, key) {
  const g = DEFAULTS[group];
  if (!g || !(key in g)) throw new Error(`No label default for ${group}.${key} (assets/labels.json)`);
  return g[key];
}
/** One label. own is the slide slot value. Empty values (empty string, null) fall through to the next step (same as the earlier || default rule) */
function label(group, key, own) {
  if (own) return own;
  const m = deck[group];
  if (m && m[key]) return m[key];
  return fallback(group, key);
}
/** Label that also takes an empty string or null as a value (stepLabel "" shows the title only) */
function labelKeep(group, key, own) {
  if (own !== undefined) return own;
  const m = deck[group];
  if (m && m[key] !== undefined) return m[key];
  return fallback(group, key);
}
/** Object labels (swot.labels and the like). meta.labels (empty values skipped) goes over the default and the slide value over both, merged per key */
function labels(group, key, own) {
  const m = deck[group] && deck[group][key];
  const set = m && typeof m === "object" ? Object.fromEntries(Object.entries(m).filter(([, v]) => v)) : {};
  return { ...fallback(group, key), ...set, ...(own || {}) };
}
/** Replaces {n} and {t} in a format string */
function format(tpl, vars) {
  return String(tpl).replace(/\{(\w+)\}/g, (all, k) => (vars[k] !== undefined ? String(vars[k]) : all));
}
/** Language tags written into the PPTX (passed to finalize.py through build.json) */
function language() {
  return { latin: label("language", "latin"), east_asia: label("language", "east_asia") };
}
/** Whether the text starts with a note token added with meta.labels.notation.source ("token:" form). Each typesetting rule judges the built-in tokens (※, 출처:, 자료:, Source:, Note:) */
function isExtraNote(text) {
  return !!notePattern && notePattern.test(String(text));
}

module.exports = { DEFAULTS, useDeck, label, labelKeep, labels, format, language, isExtraNote };
