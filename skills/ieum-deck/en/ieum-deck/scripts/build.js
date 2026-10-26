#!/usr/bin/env node
"use strict";
// build.js
// The only generation path that typesets storyboard.json into pptx deterministically.
// Usage: node build.js <storyboard.json> <out.pptx> [--layout 16:9|A4|10.83|4:3] [--digest] [--marker square|bar|triangle] [--theme navy|mono]
// --digest : summary keeping only headline and template per slide (for quick structure review)
// A slide's byLayout replaces the values at its paths only when building with that page size (page-size-specific text)
// Fixed template and block labels resolve from the slide slot, then meta.labels, then assets/labels.json (labels.js)
// Custom slides (own:N) play back the own-deck.json at the meta.ownDeck path (relative to the storyboard allowed) or the IEUM_DECK_OWN environment variable

const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");
const T = require("./tokens.js");
const A = require("./atoms.js");
const TEMPLATES = require("./templates.js");
const LB = require("./labels.js");

const OWN_ENV = "IEUM_DECK_OWN";
// Line break unit (meta.lineBreak). word is word-level (default), char is character-level. finalize.py reads the build record and writes it on every paragraph property
const LINE_BREAKS = ["word", "char"];

function parseArgs(argv) {
  const o = { layout: null, digest: false, marker: null, theme: null, args: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--layout") o.layout = argv[++i];
    else if (a === "--digest") o.digest = true;
    else if (a === "--marker") o.marker = argv[++i];
    else if (a === "--theme") o.theme = argv[++i];
    else o.args.push(a);
  }
  return o;
}

/** Custom slide path. null if absent (decks without own:N build without custom slides) */
function ownPath(meta, storyPath) {
  const p = meta.ownDeck || process.env[OWN_ENV];
  if (!p) return null;
  return path.isAbsolute(p) ? p : path.resolve(path.dirname(storyPath), p);
}
function loadOwn(p) {
  if (!p) return null;
  if (!fs.existsSync(p)) throw new Error(`Custom slide file ${p} not found. Create it with own_extract.py`);
  const d = JSON.parse(fs.readFileSync(p, "utf8"));
  const byN = {};
  d.slides.forEach((s) => (byN[s.n] = s));
  byN.__colorMap = d.colorMap || {};
  return byN;
}

/** Typesets one slide. Returns: warning list */
function buildSlide(pres, sb, meta, own, S, index, warnings) {
  const slide = pres.addSlide();
  const tpl = sb.template || sb.type || "free";
  const ctx = { pres, S, T, A, own, meta, sb, index, warn: (m) => warnings.push(`[${sb.id || index}] ${m}`) };
  // Normalize the section number to the "1." form (add a missing period as in 01 or 1, and drop leading zeros)
  const secNo = sb.secNo == null ? sb.secNo : String(sb.secNo).trim().replace(/^0+(\d)/, "$1").replace(/^([\dIVXivx①-⑮]+)$/, "$1.");
  const band = { secNo, secTitle: sb.section, tracker: sb.tracker || sb.chapter, headline: sb.headline, marker: sb.marker, markerNote: sb.markerNote };
  // Custom slide playback: template "own:N"
  const m = /^own:(\d+)$/.exec(tpl);
  if (m) {
    if (!own) throw new Error(`${tpl} used: no custom slides registered (set own-deck.json with meta.ownDeck or ${OWN_ENV})`);
    const s = own[+m[1]];
    if (!s) throw new Error(`own:${m[1]} not found`);
    const b0 = { ...s.band, ...stripUndefined(band) };
    // Without marker text, skip the marker band (prevents a defect that leaves only an empty square)
    const base = s.mode || "full";
    const mode = sb.bandMode || (String(b0.marker || "").trim() ? base : bandNoMarker(base));
    const company = (sb.slots && sb.slots.company) || meta.company || LB.label("common", "company");
    const b = b0;
    Object.keys(b).forEach((k) => { if (b[k]) b[k] = A.scrub(b[k], company); });
    if (mode !== "blank") A.bodyBand(pres, slide, S, b, mode, { accentHeadline: sb.accent });
    A.playOwn(pres, slide, s, sb.slots, ctx);
    if (mode !== "blank") A.pageNo(slide, S, index + 1);
    return;
  }
  const fn = TEMPLATES[tpl];
  if (!fn) throw new Error(`Unknown template ${tpl} (slide ${sb.id || index})`);
  const spec = TEMPLATES.SPEC[tpl] || {};
  const mode0 = sb.bandMode || spec.band || "full";
  const mode = sb.bandMode || (String(band.marker || "").trim() ? mode0 : bandNoMarker(mode0));
  if (mode !== "blank") A.bodyBand(pres, slide, S, band, mode, { accentHeadline: sb.accent });
  fn(ctx, slide, sb);
  if (mode !== "blank" || spec.pageNo) A.pageNo(slide, S, index + 1);
}
/** Lowers the mode to one that skips the marker band when there is no marker text */
function bandNoMarker(mode) {
  return mode === "full" ? "noMarker" : mode;
}
/** Applies page-size-specific text. sb.byLayout = {"4:3": {"slots.regions.1.block.items": [...]}, "A4,10.83": {...}}
 *  Keys are page size names (comma-separated for several), values map dot paths (arrays numbered from 0) to replacements. Only keys matching the build page size apply */
function applyLayoutPatch(sb, layoutKey) {
  if (!sb.byLayout) return sb;
  const out = JSON.parse(JSON.stringify(sb));
  delete out.byLayout;
  Object.entries(sb.byLayout).forEach(([keys, patch]) => {
    const lays = keys.split(",").map((k) => k.trim());
    lays.forEach((k) => { if (!T.LAYOUTS[k]) throw new Error(`Slide ${sb.id} byLayout page size ${k} is undefined. Choose: ${Object.keys(T.LAYOUTS).join(", ")}`); });
    // Check every path regardless of page size so typos for other page sizes also surface
    Object.keys(patch).forEach((p) => pathParent(sb, p));
    if (lays.includes(layoutKey)) Object.entries(patch).forEach(([p, v]) => { const [parent, last] = pathParent(out, p); parent[last] = v; });
  });
  return out;
}
/** Parent object and last key of a dot path. Error if an intermediate path is missing */
function pathParent(obj, p) {
  const segs = p.split(".");
  let cur = obj;
  for (const s of segs.slice(0, -1)) {
    if (cur == null || typeof cur !== "object" || !(s in cur)) throw new Error(`Slide ${obj.id} byLayout path ${p} not found`);
    cur = cur[s];
  }
  const last = segs[segs.length - 1];
  // Arrays replace existing items only (objects may take new keys)
  if (cur == null || typeof cur !== "object" || (Array.isArray(cur) && !(last in cur))) throw new Error(`Slide ${obj.id} byLayout path ${p} not found`);
  return [cur, last];
}
function stripUndefined(o) {
  const r = {};
  Object.keys(o).forEach((k) => { if (o[k] !== undefined && o[k] !== null) r[k] = o[k]; });
  return r;
}

async function main() {
  const argv = parseArgs(process.argv.slice(2));
  const [inPath, outPath] = argv.args;
  if (!inPath || !outPath) { console.error("usage: node build.js <storyboard.json> <out.pptx> [--layout KEY] [--digest] [--marker square|bar|triangle] [--theme navy|mono]"); process.exit(2); }
  const story = JSON.parse(fs.readFileSync(inPath, "utf8"));
  const meta = story.meta || {};
  LB.useDeck(meta); // Register the deck-level labels (meta.labels)
  const layoutKey = argv.layout || meta.layout || "16:9";
  if (!T.LAYOUTS[layoutKey]) throw new Error(`Page size ${layoutKey} is undefined. Choose: ${Object.keys(T.LAYOUTS).join(", ")}`);
  const theme = argv.theme || meta.theme || "navy";
  if (!T.THEMES[theme] && !meta.themeColors) throw new Error(`Color theme ${theme} is undefined. Choose: ${Object.keys(T.THEMES).join(", ")} or set meta.themeColors`);
  const lineBreak = meta.lineBreak || LINE_BREAKS[0];
  if (!LINE_BREAKS.includes(lineBreak)) throw new Error(`Line break unit ${lineBreak} is undefined. Choose: ${LINE_BREAKS.join(", ")}`);
  A.setImageBase(path.dirname(path.resolve(inPath)));
  const ownFile = ownPath(meta, inPath);
  const own = loadOwn(ownFile);
  if (own) T.setOwnColorMap(own.__colorMap);
  const themeResult = T.applyTheme(theme, meta.themeColors);
  // A base color too light for white text is darkened before use, so print the adjusted value for the user report
  if (themeResult.adjusted) console.log(`THEME base color lightness adjusted #${themeResult.adjusted.from} → #${themeResult.adjusted.to} (white text on label cells reaches 4.5:1 contrast)`);
  if (argv.marker) T.MARKER.shape = argv.marker;
  else if (meta.marker) T.MARKER.shape = meta.marker;
  const S = T.scaled(layoutKey);
  const pres = new PptxGenJS();
  pres.defineLayout({ name: S.layout.name, width: S.layout.W, height: S.layout.H });
  pres.layout = S.layout.name; // Set before adding slides (pptxgenjs rule)
  pres.title = meta.title || "";
  pres.author = meta.author || "";
  // Set document properties so library defaults (company, subject) do not remain. pptxgenjs writes company without escaping, so escape it here
  pres.company = String(meta.company || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  pres.subject = "";
  const warnings = [];
  let slides = (story.slides || []).map((sb) => applyLayoutPatch(sb, layoutKey));
  if (argv.digest) slides = slides.map((s) => ({ id: s.id, template: "digest", headline: s.headline, section: s.section, chapter: s.chapter, secNo: s.secNo, marker: s.marker, digestOf: s.template || s.type, digest: s.digest }));
  slides.forEach((sb, i) => buildSlide(pres, sb, meta, own, S, i, warnings));
  await pres.writeFile({ fileName: outPath });
  T.writeLimits(path.join(__dirname));
  // Custom slide playback keeps the source font and width-absorbing shrink, so those slides skip the body minimum check (read by check_layout)
  const ownSlides = slides.map((s, i) => (String(s.template || "").startsWith("own:") ? i + 1 : 0)).filter(Boolean);
  // palette records custom theme colors so they count as allowed table cell colors (read by check_layout and finalize)
  // language holds the language tags written into the PPTX (meta.labels.language, read by finalize)
  // lineBreak holds the line break unit written on paragraph properties (meta.lineBreak, read by finalize and check_layout)
  const themeLabel = meta.themeColors && meta.themeColors.base ? `custom #${T.COLOR.navy}` : theme;
  const report = { out: outPath, slides: slides.length, layout: layoutKey, theme: themeLabel, palette: T.themePalette(), language: LB.language(), lineBreak, themeAdjusted: themeResult.adjusted, ownDeck: ownFile, ownSlides, warnings };
  fs.writeFileSync(outPath.replace(/\.pptx$/, "") + ".build.json", JSON.stringify(report, null, 1));
  console.log(`built ${outPath} slides=${slides.length} layout=${layoutKey} theme=${themeLabel} warnings=${warnings.length}`);
  warnings.forEach((w) => console.log("WARN " + w));
}

// Input errors print only the message. The stack prints only with IEUM_DECK_DEBUG=1 (for debugging)
main().catch((e) => { console.error(process.env.IEUM_DECK_DEBUG ? e.stack || e : `ERROR ${e.message || e}`); process.exit(1); });
