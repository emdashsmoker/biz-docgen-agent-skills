"use strict";
// templates.js
// Slot templates. Called by the storyboard template name, they typeset slots (or panels, blocks) values in the body under the band.
// Coordinates are computed from the body area of tokens.scaled(layout) and rearranged by item count (modules 2-5, Tasks 2-6, columns 2-4, rows variable).
// With registered custom slides, the own:N template (atoms.playOwn) plays back source coordinates, and this file handles templates whose layout changes with the content.

const T = require("./tokens.js");
const A = require("./atoms.js");
const C = require("./composite.js");
const LB = require("./labels.js"); // Fixed label lookup (slide slot, then meta.labels, then assets/labels.json)

// Band mode and page number rules. band: full | noMarker | headerOnly | blank
const SPEC = {
  cover: { band: "blank" }, contents: { band: "blank" }, divider: { band: "blank" }, end: { band: "blank" },
  digest: { band: "full" }, free: { band: "full" }, purpose: { band: "full" }, scope: { band: "full" }, features: { band: "full" },
  strategy: { band: "full" }, process: { band: "full" }, module_overview: { band: "full" }, task: { band: "full" }, task_multi: { band: "full" },
  bullets: { band: "full" }, table: { band: "full" }, chart_text: { band: "full" }, chart_two: { band: "full" }, compare: { band: "full" },
  roadmap: { band: "full" }, gantt: { band: "full" }, org: { band: "full" }, staff_card: { band: "full" }, swot: { band: "full" },
  orgchart: { band: "full" }, cards: { band: "full" }, steps: { band: "full" }, illustrative: { band: "full" }, conclusion: { band: "full" },
  composite: { band: "full" },
};

// ---------------------------------------------------------------- Shared helpers
function body(ctx, sb) {
  const S = ctx.S;
  const top = sb.marker ? S.contentY : S.contentYNoMarker;
  // With a source line, the body ends above it, and footnotes raise it by their line count
  const nFoot = noteRows(sb);
  const bottom = sb.source || nFoot ? S.noteY - 0.12 - nFoot : S.contentBottom;
  const pad = T.BAND.BODY_PAD * S.sy;
  return { x: S.bodyX, y: top + pad, w: S.bodyW, h: bottom - top - pad };
}
function cols(box, n, gap) {
  const g = gap != null ? gap : T.PANEL.GAP;
  const w = (box.w - g * (n - 1)) / n;
  return Array.from({ length: n }, (_, i) => ({ x: box.x + i * (w + g), y: box.y, w, h: box.h }));
}
function rows(box, n, gap) {
  const g = gap != null ? gap : T.PANEL.GAP;
  const h = (box.h - g * (n - 1)) / n;
  return Array.from({ length: n }, (_, i) => ({ x: box.x, y: box.y + i * (h + g), w: box.w, h }));
}
function label(ctx, slide, box, text, opt) {
  // Navy label cell (table header, panel title)
  const o = opt || {};
  slide.addText(A.runsOf(A.parasFromString(text, { sz: o.sz || T.SIZE.panelHead, b: true, color: o.color || T.COLOR.white, align: "center" })), {
    x: box.x, y: box.y, w: box.w, h: box.h, shape: ctx.pres.ShapeType.rect, fill: { color: o.fill || T.COLOR.navy },
    line: { color: "FFFFFF", width: 0, transparency: 100 }, valign: "middle", margin: A.boxMargin([T.PANEL.LABEL_MG_X, T.PANEL.LABEL_MG_Y, T.PANEL.LABEL_MG_X, T.PANEL.LABEL_MG_Y]), isTextBox: true, autoFit: false,
  });
}
function frame(ctx, slide, box, opt) {
  const o = opt || {};
  slide.addShape(ctx.pres.ShapeType.rect, { x: box.x, y: box.y, w: box.w, h: box.h, fill: o.fill ? { color: o.fill } : { color: T.COLOR.white }, line: { color: o.line || T.COLOR.borderLight, width: o.pt || T.PANEL.LINE_PT } });
}
function subhead(ctx, slide, box, text) {
  // Unfilled area title: text + gray solid underline (one tier below a filled label)
  A.text(slide, { x: box.x, y: box.y, w: box.w, h: 0.34 }, text, { sz: T.SIZE.panelHead, color: T.COLOR.textDark, align: "center", mg: [0, 0, 0, 0] });
  slide.addShape(ctx.pres.ShapeType.line, { x: box.x, y: box.y + 0.36, w: box.w, h: 0, line: { color: T.COLOR.border, width: 0.5 } });
  return { x: box.x, y: box.y + T.PANEL.SUBHEAD_H, w: box.w, h: box.h - T.PANEL.SUBHEAD_H };
}
/** Computes one shared size so boxes of the same tier use the same font (fitted to the tightest box) */
function groupSize(boxes, itemsList, base) {
  const sz0 = base || T.SIZE.body;
  let best = sz0;
  boxes.forEach((box, i) => {
    const items = (itemsList[i] || []).filter(Boolean);
    if (!items.length || !box) return;
    const innerW = box.w - 2 * T.PANEL.INSET, innerH = box.h - 2 * T.PANEL.INSET;
    for (let sz = sz0; sz >= T.SIZE.BODY_MIN; sz--) {
      const h = items.reduce((acc, t) => {
        const txt = typeof t === "string" ? t : t.text;
        return acc + Math.max(1, A.estimateLines(txt, innerW - T.PARA.bulletIndentIn, sz)) * A.lineHeightIn(sz) + T.PARA.paraGapPt / 72;
      }, 0);
      if (h <= innerH) { best = Math.min(best, sz); return; }
      if (sz === T.SIZE.BODY_MIN) best = T.SIZE.BODY_MIN;
    }
  });
  return best;
}

const PP_LINE_RATIO = 1.4; // Approximate NanumGothic line height in PowerPoint (relative to font size). Higher than the rendering value 1.2
/** Paragraphs of a bullet list. Shared by bullets and bulletFitSize so both measure the same paragraphs */
function bulletParas(list, o, sz) {
  const paras = [];
  list.forEach((it) => {
    const tx = typeof it === "string" ? it : it.text;
    // A bullet marks item boundaries, so a box with one item gets no bullet even when it wraps onto two lines
    const single = !o.forceBullet && list.length === 1 && !(typeof it !== "string" && it.sub && it.sub.length);
    // Lines starting with ※ or 출처 are notes, so they get no bullet and show in small gray
    // To tell them from normal items such as "자료 수집", 출처 and 자료 count as notes only with a colon (English Source and Note follow the same rule)
    // Tokens added with meta.labels.notation.source ("token:") are notes too
    const isNote = /^\s*(※|출처\s*[:：]|자료\s*[:：]|[Ss]ources?\s*[:：]|[Nn]otes?\s*[:：])/.test(String(tx)) || LB.isExtraNote(tx);
    if (isNote) {
      paras.push({ bullet: false, indent: 0, marL: 0, align: "left", spcBef: o.gapPt || T.PARA.paraGapPt,
                   runs: [{ t: tx, sz: Math.max(T.SIZE.BODY_MIN, T.SIZE.note), color: T.COLOR.textMuted }] });
      return;
    }
    // In a numbered list the leading number (1-1. etc.) replaces the bullet, so no bullet is added (one number or symbol only)
    paras.push({ bullet: !single && !o.numbered, indent: T.PARA.bulletIndentIn, align: single ? (o.align || "center") : "left", spcBef: o.gapPt || T.PARA.paraGapPt, runs: [{ t: tx, sz, b: !!o.bold, color: o.color || T.COLOR.textDark }] });
    if (typeof it !== "string" && it.sub) it.sub.forEach((s) => paras.push({ bullet: true, lvl: 1, buChar: "-", indent: T.PARA.bulletIndentIn, align: "left", runs: [{ t: s, sz: o.subSz || Math.max(T.SIZE.BODY_MIN, sz - 1), color: T.COLOR.textGray }] }));
  });
  return paras;
}
/** Bullet font size fitted to a box. To give several boxes of one level a common size, use the smallest of the per-box values */
function bulletFitSize(box, items, opt) {
  const o = opt || {};
  const sz = o.sz || T.SIZE.body;
  const list = Array.isArray(items) ? items : [items];
  const fitted = A.fitParas(bulletParas(list, o, sz), box.w - 2 * T.PANEL.INSET, box.h - 2 * T.PANEL.INSET, T.SIZE.BODY_MIN);
  const first = fitted.find((p) => p.bullet && !p.lvl) || fitted[0];
  return first ? first.runs[0].sz : sz;
}
/** Total height of bullet paragraphs (ratio is the line height multiple, the rendering value when omitted) */
function bulletParasH(ps, innerW, ratio) {
  return ps.reduce((h, p) => h + A.estimateLines(p.runs[0].t, innerW - T.PARA.bulletIndentIn, p.runs[0].sz, p.runs[0].b) * A.lineHeightIn(p.runs[0].sz, ratio) + (p.spcBef || 0) / 72, 0);
}
/** Bullet paragraphs fitted to the box and the inner box size. Shared by bullets and bulletGap so both measure spacing on the same paragraphs */
function fitBullets(box, items, o) {
  const list = Array.isArray(items) ? items : [items];
  const innerW = box.w - 2 * T.PANEL.INSET, innerH = box.h - 2 * T.PANEL.INSET;
  return { list, innerW, innerH, fitted: A.fitParas(bulletParas(list, o, o.sz || T.SIZE.body), innerW, innerH, T.SIZE.BODY_MIN) };
}
/** Spacing (pt) added between paragraphs by splitting the spare height
 *  The height is measured in PowerPoint line height (PP_LINE_RATIO) so taller lines in PowerPoint still stay inside the box */
function slackGapPt(fitted, innerW, innerH) {
  const slack = innerH - bulletParasH(fitted, innerW, PP_LINE_RATIO);
  return Math.min(T.PARA.paraGapMaxPt, Math.max(0, (slack * 72) / (fitted.length + 1)));
}
/** Bullet paragraph spacing (pt) of one box on its own = base spacing + share of the spare height. null with one paragraph or fewer (no gap to split) */
function bulletGap(box, items, opt) {
  const o = opt || {};
  const { fitted, innerW, innerH } = fitBullets(box, items, o);
  return fitted.length > 1 ? (o.gapPt || T.PARA.paraGapPt) + slackGapPt(fitted, innerW, innerH) : null;
}
/** Shared paragraph spacing of a group of sibling boxes on the same tier (the smallest per-box spacing)
 *  Splitting spare height per box makes neighboring boxes disagree, so the group uses one spacing. It follows the tightest box, so no box gets taller
 *  opt is the option passed to bullets (an array in boxes order when it differs per box). Empty slots are null boxes. undefined when no box has two or more paragraphs */
function groupGap(boxes, itemsList, opt) {
  const gaps = boxes.map((box, i) => (box ? bulletGap(box, itemsList[i] || [], Array.isArray(opt) ? opt[i] : opt) : null)).filter((g) => g != null);
  return gaps.length ? Math.min(...gaps) : undefined;
}
/** Bullet list. items: string | {text, sub:[]}. With opt.groupGapPt the value is used as paragraph spacing instead of splitting the spare height (groupGap result) */
function bullets(ctx, slide, box, items, opt) {
  const o = opt || {};
  const { list, innerW, innerH, fitted: fit0 } = fitBullets(box, items, o);
  let fitted = fit0;
  // Spare height goes only to item spacing. The font keeps the tier size so it matches neighboring boxes
  // A group of sibling boxes receives the shared spacing and sets body paragraph spacing to it (sub items get only the part above the base spacing)
  if (fitted.length > 1) {
    const base = o.gapPt || T.PARA.paraGapPt;
    const extra = o.groupGapPt != null ? o.groupGapPt - base : slackGapPt(fitted, innerW, innerH);
    fitted = fitted.map((p) => ({ ...p, spcBef: Math.max(0, (p.spcBef || 0) + extra) }));
  }
  const used = bulletParasH(fitted, innerW);
  if (used < box.h * (1 - T.PANEL.SLACK_WARN) && list.length > 1 && !o.noWarn) ctx.warn(`empty space ${Math.round((1 - used / box.h) * 100)}% (${list.length} bullets, box ${box.h.toFixed(2)}in)`);
  // Horizontal fill: average share of bullet item lines in the inner box width (only short items leave the right side empty)
  const bl = fitted.filter((p) => p.bullet && !p.lvl);
  const placeholder = bl.some((p) => /\[[^\]]+\]/.test(p.runs[0].t));
  if (bl.length > 1 && !placeholder) {
    const aw = innerW - T.PARA.bulletIndentIn;
    const hfill = bl.reduce((a, p) => a + Math.min(1, A.lineWidthIn(p.runs[0].t, p.runs[0].sz, p.runs[0].b) / aw), 0) / bl.length;
    const hmax = Math.max(...bl.map((p) => Math.min(1, A.lineWidthIn(p.runs[0].t, p.runs[0].sz, p.runs[0].b) / aw)));
    if ((hfill < T.LIMIT.boxTextFillMin || hmax < T.LIMIT.boxTextMaxFillMin) && globalThis.process.env.HFILL_DUMP) globalThis.process.stderr.write(`DUMP ${JSON.stringify({ id: ctx.sb.id, aw: +aw.toFixed(2), sz: bl[0].runs[0].sz, items: bl.map((p) => p.runs[0].t) })}\n`);
    if (hfill < T.LIMIT.boxTextFillMin || hmax < T.LIMIT.boxTextMaxFillMin) ctx.warn(`box text fill average ${Math.round(hfill * 100)}%, longest ${Math.round(hmax * 100)}% ('${bl[0].runs[0].t.slice(0, 12)}' and ${bl.length - 1} more items, enrich the text or narrow the cell)`);
  }
  slide.addText(A.runsOf(fitted), { x: box.x, y: box.y, w: box.w, h: box.h, isTextBox: true, valign: o.valign || "middle", margin: A.boxMargin([T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET]), fill: o.fill ? { color: o.fill } : undefined, line: o.line ? { color: o.line, width: T.PANEL.LINE_PT } : undefined, autoFit: false });
}
/** Panel body box (below the label bar) */
function panelBody(box, p) {
  const headH = p.head ? T.PANEL.TITLE_H : 0;
  return { x: box.x, y: box.y + headH, w: box.w, h: box.h - headH };
}
/** Panel: label bar + bordered body + bullets */
function panel(ctx, slide, box, p) {
  if (p.head) label(ctx, slide, { x: box.x, y: box.y, w: box.w, h: T.PANEL.TITLE_H }, p.head, { fill: p.headFill });
  const bd = panelBody(box, p);
  frame(ctx, slide, bd, { fill: p.fill });
  if (p.items) bullets(ctx, slide, bd, p.items, { noWarn: p.noWarn, sz: p.sz, subSz: p.subSz, groupGapPt: p.groupGapPt });
  else if (p.text) A.text(slide, bd, p.text, { sz: T.SIZE.body, align: "center" });
  return bd;
}
/** Shared paragraph spacing of side-by-side panels. ps holds the values passed to panel in boxes order (null for empty slots) */
function panelsGap(boxes, ps) {
  const has = (p) => !!(p && p.items);
  return groupGap(boxes.map((b, i) => (has(ps[i]) ? panelBody(b, ps[i]) : null)), ps.map((p) => (has(p) ? p.items : [])), ps.map((p) => ({ sz: p && p.sz, subSz: p && p.subSz })));
}
/** Table. head[], rows[][], colW (ratios, automatic if omitted), align[] */
// Table cell value checks. Items in a cell are separated by array elements or line breaks
const HARVEY = { "●": "full", "◐": "half", "○": "none" };
const cellItems = (v) => (Array.isArray(v) ? v : v && Array.isArray(v.items) ? v.items : null);
// Numeric cell values (e.g. headcount 36) are typeset as strings
const cellText = (v) => (typeof v === "string" ? v : typeof v === "number" ? String(v) : v && !Array.isArray(v) && v.text != null ? String(v.text) : "");
const isHarvey = (v) => typeof v === "string" && !!HARVEY[v.trim()];
/** Cell item list (each array element and each line-break piece is 1 item. Empty items excluded) */
const cellList = (v) => (v && v.merged ? [] : (cellItems(v) || [cellText(v)]).flatMap((t) => String(t == null ? "" : t).split("\n")).map((t) => t.trim()).filter(Boolean));
const cellBold = (v) => !!(v && typeof v === "object" && !Array.isArray(v) && v.bold);
const cellSpan = (v) => (v && v.colspan) || 1;
const TABLE_CELL_PAD = T.PANEL.CELL_MG[0]; // Left and right table cell inset
const TABLE_CELL_VPAD = T.PANEL.CELL_MG[1] + T.PANEL.CELL_MG[3]; // Sum of top and bottom table cell insets
const TABLE_HEAD_PAD = 0.12; // Sum of left and right header cell insets
const TABLE_COL_MIN = 0.5; // Minimum column width (one-symbol columns and Harvey ball columns)
const TABLE_BODY_GROUP_MIN = 3; // Minimum column count of a data column group that receives spare width (groups forming the table body, such as role codes, years, alternatives)
const ROW_BREATH = 0.12; // Top and bottom room left after widening line spacing in multi-line cell rows
const QUESTION_END = /(는가|인가|은가|한가|던가|을까|할까|는지|\?)\s*$/; // Question sentence endings (diagnostic question columns are left-aligned)
const DATA_CELL_MAX_CHARS = 2; // Columns holding only symbols of two characters or less, like role codes, are data columns (number and Harvey ball columns included)
const LNSPC_MAX = 1.3; // Line spacing cap for multi-line cells (when row height remains)
// Width factors for the edge zone check. When text sits at 99-100% of the cell width, rendering error (up to 0.65% wider than calculated at 11pt)
// splits estimated and rendered line counts, causing ghost lines (only one-line rows grow taller) or row growth. Stable when line counts agree at -3% and +3% cell width
const EDGE_FACTORS = [0.97, 1.03];
const EDGE_STEP = 0.005; // Width unit moved between columns by edge avoidance (inches)
const EDGE_PASSES = 3; // Maximum rechecks for other columns entering the edge zone after the width freed by a narrowed column is shared
const sumOf = (a) => a.reduce((x, y) => x + y, 0);
/** Text list per column [{t, b, pad}]. pad is the margin subtracted from the column width (TABLE_HEAD_PAD for head cells; side margins and bullet indent for body cells. Same basis as tableMetrics) */
function colTexts(tb, ncol, listCols) {
  const out = Array.from({ length: ncol }, () => []);
  (tb.head || []).forEach((h, i) => { if (i < ncol) out[i].push({ t: String(h), b: true, pad: TABLE_HEAD_PAD }); });
  tb.rows.forEach((r) => r.forEach((c, i) => {
    if (i >= ncol || cellSpan(c) > 1) return;
    const pad = 2 * TABLE_CELL_PAD + (listCols[i] ? T.PARA.bulletIndentIn : 0);
    cellList(c).forEach((t) => out[i].push({ t, b: cellBold(c), pad }));
  }));
  return out;
}
const linesAt = (xs, w, f, sz) => xs.map((x) => A.estimateLines(x.t, Math.max(0.3, w - x.pad) * f, sz, x.b));
const sameLines = (a, b) => a.every((n, k) => n === b[k]);
/** Whether line counts differ between the two width factors (edge zone) */
const isEdgeCol = (xs, w, sz) => !sameLines(linesAt(xs, w, EDGE_FACTORS[0], sz), linesAt(xs, w, EDGE_FACTORS[1], sz));
// Avoiding line breaks inside a word. A column where the renderer splits a word caught at the line end, as in '○○|억원' or '(기|업)' (same computed width as the check_layout warning),
// moves to a width where that word fits on the upper line or moves whole to the next line
// Why: of 117 rendered breaks inside a word in the A4, 10.83 and 4:3 sample renders, 36 are in table cells. 9 remain after this avoidance, all at check_layout warning positions
//      The rendered/computed width ratio is 0.990 at the 1st percentile and 1.007 at most over both samples and four page sizes, so a column that had a split moves to a width with no split at ±1% of the computed width
//      Avoiding splits only at the computed width leaves 16 (15 without a warning) through rendering error; avoiding them at ±3% (edge zone factors) leaves 20 for lack of width to move. 16:9 samples have no splitting column, so their widths stay as they were
const SPLIT_BAND = 0.01;
// Growth cap (ratio) for the other columns that receive the freed width when a column narrows to avoid a break inside a word
// Why: in the narrow sample page sizes, 13 of 14 such narrowings widen the other columns by 0.7-16%. The one that widens a short label column by 85% in a two-column table unbalances the table, so it does not narrow
const SPLIT_GROW_MAX = 0.25;
const hasSplit = (xs, w, sz, f) => xs.some((x) => A.wordSplits(x.t, Math.max(0.3, w - x.pad) * (f || 1), sz, x.b).length > 0);
const hasNearSplit = (xs, w, sz) => [1, 1 - SPLIT_BAND, 1 + SPLIT_BAND].some((f) => hasSplit(xs, w, sz, f));
/** Edge and in-word break avoidance. Such a column takes width in EDGE_STEP units from other columns whose line counts do not change and that gain no break inside a word
 *  When not enough width can be taken, the column narrows until its line count is settled and no word is split, and the freed width goes to the other columns in proportion to their widths
 *  When no width avoids the break inside a word, only the edge zone is avoided
 *  Equal-width data column groups are not widened, and when giving width every column in the group gives the same amount (keeps equal widths within the group)
 *  Modifies cw in place */
function settleEdgeCols(cw, texts, sz, minW, grouped) {
  const inGroup = new Set(grouped.flat());
  const units = [...grouped, ...cw.map((_, j) => [j]).filter(([j]) => !inGroup.has(j))];
  const wasSplit = new Set(); // Columns that had a break inside a word (kept free of splits at ±SPLIT_BAND of the computed width too)
  const splitAt = (j, w) => (wasSplit.has(j) ? hasNearSplit(texts[j], w, sz) : hasSplit(texts[j], w, sz));
  const unsettled = (j, w) => isEdgeCol(texts[j], w, sz) || splitAt(j, w);
  const steady = (j, w) => EDGE_FACTORS.every((f) => sameLines(linesAt(texts[j], cw[j], f, sz), linesAt(texts[j], w, f, sz))) && !splitAt(j, w);
  const canGive = (u) => u.every((j) => cw[j] - EDGE_STEP >= minW[j] && !unsettled(j, cw[j]) && steady(j, cw[j] - EDGE_STEP));
  /** Moves column i to a width that is not bad. Returns false and leaves cw unchanged when it cannot */
  const move = (i, bad, growMax) => {
    const before = cw.slice();
    while (bad(cw[i])) {
      // Take from the widest column (group) that can give
      const donors = units.filter((u) => !u.includes(i) && canGive(u));
      if (!donors.length) break;
      const widest = donors.reduce((a, b) => (Math.min(...b.map((j) => cw[j])) > Math.min(...a.map((j) => cw[j])) ? b : a));
      widest.forEach((j) => { cw[j] -= EDGE_STEP; cw[i] += EDGE_STEP; });
    }
    if (!bad(cw[i])) return true;
    before.forEach((v, j) => { cw[j] = v; });
    const rest = sumOf(cw) - cw[i];
    let w = cw[i];
    while (w - EDGE_STEP >= minW[i] && bad(w) && (cw[i] - w + EDGE_STEP) / rest <= growMax) w -= EDGE_STEP;
    if (bad(w)) return false; // Keep the original width if the counts still differ or a word is still split at the minimum
    const freed = cw[i] - w;
    cw.forEach((v, j) => { if (j !== i) cw[j] += (freed * v) / rest; });
    cw[i] = w;
    return true;
  };
  for (let pass = 0; pass < EDGE_PASSES; pass++) {
    let changed = false;
    for (let i = 0; i < cw.length; i++) {
      if (inGroup.has(i) || !texts[i].length) continue;
      if (hasSplit(texts[i], cw[i], sz)) wasSplit.add(i);
      if (!unsettled(i, cw[i])) continue;
      changed = true;
      if (!wasSplit.has(i)) move(i, (w) => isEdgeCol(texts[i], w, sz), Infinity);
      else if (!move(i, (w) => unsettled(i, w), SPLIT_GROW_MAX)) move(i, (w) => isEdgeCol(texts[i], w, sz), Infinity);
    }
    if (!changed) break;
  }
}
/** Column widths (inches). Allocated from each column's one-line width (nat) and widest word (min)
 *  If all columns fit on one line, spare width is split in proportion to one-line widths. Otherwise word widths are guaranteed and the rest is split in proportion to the shortfall up to one-line width */
function tableColW(tb, w, sz, listCols, dataCols) {
  // dataCols[i]: data column kind string (harvey, num, code) or an empty string
  const ncol = listCols.length;
  const nat = Array(ncol).fill(TABLE_COL_MIN), min = Array(ncol).fill(TABLE_COL_MIN);
  const words = (t, b) => Math.max(0, ...String(t).split(" ").map((x) => A.lineWidthIn(x, sz, b)));
  (tb.head || []).forEach((h, i) => {
    nat[i] = Math.max(nat[i], A.lineWidthIn(String(h), sz, true) + TABLE_HEAD_PAD);
    min[i] = Math.max(min[i], words(h, true) + TABLE_HEAD_PAD);
  });
  tb.rows.forEach((r) => r.forEach((c, i) => {
    if (i >= ncol || cellSpan(c) > 1) return;
    const pad = 2 * TABLE_CELL_PAD + (listCols[i] ? T.PARA.bulletIndentIn : 0);
    cellList(c).forEach((t) => {
      nat[i] = Math.max(nat[i], A.lineWidthIn(t, sz, cellBold(c)) + pad);
      min[i] = Math.max(min[i], words(t, cellBold(c)) + pad);
    });
  }));
  const sN = sumOf(nat);
  // Data column group: a run of 2 or more data columns of the same kind (numbers, Harvey balls, symbols of two characters or less) (role codes, figures per year, evaluations per alternative)
  const groups = [];
  for (let i = 0; i < ncol; i++) {
    if (!dataCols || !dataCols[i]) continue;
    const last = groups[groups.length - 1];
    if (last && last[last.length - 1] === i - 1 && dataCols[i - 1] === dataCols[i]) last.push(i); else groups.push([i]);
  }
  const grouped = groups.filter((g) => g.length > 1);
  // Only groups of 3 or more columns forming the table body receive spare width (so 2-column symbol groups such as number and type do not take it)
  const inGroup = new Set(grouped.filter((g) => g.length >= TABLE_BODY_GROUP_MIN).flat());
  // With spare width, give it only to a data column group of 3 or more if one exists, otherwise to all columns in proportion to one-line widths (text columns fit their text)
  // When short, shrink the widest columns first to one width C so short columns stay on one line (word widths guaranteed)
  const capAt = (C) => nat.map((n, i) => Math.min(n, Math.max(C, min[i])));
  let cw;
  if (sN <= w) {
    const recv = inGroup.size ? [...inGroup] : nat.map((_, i) => i);
    const rSum = sumOf(recv.map((i) => nat[i]));
    cw = nat.slice();
    recv.forEach((i) => { cw[i] = nat[i] + ((w - sN) * nat[i]) / rSum; });
  } else if (sumOf(capAt(0)) >= w) cw = capAt(0).map((m, _, a) => (m * w) / sumOf(a));
  else {
    let lo = 0, hi = Math.max(...nat);
    for (let it = 0; it < 40; it++) { const mid = (lo + hi) / 2; if (sumOf(capAt(mid)) > w) hi = mid; else lo = mid; }
    cw = capAt(lo);
  }
  // Columns in a group get the same width (repeat after excluding columns whose one-line width exceeds the average)
  grouped.forEach((g) => {
    let pool = g.slice();
    for (let it = 0; it < g.length; it++) {
      const avg = sumOf(pool.map((i) => cw[i])) / pool.length;
      if (!pool.some((i) => nat[i] > avg + 1e-6)) { pool.forEach((i) => { cw[i] = avg; }); break; }
      pool = pool.filter((i) => nat[i] <= avg + 1e-6);
      if (pool.length < 2) break;
    }
  });
  settleEdgeCols(cw, colTexts(tb, ncol, listCols), sz, min, grouped);
  const out = cw.map((v) => +v.toFixed(3));
  out[ncol - 1] = +(w - sumOf(out.slice(0, -1))).toFixed(3);
  return { cw: out, fill: sN / w };
}
/** Table column widths, column formats, needed height and cap per row
 *  Column format: columns with a cell of 2 or more items get bullets and left alignment in every cell, question sentence columns are left-aligned, other columns are centered (a column with a storyboard align uses that alignment)
 *  Row height cap: ROW_H_TEXT for text-only single-line rows, the widened spacing for multi-line rows, ROW_H_MAX for tables with Harvey balls */
function tableMetrics(tb, w, szOpt) {
  const ncol = tb.head ? tb.head.length : tb.rows[0].length;
  const sz = szOpt || (tb.rows.length > 10 ? T.SIZE.tableDense : T.SIZE.tableBody);
  const lh = A.lineHeightIn(sz, T.METRIC.TABLE_LINE_HEIGHT);
  const fixed = tb.colW && tb.colW.length === ncol;
  const colOf = (i) => tb.rows.map((r) => r[i]).filter((c) => c != null && cellSpan(c) === 1 && !c.merged);
  const listCols = Array.from({ length: ncol }, (_, i) => colOf(i).some((c) => cellList(c).length > 1));
  const isNum = (t) => /^[\d.,%+\-~ ]+$/.test(t);
  const textsOf = (i) => colOf(i).map((c) => cellList(c).join(" ")).filter(Boolean);
  // Data column kinds: Harvey balls, numbers, symbols of two characters or less (other columns are text columns)
  const kindOf = (ts) => (!ts.length ? "" : ts.every(isHarvey) ? "harvey" : ts.every(isNum) ? "num" : ts.every((t) => t.length <= DATA_CELL_MAX_CHARS) ? "code" : "");
  const dataCols = listCols.map((l, i) => (l ? "" : kindOf(textsOf(i))));
  const colw = fixed ? tb.colW.map((r) => +((w * r) / sumOf(tb.colW)).toFixed(3)) : tableColW(tb, w, sz, listCols, dataCols).cw;
  const innerOf = (cw, i, span) => Math.max(0.3, sumOf(cw.slice(i, i + span)) - 2 * TABLE_CELL_PAD - (listCols[i] ? T.PARA.bulletIndentIn : 0));
  // Column alignment takes the storyboard align first. Missing columns use the default alignment
  // Why: the shape of cell text cannot separate quantities (85.5백만원, 9개월) from identifiers (year 2005, serial 1). The author, who knows what a column means, sets right alignment for quantity columns
  // Default alignment: columns with cells of 2 or more items and question sentence columns are left-aligned, other columns (one-line text, numbers, Harvey balls, symbols) are centered
  const aligns = listCols.map((l, i) => (tb.align && tb.align[i]) || (l || textsOf(i).some((t) => QUESTION_END.test(t)) ? "left" : "center"));
  const linesOf = (v, i) => {
    if (v && v.merged) return 1;
    const inner = innerOf(colw, i, cellSpan(v));
    return Math.max(1, sumOf(cellList(v).map((t) => Math.max(1, A.estimateLines(t, inner, sz, cellBold(v))))));
  };
  const lines = tb.rows.map((r) => Math.max(1, ...r.map((c, i) => (c && c.rowspan > 1 ? 1 : linesOf(c, i)))));
  const visual = tb.rows.some((r) => r.some((c) => isHarvey(c)));
  const need = lines.map((n) => Math.max(T.PANEL.ROW_H_MIN, n * lh + TABLE_CELL_VPAD));
  const cap = lines.map((n, i) => Math.max(need[i], visual ? T.PANEL.ROW_H_MAX : n > 1 ? Math.min(T.PANEL.ROW_H_MAX, n * lh * LNSPC_MAX + TABLE_CELL_VPAD + ROW_BREATH) : Math.max(T.PANEL.ROW_H_TEXT, lh + TABLE_CELL_VPAD)));
  const headH = tb.head ? Math.max(T.PANEL.TABLE_HEAD_H, ...tb.head.map((x, i) => A.estimateLines(String(x), Math.max(0.3, colw[i] - TABLE_HEAD_PAD), sz, true) * A.lineHeightIn(sz) + 0.14)) : 0;
  // Text fill: share of the per-column one-line width sum in the table width (tables with placeholder cells are excluded because real values are not in yet)
  const placeholder = tb.rows.some((r) => r.some((c) => /^\[[^\]]+\]$/.test(cellText(c).trim())));
  const fill = placeholder ? 1 : tableColW(tb, w, sz, listCols, dataCols).fill;
  return { ncol, colw, sz, lh, lines, need, cap, headH, visual, listCols, aligns, linesOf, fill };
}
/** Row heights within height h. Needed heights come first, and spare height fills the lowest rows first toward equal height up to the caps */
function tableLayout(tb, w, h, szOpt) {
  const M = tableMetrics(tb, w, szOpt);
  const avail = Math.max(0.1, h - M.headH);
  const nSum = M.need.reduce((a, b) => a + b, 0);
  let rows;
  if (avail <= nSum) rows = M.need.map((v) => (v * avail) / nSum);
  else {
    // _fill fills up to the available height past the row height cap to align ends with neighboring cells (composite sets it only when the shortfall is small)
    const target = tb._fill ? avail : Math.min(avail, M.cap.reduce((a, b) => a + b, 0));
    const fill = (lv) => M.need.map((v, i) => Math.min(M.cap[i], Math.max(v, lv)));
    let lo = 0, hi = T.PANEL.ROW_H_MAX * 4;
    for (let it = 0; it < 40; it++) { const mid = (lo + hi) / 2; if (fill(mid).reduce((a, b) => a + b, 0) > target) hi = mid; else lo = mid; }
    rows = fill(lo);
    const short = target - rows.reduce((a, b) => a + b, 0);
    if (tb._fill && short > 0.001) rows = rows.map((v) => v + short / rows.length);
  }
  return { ...M, rows, total: M.headH + rows.reduce((a, b) => a + b, 0) };
}
function tableBlock(ctx, slide, box, tb, opt) {
  const o = opt || {};
  const L = tableLayout(tb, box.w, box.h, o.sz);
  const { colw, sz, headH, lh, listCols, aligns } = L;
  if (L.fill < T.LIMIT.tableFillMin && !o.noWarn) ctx.warn(`table text fill ${Math.round(L.fill * 100)}% (enrich cell text, add columns or narrow the cell)`);
  if (tb.align && tb.align.length !== L.ncol) ctx.warn(`table align has ${tb.align.length} entries for ${L.ncol} columns (match the column count. Missing columns use the default alignment)`);
  const hts = tb.head ? [headH, ...L.rows] : L.rows.slice();
  const rowHt = (ri) => hts[ri];
  const rowY = (ri) => hts.slice(0, ri).reduce((a, b) => a + b, 0);
  const colX = (ci) => box.x + colw.slice(0, ci).reduce((a, w2) => a + w2, 0);
  const mk = (txt, i, head) => {
    const at = txt && typeof txt === "object" && !Array.isArray(txt) ? txt : {};
    const runOf = (t) => ({ t: String(t), sz, b: head || !!at.bold, color: head ? T.COLOR.white : T.COLOR.textDark });
    const items = head ? [String(txt)] : cellList(txt);
    // Only cells with 2 or more items get a bullet per item (marks item boundaries). Single-item cells in the same column follow the column alignment (left) without bullets
    const paras = !head && items.length > 1
      ? items.map((t) => ({ align: "left", bullet: true, indent: T.PARA.bulletIndentIn, runs: [runOf(t)] }))
      : [{ align: head ? "center" : aligns[i], runs: [runOf(items.join(" "))] }];
    return { fill: head ? T.COLOR.navy : at.fill || undefined, paras, colspan: at.colspan, rowspan: at.rowspan, merged: at.merged };
  };
  const rowsOut = [];
  if (tb.head) rowsOut.push(tb.head.map((h, i) => mk(h, i, true)));
  tb.rows.forEach((r) => rowsOut.push(r.map((c, i) => mk(c, i, false))));
  // Multi-line cells widen line spacing as far as the row height allows, spreading the cell's spare space between lines
  tb.rows.forEach((r, ri) => r.forEach((c, ci) => {
    const cell = rowsOut[ri + (tb.head ? 1 : 0)][ci];
    if (!cell || c && c.merged) return;
    const lines = L.linesOf(c, ci);
    if (lines < 2) return;
    const spc = Math.min(LNSPC_MAX, (L.rows[ri] - TABLE_CELL_VPAD - ROW_BREATH) / (lines * lh));
    if (spc > 1.05) cell.paras = cell.paras.map((p) => ({ ...p, lnSpc: +spc.toFixed(2) }));
  }));
  // Harvey balls: ● ◐ ○ cells are emptied of text and drawn as circle shapes at the cell center
  const balls = [];
  rowsOut.forEach((row, ri) => row.forEach((cell, ci) => {
    if (ri === 0 && tb.head) return;
    const t = cell.paras[0].runs[0].t.trim();
    const cy = box.y + rowY(ri) + rowHt(ri) / 2;
    if (HARVEY[t]) { cell.paras[0].runs[0].t = ""; balls.push({ kind: HARVEY[t], cx: colX(ci) + colw[ci] / 2, cy }); }
  }));
  const rowh = rowsOut.map((_, ri) => +rowHt(ri).toFixed(3));
  const totalH = rowh.reduce((a, v) => a + v, 0);
  A.table(slide, { x: box.x, y: box.y, w: box.w, h: totalH, table: { colw, rowh, rows: rowsOut } }, { sz });
  const d = Math.min(0.2, Math.min(...L.rows) * 0.5);
  balls.forEach((bl) => {
    const bx = { x: bl.cx - d / 2, y: bl.cy - d / 2, w: d, h: d };
    // Use the body text color so the balls do not stand out in the table
    const ink = T.COLOR.textDark;
    if (bl.kind === "full") slide.addShape(ctx.pres.ShapeType.ellipse, { ...bx, fill: { color: ink }, line: { color: ink, width: 0.75 } });
    else if (bl.kind === "none") slide.addShape(ctx.pres.ShapeType.ellipse, { ...bx, fill: { color: T.COLOR.white }, line: { color: ink, width: 0.75 } });
    else {
      slide.addShape(ctx.pres.ShapeType.ellipse, { ...bx, fill: { color: T.COLOR.white }, line: { color: ink, width: 0.75 } });
      slide.addShape(ctx.pres.ShapeType.pie, { ...bx, fill: { color: ink }, line: { color: ink, width: 0.75 }, angleRange: [90, 270] });
    }
  });
  return totalH;
}
/** Cell width and tip width of a chevron row. With the default adj 50000, the tip width is half the short side */
function chevronGeom(box, n, h) {
  const ov = T.PANEL.CHEVRON_OVERLAP;
  const w = (box.w + ov * (n - 1)) / n;
  return { ov, w, pointW: 0.5 * Math.min(w, h || box.h) };
}
/** Box columns under chevrons. The box left edge meets the chevron tail corner, and the right edge meets the shoulder where the tip starts to narrow */
function chevronCols(chev, n, y, h) {
  const g = chevronGeom(chev, n, chev.h);
  return Array.from({ length: n }, (_, i) => ({ x: chev.x + i * (g.w - g.ov), y, w: g.w - g.pointW, h }));
}
/** Chevron row. steps: string[] or {title, sub}[] */
function chevronRow(ctx, slide, box, steps, opt) {
  const o = opt || {};
  const n = steps.length;
  const { ov, w } = chevronGeom(box, n, o.h || box.h);
  steps.forEach((s, i) => {
    const title = typeof s === "string" ? s : s.title;
    const st = i === 0 && !o.allChevron ? ctx.pres.ShapeType.homePlate : ctx.pres.ShapeType.chevron;
    const h = o.h || box.h;
    const pointW = chevronGeom(box, n, h).pointW;
    const innerW = w - (st === ctx.pres.ShapeType.chevron ? 1.0 * pointW : 0.5 * pointW) - 0.1;
    const paras = A.fitParas(A.parasFromString(title, { sz: o.sz || T.SIZE.panelHead, b: true, color: T.COLOR.white, align: "center" }), innerW, h - 0.04, T.SIZE.BODY_MIN);
    slide.addText(A.runsOf(paras), { x: box.x + i * (w - ov), y: box.y, w, h, shape: st, fill: { color: o.fills && o.fills[i] ? o.fills[i] : T.COLOR.navy }, line: { color: "FFFFFF", width: 0.75 }, valign: "middle", margin: A.boxMargin([0.05, 0.02, 0.05, 0.02]), isTextBox: true, autoFit: false });
  });
  return w;
}
/** Conclusion box: navy label on the left + tinted message on the right */
/** Conclusion band label. Slide pointLabel, then meta.pointLabel, then meta.labels.common.pointLabel, then the default */
/** Height (inches) for the footnote line count */
function noteRows(sb) {
  return 0.2 * [].concat((sb && sb.footnotes) || []).filter(Boolean).length;
}
function pointLabel(ctx, sb) {
  return (sb && sb.pointLabel) || (ctx.meta && ctx.meta.pointLabel) || LB.label("common", "pointLabel");
}
const CALLOUT_LABEL_W = 1.2; // Point band label cell width (inches on 16:9, scaled by the page width ratio)
const CALLOUT_MG = [0.12, 0.03, 0.08, 0.03]; // Point band text cell insets (left, top, right, bottom inches)
const CALLOUT_H = 0.5; // Point band height (inches)
const CALLOUT_W_STEP = 0.1; // Step for widening the Point band (inches)
/** Lines of the Point text (array items and line breaks split into lines) */
function calloutLines(text) {
  return [].concat(text).flatMap((t) => String(t).split("\n")).filter(Boolean);
}
function callout(ctx, slide, box, lbl, text) {
  const lw = CALLOUT_LABEL_W * ctx.S.sx;
  label(ctx, slide, { x: box.x, y: box.y, w: lw, h: box.h }, lbl || pointLabel(ctx, ctx.sb), { sz: T.SIZE.body });
  // Several lines get bullets to keep items apart (1 line is written as a sentence without a bullet)
  const lines = calloutLines(text);
  const paras = lines.map((t) => ({ align: "left", bullet: lines.length > 1, indent: lines.length > 1 ? T.PARA.bulletIndentIn : 0, marL: lines.length > 1 ? T.PARA.bulletIndentIn : 0, runs: [{ t, sz: T.SIZE.body, b: true, color: T.COLOR.textDark }] }));
  slide.addText(A.runsOf(paras), { x: box.x + lw, y: box.y, w: box.w - lw, h: box.h, shape: ctx.pres.ShapeType.rect, fill: { color: T.COLOR.tintBg }, line: { color: T.COLOR.borderLight, width: T.PANEL.LINE_PT }, valign: "middle", margin: A.boxMargin(CALLOUT_MG), isTextBox: true, autoFit: false });
}
/** Point band width. Starts at the group width w0 and widens until the text fits in the band height (upper bound maxW)
 *  When a panel or card group narrows to short items, the band text overflows, so the band and the group are widened together */
function calloutW(ctx, text, w0, maxW) {
  const lines = calloutLines(text);
  const ind = lines.length > 1 ? T.PARA.bulletIndentIn : 0;
  const inset = CALLOUT_LABEL_W * ctx.S.sx + CALLOUT_MG[0] + CALLOUT_MG[2] + ind;
  const maxLines = Math.max(1, Math.floor((CALLOUT_H - CALLOUT_MG[1] - CALLOUT_MG[3]) / A.lineHeightIn(T.SIZE.body)));
  const fits = (w) => lines.reduce((n, t) => n + A.estimateLines(t, w - inset, T.SIZE.body, true), 0) <= maxLines;
  let w = w0;
  while (w < maxW && !fits(w)) w = Math.min(maxW, w + CALLOUT_W_STEP);
  return w;
}
/** Adds ※ before a note string (left as is if it starts with ※ or *) */
function noteText(v, joiner) {
  const arr = [].concat(v).filter(Boolean).map((x) => String(x).trim());
  if (joiner === "; ") return `※ ${arr.map((x) => x.replace(/^※\s*/, "")).join("; ")}`;
  // ※ is added even before text starting with 출처 or 자료 (prevents a missing ※ mark)
  return arr.map((x) => (/^(※|\*)/.test(x) ? x : `※ ${x}`)).join("\n");
}
function source(ctx, slide, sb) {
  A.footnotes(slide, ctx.S, sb.footnotes);
  if (!sb.source) return;
  const S = ctx.S;
  A.text(slide, { x: S.bodyX, y: S.noteY, w: S.bodyW, h: 0.24 }, noteText(sb.source, "; "), { sz: T.SIZE.note, color: T.COLOR.textMuted, align: "left", valign: "top", mg: [0, 0, 0, 0] });
}
function tag(ctx, slide, box, text) {
  // Sample, Illustrative tag: bordered box rotated -27 degrees
  // Over a table, LibreOffice draws the table on top and hides it, so the tag goes outside the content box (top left) with a white fill
  slide.addText(A.runsOf(A.parasFromString(text, { sz: T.SIZE.tableDense, b: true, color: T.COLOR.navyDeep, align: "center" })), { x: box.x, y: box.y, w: 1.1, h: 0.3, rotate: -15, shape: ctx.pres.ShapeType.rect, fill: { color: T.COLOR.white }, line: { color: T.COLOR.navyDeep, width: 1.25 }, valign: "middle", margin: 0, isTextBox: true, autoFit: false });
}

// ---------------------------------------------------------------- The 4 band templates
const COVER_NAME_W = 6.0; // Width of the cover company name text box (inches on 16:9). Holds about 24 characters in 18pt bold

function cover(ctx, slide, sb) {
  const S = ctx.S, s = sb.slots || {};
  const L = S.layout;
  // One horizontal line above and one below the title (y 2.03 and 3.76)
  const mx = S.marginX; // The edge margin is fixed regardless of page size
  const rule = (y) => slide.addShape(ctx.pres.ShapeType.line, { x: mx, y: y * S.sy, w: L.W - 2 * mx, h: 0, line: { color: T.COLOR.border, width: 0.5 } });
  rule(2.03);
  // The title sits exactly centered between the two horizontal lines
  const tH = 1.1 * S.sy, tMid = (2.03 + 3.76) / 2 * S.sy;
  A.text(slide, { x: 0.66 * S.sx, y: +(tMid - tH / 2).toFixed(3), w: L.W - 1.3 * S.sx, h: tH }, s.title || sb.headline || "", { sz: T.SIZE.coverTitle - 4, bold: true, align: "left", valign: "middle", mg: [0, 0, 0, 0] }); // Holds a 2-line title
  rule(3.76);
  label(ctx, slide, { x: mx, y: 3.96 * S.sy, w: 1.7 * S.sx, h: 0.4 }, LB.label("cover", "label", s.label), { sz: T.SIZE.body });
  A.text(slide, { x: mx, y: 4.5 * S.sy, w: 4 * S.sx, h: 0.4 }, s.date || "", { sz: T.SIZE.coverSub, align: "left", mg: [0, 0, 0, 0] });
  // The contracting agency goes under the date by default. With clientPos "top", it goes small above the line over the title
  if (s.client) {
    if (s.clientPos === "top") A.text(slide, { x: mx, y: 1.6 * S.sy, w: 8 * S.sx, h: 0.36 }, s.client, { sz: T.SIZE.body, color: T.COLOR.textGray, align: "left", mg: [0, 0, 0, 0] });
    else A.text(slide, { x: mx, y: 4.9 * S.sy, w: 8 * S.sx, h: 0.4 }, s.client, { sz: T.SIZE.coverSub, align: "left", mg: [0, 0, 0, 0] });
  }
  const logoBox = { x: L.W / 2 - 1.1 * S.sx, y: 5.6 * S.sy, w: 2.2 * S.sx, h: 0.6 };
  // Without a logo, the company name is typeset on one line in a box wider than the logo spot (long names would wrap at the logo spot width)
  const nameBox = { x: L.W / 2 - (COVER_NAME_W / 2) * S.sx, y: logoBox.y, w: COVER_NAME_W * S.sx, h: logoBox.h };
  if (s.logo) A.image(ctx.pres, slide, logoBox, s.logo); else A.text(slide, nameBox, s.company || ctx.meta.company || LB.label("common", "company"), { sz: T.SIZE.marker, bold: true, align: "center", mg: [0, 0, 0, 0] });
}
function contents(ctx, slide, sb) {
  const S = ctx.S, items = (sb.slots && sb.slots.items) || sb.items || [];
  const L = S.layout;
  A.text(slide, { x: 2.5 * S.sx, y: 2.15 * S.sy, w: 2.2 * S.sx, h: 0.9 }, LB.label("contents", "title", sb.slots && sb.slots.title), { sz: T.SIZE.contentsTitle, bold: true, align: "center", mg: [0, 0, 0, 0] });
  slide.addShape(ctx.pres.ShapeType.line, { x: 2.5 * S.sx, y: 2.1 * S.sy, w: 2.2 * S.sx, h: 0, line: { color: T.COLOR.border, width: 0.75 } });
  slide.addShape(ctx.pres.ShapeType.line, { x: 2.5 * S.sx, y: 3.1 * S.sy, w: 2.2 * S.sx, h: 0, line: { color: T.COLOR.border, width: 0.75 } });
  const roman = ["Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ"];
  const step = Math.min(0.62, 3.0 / Math.max(items.length, 1));
  items.forEach((it, i) => {
    const y = 2.2 * S.sy + i * step;
    A.text(slide, { x: 6.5 * S.sx, y, w: 0.6, h: 0.45 }, `${roman[i] || i + 1}.`, { sz: T.SIZE.contentsItem, bold: true, align: "left", mg: [0, 0, 0, 0] });
    A.text(slide, { x: 7.2 * S.sx, y, w: L.W - 7.2 * S.sx - S.marginX, h: 0.45 }, it, { sz: T.SIZE.contentsItem, align: "left", mg: [0, 0, 0, 0] });
  });
}
function divider(ctx, slide, sb) {
  const S = ctx.S, s = sb.slots || {}, items = s.items || sb.items || [];
  A.text(slide, { x: 2.23 * S.sx, y: 2.37 * S.sy, w: 1.0, h: 0.5 }, `${s.no || ""}.`, { sz: T.SIZE.dividerNo, bold: true, align: "left", mg: [0, 0, 0, 0] });
  A.text(slide, { x: 3.4 * S.sx, y: 2.42 * S.sy, w: 7 * S.sx, h: 0.45 }, s.title || sb.headline || "", { sz: T.SIZE.secTitle, align: "left", mg: [0, 0, 0, 0] });
  slide.addShape(ctx.pres.ShapeType.line, { x: 2.23 * S.sx, y: 2.98 * S.sy, w: 9.1 * S.sx, h: 0, line: { color: T.COLOR.border, width: 0.75 } });
  items.forEach((it, i) => A.text(slide, { x: 3.9 * S.sx, y: 3.15 * S.sy + i * 0.42, w: 7 * S.sx, h: 0.38 }, `${i + 1}.  ${it}`, { sz: T.SIZE.dividerItem, align: "left", mg: [0, 0, 0, 0] }));
}
function end(ctx, slide, sb) {
  const S = ctx.S, s = sb.slots || {};
  A.text(slide, { x: S.marginX, y: 2.9 * S.sy, w: S.contentW, h: 0.9 }, LB.label("end", "title", s.title), { sz: T.SIZE.dividerTitle, bold: true, align: "center", mg: [0, 0, 0, 0] });
  A.text(slide, { x: S.marginX, y: 3.9 * S.sy, w: S.contentW, h: 0.5 }, s.company || ctx.meta.company || LB.label("common", "company"), { sz: T.SIZE.marker, align: "center", mg: [0, 0, 0, 0] });
}

// ---------------------------------------------------------------- Proposal overview
/** Background (numbered leads + evidence) in 2 columns + purpose box + issues and solutions. slots: {leftHead, leads:[{title, sub:[]}], rightHead, purposeHead, purpose, issueHead, issues:[]} */
function purpose(ctx, slide, sb) {
  const s = sb.slots || {};
  const b = body(ctx, sb);
  const lw = b.w * 0.62, rw = b.w - lw - 0.5 * ctx.S.sx;
  const L = subhead(ctx, slide, { x: b.x, y: b.y, w: lw, h: b.h }, LB.label("purpose", "leftHead", s.leftHead));
  const R = subhead(ctx, slide, { x: b.x + lw + 0.5 * ctx.S.sx, y: b.y, w: rw, h: b.h }, LB.label("purpose", "rightHead", s.rightHead));
  // The background lead group sits on a home plate background. finalize applies the tip width adj(16372) as avLst
  slide.addShape(ctx.pres.ShapeType.homePlate, { x: L.x, y: L.y, w: L.w, h: L.h, fill: { color: T.COLOR.white }, line: { color: T.COLOR.borderLight, width: T.PANEL.LINE_PT }, objectName: "adj:16372" });
  const leads = s.leads || [];
  // Measure the height each lead needs first, then share the remaining height in proportion so leads do not overlap
  const twAll = L.w - 0.8 - Math.min(L.w, L.h) * 0.16372 - 0.15;
  const need = leads.map((ld) => {
    const th0 = A.estimateLines(ld.title, twAll - 0.1, T.SIZE.panelHead, true) > 1 ? 0.55 : 0.4;
    const subs0 = (ld.sub || []).filter(Boolean);
    const subH = subs0.reduce((a, t) => a + Math.max(1, A.estimateLines(typeof t === "string" ? t : t.text, twAll - T.PARA.bulletIndentIn, T.SIZE.body)) * A.lineHeightIn(T.SIZE.body) + 0.045, 0);
    const noteH0 = 0.2 * [].concat(ld.note || []).filter(Boolean).length;
    return th0 + 0.12 + subH + noteH0 + 0.12;
  });
  const sum = need.reduce((a, b) => a + b, 0) || 1;
  const availL = L.h - 0.22; // keep margin above and below the chevron (so the last bullet does not touch the bottom line)
  const scale = availL / sum;
  const heights = need.map((h) => h * Math.min(1.6, Math.max(0.85, scale)));
  const tot = heights.reduce((a, b) => a + b, 0);
  if (tot > availL) heights.forEach((h, i) => { heights[i] = h * (availL / tot); });
  const tw = L.w - 0.8 - Math.min(L.w, L.h) * 0.16372 - 0.15; // stop inside the tip
  let acc = L.y + 0.06;
  const geo = leads.map((ld, i) => {
    const rh = heights[i];
    const y = acc;
    acc += rh;
    const th = A.estimateLines(ld.title, tw - 0.1, T.SIZE.panelHead, true) > 1 ? 0.55 : 0.4;
    // Lead evidence is bullets; a note is a small gray line starting with ※
    const subs = (ld.sub || []).filter((x) => x != null);
    const notes = [].concat(ld.note || []).filter(Boolean);
    const noteH = notes.length ? 0.2 * notes.length : 0;
    return { ld, y, rh, th, subs, notes, noteH, sbox: { x: L.x + 0.8, y: y + th + 0.1, w: tw, h: rh - th - 0.15 - noteH } };
  });
  // Evidence bullets are one level, so every lead uses the smallest of the sizes fitted per lead cell
  const subOpt = { valign: "top", noWarn: true, forceBullet: true, gapPt: 3 };
  geo.forEach((g) => { g.fit = g.subs.length ? bulletFitSize(g.sbox, g.subs, subOpt) : null; });
  const fits = geo.filter((g) => g.fit != null).map((g) => g.fit);
  const subSz = fits.length ? Math.min(...fits) : T.SIZE.body;
  // Only leads that would fit larger than the common size start from it (the lead that set the common size keeps its own fit)
  const subOpts = geo.map((g) => (g.fit > subSz ? { ...subOpt, sz: subSz } : subOpt));
  // Evidence bullets also use one paragraph spacing across leads
  const subGap = groupGap(geo.map((g) => (g.subs.length ? g.sbox : null)), geo.map((g) => g.subs), subOpts);
  geo.forEach(({ ld, y, rh, th, subs, notes, noteH, sbox }, i) => {
    label(ctx, slide, { x: L.x + 0.33, y: y + 0.15, w: 0.37, h: 0.36 }, String(i + 1), { sz: T.SIZE.body });
    A.text(slide, { x: L.x + 0.8, y: y + 0.1, w: tw, h: th }, ld.title, { sz: T.SIZE.panelHead, bold: true, align: "left", valign: "middle" });
    // Shrink the font to fit the lead cell; review catches anything that still overflows
    if (subs.length) bullets(ctx, slide, sbox, subs, { ...subOpts[i], groupGapPt: subGap });
    // The note sits right below the evidence bullet box (bullets spread leftover height into item gaps and fill the box, so a fixed per-item offset overlaps)
    // The evidence box height already excludes the note height (noteH), so the note stays inside the lead cell
    const noteY = subs.length ? sbox.y + sbox.h : y + th + 0.12 + Math.min(rh - th - 0.17 - noteH, 0.02);
    if (notes.length) A.text(slide, { x: L.x + 0.8, y: noteY, w: tw, h: noteH },
      noteText(notes),
      { sz: T.SIZE.note, color: T.COLOR.textMuted, align: "left", valign: "top", mg: [0, 0, 0, 0] });
  });
  label(ctx, slide, { x: R.x, y: R.y, w: R.w, h: T.PANEL.HEAD_H }, LB.label("purpose", "purposeHead", s.purposeHead), { sz: T.SIZE.body });
  const pb = { x: R.x, y: R.y + T.PANEL.HEAD_H, w: R.w, h: 1.05 };
  frame(ctx, slide, pb); A.text(slide, pb, s.purpose || "", { sz: T.SIZE.body, bold: true, align: "center" });
  const ib = subhead(ctx, slide, { x: R.x, y: pb.y + pb.h + 0.2, w: R.w, h: R.h - pb.h - 0.6 }, LB.label("purpose", "issueHead", s.issueHead));
  const issues = s.issues || [];
  const ih = Math.min(0.5, ib.h / Math.max(issues.length, 1) - 0.08);
  issues.forEach((it, i) => { const bx = { x: ib.x, y: ib.y + i * (ih + 0.08), w: ib.w, h: ih }; frame(ctx, slide, bx); A.text(slide, bx, it, { sz: T.SIZE.body, align: "center" }); });
  source(ctx, slide, sb);
}
const OUT_ROW_MAX = 5; // max cells in one output row (more splits into two rows)
const OUT_ROW_GAP = 0.1; // gap between output rows
/** Output cell layout. If outputs has the same length as the modules and some element is an array, align several items (bullets) per module under each module column
 *  If it is a string list, place by count: 1-2 centers module-column-width cells, 3-5 go in one row, 6 or more go in two rows of at most 5 cells
 *  Cell height is unified to the height the longest cell needs. The returned y is relative to the top of the output area */
function scopeOutputs(outs, nMod, modCols, ix, iw) {
  if (!outs.length) return { h: 0, cells: [] };
  const lists = outs.map((o) => [].concat(o));
  const need = (w, l) => Math.max(0.5, itemsNeedH(l, w, T.SIZE.body));
  if (nMod && outs.length === nMod && outs.some(Array.isArray)) {
    const h = Math.max(...modCols.map((c, i) => need(c.w, lists[i])));
    return { h, cells: modCols.map((c, i) => ({ x: c.x, y: 0, w: c.w, h, items: lists[i] })) };
  }
  const n = outs.length, nRow = n > OUT_ROW_MAX ? 2 : 1, per = Math.ceil(n / nRow);
  const cw = n <= 2 ? modCols[0].w : cols({ x: ix, y: 0, w: iw, h: 1 }, per)[0].w;
  const h = Math.max(...lists.map((l) => need(cw, l)));
  const cells = [];
  for (let r = 0; r < nRow; r++) {
    const row = lists.slice(r * per, (r + 1) * per);
    const rw = cw * row.length + T.PANEL.GAP * (row.length - 1), x0 = ix + (iw - rw) / 2;
    row.forEach((l, j) => cells.push({ x: x0 + j * (cw + T.PANEL.GAP), y: r * (h + OUT_ROW_GAP), w: cw, h, items: l }));
  }
  return { h: nRow * h + (nRow - 1) * OUT_ROW_GAP, cells };
}
/** Vision band + goal + N module columns of scope + outputs. slots: {vision, goal, modules:[{title, items:[]}], outputs:[text | per-module text array]} */
const SCOPE_TAG_W = 0.7; // structure label (VISION, SCOPE, OUTPUT) column width (16:9 basis, scaled by the page ratio)
const SCOPE_TAG_GAP = 0.1; // gap between the structure label column and the content
const SCOPE_TAG_MG = 0.03; // structure label side margin (centered, so a smaller margin keeps the text in place)
const SCOPE_TAG_KEYS = ["visionTag", "scopeTag", "outputTag"]; // structure label slots (defaults VISION, SCOPE, OUTPUT)
function scope(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb), S = ctx.S;
  // Set the column width floor to the longest label so structure label words fit on one line even on narrow pages
  const tags = SCOPE_TAG_KEYS.map((k) => LB.label("scope", k, s[k]));
  const tagW = Math.max(SCOPE_TAG_W * S.sx, A.wordWidthIn(tags, T.SIZE.note, false) + 2 * SCOPE_TAG_MG);
  const ix = b.x + tagW + SCOPE_TAG_GAP * S.sx, iw = b.x + b.w - ix;
  const tag = (y, h, t) => A.text(slide, { x: b.x, y, w: tagW, h }, t, { sz: T.SIZE.note, color: T.COLOR.textMuted, align: "center", mg: [SCOPE_TAG_MG, null, SCOPE_TAG_MG, null] });
  tag(b.y, 0.5, tags[0]);
  const vb = { x: ix, y: b.y, w: iw, h: 0.5 };
  frame(ctx, slide, vb, { line: T.COLOR.navy, pt: 1.0 }); A.text(slide, vb, `"${s.vision || ""}"`, { sz: T.SIZE.panelHead, bold: true, color: T.COLOR.navy, align: "center" });
  label(ctx, slide, { x: ix, y: vb.y + 0.6, w: iw, h: 0.34 }, LB.label("scope", "goalHead", s.goalHead), { sz: T.SIZE.body });
  const gb = { x: ix, y: vb.y + 0.94, w: iw, h: 0.4 };
  frame(ctx, slide, gb, { fill: T.COLOR.tintHead }); A.text(slide, gb, s.goal || "", { sz: T.SIZE.body, bold: true, align: "center" });
  const mods = s.modules || [];
  const modCols = cols({ x: ix, y: 0, w: iw, h: 1 }, Math.max(mods.length, 1));
  const outs = [].concat(s.outputs || []).filter((o) => o && (!Array.isArray(o) || o.length));
  const outLay = scopeOutputs(outs, mods.length, modCols, ix, iw);
  const outH = outLay.h;
  const my = gb.y + gb.h + 0.25, mh = b.y + b.h - my - (outs.length ? outH + 0.25 : 0);
  tag(my, mh, tags[1]);
  // The module row and the output row each use one paragraph spacing
  const mcols = cols({ x: ix, y: my, w: iw, h: mh }, Math.max(mods.length, 1));
  const mps = mcols.map((c, i) => (mods[i] ? { head: mods[i].title, items: mods[i].items, noWarn: true } : null));
  const mgap = panelsGap(mcols, mps);
  mcols.forEach((c, i) => { if (mps[i]) panel(ctx, slide, c, { ...mps[i], groupGapPt: mgap }); });
  if (outs.length) {
    const oy = b.y + b.h - outH;
    tag(oy, outH, tags[2]);
    const ocbs = outLay.cells.map((c) => ({ x: c.x, y: oy + c.y, w: c.w, h: c.h }));
    const oopt = { noWarn: true, valign: "middle" };
    const ogap = groupGap(ocbs, outLay.cells.map((c) => c.items), oopt);
    ocbs.forEach((cb, j) => { frame(ctx, slide, cb); bullets(ctx, slide, cb, outLay.cells[j].items, { ...oopt, groupGapPt: ogap }); });
  }
  source(ctx, slide, sb);
}
/** Question banner + 3 columns of capability tiles (1-4 items per column). slots: {question, tiles:[{title, items:[]}]} */
function features(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  // Layout: capability columns under the question banner (full-width rounded rectangle). Column heads are navy labels, items are bordered boxes
  const tiles = s.tiles || [];
  const maxItems = Math.max(...tiles.map((tl) => ((tl && tl.items) || []).length), 1);
  const Q_H = 0.5, Q_GAP = 0.3;
  // Give leftover height to box height first, then item gaps, so few items still fill the body band
  const BOX_MIN = 0.44, BOX_MAX = 0.95, GAP_MIN = 0.12, GAP_MAX = 0.25, HEAD_GAP = 0.15;
  const avail = b.h - Q_H - Q_GAP - T.PANEL.TITLE_H - HEAD_GAP;
  let ih = BOX_MIN, gap = GAP_MIN;
  let slack = avail - (maxItems * ih + (maxItems - 1) * gap);
  if (slack > 0) { const a = Math.min(BOX_MAX - ih, slack / maxItems); ih += a; slack -= a * maxItems; }
  if (slack > 0 && maxItems > 1) { const a = Math.min(GAP_MAX - gap, slack / (maxItems - 1)); gap += a; slack -= a * (maxItems - 1); }
  if (slack < 0) { ih = Math.max(0.3, (avail - (maxItems - 1) * GAP_MIN) / maxItems); gap = GAP_MIN; slack = 0; }
  // If height is still left, center the whole group, question banner included, vertically in the body band
  const top = b.y + Math.max(0, slack / 2);
  const qb = { x: b.x, y: top, w: b.w, h: Q_H };
  slide.addText(A.runsOf(A.parasFromString(s.question || "", { sz: T.SIZE.marker, b: true, color: T.COLOR.white, align: "center" })), { ...qb, shape: ctx.pres.ShapeType.roundRect, rectRadius: 0.05, fill: { color: T.COLOR.navyDeep }, line: { color: "FFFFFF", width: 0, transparency: 100 }, valign: "middle", margin: 0, isTextBox: true, autoFit: false });
  const tileTop = qb.y + Q_H + Q_GAP;
  cols({ x: b.x, y: tileTop, w: b.w, h: T.PANEL.TITLE_H }, Math.max(tiles.length, 1)).forEach((c, i) => {
    const tl = tiles[i]; if (!tl) return;
    label(ctx, slide, { x: c.x, y: tileTop, w: c.w, h: T.PANEL.TITLE_H }, tl.title);
    ((tl.items) || []).forEach((it, j) => {
      const bx = { x: c.x, y: tileTop + T.PANEL.TITLE_H + HEAD_GAP + j * (ih + gap), w: c.w, h: ih };
      frame(ctx, slide, bx);
      A.text(slide, bx, it, { sz: T.SIZE.body, align: "center", valign: "middle" });
    });
  });
  source(ctx, slide, sb);
}
const STRAT_ROOF_H = 0.6; // roof (goal) height (one 16pt line plus top and bottom margin)
const STRAT_GAP = 0.16; // vertical gap between roof, pillars, result boxes and base (same value on every level)
const STRAT_RES_H = 0.42; // height of the result box under each pillar
const STRAT_BASE_H = 0.5; // base (conclusion) height (one 14pt line plus margin; same value as the composite conclusion band)
const STRAT_EAVE = 0.2; // how far the roof and base extend past the pillar group on each side
/** Roof (goal) + N strategy pillars + base (conclusion). slots: {goal, strategies:[{title, items:[], result}], conclusion} */
function strategy(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const st = s.strategies || [];
  // So the roof (goal), equal-width pillars (strategies) and base (conclusion) read as one house, the roof and base span the full body and the pillar group is inset by STRAT_EAVE on each side
  // Roof text starts at 16pt and shrinks down to 14pt if it does not fit the roof's inner width (excluding the slopes)
  const roof = A.fitParas(A.parasFromString(s.goal || "", { sz: T.SIZE.goalBand, b: true, color: T.COLOR.white, align: "center" }), b.w - 2 * STRAT_ROOF_H, STRAT_ROOF_H - 0.1, T.SIZE.panelHead);
  slide.addText(A.runsOf(roof), { x: b.x, y: b.y, w: b.w, h: STRAT_ROOF_H, shape: ctx.pres.ShapeType.trapezoid, fill: { color: T.COLOR.navyDeep }, line: { color: "FFFFFF", width: 0, transparency: 100 }, valign: "middle", margin: 0, isTextBox: true, autoFit: false });
  const hasRes = st.some((x) => x && x.result);
  const baseY = b.y + b.h - STRAT_BASE_H;
  const top = b.y + STRAT_ROOF_H + STRAT_GAP;
  const bottom = s.conclusion ? baseY - STRAT_GAP : b.y + b.h;
  const cb = { x: b.x + STRAT_EAVE, y: top, w: b.w - 2 * STRAT_EAVE, h: bottom - top };
  const resH = hasRes ? STRAT_GAP + STRAT_RES_H : 0;
  const scols = cols(cb, Math.max(st.length, 1));
  const bds = scols.map((c) => ({ x: c.x, y: c.y + T.PANEL.TITLE_H, w: c.w, h: c.h - T.PANEL.TITLE_H - resH }));
  // Pillar columns use one paragraph spacing
  const sgap = groupGap(bds.map((bd, i) => (st[i] ? bd : null)), st.map((x) => (x && x.items) || []), { noWarn: true });
  scols.forEach((c, i) => {
    const x = st[i]; if (!x) return;
    label(ctx, slide, { x: c.x, y: c.y, w: c.w, h: T.PANEL.TITLE_H }, `${["①", "②", "③", "④", "⑤"][i]} ${x.title}`);
    const bd = bds[i];
    frame(ctx, slide, bd); bullets(ctx, slide, bd, x.items || [], { noWarn: true, groupGapPt: sgap });
    if (x.result) { const rb = { x: c.x, y: bd.y + bd.h + STRAT_GAP, w: c.w, h: STRAT_RES_H }; frame(ctx, slide, rb, { line: T.COLOR.navy, pt: 1 }); A.text(slide, rb, x.result, { sz: T.SIZE.body, bold: true, align: "center" }); }
  });
  if (s.conclusion) label(ctx, slide, { x: b.x, y: baseY, w: b.w, h: STRAT_BASE_H }, s.conclusion, { fill: T.COLOR.navyDeep, sz: T.SIZE.panelHead });
  source(ctx, slide, sb);
}
/** N module chevron columns + Task boxes linked vertically. slots: {modules:[{id, title, tasks:[]}]} */
function process(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const mods = s.modules || [];
  cols(b, Math.max(mods.length, 1), 0.45 * ctx.S.sx).forEach((c, i) => {
    const m = mods[i]; if (!m) return;
    A.text(slide, { x: c.x, y: c.y, w: c.w, h: 0.3 }, m.id || LB.format(LB.label("process", "idFormat", s.idFormat), { n: i + 1 }), { sz: T.SIZE.body, color: T.COLOR.textGray, align: "center", mg: [0, 0, 0, 0] });
    // Many modules make the chevrons narrow, so raise the height and drop the font one step
    const many = mods.length >= 6;
    chevronRow(ctx, slide, { x: c.x, y: c.y + 0.35, w: c.w, h: many ? 0.62 : 0.5 }, [LB.format(LB.label("process", "titleFormat", s.titleFormat), { n: i + 1, t: `${m.title}` })], { allChevron: i > 0, sz: many ? T.SIZE.body : T.SIZE.panelHead });
    const tasks = m.tasks || [];
    const top0Base = mods.length >= 6 ? 1.22 : 1.1;
    // Spread Task boxes evenly down to the body bottom. Align the last box bottom with the body bottom, but stretch gaps to at most 1.5x the even gap
    const top0 = top0Base, availT = c.h - top0;
    const nT = Math.max(tasks.length, 1);
    const th = Math.max(0.36, Math.min(0.5, availT / nT - 0.3));
    const pitch = nT > 1 ? Math.min((availT - th) / (nT - 1), (availT / nT) * 1.5) : 0;
    tasks.forEach((t, j) => {
      const tb = { x: c.x + c.w * 0.1, y: c.y + top0 + j * pitch, w: c.w * 0.8, h: th };
      frame(ctx, slide, tb); A.text(slide, tb, `${i + 1}-${j + 1}. ${t}`, { sz: T.SIZE.body, align: "center" });
      // Draw from the previous box bottom to the next box top so the link looks unbroken
      if (j > 0) {
        const prevBottom = c.y + top0 + (j - 1) * pitch + th;
        slide.addShape(ctx.pres.ShapeType.line, { x: c.x + c.w / 2, y: prevBottom, w: 0, h: tb.y - prevBottom, line: { color: T.COLOR.border, width: 1, endArrowType: "triangle" } });
      }
    });
    // Between modules, an elbow connector runs from the last Task of one module to the first Task of the next
    if (i < mods.length - 1 && tasks.length) {
      const lastY = c.y + top0 + (tasks.length - 1) * pitch + th / 2;
      const nextY = c.y + top0 + th / 2;
      const x0 = c.x + c.w * 0.9, gapW = 0.45 * ctx.S.sx + c.w * 0.2;
      slide.addShape(ctx.pres.ShapeType.line, { x: x0, y: lastY, w: gapW / 2, h: 0, line: { color: T.COLOR.border, width: 1 } });
      slide.addShape(ctx.pres.ShapeType.line, { x: x0 + gapW / 2, y: nextY, w: 0, h: lastY - nextY, line: { color: T.COLOR.border, width: 1 } });
      slide.addShape(ctx.pres.ShapeType.line, { x: x0 + gapW / 2, y: nextY, w: gapW / 2, h: 0, line: { color: T.COLOR.border, width: 1, endArrowType: "triangle" } });
    }
  });
  source(ctx, slide, sb);
}

// ---------------------------------------------------------------- Execution plan (shared)
/** Module overview: stage chevrons (N Task columns) + row labels (추진과정 process, 활용자료 data, 산출물 outputs). slots: {tasks:[{title, process:[], data:[], output:[]}], rowLabels} */
const MO_LABEL_W = 0.95; // module overview row label column width (16:9 basis, scaled by the page ratio)
const MO_GRID_GAP = 0.12; // gap between the row label column and the stage grid
function module_overview(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb), S = ctx.S;
  const tasks = s.tasks || [];
  // rowLabels defaults to 4 entries [head row, 3 content rows]. With only 3, prepend the head row label so rows stay aligned
  const given = (s.rowLabels || []).filter(Boolean);
  const base = LB.label("module_overview", "rowLabels").slice(0, 4);
  const rl = given.length >= 4 ? given.slice(0, 4) : given.length === 3 ? [base[0]].concat(given) : base;
  // Floor the label box width (lw + grid gap - label gap) at the word width plus margin so row label words fit on one line even on narrow pages
  const lw = Math.max(MO_LABEL_W * S.sx, A.wordWidthIn(rl, T.SIZE.body, true) + 2 * T.PANEL.LABEL_MG_X + T.PANEL.LABEL_GAP - MO_GRID_GAP);
  const gy = [0, 0.55, 0.55 + (b.h - 0.55) * 0.5, 0.55 + (b.h - 0.55) * 0.78, b.h];
  rl.forEach((r, i) => label(ctx, slide, { x: b.x, y: b.y + gy[i] + (i ? 0.1 : 0), w: lw + MO_GRID_GAP - T.PANEL.LABEL_GAP, h: gy[i + 1] - gy[i] - (i ? 0.1 : 0.05) }, r, { sz: T.SIZE.body }));
  const grid = { x: b.x + lw + MO_GRID_GAP, y: b.y, w: b.w - lw - MO_GRID_GAP, h: b.h };
  const chev = { x: grid.x, y: grid.y, w: grid.w, h: 0.5 };
  chevronRow(ctx, slide, chev, tasks.map((t) => t.title), {});
  const tcols = chevronCols(chev, Math.max(tasks.length, 1), grid.y, grid.h);
  // Boxes in the same row share one font size (a common size is computed per row)
  // Paragraph spacing is also one value per row (after the common size is set, per-box spacing is measured at that size and the smallest is used)
  const rowSz = {}, rowGap = {};
  [["process", 1], ["data", 2], ["output", 3]].forEach(([k, r]) => {
    const boxes = tcols.map((c) => ({ x: c.x, y: b.y + gy[r] + 0.1, w: c.w, h: gy[r + 1] - gy[r] - 0.1 }));
    rowSz[k] = groupSize(boxes, tasks.map((t) => (t && t[k]) || []));
    rowGap[k] = groupGap(boxes, tasks.map((t) => (t && t[k]) || []), { sz: rowSz[k] });
  });
  tcols.forEach((c, i) => {
    const t = tasks[i]; if (!t) return;
    [["process", 1], ["data", 2], ["output", 3]].forEach(([k, r]) => {
      const bx = { x: c.x, y: b.y + gy[r] + 0.1, w: c.w, h: gy[r + 1] - gy[r] - 0.1 };
      frame(ctx, slide, bx); bullets(ctx, slide, bx, t[k] || [], { noWarn: true, valign: "middle", sz: rowSz[k], groupGapPt: rowGap[k] });
    });
  });
  source(ctx, slide, sb);
}
/** One Task: survey design table on the left (target, source, scale, method, output) + measured sample on the right. slots: {leftHead, head:[2 column titles], rows:[[item, content]], sample:{head, table|items|image|chart, tag}, point} */
function task(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const lw = b.w * 0.42;
  const L = subhead(ctx, slide, { x: b.x, y: b.y, w: lw, h: b.h - (s.point ? 0.7 : 0) }, LB.label("task", "leftHead", s.leftHead));
  tableBlock(ctx, slide, L, { head: LB.label("task", "head", s.head), rows: s.rows || [] });
  const R = subhead(ctx, slide, { x: b.x + lw + 0.3, y: b.y, w: b.w - lw - 0.3, h: b.h - (s.point ? 0.7 : 0) }, LB.label("task", "sample.head", s.sample && s.sample.head));
  sampleBlock(ctx, slide, R, s.sample || {});
  if (s.point) callout(ctx, slide, { x: b.x, y: b.y + b.h - 0.5, w: b.w, h: 0.5 }, pointLabel(ctx, sb), s.point);
  source(ctx, slide, sb);
}
function sampleBlock(ctx, slide, box, sm) {
  if (sm.table) tableBlock(ctx, slide, box, sm.table);
  else if (sm.chart) A.chart(ctx.pres, slide, box, sm.chart);
  else if (sm.image !== undefined) A.image(ctx.pres, slide, box, sm.image, { label: "표본 화면" });
  else { frame(ctx, slide, box); bullets(ctx, slide, box, sm.items || [], { noWarn: true }); }
  tag(ctx, slide, { x: box.x + 0.05, y: box.y - 0.5 }, LB.label("task", "sample.tag", sm.tag));
}
/** Group of 2-3 Tasks: per column, a Task label + data, method and output bullets. slots: {tasks:[{id, title, items:[]}], rowLabels, freeLabel, point} */
function task_multi(ctx, slide, sb) {
  // Matrix with 2-4 Tasks as columns and item labels aligned as rows. Items are parsed as "label : value" to align rows
  const s = sb.slots || {}, b = body(ctx, sb);
  const tasks = s.tasks || [];
  const parse = (t) => {
    const m = {};
    (t.items || []).forEach((it) => {
      const g = String(it).match(/^\s*([^:：]{1,10})\s*[:：]\s*(.+)$/);
      if (g) (m[g[1].trim()] = m[g[1].trim()] || []).push(g[2].trim());
      else (m.__free = m.__free || []).push(String(it));
    });
    return m;
  };
  const maps = tasks.map(parse);
  let labels = s.rowLabels || [];
  if (!labels.length) {
    const seen = [];
    maps.forEach((m) => Object.keys(m).forEach((k) => { if (k !== "__free" && !seen.includes(k)) seen.push(k); }));
    labels = seen;
  }
  const hasFree = maps.some((m) => m.__free && m.__free.length);
  const freeLabel = LB.label("task_multi", "freeLabel", s.freeLabel); // label of the row collecting items not in "label : value" form
  const rows = labels.concat(hasFree ? [freeLabel] : []);
  const cb = { x: b.x, y: b.y, w: b.w, h: b.h - (s.point ? 0.62 : 0) };
  const labW = 1.0 * ctx.S.sx;
  const headH = 0.42;
  const gridX = cb.x + labW + 0.08;
  const gridW = cb.w - labW - 0.08;
  const colW = (gridW - T.PANEL.GAP * (Math.max(tasks.length, 1) - 1)) / Math.max(tasks.length, 1);
  // Column heads: Task chevrons
  tasks.forEach((t, i) => {
    const x = gridX + i * (colW + T.PANEL.GAP);
    label(ctx, slide, { x, y: cb.y, w: colW, h: headH }, `${t.id || LB.format(LB.label("task_multi", "idFormat", s.idFormat), { n: i + 1 })}. ${t.title || ""}`, { sz: T.SIZE.body });
  });
  const rowH = Math.max(0.3, (cb.h - headH - 0.1 - T.PANEL.GAP * (rows.length - 1)) / Math.max(rows.length, 1));
  rows.forEach((rl, r) => {
    const y = cb.y + headH + 0.1 + r * (rowH + T.PANEL.GAP);
    label(ctx, slide, { x: cb.x, y, w: labW + 0.08 - T.PANEL.LABEL_GAP, h: rowH }, rl, { sz: T.SIZE.tableDense, fill: T.COLOR.navyDeep });
    const valsOf = (i) => (rl === freeLabel ? (maps[i].__free || []) : (maps[i][rl] || []));
    // Bullet cells (two or more values) in the same row use one paragraph spacing
    const vopt = { noWarn: true, sz: T.SIZE.tableDense, forceBullet: true };
    const vboxes = tasks.map((t, i) => (valsOf(i).length > 1 ? { x: gridX + i * (colW + T.PANEL.GAP), y, w: colW, h: rowH } : null));
    const vgap = groupGap(vboxes, tasks.map((t, i) => valsOf(i)), vopt);
    tasks.forEach((t, i) => {
      const x = gridX + i * (colW + T.PANEL.GAP);
      const vals = valsOf(i);
      frame(ctx, slide, { x, y, w: colW, h: rowH });
      if (vals.length === 1) A.text(slide, { x: x + 0.08, y, w: colW - 0.16, h: rowH }, vals[0], { sz: T.SIZE.tableDense, align: "center", valign: "middle" });
      else if (vals.length) bullets(ctx, slide, vboxes[i], vals, { ...vopt, groupGapPt: vgap });
    });
  });
  if (s.point) callout(ctx, slide, { x: b.x, y: b.y + b.h - 0.5, w: b.w, h: 0.5 }, pointLabel(ctx, sb), s.point);
  source(ctx, slide, sb);
}

const PANEL_ITEM_SZ = 14; // starting item font size in panel templates (same size as the panel title; weight sets the hierarchy)
/** 1-4 panel columns. slots: {panels:[{head, items|text}], point} */
function bulletsT(ctx, slide, sb) {
  const b = body(ctx, sb), pn = sb.panels || (sb.slots && sb.slots.panels) || [];
  const point = sb.point || (sb.slots && sb.slots.point);
  const ptH = point ? 0.7 : 0;
  const n = Math.max(pn.length, 1), gap = T.PANEL.GAP;
  const lists = pn.map((p) => (p && (p.items || p.text)) || []);
  // Compute one common size so side-by-side panels share a font (items start at 14pt and shrink down to 11pt if height runs short)
  const full = cols({ x: b.x, y: b.y, w: b.w, h: b.h - ptH }, n);
  const psz = groupSize(full.map((c) => ({ ...c, h: c.h - T.PANEL.TITLE_H })), pn.map((p) => (p && p.items) || []), PANEL_ITEM_SZ);
  const ssz = Math.max(T.SIZE.BODY_MIN, psz - 2);
  // Give all panels one width fitted to the longest line and center the panel group and the 수행 Point callout (so short items leave no empty right side)
  const pw0 = Math.min(full[0].w, Math.max(...lists.map((l) => itemsNeedW(l, psz, ssz))) + 2 * T.PANEL.INSET + FIT_W_SLACK);
  // If the Point text does not fit in the band height, widen the panel group and the band together (the band has the same width as the panel group)
  const gw0 = pw0 * n + gap * (n - 1);
  const gw = point ? calloutW(ctx, point, gw0, b.w) : gw0;
  const pw = gw === gw0 ? pw0 : Math.min(full[0].w, (gw - gap * (n - 1)) / n), x0 = b.x + (b.w - gw) / 2;
  // Base panel height on content height and center the panels plus 수행 Point group vertically in the body
  const gh = T.PANEL.TITLE_H + panelBodyH(pn.map(() => pw), lists, psz, b.h - ptH - T.PANEL.TITLE_H, ssz);
  const top = b.y + (b.h - gh - ptH) / 2;
  const pboxes = cols({ x: x0, y: top, w: gw, h: gh }, n, gap);
  const pps = pboxes.map((c, i) => (pn[i] ? { ...pn[i], sz: psz, subSz: ssz } : null));
  const pgap = panelsGap(pboxes, pps); // side-by-side panels also share one paragraph spacing
  pboxes.forEach((c, i) => { if (pps[i]) panel(ctx, slide, c, { ...pps[i], groupGapPt: pgap }); });
  if (point) callout(ctx, slide, { x: x0, y: top + gh + 0.2, w: gw, h: 0.5 }, pointLabel(ctx, sb), point);
  source(ctx, slide, sb);
}
/** Height a text list takes in a box of width w (includes bullet indent, sub-items, paragraph gaps and box inset) */
function itemsNeedH(items, w, sz, subSz) {
  const list = (Array.isArray(items) ? items : [items]).filter((x) => x != null && x !== "");
  if (!list.length) return 0;
  const size = sz || T.SIZE.body, ssz = subSz || size;
  const innerW = Math.max(0.3, w - 2 * T.PANEL.INSET - (list.length > 1 ? T.PARA.bulletIndentIn : 0));
  const lineH = (t, ww, z) => Math.max(1, A.estimateLines(typeof t === "string" ? t : (t && t.text) || "", ww, z)) * A.lineHeightIn(z);
  const h = list.reduce((a, t) => a + lineH(t, innerW, size) + subsOf(t).reduce((x, u) => x + lineH(u, innerW - T.PARA.bulletIndentIn, ssz), 0), 0);
  return h + (list.length - 1) * (T.PARA.paraGapPt / 72) + 2 * T.PANEL.INSET;
}
const subsOf = (t) => (t && typeof t === "object" && Array.isArray(t.sub) ? t.sub : []);
/** Width of the longest line in a text list (includes bullet indent, excludes box inset). Sub-items indent one more level */
function itemsNeedW(items, sz, subSz) {
  const list = (Array.isArray(items) ? items : [items]).filter((x) => x != null && x !== "");
  const ind = T.PARA.bulletIndentIn;
  return Math.max(0, ...list.map((t) => {
    const lead = list.length > 1 || subsOf(t).length ? ind : 0;
    return Math.max(A.lineWidthIn(typeof t === "string" ? t : t.text, sz) + lead, ...subsOf(t).map((u) => A.lineWidthIn(u, subSz || sz) + 2 * ind));
  }));
}
/** Body height of side-by-side panels (capped at the available height)
 *  With several items, the height with item gaps widened up to paraGapMaxPt; with one item, FILL_EXPAND times the needed content height
 *  Keeps panels with few items from stretching to full body height and looking empty; leftover height goes to the margin outside the group */
function panelBodyH(widths, lists, sz, avail, subSz) {
  const cap = (l, i) => {
    const list = (Array.isArray(l) ? l : [l]).filter((x) => x != null && x !== "");
    const need = Math.max(0.5, itemsNeedH(list, widths[i], sz, subSz));
    return list.length > 1 ? need + (list.length + 1) * ((T.PARA.paraGapMaxPt - T.PARA.paraGapPt) / 72) : need * T.PANEL.FILL_EXPAND;
  };
  return Math.min(avail, Math.max(0.5, ...lists.map(cap)));
}
/** Full-width table. slots: {title, head, rows, colW, align, point} */
function table(ctx, slide, sb) {
  const s = sb.slots || sb, b = body(ctx, sb);
  const titleH = s.title ? T.PANEL.SUBHEAD_H : 0, legH = s.legend ? 0.3 : 0, ptH = s.point ? 0.7 : 0;
  // If the row height cap leaves the table shorter than the body, center the title, table and 수행 Point group vertically (body() already excludes the footnote height)
  const availT = b.h - titleH - legH - ptH;
  const shift = Math.max(0, (availT - tableLayout(s, b.w, availT).total) / 2);
  const g = { x: b.x, y: b.y + shift, w: b.w, h: b.h - 2 * shift };
  let box = s.title ? subhead(ctx, slide, g, s.title) : g;
  // Place the legend on one line at the top right of the table (Harvey balls and the like)
  if (s.legend) {
    A.text(slide, { x: box.x, y: box.y, w: box.w, h: 0.26 }, s.legend, { sz: T.SIZE.tableDense, color: T.COLOR.textGray, align: "right", mg: [0, 0, 0, 0] });
    box = { ...box, y: box.y + 0.3, h: box.h - 0.3 };
  }
  const used = tableBlock(ctx, slide, { ...box, h: box.h - ptH }, s);
  if (s.point) callout(ctx, slide, { x: b.x, y: box.y + used + 0.2, w: b.w, h: 0.5 }, pointLabel(ctx, sb), s.point);
  if (s.rows && s.rows.length > T.LIMIT.tableRowsPerSlide) ctx.warn(`table ${s.rows.length} rows: over the ${T.LIMIT.tableRowsPerSlide} limit, split needed`);
  source(ctx, slide, sb);
  return used;
}
/** One chart + findings on the right. slots: {chartTitle, chart, findings:[{head, items}]} */
function chart_text(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const lw = b.w * 0.55;
  const L = subhead(ctx, slide, { x: b.x, y: b.y, w: lw, h: b.h }, s.chartTitle || "");
  A.chart(ctx.pres, slide, { x: L.x, y: L.y, w: L.w, h: Math.max(T.PANEL.CHART_MIN_H, L.h - 0.1) }, s.chart || { type: "bar", barDir: "bar", categories: [], series: [] });
  const R = { x: b.x + lw + 0.3, y: b.y, w: b.w - lw - 0.3, h: b.h };
  const f = s.findings || [];
  // Base finding panel height on content and center the panel group vertically against the chart height
  const nf = Math.max(f.length, 1);
  const fAvail = (R.h - T.PANEL.GAP * (nf - 1)) / nf - T.PANEL.TITLE_H;
  const fh = T.PANEL.TITLE_H + panelBodyH(f.map(() => R.w), f.map((x) => (x && x.items) || []), T.SIZE.body, fAvail);
  const fH = fh * nf + T.PANEL.GAP * (nf - 1);
  const fboxes = rows({ ...R, y: R.y + (R.h - fH) / 2, h: fH }, nf);
  const fps = fboxes.map((r, i) => (f[i] ? { head: f[i].head, items: f[i].items, noWarn: true } : null));
  const fgap = panelsGap(fboxes, fps); // finding panels also share one paragraph spacing
  fboxes.forEach((r, i) => { if (fps[i]) panel(ctx, slide, r, { ...fps[i], groupGapPt: fgap }); });
  source(ctx, slide, sb);
}
/** Two charts side by side + findings for each. slots: {left:{title, chart, items}, right:{...}} */
function chart_two(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  cols(b, 2, 0.4).forEach((c, i) => {
    const side = i === 0 ? s.left : s.right; if (!side) return;
    const box = subhead(ctx, slide, c, side.title || "");
    A.chart(ctx.pres, slide, { x: box.x, y: box.y, w: box.w, h: box.h * 0.62 }, side.chart || { type: "bar", categories: [], series: [] });
    bullets(ctx, slide, { x: box.x, y: box.y + box.h * 0.66, w: box.w, h: box.h * 0.34 }, side.items || [], { noWarn: true, valign: "middle" });
  });
  source(ctx, slide, sb);
}
/** AS-IS / TO-BE contrast + gap. slots: {asis:{head, items}, tobe:{head, items}, gap:[]} */
// Row-paired comparison: when current items, gaps and improved items pair 1:1, each row gets a current box, a gap arrow and an improved box
const CMP_SIZES = [[14, 12, 13], [13, 12, 12], [12, 11, 12]]; // [item, evidence, gap] font sizes. Step down to the next set if the body height is exceeded
const CMP_COL_GAP = 0.16; // gap between the boxes and the gap arrow
const CMP_ROW_GAP = 0.14; // row gap
const CMP_HEAD_GAP = 0.1; // gap between the column title and the first row
const CMP_ROW_PAD = 0.16; // total top and bottom text slack in a row box
const CMP_PAD_X = 0.14; // left and right text margin in a row box
const CMP_ARROW_W = [1.5, 2.6]; // gap arrow width floor and cap (text longer than the cap wraps to two lines)
const CMP_ARROW_H_RATIO = 0.62; // gap arrow height relative to row height
const CMP_ARROW_ADJ = 30000; // arrow tip ratio (30% of the shape height)
const pairLead = (it) => (typeof it === "string" ? it : it.text);
/** Comparison box paragraphs. The item is a bold title and evidence items are dash bullets (a single evidence item is one line under the title with no bullet) */
function pairParas(it, iSz, sSz) {
  const subs = subsOf(it);
  const ps = [{ bullet: false, align: subs.length ? "left" : "center", runs: [{ t: pairLead(it), sz: iSz, b: true, color: T.COLOR.textDark }] }];
  subs.forEach((u) => ps.push({ bullet: subs.length > 1, buChar: "-", indent: T.PARA.bulletIndentIn, align: "left", spcBef: T.PARA.paraGapPt, runs: [{ t: u, sz: sSz, color: T.COLOR.textGray }] }));
  return ps;
}
const parasLead = (p) => (p.bullet ? T.PARA.bulletIndentIn : 0);
const parasNeedW = (ps) => Math.max(...ps.map((p) => A.lineWidthIn(p.runs[0].t, p.runs[0].sz, p.runs[0].b) + parasLead(p)));
const parasNeedH = (ps, innerW) => ps.reduce((h, p) => h + A.estimateLines(p.runs[0].t, innerW - parasLead(p), p.runs[0].sz, p.runs[0].b) * A.lineHeightIn(p.runs[0].sz) + (p.spcBef || 0) / 72, 0);
function comparePaired(ctx, slide, s, b) {
  const L = s.asis.items, R = s.tobe.items, G = s.gap, n = L.length, ins = T.PANEL.INSET;
  let lay = null;
  for (const [iSz, sSz, gSz] of CMP_SIZES) {
    const pl = L.map((it) => pairParas(it, iSz, sSz)), pr = R.map((it) => pairParas(it, iSz, sSz));
    const ah0 = A.lineHeightIn(gSz) + 2 * ins; // arrow height for a one-line gap text (used to estimate the tip width)
    const tip = ah0 * (CMP_ARROW_ADJ / 100000);
    const gw = Math.min(CMP_ARROW_W[1], Math.max(CMP_ARROW_W[0], ...G.map((g) => A.lineWidthIn(g, gSz, true) + 2 * ins + tip + FIT_W_SLACK)));
    // Current and improved boxes share one width. Fit it to the longest line and shrink it into the body width if it overflows
    const w = Math.min((b.w - gw - 2 * CMP_COL_GAP) / 2, Math.max(...[...pl, ...pr].map(parasNeedW)) + 2 * CMP_PAD_X + FIT_W_SLACK);
    const gh = Math.max(...G.map((g) => A.estimateLines(g, gw - 2 * ins - tip, gSz, true))) * A.lineHeightIn(gSz) + 2 * ins;
    const rowH = Math.max(gh / CMP_ARROW_H_RATIO, Math.max(...[...pl, ...pr].map((ps) => parasNeedH(ps, w - 2 * CMP_PAD_X))) + 2 * ins + CMP_ROW_PAD);
    const total = T.PANEL.TITLE_H + CMP_HEAD_GAP + n * rowH + (n - 1) * CMP_ROW_GAP;
    lay = { gSz, pl, pr, gw, w, rowH, total, tip };
    if (total <= b.h) break;
  }
  if (lay.total > b.h) ctx.warn(`compare total row height ${lay.total.toFixed(2)} > body ${b.h.toFixed(2)}in (shorten items or evidence)`);
  const gwTot = 2 * lay.w + lay.gw + 2 * CMP_COL_GAP;
  const x0 = b.x + (b.w - gwTot) / 2, y0 = b.y + Math.max(0, (b.h - lay.total) / 2);
  const xs = [x0, x0 + lay.w + CMP_COL_GAP, x0 + lay.w + lay.gw + 2 * CMP_COL_GAP];
  const ws = [lay.w, lay.gw, lay.w];
  // Column titles go gray for current, light navy for gap and navy for improved, so they darken from left to right
  [[LB.label("compare", "asis.head", s.asis.head), T.COLOR.textMuted, T.COLOR.white], [LB.label("compare", "gapHead", s.gapHead), T.COLOR.tintHead, T.COLOR.textDark], [LB.label("compare", "tobe.head", s.tobe.head), T.COLOR.navy, T.COLOR.white]]
    .forEach(([t, fill, color], j) => label(ctx, slide, { x: xs[j], y: y0, w: ws[j], h: T.PANEL.TITLE_H }, t, { fill, color }));
  const mg = A.boxMargin([CMP_PAD_X, ins, CMP_PAD_X, ins]);
  for (let i = 0; i < n; i++) {
    const y = y0 + T.PANEL.TITLE_H + CMP_HEAD_GAP + i * (lay.rowH + CMP_ROW_GAP);
    [[lay.pl[i], xs[0]], [lay.pr[i], xs[2]]].forEach(([ps, x]) => slide.addText(A.runsOf(ps), {
      x, y, w: lay.w, h: lay.rowH, shape: ctx.pres.ShapeType.rect, fill: { color: T.COLOR.white }, line: { color: T.COLOR.borderLight, width: T.PANEL.LINE_PT },
      valign: "middle", margin: mg, isTextBox: true, autoFit: false,
    }));
    const ah = lay.rowH * CMP_ARROW_H_RATIO;
    slide.addText(A.runsOf(A.parasFromString(G[i], { sz: lay.gSz, b: true, color: T.COLOR.white, align: "center" })), {
      x: xs[1], y: y + (lay.rowH - ah) / 2, w: lay.gw, h: ah, shape: ctx.pres.ShapeType.homePlate, fill: { color: T.COLOR.navy },
      line: { color: "FFFFFF", width: 0, transparency: 100 }, valign: "middle", margin: A.boxMargin([ins, 0.02, ins + ah * (CMP_ARROW_ADJ / 100000), 0.02]),
      isTextBox: true, autoFit: false, objectName: `adj:${CMP_ARROW_ADJ}`,
    });
  }
}
function compare(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const nA = (s.asis && s.asis.items || []).length;
  if (nA && Array.isArray(s.gap) && s.gap.length === nA && (s.tobe && s.tobe.items || []).length === nA) { comparePaired(ctx, slide, s, b); source(ctx, slide, sb); return; }
  const gh = s.gap ? 1.0 : 0;
  const pw = cols({ x: b.x, y: b.y, w: b.w, h: 1 }, 2, 0.8)[0].w;
  // Base panel height on content and center the contrast panels plus GAP band group vertically in the body
  const ph = T.PANEL.TITLE_H + panelBodyH([pw, pw], [(s.asis && s.asis.items) || [], (s.tobe && s.tobe.items) || []], T.SIZE.body, b.h - gh - T.PANEL.TITLE_H);
  const top = b.y + (b.h - ph - gh) / 2;
  const cb = { x: b.x, y: top, w: b.w, h: ph };
  const [L, R] = cols(cb, 2, 0.8);
  const lp = { head: LB.label("compare", "asis.head", s.asis && s.asis.head), items: s.asis && s.asis.items, headFill: T.COLOR.textMuted, noWarn: true };
  const rp = { head: LB.label("compare", "tobe.head", s.tobe && s.tobe.head), items: s.tobe && s.tobe.items, noWarn: true };
  const pgap = panelsGap([L, R], [lp, rp]); // contrast panels share one paragraph spacing
  panel(ctx, slide, L, { ...lp, groupGapPt: pgap });
  panel(ctx, slide, R, { ...rp, groupGapPt: pgap });
  slide.addShape(ctx.pres.ShapeType.rightArrow, { x: L.x + L.w + 0.15, y: cb.y + cb.h / 2 - 0.25, w: 0.5, h: 0.5, fill: { color: T.COLOR.navy }, line: { color: "FFFFFF", width: 0, transparency: 100 } });
  if (s.gap) { const gy = top + ph + 0.2; label(ctx, slide, { x: b.x, y: gy, w: 1.2 * ctx.S.sx, h: 0.8 }, LB.label("compare", "gapHead", s.gapHead), { sz: T.SIZE.body }); const gb = { x: b.x + 1.2 * ctx.S.sx, y: gy, w: b.w - 1.2 * ctx.S.sx, h: 0.8 }; frame(ctx, slide, gb, { fill: T.COLOR.tintBg }); bullets(ctx, slide, gb, s.gap, { noWarn: true }); }
  source(ctx, slide, sb);
}
/** Roadmap: strategy rows × year columns. slots: {periods:[], lanes:[{title, tasks:[{text, from, to}]}], note} */
function roadmap(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb), S = ctx.S;
  const lw = 2.3 * S.sx, periods = s.periods || [], lanes = s.lanes || [];
  const gx = b.x + lw + 0.1, gw = b.w - lw - 0.1, pw = gw / Math.max(periods.length, 1);
  label(ctx, slide, { x: b.x, y: b.y, w: lw + 0.1 - T.PANEL.LABEL_GAP, h: 0.35 }, LB.label("roadmap", "laneHead", s.laneHead), { sz: T.SIZE.body });
  periods.forEach((p, i) => label(ctx, slide, { x: gx + i * pw, y: b.y, w: pw - 0.02, h: 0.35 }, p, { fill: T.COLOR.tintHead, color: T.COLOR.textDark, sz: T.SIZE.body }));
  const lh = (b.h - 0.45 - (s.note ? 0.4 : 0)) / Math.max(lanes.length, 1);
  lanes.forEach((ln, i) => {
    const y = b.y + 0.45 + i * lh;
    label(ctx, slide, { x: b.x, y: y + 0.05, w: lw + 0.1 - T.PANEL.LABEL_GAP, h: lh - 0.1 }, `${i + 1}  ${ln.title}`, { sz: T.SIZE.body });
    slide.addShape(ctx.pres.ShapeType.line, { x: gx, y: y + lh - 0.02, w: gw, h: 0, line: { color: T.COLOR.borderLight, width: 0.5 } });
    // Compute bar height including gaps so the bar group stays above the lane divider
    const nTask = Math.max((ln.tasks || []).length, 1);
    const GAP = 0.04, PAD = 0.08;
    const avail = lh - 0.02 - PAD * 2 - GAP * (nTask - 1);
    const th = Math.max(0.18, Math.min(0.36, avail / nTask));
    (ln.tasks || []).forEach((t, j) => {
      const bx = { x: gx + (t.from || 0) * pw + 0.05, y: y + PAD + j * (th + GAP), w: ((t.to != null ? t.to : t.from || 0) - (t.from || 0) + 1) * pw - 0.1, h: th };
      slide.addText(A.runsOf(A.parasFromString(t.text, { sz: T.SIZE.tableDense, color: T.COLOR.textDark, align: "left" })), { ...bx, shape: ctx.pres.ShapeType.rect, fill: { color: T.COLOR.tintBg }, line: { color: T.COLOR.borderLight, width: 0.5 }, valign: "middle", margin: A.boxMargin([0.06, 0.01, 0.06, 0.01]), isTextBox: true, autoFit: false });
    });
  });
  if (s.note) A.text(slide, { x: b.x, y: b.y + b.h - 0.35, w: b.w, h: 0.3 }, noteText(s.note), { sz: T.SIZE.note, color: T.COLOR.textMuted, align: "center" });
  source(ctx, slide, sb);
}
/** Gantt: category and task columns + weekly grid by month. slots: {months:N, weeks:4, groups:[{name, tasks:[{name, from, to}]}], reports:[{name, at}], groupHead, taskHead, reportHead} */
function gantt(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const months = s.months || 4, weeks = s.weeks || 4;
  const groups = s.groups || [];
  // Task column head and report row group name (defaults are proposal terms; general planning decks change them via slots)
  const taskHead = LB.label("gantt", "taskHead", s.taskHead), reportHead = LB.label("gantt", "reportHead", s.reportHead), groupHead = LB.label("gantt", "groupHead", s.groupHead);
  const monthFormat = LB.label("gantt", "monthFormat", s.monthFormat);
  const head1 = [{ text: groupHead, rowspan: 2 }, { text: taskHead, rowspan: 2 }];
  for (let i = 0; i < months; i++) { head1.push({ text: LB.format(monthFormat, { n: i + 1 }), colspan: weeks }); for (let j = 1; j < weeks; j++) head1.push({ merged: true }); }
  const head2 = [{ merged: true }, { merged: true }, ...Array.from({ length: months * weeks }, (_, i) => `${(i % weeks) + 1}`)];
  const rowsOut = [];
  groups.forEach((g) => g.tasks.forEach((t, j) => {
    const r = [j === 0 ? { text: g.name, rowspan: g.tasks.length } : { merged: true }, t.name];
    for (let c = 0; c < months * weeks; c++) r.push(c >= t.from && c <= t.to ? { text: "", fill: T.COLOR.textMuted } : "");
    rowsOut.push(r);
  }));
  (s.reports || []).forEach((rp, j) => {
    const r = [j === 0 ? { text: reportHead, rowspan: s.reports.length } : { merged: true }, rp.name];
    for (let c = 0; c < months * weeks; c++) r.push(c === rp.at ? "●" : "");
    rowsOut.push(r);
  });
  const colW = [1.2, 2.3, ...Array(months * weeks).fill(0.55)];
  const nrow = rowsOut.length + 2;
  const rh = Math.min(0.32, b.h / nrow);
  const sum = colW.reduce((a, c) => a + c, 0), colw = colW.map((r) => +((b.w * r) / sum).toFixed(3));
  // On narrow pages, floor the category and task column widths at the longest word so words do not break mid-word, and take the shortfall evenly from the week columns
  const sz = T.SIZE.tableDense, pad = 2 * TABLE_CELL_PAD;
  const need = [
    Math.max(A.wordWidthIn(groupHead, sz, true), A.wordWidthIn([reportHead, ...groups.map((g) => g.name)], sz, false)) + pad,
    Math.max(A.wordWidthIn(taskHead, sz, true), A.wordWidthIn([...groups.flatMap((g) => g.tasks.map((t) => t.name)), ...(s.reports || []).map((rp) => rp.name)], sz, false)) + pad,
  ];
  if (colw[0] < need[0] || colw[1] < need[1]) {
    colw[0] = +Math.max(colw[0], need[0]).toFixed(3); colw[1] = +Math.max(colw[1], need[1]).toFixed(3);
    const wk = +((b.w - colw[0] - colw[1]) / (months * weeks)).toFixed(3);
    for (let i = 2; i < colw.length; i++) colw[i] = wk;
  }
  const mk = (c, head) => ({ fill: head ? T.COLOR.navy : (c && c.fill) || undefined, colspan: c && c.colspan, rowspan: c && c.rowspan, merged: c && c.merged, paras: [{ align: "center", runs: [{ t: typeof c === "string" ? c : (c && c.text) || "", sz: T.SIZE.tableDense, b: head, color: head ? T.COLOR.white : T.COLOR.textDark }] }] });
  // If the row height cap leaves body height unused, center the table vertically in the body
  A.table(slide, { x: b.x, y: b.y + Math.max(0, (b.h - rh * nrow) / 2), w: b.w, h: rh * nrow, table: { colw, rowh: Array(nrow).fill(rh), rows: [head1.map((c) => mk(c, true)), head2.map((c) => mk(c, true)), ...rowsOut.map((r) => r.map((c) => mk(c, false)))] } }, { sz: T.SIZE.tableDense });
  source(ctx, slide, sb);
}
/** Project organization chart: client agency, PM, quality control, advisory, module teams. slots: {client, pm, qa, advisory, teams:[{name, members:[], share}], note} */
/** Project organization chart. Vertical reporting line: client agency → project manager (PM) → quality manager (PL) → module teams.
 * The advisory committee (steering committee) links horizontally to the right of the PM. slots: {client, pm, pmTitle, qa, qaTitle, advisory, advisoryTitle, advisoryNote, teams[{name, members[], share}], note} */
function org(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb), S = ctx.S;
  const many = (s.teams || []).length > 6; // with many modules, compress the upper reporting line to free space below
  const cx = b.x + b.w / 2, bw = 2.78 * S.sx, h1 = many ? 0.36 : 0.44, h2 = many ? 0.5 : 0.64, vgap = many ? 0.22 : 0.33;
  const line = (x, y, w, h, dash) => slide.addShape(ctx.pres.ShapeType.line, { x, y, w, h, line: { color: T.COLOR.border, width: 1, dashType: dash ? "dash" : undefined } });
  const box = (x, y, w, h, tx, fill) => {
    const o = { x, y, w, h };
    if (fill === "navy") label(ctx, slide, o, tx, { sz: T.SIZE.body });
    else { frame(ctx, slide, o, { fill: fill === "tint" ? T.COLOR.tintHead : undefined }); A.text(slide, o, tx, { sz: T.SIZE.body, align: "center" }); }
  };
  // Level 1: client agency
  let y = b.y;
  box(cx - bw / 2, y, bw, h1, LB.label("org", "client", s.client), "navy");
  if (s.clientNote) { // the client role note sits as a bullet list to the right of the box; width and height are capped so it does not overlap the advisory box
    const items = Array.isArray(s.clientNote) ? s.clientNote : String(s.clientNote).split("\n").filter(Boolean);
    const nx = cx + bw / 2 + 0.04;
    const advY = y + h1 + vgap; // top of the advisory box
    const nw = Math.min(2.1 * S.sx, b.x + b.w - nx);
    const nh = Math.min(0.26 * items.length, Math.max(0.3, advY - (y - 0.13) - 0.06)); // height that stays clear of the advisory box
    bullets(ctx, slide, { x: nx, y: y - 0.13, w: nw, h: nh }, items, { noWarn: true, valign: "top", sz: T.SIZE.body });
  }
  line(cx, y + h1, 0, vgap);
  // Level 2: PM, with the advisory committee on the right
  y += h1 + vgap;
  box(cx - bw / 2, y, bw, h2, `${LB.label("org", "pmTitle", s.pmTitle)}\n${s.pm || "[인력A]"}`, "navy");
  if (s.advisory) {
    line(cx + bw / 2, y + h2 / 2, 1.0 * S.sx, 0);
    box(cx + bw / 2 + 1.0 * S.sx, y, bw, h2, `${LB.label("org", "advisoryTitle", s.advisoryTitle)}\n${s.advisory}`);
    if (s.advisoryNote) { // the advisory role note sits next to its box
      const items = Array.isArray(s.advisoryNote) ? s.advisoryNote : String(s.advisoryNote).split("\n").filter(Boolean);
      bullets(ctx, slide, { x: cx + bw / 2 + 1.0 * S.sx, y: y + h2 + 0.04, w: bw, h: 0.26 * items.length }, items, { noWarn: true, valign: "top", fixedSize: true, sz: T.SIZE.body });
    }
  }
  line(cx, y + h2, 0, vgap);
  // Level 3: quality manager (on the vertical line between the PM and the module teams)
  y += h2 + vgap;
  if (s.qa) { box(cx - bw / 2, y, bw, h2, `${LB.label("org", "qaTitle", s.qaTitle)}\n${s.qa}`, "tint"); line(cx, y + h2, 0, vgap + 0.03); y += h2 + vgap + 0.03; }
  // Level 4: module teams (4-6 in one row, 7 or more in two rows)
  const teams = s.teams || [];
  const n = Math.max(teams.length, 1);
  const rowN = n > 6 ? 2 : 1;
  const perRow = Math.ceil(n / rowN);
  const gap = perRow >= 5 ? 0.12 : perRow >= 4 ? 0.18 : 0.22;
  const areaH = b.y + b.h - y - 0.22 - (s.note ? 0.32 : 0);
  const rowGap = rowN > 1 ? 0.45 : 0.25; // two-row layouts leave room so the reporting line shows between rows
  const rowH = (areaH - (rowN - 1) * rowGap) / rowN;
  const tc = [];
  for (let r = 0; r < rowN; r++) cols({ x: b.x, y: y + 0.22 + r * (rowH + rowGap), w: b.w, h: rowH }, perRow, gap).forEach((c) => tc.push(c));
  // Per row, a horizontal connector plus vertical drops to each box. With two rows, extend the center spine to the lower row
  let prevRy = y;
  for (let r = 0; r < rowN; r++) {
    const rowBoxes = tc.slice(r * perRow, (r + 1) * perRow).filter((c, i) => teams[r * perRow + i]);
    if (!rowBoxes.length) continue;
    const ry = rowBoxes[0].y - 0.22;
    if (r > 0) line(cx, prevRy, 0, ry - prevRy); // run the center spine unbroken from the upper row connector to the lower row connector
    prevRy = ry;
    if (rowBoxes.length > 1) line(rowBoxes[0].x + rowBoxes[0].w / 2, ry, rowBoxes[rowBoxes.length - 1].x - rowBoxes[0].x, 0);
    rowBoxes.forEach((c) => line(c.x + c.w / 2, ry, 0, 0.22));
  }
  const headH = 0.42;
  tc.forEach((c, i) => {
    const t = teams[i]; if (!t) return;
    const hh = Math.min(headH, c.h * 0.32);
    label(ctx, slide, { x: c.x, y: c.y, w: c.w, h: hh }, t.name, { sz: perRow >= 5 ? T.SIZE.tableDense : T.SIZE.body, fill: T.COLOR.tintHead, color: T.COLOR.textDark });
    const bd = { x: c.x, y: c.y + hh, w: c.w, h: c.h - hh - (t.share ? 0.3 : 0) };
    frame(ctx, slide, bd);
    // Staff names are centered without bullets. A short box joins them on one line
    const mem = t.members || [];
    const small = bd.h < 0.7;
    const sz = perRow >= 5 || small ? T.SIZE.tableDense : T.SIZE.body;
    if (small) A.text(slide, bd, mem.join(", "), { sz, align: "center", valign: "middle" });
    else {
      // Share leftover height as gaps between staff lines, with a cap so they do not spread too far apart
      const need = mem.length * A.lineHeightIn(sz);
      const extra = Math.max(0, Math.min(T.PARA.paraGapMaxPt, ((bd.h - 0.16 - need) * 72) / Math.max(mem.length, 1)));
      const paras = mem.map((m, k) => ({ align: "center", spcBef: k ? extra : 0, runs: [{ t: m, sz, color: T.COLOR.textDark }] }));
      slide.addText(A.runsOf(paras), { x: bd.x, y: bd.y, w: bd.w, h: bd.h, isTextBox: true, valign: "middle", margin: A.boxMargin([0.06, 0.04, 0.06, 0.04]), autoFit: false });
    }
    // The share text is body information, so it uses the body floor (11pt); check_layout reads 10pt as note size
    if (t.share) A.text(slide, { x: c.x, y: bd.y + bd.h, w: c.w, h: 0.28 }, t.share, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textMuted, align: "center" });
  });
  if (s.note) A.text(slide, { x: b.x, y: b.y + b.h - 0.28, w: b.w, h: 0.28 }, noteText(s.note), { sz: T.SIZE.note, color: T.COLOR.textMuted, align: "left" });
  source(ctx, slide, sb);
}

/** 2-4 columns of staff cards: role, name slot, career, 3 track records. slots: {people:[{role, name, career:[], records:[], photo}], recordsHead} */
function staff_card(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const people = s.people || [];
  // With many people, drop photos to free text width (matches org charts with more modules)
  const dense = people.length >= 4;
  const pcols = cols(b, Math.max(people.length, 1), dense ? 0.12 : T.PANEL.GAP);
  const pxOf = (p) => (dense && !p.photo ? 0 : 1.0); // photo column width
  const careerBox = (c, p) => ({ x: c.x + 0.1 + pxOf(p), y: c.y + T.PANEL.TITLE_H + 0.5, w: c.w - 0.2 - pxOf(p), h: 0.75 });
  const recordBox = (c) => ({ x: c.x + 0.12, y: c.y + T.PANEL.TITLE_H + 1.68, w: c.w - 0.24, h: c.h - T.PANEL.TITLE_H - 1.8 });
  const copt = { noWarn: true, valign: "top" }, ropt = { noWarn: true, valign: "top", sz: dense ? T.SIZE.tableDense : T.SIZE.body };
  // Career cells and record cells each use one paragraph spacing
  const cgap = groupGap(pcols.map((c, i) => (people[i] ? careerBox(c, people[i]) : null)), people.map((p) => (p && p.career) || []), copt);
  const rgap = groupGap(pcols.map((c, i) => (people[i] ? recordBox(c) : null)), people.map((p) => (p && p.records) || []), ropt);
  pcols.forEach((c, i) => {
    const p = people[i]; if (!p) return;
    label(ctx, slide, { x: c.x, y: c.y, w: c.w, h: T.PANEL.TITLE_H }, p.role);
    frame(ctx, slide, { x: c.x, y: c.y + T.PANEL.TITLE_H, w: c.w, h: c.h - T.PANEL.TITLE_H });
    const px = pxOf(p);
    if (px) A.image(ctx.pres, slide, { x: c.x + 0.12, y: c.y + T.PANEL.TITLE_H + 0.12, w: 0.9, h: 1.1 }, p.photo, { label: "사진" });
    A.text(slide, { x: c.x + 0.1 + px, y: c.y + T.PANEL.TITLE_H + 0.12, w: c.w - 0.2 - px, h: 0.36 }, p.name || "[인력]", { sz: T.SIZE.panelHead, bold: true, align: px ? "left" : "center" });
    bullets(ctx, slide, careerBox(c, p), p.career || [], { ...copt, groupGapPt: cgap });
    label(ctx, slide, { x: c.x + 0.12, y: c.y + T.PANEL.TITLE_H + 1.35, w: c.w - 0.24, h: 0.28 }, LB.label("staff_card", "recordsHead", s.recordsHead), { fill: T.COLOR.tintHead, color: T.COLOR.textDark, sz: T.SIZE.body });
    bullets(ctx, slide, recordBox(c), p.records || [], { ...ropt, groupGapPt: rgap });
  });
  source(ctx, slide, sb);
}
/** SWOT: internal and external factors + matrix + strategic directions. slots: {S:[], W:[], O:[], T:[], so, st, wo, wt, labels:{S, W, O, T}} */
const SWOT_GAP = 0.5; // gap between factor columns and strategy cells (room for the arrows converging on the strategy cells)
const SWOT_ARROW = { w: 0.3, h: 0.34 }; // size of the arrows from factor cells to strategy cells
const SWOT_SIDE_SHARE = 0.27; // width share of one factor column (strategy cells take 0.46)
function swot(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  // The middle strategy area holds two cells side by side, so it is wider than the factor columns
  const sideW = (b.w - 2 * SWOT_GAP) * SWOT_SIDE_SHARE, midW = b.w - 2 * SWOT_GAP - 2 * sideW;
  const L = { x: b.x, y: b.y, w: sideW, h: b.h }, M = { x: b.x + sideW + SWOT_GAP, y: b.y, w: midW, h: b.h }, R = { x: M.x + midW + SWOT_GAP, y: b.y, w: sideW, h: b.h };
  const lb = LB.labels("swot", "labels", s.labels); // factor cell titles (changed through labels)
  // The four factor cells use one paragraph spacing (drawn in S, W, O, T order)
  const fboxes = rows(L, 2).concat(rows(R, 2));
  const fps = [{ head: lb.S, items: s.S, noWarn: true }, { head: lb.W, items: s.W, noWarn: true }, { head: lb.O, items: s.O, noWarn: true }, { head: lb.T, items: s.T, noWarn: true }];
  const fgap = panelsGap(fboxes, fps);
  fboxes.forEach((r, i) => panel(ctx, slide, r, { ...fps[i], groupGapPt: fgap }));
  // Arrows converging from the four factor cells on the middle strategy cells (left column points right, right column points left)
  const noLine = { color: "FFFFFF", width: 0, transparency: 100 };
  rows(L, 2).forEach((r) => {
    const cy = r.y + r.h / 2 - SWOT_ARROW.h / 2;
    slide.addShape(ctx.pres.ShapeType.rightArrow, { x: L.x + L.w + (SWOT_GAP - SWOT_ARROW.w) / 2, y: cy, w: SWOT_ARROW.w, h: SWOT_ARROW.h, fill: { color: T.COLOR.navy }, line: noLine });
    slide.addShape(ctx.pres.ShapeType.leftArrow, { x: M.x + M.w + (SWOT_GAP - SWOT_ARROW.w) / 2, y: cy, w: SWOT_ARROW.w, h: SWOT_ARROW.h, fill: { color: T.COLOR.navy }, line: noLine });
  });
  const q = [[lb.SO, s.so], [lb.WO, s.wo], [lb.ST, s.st], [lb.WT, s.wt]];
  const cell = (M.w - 0.1) / 2, ch = (M.h - 0.1) / 2;
  const qboxes = q.map((_, i) => ({ x: M.x + (i % 2) * (cell + 0.1), y: M.y + Math.floor(i / 2) * (ch + 0.1), w: cell, h: ch }));
  const qbody = (bx) => ({ x: bx.x, y: bx.y + 0.3, w: bx.w, h: bx.h - 0.3 });
  const qopt = { noWarn: true, valign: "middle" };
  const qgap = groupGap(qboxes.map(qbody), q.map(([, v]) => v || []), qopt); // the four strategy cells use one paragraph spacing
  q.forEach(([k, v], i) => {
    const bx = qboxes[i];
    frame(ctx, slide, bx);
    A.text(slide, { x: bx.x, y: bx.y, w: bx.w, h: 0.3 }, k, { sz: T.SIZE.body, bold: true, color: T.COLOR.navy, align: "center" });
    bullets(ctx, slide, qbody(bx), v || [], { ...qopt, groupGapPt: qgap });
  });
  source(ctx, slide, sb);
}
/** N card columns (title + body). slots: {cards:[{title, items|text}], point} */
function cards(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const cd = s.cards || [];
  const n = cd.length, ncol = n > 4 ? Math.ceil(n / 2) : n, nrow = n > 4 ? 2 : 1;
  const ptH = s.point ? 0.7 : 0;
  const cb = { x: b.x, y: b.y, w: b.w, h: b.h - ptH };
  const full = rows(cb, nrow).flatMap((r) => cols(r, ncol));
  const lists = cd.map((x) => (x && (x.items || x.text)) || []);
  const csz = groupSize(full.map((c) => ({ ...c, h: c.h - T.PANEL.TITLE_H })), cd.map((x) => (x && x.items) || []), PANEL_ITEM_SZ);
  const ssz = Math.max(T.SIZE.BODY_MIN, csz - 2);
  // Give all cards one width fitted to the longest line and center the card group and the 수행 Point callout (so short items leave no empty right side)
  const cw0 = Math.min(full[0].w, Math.max(...lists.map((l) => itemsNeedW(l, csz, ssz))) + 2 * T.PANEL.INSET + FIT_W_SLACK);
  // If the Point text does not fit in the band height, widen the card group and the band together (the band has the same width as the card group)
  const gw0 = cw0 * ncol + T.PANEL.GAP * (ncol - 1);
  const gw = s.point ? calloutW(ctx, s.point, gw0, b.w) : gw0;
  const cw = gw === gw0 ? cw0 : Math.min(full[0].w, (gw - T.PANEL.GAP * (ncol - 1)) / ncol), x0 = b.x + (b.w - gw) / 2;
  // Base card height on content height and center the cards plus 수행 Point group vertically in the body
  const rowAvail = full[0].h - T.PANEL.TITLE_H;
  const ch = T.PANEL.TITLE_H + panelBodyH(cd.map(() => cw), lists, csz, rowAvail, ssz);
  const gridH = ch * nrow + T.PANEL.GAP * (nrow - 1);
  const top = b.y + (b.h - gridH - ptH) / 2;
  const cboxes = rows({ x: x0, y: top, w: gw, h: gridH }, nrow).flatMap((r) => cols(r, ncol));
  const cps = cboxes.map((c, k) => (cd[k] ? { head: cd[k].title, items: cd[k].items, text: cd[k].text, noWarn: true, sz: csz, subSz: ssz } : null));
  const cgap = panelsGap(cboxes, cps); // cards also share one paragraph spacing
  cboxes.forEach((c, k) => { if (cps[k]) panel(ctx, slide, c, { ...cps[k], groupGapPt: cgap }); });
  if (s.point) callout(ctx, slide, { x: x0, y: top + gridH + 0.2, w: gw, h: 0.5 }, pointLabel(ctx, sb), s.point);
  source(ctx, slide, sb);
}
/** 4-5 methodology step chevrons + a description per step. slots: {steps:[{title, items:[]}], point} */
function steps(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const st = s.steps || [];
  // Fit box height to the item count and leave the rest empty so boxes do not stretch long and empty
  const maxItems = Math.max(...st.map((x) => (x.items || []).length), 1);
  const availH = b.h - 0.7 - (s.point ? 0.7 : 0);
  const need = 0.36 * maxItems + 0.34;
  // With few items, cap boxes at 1.3x the item height and center the whole group in the body so top and bottom margins are equal
  const bodyH = Math.min(availH, need * 1.3);
  const groupH = 0.7 + bodyH + (s.point ? 0.75 : 0);
  // body() already excludes the source line and footnote height, so center within the body height
  const shift = Math.max(0, (b.h - groupH) / 2);
  // stepLabel sets the chevron prefix; an empty string shows the title only
  const lab = LB.labelKeep("steps", "stepLabel", s.stepLabel);
  const chev = { x: b.x, y: b.y + shift, w: b.w, h: 0.55 };
  chevronRow(ctx, slide, chev, st.map((x, i) => (lab ? `${lab} ${i + 1}. ${x.title}` : x.title)));
  const scols = chevronCols(chev, Math.max(st.length, 1), b.y + 0.7 + shift, bodyH);
  const sopts = scols.map((c, i) => ({ noWarn: true, valign: "middle", gapPt: Math.min(14, Math.max(8, (c.h - 0.3) / Math.max(((st[i] && st[i].items) || []).length, 1) * 24)) }));
  // Step boxes use one paragraph spacing (the smallest of each box's base spacing plus its spare-height share)
  const sgap = groupGap(scols.map((c, i) => (st[i] ? c : null)), st.map((x) => (x && x.items) || []), sopts);
  scols.forEach((c, i) => { if (st[i]) { frame(ctx, slide, c); bullets(ctx, slide, c, st[i].items || [], { ...sopts[i], groupGapPt: sgap }); } });
  if (s.point) callout(ctx, slide, { x: b.x, y: Math.min(b.y + 0.7 + shift + bodyH + 0.25, b.y + b.h - 0.5), w: b.w, h: 0.5 }, pointLabel(ctx, sb), s.point); // right below the boxes
  source(ctx, slide, sb);
}

// Staff table column alignment (group, staff, share). The builder makes this fixed-column table, so right alignment of its quantity columns (staff, share) is set here
const PEOPLE_ALIGN = ["center", "right", "right"];
/** Company organization chart. slots: {ceo, advisory{name,note}, staff{name,note}, units[{name,teams[]}], people[{label,count,ratio}], peopleHead[], network[], leftHead, rightHead, netHead} */
function orgchart(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb), P = ctx.pres;
  const allUnits = s.units || [];
  const units = allUnits.slice(0, 8);
  if (allUnits.length > units.length) ctx.warn(`${allUnits.length} divisions: ${allUnits.length - units.length} over the limit of 8 not shown`);
  const people = (s.people || []).slice(0, 8);
  const net = (s.network || []).slice(0, 6);
  const netH = net.length ? 0.68 : 0;
  // With 7 or more divisions, widen the chart so team names fit on one line
  const leftW = people.length ? b.w * (units.length >= 7 ? 0.76 : 0.62) : b.w;
  const L = subhead(ctx, slide, { x: b.x, y: b.y, w: leftW, h: b.h - netH }, LB.label("orgchart", "leftHead", s.leftHead));
  const line = (x, y, w, h) => slide.addShape(P.ShapeType.line, { x, y, w, h, line: { color: T.COLOR.border, width: 1 } });
  const ceoW = Math.min(2.4, L.w * 0.26);
  const sideW = Math.min(2.2, L.w * 0.26);
  const cx = L.x + L.w / 2;
  const CEO_H = 0.42;
  // The division count sets division box height, and the whole row uses the same value
  const many = units.length >= 5;
  const unitH = many ? 0.5 : 0.36;
  const unitSz = many ? T.SIZE.tableDense : T.SIZE.body;
  // Show only division and team names and leave out division descriptions (keeps descriptions from mixing with names)
  const teamsOf = (u) => ((u && u.teams) || []).filter(Boolean);
  const maxTeams = Math.max(...units.map((u) => teamsOf(u).length), 0);
  const DROP_MIN = 0.4, DROP_MAX = 1.0;
  // With many divisions, narrow the column gap to free width for team names
  const colGap = units.length >= 7 ? 0.07 : 0.1;
  const colW = (L.w - colGap * (Math.max(units.length, 1) - 1)) / Math.max(units.length, 1);
  const teamInnerW = Math.max(0.3, colW - 0.1 - 0.18);
  // Measure the actual line count of team names to set box height (keeps long names from overflowing a one-line box)
  const teamLines = Math.max(1, ...units.flatMap((u) => teamsOf(u).map((x) => A.estimateLines(x, teamInnerW, T.SIZE.tableDense, true))));
  const TEAM_MIN = Math.max(0.28, teamLines * A.lineHeightIn(T.SIZE.tableDense) + 0.12);
  const TEAM_MAX = Math.max(TEAM_MIN + 0.04, 0.38);
  const GAP_MIN = 0.03, GAP_MAX = 0.14;
  const UNIT_PAD = 0.08;
  const need = (n, th, gap, drop) => drop + unitH + (n ? UNIT_PAD + n * th + (n - 1) * gap : 0);
  const avail = L.h - CEO_H;
  // Every team gets its own box; if space runs short, warn instead of abbreviating
  const showTeams = maxTeams;
  const minNeed = need(showTeams, TEAM_MIN, GAP_MIN, DROP_MIN);
  if (minNeed > avail) ctx.warn(`org chart vertical space short: needs ${minNeed.toFixed(2)}in, available ${avail.toFixed(2)}in. Reduce the team count or drop the partner network or staff table`);
  let teamH = TEAM_MIN, gap = GAP_MIN, drop = DROP_MIN;
  let slack = avail - need(showTeams, teamH, gap, drop);
  if (slack > 0 && showTeams) { const a = Math.min(TEAM_MAX - teamH, slack / showTeams); teamH += a; slack -= a * showTeams; }
  if (slack > 0 && showTeams > 1) { const a = Math.min(GAP_MAX - gap, slack / (showTeams - 1)); gap += a; slack -= a * (showTeams - 1); }
  if (slack > 0) { const a = Math.min(DROP_MAX - drop, slack); drop += a; slack -= a; }
  // If space runs short, fit the boxes inside the body band (the review tools flag any text that still overflows)
  if (minNeed > avail && showTeams) {
    const cap = (avail - DROP_MIN - unitH - UNIT_PAD - GAP_MIN * (showTeams - 1)) / showTeams;
    if (cap > 0.2) { teamH = Math.min(teamH, cap); gap = GAP_MIN; drop = DROP_MIN; }
  }
  // If height is still left, center the whole group vertically in the area under the subheading
  const top = L.y + Math.max(0, slack / 2);
  const ceoBox = { x: cx - ceoW / 2, y: top, w: ceoW, h: CEO_H };
  const sideMid = top + CEO_H / 2;
  slide.addText(A.runsOf(A.parasFromString(LB.label("orgchart", "ceo", s.ceo), { sz: T.SIZE.body, b: true, color: T.COLOR.white, align: "center" })),
    { ...ceoBox, shape: P.ShapeType.rect, fill: { color: T.COLOR.navy }, line: { color: T.COLOR.navy, width: 0.75 }, valign: "middle", margin: 0, isTextBox: true, autoFit: false });
  // Management support sits left of the CEO and the advisory committee right of the CEO on the same row, so the reporting line stays one horizontal line
  if (s.staff) {
    const sb2 = { x: L.x, y: top, w: sideW, h: CEO_H };
    frame(ctx, slide, sb2, { fill: T.COLOR.tintHead });
    A.text(slide, sb2, [s.staff.name, s.staff.note].filter(Boolean).join("\n"), { sz: T.SIZE.body, bold: true, align: "center", valign: "middle" });
    line(sb2.x + sb2.w, sideMid, ceoBox.x - (sb2.x + sb2.w), 0);
  }
  if (s.advisory) {
    const ab = { x: L.x + L.w - sideW, y: top, w: sideW, h: CEO_H };
    frame(ctx, slide, ab);
    A.text(slide, ab, [s.advisory.name, s.advisory.note].filter(Boolean).join("\n"), { sz: T.SIZE.body, bold: true, align: "center", valign: "middle" });
    line(ceoBox.x + ceoBox.w, sideMid, ab.x - (ceoBox.x + ceoBox.w), 0);
  }
  // Division row
  const unitY = top + CEO_H + drop;
  const branchY = unitY - 0.18;
  if (units.length) line(cx, top + CEO_H, 0, branchY - (top + CEO_H));
  const ub = cols({ x: L.x, y: unitY, w: L.w, h: unitH }, Math.max(units.length, 1), colGap);
  if (units.length > 1) line(ub[0].x + ub[0].w / 2, branchY, (ub[units.length - 1].x + ub[units.length - 1].w / 2) - (ub[0].x + ub[0].w / 2), 0);
  const teamTop = unitY + unitH + UNIT_PAD;
  units.forEach((u, i) => {
    const c = ub[i];
    line(c.x + c.w / 2, branchY, 0, unitY - branchY);
    frame(ctx, slide, c, { fill: T.COLOR.tintHead });
    const all = teamsOf(u);
    A.text(slide, c, u.name || "", { sz: unitSz, bold: true, align: "center", valign: "middle" });
    all.forEach((tname, j) => {
      const tb = { x: c.x + 0.05, y: teamTop + j * (teamH + gap), w: c.w - 0.1, h: teamH };
      frame(ctx, slide, tb);
      A.text(slide, tb, tname, { sz: T.SIZE.tableDense, bold: true, align: "center", valign: "middle" });
    });
  });
  // Staff composition table on the right
  if (people.length) {
    const R = subhead(ctx, slide, { x: b.x + leftW + 0.25, y: b.y, w: b.w - leftW - 0.25, h: b.h - netH }, LB.label("orgchart", "rightHead", s.rightHead));
    const head = LB.label("orgchart", "peopleHead", s.peopleHead);
    const rows2 = people.map((p) => [p.label || "", p.count || "", p.ratio || ""]);
    tableBlock(ctx, slide, R, { head, rows: rows2, align: PEOPLE_ALIGN });
  }
  // Network band at the bottom
  if (net.length) {
    const ny = b.y + b.h - netH + 0.06;
    const lw2 = Math.min(2.1, b.w * 0.18);
    const box = { x: b.x, y: ny + 0.12, w: b.w, h: 0.44 };
    label(ctx, slide, { x: box.x, y: box.y, w: lw2, h: box.h }, LB.label("orgchart", "netHead", s.netHead), { sz: T.SIZE.tableDense });
    const rest = { x: box.x + lw2 + 0.08, y: box.y, w: box.w - lw2 - 0.08, h: box.h };
    frame(ctx, slide, rest);
    cols(rest, net.length, 0.06).forEach((c, i) => A.text(slide, c, net[i], { sz: T.SIZE.body, bold: true, align: "center", valign: "middle" }));
  }
  source(ctx, slide, sb);
}

/** Output example (Illustrative tag): full-width table or image. slots: {title, table|image} */
function illustrative(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  // If the row height cap leaves the table short, center the title and table group vertically in the body
  const shift = s.table ? Math.max(0, (b.h - 0.45 - tableLayout(s.table, b.w, b.h - 0.45).total) / 2) : 0;
  A.text(slide, { x: b.x, y: b.y + shift, w: b.w, h: 0.35 }, LB.label("illustrative", "title", s.title), { sz: T.SIZE.panelHead, align: "center" });
  const box = { x: b.x, y: b.y + 0.45 + shift, w: b.w, h: b.h - 0.45 - 2 * shift };
  if (s.table) tableBlock(ctx, slide, box, s.table); else A.image(ctx.pres, slide, box, s.image, { label: "산출물 화면" });
  tag(ctx, slide, { x: b.x + 0.05, y: b.y + 0.05 + shift }, LB.label("illustrative", "tag", s.tag));
  source(ctx, slide, sb);
}
/** Summary: panels on top + conclusion band at the bottom. slots: {panels, conclusion} */
const CONC_ITEM_SZ = 14; // summary panel item font (same size as the panel title; weight sets the hierarchy)
const CONC_SUB_SZ = 12; // summary panel evidence font
const FIT_W_SLACK = 0.1; // box width slack that absorbs line width estimation error
function conclusion(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const pn = s.panels || [];
  const n = Math.max(pn.length, 1), bandH = 0.55, bandGap = 0.2, gap = T.PANEL.GAP;
  const lists = pn.map((p) => (p && (p.items || p.text)) || []);
  // Give all panels one width fitted to the longest line and center the panel group and the conclusion band (so short items leave no empty right side)
  const needW = Math.max(...lists.map((l) => itemsNeedW(l, CONC_ITEM_SZ, CONC_SUB_SZ))) + 2 * T.PANEL.INSET + FIT_W_SLACK;
  const pw = Math.min((b.w - gap * (n - 1)) / n, needW);
  const gw = pw * n + gap * (n - 1), x0 = b.x + (b.w - gw) / 2;
  // Base panel height on content height and center the panels plus conclusion band group vertically in the body
  const gh = T.PANEL.TITLE_H + panelBodyH(pn.map(() => pw), lists, CONC_ITEM_SZ, b.h - bandH - bandGap - T.PANEL.TITLE_H, CONC_SUB_SZ);
  const top = b.y + (b.h - gh - bandGap - bandH) / 2;
  const pboxes = cols({ x: x0, y: top, w: gw, h: gh }, n, gap);
  const pps = pboxes.map((c, i) => (pn[i] ? { ...pn[i], sz: CONC_ITEM_SZ, subSz: CONC_SUB_SZ, noWarn: true } : null));
  const pgap = panelsGap(pboxes, pps); // side-by-side panels also share one paragraph spacing
  pboxes.forEach((c, i) => { if (pps[i]) panel(ctx, slide, c, { ...pps[i], groupGapPt: pgap }); });
  label(ctx, slide, { x: x0, y: top + gh + bandGap, w: gw, h: bandH }, s.conclusion || "", { fill: T.COLOR.navyDeep, sz: T.SIZE.panelHead });
  source(ctx, slide, sb);
}
/** Free layout: places blocks at ratio coordinates (0-1) relative to the body band. blocks:[{kind, x, y, w, h, ...}] */
function free(ctx, slide, sb) {
  const b = body(ctx, sb);
  const abs = (k) => ({ x: b.x + k.x * b.w, y: b.y + k.y * b.h, w: k.w * b.w, h: k.h * b.h });
  ((sb.blocks || (sb.slots && sb.slots.blocks)) || []).forEach((k) => { // blocks may sit at the slide top level or in slots
    const bx = abs(k);
    switch (k.kind) {
      case "panel": panel(ctx, slide, bx, k); break;
      case "bullets": bullets(ctx, slide, bx, k.items, { noWarn: true, fill: k.fill, line: k.line }); break;
      case "text": A.text(slide, bx, k.text, { sz: k.sz || T.SIZE.body, bold: k.bold, align: k.align || "center", fill: k.fill, line: k.line ? { color: k.line, pt: T.PANEL.LINE_PT } : undefined }); break;
      case "label": label(ctx, slide, bx, k.text, { fill: k.fill, sz: k.sz }); break;
      case "box": frame(ctx, slide, bx, { fill: k.fill, line: k.line }); if (k.text) A.text(slide, bx, k.text, { sz: k.sz || T.SIZE.body, bold: k.bold, align: "center" }); break;
      case "table": tableBlock(ctx, slide, bx, k); break;
      case "chart": A.chart(ctx.pres, slide, bx, k.chart || k); break;
      case "chevron": chevronRow(ctx, slide, bx, k.steps, { h: bx.h, allChevron: k.allChevron }); break;
      case "callout": callout(ctx, slide, bx, k.label, k.text); break;
      case "image": A.image(ctx.pres, slide, bx, k.src, { caption: k.caption, label: k.label }); break;
      case "arrow": slide.addShape(ctx.pres.ShapeType[k.dir === "down" ? "downArrow" : "rightArrow"], { ...bx, fill: { color: T.COLOR.navy }, line: { color: "FFFFFF", width: 0, transparency: 100 } }); break;
      case "line": slide.addShape(ctx.pres.ShapeType.line, { ...bx, line: { color: k.color || T.COLOR.border, width: k.pt || 0.75, endArrowType: k.arrow ? "triangle" : undefined, dashType: k.dash ? "dash" : undefined } }); break;
      case "circle": slide.addText(A.runsOf(A.parasFromString(k.text || "", { sz: k.sz || T.SIZE.body, b: true, color: T.COLOR.white, align: "center" })), { ...bx, shape: ctx.pres.ShapeType.ellipse, fill: { color: k.fill || T.COLOR.navy }, line: { color: "FFFFFF", width: 0, transparency: 100 }, valign: "middle", margin: 0, isTextBox: true }); break;
      case "grid": { const cw = bx.w / k.cols, ch = bx.h / k.rows; (k.cells || []).forEach((c) => { const cb = { x: bx.x + c.c * cw + 0.03, y: bx.y + c.r * ch + 0.03, w: cw * (c.span || 1) - 0.06, h: ch - 0.06 }; if (c.fill === "navy") label(ctx, slide, cb, c.text, { sz: T.SIZE.body }); else { frame(ctx, slide, cb, { fill: c.fill === "tint" ? T.COLOR.tintHead : undefined }); A.text(slide, cb, c.text, { sz: T.SIZE.body, align: "center" }); } }); break; }
      default: ctx.warn(`free block kind ${k.kind} not supported`);
    }
  });
  source(ctx, slide, sb);
}
/** Area grid plus block combinations. Layout rules live in composite.js; per-method layouts live in references/recipes.md */
function compositeT(ctx, slide, sb) {
  C.composite(ctx, slide, sb, HELPERS);
}
function digest(ctx, slide, sb) {
  const S = ctx.S;
  A.text(slide, { x: S.bodyX, y: S.contentY, w: S.bodyW, h: 1.0 }, `[${sb.digestOf}] ${sb.digest || ""}`, { sz: T.SIZE.body, color: T.COLOR.textMuted, valign: "top", align: "left" });
}

const HELPERS = { body, cols, rows, label, frame, subhead, bulletsBlock: bullets, groupGap, panel, tableBlock, tableLayout, tableMetrics, chevronRow, chevronCols, callout, tag, source, pointLabel, noteRows };
module.exports = { SPEC, cover, contents, divider, end, digest, free, purpose, scope, features, strategy, process, module_overview, task, task_multi, bullets: bulletsT, table, chart_text, chart_two, compare, roadmap, gantt, org, orgchart, staff_card, swot, cards, steps, illustrative, conclusion, composite: compositeT,
  helpers: HELPERS };
