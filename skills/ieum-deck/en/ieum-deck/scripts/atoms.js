"use strict";
// atoms.js
// Atoms on top of pptxgenjs. Text, shapes, lines, tables, charts, images, the 4 band types and custom slide playback (playOwn).
// Coordinates are in inches and colors are 6-digit tokens. Numeric constants come only from tokens.js.

const T = require("./tokens.js");
const LB = require("./labels.js"); // Note tokens added with meta.labels.notation.source
const fs = require("fs");
const path = require("path");
// Measured NanumGothic widths (em). Without them, tokens.METRIC approximations are used
// Reproduction: ASCII glyph widths are the hmtx advance widths of NanumGothic.ttf and NanumGothicBold.ttf divided by head.unitsPerEm (checked with fontTools)
//       Category keys (hangul, cjkpunct, fullwidth, enclosed, other) hold a representative width per category
//       Symbol keys (× ÷ ± · 〉 … “ ” ‘ ’) are hmtx values too. Kept separately because they differ widely from the category width (× 0.592 vs category 0.509, … 0.94 vs category 0.509, etc.)
//       They match the LibreOffice rendered width of a run of 10 identical symbols within 0.001em (same values in regular and bold)
let METRICS = null;
try { METRICS = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "assets", "font-metrics.json"), "utf8")); } catch (e) { METRICS = null; }

// ---------------------------------------------------------------- Colors and fonts
function remap(hex) {
  if (!hex || hex === "none") return hex;
  const h = String(hex).replace("#", "").toUpperCase();
  return T.COLOR_REMAP[h] || h;
}
function face(bold) {
  return bold ? T.FONT.bold : T.FONT.regular;
}

// ---------------------------------------------------------------- Text width estimation
/** Hanja code ranges: unified ideographs, extension A, compatibility ideographs (the range Korean input methods use for homographs) */
const isHanja = (c) => (c >= 0x4e00 && c <= 0x9fff) || (c >= 0x3400 && c <= 0x4dbf) || (c >= 0xf900 && c <= 0xfaff);
/** Full-width symbols: arrows, box drawing, shapes (○ ● ◐ □ ■), misc symbols, ※. 0.94em in NanumGothic, same as Hangul */
const isWideSymbol = (c) => (c >= 0x2190 && c <= 0x21ff) || (c >= 0x2500 && c <= 0x27bf) || c === 0x203b;
/** Hangul compatibility jamo (ㄱ, ㅏ, ㆍ). 0.94em in NanumGothic, same as Hangul (checked with hmtx and rendered width) */
const isHangulJamo = (c) => c >= 0x3130 && c <= 0x318f;
/** Roman numerals (Ⅰ-Ⅹ, ⅰ-ⅹ). 0.94em in NanumGothic, same as Hangul (checked with hmtx and rendered width) */
const isRomanNumeral = (c) => c >= 0x2160 && c <= 0x2179;
function charEm(ch, bold) {
  const c = ch.codePointAt(0);
  if (METRICS) {
    const m = METRICS[bold ? "bold" : "regular"];
    if (m[ch] != null) return m[ch];
    if (c >= 0xac00 && c <= 0xd7a3) return m.hangul;
    if (c >= 0x3000 && c <= 0x303f) return m.cjkpunct;
    if (c >= 0xff00 && c <= 0xffef) return m.fullwidth;
    if (c >= 0x2460 && c <= 0x24ff) return m.enclosed;
    if (isHanja(c)) return m.hangul; // Hanja (unified, extension A, compatibility) is full width in NanumGothic, same as Hangul
    if (isWideSymbol(c) || isHangulJamo(c) || isRomanNumeral(c)) return m.hangul;
    return m.other;
  }
  if (ch === " ") return T.METRIC.EM_SPACE;
  const wide = (c >= 0xac00 && c <= 0xd7a3) || (c >= 0x3000 && c <= 0x303f) || (c >= 0xff00 && c <= 0xffef) || isHanja(c) || (c >= 0x2460 && c <= 0x24ff) || isHangulJamo(c) || isWideSymbol(c);
  return wide ? T.METRIC.EM_HANGUL : T.METRIC.EM_LATIN;
}
// Script class. LibreOffice adds a gap (METRIC.SCRIPT_GAP_EM) at every boundary where the script changes between Latin and Asian
// Weak characters (WEAK) take the script of the preceding character and count as Latin at the start of a paragraph
// Measured (LibreOffice 24.2, English locale): Latin is ASCII (letters, digits, punctuation, straight quotes) and Latin-1 symbols (× ÷ ± ·)
//   Asian is Hangul syllables, Hangul compatibility jamo (ㄱ ㆍ), CJK punctuation (〉) and Hanja. Weak is space, ○ ● ◐ ①-⑤ ※ Ⅰ-Ⅵ … “ ” ‘ ’ →
//   Full-width forms (U+FF00-FFEF) are not measured. Placed in Asian as the same East Asian category
//   Treating a weak character at the start of a paragraph as Latin is confirmed only in the English locale
const SCRIPT = { WEAK: 0, LATIN: 1, ASIAN: 2 };
function scriptOf(c) {
  if (c <= 0x20 || c === 0xa0) return SCRIPT.WEAK; // space, control characters such as line breaks, no-break space
  if (c <= 0xff) return SCRIPT.LATIN;
  if ((c >= 0xac00 && c <= 0xd7a3) || isHangulJamo(c) || (c >= 0x3000 && c <= 0x303f) || (c >= 0xff00 && c <= 0xffef) || isHanja(c)) return SCRIPT.ASIAN;
  return SCRIPT.WEAK;
}
/** Text width (em) and the scripts at both ends. prev is the script of the character right before the text (for weak characters, WEAK at the start of a paragraph)
 *  Gaps are added only between characters inside the text. The caller judges the gap between the preceding character and the first character with first */
function spanEm(s, bold, prev) {
  let em = 0, cur = prev || SCRIPT.WEAK, first = SCRIPT.WEAK;
  for (const ch of String(s)) {
    const sc = scriptOf(ch.codePointAt(0)) || cur || SCRIPT.LATIN;
    if (first && sc !== cur) em += scriptGapEm();
    em += charEm(ch, bold);
    if (!first) first = sc;
    cur = sc;
  }
  return { em, first, last: cur };
}
/** Script boundary gap (em). A measured NanumGothic value, so it applies only with the measured width file (the SAFETY factor absorbs the gap for approximate widths) */
function scriptGapEm() {
  return METRICS ? T.METRIC.SCRIPT_GAP_EM : 0;
}
/** Width (em) of one-line text. Treated as text running from the start of a paragraph, including script boundary gaps */
function textEm(s, bold) {
  return spanEm(s, bold, SCRIPT.WEAK).em;
}
/** Number of lines at fontPt in a box of width widthIn */
function estimateLines(str, widthIn, fontPt, bold) {
  if (!str) return 0;
  const cap = ((widthIn * 72) / fontPt) * (METRICS ? T.METRIC.SAFETY_LINES : T.METRIC.SAFETY);
  let lines = 0;
  for (const para of String(str).split("\n")) {
    // The script of weak characters carries on from the start of the paragraph (last: script of the last character of the previous word)
    let cur = 0, n = 1, last = SCRIPT.WEAK;
    for (const w of para.split(" ")) {
      const s = spanEm(w, bold, last);
      // The space and the script boundary gap count only when the word joins the previous word on the same line (a trailing space and gap at a line break take no line width)
      const gap = s.first && last && s.first !== last ? scriptGapEm() : 0;
      const need = s.em + (cur > 0 ? charEm(" ", bold) + gap : 0);
      if (cur > 0 && cur + need > cap) { n += 1; cur = s.em; } else cur += need;
      if (cur > cap) { n += Math.floor(cur / cap); cur = cur % cap; }
      last = s.last;
    }
    lines += n;
  }
  return lines;
}
const LINE_FIT_EPS = 0.01; // Margin so width rounding does not turn a one-line judgment into two lines (inches)
/** Minimum width (inches) that fits the text on one line. A more conservative width criterion than the width estimateLines judges as 1 line (SAFETY_METRIC. estimateLines also counts 1 line at this width) */
function lineWidthIn(str, pt, bold) {
  return (textEm(str, bold) * pt) / 72 / (METRICS ? T.METRIC.SAFETY_METRIC : T.METRIC.SAFETY) + LINE_FIT_EPS;
}
/** One-line width (inches) of the widest word (space-delimited) in a text list. Used as the minimum label column and box width on narrow page sizes to prevent mid-word line breaks */
function wordWidthIn(texts, pt, bold) {
  const words = [].concat(texts || []).flatMap((t) => String(t == null ? "" : t).split(/\s+/)).filter(Boolean);
  return words.length ? Math.max(...words.map((w) => lineWidthIn(w, pt, bold))) : 0;
}
function lineHeightIn(pt, ratio) {
  return (pt * (ratio || T.METRIC.LINE_HEIGHT)) / 72;
}

/**
 * Shrinks font sizes uniformly so a paragraph group fits the box (inner w,h). When NanumGothic is wider than the source slide font,
 * this absorbs the extra line breaks at the same size inside the box. The minimum is minPt (body 11pt).
 * Returns: new paras (the original is unchanged)
 */
function fitParas(paras, innerW, innerH, minPt, lineRatio) {
  if (!paras || !paras.length || innerW <= 0.05) return paras;
  const floor = minPt || T.SIZE.BODY_MIN;
  const need = (scale) => {
    let h = 0;
    for (const p of paras) {
      const txt = p.runs.filter((r) => !r.br).map((r) => r.t).join("");
      const r0 = p.runs.find((r) => !r.br) || { sz: T.SIZE.body };
      const sz = Math.max(floor, (r0.sz || T.SIZE.body) * scale);
      const indent = p.bullet ? (p.indent != null ? Math.abs(p.indent) : T.PARA.bulletIndentIn) : (p.marL || 0);
      const lines = Math.max(1, estimateLines(txt, innerW - indent, sz, r0.b));
      const gap = ((p.spcBef || 0) + (p.spcAft || 0)) / 72;
      h += lines * lineHeightIn(sz, lineRatio || p.lnSpc) + gap;
    }
    return h;
  };
  // With no line breaks at all (every paragraph 1 line), a height shortfall is the same tolerated overflow as the source, so no shrink
  const wraps = paras.some((p) => {
    const txt = p.runs.filter((r) => !r.br).map((r) => r.t).join("");
    const r0 = p.runs.find((r) => !r.br) || { sz: T.SIZE.body };
    const indent = p.bullet ? (p.indent != null ? Math.abs(p.indent) : T.PARA.bulletIndentIn) : (p.marL || 0);
    return estimateLines(txt, innerW - indent, r0.sz || T.SIZE.body, r0.b) > 1;
  });
  if (!wraps && paras.length <= 3) return paras;
  let scale = 1.0;
  while (scale > 0.6 && need(scale) > innerH + 0.1) scale -= 0.04; // PowerPoint tolerates overflow into the insets, so allow 0.1 inch
  let out = scale >= 0.999 ? paras : paras.map((p) => ({ ...p, runs: p.runs.map((r) => ({ ...r, sz: Math.max(floor, +(((r.sz || T.SIZE.body) * scale)).toFixed(1)) })) }));
  // If it still overflows at the font minimum, cut the space between paragraphs to fit the box
  const heightOf = (ps) => ps.reduce((h, p) => {
    const txt = p.runs.filter((r) => !r.br).map((r) => r.t).join("");
    const r0 = p.runs.find((r) => !r.br) || { sz: T.SIZE.body };
    const indent = p.bullet ? (p.indent != null ? Math.abs(p.indent) : T.PARA.bulletIndentIn) : (p.marL || 0);
    return h + Math.max(1, estimateLines(txt, innerW - indent, r0.sz || T.SIZE.body, r0.b)) * lineHeightIn(r0.sz || T.SIZE.body, lineRatio || p.lnSpc) + ((p.spcBef || 0) + (p.spcAft || 0)) / 72;
  }, 0);
  for (const cut of [0.6, 0.3, 0]) {
    if (heightOf(out) <= innerH + 0.1) break;
    out = out.map((p, i) => (i === 0 ? p : { ...p, spcBef: Math.round((p.spcBef || 0) * cut * 10) / 10 }));
  }
  return out;
}

// ---------------------------------------------------------------- Default options
const DEFAULT_MG_IN = [0.1, 0.05, 0.1, 0.05]; // OOXML bodyPr default insets (l,t,r,b). Fills insets missing in the custom slide source
const TEXT_MG_IN = [0.075, 0.05, 0.075, 0.05]; // Insets of generated text boxes without explicit insets (l,t,r,b). Left plus right is 0.15
/** Text box insets [left, top, right, bottom] (inches) → [left, top, right, bottom] (pt). Empty values take the default */
function mgPt(mg) {
  const m = mg && mg.length === 4 ? mg.map((v, i) => (v == null ? DEFAULT_MG_IN[i] : v)) : DEFAULT_MG_IN;
  return m.map((v) => +(v * 72).toFixed(1));
}
/** Text box insets [left, top, right, bottom] (inches) → pptxgenjs text box margin argument. pptxgenjs reads [left, right, bottom, top] */
function boxMargin(mg) {
  const [l, t, r, b] = mgPt(mg);
  return [l, r, b, t];
}
const DASH_MAP = { solid: "solid", dash: "dash", sysDash: "sysDash", sysDot: "sysDot", dot: "sysDot", lgDash: "lgDash", dashDot: "dashDot", lgDashDot: "lgDashDot", lgDashDotDot: "lgDashDotDot", sysDashDot: "dashDot" };
const ARROW_MAP = { triangle: "triangle", arrow: "arrow", oval: "oval", stealth: "stealth", diamond: "diamond" };

function lineOpt(ln, fallbackPt) {
  if (!ln || ln.color === "none") return { color: "FFFFFF", width: 0, transparency: 100 };
  const o = { color: remap(ln.color || T.COLOR.borderLight), width: ln.pt != null ? ln.pt : (fallbackPt || T.PANEL.LINE_PT) };
  if (ln.dash && DASH_MAP[ln.dash] && ln.dash !== "solid") o.dashType = DASH_MAP[ln.dash];
  if (ln.head && ARROW_MAP[ln.head]) o.beginArrowType = ARROW_MAP[ln.head];
  if (ln.tail && ARROW_MAP[ln.tail]) o.endArrowType = ARROW_MAP[ln.tail];
  return o;
}

// ---------------------------------------------------------------- Text run list conversion
/**
 * paras: [{align, bullet, buChar, lvl, marL, indent, spcBef, spcAft, lnSpc, runs:[{t,sz,b,color,u,br}]}]
 * → pptxgenjs text array. Paragraph properties go on the first run of the paragraph
 */
function runsOf(paras, defaults) {
  const out = [];
  const d = defaults || {};
  paras.forEach((p, pi) => {
    const last = pi === paras.length - 1;
    const pOpt = {};
    if (p.align) pOpt.align = p.align;
    if (p.bullet) {
      const indent = Math.round((p.indent != null ? Math.abs(p.indent) : T.PARA.bulletIndentIn) * 72);
      if (p.buNum) pOpt.bullet = { type: "number", style: p.buNum, indent };
      else pOpt.bullet = { code: p.buChar ? p.buChar.codePointAt(0).toString(16).toUpperCase().padStart(4, "0") : "2022", indent };
      pOpt.indentLevel = p.lvl || 0;
    } else if (p.marL) {
      // Indents without bullets are approximated with indentLevel
      pOpt.indentLevel = Math.min(4, Math.round(p.marL / 0.25));
    }
    if (p.spcBef != null) pOpt.paraSpaceBefore = p.spcBef;
    if (p.spcAft != null) pOpt.paraSpaceAfter = p.spcAft;
    if (p.lnSpc != null) pOpt.lineSpacingMultiple = p.lnSpc;
    const runs = p.runs && p.runs.length ? p.runs : [{ t: "", sz: d.sz || T.SIZE.body }];
    // Merge adjacent runs with the same format (reduces the pptxgenjs defect of writing a pPr per run)
    const merged = [];
    runs.forEach((r) => {
      const prev = merged[merged.length - 1];
      if (prev && !prev.br && !r.br && prev.sz === r.sz && !!prev.b === !!r.b && prev.color === r.color && !!prev.u === !!r.u) prev.t += r.t;
      else merged.push({ ...r });
    });
    merged.forEach((r, ri) => {
      if (r.br) return; // A line break run is handled as breakLine of the previous run
      const o = {
        fontSize: r.sz || d.sz || T.SIZE.body,
        bold: !!(r.b != null ? r.b : d.bold),
        color: remap(r.color || d.color || T.COLOR.textDark),
        fontFace: face(r.b != null ? r.b : d.bold),
      };
      if (r.u) o.underline = { style: "sng" };
      // Paragraph properties go on the first run. Alignment and indent are copied to every run (pptxgenjs treats an alignment change or a bullet as a paragraph break)
      // finalize.py removes the extra pPr created per run
      const first = out.length === 0 || out[out.length - 1].options.breakLine;
      Object.assign(o, first ? pOpt : { align: pOpt.align, indentLevel: pOpt.indentLevel, lineSpacingMultiple: pOpt.lineSpacingMultiple });
      const prev = merged[ri - 1];
      if (prev && prev.br) o.softBreakBefore = true; // A line break inside a paragraph (a:br) keeps numbering and alignment
      if (ri === merged.length - 1 && !last) o.breakLine = true;
      out.push({ text: r.t, options: o });
    });
  });
  return out;
}
/** String → paras (split into paragraphs at line breaks) */
function parasFromString(s, base) {
  const b = base || {};
  return String(s).split("\n").map((line) => ({ ...b, runs: [{ t: line, sz: b.sz, b: b.b, color: b.color }] }));
}

// ---------------------------------------------------------------- Atoms
/** Text box. paras or a string */
function text(slide, box, content, opt) {
  const o = opt || {};
  const paras = typeof content === "string" ? parasFromString(content, { sz: o.sz, b: o.bold, color: o.color, align: o.align }) : content;
  const arr = runsOf(paras, { sz: o.sz, bold: o.bold, color: o.color });
  slide.addText(arr, {
    x: box.x, y: box.y, w: box.w, h: box.h,
    isTextBox: true,
    valign: o.valign || "middle",
    align: o.align || undefined,
    margin: boxMargin(o.mg || TEXT_MG_IN),
    fill: o.fill ? { color: remap(o.fill) } : undefined,
    line: o.line ? lineOpt(o.line) : undefined,
    shape: o.shape,
    rectRadius: o.rectRadius,
    rotate: o.rotate,
    vert: o.vert,
    autoFit: false,
    wrap: o.wrap !== false,
  });
}

const PRESET_MAP = { round2SameRect: "roundRect", straightConnector1: "line" };
function shapeType(pres, preset) {
  const name = PRESET_MAP[preset] || preset || "rect";
  return pres.ShapeType[name] || pres.ShapeType.rect;
}

/** Shape (fill, line, inner text). atom uses the shape atom format of own-deck */
function shape(pres, slide, atom, override) {
  const ov = override || {};
  const fillHex = ov.fill !== undefined ? ov.fill : atom.fill;
  const fill = fillHex && fillHex !== "none" && fillHex !== "gradient" ? { color: remap(fillHex), transparency: atom.alpha != null ? Math.round(100 - atom.alpha) : undefined } : undefined;
  const ln = ov.line !== undefined ? ov.line : atom.line;
  const line = ln ? lineOpt(ln) : (fill ? { color: "FFFFFF", width: 0, transparency: 100 } : undefined);
  const base = {
    x: atom.x, y: atom.y, w: Math.max(atom.w, 0.01), h: Math.max(atom.h, 0.01),
    fill, line,
    rotate: atom.rot ? (atom.rot > 180 ? atom.rot - 360 : atom.rot) : undefined, flipH: atom.flipH || undefined, flipV: atom.flipV || undefined,
  };
  const st = shapeType(pres, atom.preset);
  if (atom.preset === "roundRect" || atom.preset === "round2SameRect") base.rectRadius = Math.min(T.PANEL.ROUND_RADIUS, Math.min(atom.w, atom.h) * 0.2);
  // pptxgenjs does not support adjust values (tip width, etc.), so they travel in the shape name and finalize.py moves them to avLst
  if (atom.adj != null && atom.preset !== "roundRect" && atom.preset !== "round2SameRect") base.objectName = `adj:${atom.adj}`;
  let paras = ov.paras !== undefined ? ov.paras : atom.paras;
  if (paras) {
    // In small boxes (number circles, single-character labels) the default insets eat the width, so insets are 0
    const small = atom.w < T.PANEL.SMALL_BOX_W;
    const narrowChevron = (atom.preset === "chevron" || atom.preset === "homePlate") && atom.w < 1.6 * atom.h; // Short chevrons whose tips eat the text width
    const mgArr = small || narrowChevron ? [0, 0, 0, 0] : mgPt(atom.mg);
    const mg = mgArr.map((v) => v / 72);
    // Chevrons and home plates lose text area by the tip width (OOXML text rectangle definition)
    const pointW = atom.preset === "chevron" || atom.preset === "homePlate" ? Math.min(atom.w, atom.h) * (atom.adj != null ? atom.adj / 100000 : 0.5) : 0;
    const innerW = atom.w - mg[0] - mg[2] - (atom.preset === "chevron" ? 2 * pointW : pointW);
    if (ov.scale != null && ov.scale < 1) paras = paras.map((p) => ({ ...p, runs: p.runs.map((r) => ({ ...r, sz: Math.max(ov.minPt || T.SIZE.BODY_MIN, +((r.sz || T.SIZE.body) * ov.scale).toFixed(1)) })) }));
    if (ov.fillText) { paras = growParas(paras, innerW, atom.h - mg[1] - mg[3], 1.0); atom = { ...atom, va: "middle" }; } // Boxes that absorbed empty area fill it by widening spacing only, keeping the tier font size
    paras = fitParas(paras, innerW, atom.h - mg[1] - mg[3], ov.minPt);
    // Text judged as 1 paragraph on 1 line turns wrapping off to prevent unexpected breaks from renderer spacing errors
    const oneLine = paras.length === 1 && !paras[0].runs.some((r) => r.br) && estimateLines(paras[0].runs.map((r) => r.t).join(""), innerW, paras[0].runs[0].sz || T.SIZE.body, paras[0].runs[0].b) <= 1;
    slide.addText(runsOf(paras, { color: ov.textColor }), {
      ...base, shape: st, isTextBox: true,
      valign: ov.fillText ? "middle" : (ov.va || atom.va || "middle"),
      margin: boxMargin(mgArr.map((v) => v / 72)),
      wrap: !(small || oneLine) || narrowChevron, // Short chevrons always wrap (their text rectangle is narrow and overflows)
      vert: atom.vert || undefined,
      autoFit: false,
    });
  } else {
    slide.addShape(st, base);
  }
}

/** Finds a slot by the original text start key "~text" (substitution without counting t{k} numbers). Whitespace ignored, prefix match */
function textKey(sl, cur) {
  const norm = (v) => String(v).replace(/\s+/g, "");
  const c = norm(cur);
  if (!c) return null;
  for (const k of Object.keys(sl)) {
    if (k[0] === "~" && k.length > 1 && c.startsWith(norm(k.slice(1)))) return sl[k];
  }
  return null;
}

/** Width and height (inches) actually taken by the glyphs inside a text box */
function inkExtent(atom) {
  const mg = mgPt(atom.mg).map((v) => v / 72);
  const innerW = Math.max(0.2, atom.w - mg[0] - mg[2]);
  let w = 0, h = 0;
  (atom.paras || []).forEach((p) => {
    const r0 = p.runs.find((r) => !r.br) || { sz: T.SIZE.body };
    const txt = p.runs.filter((r) => !r.br).map((r) => r.t).join("");
    const indent = p.bullet ? (p.indent != null ? Math.abs(p.indent) : T.PARA.bulletIndentIn) : (p.marL || 0);
    const lines = estimateLines(txt, innerW - indent, r0.sz || T.SIZE.body, r0.b);
    w = Math.max(w, Math.min(innerW, textEm(txt, r0.b) * (r0.sz || T.SIZE.body) / 72 + indent));
    h += lines * lineHeightIn(r0.sz || T.SIZE.body) + (p.spcBef || 0) / 72;
  });
  return { w: w + mg[0] + mg[2], h: h + mg[1] + mg[3] };
}

/** Sibling box key: source font size + box width and height (0.1 inch units). Boxes with the same key share a shrink ratio */
function sizeKey(atom, paras) {
  return `${Math.round(paras[0].runs[0].sz || T.SIZE.body)}|${Math.round(atom.w * 10)}|${Math.round(atom.h * 10)}`;
}

/** Enlarges fonts to fill the box (capped at maxScale). Line spacing is also spread through spcBef */
function growParas(paras, innerW, innerH, maxScale) {
  const need = (sc) => paras.reduce((h, p) => {
    const r0 = p.runs.find((r) => !r.br) || { sz: T.SIZE.body };
    const txt = p.runs.filter((r) => !r.br).map((r) => r.t).join("");
    const indent = p.bullet ? (p.indent != null ? Math.abs(p.indent) : T.PARA.bulletIndentIn) : (p.marL || 0);
    return h + estimateLines(txt, innerW - indent, (r0.sz || T.SIZE.body) * sc, r0.b) * lineHeightIn((r0.sz || T.SIZE.body) * sc) + ((p.spcBef || 0) + (p.spcAft || 0)) / 72;
  }, 0);
  let sc = 1;
  while (sc < maxScale && need(sc + 0.05) <= innerH * 0.75) sc += 0.05;
  const out = paras.map((p) => ({ ...p, runs: p.runs.map((r) => ({ ...r, sz: +((r.sz || T.SIZE.body) * sc).toFixed(1) })) }));
  const slack = innerH - need(sc);
  const extra = Math.min(T.PARA.paraGapMaxPt, Math.max(0, (slack * 72) / (out.length + 1)));
  return out.map((p, i) => (i === 0 ? p : { ...p, spcBef: (p.spcBef || 0) + extra })); // Spacing only between paragraphs (keeps vertical centering)
}

/** Font shrink ratio needed to fit the box (1 means no shrink) */
function shrinkRatio(atom, paras, minPt) {
  const small = atom.w < T.PANEL.SMALL_BOX_W;
  const mg = (small ? [0, 0, 0, 0] : mgPt(atom.mg)).map((v) => v / 72);
  const pointW = atom.preset === "chevron" || atom.preset === "homePlate" ? Math.min(atom.w, atom.h) * (atom.adj != null ? atom.adj / 100000 : 0.5) : 0;
  const innerW = atom.w - mg[0] - mg[2] - (atom.preset === "chevron" ? 1.0 * pointW : 0.5 * pointW);
  const fitted = fitParas(paras, innerW, atom.h - mg[1] - mg[3], minPt);
  const before = paras[0].runs[0].sz || T.SIZE.body;
  const after = fitted[0].runs[0].sz || before;
  return after / before;
}

/** Icon image replacement: chooses a kind from keywords in nearby labels and composes it from shapes (no glyph font dependency)
 * kinds: lock (physical, access), shield (technical, network, VPN), clipboard (administrative, training, inspection), calendar (schedule, reporting, WBS), data (data, DB), gear (implications, tools), check (default). Keywords are matched in Korean and English */
function iconKind(box, nearbyTexts) {
  const t = (nearbyTexts || []).join(" ");
  if (box.h > box.w * 1.1 || /총원|인원|임직원|구성원/.test(t) || /\b(?:headcount|employees|workforce)\b/i.test(t)) return "person";
  if (/파쇄|폐기/.test(t) || /\b(?:shred|dispos)/i.test(t)) return "shredder";
  if (/WBS|진도|실적|집계/.test(t) || /\b(?:progress|performance|tally)/i.test(t)) return "dashboard";
  if (/물리|출입|잠금|보관/.test(t) || /\b(?:physical|access|lock|storage)/i.test(t)) return "lock";
  if (/기술 보안|네트워크|VPN|바이러스|단말/.test(t) || /\b(?:technical security|network|virus|device)/i.test(t)) return "shield";
  if (/관리 보안|교육|점검|파쇄|체크|양식/.test(t) || /\b(?:administrative security|training|inspection|checklist|forms?\b)/i.test(t)) return "clipboard";
  if (/일정|보고|WBS|달력|계획/.test(t) || /\b(?:schedule|report|calendar|plan)/i.test(t)) return "calendar";
  if (/시사점|도구|분석/.test(t) || /\b(?:implication|tool|analy)/i.test(t)) return "gear";
  if (/데이터|DATA|DB|자료/.test(t) || /\b(?:data|database)\b/i.test(t)) return "data";
  return "check";
}
function iconGlyph(pres, slide, box, kind) {
  const d = Math.min(box.w, box.h) * 0.82; // Drawn smaller than the source picture to keep space from nearby text
  const x = box.x + (box.w - d) / 2, y = box.y + (box.h - d) / 2;
  const navy = { color: T.COLOR.navy };
  if ((kind || "") === "person") {
    slide.addShape(pres.ShapeType.ellipse, { x: x + d * 0.3, y: y + d * 0.02, w: d * 0.4, h: d * 0.4, fill: navy, line: { color: "FFFFFF", width: 0, transparency: 100 } });
    slide.addShape(pres.ShapeType.roundRect, { x: x + d * 0.12, y: y + d * 0.46, w: d * 0.76, h: d * 0.52, rectRadius: d * 0.2, fill: navy, line: { color: "FFFFFF", width: 0, transparency: 100 } });
    return;
  }
  const noLine = { color: "FFFFFF", width: 0, transparency: 100 };
  const white = (w) => ({ color: T.COLOR.white, width: w });
  const k = kind || "check";
  if (k === "dashboard") { // Monitor + 3 rising bars + stand
    slide.addShape(pres.ShapeType.roundRect, { x: x + d * 0.05, y: y + d * 0.08, w: d * 0.9, h: d * 0.62, rectRadius: d * 0.06, fill: navy, line: noLine });
    [[0.2, 0.38, 0.2], [0.4, 0.28, 0.3], [0.6, 0.18, 0.4]].forEach(([rx, ry, rh]) => slide.addShape(pres.ShapeType.rect, { x: x + d * rx, y: y + d * ry, w: d * 0.14, h: d * rh, fill: { color: T.COLOR.white }, line: noLine }));
    slide.addShape(pres.ShapeType.rect, { x: x + d * 0.42, y: y + d * 0.72, w: d * 0.16, h: d * 0.1, fill: navy, line: noLine });
    slide.addShape(pres.ShapeType.roundRect, { x: x + d * 0.25, y: y + d * 0.82, w: d * 0.5, h: d * 0.08, rectRadius: d * 0.03, fill: navy, line: noLine });
    return;
  }
  if (k === "shredder") { // Document + slot + body + shredded strips
    slide.addShape(pres.ShapeType.rect, { x: x + d * 0.3, y: y + d * 0.02, w: d * 0.4, h: d * 0.32, fill: { color: T.COLOR.white }, line: { color: T.COLOR.navy, width: Math.max(1, d * 2.5) } });
    [0.1, 0.17, 0.24].forEach((ry) => slide.addShape(pres.ShapeType.line, { x: x + d * 0.36, y: y + d * ry, w: d * 0.28, h: 0, line: { color: T.COLOR.navyPastel, width: Math.max(0.8, d * 1.5) } }));
    slide.addShape(pres.ShapeType.roundRect, { x: x + d * 0.08, y: y + d * 0.34, w: d * 0.84, h: d * 0.38, rectRadius: d * 0.05, fill: navy, line: noLine });
    slide.addShape(pres.ShapeType.rect, { x: x + d * 0.2, y: y + d * 0.4, w: d * 0.6, h: d * 0.05, fill: { color: T.COLOR.white }, line: noLine });
    [0.22, 0.34, 0.46, 0.58, 0.7].forEach((rx) => slide.addShape(pres.ShapeType.rect, { x: x + d * rx, y: y + d * 0.74, w: d * 0.07, h: d * 0.22, fill: { color: T.COLOR.navyPastel }, line: noLine }));
    return;
  }
  if (k === "lock") {
    slide.addShape(pres.ShapeType.roundRect, { x: x + d * 0.28, y: y + d * 0.08, w: d * 0.44, h: d * 0.5, rectRadius: d * 0.15, fill: { color: T.COLOR.white, transparency: 100 }, line: { color: T.COLOR.navy, width: Math.max(1.5, d * 6) } });
    slide.addShape(pres.ShapeType.roundRect, { x: x + d * 0.15, y: y + d * 0.42, w: d * 0.7, h: d * 0.5, rectRadius: d * 0.06, fill: navy, line: noLine });
    slide.addShape(pres.ShapeType.ellipse, { x: x + d * 0.44, y: y + d * 0.58, w: d * 0.12, h: d * 0.12, fill: { color: T.COLOR.white }, line: noLine });
    return;
  }
  if (k === "shield") {
    slide.addShape(pres.ShapeType.homePlate, { x: x + d * 0.12, y: y + d * 0.06, w: d * 0.76, h: d * 0.88, rotate: 90, fill: navy, line: noLine, objectName: "adj:35000" });
    slide.addShape(pres.ShapeType.line, { x: x + d * 0.34, y: y + d * 0.48, w: d * 0.12, h: d * 0.14, line: white(Math.max(1.5, d * 5)) });
    slide.addShape(pres.ShapeType.line, { x: x + d * 0.46, y: y + d * 0.32, w: d * 0.22, h: d * 0.3, flipV: true, line: white(Math.max(1.5, d * 5)) });
    return;
  }
  if (k === "clipboard") {
    slide.addShape(pres.ShapeType.roundRect, { x: x + d * 0.18, y: y + d * 0.1, w: d * 0.64, h: d * 0.82, rectRadius: d * 0.05, fill: navy, line: noLine });
    slide.addShape(pres.ShapeType.rect, { x: x + d * 0.38, y: y + d * 0.04, w: d * 0.24, h: d * 0.12, fill: { color: T.COLOR.textMuted }, line: noLine });
    [0.36, 0.52, 0.68].forEach((ry) => slide.addShape(pres.ShapeType.line, { x: x + d * 0.3, y: y + d * ry, w: d * 0.4, h: 0, line: white(Math.max(1.2, d * 3)) }));
    return;
  }
  if (k === "calendar") {
    slide.addShape(pres.ShapeType.rect, { x: x + d * 0.12, y: y + d * 0.14, w: d * 0.76, h: d * 0.74, fill: { color: T.COLOR.white }, line: { color: T.COLOR.navy, width: Math.max(1.2, d * 4) } });
    slide.addShape(pres.ShapeType.rect, { x: x + d * 0.12, y: y + d * 0.14, w: d * 0.76, h: d * 0.2, fill: navy, line: noLine });
    [[0.28, 0.45], [0.5, 0.45], [0.28, 0.65], [0.5, 0.65]].forEach(([rx, ry]) => slide.addShape(pres.ShapeType.rect, { x: x + d * rx, y: y + d * ry, w: d * 0.14, h: d * 0.12, fill: { color: T.COLOR.navyPastel }, line: noLine }));
    return;
  }
  if (k === "data") {
    slide.addShape(pres.ShapeType.can, { x: x + d * 0.2, y: y + d * 0.08, w: d * 0.6, h: d * 0.84, fill: navy, line: { color: T.COLOR.white, width: 1 } });
    return;
  }
  if (k === "gear") {
    for (let i = 0; i < 4; i++) slide.addShape(pres.ShapeType.rect, { x: x + d * 0.4, y: y + d * 0.06, w: d * 0.2, h: d * 0.88, rotate: i * 45, fill: navy, line: noLine });
    slide.addShape(pres.ShapeType.ellipse, { x: x + d * 0.18, y: y + d * 0.18, w: d * 0.64, h: d * 0.64, fill: navy, line: noLine });
    slide.addShape(pres.ShapeType.ellipse, { x: x + d * 0.38, y: y + d * 0.38, w: d * 0.24, h: d * 0.24, fill: { color: T.COLOR.white }, line: noLine });
    return;
  }
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: navy, line: noLine });
  slide.addShape(pres.ShapeType.line, { x: x + d * 0.28, y: y + d * 0.5, w: d * 0.16, h: d * 0.18, line: white(Math.max(1.5, d * 5)) });
  slide.addShape(pres.ShapeType.line, { x: x + d * 0.44, y: y + d * 0.32, w: d * 0.3, h: d * 0.36, flipV: true, line: white(Math.max(1.5, d * 5)) });
}

/** Line. bentConnector is split into 2-3 straight lines (not supported by pptxgenjs) */
function line(pres, slide, atom) {
  const ln = lineOpt(atom.line, T.PANEL.LINE_PT);
  const opt = { x: atom.x, y: atom.y, w: atom.w, h: atom.h, line: ln, flipH: atom.flipH || undefined, flipV: atom.flipV || undefined, rotate: atom.rot || undefined };
  if (atom.preset === "bentConnector2" || atom.preset === "bentConnector3") {
    const x0 = atom.flipH ? atom.x + atom.w : atom.x;
    const x1 = atom.flipH ? atom.x : atom.x + atom.w;
    const y0 = atom.flipV ? atom.y + atom.h : atom.y;
    const y1 = atom.flipV ? atom.y : atom.y + atom.h;
    const plain = { color: ln.color, width: ln.width, dashType: ln.dashType };
    const pts = atom.preset === "bentConnector2" ? [[x0, y0], [x1, y0], [x1, y1]] : [[x0, y0], [(x0 + x1) / 2, y0], [(x0 + x1) / 2, y1], [x1, y1]];
    // Set the direction (flip) per segment so the arrowhead attaches only at the real end point (end of the last segment)
    for (let i = 0; i < pts.length - 1; i++) {
      const [ax, ay] = pts[i], [bx, by] = pts[i + 1];
      const seg = { x: Math.min(ax, bx), y: Math.min(ay, by), w: Math.abs(bx - ax), h: Math.abs(by - ay), line: { ...plain }, flipH: bx < ax || undefined, flipV: by < ay || undefined };
      if (i === 0 && ln.beginArrowType) seg.line.beginArrowType = ln.beginArrowType;
      if (i === pts.length - 2 && ln.endArrowType) seg.line.endArrowType = ln.endArrowType;
      slide.addShape(pres.ShapeType.line, seg);
    }
    return;
  }
  slide.addShape(pres.ShapeType.line, opt);
}

/** Native table. atom.table = {colw, rowh, rows:[[cell]]}. cell = {colspan,rowspan,merged,fill,va,mg,borders,paras} */
function table(slide, atom, opt) {
  const tb = atom.table;
  const o = opt || {};
  const rows = [];
  const ratioBySz = {};
  for (let pass = 0; pass < 2; pass++) {
  rows.length = 0;
  tb.rows.forEach((r, rowIdx) => {
    const cells = [];
    let colIdx = 0;
    r.forEach((c) => {
      if (c.merged) { colIdx += 1; return; }
      const co = {};
      if (c.colspan) co.colspan = c.colspan;
      if (c.rowspan) co.rowspan = c.rowspan;
      // Without a fill, renderers add the table style accent color, so fix it to white
      co.fill = c.fill && c.fill !== "none" ? { color: remap(c.fill) } : { color: T.COLOR.white };
      co.valign = c.va || "middle";
      // pptxgenjs table cell margin is [top, right, bottom, left] and reads inches when the first value is below 1
      const m = (c.mg && c.mg.length === 4 ? c.mg : []).map((v, i) => (v == null ? T.PANEL.CELL_MG[i] : v));
      const cm = m.length ? m : T.PANEL.CELL_MG;
      co.margin = [cm[1], cm[2], cm[3], cm[0]].map((v) => Math.min(0.99, v));
      const border = ["T", "R", "B", "L"].map((side) => {
        const b = c.borders && c.borders[side];
        if (b && b.color === "none") return { type: "none" };
        if (b) return { type: "solid", pt: b.pt || T.PANEL.LINE_PT, color: remap(b.color || T.COLOR.borderLight) };
        // When the source cell sets borders, unset sides get no line (transparent unit rows). Generated templates (unset) get the default gray line
        if (c.borders) return { type: "none" };
        return { type: "solid", pt: T.PANEL.LINE_PT, color: T.COLOR.borderLight };
      });
      co.border = border;
      let paras = c.paras || [{ runs: [{ t: "", sz: o.sz || T.SIZE.tableBody }] }];
      // Forced line breaks in a cell are joined with spaces when the text fits on one line, preventing row height growth
      paras = paras.map((p) => {
        if (!p.runs.some((r) => r.br)) return p;
        const joined = p.runs.map((r) => (r.br ? " " : r.t)).join("").replace(/\s+/g, " ").trim();
        const r0 = p.runs.find((r) => !r.br) || p.runs[0];
        const cwTmp = tb.colw.slice(colIdx, colIdx + (c.colspan || 1)).reduce((x, y) => x + y, 0) - 0.16;
        return estimateLines(joined, cwTmp, r0.sz || T.SIZE.tableBody, r0.b) <= 1 ? { ...p, runs: [{ ...r0, t: joined }] } : p;
      });
      // Shrink the font to the cell width (merges included) and row height. The column index accumulates while skipping merged cells
      const span = c.colspan || 1;
      const cw = tb.colw.slice(colIdx, colIdx + span).reduce((a, b) => a + b, 0);
      const rh = tb.rowh.slice(rowIdx, rowIdx + (c.rowspan || 1)).reduce((a, b) => a + b, 0);
      // Prevent row height growth: NanumGothic line spacing is high, so judge with a 0.05 inch margin and 1.35 spacing. The same source size shares one shrink ratio across the table (so sizes do not drift per cell)
      // Multi-line cells (2 or more paragraphs, or wrapping at the source size) let the row grow as in the source. Only 1-line cells shrink to the row height
      const r00 = paras[0].runs.find((x) => !x.br) || paras[0].runs[0];
      const multi = paras.length >= 2 || estimateLines(paras[0].runs.filter((x) => !x.br).map((x) => x.t).join(""), cw - cm[0] - cm[2], r00.sz || T.SIZE.tableBody, r00.b) > 1;
      const fitted = fitParas(paras, cw - cm[0] - cm[2], multi ? 99 : rh - cm[1] - cm[3] - 0.05, o.minPt || T.SIZE.OWN_MIN - 1, T.METRIC.TABLE_LINE_HEIGHT);
      const sz0 = Math.round((paras[0].runs[0] && paras[0].runs[0].sz) || o.sz || T.SIZE.tableBody);
      const r = ((fitted[0].runs[0] && fitted[0].runs[0].sz) || sz0) / sz0;
      if (pass === 0) { (ratioBySz[sz0] = ratioBySz[sz0] || []).push(r); return; }
      // Unify on the shrink ratio that fits most (80%) cells and shrink only the few narrow cells individually (so the whole table is not dragged down by the smallest cell)
      const arr = (ratioBySz[sz0] || [1]).slice().sort((p, q) => p - q);
      const uni = Math.min(arr[Math.floor(arr.length * 0.2)], 1);
      const own = r;
      const use = Math.min(uni, own < uni ? own : uni);
      paras = paras.map((p) => ({ ...p, runs: p.runs.map((x) => ({ ...x, sz: Math.max(o.minPt || T.SIZE.OWN_MIN - 1, +(((x.sz || sz0) * use)).toFixed(1)) })) }));
      const runs = runsOf(paras, { sz: o.sz || T.SIZE.tableBody });
      // Cell alignment is the first paragraph's align, otherwise the column rule (set by the caller through opt.align)
      const al = paras[0] && paras[0].align ? paras[0].align : (o.align || "left");
      co.align = al;
      co.fontFace = T.FONT.regular;
      cells.push({ text: runs, options: co });
      colIdx += span;
    });
    rows.push(cells);
  });
  }
  slide.addTable(rows, {
    x: atom.x, y: atom.y, w: atom.w, h: atom.h,
    colW: tb.colw, rowH: tb.rowh,
    fontFace: T.FONT.regular, fontSize: o.sz || T.SIZE.tableBody, color: T.COLOR.textDark,
    autoPage: false,
  });
}

/** Native chart. spec = {type: bar|line|pie|doughnut, barDir, categories, series:[{name, values}], holeSize, showLegend, highlight} */
const COL_GAP_SINGLE = 130; // Bar gap for single-series column bars (% of bar width)
const NEG_LABEL_ROOM = 0.22, POS_LABEL_ROOM = 0.12; // Value axis room for bar charts with negatives (relative to the value range. Label room under negative bars and above positive bars)
/** n colors spaced evenly between two colors (both end colors included) */
function rampBetween(from, to, n) {
  const rgb = (hex) => [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16));
  const [a, b] = [rgb(from), rgb(to)];
  return Array.from({ length: n }, (_, k) => a.map((v, j) => Math.round(v + ((b[j] - v) * k) / (n - 1)).toString(16).padStart(2, "0")).join("").toUpperCase());
}
function chart(pres, slide, box, spec) {
  const ctype = { bar: pres.ChartType.bar, line: pres.ChartType.line, pie: pres.ChartType.pie, doughnut: pres.ChartType.doughnut, area: pres.ChartType.area }[spec.type] || pres.ChartType.bar;
  let cats = (spec.categories || []).map(String);
  let series = (spec.series || []).map((s) => ({ name: s.name || "", labels: cats, values: (s.values || []).map((v) => (v == null ? 0 : v)) }));
  if (!series.length) series = [{ name: "", labels: cats, values: cats.map(() => 0) }];
  const opt = {
    x: box.x, y: box.y, w: box.w, h: box.h,
    chartColors: series.length > 1 ? T.COLOR.navyRamp : [T.COLOR.navyPastel],
    showValue: true, dataLabelFontSize: T.SIZE.tableDense, dataLabelColor: T.COLOR.textDark, dataLabelFontFace: T.FONT.regular,
    dataLabelFormatCode: spec.numFmt || undefined, valAxisLabelFormatCode: spec.numFmt || undefined,
    catAxisLabelFontSize: T.SIZE.tableDense, catAxisLabelFontFace: T.FONT.regular, catAxisLabelColor: T.COLOR.textDark,
    valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, catAxisLineShow: false, valAxisLineShow: false,
    showLegend: !!spec.showLegend || series.length > 1, legendPos: "b", legendFontSize: T.SIZE.tableDense, legendFontFace: T.FONT.regular,
    showTitle: false, border: { pt: 0, color: "FFFFFF" }, plotArea: { border: { pt: 0, color: "FFFFFF" } },
  };
  if (spec.type === "bar") {
    opt.barDir = spec.barDir === "bar" ? "bar" : "col";
    if (opt.barDir === "bar" && series.length === 1 && !spec.keepOrder) {
      // Item comparison puts the largest value on top: sort descending and reverse the category axis
      const pairs = cats.map((c, i) => [c, series[0].values[i]]).sort((a, b) => b[1] - a[1]);
      cats = pairs.map((p) => p[0]);
      series[0].labels = cats;
      series[0].values = pairs.map((p) => p[1]);
      opt.catAxisOrientation = "maxMin";
    }
    // Single-series column bars get wider gaps and thinner bars (so length differences stand out)
    opt.barGapWidthPct = series.length === 1 && opt.barDir === "col" ? COL_GAP_SINGLE : 60;
    if (spec.grouping === "stacked" || spec.grouping === "percentStacked") {
      opt.barGrouping = spec.grouping; opt.dataLabelPosition = "ctr";
      // Labels inside segments use one dark text color, so drop the darkest navy and use only the lighter colors
      // With more series than light colors, space colors evenly between the darkest and lightest light color (the background tint is not used as a series color because it does not stand out from white)
      if (series.length > 1) {
        const light = T.COLOR.navyRamp.slice(1);
        opt.chartColors = series.length > light.length ? rampBetween(light[0], light[light.length - 1], series.length) : light;
      }
    }
    // With negative bars, the zero baseline must show for the direction of change to read, so show the category axis line
    if (series.some((sr) => sr.values.some((v) => v < 0))) {
      opt.catAxisLineShow = true; opt.catAxisLineColor = T.COLOR.border; opt.catAxisLabelPos = "low";
      // Category names sit at the bottom edge (low), so leave label room at the value axis minimum and maximum to keep labels past the longest negative bar off the category name line
      if (!opt.barGrouping) {
        const all = series.flatMap((sr) => sr.values);
        const lo = Math.min(0, ...all), hi = Math.max(0, ...all), span = hi - lo || 1;
        opt.valAxisMinVal = +(lo - span * NEG_LABEL_ROOM).toFixed(4);
        if (hi > 0) opt.valAxisMaxVal = +(hi + span * POS_LABEL_ROOM).toFixed(4);
      }
    }
    // A stacked bar with 1 category (share bar) hides the axis because the category name overlaps the cell caption
    if (cats.length === 1) opt.catAxisHidden = true;
    if (spec.highlight != null && series.length === 1) {
      opt.chartColors = series[0].values.map((_, i) => (i === spec.highlight ? T.COLOR.navy : T.COLOR.navyPastel));
    }
  }
  if (spec.type === "pie" || spec.type === "doughnut") {
    opt.chartColors = series[0].values.map((_, i) => T.COLOR.navyRamp[i % T.COLOR.navyRamp.length]);
    opt.showLegend = true; opt.legendPos = "r";
    // WHY: pptxgenjs allows only one label color per chart. White text inside segments is unreadable on light segments,
    //      so labels go outside the segments in dark text
    opt.dataLabelPosition = "outEnd"; opt.showPercent = true; opt.showValue = false;
    opt.dataLabelColor = T.COLOR.textDark;
    if (spec.type === "doughnut") { opt.holeSize = spec.holeSize || 78; opt.showLegend = false; opt.showPercent = false; opt.showValue = false; opt.showLabel = false; } // A separate text box carries the center figure text
  }
  if (spec.type === "line") { opt.lineSize = 2; opt.lineDataSymbol = "circle"; opt.lineDataSymbolSize = 6; opt.chartColors = [T.COLOR.navy, T.COLOR.navyPastel, T.COLOR.navyPastel2]; opt.dataLabelPosition = "t"; } // Labels sit above the markers so they do not overlap the line
  slide.addChart(ctype, series, opt);
}

let IMAGE_BASE = null; // Storyboard folder. Base for relative paths so the same storyboard finds the same images wherever it is built

/** Sets the base folder for relative image paths (build.js sets it to the storyboard folder) */
function setImageBase(dir) { IMAGE_BASE = dir; }

/** Resolves an image path. A relative path uses the file under the storyboard folder if it exists, otherwise the working folder (keeps the earlier behavior) */
function resolveImage(src) {
  if (!src || /^data:/.test(src) || path.isAbsolute(src) || !IMAGE_BASE) return src;
  const p = path.resolve(IMAGE_BASE, src);
  return fs.existsSync(p) ? p : src;
}

/** Image. Without a path, a placeholder box (tint fill, dashed line, "이미지" label) */
function image(pres, slide, box, srcIn, opt) {
  const o = opt || {};
  const src = resolveImage(srcIn);
  if (src) {
    // Read the source aspect ratio, fit it inside the box (contain) and center it. pptxgenjs sizing is interpreted differently by renderers, so compute it directly
    const dim = imageDims(src);
    let { x, y, w, h } = box;
    if (dim && dim.w && dim.h && o.fit !== "stretch") {
      const r = Math.min(box.w / dim.w, box.h / dim.h);
      w = +(dim.w * r).toFixed(3); h = +(dim.h * r).toFixed(3);
      x = +(box.x + (box.w - w) / 2).toFixed(3); y = +(box.y + (box.h - h) / 2).toFixed(3);
    }
    const im = { x, y, w, h };
    if (/^data:/.test(src)) im.data = src; else im.path = src;
    if (src !== srcIn) im.altText = srcIn; // Alt text is the path as written in the storyboard (keeps absolute work folder paths out of the file)
    slide.addImage(im);
  } else {
    slide.addText([{ text: o.label || "이미지", options: { fontSize: T.SIZE.note, color: T.COLOR.textMuted, fontFace: T.FONT.regular } }], {
      x: box.x, y: box.y, w: box.w, h: box.h, shape: pres.ShapeType.rect, fill: { color: T.COLOR.tintLight },
      line: { color: T.COLOR.borderLight, width: 0.5, dashType: "dash" }, align: "center", valign: "middle", margin: 0,
    });
  }
  // A caption is body-type text describing the image, so it uses the body minimum size (11pt) and body text color (textDark) (set apart from small gray note text)
  if (o.caption) text(slide, { x: box.x, y: box.y + box.h + 0.03, w: box.w, h: 0.25 }, o.caption, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textDark, align: "center", mg: [0, 0, 0, 0] });
}

/** Pixel size of PNG, JPEG, GIF (path or data URI). null on failure */
function imageDims(src) {
  try {
    const fs = require("fs");
    let buf;
    if (/^data:/.test(src)) buf = Buffer.from(src.split(",")[1], "base64");
    else buf = fs.readFileSync(src);
    if (buf[0] === 0x89 && buf[1] === 0x50) return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
    if (buf[0] === 0x47 && buf[1] === 0x49) return { w: buf.readUInt16LE(6), h: buf.readUInt16LE(8) };
    if (buf[0] === 0xff && buf[1] === 0xd8) {
      let i = 2;
      while (i < buf.length) {
        if (buf[i] !== 0xff) { i++; continue; }
        const m = buf[i + 1];
        if (m >= 0xc0 && m <= 0xcf && m !== 0xc4 && m !== 0xc8 && m !== 0xcc) return { h: buf.readUInt16BE(i + 5), w: buf.readUInt16BE(i + 7) };
        i += 2 + buf.readUInt16BE(i + 2);
      }
    }
  } catch (e) { /* size unknown */ }
  return null;
}

// ---------------------------------------------------------------- Band
function markerGlyph(pres, slide, S) {
  const m = T.MARKER;
  const g = m[m.shape] || m.square;
  const cx = S.markerShape.x + S.markerShape.w / 2;
  const cy = S.markerShape.y + S.markerShape.h / 2;
  const st = m.shape === "triangle" ? pres.ShapeType.triangle : pres.ShapeType.rect;
  const x = m.shape === "square" ? S.markerShape.x : cx - g.w / 2;
  slide.addShape(st, { x, y: cy - g.h / 2, w: g.w, h: g.h, fill: { color: T.COLOR.navy }, line: { color: "FFFFFF", width: 0, transparency: 100 }, rotate: m.shape === "triangle" ? 90 : undefined });
}

/**
 * Body slide band. mode: full (with marker) | noMarker | headerOnly
 * band = {secNo, secTitle, tracker, headline, marker}
 */
function bodyBand(pres, slide, S, band, mode, opt) {
  const o = opt || {};
  const hl = band.headline || "";
  // The section number and title are typeset as two runs in one paragraph so the title follows the number whatever the digit count and font width
  // (separate number and title boxes let the period and title overlap depending on renderer glyph widths when the number grows, as in "10.")
  const no = band.secNo || "";
  if (no) {
    const runs = [{ t: `${no} `, sz: T.SIZE.secNo, color: T.COLOR.textDark }, { t: band.secTitle || "", sz: T.SIZE.secTitle, color: T.COLOR.textDark }];
    text(slide, { x: S.secNo.x, y: S.secNo.y, w: S.secTitle.x + S.secTitle.w - S.secNo.x, h: S.secNo.h }, [{ align: "left", runs }], { valign: "middle", mg: [0, 0, 0, 0] });
  } else text(slide, S.secTitle, band.secTitle || "", { sz: T.SIZE.secTitle, color: T.COLOR.textDark, valign: "middle", mg: [0, 0, 0, 0] });
  text(slide, S.tracker, band.tracker || "", { sz: T.SIZE.tracker, color: T.COLOR.textDark, align: "right", valign: "middle", mg: [0, 0, 0, 0] });
  if (mode === "headerOnly") return;
  const hlParas = o.accentHeadline ? headlineWithAccent(hl, o.accentHeadline) : parasFromString(hl, { sz: T.SIZE.headline, b: true, color: T.COLOR.textDark, align: "center" });
  text(slide, S.headline, hlParas, { valign: "middle", mg: [0, 0, 0, 0] });
  // The headline belongs to the band only when it sits between the top and bottom rules, so the two rules are drawn as a pair
  for (const ry of [S.ruleTopY, S.ruleY]) {
    slide.addShape(pres.ShapeType.line, { x: S.marginX, y: ry, w: S.ruleW, h: 0, line: { color: T.COLOR.textDark, width: T.BAND.RULE_PT } });
  }
  if (mode === "noMarker") return;
  markerGlyph(pres, slide, S);
  text(slide, S.markerText, band.marker || "", { sz: T.SIZE.marker, bold: true, color: T.COLOR.textDark, valign: "middle", mg: [0, 0, 0, 0] });
  // Subtitle with footnote numbers to the right of the marker band (optional)
  if (band.markerNote) {
    const x = S.markerText.x + textEm(band.marker || "", true) * T.SIZE.marker / 72 + 0.25;
    text(slide, { x, y: S.markerText.y, w: Math.max(1.0, S.marginX + S.ruleW - x), h: S.markerText.h }, band.markerNote,
      { sz: T.SIZE.note, color: T.COLOR.textMuted, valign: "middle", mg: [0, 0, 0, 0] });
  }
}
/** Colors one key phrase of the headline with the accent color */
function headlineWithAccent(hl, phrase) {
  const sz = T.SIZE.headline;
  const i = hl.indexOf(phrase);
  if (i < 0) return parasFromString(hl, { sz, b: true, color: T.COLOR.textDark, align: "center" });
  return [{ align: "center", runs: [
    { t: hl.slice(0, i), sz, b: true, color: T.COLOR.textDark },
    { t: phrase, sz, b: true, color: T.COLOR.accent },
    { t: hl.slice(i + phrase.length), sz, b: true, color: T.COLOR.textDark },
  ] }];
}
/** Footnote list. Placed above the source line at the slide bottom in the 1) 2) format */
function footnotes(slide, S, items) {
  const arr = [].concat(items || []).filter(Boolean);
  if (!arr.length) return;
  const paras = arr.map((t, i) => ({ align: "left", runs: [{ t: /^\d+\)/.test(String(t).trim()) ? String(t) : `${i + 1}) ${t}`, sz: T.SIZE.note, color: T.COLOR.textMuted }] }));
  text(slide, { x: S.bodyX, y: S.noteY - 0.2 * arr.length, w: S.bodyW, h: 0.2 * arr.length }, paras, { valign: "top", mg: [0, 0, 0, 0] });
}
function pageNo(slide, S, n) {
  text(slide, S.pageNo, String(n), { sz: T.SIZE.pageNo, color: T.COLOR.textGray, align: "right", valign: "middle", mg: [0, 0, 0, 0] });
}

// ---------------------------------------------------------------- Custom slide playback
/**
 * Typesets own-deck slide atoms in order. slots replace text, table cells and images
 * slots keys: t{k} (k-th text atom), tb{k}.r{i}c{j}, img{k}, ch{k} (chart spec)
 * Returns: {textIds:[{id, text}], imageIds, chartIds} (for templates.md documentation and lint)
 */
function playOwn(pres, slide, ownSlideSrc, slots, ctx) {
  const ownSlide = { ...ownSlideSrc, atoms: ownSlideSrc.atoms.map((a) => ({ ...a })) }; // Shallow copy so coordinate adjustments do not accumulate in the source geometry
  const sl = slots || {};
  const ids = { texts: [], tables: [], images: [], charts: [] };
  let tk = 0, bk = 0, ik = 0, ck = 0;
  const sx = ctx && ctx.S ? ctx.S.sx : 1;
  const sy = ctx && ctx.S ? ctx.S.sy : 1;
  const sc = (a) => (sx === 1 && sy === 1 ? a : { ...a, x: +(a.x * sx).toFixed(3), y: +(a.y * sy).toFixed(3), w: +(a.w * sx).toFixed(3), h: +(a.h * sy).toFixed(3) });
  // Pre-pass: minimum shrink ratio per group of equal source font sizes (keeps sibling boxes at matching sizes). Substituted slot text is approximated from the source
  const ratioBySize = {};
  const skippedBoxes = []; // Boxes omitted by empty string slots. Connectors touching them are omitted too
  const widen = {}; // Table index → new right end x (absorbs the illustration spot)
  const widenLeft = {}; // Table index → new left start x
  const skipImage = new Set();
  const tinyCount = ownSlide.atoms.filter((o) => o.kind === "image" && o.w < 0.45 && o.h < 0.45).length;
  const skipShape = new Set();
  // Arrows are centered on the boxes above and below (corrects small offsets in the source)
  const ARROW = new Set(["downArrow", "upArrow", "leftArrow", "rightArrow"]);
  ownSlide.atoms.forEach((a) => {
    if (a.kind !== "shape" || !ARROW.has(a.preset)) return;
    const cx0 = a.x + a.w / 2, cy0 = a.y + a.h / 2;
    // A vertical arrow between side-by-side boxes becomes a horizontal arrow (and the reverse)
    const yOverlap = (b) => Math.min(b.y + b.h, a.y + a.h) - Math.max(b.y, a.y) > a.h * 0.4;
    const xOverlap = (b) => Math.min(b.x + b.w, a.x + a.w) - Math.max(b.x, a.x) > a.w * 0.4;
    const cand = ownSlide.atoms.filter((b) => b !== a && b.kind === "shape" && !ARROW.has(b.preset) && b.w > a.w * 2);
    const rowMates = cand.filter((b) => yOverlap(b) && Math.abs(b.x + b.w / 2 - cx0) < b.w + 0.8);
    const colMates = cand.filter((b) => xOverlap(b) && Math.abs(b.y + b.h / 2 - cy0) < b.h + 0.8);
    // Boxes on both sides make it horizontal, boxes above and below make it vertical
    const hasLeft = rowMates.some((b) => b.x + b.w <= cx0 + 0.05);
    const hasRight = rowMates.some((b) => b.x >= cx0 - 0.05);
    const hasUp = colMates.some((b) => b.y + b.h <= cy0 + 0.05);
    const hasDown = colMates.some((b) => b.y >= cy0 - 0.05);
    // With boxes in both directions, follow the closer side
    const dMin = (arr, f) => arr.length ? Math.min(...arr.map(f)) : 99;
    const hGap = Math.max(dMin(rowMates.filter((b) => b.x + b.w <= cx0 + 0.05), (b) => cx0 - (b.x + b.w)),
                          dMin(rowMates.filter((b) => b.x >= cx0 - 0.05), (b) => b.x - cx0));
    const vGap = Math.max(dMin(colMates.filter((b) => b.y + b.h <= cy0 + 0.05), (b) => cy0 - (b.y + b.h)),
                          dMin(colMates.filter((b) => b.y >= cy0 - 0.05), (b) => b.y - cy0));
    if (hasLeft && hasRight && (!(hasUp && hasDown) || hGap < vGap)) { if (a.preset === "downArrow" || a.preset === "upArrow") a.preset = "rightArrow"; }
    else if (hasUp && hasDown && (!(hasLeft && hasRight) || vGap <= hGap)) { if (a.preset === "rightArrow" || a.preset === "leftArrow") a.preset = "downArrow"; }
    const cx = a.x + a.w / 2, cy = a.y + a.h / 2;
    const vert = a.preset === "downArrow" || a.preset === "upArrow";
    const near = ownSlide.atoms.filter((b) => b !== a && b.kind === "shape" && !ARROW.has(b.preset) && b.w > a.w * 3
      && (vert ? Math.abs(b.x + b.w / 2 - cx) < b.w / 2 && Math.abs(b.y + b.h / 2 - cy) < b.h + 0.8
               : Math.abs(b.y + b.h / 2 - cy) < b.h / 2 && Math.abs(b.x + b.w / 2 - cx) < b.w + 0.8));
    if (near.length < 2) return;
    if (vert) {
      // The cross axis goes to the box center, and the travel axis to the middle of the gap between the boxes above and below
      const target = near.reduce((s2, b) => s2 + b.x + b.w / 2, 0) / near.length;
      if (Math.abs(target - cx) < 0.25) a.x = +(target - a.w / 2).toFixed(3);
      // The travel axis (vertical) position stays as in the source so the arrow keeps pointing at the same target
    } else {
      const target = near.reduce((s2, b) => s2 + b.y + b.h / 2, 0) / near.length;
      if (Math.abs(target - cy) < 0.25) a.y = +(target - a.h / 2).toFixed(3);
      // The travel axis (horizontal) position stays as in the source
    }
  });
  const panelFrames = []; // Panel borders drawn separately at the source size
  const chevronStrip = [];
  const bigIcons = [];
  const fillBox = new Set();
  const narrowTo = {};
  const shrinkTo = {};
  const grow = {}; // Text box → new height (absorbs the icon strip area below)
  if (tinyCount >= 4) {
    const strip = ownSlide.atoms.filter((o) => o.kind === "image" && o.w < 0.45 && o.h < 0.45);
    const bottom = Math.max(...strip.map((o) => o.y + o.h)), top = Math.min(...strip.map((o) => o.y)), sx0 = Math.min(...strip.map((o) => o.x)), sx1 = Math.max(...strip.map((o) => o.x + o.w));
    const above = ownSlide.atoms.filter((o) => o.paras && o.y < top - 0.3 && o.y + o.h > top - 0.6 && o.x < sx1 && o.x + o.w > sx0).sort((p, q) => (q.y + q.h) - (p.y + p.h))[0];
    if (above) {
      if (above.y + above.h > top) shrinkTo[ownSlide.atoms.indexOf(above)] = top - above.y - 0.05; // A text box containing the strip shrinks to just above the strip
      // Draw the parenthesized labels of the text above ("(도구 연결) …") as step chevrons to fill the strip area
      const labels = [];
      above.paras.forEach((p) => { const m = p.runs.map((r) => r.t).join("").match(/^\s*[\(（]([^)）]{2,12})[\)）]/); if (m) labels.push(m[1]); });
      delete shrinkTo[ownSlide.atoms.indexOf(above)];
      grow[ownSlide.atoms.indexOf(above)] = bottom - above.y + 0.05; // Extend the text box over the strip area and enlarge the font to fill it (fill)
      fillBox.add(ownSlide.atoms.indexOf(above));
      // With a large icon (calendar, etc.) at the same height inside the box, limit the text width to just before it
      const bigIcon = ownSlide.atoms.find((o) => o.kind === "image" && o.w >= 0.45 && o.x > above.x + above.w * 0.5 && o.x < above.x + above.w && o.y < bottom && o.y + o.h > above.y);
      if (bigIcon) { // The panel border is drawn separately at the source size and only the text box shrinks to just before the icon
        if (above.fill || (above.line && above.line.color && above.line.color !== "none")) {
          panelFrames.push({ x: above.x, y: above.y, w: above.w, h: bottom - above.y + 0.05, fill: above.fill, line: above.line, preset: above.preset });
          above.fill = "none"; above.line = { color: "none" };
        }
        narrowTo[ownSlide.atoms.indexOf(above)] = bigIcon.x - above.x - 0.1;
        bigIcon.y = +((above.y + bottom + 0.05) / 2 - bigIcon.h / 2).toFixed(3);
      }
    }
    // Small connecting shapes (arrows, labels) at the strip height are omitted too
    ownSlide.atoms.forEach((o) => { if (o !== above && o.kind !== "image" && o.y >= top - 0.15 && o.y + o.h <= bottom + 0.15 && o.x >= sx0 - 0.3 && o.x + o.w <= sx1 + 1.5) skipShape.add(o); });
  }
  // A text box covered by an image that becomes an icon shrinks to the icon's left edge to prevent overlap (applied before drawing)
  ownSlide.atoms.forEach((im, k) => {
    if (im.kind !== "image" || im.identity) return;
    const id = "img" + ownSlide.atoms.slice(0, k + 1).filter((o) => o.kind === "image").length;
    if (sl[id] || im.w >= T.PANEL.ICON_MAX || im.h >= T.PANEL.ICON_MAX) return;
    ownSlide.atoms.forEach((o) => {
      if (narrowTo[ownSlide.atoms.indexOf(o)] || fillBox.has(ownSlide.atoms.indexOf(o))) return; // Skip boxes already adjusted by the strip absorption rule
      if (!o.paras || o.kind === "table") return;
      const ox = Math.min(o.x + o.w, im.x + im.w) - Math.max(o.x, im.x);
      const oy = Math.min(o.y + o.h, im.y + im.h) - Math.max(o.y, im.y);
      if (ox <= 0.05 || oy <= 0.05 || o.x >= im.x - 0.2) return;
      // Draw the panel border separately at the source size, and shrink only the text box to just before the icon to prevent overlap
      const nw = im.x - 0.1 - o.x;
      if (nw < o.w * 0.5) return;
      if (o.fill || (o.line && o.line.color && o.line.color !== "none")) {
        panelFrames.push({ x: o.x, y: o.y, w: o.w, h: o.h, fill: o.fill, line: o.line, preset: o.preset });
        o.fill = "none"; o.line = { color: "none" };
      }
      o.w = +nw.toFixed(3);
    });
  });
  // A "시각자료" placeholder box inside a text box is omitted unless a slot fills it, and the text takes the whole area
  ownSlide.atoms.forEach((o) => {
    const t = ((o.paras || []).flatMap((p) => p.runs.map((r) => r.t)).join("") || "").trim();
    if (o.kind !== "shape" || !/^(시각자료|이미지|사진|도식|산출물 화면)$/.test(t)) return;
    if (sl["~" + t] || sl[t]) return; // Kept when the user sets content
    skipShape.add(o);
  });
  // When a large illustration (image) sits inside a text box, the text area shrinks to just above it
  ownSlide.atoms.forEach((im) => {
    if (im.kind !== "image" || im.identity || im.w < T.PANEL.ICON_MAX) return;
    ownSlide.atoms.forEach((o, oi) => {
      if (!o.paras || o.kind === "table" || narrowTo[oi] || fillBox.has(oi) || shrinkTo[oi]) return;
      const ox = Math.min(o.x + o.w, im.x + im.w) - Math.max(o.x, im.x);
      const oy = Math.min(o.y + o.h, im.y + im.h) - Math.max(o.y, im.y);
      if (ox <= 0.1 || oy <= 0.1) return;
      if (im.y - o.y < 0.3) return; // When the image covers the top of the box, the width adjustment rule handles it
      shrinkTo[oi] = im.y - o.y - 0.08; // Text goes only above the illustration
    });
  });
  let ik0 = 0;
  for (const raw of ownSlide.atoms) {
    if (raw.kind !== "image") continue;
    ik0 += 1;
    if (sl["img" + ik0] || raw.identity || raw.w <= 1.5 || raw.h <= 0.9) continue;
    const tbL = ownSlide.atoms.find((o) => o.kind === "table" && o.y < raw.y + raw.h && o.y + o.h > raw.y && o.x > raw.x + raw.w - 0.5 && !ownSlide.atoms.some((m) => m !== o && m !== raw && m.kind !== "line" && m.x > raw.x + raw.w - 0.1 && m.x < o.x && m.y < o.y + o.h && m.y + m.h > o.y));
    if (tbL) { // The illustration spot left of a table (certificates, etc.) is omitted and the table widens to the left
      widenLeft[ownSlide.atoms.indexOf(tbL)] = raw.x * sx; skipImage.add(raw); continue;
    }
    const tb = ownSlide.atoms.find((o) => o.kind === "table" && o.y < raw.y + raw.h && o.y + o.h > raw.y && o.x + o.w < raw.x + 0.5);
    if (tb) {
      // With other elements between the table and the illustration, widen only up to those elements
      const between = ownSlide.atoms.filter((o) => o !== tb && o !== raw && o.kind !== "line" && o.x > tb.x + tb.w - 0.1 && o.x < raw.x && o.y < tb.y + tb.h + 0.6 && o.y + o.h > tb.y - 0.6);
      // Push the in-between elements (procedure lists, etc.) to the illustration's right end and widen the table up to them, removing empty area
      // Full-width title text is excluded, and only list boxes move
      const movable = between.filter((o) => o.w < (raw.x + raw.w - tb.x - tb.w) * 0.6);
      // List boxes keep the source width, and the illustration spot is filled with a topic icon and caption
      if (movable.length) {
        const near = ownSlide.atoms.filter((o) => o.paras).map((o) => o.paras.map((p) => p.runs.map((r) => r.t).join("")).join(" ")).join(" ");
        bigIcons.push({ x: raw.x * sx, y: raw.y * sy, w: raw.w * sx, h: raw.h * sy, kind: iconKind(raw, [near]), caption: /파쇄/.test(near) ? "현장 파쇄 후 파쇄확인서 제출" : "" });
      }
      // Spread the in-between elements evenly over the table's vertical range (removes empty area below)
      if (movable.length > 1) {
        const top0 = Math.min(...movable.map((o) => o.y)), bot0 = Math.max(...movable.map((o) => o.y + o.h));
        const span0 = bot0 - top0, span1 = tb.y + tb.h - top0;
        if (span1 > span0 + 0.2) movable.forEach((o) => { o.y = +(top0 + (o.y - top0) * (span1 - o.h) / Math.max(0.01, span0 - o.h)).toFixed(3); });
      }
      if (!movable.length) widen[ownSlide.atoms.indexOf(tb)] = (raw.x + raw.w) * sx; // Without in-between elements, widen the table
      if (movable.length > 1) { // Spread the list boxes evenly over the table's vertical range
        const top0 = Math.min(...movable.map((o) => o.y)), bot0 = Math.max(...movable.map((o) => o.y + o.h));
        const span0 = bot0 - top0, span1 = tb.y + tb.h - top0;
        if (span1 > span0 + 0.2) movable.forEach((o) => { o.y = +(top0 + (o.y - top0) * (span1 - o.h) / Math.max(0.01, span0 - o.h)).toFixed(3); });
      }
      skipImage.add(raw);
    }
  }
  let pk = 0;
  for (const raw of ownSlide.atoms) {
    if ((raw.kind !== "shape" && raw.kind !== "graphic") || !raw.paras) continue;
    pk += 1;
    const a = sc(raw);
    const cur0 = a.paras.map((p) => p.runs.map((x) => x.t).join("")).join("\n");
    const v0 = sl["t" + pk] != null ? sl["t" + pk] : textKey(sl, cur0);
    if (v0 === "") { skippedBoxes.push(raw); continue; }
    const paras = v0 != null ? substitute(a.paras, v0) : a.paras;
    const r = shrinkRatio(a, paras, T.SIZE.OWN_MIN);
    const key = sizeKey(a, paras);
    ratioBySize[key] = Math.min(ratioBySize[key] == null ? 1 : ratioBySize[key], r);
  }
  // Absorb empty area from omitted columns: remaining boxes in the same row strip (same y, h) are spread over the full original width
  if (skippedBoxes.length) {
    const band = (a) => `${Math.round(a.y * 20)}|${Math.round(a.h * 20)}|${Math.round(a.w * 20)}`; // Repeated columns with the same y, h, w
    const groups = {};
    ownSlide.atoms.forEach((a) => {
      if (a.kind !== "shape" && a.kind !== "graphic") return;
      if (!a.paras && !skippedBoxes.includes(a)) return;
      (groups[band(a)] = groups[band(a)] || []).push(a);
    });
    const shift = new Map();
    Object.values(groups).forEach((g) => {
      const kept = g.filter((a) => !skippedBoxes.includes(a)).sort((p, q) => p.x - q.x);
      const dropped = g.filter((a) => skippedBoxes.includes(a));
      if (!dropped.length || kept.length < 1 || g.length < 2) return;
      const x0 = Math.min(...g.map((a) => a.x));
      const x1 = Math.max(...g.map((a) => a.x + a.w));
      const gap = g.length > 1 ? (x1 - x0 - g.length * g[0].w) / (g.length - 1) : 0;
      const w = (x1 - x0 - gap * (kept.length - 1)) / kept.length;
      kept.forEach((a, i) => {
        const nx = x0 + i * (w + gap);
        shift.set(a, [nx - a.x, w / a.w]);
        a.x = +nx.toFixed(3);
        a.w = +w.toFixed(3);
      });
    });
    // Connectors and small shapes inside redistributed boxes move by the same ratio
    if (shift.size) {
      const moved = [...shift.keys()];
      ownSlide.atoms.forEach((o) => {
        if (shift.has(o) || o.kind === "table" || o.kind === "chart") return;
        const host = moved.find((m) => o.x >= m.x - (shift.get(m)[0] || 0) - 0.05 && o.x + o.w <= m.x - shift.get(m)[0] + m.w / shift.get(m)[1] + 0.05 && o.y >= m.y - 0.05 && o.y + o.h <= m.y + m.h + 0.05);
        if (!host) return;
        const [dx, k] = shift.get(host);
        const relX = o.x - (host.x - dx);
        o.x = +(host.x + relX * k).toFixed(3);
        o.w = +(o.w * k).toFixed(3);
      });
    }
  }
  panelFrames.forEach((f) => {
    const a = sc({ x: f.x, y: f.y, w: f.w, h: f.h });
    slide.addShape(shapeType(pres, f.preset), { x: a.x, y: a.y, w: a.w, h: a.h,
      fill: f.fill && f.fill !== "none" ? { color: remap(f.fill) } : { color: T.COLOR.white, transparency: 100 },
      line: f.line && f.line.color && f.line.color !== "none" ? { color: remap(f.line.color), width: f.line.pt || T.PANEL.LINE_PT, dashType: f.line.dash ? DASH_MAP[f.line.dash] : undefined } : { color: "FFFFFF", width: 0, transparency: 100 } });
  });
  for (const raw of ownSlide.atoms) {
    const atom = sc(raw);
    if (atom.kind === "image") {
      ik += 1;
      const id = "img" + ik;
      ids.images.push(id);
      if (atom.identity && !sl[id]) continue; // Logo: omitted when not provided
      if (!sl[id] && raw.w < 0.45 && raw.h < 0.45 && tinyCount >= 4) continue; // Tool icon strips (4 or more under 0.45 inch) are omitted (the text box above extends over that area)
      if (skipImage.has(raw)) continue; // Illustration spot right of a table (absorbed by widening the table)
      if (!sl[id] && raw.w < T.PANEL.ICON_MAX && raw.h < T.PANEL.ICON_MAX) { // Judged on source coordinates (same result when the page size shrinks)
        // A text box covered by the icon shrinks to the icon's left edge to prevent overlap
        ownSlide.atoms.forEach((o) => {
          if (!o.paras || o.kind === "table") return;
          const overlapX = Math.min(o.x + o.w, raw.x + raw.w) - Math.max(o.x, raw.x);
          const overlapY = Math.min(o.y + o.h, raw.y + raw.h) - Math.max(o.y, raw.y);
          if (overlapX > 0.05 && overlapY > 0.05 && o.x < raw.x - 0.2) o.w = +(raw.x - 0.08 - o.x).toFixed(3);
        }); // Icon images are replaced with shape compositions whose kind comes from nearby label keywords
        const near = ownSlide.atoms.filter((o) => o.paras && Math.abs(o.x + o.w / 2 - raw.x - raw.w / 2) < 3.2 && Math.abs(o.y + o.h / 2 - raw.y - raw.h / 2) < 1.0).map((o) => o.paras.map((p) => p.runs.map((r) => r.t).join("")).join(" "));
        iconGlyph(pres, slide, atom, iconKind(raw, near));
        continue;
      }
      if (!sl[id] && raw.h < 0.7 && raw.w > 1.0) { // A single logo becomes [기관명], and a process example strip takes the ○○○ → ○○○ format
        const near = ownSlide.atoms.filter((o) => o.paras && o.y < raw.y && o.y > raw.y - 3.2 && Math.min(o.x + o.w, raw.x + raw.w) - Math.max(o.x, raw.x) > 0.3).map((o) => o.paras.map((p) => p.runs.map((r) => r.t).join("")).join(" ")).join(" ");
        const proc = /프로세스|절차|흐름|단계/.test(near);
        text(slide, atom, proc ? "접수 → 검토 → 승인 → 처리 → 통보" : "[기관명]", { sz: T.SIZE.tableDense, color: T.COLOR.textMuted, align: "center" });
        continue;
      }
      image(pres, slide, atom, sl[id], { label: atom.identity ? "로고" : "이미지" });
      continue;
    }
    if (atom.kind === "chart") {
      ck += 1;
      const id = "ch" + ck;
      ids.charts.push(id);
      const spec = sl[id] || atom.chart;
      chart(pres, slide, atom, { ...atom.chart, ...spec, categories: spec.categories && spec.categories.length ? spec.categories : ["항목 A", "항목 B", "항목 C"], series: spec.series && spec.series.length && spec.series[0].values.length ? spec.series : [{ name: "", values: [30, 45, 25] }] });
      if ((spec.type || atom.chart.type) === "doughnut") {
        // Cover the center with a white circle so the ring thickness holds even if the renderer ignores holeSize
        const hs = (spec.holeSize || atom.chart.holeSize || 75) / 100;
        const d = Math.min(atom.w, atom.h) * hs * T.METRIC.DONUT_PLOT;
        slide.addShape(pres.ShapeType.ellipse, { x: atom.x + atom.w / 2 - d / 2, y: atom.y + atom.h / 2 - d / 2, w: d, h: d, fill: { color: T.COLOR.white }, line: { color: "FFFFFF", width: 0, transparency: 100 } });
      }
      continue;
    }
    if (atom.kind === "table") {
      bk += 1;
      const id = "tb" + bk;
      const tb = JSON.parse(JSON.stringify(atom.table));
      if (sx !== 1) { tb.colw = tb.colw.map((v) => +(v * sx).toFixed(3)); tb.rowh = tb.rowh.map((v) => +(v * sy).toFixed(3)); }
      const newRight = widen[ownSlide.atoms.indexOf(raw)];
      if (newRight) { const k = (newRight - atom.x) / atom.w; tb.colw = tb.colw.map((v) => +(v * k).toFixed(3)); atom.w = +(newRight - atom.x).toFixed(3); }
      // When table slots fill only some rows, drop the empty rows and reduce the table height (staffing tables, etc.)
      const usedRows = new Set();
      Object.keys(sl).forEach((k) => { const m = k.match(new RegExp("^tb" + bk + "\\.r(\\d+)c\\d+$")); if (m && String(sl[k]).trim()) usedRows.add(+m[1]); });
      if (usedRows.size && tb.rows.length > 3) {
        const last = Math.max(...usedRows, 0);
        const anyRowSlot = Object.keys(sl).some((k) => new RegExp("^tb" + bk + "\\.r\\d+c\\d+$").test(k));
        if (anyRowSlot && last >= 1 && last < tb.rows.length - 1) {
          const drop = tb.rows.length - 1 - last;
          const cut = tb.rowh.slice(last + 1).reduce((a, b) => a + b, 0);
          tb.rows = tb.rows.slice(0, last + 1); tb.rowh = tb.rowh.slice(0, last + 1);
          atom.h = +(atom.h - cut).toFixed(3);
          if (drop) ids.dropped = (ids.dropped || 0) + drop;
        }
      }
      const newLeft = widenLeft[ownSlide.atoms.indexOf(raw)];
      if (newLeft != null) { const nw = atom.x + atom.w - newLeft; const k = nw / atom.w; tb.colw = tb.colw.map((v) => +(v * k).toFixed(3)); atom.x = +newLeft.toFixed(3); atom.w = +nw.toFixed(3); }
      tb.rows.forEach((r, i) => r.forEach((c, j) => {
        const key = `${id}.r${i}c${j}`;
        const cur = c.paras ? c.paras.map((p) => p.runs.map((x) => x.t).join("")).join("\n") : "";
        ids.tables.push({ id: key, text: cur });
        const byText = textKey(sl, cur);
        if (sl[key] != null) c.paras = substitute(c.paras, sl[key]);
        else if (byText != null) c.paras = substitute(c.paras, byText);
        else if (scrub(cur, sl.company) !== cur) c.paras = substitute(c.paras, scrub(cur, sl.company));
      }));
      table(slide, { ...atom, table: tb });
      continue;
    }
    if (atom.kind === "line") {
      if (skipShape.has(raw)) continue;
      const hit = (px, py) => skippedBoxes.find((b) => px >= b.x - 0.08 && px <= b.x + b.w + 0.08 && py >= b.y - 0.08 && py <= b.y + b.h + 0.9); // An omitted box and the connecting segment below it
      const p0 = [raw.flipH ? raw.x + raw.w : raw.x, raw.flipV ? raw.y + raw.h : raw.y];
      const p1 = [raw.flipH ? raw.x : raw.x + raw.w, raw.flipV ? raw.y : raw.y + raw.h];
      const b0 = hit(p0[0], p0[1]), b1 = hit(p1[0], p1[1]);
      if (b0 || b1) {
        // A connector leaving an omitted box moves its start to the last remaining box in the same column (keeps links between modules)
        const bx = b0 || b1;
        const survivors = ownSlide.atoms.filter((o) => o.paras && !skippedBoxes.includes(o) && o.y < bx.y && Math.min(o.x + o.w, bx.x + bx.w) - Math.max(o.x, bx.x) > bx.w * 0.5 && o.w < bx.w * 1.5);
        if (!survivors.length || (b0 && b1)) continue;
        if (raw.w < 0.15 && raw.h < 0.5) continue; // Short vertical arrows that led down into an omitted box are removed
        const last = survivors.sort((p, q) => (q.y + q.h) - (p.y + p.h))[0];
        const other = b0 ? p1 : p0;
        // If the other end is to the right (next module), start from the right middle of the last box, otherwise from its bottom middle
        const np = other[0] > last.x + last.w + 0.2 ? [last.x + last.w, last.y + last.h / 2] : [b0 ? p0[0] : p1[0], last.y + last.h + 0.02];
        const q0 = b0 ? np : p0, q1 = b1 ? np : p1;
        const a2 = { ...raw, x: Math.min(q0[0], q1[0]), y: Math.min(q0[1], q1[1]), w: Math.abs(q1[0] - q0[0]), h: Math.abs(q1[1] - q0[1]), flipH: q1[0] < q0[0], flipV: q1[1] < q0[1] };
        line(pres, slide, sc(a2)); continue;
      }
      line(pres, slide, atom); continue;
    }
    if (atom.kind === "shape" || atom.kind === "graphic") {
      if (skipShape.has(raw)) { if (raw.paras) tk += 1; continue; }
      if (grow[ownSlide.atoms.indexOf(raw)]) atom.h = +(grow[ownSlide.atoms.indexOf(raw)] * sy).toFixed(3);
      if (shrinkTo[ownSlide.atoms.indexOf(raw)]) {
        atom.h = +(shrinkTo[ownSlide.atoms.indexOf(raw)] * sy).toFixed(3);
        atom.va = "top"; // A shrunk box is top-aligned so overflow does not poke out above it
      }
      if (narrowTo[ownSlide.atoms.indexOf(raw)]) atom.w = +(narrowTo[ownSlide.atoms.indexOf(raw)] * sx).toFixed(3);
      let ov = {};
      if (fillBox.has(ownSlide.atoms.indexOf(raw))) ov.fillText = true;
      // Center text inside a donut chart shrinks to 85% so it does not overlap the ring
      const donut = raw.paras && ownSlide.atoms.find((c) => c.kind === "chart" && c.chart.type === "doughnut" && raw.x >= c.x && raw.x + raw.w <= c.x + c.w && raw.y >= c.y && raw.y + raw.h <= c.y + c.h);
      if (donut) { // Text inside the donut is placed in order by splitting the hole area vertically (prevents overlap)
        const inside = ownSlide.atoms.filter((o) => o.paras && o.x >= donut.x && o.x + o.w <= donut.x + donut.w && o.y >= donut.y && o.y + o.h <= donut.y + donut.h).sort((p, q) => p.y - q.y);
        const idx = Math.max(0, inside.indexOf(raw));
        const hole = Math.min(donut.w, donut.h) * 0.5;
        const cellH = hole / Math.max(inside.length, 1);
        atom.w = +(hole * sx).toFixed(3); atom.h = +(cellH * sy).toFixed(3);
        atom.x = +((donut.x + donut.w / 2) * sx - atom.w / 2).toFixed(3);
        atom.y = +(((donut.y + donut.h / 2) - hole / 2 + idx * cellH) * sy).toFixed(3);
        atom.mg = [0, 0, 0, 0]; atom.va = "middle";
        ov.scale = inside.length > 1 ? 0.55 : 0.65;
      }
      const company = sl.company || (ctx && ctx.meta && ctx.meta.company) || LB.label("common", "company");
      if (atom.paras) {
        tk += 1;
        const id = "t" + tk;
        const cur = atom.paras.map((p) => p.runs.map((x) => x.t).join("")).join("\n");
        ids.texts.push({ id, text: cur });
        const byText = textKey(sl, cur);
        const v = sl[id] != null ? sl[id] : byText;
        if (v === "") continue; // An empty string substitution omits the box itself (when there are fewer items than in the source)
        if (v != null) ov.paras = substitute(atom.paras, v);
        else if (scrub(cur, company) !== cur) ov.paras = substitute(atom.paras, scrub(cur, company));
      }
      // Original text only needs to absorb the font width difference, so its minimum is lower. Substituted text keeps the body minimum so fonts do not drift
      ov.minPt = ov.paras ? T.SIZE.BODY_MIN : T.SIZE.OWN_MIN;
      // When substituted text has more lines than the original, top-align it so it does not cover the elements above
      if (ov.paras && raw.paras) {
        // Account for the text area narrowed by an icon placed on the box
        const icon = ownSlide.atoms.find((im) => im.kind === "image" && im.x < raw.x + raw.w && im.x + im.w > raw.x && im.y < raw.y + raw.h && im.y + im.h > raw.y);
        const effW = icon ? Math.max(1, icon.x - raw.x - 0.1) : raw.w;
        const wrapW = effW - 0.3;
        const count = (ps) => ps.reduce((a, p) => {
          const t = p.runs.map((r) => r.t).join("");
          const sz = (p.runs[0] && p.runs[0].sz) || T.SIZE.body;
          return a + t.split("\n").reduce((b, seg) => b + Math.max(1, estimateLines(seg, wrapW - T.PARA.bulletIndentIn, sz)), 0);
        }, 0);
        const avgSz = ov.paras.reduce((a, p) => a + ((p.runs[0] && p.runs[0].sz) || T.SIZE.body), 0) / Math.max(ov.paras.length, 1);
        const need = count(ov.paras) * lineHeightIn(avgSz) + (ov.paras.length - 1) * 0.075;
        // Top-align when the line count grew or the box is 70% full or more (prevents upward overflow from renderer wrapping differences)
        // With room to spare, widen paragraph spacing to fill the box evenly (up to 10pt)
        if (ov.paras.length > 1 && need < raw.h * 0.8) {
          const slack = (raw.h - 0.12 - need) / (ov.paras.length - 1) * 72;
          const gap = Math.max(2.5, Math.min(10, slack * 0.8));
          ov.paras = ov.paras.map((p, i) => (i === 0 ? p : { ...p, spcBef: +gap.toFixed(1) }));
        }
        // If it looks likely to overflow the box, cut paragraph spacing first and keep the font
        if (need > raw.h - 0.08) {
          // Shrink only paragraph and line spacing (the font stays)
          ov.paras = ov.paras.map((p, i) => ({ ...p, spcBef: i === 0 ? p.spcBef : 2, lnSpc: Math.min(p.lnSpc || 1.25, 1.05) }));
          // If it still overflows after cutting spacing, keep the font and let a lint warning prompt shorter text
        }
      }
      if (atom.rot && atom.paras && /Illustrative|Sample|시안/i.test(atom.paras.map((p) => p.runs.map((r) => r.t).join("")).join(""))) {
        // Rotated tag: renderers draw tables on top, so a tag over a table moves to the top left outside the table with a white fill
        const tb = ownSlide.atoms.find((o) => o.kind === "table" && atom.x < o.x + o.w && atom.x + atom.w > o.x && atom.y < o.y + o.h && atom.y + atom.h > o.y);
        const a2 = { ...atom, fill: "FFFFFF", rot: 345 };
        if (tb) { a2.x = tb.x * sx + 0.05; a2.y = tb.y * sy - atom.h - 0.02; }
        shape(pres, slide, a2, ov);
        continue;
      }
      if (ov.paras || atom.paras) {
        const paras = ov.paras || atom.paras;
        ov.scale = ratioBySize[sizeKey(atom, paras)]; // Sibling boxes share a shrink ratio (lint warns about long slot text)
      }
      // One-line boxes side by side in the same row are centered vertically so their baselines line up even with different fonts
      if (!ov.va && raw.paras && raw.paras.length === 1) {
        const mate = ownSlide.atoms.some((b) => b !== raw && b.paras && b.paras.length === 1
          && Math.abs(b.y - raw.y) < 0.06 && Math.abs(b.h - raw.h) < 0.06 && Math.abs(b.x - raw.x) > 0.1);
        if (mate) ov.va = "middle";
      }
      shape(pres, slide, atom, ov); // Keep the source z-order (pushed back, white boxes would hide symbols and pictures)
    }
  }
  bigIcons.forEach((bi) => {
    const d = Math.min(bi.w, bi.h * (bi.caption ? 0.75 : 1));
    iconGlyph(pres, slide, { x: bi.x + (bi.w - d) / 2, y: bi.y, w: d, h: d }, bi.kind);
    if (bi.caption) text(slide, { x: bi.x, y: bi.y + d + 0.05, w: bi.w, h: 0.3 }, bi.caption, { sz: T.SIZE.body, bold: true, color: T.COLOR.navy, align: "center" });
  });
  chevronStrip.forEach((cs) => {
    const n = cs.labels.length, ov = 0.08, w = (cs.w + ov * (n - 1)) / n;
    cs.labels.forEach((lb, i) => slide.addText([{ text: lb, options: { fontSize: T.SIZE.tableDense, bold: true, color: T.COLOR.white, fontFace: T.FONT.regular } }], {
      x: cs.x + i * (w - ov), y: cs.y, w, h: cs.h, shape: i === 0 ? pres.ShapeType.homePlate : pres.ShapeType.chevron, fill: { color: T.COLOR.navy }, line: { color: "FFFFFF", width: 0.75 }, align: "center", valign: "middle", margin: 0, objectName: "adj:30000",
    }));
  });
  return ids;
}
// Replaces the company name token. Puts the meta.company value into __COMPANY__
// Other text stays as is, and text replacement rules apply only at the extraction step (own_extract.py)
function scrub(textValue, company) {
  return String(textValue).replace(/__COMPANY__/g, company || LB.label("common", "company"));
}
/** Replaces only the text while keeping the existing paragraph format. Line breaks split paragraphs. With too few paragraphs, the last paragraph format repeats */
function substitute(paras, value) {
  const lines = String(value).split("\n");
  const base = paras && paras.length ? paras : [{ runs: [{ t: "", sz: T.SIZE.body }] }];
  return lines.map((ln, i) => {
    const src = base[Math.min(i, base.length - 1)];
    const r0 = src.runs.find((r) => !r.br) || { sz: T.SIZE.body };
    // A ※ paragraph in the source is an example note position, so follow the writer's choice
    const srcText = src.runs.map((r) => r.t).join("").trim();
    if (/^※/.test(srcText) && ln.trim() && !/^\s*(※|\*|출처|자료|[Ss]ources?\s*[:：]|[Nn]otes?\s*[:：])/.test(ln) && !LB.isExtraNote(ln)) {
      // Text that is not a note takes the format of the bullet paragraph right above and reads as a normal item
      const prev = base.slice(0, Math.min(i, base.length - 1)).reverse().find((p) => p.bullet);
      if (prev) {
        const pr = prev.runs.find((r) => !r.br) || { sz: T.SIZE.body };
        return { ...prev, runs: [{ t: ln, sz: pr.sz, b: pr.b, color: pr.color }] };
      }
    }
    return { ...src, runs: [{ t: ln, sz: r0.sz, b: r0.b, color: r0.color }] };
  });
}

module.exports = { footnotes, scrub, remap, face, estimateLines, fitParas, lineHeightIn, lineWidthIn, wordWidthIn, textEm, runsOf, parasFromString, text, shape, line, table, chart, image, setImageBase, bodyBand, pageNo, markerGlyph, playOwn, substitute, lineOpt, mgPt, boxMargin, TEXT_MG_IN };
