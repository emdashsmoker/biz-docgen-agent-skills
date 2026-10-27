"use strict";
// composite.js
// The composite template, which typesets analysis slides from an area grid and blocks.
// The model only sets grid ratios, block kinds and text; this file computes the coordinates.
// Grid: rows[{h, cols[]}] or cols[] (one row). Areas: regions[{title, block or blocks[], note}]
// Block kinds: table, bullets, text, stack, summary, labeled, grid, vsteps, chevrons, flow, flowchart, valuechain, porter, zones, logicmodel, goalsystem, house, canvas, market, matrix, pyramid, cycle, tree, governance, timeline, funnel, numbers, chart, image
// Blocks grow from natural height (the height their content needs) up to a capacity height (table rows, gaps between boxes, diagram size); leftover height goes to row gaps and the margin outside the group

const T = require("./tokens.js");
const A = require("./atoms.js");
const LB = require("./labels.js"); // Block label lookup (block field, then meta.labels, then assets/labels.json)

const GAP_COL = 0.3; // horizontal gap between areas
const GAP_COL_FLOW = 0.6; // horizontal gap between areas when an arrow goes between them
const GAP_ROW = 0.3; // vertical gap between rows
const GAP_ROW_MAX = 0.55; // gap cap when leftover height is shared between rows
const GAP_ROW_FLOW = 0.45; // vertical gap between rows when an arrow goes between them
const GAP_COL_DIV = 0.6, GAP_ROW_DIV = 0.5; // gaps when a divider line goes between cells (margin on both sides of the line)
const CAPTION_H = 0.34; // cell caption height (one bold left-aligned line)
const ELASTIC_MIN = 0.7; // floor a diagram row can shrink to (relative to the set height)
const ELASTIC_BLOCK_MIN = 1.9; // height floor for text box blocks and diagram blocks stacked in one cell (a height where chart labels do not overlap)
const SIBLING_STRETCH = 1.2; // factor a text box block may stretch to match a neighbor cell's height (relative to natural height)
const GAP_BLOCK = 0.2; // gap between blocks in one area
const GAP_ITEM = 0.14; // gap between boxes inside a block
const LABEL_GAP = T.PANEL.LABEL_GAP; // gap between a row label box and its content box
const GAP_ITEM_MAX = 0.36; // cap for the gap between boxes (when the cell has height to spare)
const HIER_GAP_X = 0.2, HIER_GAP_Y = 0.2; // horizontal and vertical gaps between cells in a hierarchy (grid style hierarchy)
const HIER_ROW_MIN = 0.5; // hierarchy row height floor
const CELL_GAP_V = 0.1; // vertical gap between label rows and grid rows (the 0.06 horizontal gap stays narrow so labels visibly pair with their content)
const CELL_GAP_V_MAX = 0.24, HIER_GAP_Y_MAX = 0.4; // row gap caps when the cell has height to spare (plain grid, hierarchy)
const CELL_GAP_H = 0.14; // horizontal gap between plain grid cells (same as the row label gap so bordered cells do not look joined)
const GRID_FLOW_GAP = 0.46; // gap between flow grid columns (the 0.28 right arrow width plus side margin)
const STEP_GAP = 0.26, STEP_GAP_MAX = 0.5; // arrow gap between vertical steps, and its cap
const FLOW_GAP = 0.42, FLOW_GAP_MAX = 0.6; // arrow gap between flow boxes, and its cap
const NOTE_H = 0.26; // area note (※) height
const CELL_SNAP = 0.3; // if a table cell is shorter than its neighbor by this much or less, raise the row height so top and bottom edges align
const BOTTOM_BAND_H = 0.5; // height of the conclusion band and the 수행 Point callout
const BOTTOM_GAP = 0.2;
const ARROW_W = 0.28, ARROW_H = 0.34; // arrows between areas
const CHART_MIN_H = 1.2, CHART_MIN_W = 2.4; // chart area floor that still fits a four-quadrant layout (smaller sizes overlap labels)
const PIE_ASPECT_MAX = 2.0; // pie chart cell width cap (relative to height)
const MATRIX_AXIS_PAD = 0.42; // room for matrix axis names
const MATRIX_ASPECT_MAX = 1.25; // matrix plane width cap (relative to height)
const MARKER_D = 0.3, MARKER_D_WIDE = 0.38; // matrix number marker diameter (single digit; all markers when a two-digit number is present)
const CIRCLED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"];

// ---------------------------------------------------------------- Measurement
const itemsOf = (x) => (x == null ? [] : Array.isArray(x.items) ? x.items : x.text != null ? [x.text] : typeof x === "string" ? [x] : []);
const textOf = (it) => (typeof it === "string" ? it : (it && it.text) || "");
/** Body text list. Text split by newlines counts as several items, each with its own bullet (newlines in labels and titles stay line breaks) */
const splitItems = (items) => (items || [])
  .flatMap((t) => (typeof t === "string" ? t.split("\n") : t && typeof t.text === "string" && t.text.includes("\n") ? t.text.split("\n").map((x) => ({ ...t, text: x })) : [t]))
  .filter((x) => x != null && (typeof x === "string" ? x.trim() !== "" : !(typeof x.text === "string" && x.text.trim() === "")));

/** Height a text list takes in a box of width w (includes bullet indent and paragraph gaps) */
function needH(items, w, sz, bullet) {
  // Only bullet item lists treat newlines as item separators (labels, titles and conclusion bands keep line breaks)
  const list = bullet ? splitItems(items) : (items || []).filter((x) => x != null && x !== "");
  if (!list.length) return 0;
  const indent = bullet && list.length > 1 ? T.PARA.bulletIndentIn : 0;
  const innerW = Math.max(0.3, w - 2 * T.PANEL.INSET - indent);
  const lines = list.reduce((a, t) => a + Math.max(1, A.estimateLines(textOf(t), innerW, sz)), 0);
  return lines * A.lineHeightIn(sz) + (list.length - 1) * (T.PARA.paraGapPt / 72) + 2 * T.PANEL.INSET;
}

/** Share available height in proportion to needed height. Shrinks proportionally when short and grows proportionally when there is extra */
function share(needs, avail, minEach) {
  const n = needs.map((v) => Math.max(minEach || 0.3, v));
  const sum = n.reduce((a, b) => a + b, 0) || 1;
  return n.map((v) => (v / sum) * avail);
}

/** Box column distribution. If available height exceeds the sum of natural heights, boxes keep natural height and leftover goes to the gaps between boxes first (capped at gapMax)
 *  Height left after the gaps hit the cap is shared among boxes in proportion. If height runs short, use the base gap and share in proportion to needed height */
function spread(needs, nats, avail, gap0, gapMax, minEach) {
  const n = needs.length;
  const nSum = nats.reduce((a, b) => a + b, 0);
  if (n < 2 || nSum + gap0 * (n - 1) >= avail) return { hs: share(needs, avail - gap0 * Math.max(0, n - 1), minEach), gap: gap0 };
  const gap = Math.min(gapMax, (avail - nSum) / (n - 1));
  const rest = avail - nSum - gap * (n - 1);
  return { hs: nats.map((v) => v + (rest * v) / (nSum || 1)), gap };
}

/** Row height equalization: if the tallest row's needed height fits within the average height, give every row the same height (removes size differences between rows with similar content) */
function evenRows(hs, needs) {
  if (hs.length < 2) return hs;
  const eq = hs.reduce((a, v) => a + v, 0) / hs.length;
  return Math.max(...needs) <= eq + 1e-6 ? hs.map(() => eq) : hs;
}

/** Common font size for boxes at the same level (from body 12pt down to the 11pt floor) */
function commonSize(boxes, lists) {
  for (let sz = T.SIZE.body; sz >= T.SIZE.BODY_MIN; sz--) {
    const ok = boxes.every((b, i) => !lists[i] || !lists[i].length || needH(lists[i], b.w, sz, true) <= b.h + 0.02);
    if (ok) return sz;
  }
  return T.SIZE.BODY_MIN;
}

/** Shared paragraph spacing of cells on the same tier (the same group as commonSize). Measures each cell with the same text split as writeItems and uses the smallest
 *  Cells not drawn as bullets (labels, cylinders and so on) are null in boxes */
function commonGap(H, boxes, lists, sz) {
  return H.groupGap(boxes, lists.map(splitItems), { sz, forceBullet: true });
}

// ---------------------------------------------------------------- Shared drawing
function writeItems(ctx, H, slide, box, items, sz, opt) {
  const o = opt || {};
  const list = splitItems(items);
  if (!list.length) return;
  if (list.length === 1 && !o.forceBullet) {
    A.text(slide, box, textOf(list[0]), { sz, bold: o.bold, align: o.align || "center", valign: "middle", color: o.color });
    return;
  }
  H.bulletsBlock(ctx, slide, box, list, { sz, noWarn: true, valign: o.valign || "middle", forceBullet: true, color: o.color, numbered: o.numbered, groupGapPt: o.groupGapPt });
}
function arrowShape(ctx, slide, cx, cy, dir, w, h) {
  const aw = w || ARROW_W, ah = h || ARROW_H;
  const ST = ctx.pres.ShapeType;
  const st = dir === "down" ? ST.downArrow : dir === "up" ? ST.upArrow : ST.rightArrow;
  const vertical = dir === "down" || dir === "up";
  const bw = vertical ? ah : aw, bh = vertical ? aw : ah;
  slide.addShape(st, { x: cx - bw / 2, y: cy - bh / 2, w: bw, h: bh, fill: { color: T.COLOR.navy }, line: { color: "FFFFFF", width: 0, transparency: 100 } });
}
/** Straight line between two points. Lines pointing left or up use flips so the arrowhead lands on the end point */
function seg(ctx, slide, x1, y1, x2, y2, arrow) {
  slide.addShape(ctx.pres.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1, line: { color: T.COLOR.textGray, width: 1, endArrowType: arrow ? "triangle" : undefined } });
}
function hline(ctx, slide, x, y, w, opt) {
  slide.addShape(ctx.pres.ShapeType.line, { x, y, w, h: 0, line: { color: T.COLOR.border, width: 1, dashType: opt && opt.dash ? "dash" : undefined, endArrowType: opt && opt.arrow ? "triangle" : undefined } });
}
/** Storage cylinder (elements where data accumulates, such as databases and document stores). The name sits in the area below the top face */
function dbBox(ctx, slide, b, text, sz) {
  slide.addText(A.runsOf(A.parasFromString(text || "", { sz, color: T.COLOR.textDark, align: "center" })), {
    x: b.x, y: b.y, w: b.w, h: b.h, shape: ctx.pres.ShapeType.can, fill: { color: T.COLOR.tintBg }, line: { color: T.COLOR.border, width: T.PANEL.LINE_PT },
    valign: "middle", margin: A.boxMargin([T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET]), isTextBox: true, autoFit: false, objectName: `adj:${DB_CAN_ADJ}`,
  });
}
const DB_CAN_ADJ = 25000; // cylinder top ellipse height (25% of the shape's short side)
const DB_ZONE_PAD_W = 0.8; // cylinder width in zone diagrams = name line width + side slack (keeps it from flattening into a disc in wide cells)
const isDb = (c) => !!(c && typeof c === "object" && c.shape === "db");
function vline(ctx, slide, x, y, h, opt) {
  slide.addShape(ctx.pres.ShapeType.line, { x, y, w: 0, h, line: { color: T.COLOR.border, width: 1, dashType: opt && opt.dash ? "dash" : undefined, endArrowType: opt && opt.arrow ? "triangle" : undefined } });
}

// ---------------------------------------------------------------- Blocks
const BLOCKS = {};

/** Table. {head, rows, colW?, align?} (without colW and align, column widths and alignment are computed automatically) */
BLOCKS.table = (ctx, H, slide, box, k) => {
  if (!k.rows || !k.rows.length) { ctx.warn("composite table has no rows"); return; }
  H.tableBlock(ctx, slide, box, k);
};

/** Bullet box. {head?, items} */
BLOCKS.bullets = (ctx, H, slide, box, k) => {
  const items = itemsOf(k);
  if (k.head) { H.panel(ctx, slide, box, { head: k.head, items, noWarn: true }); return; }
  H.frame(ctx, slide, box, { fill: k.fill === "tint" ? T.COLOR.tintBg : undefined });
  writeItems(ctx, H, slide, box, items, commonSize([box], [items]));
};

/** Message box. {text, style: navy | tint | box | plain} */
BLOCKS.text = (ctx, H, slide, box, k) => {
  const style = k.style || "box";
  const sz = k.sz || (box.h >= 0.7 ? T.SIZE.panelHead : T.SIZE.body);
  if (style === "navy") { H.label(ctx, slide, box, k.text || "", { sz }); return; }
  if (style === "tint") H.frame(ctx, slide, box, { fill: T.COLOR.tintHead });
  else if (style === "box") H.frame(ctx, slide, box);
  A.text(slide, box, k.text || "", { sz, bold: style !== "plain", align: k.align || "center", valign: "middle" });
};

/** Vertical stack of titled boxes. {items:[{head, items|text}]} */
BLOCKS.stack = (ctx, H, slide, box, k) => {
  const list = k.items || [];
  if (!list.length) return;
  const needs = list.map((x) => (x.head ? T.PANEL.HEAD_H : 0) + needH(itemsOf(x), box.w, T.SIZE.body, true));
  const nats = list.map((x) => (x.head ? T.PANEL.HEAD_H : 0) + grow(needH(itemsOf(x), box.w, T.SIZE.body, true), 0.4));
  const { hs, gap } = spread(needs, nats, box.h, GAP_ITEM, GAP_ITEM_MAX, 0.55);
  const bodies = hs.map((h, i) => ({ w: box.w, h: h - (list[i].head ? T.PANEL.HEAD_H : 0) }));
  const sz = commonSize(bodies, list.map(itemsOf));
  const cgap = commonGap(H, bodies, list.map(itemsOf), sz);
  let y = box.y;
  list.forEach((x, i) => {
    const b = { x: box.x, y, w: box.w, h: hs[i] };
    if (x.head) H.label(ctx, slide, { x: b.x, y: b.y, w: b.w, h: T.PANEL.HEAD_H }, x.head, { sz: T.SIZE.body, fill: x.headFill === "tint" ? T.COLOR.tintHead : undefined, color: x.headFill === "tint" ? T.COLOR.textDark : undefined });
    const bd = { x: b.x, y: b.y + (x.head ? T.PANEL.HEAD_H : 0), w: b.w, h: b.h - (x.head ? T.PANEL.HEAD_H : 0) };
    H.frame(ctx, slide, bd, { fill: x.fill === "tint" ? T.COLOR.tintBg : undefined });
    writeItems(ctx, H, slide, bd, itemsOf(x), sz, { groupGapPt: cgap });
    y += hs[i] + gap;
  });
};

/** Summary box. Holds a one-sentence conclusion band and matching items inside one navy border (the summary column right of per-area analysis cells)
 *  {lead, items:[{head, items|text}]} Thin dividers separate items, and item cells share leftover height equally */
const SUM_LEAD_MIN = 0.5; // conclusion band height floor (one 14pt conclusion line plus top and bottom margin)
const SUM_HEAD_GAP_PT = 3; // gap between an item title and its content (pt)
const SUM_RULE_INSET = 0.14; // side inset of the item dividers
const SUMMARY_FILL_H = 4.6; // summary box capacity height (set at or above body height so it follows the neighbor cell's height)
const sumLeadH = (k, w) => (k.lead ? Math.max(SUM_LEAD_MIN, needH([k.lead], w, T.SIZE.panelHead, false) + 0.08) : 0);
/** Needed height of an item cell: title line plus content text (box inset included) */
function sumItemNeed(x, w, sz) {
  const head = x.head ? A.estimateLines(x.head, w - 2 * T.PANEL.INSET, sz, true) * A.lineHeightIn(sz) + SUM_HEAD_GAP_PT / 72 : 0;
  const its = itemsOf(x);
  return head + (its.length ? needH(its, w, sz, true) : 2 * T.PANEL.INSET);
}
BLOCKS.summary = (ctx, H, slide, box, k) => {
  const list = k.items || [];
  const lh = sumLeadH(k, box.w);
  H.frame(ctx, slide, box, { line: T.COLOR.navy, pt: 1 });
  if (k.lead) H.label(ctx, slide, { x: box.x, y: box.y, w: box.w, h: lh }, k.lead, { sz: T.SIZE.panelHead });
  if (!list.length) return;
  const bodyY = box.y + lh, bodyH = box.h - lh;
  let sz = T.SIZE.body;
  const needAt = (s) => list.map((x) => sumItemNeed(x, box.w, s));
  while (sz > T.SIZE.BODY_MIN && needAt(sz).reduce((a, v) => a + v, 0) > bodyH + 0.02) sz--;
  const needs = needAt(sz), tot = needs.reduce((a, v) => a + v, 0);
  // Split item cells into equal heights (if the longest item does not fit, add equal shares of the leftover height to each needed height)
  const even = bodyH / list.length;
  const hs = tot > bodyH ? needs.map((v) => (v * bodyH) / tot) : Math.max(...needs) <= even ? needs.map(() => even) : needs.map((v) => v + (bodyH - tot) / list.length);
  // Horizontal fill: average share of the inner box width taken by bullet item lines (same floor as bullet boxes)
  const aw = box.w - 2 * T.PANEL.INSET - T.PARA.bulletIndentIn;
  const bl = list.flatMap((x) => (itemsOf(x).length > 1 ? itemsOf(x).map(textOf) : []));
  if (bl.length > 1 && !bl.some((t) => /\[[^\]]+\]/.test(t))) {
    const hfill = bl.reduce((a, t) => a + Math.min(1, A.lineWidthIn(t, sz, false) / aw), 0) / bl.length;
    const hmax = Math.max(...bl.map((t) => Math.min(1, A.lineWidthIn(t, sz, false) / aw)));
    const wrapped = bl.filter((t) => A.lineWidthIn(t, sz, false) > aw);
    if (wrapped.length) ctx.warn(`summary box items wrapped ${wrapped.length} ('${wrapped[0].slice(0, 12)}', shorten to one line or widen the column)`);
    const dump = globalThis.process.env.HFILL_DUMP; // "all" also records boxes that pass (for checking the fill distribution)
    if (dump && (dump === "all" || hfill < T.LIMIT.summaryFillMin || hmax < T.LIMIT.summaryMaxFillMin)) globalThis.process.stderr.write(`DUMP ${JSON.stringify({ id: ctx.sb.id, aw: +aw.toFixed(2), bw: +box.w.toFixed(2), sz, fill: +hfill.toFixed(3), max: +hmax.toFixed(3), items: bl })}\n`);
    if (hfill < T.LIMIT.summaryFillMin || hmax < T.LIMIT.summaryMaxFillMin) ctx.warn(`summary box text fill average ${Math.round(hfill * 100)}%, longest ${Math.round(hmax * 100)}% ('${bl[0].slice(0, 12)}' and ${bl.length - 1} more items; expand the text or narrow the column)`);
  }
  let y = bodyY;
  list.forEach((x, i) => {
    if (i > 0) hline(ctx, slide, box.x + SUM_RULE_INSET, y, box.w - 2 * SUM_RULE_INSET);
    const its = itemsOf(x);
    const paras = [];
    if (x.head) paras.push({ align: "left", runs: [{ t: x.head, sz, b: true, color: T.COLOR.navy }] });
    its.forEach((t, j) => paras.push({ align: "left", bullet: its.length > 1, indent: T.PARA.bulletIndentIn, spcBef: j === 0 ? (x.head ? SUM_HEAD_GAP_PT : 0) : T.PARA.paraGapPt, runs: [{ t: textOf(t), sz, color: T.COLOR.textDark }] }));
    slide.addText(A.runsOf(paras), { x: box.x, y, w: box.w, h: hs[i], isTextBox: true, valign: "middle", margin: A.boxMargin([T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET]), autoFit: false });
    y += hs[i];
  });
};

/** Rows of a left label and right content. {rows:[{label, items|text}], labelW} */
BLOCKS.labeled = (ctx, H, slide, box, k) => {
  const rows = k.rows || [];
  if (!rows.length) return;
  const lw = Math.min(k.labelW ? box.w * k.labelW : box.w * 0.28, 1.8);
  const cw = box.w - lw - 0.06;
  const nats = rows.map((r) => grow(Math.max(needH([r.label || ""], lw + 0.06 - LABEL_GAP, T.SIZE.body, false), needH(itemsOf(r), cw, T.SIZE.body, true)), 0.34));
  const rowNeeds = rows.map((r) => Math.max(needH([r.label || ""], lw + 0.06 - LABEL_GAP, T.SIZE.body, false), needH(itemsOf(r), cw, T.SIZE.body, true)));
  const sp = spread(rows.map((r) => needH(itemsOf(r), cw, T.SIZE.body, true)), nats, box.h, CELL_GAP_V, CELL_GAP_V_MAX, 0.34);
  const hs = evenRows(sp.hs, rowNeeds), gap = sp.gap;
  const sz = commonSize(hs.map((h) => ({ w: cw, h })), rows.map(itemsOf));
  const cgap = commonGap(H, hs.map((h) => ({ w: cw, h })), rows.map(itemsOf), sz);
  let y = box.y;
  rows.forEach((r, i) => {
    H.label(ctx, slide, { x: box.x, y, w: lw + 0.06 - LABEL_GAP, h: hs[i] }, r.label || "", { sz: T.SIZE.body });
    const cb = { x: box.x + lw + 0.06, y, w: cw, h: hs[i] };
    H.frame(ctx, slide, cb, { fill: r.fill === "tint" ? T.COLOR.tintBg : undefined });
    writeItems(ctx, H, slide, cb, itemsOf(r), sz, { align: r.align, groupGapPt: cgap });
    y += hs[i] + gap;
  });
};

/** Grid cell widths and needed height per row (shared so drawing and natural height measurement use the same calculation) */
const DIV_JOIN_TOL = 0.01; // position tolerance for joining per-row vertical dividers into one line (inches)
const GRID_LABEL_W_MAX = 1.6; // grid label column width cap
function gridGeom(k, box) {
  const rows = k.rows || [];
  const hasLabel = rows.some((r) => r.label);
  const ncol = Math.max(...rows.map((r) => (r.cells || []).reduce((a, c) => a + ((c && c.span) || 1), 0)), (k.head || []).length, 1);
  // hierarchy is a hierarchy chart such as a vision system or goal system: labels are plain text and wider gaps between cells separate the levels
  const hier = k.style === "hierarchy";
  const lg = hier ? HIER_GAP_X : 0.06; // between label and cell
  // Label column width floor: the width that fits the longest label word on one line (hierarchy labels are plain text with no margin; others use the navy label box width lw + lg - LABEL_GAP)
  const labelMin = hasLabel ? A.wordWidthIn(rows.map((r) => r.label || ""), T.SIZE.body, true) + (hier ? 0 : 2 * T.PANEL.LABEL_MG_X + LABEL_GAP - lg) : 0;
  const lw = hasLabel ? Math.min(Math.max(k.labelW ? box.w * k.labelW : box.w * (hier ? 0.1 : 0.18), labelMin), GRID_LABEL_W_MAX) : 0;
  const gx = box.x + (hasLabel ? lw + lg : 0);
  const gw = box.w - (hasLabel ? lw + lg : 0);
  const cg = hier ? HIER_GAP_X : k.flow ? GRID_FLOW_GAP : CELL_GAP_H;
  const vg = hier ? HIER_GAP_Y : CELL_GAP_V;
  const cw = (gw - cg * (ncol - 1)) / ncol;
  const headH = k.head ? 0.34 : 0;
  // Row sz is the set size for rows that carry hierarchy (vision, mission and so on). Rows without it use the common size
  const rowPt = (r) => (r.sz ? Math.max(T.SIZE.BODY_MIN, Math.min(r.sz, T.SIZE.headline)) : T.SIZE.body);
  const cellsOf = (r) => (r.cells || []).map((c) => ({ w: cw * ((c && c.span) || 1) + cg * (((c && c.span) || 1) - 1), items: itemsOf(typeof c === "string" ? { text: c } : c) }));
  const needs = rows.map((r) => Math.max(0.34, needH([r.label || ""], hier ? lw : lw + lg - LABEL_GAP, T.SIZE.body, false), ...cellsOf(r).map((c) => needH(c.items, c.w, rowPt(r), true))));
  return { rows, hier, hasLabel, lw, lg, gx, gw, cg, vg, cw, ncol, headH, rowPt, cellsOf, needs };
}

/** Contrast check for navy text on a tintHead fill. Called only by elements that actually draw that pair
 *  When a user color pair falls below the minimum, colors stay as specified and only a warning is left (user color choices take priority) */
function warnNavyOnTint(ctx, where) {
  const r = T.contrast(T.COLOR.navy, T.COLOR.tintHead);
  if (r < T.TINT_TEXT_CONTRAST_MIN) ctx.warn(`${where}: contrast of navy #${T.COLOR.navy} text on tintHead #${T.COLOR.tintHead} fill ${r.toFixed(1)} < ${T.TINT_TEXT_CONTRAST_MIN}`);
}

/** Label column plus cell grid. {head?:[], rows:[{label?, sz?, cells:[text | {text|items, fill, span, bold, color, shape}]}], labelW, flow}
 *  A cell shape value of db draws a storage cylinder
 *  With flow true, columns spread apart and a right arrow sits at the vertical middle of the row group (when columns follow in sequence, such as current, criteria, improved) */
BLOCKS.grid = (ctx, H, slide, box, k) => {
  if (!(k.rows || []).length) return;
  if (k.rows.some((r) => (r.cells || []).some((c) => c && c.fill === "tint" && c.color === "navy"))) warnNavyOnTint(ctx, "grid tint cell");
  const { rows, hier, hasLabel, lw, lg, gx, cg, vg: vg0, cw, ncol, headH, rowPt, cellsOf, needs } = gridGeom(k, box);
  const rowMin = hier ? HIER_ROW_MIN : 0.34;
  // The gap under the head row grows along with the row gaps
  const sp = spread(needs, needs.map((v) => grow(v, rowMin)), box.h - (k.head ? headH + vg0 : 0), vg0, hier ? HIER_GAP_Y_MAX : CELL_GAP_V_MAX, rowMin);
  const vg = sp.gap, hs = sp.hs;
  let y = box.y;
  if (k.head) {
    k.head.forEach((h, j) => H.label(ctx, slide, { x: gx + j * (cw + cg), y, w: cw, h: headH }, h, { sz: T.SIZE.body, fill: T.COLOR.tintHead, color: T.COLOR.textDark }));
    y += headH + vg0;
  }
  const rowsTop = y;
  const cellBoxes = [], cellLists = [];
  rows.forEach((r, i) => { if (!r.sz) cellsOf(r).forEach((c) => { cellBoxes.push({ w: c.w, h: hs[i] }); cellLists.push(c.items); }); });
  const sz = commonSize(cellBoxes, cellLists);
  const fitRow = (r, h) => { for (let p = rowPt(r); p > T.SIZE.BODY_MIN; p--) if (cellsOf(r).every((c) => needH(c.items, c.w, p, true) <= h + 0.02)) return p; return T.SIZE.BODY_MIN; };
  // Paragraph spacing is also one value per font group (per row for rows with their own sz). Label and cylinder cells are not bullets, so they are left out
  const textCell = (c, j, r, h) => { const cell = (r.cells || [])[j]; return cell && (cell.fill === "navy" || isDb(cell)) ? null : { w: c.w, h }; };
  const rowGap = (rs, z) => commonGap(H, rs.flatMap(([r, i]) => cellsOf(r).map((c, j) => textCell(c, j, r, hs[i]))), rs.flatMap(([r]) => cellsOf(r).map((c) => c.items)), z);
  const cgap = rowGap(rows.map((r, i) => [r, i]).filter(([r]) => !r.sz), sz);
  rows.forEach((r, i) => {
    if (hasLabel && hier) A.text(slide, { x: box.x, y, w: lw, h: hs[i] }, r.label || "", { sz: T.SIZE.body, bold: true, color: T.COLOR.textGray, align: "center", valign: "middle", mg: [0, 0, 0, 0] });
    else if (hasLabel) H.label(ctx, slide, { x: box.x, y, w: lw + lg - LABEL_GAP, h: hs[i] }, r.label || "", { sz: T.SIZE.body });
    const rsz = r.sz ? fitRow(r, hs[i]) : sz;
    const rgap = r.sz ? rowGap([[r, i]], rsz) : cgap;
    let col = 0;
    (r.cells || []).forEach((c) => {
      const cell = typeof c === "string" ? { text: c } : c || {};
      const span = cell.span || 1;
      const cb = { x: gx + col * (cw + cg), y, w: cw * span + cg * (span - 1), h: hs[i] };
      if (cell.fill === "navy") H.label(ctx, slide, cb, textOf(cell) || itemsOf(cell).join("\n"), { sz: rsz });
      else if (isDb(cell)) dbBox(ctx, slide, cb, textOf(cell), rsz);
      else { H.frame(ctx, slide, cb, { fill: cell.fill === "tint" ? T.COLOR.tintHead : undefined }); writeItems(ctx, H, slide, cb, itemsOf(cell), rsz, { bold: !!cell.bold, color: cell.color === "navy" ? T.COLOR.navy : undefined, numbered: !!cell.numbered, groupGapPt: rgap }); }
      col += span;
    });
    y += hs[i] + vg;
  });
  if (k.flow) {
    const cy = (rowsTop + y - vg) / 2;
    for (let j = 0; j < ncol - 1; j++) arrowShape(ctx, slide, gx + (j + 1) * cw + j * cg + cg / 2, cy, "right");
  }
};

/** Vertical steps. {steps:[{title, items|text}], arrows, label} Step labels on the left and descriptions on the right */
BLOCKS.vsteps = (ctx, H, slide, box, k) => {
  const st = k.steps || [];
  if (!st.length) return;
  const arrows = k.arrows !== false;
  const lw = Math.min(box.w * 0.34, 1.9);
  const cw = box.w - lw - 0.08;
  const needs = st.map((s) => Math.max(needH(itemsOf(s), cw, T.SIZE.body, true), needH([s.title || ""], lw + 0.08 - LABEL_GAP, T.SIZE.body, false)));
  const sp = spread(needs, needs.map((v) => grow(v, 0.42)), box.h, arrows ? STEP_GAP : GAP_ITEM, arrows ? STEP_GAP_MAX : GAP_ITEM_MAX, 0.42);
  const hs = evenRows(sp.hs, needs), gap = sp.gap;
  const sz = commonSize(hs.map((h) => ({ w: cw, h })), st.map(itemsOf));
  const cgap = commonGap(H, hs.map((h) => ({ w: cw, h })), st.map(itemsOf), sz);
  let y = box.y;
  st.forEach((s, i) => {
    const pre = k.label === "" ? "" : k.label ? `${k.label} ${i + 1}. ` : `${i + 1}. `;
    // If a title with a prefix (Round 1. and the like) runs past one line, break after the prefix so no word breaks mid-word
    const full = `${pre}${s.title || ""}`;
    const txt = pre && A.estimateLines(full, lw + 0.08 - LABEL_GAP - 0.1, T.SIZE.body) > 1 ? `${pre.trim()}\n${s.title || ""}` : full;
    H.label(ctx, slide, { x: box.x, y, w: lw + 0.08 - LABEL_GAP, h: hs[i] }, txt, { sz: T.SIZE.body });
    const cb = { x: box.x + lw + 0.08, y, w: cw, h: hs[i] };
    H.frame(ctx, slide, cb);
    writeItems(ctx, H, slide, cb, itemsOf(s), sz, { groupGapPt: cgap });
    if (arrows && i < st.length - 1) arrowShape(ctx, slide, box.x + (lw + 0.08 - LABEL_GAP) / 2, y + hs[i] + gap / 2, "down", 0.16, 0.2);
    y += hs[i] + gap;
  });
};

/** Horizontal chevrons plus a description box per step. {steps:[{title, items|text}]} */
BLOCKS.chevrons = (ctx, H, slide, box, k) => {
  const st = k.steps || [];
  if (!st.length) return;
  const anyItems = st.some((s) => itemsOf(s).length);
  const chH = anyItems ? Math.min(0.55, box.h * 0.3) : Math.min(0.8, box.h);
  const top = anyItems ? box.y : box.y + (box.h - chH) / 2;
  const chev = { x: box.x, y: top, w: box.w, h: chH };
  H.chevronRow(ctx, slide, chev, st.map((s) => s.title || ""), { sz: T.SIZE.body });
  if (!anyItems) return;
  // Align each box's right edge with the chevron shoulder (where the tip starts to narrow)
  const cs = H.chevronCols(chev, st.length, box.y + chH + 0.12, box.h - chH - 0.12);
  const sz = commonSize(cs, st.map(itemsOf));
  const cgap = commonGap(H, cs, st.map(itemsOf), sz);
  cs.forEach((c, i) => { H.frame(ctx, slide, c); writeItems(ctx, H, slide, c, itemsOf(st[i]), sz, { groupGapPt: cgap }); });
};

/** Flow of boxes joined by arrows. {nodes:[{title?, items|text, fill}], dir: h | v} */
BLOCKS.flow = (ctx, H, slide, box, k) => {
  const nodes = k.nodes || [];
  if (!nodes.length) return;
  const vertical = k.dir === "v";
  const headOf = (n) => (n.title && itemsOf(n).length ? T.PANEL.HEAD_H : 0);
  const sp = vertical ? spread(nodes.map((n) => headOf(n) + needH(itemsOf(n), box.w, T.SIZE.body, true)), nodes.map((n) => headOf(n) + grow(needH(n.title && !itemsOf(n).length ? [n.title] : itemsOf(n), box.w, T.SIZE.body, true), 0.4)), box.h, FLOW_GAP, FLOW_GAP_MAX, 0.4) : null;
  const gap = vertical ? sp.gap : FLOW_GAP;
  const parts = vertical
    ? (() => { let y = box.y; return sp.hs.map((h) => { const r = { x: box.x, y, w: box.w, h }; y += h + gap; return r; }); })()
    : H.cols(box, nodes.length, gap);
  const bodies = parts.map((p, i) => ({ w: p.w, h: p.h - (nodes[i].title && itemsOf(nodes[i]).length ? T.PANEL.HEAD_H : 0) }));
  const sz = commonSize(bodies, nodes.map(itemsOf));
  // Navy label boxes are not bullets, so they are left out of the spacing group
  const cgap = commonGap(H, bodies.map((bd, i) => (nodes[i].fill === "navy" && !(nodes[i].title && itemsOf(nodes[i]).length) ? null : bd)), nodes.map(itemsOf), sz);
  parts.forEach((p, i) => {
    const n = nodes[i];
    const its = itemsOf(n);
    if (n.title && its.length) {
      H.label(ctx, slide, { x: p.x, y: p.y, w: p.w, h: T.PANEL.HEAD_H }, n.title, { sz: T.SIZE.body });
      const bd = { x: p.x, y: p.y + T.PANEL.HEAD_H, w: p.w, h: p.h - T.PANEL.HEAD_H };
      H.frame(ctx, slide, bd, { fill: n.fill === "tint" ? T.COLOR.tintBg : undefined });
      writeItems(ctx, H, slide, bd, its, sz, { groupGapPt: cgap });
    } else if (n.fill === "navy") H.label(ctx, slide, p, n.title || textOf(its[0]), { sz });
    else { H.frame(ctx, slide, p, { fill: n.fill === "tint" ? T.COLOR.tintHead : undefined }); if (n.title) A.text(slide, p, n.title, { sz, bold: true, align: "center", valign: "middle" }); else writeItems(ctx, H, slide, p, its, sz, { groupGapPt: cgap }); }
    if (i < parts.length - 1) {
      if (vertical) arrowShape(ctx, slide, p.x + p.w / 2, p.y + p.h + gap / 2, "down", 0.2, 0.26);
      else arrowShape(ctx, slide, p.x + p.w + gap / 2, p.y + p.h / 2, "right", 0.22, 0.28);
    }
  });
};

/** 2×2 matrix. {x:{label, low, high}, y:{label}, quadrants:[top left, top right, bottom left, bottom right], items:[{label, x, y}], focus, legend}
 *  The y axis label is vertical text, so there are no end-label boxes and the direction goes in the label */
BLOCKS.matrix = (ctx, H, slide, box, k) => {
  const items = k.items || [];
  const legend = k.legend != null ? k.legend : items.length > 0;
  // Number markers: used with a legend box, or when a table on the same slide holds the numbered items (numbered)
  const numbered = k.numbered != null ? k.numbered : legend;
  const lgW = legend ? Math.min(box.w * 0.38, 3.0) : 0;
  const axisPad = MATRIX_AXIS_PAD;
  const ph = box.h - axisPad;
  // Cap the plane width at MATRIX_ASPECT_MAX times its height so the quadrants do not look squashed, and center the plane plus legend group in the cell
  const pw = Math.min(box.w - lgW - (legend ? 0.2 : 0) - axisPad, ph * MATRIX_ASPECT_MAX);
  const groupW = axisPad + pw + (legend ? 0.2 + lgW : 0);
  const ox = box.x + (box.w - groupW) / 2;
  const px = ox + axisPad, py = box.y, pW = pw, pH = ph;
  const qw = pW / 2, qh = pH / 2;
  const q = k.quadrants || [];
  if (k.focus != null && q[k.focus]) warnNavyOnTint(ctx, "matrix focus quadrant");
  [[0, 0], [1, 0], [0, 1], [1, 1]].forEach(([c, r], i) => {
    const qb = { x: px + c * qw, y: py + r * qh, w: qw, h: qh };
    slide.addShape(ctx.pres.ShapeType.rect, { ...qb, fill: { color: k.focus === i ? T.COLOR.tintHead : T.COLOR.white }, line: { color: T.COLOR.borderLight, width: 0.5 } });
    if (q[i]) A.text(slide, { x: qb.x + 0.06, y: r === 0 ? qb.y + 0.04 : qb.y + qb.h - 0.34, w: qb.w - 0.12, h: 0.3 }, q[i], { sz: T.SIZE.body, bold: true, color: k.focus === i ? T.COLOR.navy : T.COLOR.textGray, align: c === 0 ? "left" : "right", mg: [0, 0, 0, 0] });
  });
  // Axes: arrowheads on the left vertical axis and the bottom horizontal axis
  vline(ctx, slide, px, py + pH, -pH, { arrow: true });
  hline(ctx, slide, px, py + pH, pW + 0.05, { arrow: true });
  const xa = k.x || {}, ya = k.y || {};
  A.text(slide, { x: px, y: py + pH + 0.04, w: pW, h: 0.3 }, xa.label || "", { sz: T.SIZE.body, bold: true, align: "center", mg: [0, 0, 0, 0] });
  if (xa.low) A.text(slide, { x: px, y: py + pH + 0.04, w: 1.2, h: 0.3 }, xa.low, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textMuted, align: "left", mg: [0, 0, 0, 0] });
  if (xa.high) A.text(slide, { x: px + pW - 1.2, y: py + pH + 0.04, w: 1.2, h: 0.3 }, xa.high, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textMuted, align: "right", mg: [0, 0, 0, 0] });
  A.text(slide, { x: ox - 0.02, y: py, w: 0.34, h: pH }, ya.label || "", { sz: T.SIZE.body, bold: true, align: "center", vert: "vert270", mg: [0, 0, 0, 0] });
  // With two-digit numbers (10 or more), enlarge every marker to the same size so numbers do not wrap inside the circle
  const d = numbered && items.length >= 10 ? MARKER_D_WIDE : MARKER_D;
  items.forEach((it, i) => {
    const cx = px + Math.max(0.05, Math.min(0.95, it.x != null ? it.x : 0.5)) * pW;
    const cy = py + (1 - Math.max(0.05, Math.min(0.95, it.y != null ? it.y : 0.5))) * pH;
    slide.addText(A.runsOf(A.parasFromString(numbered ? String(i + 1) : it.label || "", { sz: T.SIZE.BODY_MIN, b: true, color: numbered ? T.COLOR.white : T.COLOR.textDark, align: "center" })),
      numbered ? { x: cx - d / 2, y: cy - d / 2, w: d, h: d, shape: ctx.pres.ShapeType.ellipse, fill: { color: T.COLOR.navy }, line: { color: "FFFFFF", width: 0.75 }, valign: "middle", margin: 0, isTextBox: true, wrap: d !== MARKER_D_WIDE }
        : { x: cx - 0.8, y: cy - 0.16, w: 1.6, h: 0.32, shape: ctx.pres.ShapeType.rect, fill: { color: T.COLOR.white }, line: { color: T.COLOR.navy, width: 0.75 }, valign: "middle", margin: 0, isTextBox: true });
  });
  if (legend && items.length) {
    // Size the legend box to the item count and center it vertically against the matrix
    const lh = Math.min(pH, needH(items.map((it, i) => `${i + 1}. ${it.label || ""}`), lgW, T.SIZE.body, false) + 0.1 * items.length + 0.1);
    const lb = { x: px + pW + 0.2, y: py + (pH - lh) / 2, w: lgW, h: lh };
    H.frame(ctx, slide, lb);
    const paras = items.map((it, i) => ({ align: "left", spcBef: i ? 6 : 0, runs: [{ t: `${i + 1}. ${it.label || ""}`, sz: T.SIZE.body, color: T.COLOR.textDark }] }));
    slide.addText(A.runsOf(A.fitParas(paras, lb.w - 0.2, lb.h - 0.16, T.SIZE.BODY_MIN)), { ...lb, isTextBox: true, valign: "middle", margin: A.boxMargin([0.1, 0.08, 0.1, 0.08]), autoFit: false });
  }
  return { x: ox, w: groupW }; // drawn horizontal range (used to match the width of the band below)
};

/** Pyramid. {levels:[top to bottom order], side?:[description per level]} */
const PYR_APEX_MG = 0.1; // total side margin of the apex triangle text
const PYR_APEX_TEXT_W = 0.6; // triangle width ratio at the height of the apex text box's lower line (a width where the line stays inside the triangle)
BLOCKS.pyramid = (ctx, H, slide, box, k) => {
  const lv = k.levels || [];
  if (!lv.length) return;
  const side = k.side || [];
  const pw = side.length ? box.w * 0.46 : box.w;
  const n = lv.length, gap = 0.06;
  const lh = (box.h - gap * (n - 1)) / n;
  // Level description cells use one paragraph spacing
  const sideItems = (v) => itemsOf(typeof v === "string" ? { text: v } : v);
  const sgap = commonGap(H, lv.map((_, i) => (side[i] ? { w: box.x + box.w - (box.x + pw + 0.2), h: lh } : null)), lv.map((_, i) => (side[i] ? sideItems(side[i]) : [])), T.SIZE.body);
  lv.forEach((t, i) => {
    const y = box.y + i * (lh + gap);
    const topW = (pw * i) / n, botW = (pw * (i + 1)) / n;
    const inset = (botW - topW) / 2;
    const x = box.x + (pw - botW) / 2;
    const ss = Math.min(botW, lh);
    const shape = i === 0 ? ctx.pres.ShapeType.triangle : ctx.pres.ShapeType.trapezoid;
    const fill = i === 0 ? T.COLOR.navy : [T.COLOR.navyPastel, T.COLOR.navyPastel2, T.COLOR.tintNavy, T.COLOR.tintHead][Math.min(i - 1, 3)];
    const dark = i <= 1;
    const opt = { x, y, w: botW, h: lh, shape, fill: { color: fill }, line: { color: "FFFFFF", width: 0.75 }, valign: i === 0 ? "bottom" : "middle", margin: A.boxMargin([0.05, 0.02, 0.05, 0.04]), isTextBox: true, autoFit: false };
    if (i > 0) opt.objectName = `adj:${Math.round((inset / ss) * 100000)}`;
    const paras = A.fitParas(A.parasFromString(t, { sz: T.SIZE.body, b: true, color: dark ? T.COLOR.white : T.COLOR.textDark, align: "center" }), Math.max(0.4, topW + inset - 0.1), lh - 0.04, T.SIZE.BODY_MIN);
    // The apex triangle's text area is half the base width, so on narrow pages where a word does not fit, overlay a base-width text box on the lower half of the triangle
    const apexTight = i === 0 && A.wordWidthIn(t, T.SIZE.BODY_MIN, true) > botW / 2 - PYR_APEX_MG;
    if (apexTight) {
      slide.addShape(shape, { x, y, w: botW, h: lh, fill: { color: fill }, line: { color: "FFFFFF", width: 0.75 } });
      const ap = A.fitParas(A.parasFromString(t, { sz: T.SIZE.body, b: true, color: T.COLOR.white, align: "center" }), botW * PYR_APEX_TEXT_W - PYR_APEX_MG, lh / 2, T.SIZE.BODY_MIN);
      A.text(slide, { x, y: y + lh / 2, w: botW, h: lh / 2 }, ap, { valign: "bottom", mg: [0, 0, 0, 0.04] });
    } else slide.addText(A.runsOf(paras), opt);
    if (side[i]) {
      const sx = box.x + pw + 0.2;
      hline(ctx, slide, box.x + pw / 2 + botW / 2 - inset / 2, y + lh / 2, sx - (box.x + pw / 2 + botW / 2 - inset / 2), { dash: true });
      const sb = { x: sx, y, w: box.x + box.w - sx, h: lh };
      H.frame(ctx, slide, sb);
      writeItems(ctx, H, slide, sb, sideItems(side[i]), T.SIZE.body, { groupGapPt: sgap });
    }
  });
};

/** Cycle. {stages:[{title, text?}], center} Stage boxes sit around a circle with arrowheads showing direction */
BLOCKS.cycle = (ctx, H, slide, box, k) => {
  const st = k.stages || [];
  const n = st.length;
  if (n < 2) return;
  const cx = box.x + box.w / 2, cy = box.y + box.h / 2;
  const nw = Math.min(box.w * 0.34, 2.4), nh = Math.min(box.h * 0.26, 1.1);
  const rx = Math.max(0.5, box.w / 2 - nw / 2), ry = Math.max(0.4, box.h / 2 - nh / 2);
  slide.addShape(ctx.pres.ShapeType.ellipse, { x: cx - rx, y: cy - ry, w: 2 * rx, h: 2 * ry, fill: { color: T.COLOR.white, transparency: 100 }, line: { color: T.COLOR.border, width: 1.25 } });
  const ang = (i) => -Math.PI / 2 + (2 * Math.PI * i) / n;
  // Direction arrowheads: triangles rotated to the tangent at the middle of the arc between neighboring stages
  for (let i = 0; i < n; i++) {
    const a = (ang(i) + ang(i + 1)) / 2;
    const ax = cx + rx * Math.cos(a), ay = cy + ry * Math.sin(a);
    const tangent = Math.atan2(ry * Math.cos(a), -rx * Math.sin(a)) * 180 / Math.PI;
    slide.addShape(ctx.pres.ShapeType.triangle, { x: ax - 0.1, y: ay - 0.09, w: 0.2, h: 0.18, rotate: Math.round(tangent + 90), fill: { color: T.COLOR.navy }, line: { color: T.COLOR.navy, width: 0.5 } });
  }
  if (k.center) {
    const cd = Math.min(rx, ry) * 0.9;
    slide.addText(A.runsOf(A.parasFromString(k.center, { sz: T.SIZE.panelHead, b: true, color: T.COLOR.navy, align: "center" })), { x: cx - cd / 2, y: cy - cd / 4, w: cd, h: cd / 2, isTextBox: true, valign: "middle", margin: 0 });
  }
  const bodies = st.map(() => ({ w: nw, h: nh - 0.32 }));
  const sz = commonSize(bodies, st.map((s) => (s.text ? [s.text] : [])));
  const cgap = commonGap(H, bodies, st.map((s) => (s.text ? [s.text] : [])), sz);
  st.forEach((s, i) => {
    const nx = cx + rx * Math.cos(ang(i)) - nw / 2, ny = cy + ry * Math.sin(ang(i)) - nh / 2;
    const hasText = !!s.text;
    H.label(ctx, slide, { x: nx, y: ny, w: nw, h: hasText ? 0.32 : nh }, s.title || "", { sz: T.SIZE.body });
    if (hasText) {
      const bd = { x: nx, y: ny + 0.32, w: nw, h: nh - 0.32 };
      H.frame(ctx, slide, bd);
      writeItems(ctx, H, slide, bd, [s.text], sz, { groupGapPt: cgap });
    }
  });
};

/** Tree. {root, children:[{text, children:[text]}], top?, sides?:[{side, text, dash}]} Two levels unfolding top to bottom
 *  top is the parent entity above root (joined by an arrow); sides are partner entities left and right of root (joined by a horizontal line, dashed when dash is true) */
const TREE_TOP_DROP = 0.3; // arrow span between the parent entity and root
const TREE_SIDE_GAP = 0.32; // horizontal line length between root and the side entities
const TREE_SIDE_W_MAX = 2.4; // side entity box width cap
const TREE_ROOT_H = 0.44, TREE_DROP = 0.36, TREE_L1_H = 0.44, TREE_L2_TOP = 0.22, TREE_L2_H = 0.42, TREE_L2_GAP = 0.1;
const TREE_DROP_EXTRA = 0.24, TREE_L2_GAP_EXTRA = 0.12; // extra caps for the level-1 connector and level-2 box gap when the cell has height to spare
const TREE_L2_H_MIN = 0.34; // level-2 box height floor when the cell is short (one 11pt line plus margin)
BLOCKS.tree = (ctx, H, slide, box, k) => {
  const ch = k.children || [];
  const rootH = TREE_ROOT_H, l1H = TREE_L1_H, l2H = TREE_L2_H;
  const rootW = Math.min(box.w * 0.4, 3.2);
  const rx = box.x + (box.w - rootW) / 2;
  const maxL2 = Math.max(0, ...ch.map((c) => (c.children || []).length));
  const topH = k.top ? rootH + TREE_TOP_DROP : 0;
  const needHAll = topH + rootH + TREE_DROP + l1H + (maxL2 ? TREE_L2_TOP + maxL2 * l2H + nGaps(maxL2) * TREE_L2_GAP : 0);
  // If the cell has height to spare, lengthen the level-1 connector and level-2 box gaps and align to the top
  const extra = Math.max(0, box.h - needHAll);
  const drop = TREE_DROP + Math.min(TREE_DROP_EXTRA, extra * 0.4);
  const l2Gap = maxL2 > 1 ? TREE_L2_GAP + Math.min(TREE_L2_GAP_EXTRA, (extra - (drop - TREE_DROP)) / (maxL2 - 1)) : TREE_L2_GAP;
  if (k.top) {
    H.label(ctx, slide, { x: rx, y: box.y, w: rootW, h: rootH }, k.top, { sz: T.SIZE.body, fill: T.COLOR.navyDeep });
    seg(ctx, slide, rx + rootW / 2, box.y + rootH, rx + rootW / 2, box.y + topH, true);
  }
  const top = box.y + topH;
  H.label(ctx, slide, { x: rx, y: top, w: rootW, h: rootH }, k.root || "", { sz: T.SIZE.body });
  (k.sides || []).forEach((sd) => {
    const sw = Math.min(TREE_SIDE_W_MAX, (box.w - rootW) / 2 - TREE_SIDE_GAP);
    const lines = Math.max(1, A.estimateLines(sd.text || "", sw - 2 * T.PANEL.INSET, T.SIZE.body));
    const sh = Math.max(rootH, lines * A.lineHeightIn(T.SIZE.body) + 2 * T.PANEL.INSET);
    const left = sd.side === "left";
    const sb = { x: left ? rx - TREE_SIDE_GAP - sw : rx + rootW + TREE_SIDE_GAP, y: top + rootH / 2 - sh / 2, w: sw, h: sh };
    H.frame(ctx, slide, sb);
    A.text(slide, sb, sd.text || "", { sz: T.SIZE.body, align: "center", valign: "middle" });
    hline(ctx, slide, left ? sb.x + sw : rx + rootW, top + rootH / 2, TREE_SIDE_GAP, { dash: !!sd.dash });
  });
  if (!ch.length) return;
  const cs = H.cols({ x: box.x, y: top + rootH + drop, w: box.w, h: l1H }, ch.length, 0.12);
  const busY = top + rootH + drop / 2;
  vline(ctx, slide, rx + rootW / 2, top + rootH, drop / 2);
  if (cs.length > 1) hline(ctx, slide, cs[0].x + cs[0].w / 2, busY, cs[cs.length - 1].x - cs[0].x);
  const spare = box.y + box.h - (top + rootH + drop + l1H + TREE_L2_TOP);
  const l2h = maxL2 ? Math.min(0.5, Math.max(TREE_L2_H_MIN, (spare - l2Gap * (maxL2 - 1)) / maxL2)) : l2H;
  cs.forEach((c, i) => {
    vline(ctx, slide, c.x + c.w / 2, busY, drop / 2);
    H.frame(ctx, slide, c, { fill: T.COLOR.tintHead });
    A.text(slide, c, ch[i].text || "", { sz: T.SIZE.body, bold: true, align: "center" });
    const kids = ch[i].children || [];
    if (!kids.length) return;
    const lx = c.x + 0.12;
    const y0 = c.y + c.h + TREE_L2_TOP;
    kids.forEach((t, j) => {
      const kb = { x: c.x + 0.26, y: y0 + j * (l2h + l2Gap), w: c.w - 0.26, h: l2h };
      H.frame(ctx, slide, kb);
      writeItems(ctx, H, slide, kb, [t], T.SIZE.BODY_MIN, { align: "left" });
      hline(ctx, slide, lx, kb.y + l2h / 2, 0.14);
    });
    vline(ctx, slide, lx, c.y + c.h, TREE_L2_TOP + (kids.length - 1) * (l2h + l2Gap) + l2h / 2);
  });
};

/** Governance diagram. A central vertical line (the R&D fund transfer and management path) with review and partner entities on the left and right
 *  {spine:[entity], sides:[{at, side, text, dash}]}
 *  spine is the top-to-bottom order of entities R&D funds pass through (the first entity has a navy fill)
 *  sides sit left or right at the same height as the at-th spine entity and join it with a horizontal line (dashed when dash is true) */
const GOV_NODE_H = 0.5, GOV_NODE_H_MAX = 0.62; // spine box height and cap
const GOV_GAP = 0.36, GOV_GAP_MAX = 0.6; // arrow span between spine boxes and cap
const GOV_SPINE_W = 0.36, GOV_SPINE_W_MAX = 2.4; // spine box width (ratio of cell width, cap)
const GOV_LINK_MIN = 0.3; // minimum connector length between side entity boxes and spine boxes
const GOV_SIDE_W_MAX = 2.0; // side entity box width cap
const GOV_TEXT_MG = A.TEXT_MG_IN[0]; // side text margin for spine and side entity boxes (same as text boxes with no set margin)
BLOCKS.governance = (ctx, H, slide, box, k) => {
  const sp = (k.spine || []).map(textOf);
  if (!sp.length) return;
  const n = sp.length;
  const need = n * GOV_NODE_H + nGaps(n) * GOV_GAP;
  const scale = Math.min(1, box.h / need);
  // Give leftover height to the arrow spans (up to the cap), then box height (up to the cap); the rest becomes vertical centering margin
  const gap = n > 1 ? Math.min(GOV_GAP_MAX, GOV_GAP * scale + Math.max(0, box.h - need) / (n - 1)) : 0;
  const nh = Math.min(GOV_NODE_H_MAX, Math.max(GOV_NODE_H * scale, (box.h - nGaps(n) * gap) / n));
  const top = box.y + Math.max(0, (box.h - n * nh - nGaps(n) * gap) / 2);
  const sides = (k.sides || []).filter((s) => s && sp[s.at] != null);
  // Word width floor: the width at which side entity boxes and spine boxes hold the longest word on one line at the body floor size (includes the default side margin of single-text boxes)
  const wordMin = (ts, bold) => (ts.length ? A.wordWidthIn(ts, T.SIZE.BODY_MIN, bold) + 2 * GOV_TEXT_MG : 0);
  const spineMin = wordMin(sp, true), sideMin = wordMin(sides.map(textOf), false);
  let sw = Math.min(box.w * GOV_SPINE_W, GOV_SPINE_W_MAX);
  let side = Math.min(GOV_SIDE_W_MAX, (box.w - sw) / 2 - GOV_LINK_MIN);
  // If side entity boxes are narrower than the word width, shrink the spine box down to its word width floor and give the width to the side boxes
  if (side < sideMin) {
    sw = Math.max(spineMin, box.w - 2 * (sideMin + GOV_LINK_MIN));
    side = Math.min(GOV_SIDE_W_MAX, (box.w - sw) / 2 - GOV_LINK_MIN);
    if (side < sideMin) ctx.warn(`governance cell width ${box.w.toFixed(2)}in may break side entity words mid-line (shorten entity names or widen the cell)`);
  }
  const sx = box.x + (box.w - sw) / 2;
  const nodes = sp.map((t, i) => ({ x: sx, y: top + i * (nh + gap), w: sw, h: nh }));
  const seen = new Set();
  sides.forEach((s) => { const key = `${s.at}${s.side}`; if (seen.has(key)) ctx.warn(`governance duplicate side entities in one spot (at ${s.at}, ${s.side})`); seen.add(key); });
  const sideBox = (s) => { const nd = nodes[s.at]; return { x: s.side === "left" ? box.x : box.x + box.w - side, y: nd.y, w: side, h: nh }; };
  // If a word is wider than its box at the height-based common size, step down one size at a time to the body floor
  const wordFits = (z) => nodes.every((nd, i) => A.wordWidthIn(sp[i], z, true) + 2 * GOV_TEXT_MG <= nd.w) && sides.every((s) => A.wordWidthIn(textOf(s), z, false) + 2 * GOV_TEXT_MG <= side);
  let sz = commonSize(nodes.concat(sides.map(sideBox)), sp.map((t) => [t]).concat(sides.map((s) => [textOf(s)])));
  while (sz > T.SIZE.BODY_MIN && !wordFits(sz)) sz--;
  // The top label box is not a bullet box, so it is left out of the spacing group
  const cgap = commonGap(H, nodes.map((nd, i) => (i ? nd : null)).concat(sides.map(sideBox)), sp.map((t) => [t]).concat(sides.map((s) => [textOf(s)])), sz);
  nodes.forEach((nd, i) => {
    if (i === 0) H.label(ctx, slide, nd, sp[i], { sz });
    else { H.frame(ctx, slide, nd, { fill: T.COLOR.tintHead }); writeItems(ctx, H, slide, nd, [sp[i]], sz, { bold: true, groupGapPt: cgap }); }
    if (i < n - 1) seg(ctx, slide, nd.x + nd.w / 2, nd.y + nd.h, nd.x + nd.w / 2, nodes[i + 1].y, true);
  });
  sides.forEach((s) => {
    const b = sideBox(s), nd = nodes[s.at];
    H.frame(ctx, slide, b);
    writeItems(ctx, H, slide, b, [textOf(s)], sz, { groupGapPt: cgap });
    const x1 = s.side === "left" ? b.x + b.w : nd.x + nd.w, x2 = s.side === "left" ? nd.x : b.x;
    hline(ctx, slide, x1, nd.y + nd.h / 2, x2 - x1, { dash: !!s.dash });
  });
};

/** Timeline. Time point markers sit on a horizontal time axis with event boxes below the markers
 *  {events:[{when, title?, items|text, mark}]}. An event with mark true (the current point) gets a filled marker and a tinted box */
const TL_WHEN_H = 0.3; // time point text line height
const TL_AXIS_GAP = 0.14; // between the time point text and the axis
const TL_DOT = 0.18; // time point marker diameter
const TL_DROP = 0.2; // between the axis and the event boxes
const TL_GAP = 0.2; // horizontal gap between event boxes
const TL_TITLE_H = 0.34; // title line height inside an event box
const TL_HEAD = TL_WHEN_H + TL_AXIS_GAP + TL_DROP; // fixed height above the event boxes
const tlColW = (w, n) => (w - TL_GAP * Math.max(0, n - 1)) / Math.max(1, n);
BLOCKS.timeline = (ctx, H, slide, box, k) => {
  const ev = k.events || [];
  if (!ev.length) return;
  const n = ev.length, cw = tlColW(box.w, n);
  const axisY = box.y + TL_WHEN_H + TL_AXIS_GAP;
  const top = axisY + TL_DROP;
  const cols = ev.map((_, i) => ({ x: box.x + i * (cw + TL_GAP), y: top, w: cw, h: box.y + box.h - top }));
  const hasTitle = ev.some((e) => e.title);
  const bodies = cols.map((c) => ({ w: c.w, h: c.h - (hasTitle ? TL_TITLE_H : 0) }));
  const sz = commonSize(bodies, ev.map(itemsOf));
  const cgap = commonGap(H, bodies, ev.map(itemsOf), sz);
  // Time axis: starts left of the first marker and ends in an arrowhead past the last marker to show the direction of time
  seg(ctx, slide, box.x, axisY, box.x + box.w, axisY, true);
  ev.forEach((e, i) => {
    const c = cols[i], cx = c.x + c.w / 2;
    A.text(slide, { x: c.x, y: box.y, w: c.w, h: TL_WHEN_H }, e.when || "", { sz: T.SIZE.panelHead, bold: true, color: T.COLOR.navy, align: "center", valign: "bottom", mg: [0, 0, 0, 0] });
    vline(ctx, slide, cx, axisY, TL_DROP);
    slide.addShape(ctx.pres.ShapeType.ellipse, { x: cx - TL_DOT / 2, y: axisY - TL_DOT / 2, w: TL_DOT, h: TL_DOT, fill: { color: e.mark ? T.COLOR.navy : T.COLOR.white }, line: { color: T.COLOR.navy, width: 1.25 } });
    H.frame(ctx, slide, c, { fill: e.mark ? T.COLOR.tintBg : undefined, line: e.mark ? T.COLOR.navy : undefined, pt: e.mark ? 1 : undefined });
    let bd = c;
    if (hasTitle) {
      A.text(slide, { x: c.x, y: c.y, w: c.w, h: TL_TITLE_H }, e.title || "", { sz: T.SIZE.body, bold: true, align: "center", valign: "middle" });
      hline(ctx, slide, c.x + 0.12, c.y + TL_TITLE_H, c.w - 0.24);
      bd = { x: c.x, y: c.y + TL_TITLE_H, w: c.w, h: c.h - TL_TITLE_H };
    }
    writeItems(ctx, H, slide, bd, itemsOf(e), sz, { forceBullet: itemsOf(e).length > 1, groupGapPt: cgap });
  });
};

/** Funnel. Stage bands narrowing from top to bottom, each matched at equal height with a description cell
 *  {head?:[column titles], stages:[{label, value, cells?:[items|text], items|text}]}. Upper stages (candidates) are light and lower stages (final) are dark
 *  With head, description cells split into columns under a head row (cells follow the head order). Without head, items form one column */
const FN_W_SHARE = 0.38; // funnel width relative to cell width
const FN_LEAD = 0.36; // width of the connector span between the funnel and the description cells
const FN_GAP = 0.08; // gap between stage bands
const FN_COL_GAP = 0.14; // gap between description cell columns
const FN_HEAD_H = 0.34, FN_HEAD_GAP = 0.1; // head row height and the gap below it
const FN_BAND_H = 0.62, FN_BAND_H_MAX = 0.9; // stage band height and cap
const FN_NARROW = 0.42; // bottom band's lower edge width ratio (relative to the top edge)
// Counts on light bands are highlighted in the theme color. With a custom theme whose band contrast falls below this value, they use the body text color
const FN_VALUE_CONTRAST_MIN = 3.0;
const fnDescW = (w) => w - w * FN_W_SHARE - FN_LEAD;
const fnCols = (k) => Math.max(1, (k.head || []).length);
const fnColW = (k, w) => (fnDescW(w) - FN_COL_GAP * (fnCols(k) - 1)) / fnCols(k);
const fnCells = (k, s) => (k.head ? (s.cells || []).map((c) => itemsOf(typeof c === "string" ? { text: c } : Array.isArray(c) ? { items: c } : c)) : [itemsOf(s)]);
const fnNeed = (k, s, w) => Math.max(0, ...fnCells(k, s).map((c) => needH(c, fnColW(k, w), T.SIZE.body, true)));
BLOCKS.funnel = (ctx, H, slide, box, k) => {
  const st = k.stages || [];
  if (st.length < 2) { ctx.warn("funnel needs 2 or more stages"); return; }
  const n = st.length, nc = fnCols(k);
  const fw = box.w * FN_W_SHARE, dx = box.x + fw + FN_LEAD, cw = fnColW(k, box.w);
  const headH = k.head ? FN_HEAD_H + FN_HEAD_GAP : 0;
  // Grow band height up to the cap (or the description height if longer) and leave the rest as top and bottom margin
  const need = Math.max(...st.map((s) => fnNeed(k, s, box.w)));
  const bh = Math.min(Math.max(FN_BAND_H_MAX, need), (box.h - headH - FN_GAP * (n - 1)) / n);
  const top = box.y + (box.h - headH - (bh * n + FN_GAP * (n - 1))) / 2 + headH;
  if (k.head) {
    const hy = top - headH;
    if (k.funnelHead) H.label(ctx, slide, { x: box.x, y: hy, w: fw, h: FN_HEAD_H }, k.funnelHead, { sz: T.SIZE.body, fill: T.COLOR.tintHead, color: T.COLOR.textDark });
    k.head.forEach((t, c) => H.label(ctx, slide, { x: dx + c * (cw + FN_COL_GAP), y: hy, w: cw, h: FN_HEAD_H }, t, { sz: T.SIZE.body, fill: T.COLOR.tintHead, color: T.COLOR.textDark }));
  }
  const ramp = T.COLOR.navyRamp || [T.COLOR.navy, T.COLOR.navyPastel, T.COLOR.navyPastel2, T.COLOR.tintHead];
  const fillOf = (i) => ramp[Math.max(0, Math.min(ramp.length - 1, Math.round(((n - 1 - i) * (ramp.length - 1)) / (n - 1))))];
  const darkOf = (i) => fillOf(i) === ramp[0] || fillOf(i) === ramp[1];
  const lists = st.map((s) => fnCells(k, s));
  const sz = commonSize(lists.flat().map(() => ({ w: cw, h: bh })), lists.flat());
  const cgap = commonGap(H, lists.flat().map(() => ({ w: cw, h: bh })), lists.flat(), sz);
  const cx = box.x + fw / 2;
  const span = bh * n + FN_GAP * (n - 1);
  const widthAt = (y) => fw * (1 - (1 - FN_NARROW) * ((y - top) / span));
  st.forEach((s, i) => {
    const y = top + i * (bh + FN_GAP);
    const wt = widthAt(y), wb = widthAt(y + bh);
    // Stage band: draw a trapezoid with top edge wt and bottom edge wb from free-form points (independent of shape adjust values)
    slide.addShape(ctx.pres.ShapeType.custGeom, { x: cx - wt / 2, y, w: wt, h: bh, fill: { color: fillOf(i) }, line: { color: T.COLOR.white, width: 0.75 },
      points: [{ x: 0, y: 0 }, { x: wt, y: 0 }, { x: (wt + wb) / 2, y: bh }, { x: (wt - wb) / 2, y: bh }, { close: true }] });
    const paras = [{ align: "center", runs: [{ t: s.label || "", sz: T.SIZE.body, b: true, color: darkOf(i) ? T.COLOR.white : T.COLOR.textDark }] }];
    const valueColor = darkOf(i) ? T.COLOR.white : T.contrast(T.COLOR.navy, fillOf(i)) >= FN_VALUE_CONTRAST_MIN ? T.COLOR.navy : T.COLOR.textDark;
    if (s.value) paras.push({ align: "center", runs: [{ t: s.value, sz: T.SIZE.panelHead, b: true, color: valueColor }] });
    slide.addText(A.runsOf(paras), { x: cx - wb / 2, y, w: wb, h: bh, isTextBox: true, valign: "middle", margin: 0 });
    // Description cells and connectors
    lists[i].forEach((its, c) => {
      const db = { x: dx + c * (cw + FN_COL_GAP), y, w: cw, h: bh };
      H.frame(ctx, slide, db);
      writeItems(ctx, H, slide, db, its, sz, { forceBullet: its.length > 1, groupGapPt: cgap });
    });
    for (let c = lists[i].length; c < nc; c++) H.frame(ctx, slide, { x: dx + c * (cw + FN_COL_GAP), y, w: cw, h: bh });
    hline(ctx, slide, cx + (wt + wb) / 4, y + bh / 2, dx - (cx + (wt + wb) / 4), { dash: true });
  });
};

/** Key figure tiles. {items:[{value, label, note?}]} */
BLOCKS.numbers = (ctx, H, slide, box, k) => {
  const its = k.items || [];
  if (!its.length) return;
  const cs = H.cols(box, its.length, 0.16);
  const vsz = box.h >= 1.3 ? T.SIZE.stat : 22;
  cs.forEach((c, i) => {
    const it = its[i];
    H.frame(ctx, slide, c);
    const vh = Math.min(0.6, c.h * 0.45);
    const block = vh + 0.32 + (it.note ? 0.26 : 0);
    const y = c.y + Math.max(0.04, (c.h - block) / 2);
    A.text(slide, { x: c.x, y, w: c.w, h: vh }, String(it.value || ""), { sz: vsz, bold: true, color: T.COLOR.navy, align: "center", mg: [0, 0, 0, 0] });
    A.text(slide, { x: c.x + 0.06, y: y + vh, w: c.w - 0.12, h: 0.32 }, it.label || "", { sz: T.SIZE.body, bold: true, align: "center", mg: [0, 0, 0, 0] });
    if (it.note) A.text(slide, { x: c.x + 0.06, y: y + vh + 0.32, w: c.w - 0.12, h: 0.26 }, it.note, { sz: T.SIZE.note, color: T.COLOR.textMuted, align: "center", mg: [0, 0, 0, 0] });
  });
};

/** Chart. {chart:{type, categories, series}} */
BLOCKS.chart = (ctx, H, slide, box, k) => {
  const spec = k.chart || k;
  if (box.h < CHART_MIN_H || box.w < CHART_MIN_W) ctx.warn(`composite chart area ${box.w.toFixed(2)}x${box.h.toFixed(2)}in (recommended floor ${CHART_MIN_W}x${CHART_MIN_H})`);
  // For pie charts the height sets the diameter, so narrow wide cells to keep the legend close to the circle
  const round = spec.type === "pie" || spec.type === "doughnut";
  const w = round ? Math.min(box.w, box.h * PIE_ASPECT_MAX) : box.w;
  A.chart(ctx.pres, slide, { ...box, x: box.x + (box.w - w) / 2, w }, spec);
};

/** Image. {src, caption, label} */
BLOCKS.image = (ctx, H, slide, box, k) => {
  const capH = k.caption ? 0.3 : 0;
  A.image(ctx.pres, slide, { x: box.x, y: box.y, w: box.w, h: box.h - capH }, k.src, { caption: k.caption, label: k.label || "이미지" });
};

/** Value chain. Top to bottom: support function bands (optional), stage chevrons, per-stage rows, common base band (optional)
 *  A functional value chain puts support function bands above the primary function chevrons to show support functions spanning every stage
 *  An industry value chain puts sub-sector rows under the supply stage chevrons and closes with a common base band
 *  {stageLabel, stages:[], support:{label, bands:[{title, items|text}]}, rows:[{label, cells:[text | {items|text, mark}]}], base:{label, text}, labelW}
 *  A mark cell uses a tint fill and bold text to flag a diagnosed segment (overlap, gap, weakness) */
const VC_CHEV_H = 0.6; // stage chevron height (one 14pt stage name line plus top and bottom margin)
const VC_GAP = 0.14; // gap between bands, chevrons and rows
const VC_BAND_TW = 1.5; // title cell width cap inside a support function band
function vcGeom(k, box, H) {
  const stages = k.stages || [];
  const lw = Math.min(box.w * (k.labelW || 0.13), 1.5);
  const gx = box.x + lw + 0.06, gw = box.w - lw - 0.06;
  const bands = (k.support && k.support.bands) || [];
  const rows = k.rows || [];
  const bandTW = Math.min(gw * 0.2, VC_BAND_TW);
  const cols0 = H.chevronCols({ x: gx, y: 0, w: gw, h: VC_CHEV_H }, Math.max(1, stages.length), 0, 1);
  const colW = cols0.map((c) => c.w);
  // Right edge of the cell grid (support function and common base bands align to it so only the chevron tips extend past)
  const gridW = cols0.length ? cols0[cols0.length - 1].x + cols0[cols0.length - 1].w - gx : gw;
  const cellItems = (c) => itemsOf(typeof c === "string" ? { text: c } : c);
  const needs = [
    ...bands.map((b) => Math.max(needH([b.title || ""], bandTW, T.SIZE.body, false), needH(itemsOf(b), gridW - bandTW, T.SIZE.body, true))),
    ...rows.map((r) => Math.max(needH([r.label || ""], lw + 0.06 - LABEL_GAP, T.SIZE.body, false), ...(r.cells || []).map((c, i) => needH(cellItems(c), colW[i] || colW[0], T.SIZE.body, true)))),
    ...(k.base ? [needH([k.base.text || ""], gridW, T.SIZE.body, false)] : []),
  ];
  const fixed = VC_CHEV_H + VC_GAP * (bands.length + rows.length + (k.base ? 1 : 0));
  return { stages, lw, gx, gw, bands, rows, bandTW, cellItems, needs, fixed, gridW };
}
BLOCKS.valuechain = (ctx, H, slide, box, k) => {
  const g = vcGeom(k, box, H);
  if (!g.stages.length) { ctx.warn("valuechain has no stages"); return; }
  const hs = share(g.needs, box.h - g.fixed, 0.4);
  const nb = g.bands.length, nr = g.rows.length;
  let y = box.y;
  if (nb) {
    const spanH = hs.slice(0, nb).reduce((a, h) => a + h, 0) + VC_GAP * (nb - 1);
    H.label(ctx, slide, { x: box.x, y, w: g.lw + 0.06 - LABEL_GAP, h: spanH }, LB.label("valuechain", "support.label", k.support.label), { sz: T.SIZE.body });
    // Support activity bands use one paragraph spacing
    const bgap = commonGap(H, g.bands.map((b, i) => ({ w: g.gridW - g.bandTW, h: hs[i] })), g.bands.map(itemsOf), T.SIZE.body);
    g.bands.forEach((b, i) => {
      H.frame(ctx, slide, { x: g.gx, y, w: g.gridW, h: hs[i] });
      H.label(ctx, slide, { x: g.gx, y, w: g.bandTW, h: hs[i] }, b.title || "", { sz: T.SIZE.body, fill: T.COLOR.tintHead, color: T.COLOR.textDark });
      writeItems(ctx, H, slide, { x: g.gx + g.bandTW, y, w: g.gridW - g.bandTW, h: hs[i] }, itemsOf(b), T.SIZE.body, { groupGapPt: bgap });
      y += hs[i] + VC_GAP;
    });
  }
  const chev = { x: g.gx, y, w: g.gw, h: VC_CHEV_H };
  H.label(ctx, slide, { x: box.x, y, w: g.lw + 0.06 - LABEL_GAP, h: VC_CHEV_H }, LB.label("valuechain", "stageLabel", k.stageLabel), { sz: T.SIZE.body });
  H.chevronRow(ctx, slide, chev, g.stages, { sz: T.SIZE.panelHead });
  y += VC_CHEV_H + VC_GAP;
  const rowHs = hs.slice(nb, nb + nr);
  const grid = g.rows.map((r, i) => H.chevronCols(chev, g.stages.length, 0, rowHs[i]));
  const sz = commonSize(grid.flat(), g.rows.flatMap((r) => g.stages.map((_, j) => g.cellItems((r.cells || [])[j] || ""))));
  const cgap = commonGap(H, grid.flat(), g.rows.flatMap((r) => g.stages.map((_, j) => g.cellItems((r.cells || [])[j] || ""))), sz);
  g.rows.forEach((r, i) => {
    H.label(ctx, slide, { x: box.x, y, w: g.lw + 0.06 - LABEL_GAP, h: rowHs[i] }, r.label || "", { sz: T.SIZE.body });
    grid[i].forEach((c, j) => {
      const cell = (r.cells || [])[j];
      const mark = cell && typeof cell === "object" && cell.mark;
      const cb = { x: c.x, y, w: c.w, h: rowHs[i] };
      H.frame(ctx, slide, cb, { fill: mark ? T.COLOR.tintHead : undefined });
      writeItems(ctx, H, slide, cb, g.cellItems(cell || ""), sz, { bold: !!mark, groupGapPt: cgap });
    });
    y += rowHs[i] + VC_GAP;
  });
  if (k.base) {
    const bh = hs[nb + nr];
    H.label(ctx, slide, { x: box.x, y, w: g.lw + 0.06 - LABEL_GAP, h: bh }, LB.label("valuechain", "base.label", k.base.label), { sz: T.SIZE.body });
    H.frame(ctx, slide, { x: g.gx, y, w: g.gridW, h: bh }, { fill: T.COLOR.tintBg });
    writeItems(ctx, H, slide, { x: g.gx, y, w: g.gridW, h: bh }, [k.base.text || ""], T.SIZE.body, { bold: true });
  }
  return { x: box.x, w: g.gx + g.gridW - box.x };
};

/** Classic value chain (Porter). Support activity bands on top, primary activity columns below, and a right arrowhead showing the direction of value creation
 *  {support:[{title, text or items}], primary:[{title, items, owner, mark}], supportLabel, primaryLabel, ownerLabel, tip}
 *  owner is the department in charge of each activity. An activity with mark true gets a tinted, bold owner cell (overlap or gap segments)
 *  tip is the text inside the arrowhead (e.g. business results). The right edges of the support bands and primary columns align with the arrowhead base */
const PT_TIP_W = 0.85; // arrowhead width
const PT_TIP_GAP = 0.1; // gap between the activity group and the arrowhead base
const PT_TIP_NEXT_GAP = 0.2; // gap between the arrowhead tip and the neighbor cell on the right
const PT_GAP = 0.08; // gap between primary activity columns and between areas
const PT_SUP_H = 0.3; // support activity band height (one line of text; thinner than primary activities to mark them as supporting)
const PT_SUP_GAP = 0.04; // gap between support activity bands
const PT_LABEL_W = 0.9; // left label column width cap (keeps width for the primary activity columns)
const PT_OWNER_H = 0.48; // owner cell height (fits "담당 부서" on two lines in a narrow label column)
const PT_TITLE_W = 1.35; // title cell width cap inside a support activity band
const PT_TIP_TEXT_RATIO = 0.62; // text box width relative to the arrowhead width (placed toward the base)
BLOCKS.porter = (ctx, H, slide, box, k) => {
  const sup = k.support || [], pri = k.primary || [];
  if (!pri.length) { ctx.warn("porter has no primary activities"); return; }
  // Label box width is lw + 0.06 - LABEL_GAP. Floor it at word width plus margin so label words fit on one line even on narrow pages (the PT_LABEL_W cap wins)
  const labels = [LB.label("porter", "supportLabel", k.supportLabel), LB.label("porter", "primaryLabel", k.primaryLabel), LB.label("porter", "ownerLabel", k.ownerLabel)];
  const lw = Math.min(PT_LABEL_W, Math.max(box.w * 0.1, A.wordWidthIn(labels, T.SIZE.body, true) + 2 * T.PANEL.LABEL_MG_X + LABEL_GAP - 0.06));
  // With a neighbor cell on the right, push the tip into the column gap and keep PT_TIP_NEXT_GAP from the neighbor (without one, stop at the cell's right edge)
  const tipEnd = box.x + box.w + (box.gapR ? Math.max(0, box.gapR - PT_TIP_NEXT_GAP) : 0);
  const gx = box.x + lw + 0.06, gw = tipEnd - PT_TIP_W - PT_TIP_GAP - gx;
  const n = pri.length, colW = (gw - PT_GAP * (n - 1)) / n;
  const titleW = Math.min(gw * 0.2, PT_TITLE_W);
  const hasOwner = pri.some((p) => p.owner);
  const headH = T.PANEL.TITLE_H;
  const measure = (sz) => {
    const supH = sup.map((st) => Math.max(PT_SUP_H, needH([st.title || ""], titleW, sz, false), needH(itemsOf(st), gw - titleW, sz, true)));
    const bodyH = Math.max(0.6, ...pri.map((p) => needH(itemsOf(p), colW, sz, true)));
    const total = supH.reduce((a, v) => a + v, 0) + PT_SUP_GAP * Math.max(0, sup.length - 1) + (sup.length ? PT_GAP : 0) + headH + bodyH + (hasOwner ? PT_GAP + PT_OWNER_H : 0);
    return { supH, bodyH, total };
  };
  let sz = T.SIZE.body, M = measure(sz);
  while (M.total > box.h + 0.01 && sz > T.SIZE.BODY_MIN) M = measure(--sz);
  if (M.total > box.h + 0.01) ctx.warn(`porter cell height ${box.h.toFixed(2)}in < content needs ${M.total.toFixed(2)}in (shorten the text)`);
  // All leftover height goes to the primary activity columns (support bands keep one-line height)
  const supH = M.supH;
  const bodyH = M.bodyH + Math.max(0, box.h - M.total);
  const top = box.y;
  let y = top;
  if (sup.length) {
    const span = supH.reduce((a, v) => a + v, 0) + PT_SUP_GAP * (sup.length - 1);
    // The support activity label is tinted and the primary activity label is navy, marking primary activities as the main area
    H.label(ctx, slide, { x: box.x, y, w: lw + 0.06 - LABEL_GAP, h: span }, labels[0], { sz: T.SIZE.body, fill: T.COLOR.tintHead, color: T.COLOR.textDark });
    const sgap = commonGap(H, supH.map((h) => ({ w: gw - titleW, h })), sup.map(itemsOf), sz); // support activity bands use one paragraph spacing
    sup.forEach((st, i) => {
      H.frame(ctx, slide, { x: gx, y, w: gw, h: supH[i] });
      H.label(ctx, slide, { x: gx, y, w: titleW, h: supH[i] }, st.title || "", { sz, fill: T.COLOR.tintHead, color: T.COLOR.textDark });
      writeItems(ctx, H, slide, { x: gx + titleW, y, w: gw - titleW, h: supH[i] }, itemsOf(st), sz, { groupGapPt: sgap });
      y += supH[i] + (i < sup.length - 1 ? PT_SUP_GAP : PT_GAP);
    });
  }
  H.label(ctx, slide, { x: box.x, y, w: lw + 0.06 - LABEL_GAP, h: headH + bodyH }, labels[1], { sz: T.SIZE.body });
  const colsB = H.cols({ x: gx, y, w: gw, h: headH + bodyH }, n, PT_GAP);
  const bsz = commonSize(colsB.map((c) => ({ w: c.w, h: bodyH })), pri.map(itemsOf));
  const bgap = commonGap(H, colsB.map((c) => ({ w: c.w, h: bodyH })), pri.map(itemsOf), bsz);
  colsB.forEach((c, i) => {
    H.label(ctx, slide, { x: c.x, y, w: c.w, h: headH }, pri[i].title || "", { sz: T.SIZE.body });
    const bd = { x: c.x, y: y + headH, w: c.w, h: bodyH };
    H.frame(ctx, slide, bd);
    writeItems(ctx, H, slide, bd, itemsOf(pri[i]), bsz, { groupGapPt: bgap });
  });
  y += headH + bodyH;
  if (hasOwner) {
    y += PT_GAP;
    H.label(ctx, slide, { x: box.x, y, w: lw + 0.06 - LABEL_GAP, h: PT_OWNER_H }, labels[2], { sz: T.SIZE.body });
    H.cols({ x: gx, y, w: gw, h: PT_OWNER_H }, n, PT_GAP).forEach((c, i) => {
      const mark = !!pri[i].mark;
      H.frame(ctx, slide, c, { fill: mark ? T.COLOR.tintHead : undefined });
      A.text(slide, c, pri[i].owner || "", { sz: bsz, bold: mark, color: T.COLOR.textDark, align: "center", valign: "middle" });
    });
    y += PT_OWNER_H;
  }
  // Arrowhead: base against the right edge of the activity group, tip at the group's vertical middle
  const tx = gx + gw + PT_TIP_GAP, th = y - top;
  slide.addShape(ctx.pres.ShapeType.custGeom, { x: tx, y: top, w: PT_TIP_W, h: th, points: [{ x: 0, y: 0 }, { x: PT_TIP_W, y: th / 2 }, { x: 0, y: th }, { close: true }], fill: { color: T.COLOR.navy }, line: { color: "FFFFFF", width: 0, transparency: 100 } });
  if (k.tip) A.text(slide, { x: tx, y: top + th / 2 - 0.4, w: PT_TIP_W * PT_TIP_TEXT_RATIO, h: 0.8 }, k.tip, { sz: T.SIZE.body, bold: true, color: T.COLOR.white, align: "center", valign: "middle", mg: [0, 0, 0, 0] });
  return { x: box.x, w: tx + PT_TIP_W - box.x };
};

/** Zone diagram. Component boxes stack vertically under each zone's head box, with dashed dividers between zones
 *  {zones:[{title, items:[text | {text, fill, shape}]}], band:{label, items:[]}}
 *  One name per component box. shape db draws a storage cylinder and fill tint marks a component of a different kind. band holds common elements spanning all zones (security and the like) */
const ZONE_HEAD_H = 0.4, ZONE_HEAD_GAP = 0.2; // zone head box height and the gap below it
const ZONE_ITEM_H = 0.42, ZONE_ITEM_GAP = 0.16, ZONE_ITEM_GAP_MAX = 0.3; // component box height and gaps
const ZONE_ITEM_W = 0.82; // component box width relative to zone width
const ZONE_GAP = 0.5; // gap between zones (room for the dashed divider)
const ZONE_BAND_H = 0.46, ZONE_BAND_GAP = 0.3; // common band height and the gap above it
function zonesNeed(k) {
  const maxN = Math.max(1, ...(k.zones || []).map((z) => (z.items || []).length));
  return ZONE_HEAD_H + ZONE_HEAD_GAP + maxN * ZONE_ITEM_H + (maxN - 1) * ZONE_ITEM_GAP + (k.band ? ZONE_BAND_GAP + ZONE_BAND_H : 0);
}
BLOCKS.zones = (ctx, H, slide, box, k) => {
  const zones = k.zones || [];
  if (!zones.length) { ctx.warn("zones has no zones"); return; }
  const bandH = k.band ? ZONE_BAND_GAP + ZONE_BAND_H : 0;
  const cols = H.cols({ x: box.x, y: box.y, w: box.w, h: box.h - bandH }, zones.length, ZONE_GAP);
  const maxN = Math.max(1, ...zones.map((z) => (z.items || []).length));
  const itemTop = box.y + ZONE_HEAD_H + ZONE_HEAD_GAP;
  const room = box.y + box.h - bandH - itemTop;
  const gap = maxN > 1 ? Math.max(ZONE_ITEM_GAP, Math.min(ZONE_ITEM_GAP_MAX, (room - maxN * ZONE_ITEM_H) / (maxN - 1))) : 0;
  zones.forEach((z, i) => {
    const c = cols[i];
    H.label(ctx, slide, { x: c.x, y: c.y, w: c.w, h: ZONE_HEAD_H }, z.title || "", { sz: T.SIZE.body, fill: T.COLOR.tintHead, color: T.COLOR.textDark });
    const iw = c.w * ZONE_ITEM_W;
    (z.items || []).forEach((it, j) => {
      const ib = { x: c.x + (c.w - iw) / 2, y: itemTop + j * (ZONE_ITEM_H + gap), w: iw, h: ZONE_ITEM_H };
      if (isDb(it)) { const dw = Math.min(iw, A.lineWidthIn(textOf(it), T.SIZE.body) + DB_ZONE_PAD_W); dbBox(ctx, slide, { ...ib, x: c.x + (c.w - dw) / 2, w: dw }, textOf(it), T.SIZE.body); return; }
      H.frame(ctx, slide, ib, { fill: it && it.fill === "tint" ? T.COLOR.tintHead : undefined });
      writeItems(ctx, H, slide, ib, [textOf(it)], T.SIZE.body);
    });
    if (i < zones.length - 1) vline(ctx, slide, c.x + c.w + ZONE_GAP / 2, c.y, c.h, { dash: true });
  });
  if (k.band) {
    const by = box.y + box.h - ZONE_BAND_H;
    const lw = Math.min(box.w * 0.12, 1.3);
    H.label(ctx, slide, { x: box.x, y: by, w: lw + 0.12 - LABEL_GAP, h: ZONE_BAND_H }, k.band.label || "", { sz: T.SIZE.body });
    const its = k.band.items || [];
    H.cols({ x: box.x + lw + 0.12, y: by, w: box.w - lw - 0.12, h: ZONE_BAND_H }, Math.max(1, its.length), ZONE_ITEM_GAP).forEach((c, j) => {
      H.frame(ctx, slide, c, { fill: T.COLOR.tintBg });
      writeItems(ctx, H, slide, c, [textOf(its[j])], T.SIZE.body);
    });
  }
};

/** Program logic model. Fixed layout of [Figure 3-3] in 「국가연구개발사업 예비타당성조사 수행 세부지침」 (2024, detailed guidelines for national R&D program preliminary feasibility studies)
 *  The vertical direction is the program logic flow; the horizontal direction is the program's time flow
 *  {issue, goal, beneficiary, input, activity, output, outcome, assumption, labels} each value is a text array. labels changes item titles with the same keys */
// Item title defaults are logicmodel.labels in assets/labels.json (overridden by meta.labels.logicmodel.labels, then the block labels)
const LM_ARROW_GAP = 0.26; // arrow gap between rows
const LM_PAD = 0.07; // inner padding of the dashed groups
const LM_HEAD_H = 0.28; // item title band height (lower than panel titles so all 8 items fit on one slide)
const LM_COL_GAP = 0.42; // horizontal arrow gap inside a group
const LM_GOAL_SHARE = 0.5; // goal box width share in the goal and beneficiary row (the guideline's original 1:1 layout)
BLOCKS.logicmodel = (ctx, H, slide, box, k) => {
  const LML = LB.labels("logicmodel", "labels", k.labels); // item titles (changed through labels)
  const its = (key) => [].concat(k[key] || []).filter(Boolean);
  const HH = LM_HEAD_H;
  const inW = box.w - 2 * LM_PAD;
  const wGoal = (inW - LM_COL_GAP) * LM_GOAL_SHARE, wBen = inW - LM_COL_GAP - wGoal;
  const w4 = (inW - 3 * LM_COL_GAP) / 4;
  const four = ["input", "activity", "output", "outcome"];
  const nd = (key, w) => needH(its(key), w, T.SIZE.body, true);
  // Full-width cells (issue, assumption) place items side by side in horizontal cells (so the right side of a full-width box is not empty)
  const wideCols = (key) => Math.max(1, its(key).length);
  const wideW = (key) => (box.w - LM_COL_GAP * (wideCols(key) - 1)) / wideCols(key);
  const ndWide = (key) => Math.max(0, ...its(key).map((t) => needH([t], wideW(key), T.SIZE.body, true)));
  const needs = [HH + ndWide("issue"), HH + Math.max(nd("goal", wGoal), nd("beneficiary", wBen)) + 2 * LM_PAD,
    HH + Math.max(...four.map((key) => nd(key, w4))) + 2 * LM_PAD, HH + ndWide("assumption")];
  const hs = share(needs, box.h - 3 * LM_ARROW_GAP, 0.6);
  const ys = hs.reduce((a, h, i) => a.concat(i ? a[i - 1] + hs[i - 1] + LM_ARROW_GAP : box.y), []);
  // Cell positions: [key, x, y, w, h]
  const cells = [["issue", box.x, ys[0], box.w, hs[0]],
    ["goal", box.x + LM_PAD, ys[1] + LM_PAD, wGoal, hs[1] - 2 * LM_PAD], ["beneficiary", box.x + LM_PAD + wGoal + LM_COL_GAP, ys[1] + LM_PAD, wBen, hs[1] - 2 * LM_PAD],
    ...four.map((key, i) => [key, box.x + LM_PAD + i * (w4 + LM_COL_GAP), ys[2] + LM_PAD, w4, hs[2] - 2 * LM_PAD]),
    ["assumption", box.x, ys[3], box.w, hs[3]]];
  const sz = commonSize(cells.map((c) => ({ w: c[3], h: c[4] - HH })), cells.map((c) => its(c[0])));
  // Paragraph spacing is measured per drawn cell (a wide cell is split into columns) and set to one value
  const wide = (key) => (key === "issue" || key === "assumption") && its(key).length > 1;
  const drawn = cells.flatMap(([key, , , w, h]) => (wide(key) ? its(key).map((t) => [{ w: wideW(key), h: h - HH }, [t]]) : [[{ w, h: h - HH }, its(key)]]));
  const cgap = commonGap(H, drawn.map((d) => d[0]), drawn.map((d) => d[1]), sz);
  [1, 2].forEach((r) => slide.addShape(ctx.pres.ShapeType.rect, { x: box.x, y: ys[r], w: box.w, h: hs[r], fill: { color: T.COLOR.white }, line: { color: T.COLOR.border, width: 1, dashType: "dash" } }));
  cells.forEach(([key, x, y, w, h]) => {
    H.label(ctx, slide, { x, y, w, h: HH }, LML[key], { sz: T.SIZE.body });
    const bd = { x, y: y + HH, w, h: h - HH };
    H.frame(ctx, slide, bd);
    if (wide(key)) {
      const cw = wideW(key);
      its(key).forEach((t, i) => {
        if (i) vline(ctx, slide, bd.x + i * (cw + LM_COL_GAP) - LM_COL_GAP / 2, bd.y + 0.08, bd.h - 0.16);
        writeItems(ctx, H, slide, { x: bd.x + i * (cw + LM_COL_GAP), y: bd.y, w: cw, h: bd.h }, [t], sz, { forceBullet: true, groupGapPt: cgap });
      });
    } else writeItems(ctx, H, slide, bd, its(key), sz, { forceBullet: its(key).length > 1, groupGapPt: cgap });
  });
  // Arrows between groups: down from issue, up from assumption
  arrowShape(ctx, slide, box.x + box.w / 2, ys[1] - LM_ARROW_GAP / 2, "down", 0.18, 0.2);
  arrowShape(ctx, slide, box.x + box.w / 2, ys[2] - LM_ARROW_GAP / 2, "down", 0.18, 0.2);
  arrowShape(ctx, slide, box.x + box.w / 2, ys[3] - LM_ARROW_GAP / 2, "up", 0.18, 0.2);
  // Time flow arrows inside a group
  arrowShape(ctx, slide, box.x + LM_PAD + wGoal + LM_COL_GAP / 2, ys[1] + hs[1] / 2, "right", 0.2, 0.24);
  [0, 1, 2].forEach((i) => arrowShape(ctx, slide, box.x + LM_PAD + (i + 1) * w4 + i * LM_COL_GAP + LM_COL_GAP / 2, ys[2] + hs[2] / 2, "right", 0.2, 0.24));
};

// ---------------------------------------------------------------- Program goal system and vision house (left row label column and hierarchy rows)
const LV_LABEL_W = 0.95; // row label column width
const LV_LABEL_GAP = 0.08; // between the row label column and the content
const LV_BAND_H = 0.36; // mission and core value band height
const LV_BAND_GAP = 0.06; // gap between vision house levels (kept narrow so it reads as one house)
/** Row label: bold gray text (the shapes on the right carry the hierarchy) */
function lvLabel(slide, x, y, h, text, w) {
  A.text(slide, { x, y, w: w || LV_LABEL_W, h }, text || "", { sz: T.SIZE.body, bold: true, color: T.COLOR.textGray, align: "center", valign: "middle", mg: [0, 0, 0, 0] });
}
/** Roof band: navy trapezoid with bold white text */
function lvRoof(ctx, slide, b, text) {
  const paras = A.fitParas(A.parasFromString(text || "", { sz: T.SIZE.panelHead, b: true, color: T.COLOR.white, align: "center" }), b.w - 2 * b.h, b.h - 0.04, T.SIZE.body);
  slide.addText(A.runsOf(paras), { x: b.x, y: b.y, w: b.w, h: b.h, shape: ctx.pres.ShapeType.trapezoid, fill: { color: T.COLOR.navyDeep }, line: { color: "FFFFFF", width: 0, transparency: 100 }, valign: "middle", margin: 0, isTextBox: true, autoFit: false });
}
/** Paragraph group box (holds title and bullet paragraphs in one text box) */
function lvParasBox(ctx, H, slide, b, paras, fill, line) {
  H.frame(ctx, slide, b, { fill, line });
  slide.addText(A.runsOf(paras), { x: b.x, y: b.y, w: b.w, h: b.h, isTextBox: true, valign: "middle", margin: A.boxMargin([T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET]), autoFit: false });
}
/** Needed height of a paragraph group (box inset included). Accounts for each paragraph's line count, bullet indent and space before */
function parasNeedH(paras, w) {
  const inner = w - 2 * T.PANEL.INSET;
  return paras.reduce((h, p) => h + Math.max(1, A.estimateLines(p.runs[0].t, inner - (p.bullet ? T.PARA.bulletIndentIn : 0), p.runs[0].sz, p.runs[0].b)) * A.lineHeightIn(p.runs[0].sz) + (p.spcBef || 0) / 72, 0) + 2 * T.PANEL.INSET;
}

/** Program goal system. Top to bottom: vision, program purpose and program goal bands, then columns of performance goals, strategic areas, and strategic tasks with sub-tasks
 *  {vision, purpose, goal, performance:[{title, quant, qual} or {title, items}], strategies:[{title, text}], tasks:[[{title, text}]], labels}. labels changes the row labels and the quant and qual prefixes
 *  The column count is the number of strategies. Performance goals, strategic areas and strategic tasks with the same index line up in one column
 *  Styling matches the hierarchy grid (grid style hierarchy): bold gray row labels, a navy vision cell, a tinted goal cell, white cells elsewhere, margins between levels */
// Row label and quant and qual prefix defaults are goalsystem.labels in assets/labels.json
const GS_BAND_MIN = 0.42; // vision, purpose and goal band height floor
const GS_BOX_GROW = 1.3; // growth factor cap for column boxes when the cell has height to spare
const GS_TASK_GAP_PT = 8; // paragraph gap between strategic tasks
BLOCKS.goalsystem = (ctx, H, slide, box, k) => {
  const L = LB.labels("goalsystem", "labels", k.labels);
  const perf = k.performance || [], strat = k.strategies || [], tasks = k.tasks || [];
  const n = Math.max(1, strat.length, perf.length, tasks.length);
  const lw = Math.min(box.w * 0.1, 1.6);
  const cx = box.x + lw + HIER_GAP_X, cw = box.w - lw - HIER_GAP_X;
  const colW = (cw - HIER_GAP_X * (n - 1)) / n;
  const indOf = (p) => (p.items ? itemsOf(p) : [p.quant ? `(${L.quant}) ${p.quant}` : "", p.qual ? `(${L.qual}) ${p.qual}` : ""].filter(Boolean));
  const perfParas = (p, sz) => [{ align: "center", runs: [{ t: p.title || "", sz, b: true, color: T.COLOR.navy }] }]
    .concat(indOf(p).map((t) => ({ align: "left", bullet: indOf(p).length > 1, indent: T.PARA.bulletIndentIn, spcBef: T.PARA.paraGapPt, runs: [{ t, sz, color: T.COLOR.textDark }] })));
  const stratParas = (st, sz) => [{ align: "center", runs: [{ t: st.title || "", sz, b: true, color: T.COLOR.textDark }] }]
    .concat(st.text ? [{ align: "center", spcBef: 2, runs: [{ t: st.text, sz, color: T.COLOR.textDark }] }] : []);
  const taskParas = (list, sz) => (list || []).flatMap((t, j) => [{ align: "left", spcBef: j ? GS_TASK_GAP_PT : 0, runs: [{ t: t.title || "", sz, b: true, color: T.COLOR.textDark }] }]
    .concat(t.text ? [{ align: "left", bullet: true, buChar: "-", indent: T.PARA.bulletIndentIn, spcBef: 2, runs: [{ t: t.text, sz, color: T.COLOR.textGray }] }] : []));
  const bands = [["vision", T.SIZE.panelHead], ["purpose", T.SIZE.body], ["goal", T.SIZE.body]].filter(([key]) => k[key]);
  const measure = (sz) => {
    const bandH = bands.map(([key, bsz]) => Math.max(GS_BAND_MIN, needH([k[key]], cw, Math.min(bsz, sz + (bsz - T.SIZE.body)), false)));
    const colRow = (paras) => (paras.length ? Math.max(...paras.map((ps) => parasNeedH(ps, colW))) : 0);
    const rowsH = [colRow(perf.map((p) => perfParas(p, sz))), colRow(strat.map((st) => stratParas(st, sz))), colRow(tasks.map((c) => taskParas(c, sz)))];
    const nRow = bandH.length + rowsH.filter((h) => h > 0).length;
    return { bandH, rowsH, nRow, total: bandH.reduce((a, v) => a + v, 0) + rowsH.reduce((a, v) => a + v, 0) + HIER_GAP_Y * Math.max(0, nRow - 1) };
  };
  let sz = T.SIZE.body, M = measure(sz);
  while (M.total > box.h + 0.01 && sz > T.SIZE.BODY_MIN) M = measure(--sz);
  if (M.total > box.h + 0.01) ctx.warn(`goalsystem cell height ${box.h.toFixed(2)}in < content needs ${M.total.toFixed(2)}in (shorten the text or adjust row ratios)`);
  // Leftover height: widen level gaps up to the cap, grow column boxes up to the factor cap, and leave the rest as top and bottom margin
  let slack = Math.max(0, box.h - M.total);
  const nGap = Math.max(0, M.nRow - 1);
  const gap = HIER_GAP_Y + (nGap ? Math.min(HIER_GAP_Y_MAX - HIER_GAP_Y, slack / nGap) : 0);
  slack -= (gap - HIER_GAP_Y) * nGap;
  const colSum = M.rowsH.reduce((a, v) => a + v, 0);
  const growK = colSum ? Math.min(GS_BOX_GROW - 1, slack / colSum) : 0;
  const rowsH = M.rowsH.map((h) => h * (1 + growK));
  slack -= colSum * growK;
  let y = box.y + slack / 2;
  const rowLabel = (h, text) => lvLabel(slide, box.x, y, h, text, lw);
  bands.forEach(([key, bsz], i) => {
    const b = { x: cx, y, w: cw, h: M.bandH[i] };
    rowLabel(b.h, L[key]);
    if (key === "vision") H.label(ctx, slide, b, k.vision, { sz: Math.min(bsz, sz + 2) });
    else { H.frame(ctx, slide, b, { fill: key === "goal" ? T.COLOR.tintHead : undefined }); A.text(slide, b, k[key], { sz, bold: key === "goal", color: key === "purpose" ? T.COLOR.navy : T.COLOR.textDark, align: "center", valign: "middle" }); }
    y += b.h + gap;
  });
  const colRow = (h, label, list, parasOf) => {
    if (!h) return;
    rowLabel(h, label);
    H.cols({ x: cx, y, w: cw, h }, n, HIER_GAP_X).forEach((c, i) => { if (list[i]) lvParasBox(ctx, H, slide, c, parasOf(list[i], sz)); });
    y += h + gap;
  };
  colRow(rowsH[0], L.performance, perf, perfParas);
  colRow(rowsH[1], L.strategies, strat, stratParas);
  colRow(rowsH[2], L.tasks, tasks, taskParas);
};

/** Vision house. Lays out a mission band, vision roof, strategic goal pillar heads, strategic task pillar bodies and a core value base (optional) as one house
 *  {mission, vision, pillars:[{title, items}], base:[text], labels, numbered}. The pillar group is inset from the roof on both sides to form eaves
 *  Unless numbered is false, strategic goals get 1. and strategic tasks get 1-1. prefixes (the numbers replace bullets)
 *  base is split into one cell per core value; without it, a floor band closes the bottom of the pillars */
// Row label defaults are house.labels in assets/labels.json
const HOUSE_ROOF_H = 0.5; // vision roof height
const HOUSE_EAVE = 0.18; // side inset of the pillar group (eaves)
const HOUSE_PILLAR_GAP = 0.14; // gap between pillars
const HOUSE_FLOOR_H = 0.08; // floor band under the pillars when there is no core value base
const HOUSE_HEAD_PAD = 0.16; // total top and bottom text slack in a pillar head (strategic goal)
const HOUSE_TASK_GAP_PT = 10; // paragraph gap between strategic tasks
const HOUSE_TASK_GAP_MAX_PT = 26; // cap for the gap between strategic tasks when pillar bodies have height to spare
BLOCKS.house = (ctx, H, slide, box, k) => {
  const L = LB.labels("house", "labels", k.labels);
  const pil = k.pillars || [];
  const num = k.numbered !== false;
  const base = (Array.isArray(k.base) ? k.base : k.base ? [k.base] : []).filter(Boolean);
  const cx = box.x + LV_LABEL_W + LV_LABEL_GAP, cw = box.w - LV_LABEL_W - LV_LABEL_GAP;
  const pw = cw - 2 * HOUSE_EAVE, n = Math.max(1, pil.length);
  const colW = (pw - HOUSE_PILLAR_GAP * (n - 1)) / n;
  const heads = pil.map((p, i) => (num ? `${i + 1}. ` : "") + (p.title || ""));
  const tasks = pil.map((p, i) => itemsOf(p).map((t, j) => (num ? `${i + 1}-${j + 1}. ` : "") + textOf(t)));
  const taskParas = (list, sz) => list.map((t, j) => ({ align: "left", spcBef: j ? HOUSE_TASK_GAP_PT : 0, runs: [{ t, sz, color: T.COLOR.textDark }] }));
  const top = (k.mission ? LV_BAND_H + LV_BAND_GAP : 0) + HOUSE_ROOF_H + LV_BAND_GAP;
  const bottom = base.length ? LV_BAND_GAP + LV_BAND_H : HOUSE_FLOOR_H;
  const headNeed = (sz) => Math.max(T.PANEL.TITLE_H, ...heads.map((t) => A.estimateLines(t, colW - 2 * T.PANEL.INSET, sz, true) * A.lineHeightIn(sz) + HOUSE_HEAD_PAD));
  const need = (sz) => headNeed(sz) + Math.max(0.5, ...tasks.map((l) => parasNeedH(taskParas(l, sz), colW)));
  let sz = T.SIZE.body;
  while (top + need(sz) + bottom > box.h + 0.01 && sz > T.SIZE.BODY_MIN) sz--;
  if (top + need(sz) + bottom > box.h + 0.01) ctx.warn(`house cell height ${box.h.toFixed(2)}in < content needs ${(top + need(sz) + bottom).toFixed(2)}in (shorten the text or adjust row ratios)`);
  let y = box.y;
  if (k.mission) {
    const b = { x: cx, y, w: cw, h: LV_BAND_H };
    lvLabel(slide, box.x, y, LV_BAND_H, L.mission);
    H.frame(ctx, slide, b); A.text(slide, b, k.mission, { sz, bold: true, color: T.COLOR.navy, align: "center", valign: "middle" });
    y += LV_BAND_H + LV_BAND_GAP;
  }
  lvLabel(slide, box.x, y, HOUSE_ROOF_H, L.vision);
  lvRoof(ctx, slide, { x: cx, y, w: cw, h: HOUSE_ROOF_H }, k.vision);
  y += HOUSE_ROOF_H + LV_BAND_GAP;
  const hh = headNeed(sz), bh = box.y + box.h - bottom - y - hh;
  lvLabel(slide, box.x, y, hh, L.goals);
  lvLabel(slide, box.x, y + hh, bh, L.tasks);
  H.cols({ x: cx + HOUSE_EAVE, y, w: pw, h: hh + bh }, n, HOUSE_PILLAR_GAP).forEach((c, i) => {
    if (!pil[i]) return;
    H.label(ctx, slide, { x: c.x, y, w: c.w, h: hh }, heads[i], { sz, fill: T.COLOR.navy });
    // If pillar bodies have height to spare, widen the gaps between tasks to fill the body evenly (the gap is unified across pillars based on the tallest pillar)
    const nMax = Math.max(1, ...tasks.map((l) => l.length));
    const extraPt = nMax > 1 ? Math.max(0, Math.min(HOUSE_TASK_GAP_MAX_PT - HOUSE_TASK_GAP_PT, ((bh - Math.max(...tasks.map((l) => parasNeedH(taskParas(l, sz), c.w)))) * 72) / (nMax + 1))) : 0;
    lvParasBox(ctx, H, slide, { x: c.x, y: y + hh, w: c.w, h: bh }, taskParas(tasks[i], sz).map((p, j) => (j ? { ...p, spcBef: p.spcBef + extraPt } : p)));
  });
  y += hh + bh;
  if (!base.length) { slide.addShape(ctx.pres.ShapeType.rect, { x: cx, y: y, w: cw, h: HOUSE_FLOOR_H, fill: { color: T.COLOR.navyDeep }, line: { color: "FFFFFF", width: 0, transparency: 100 } }); return; }
  y += LV_BAND_GAP;
  lvLabel(slide, box.x, y, LV_BAND_H, L.base);
  H.cols({ x: cx, y, w: cw, h: LV_BAND_H }, base.length, HOUSE_PILLAR_GAP).forEach((c, i) => {
    H.frame(ctx, slide, c, { fill: T.COLOR.tintHead });
    A.text(slide, c, base[i], { sz, bold: true, color: T.COLOR.textDark, align: "center", valign: "middle" });
  });
};

/** Flowchart. Start and end are ellipses, process is a rectangle, decision is a diamond (KS X ISO 5807 symbols)
 *  {lanes?:[actors], nodes:[{id, type: start|end|process|decision, text, lane, col, fill}], edges:[{from, to, label, route: hv|vh}]}
 *  lane is the row (actor) and col is the column (process order). Explicit coordinates guarantee the same layout for the same input */
const FC_NODE_H = { process: 0.5, decision: 0.72, start: 0.46, end: 0.46 };
const FC_NODE_W_MAX = 2.0; // symbol width cap
const FC_NODE_W_RATIO = 0.74; // symbol width relative to column width (leaves room for branch labels in the gap between symbols)
const FC_NODE_LANE_RATIO = 0.66; // symbol height cap relative to the actor row height (keeps margin above and below symbols)
const FC_LANE_GAP = 0.1; // gap between actor rows
const FC_BACK_DROP = 0.2; // how far a return line drops below the symbols
const FC_BACK_MIN = 0.08; // minimum gap between a return line and the symbol bottom
const FC_LANE_EDGE = 0.06; // margin between a return line and the bottom border of the actor row
const FC_LABEL_W = 0.62, FC_LABEL_H = 0.22; // branch label (yes, no) box
const FC_LABEL_MIN_W = 0.46; // floor for a branch label width in the gap between symbols (three 11pt characters)
BLOCKS.flowchart = (ctx, H, slide, box, k) => {
  const nodes = k.nodes || [], edges = k.edges || [];
  if (!nodes.length) return;
  const hasLane = Array.isArray(k.lanes) && k.lanes.length > 0;
  // Without lanes, unlabeled rows go up to the largest node.lane (lane is the row number)
  const lanes = hasLane ? k.lanes : Array(Math.max(0, ...nodes.map((n) => n.lane || 0)) + 1).fill("");
  const lw = hasLane ? Math.min(box.w * 0.12, 1.2) : 0;
  const gx = box.x + (hasLane ? lw + 0.06 : 0), gw = box.w - (hasLane ? lw + 0.06 : 0);
  const laneH = (box.h - FC_LANE_GAP * (lanes.length - 1)) / lanes.length;
  const laneY = (i) => box.y + i * (laneH + FC_LANE_GAP);
  if (hasLane) lanes.forEach((ln, i) => { H.label(ctx, slide, { x: box.x, y: laneY(i), w: lw + 0.06 - LABEL_GAP, h: laneH }, ln, { sz: T.SIZE.body }); H.frame(ctx, slide, { x: gx, y: laneY(i), w: gw, h: laneH }); });
  const ncol = Math.max(...nodes.map((n) => n.col || 0)) + 1;
  const cw = gw / ncol;
  const nw = Math.min(cw * FC_NODE_W_RATIO, FC_NODE_W_MAX);
  const SHAPE = { start: "ellipse", end: "ellipse", decision: "diamond", process: "rect" };
  const G = {};
  nodes.forEach((n) => {
    const type = SHAPE[n.type] ? n.type : "process";
    const lane = Math.max(0, Math.min(n.lane || 0, lanes.length - 1));
    const h = Math.min(FC_NODE_H[type], laneH * FC_NODE_LANE_RATIO);
    const cx = gx + cw * ((n.col || 0) + 0.5), cy = laneY(lane) + laneH / 2;
    const g = { cx, cy, w: nw, h, l: cx - nw / 2, r: cx + nw / 2, t: cy - h / 2, b: cy + h / 2, lane, laneB: laneY(lane) + laneH };
    G[n.id] = g;
    const terminal = type === "start" || type === "end";
    // For diamonds and ellipses the text box is the rectangle inside the symbol, so size text to the actual text width
    const textW = type === "decision" ? nw * 0.5 : terminal ? nw * 0.7 : nw - 0.1;
    const textH = type === "decision" ? h * 0.5 : terminal ? h * 0.7 : h - 0.06;
    const paras = A.fitParas(A.parasFromString(n.text || "", { sz: T.SIZE.body, b: terminal, color: terminal ? T.COLOR.white : T.COLOR.textDark, align: "center" }), textW, textH, T.SIZE.BODY_MIN);
    slide.addText(A.runsOf(paras), { x: g.l, y: g.t, w: nw, h, shape: ctx.pres.ShapeType[SHAPE[type]], fill: { color: terminal ? T.COLOR.navy : n.fill === "tint" ? T.COLOR.tintHead : T.COLOR.white }, line: { color: terminal ? T.COLOR.navy : T.COLOR.border, width: 1 }, valign: "middle", margin: 0, isTextBox: true, autoFit: false });
  });
  // Symbols placed in the same cell (lane, col) overlap, so warn at build (an omitted col means column 0)
  const cells = {};
  nodes.forEach((n) => { const key = `${G[n.id].lane},${n.col || 0}`; (cells[key] = cells[key] || []).push(n.id); });
  Object.entries(cells).filter(([, ids]) => ids.length > 1).forEach(([key, ids]) => ctx.warn(`flowchart symbols share a position (lane,col ${key}): ${ids.join(", ")}`));
  const lbl = (x, y, t) => t && A.text(slide, { x, y, w: FC_LABEL_W, h: FC_LABEL_H }, t, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textGray, align: "left", valign: "middle", mg: [0, 0, 0, 0] });
  edges.forEach((e) => {
    const a = G[e.from], b = G[e.to];
    if (!a || !b) { ctx.warn(`flowchart edge target missing ${e.from} → ${e.to}`); return; }
    const sameRow = Math.abs(a.cy - b.cy) < 0.01, sameCol = Math.abs(a.cx - b.cx) < 0.01;
    if (sameRow && b.cx > a.cx) { seg(ctx, slide, a.r, a.cy, b.l, b.cy, true); lbl(a.r + 0.04, a.cy - FC_LABEL_H, e.label); return; }
    // Return edges: a straight line to the symbol immediately left; with symbols in between, route below them (the detour stays inside the actor row)
    const between = sameRow && Object.values(G).some((g) => g !== a && g !== b && g.lane === a.lane && g.cx > Math.min(a.cx, b.cx) + 0.01 && g.cx < Math.max(a.cx, b.cx) - 0.01);
    if (sameRow && !between) {
      seg(ctx, slide, a.l, a.cy, b.r, b.cy, true);
      // Center the branch label under the line in the gap between the two symbols (capped to the gap width so it does not overlap the symbols)
      const gap = a.l - b.r, lw2 = Math.max(FC_LABEL_MIN_W, Math.min(FC_LABEL_W, gap - 0.04));
      if (e.label) A.text(slide, { x: b.r + (gap - lw2) / 2, y: a.cy + 0.03, w: lw2, h: FC_LABEL_H }, e.label, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textGray, align: "center", valign: "middle", mg: [0, 0, 0, 0] });
      return;
    }
    if (sameRow) {
      const yy = Math.min(Math.max(a.b, b.b) + FC_BACK_DROP, a.laneB - FC_LANE_EDGE);
      if (yy < Math.max(a.b, b.b) + FC_BACK_MIN) ctx.warn(`flowchart return line ${e.from} → ${e.to} does not fit inside the actor row (raise the row height ratio)`);
      seg(ctx, slide, a.cx, a.b, a.cx, yy, false); seg(ctx, slide, a.cx, yy, b.cx, yy, false); seg(ctx, slide, b.cx, yy, b.cx, b.b, true);
      lbl(a.cx + 0.04, a.b, e.label); return;
    }
    if (sameCol) { const down = b.cy > a.cy; seg(ctx, slide, a.cx, down ? a.b : a.t, b.cx, down ? b.t : b.b, true); lbl(a.cx + 0.04, down ? a.b : a.t - FC_LABEL_H, e.label); return; }
    const down = b.cy > a.cy, right = b.cx > a.cx;
    if (e.route === "vh") { // vertical first, then horizontal
      seg(ctx, slide, a.cx, down ? a.b : a.t, a.cx, b.cy, false); seg(ctx, slide, a.cx, b.cy, right ? b.l : b.r, b.cy, true);
      lbl(a.cx + 0.04, down ? a.b : a.t - FC_LABEL_H, e.label); return;
    }
    const sx = right ? a.r : a.l; // horizontal first, then vertical
    seg(ctx, slide, sx, a.cy, b.cx, a.cy, false); seg(ctx, slide, b.cx, a.cy, b.cx, down ? b.t : b.b, true);
    lbl(right ? sx + 0.04 : sx - FC_LABEL_W - 0.04, a.cy - FC_LABEL_H, e.label);
  });
};

/** Business model canvas. Typeset in the fixed original layout (block names and positions do not change)
 *  Top 5 columns: key partners | key activities, key resources | value propositions | customer relationships, channels | customer segments. Bottom 2 cells: cost structure | revenue streams
 *  {partners, activities, resources, value, relationships, channels, segments, cost, revenue, numbered, labels}. Each value is a text array or {items|text}. labels changes block titles with the same keys
 *  With numbered true, the canvas fill-in order number (customer segments 1 ... cost structure 9) shows right of each block title */
const BMC = [ // block title defaults are canvas.labels in assets/labels.json
  { key: "partners", order: 8, col: 0 },
  { key: "activities", order: 7, col: 1, half: 0 },
  { key: "resources", order: 6, col: 1, half: 1 },
  { key: "value", order: 2, col: 2, core: true },
  { key: "relationships", order: 4, col: 3, half: 0 },
  { key: "channels", order: 3, col: 3, half: 1 },
  { key: "segments", order: 1, col: 4 },
  { key: "cost", order: 9, bottom: 0 },
  { key: "revenue", order: 5, bottom: 1 },
];
const BMC_TOP_SHARE = 0.68; // height share of the top 5 columns (the original canvas's top-to-bottom ratio)
const BMC_GAP = 0.1; // gap between blocks (kept narrow so it reads as one canvas)
const BMC_TITLE_H = 0.36; // block title line height
BLOCKS.canvas = (ctx, H, slide, box, k) => {
  const topH = (box.h - BMC_GAP) * BMC_TOP_SHARE, botH = box.h - BMC_GAP - topH;
  const cw = (box.w - BMC_GAP * 4) / 5, bw = (box.w - BMC_GAP) / 2;
  const halfH = (topH - BMC_GAP) / 2;
  const rectOf = (d) => {
    if (d.bottom != null) return { x: box.x + d.bottom * (bw + BMC_GAP), y: box.y + topH + BMC_GAP, w: bw, h: botH };
    const x = box.x + d.col * (cw + BMC_GAP);
    return d.half == null ? { x, y: box.y, w: cw, h: topH } : { x, y: box.y + d.half * (halfH + BMC_GAP), w: cw, h: halfH };
  };
  const itemsFor = (d) => itemsOf(Array.isArray(k[d.key]) ? { items: k[d.key] } : k[d.key] || {});
  const bodies = BMC.map((d) => { const r = rectOf(d); return { w: r.w, h: r.h - BMC_TITLE_H - 0.06 }; });
  const sz = commonSize(bodies, BMC.map(itemsFor));
  const copt = { sz, noWarn: true, valign: "top", forceBullet: true };
  // Cells of the same shape (tall column, half cell, bottom cell) use one paragraph spacing. Cell heights come from the layout, so grouping different shapes leaves tall columns looking empty
  const shapeOf = (d) => (d.bottom != null ? "bottom" : d.half == null ? "tall" : "half");
  const cgap = Object.fromEntries(["tall", "half", "bottom"].map((sh) => [sh, H.groupGap(BMC.map((d, i) => (shapeOf(d) === sh ? bodies[i] : null)), BMC.map(itemsFor), copt)]));
  const own = k.labels || {}, titles = LB.labels("canvas", "labels"); // block titles (changed through labels with the block keys)
  BMC.forEach((d, i) => {
    const r = rectOf(d);
    H.frame(ctx, slide, r, { fill: d.core ? T.COLOR.tintBg : undefined });
    // Block title: bold navy text with a short rule under it (text hierarchy instead of a filled header band)
    A.text(slide, { x: r.x + 0.1, y: r.y + 0.04, w: r.w - 0.2, h: BMC_TITLE_H - 0.04 }, own[d.key] || titles[d.key], { sz: T.SIZE.body, bold: true, color: T.COLOR.navy, align: "left", valign: "middle", mg: [0, 0, 0, 0] });
    if (k.numbered) A.text(slide, { x: r.x + r.w - 0.4, y: r.y + 0.04, w: 0.3, h: BMC_TITLE_H - 0.04 }, String(d.order), { sz: T.SIZE.body, bold: true, color: T.COLOR.textMuted, align: "right", valign: "middle", mg: [0, 0, 0, 0] });
    hline(ctx, slide, r.x + 0.1, r.y + BMC_TITLE_H, Math.min(r.w - 0.2, 0.9));
    const its = itemsFor(d);
    if (its.length) H.bulletsBlock(ctx, slide, { x: r.x, y: r.y + BMC_TITLE_H + 0.04, w: r.w, h: bodies[i].h }, its, { ...copt, groupGapPt: cgap[shapeOf(d)] });
  });
};

/** Market size (TAM, SAM, SOM). Three bottom-aligned circles matched to per-market description rows by horizontal connectors
 *  {levels:[{label, name, value, items[]}]} Ordered from the outer circle (total market) to the inner circle (obtainable market)
 *  Circles hold the abbreviation and size; rows on the right hold the market name, definition and basis of estimate
 *  Description rows split the circle area height equally, and each abbreviation sits at its row's middle height so the connector is one horizontal line
 *  Description cell width fits the longest text and the whole group is centered in the cell */
const MKT_RATIO = { 2: [1, 0.55], 3: [1, 0.7, 0.38] }; // diameter ratio relative to the outer circle (by level count; ratios that keep each row's middle height inside its circle band)
const MKT_W_SHARE = 0.4; // circle area width cap relative to cell width
const MKT_LEAD = 0.5; // width of the connector span between the circle area and the description rows
const MKT_CHIP_W = 1.4; // width of the market name cell in a description row
const MKT_TAG_W = 1.4, MKT_TAG_H = 0.5; // text box for the abbreviation and size inside a circle
const MKT_DOT_X = 0.62; // horizontal position cap of the connector start dot relative to the circle center
const MKT_FIT_STEP = 0.02; // step used to widen the description cell while fitting it to the text
/** Description cell width that holds each text item on one line (bullet indent and box inset included). Returns the cap if it exceeds the cell width cap */
function fitItemsW(items, sz, maxW) {
  const list = (items || []).map(textOf).filter(Boolean);
  if (!list.length) return maxW;
  const indent = list.length > 1 ? T.PARA.bulletIndentIn : 0;
  let w = Math.max(...list.map((t) => (A.textEm(t) * sz) / 72));
  while (w < maxW && list.some((t) => A.estimateLines(t, w, sz) > 1)) w += MKT_FIT_STEP;
  return Math.min(maxW, w + indent + 2 * T.PANEL.INSET);
}
BLOCKS.market = (ctx, H, slide, box, k) => {
  const lv = (k.levels || []).slice(0, 3);
  if (lv.length < 2) { ctx.warn("market needs 2 or more market levels"); return; }
  const D = Math.min(box.h, box.w * MKT_W_SHARE);
  const y0 = box.y + (box.h - D) / 2;
  // Description rows: split the circle area height equally (row top and bottom edges align with the circle's top and bottom)
  const gap = GAP_ITEM_MAX, rh = Math.min(1.3, (D - gap * (lv.length - 1)) / lv.length);
  const top = y0 + (D - (rh * lv.length + gap * (lv.length - 1))) / 2;
  const rows = lv.map((_, i) => ({ y: top + i * (rh + gap), h: rh }));
  // Fit the description cell width to the longest text and center the circles, connectors and description cells as a group
  const fixedW = D + MKT_LEAD + MKT_CHIP_W + 0.06;
  const cwMax = box.w - fixedW;
  const sz = commonSize(rows.map((r) => ({ w: cwMax, h: r.h })), lv.map((m) => m.items || []));
  const cw = Math.max(...lv.map((m) => fitItemsW(m.items, sz, cwMax)));
  const cgap = commonGap(H, rows.map((r) => ({ w: cw, h: r.h })), lv.map((m) => m.items || []), sz); // description cells use one paragraph spacing
  const x0 = box.x + (box.w - fixedW - cw) / 2, cx = x0 + D / 2;
  const fills = [T.COLOR.navyPastel2, T.COLOR.navyPastel, T.COLOR.navy];
  const dia = MKT_RATIO[lv.length].map((r) => D * r);
  dia.forEach((d, i) => slide.addShape(ctx.pres.ShapeType.ellipse, { x: cx - d / 2, y: y0 + D - d, w: d, h: d, fill: { color: fills[i] }, line: { color: T.COLOR.white, width: 1 } }));
  const rx = x0 + D + MKT_LEAD;
  // Abbreviation height inside a circle: clamp the row's middle height into the circle band (from the top of this circle to the top of the next)
  const bandTop = dia.map((d) => y0 + D - d);
  const bandBot = dia.map((d, i) => (i < dia.length - 1 ? y0 + D - dia[i + 1] : y0 + D));
  const tagY = rows.map((r, i) => Math.min(Math.max(r.y + r.h / 2, bandTop[i] + MKT_TAG_H / 2 + 0.04), bandBot[i] - MKT_TAG_H / 2 - 0.04));
  // Connector start dots: a horizontal position fitted to the narrowest circle so every level sits on the same vertical line
  const halfChord = tagY.map((y, i) => { const r = dia[i] / 2, dy = y - (y0 + D - r); return Math.sqrt(Math.max(0, r * r - dy * dy)); });
  const dotX = cx + Math.min(MKT_DOT_X, Math.min(...halfChord) - 0.1);
  lv.forEach((m, i) => {
    const dark = i > 0;
    const paras = [{ align: "center", runs: [{ t: m.label || "", sz: T.SIZE.panelHead, b: true, color: dark ? T.COLOR.white : T.COLOR.textDark }] }];
    if (m.value) paras.push({ align: "center", runs: [{ t: m.value, sz: T.SIZE.body, b: true, color: dark ? T.COLOR.white : T.COLOR.textDark }] });
    slide.addText(A.runsOf(paras), { x: cx - MKT_TAG_W / 2, y: tagY[i] - MKT_TAG_H / 2, w: MKT_TAG_W, h: MKT_TAG_H, isTextBox: true, valign: "middle", margin: 0 });
  });
  lv.forEach((m, i) => {
    const r = rows[i], ry = r.y + r.h / 2;
    H.label(ctx, slide, { x: rx, y: r.y, w: MKT_CHIP_W, h: r.h }, `${m.name || ""}\n(${m.label || ""})`, { sz: T.SIZE.body, fill: fills[i], color: i === 0 ? T.COLOR.textDark : undefined });
    const cb = { x: rx + MKT_CHIP_W + 0.06, y: r.y, w: cw, h: r.h };
    H.frame(ctx, slide, cb);
    writeItems(ctx, H, slide, cb, m.items || [], sz, { forceBullet: (m.items || []).length > 1, groupGapPt: cgap });
    // Connector: a horizontal line from the dot inside the circle to the row's left edge (an elbow line if the abbreviation hit the band edge and the heights differ)
    const ink = { color: T.COLOR.textGray, width: 0.75 };
    const sy = tagY[i];
    slide.addShape(ctx.pres.ShapeType.ellipse, { x: dotX - 0.04, y: sy - 0.04, w: 0.08, h: 0.08, fill: { color: i === 0 ? T.COLOR.textDark : T.COLOR.white }, line: { color: i === 0 ? T.COLOR.textDark : T.COLOR.white, width: 0.5 } });
    if (Math.abs(ry - sy) < 0.01) { slide.addShape(ctx.pres.ShapeType.line, { x: dotX, y: ry, w: rx - dotX, h: 0, line: ink }); return; }
    const tx = x0 + D + MKT_LEAD / 2;
    slide.addShape(ctx.pres.ShapeType.line, { x: dotX, y: sy, w: tx - dotX, h: 0, line: ink });
    slide.addShape(ctx.pres.ShapeType.line, { x: tx, y: Math.min(sy, ry), w: 0, h: Math.abs(ry - sy), line: ink });
    slide.addShape(ctx.pres.ShapeType.line, { x: tx, y: ry, w: rx - tx, h: 0, line: ink });
  });
  return { x: x0, w: fixedW + cw }; // drawn horizontal range (used to match the width of the band below)
};

// ---------------------------------------------------------------- Natural height and capacity height
// A text-box-heavy block stretched into a box much larger than its content looks empty inside
// For each block, compute a natural height capped at FILL_EXPAND times the needed content height, and
// a capacity height it can grow to without leaving the box empty (table row height, gaps between boxes, diagram size)
// composite sets row heights from natural heights, then shares leftover height in this order: diagram rows, capacity heights, row gaps, vertical centering margin (planRows)
// Blocks drawn to fit the given space, such as charts, flowcharts, logic models and pictures, are not measured (null)
// Pyramids, matrices and cycles use their preferred height as natural height
const FILL_EXPAND = T.PANEL.FILL_EXPAND; // box height cap factor (relative to needed content height)
const PYR_LEVEL_H = 0.62, MATRIX_PREF_H = 2.9, CYCLE_PREF_H = 3.8; // pyramid level height; preferred heights of the matrix and cycle diagrams
const PYR_LEVEL_MAX = 0.9, MATRIX_MAX_H = 4.6, CYCLE_MAX_H = 4.6; // pyramid level height; capacity height caps of the matrix and cycle diagrams
const TABLE_ROW_FIT = 0.38; // table row height floor (one 11pt line plus cell padding)
const TABLE_EXPAND = 1.2; // table row natural height factor (a 0.38 inch one-line row counts as 0.46 inch)
// When measuring minimum height (needed content height), set the growth factor to 1 to reuse the same measure functions
let growFactor = FILL_EXPAND;
const grow = (need, min) => Math.max(min, need * growFactor);
const sumGap = (n, gap) => gap * Math.max(0, n - 1);
const MEASURE = {
  bullets: (k, w) => (k.head ? T.PANEL.TITLE_H : 0) + grow(needH(itemsOf(k), w, T.SIZE.body, true), 0.5),
  text: (k, w) => grow(needH([k.text || ""], w, T.SIZE.body, false), 0.46),
  stack: (k, w) => (k.items || []).reduce((a, x) => a + (x.head ? T.PANEL.HEAD_H : 0) + grow(needH(itemsOf(x), w, T.SIZE.body, true), 0.4), 0) + sumGap((k.items || []).length, GAP_ITEM),
  // The summary box follows the neighbor analysis cell's height, so its natural height is the needed height without growth
  // The summary box shrinks down to the body floor (11pt) when the cell is short, so minimum height measurement (growFactor 1) uses the floor size
  summary: (k, w) => sumLeadH(k, w) + (k.items || []).reduce((a, x) => a + Math.max(0.5, sumItemNeed(x, w, growFactor > 1 ? T.SIZE.body : T.SIZE.BODY_MIN)), 0),
  labeled: (k, w) => {
    const lw = Math.min(k.labelW ? w * k.labelW : w * 0.28, 1.8), cw = w - lw - 0.06;
    return (k.rows || []).reduce((a, r) => a + grow(Math.max(needH([r.label || ""], lw + 0.06 - LABEL_GAP, T.SIZE.body, false), needH(itemsOf(r), cw, T.SIZE.body, true)), 0.34), 0) + sumGap((k.rows || []).length, CELL_GAP_V);
  },
  grid: (k, w) => {
    const g = gridGeom(k, { x: 0, y: 0, w, h: 1 });
    return (g.headH ? g.headH + g.vg : 0) + g.needs.reduce((a, v) => a + grow(v, g.hier ? HIER_ROW_MIN : 0.34), 0) + sumGap(g.rows.length, g.vg);
  },
  vsteps: (k, w) => {
    const st = k.steps || [];
    const lw = Math.min(w * 0.34, 1.9), cw = w - lw - 0.08;
    return st.reduce((a, s) => a + grow(Math.max(needH(itemsOf(s), cw, T.SIZE.body, true), needH([s.title || ""], lw + 0.08 - LABEL_GAP, T.SIZE.body, false)), 0.42), 0) + sumGap(st.length, k.arrows !== false ? 0.26 : GAP_ITEM);
  },
  flow: (k, w) => {
    const nodes = k.nodes || [];
    const head = (n) => (n.title && itemsOf(n).length ? T.PANEL.HEAD_H : 0);
    const body = (n, bw) => grow(needH(n.title && !itemsOf(n).length ? [n.title] : itemsOf(n), bw, T.SIZE.body, true), 0.4);
    if (k.dir === "v") return nodes.reduce((a, n) => a + head(n) + body(n, w), 0) + sumGap(nodes.length, 0.42);
    const cw = (w - sumGap(nodes.length, 0.42)) / Math.max(1, nodes.length);
    return Math.max(0.6, ...nodes.map((n) => head(n) + body(n, cw)));
  },
  chevrons: (k, w, H) => {
    const st = k.steps || [];
    if (!st.some((s) => itemsOf(s).length)) return 0.8;
    const cs = H.chevronCols({ x: 0, y: 0, w, h: 0.55 }, st.length, 0, 1);
    return 0.55 + 0.12 + Math.max(0.5, ...st.map((s, i) => grow(needH(itemsOf(s), cs[i].w, T.SIZE.body, true), 0.5)));
  },
  numbers: (k) => 1.0 + ((k.items || []).some((it) => it.note) ? 0.26 : 0),
  // Tables share the per-row needed height from templates.tableMetrics (drawing and measuring follow the same rule)
  table: (k, w, H) => {
    if (!(k.rows || []).length) return TABLE_ROW_FIT;
    const M = H.tableMetrics(k, w);
    return M.headH + M.need.reduce((a, v, i) => a + (growFactor > 1 ? Math.min(M.cap[i], Math.max(v, TABLE_ROW_FIT) * TABLE_EXPAND) : v), 0);
  },
  // Minimum height measurement (growFactor 1) counts level-2 boxes at their floor height
  tree: (k) => {
    const maxL2 = Math.max(0, ...(k.children || []).map((c) => (c.children || []).length));
    const l2 = growFactor > 1 ? TREE_L2_H : TREE_L2_H_MIN;
    return (k.top ? TREE_ROOT_H + TREE_TOP_DROP : 0) + TREE_ROOT_H + TREE_DROP + TREE_L1_H + (maxL2 ? TREE_L2_TOP + maxL2 * l2 + nGaps(maxL2) * TREE_L2_GAP : 0);
  },
  zones: (k) => zonesNeed(k),
  governance: (k) => (k.spine || []).length * GOV_NODE_H + sumGap((k.spine || []).length, GOV_GAP),
  timeline: (k, w) => {
    const ev = k.events || [], cw = tlColW(w, ev.length);
    const title = ev.some((e) => e.title) ? TL_TITLE_H : 0;
    return TL_HEAD + title + grow(Math.max(0.4, ...ev.map((e) => needH(itemsOf(e), cw, T.SIZE.body, true))), 0.5);
  },
  funnel: (k, w) => {
    const st = k.stages || [];
    return (k.head ? FN_HEAD_H + FN_HEAD_GAP : 0) + st.reduce((a, s) => a + Math.max(FN_BAND_H, grow(fnNeed(k, s, w), 0.4)), 0) + sumGap(st.length, FN_GAP);
  },
  // Diagrams fill their cell but have a preferred height so they match the height of neighboring text box cells
  pyramid: (k) => (k.levels || []).length * PYR_LEVEL_H + sumGap((k.levels || []).length, 0.06),
  matrix: () => MATRIX_PREF_H,
  cycle: () => CYCLE_PREF_H,
  valuechain: (k, w, H) => {
    const g = vcGeom(k, { x: 0, y: 0, w, h: 1 }, H);
    return g.fixed + g.needs.reduce((a, v) => a + grow(v, 0.4), 0);
  },
};
// Capacity height: how far a block can grow from natural height without leaving the box empty
// Tables grow by row height (up to ROW_H_MAX), box columns by the gaps between boxes, diagrams by shape size, and other text boxes up to SIBLING_STRETCH times
const nGaps = (n) => Math.max(0, n - 1);
const CAPACITY = {
  // Tables grow to ROW_H_TEXT for one-line text-only rows, by the extra line spacing for multi-line rows, and up to ROW_H_MAX with Harvey balls (same rule as templates.tableLayout)
  table: (k, w, nat, H) => {
    if (!(k.rows || []).length) return nat;
    const M = H.tableMetrics(k, w);
    return Math.max(nat, M.headH + M.cap.reduce((x, v) => x + v, 0));
  },
  stack: (k, w, nat) => nat + nGaps((k.items || []).length) * (GAP_ITEM_MAX - GAP_ITEM),
  // The summary box fills the cell to match the neighbor analysis cell's height (item cells share the leftover height)
  summary: (k, w, nat) => Math.max(nat, SUMMARY_FILL_H),
  labeled: (k, w, nat) => nat + nGaps((k.rows || []).length) * (CELL_GAP_V_MAX - CELL_GAP_V),
  grid: (k, w, nat) => nat + nGaps((k.rows || []).length) * ((k.style === "hierarchy" ? HIER_GAP_Y_MAX - HIER_GAP_Y : CELL_GAP_V_MAX - CELL_GAP_V)),
  vsteps: (k, w, nat) => nat + nGaps((k.steps || []).length) * (k.arrows !== false ? STEP_GAP_MAX - STEP_GAP : GAP_ITEM_MAX - GAP_ITEM),
  flow: (k, w, nat) => (k.dir === "v" ? nat + nGaps((k.nodes || []).length) * (FLOW_GAP_MAX - FLOW_GAP) : nat * SIBLING_STRETCH),
  tree: (k, w, nat) => {
    const maxL2 = Math.max(0, ...(k.children || []).map((c) => (c.children || []).length));
    return nat + TREE_DROP_EXTRA + nGaps(maxL2) * TREE_L2_GAP_EXTRA + maxL2 * (0.5 - TREE_L2_H);
  },
  zones: (k, w, nat) => nat + nGaps(Math.max(1, ...(k.zones || []).map((z) => (z.items || []).length))) * (ZONE_ITEM_GAP_MAX - ZONE_ITEM_GAP),
  governance: (k) => (k.spine || []).length * GOV_NODE_H_MAX + sumGap((k.spine || []).length, GOV_GAP_MAX),
  funnel: (k, w, nat) => Math.max(nat, (k.head ? FN_HEAD_H + FN_HEAD_GAP : 0) + (k.stages || []).length * FN_BAND_H_MAX + sumGap((k.stages || []).length, FN_GAP)),
  pyramid: (k) => (k.levels || []).length * PYR_LEVEL_MAX + sumGap((k.levels || []).length, 0.06),
  // A matrix grows until its plane is close to square
  matrix: (k, w, nat) => {
    const legend = k.legend != null ? k.legend : (k.items || []).length > 0;
    const pw = Math.min(w - (legend ? Math.min(w * 0.38, 3.0) + 0.2 : 0) - MATRIX_AXIS_PAD, MATRIX_MAX_H);
    return Math.max(nat, Math.min(MATRIX_MAX_H, pw + MATRIX_AXIS_PAD));
  },
  cycle: () => CYCLE_MAX_H,
};
/** Block natural height. null if the block is not measured */
function blockNeed(k, w, H) {
  const m = MEASURE[k.kind];
  const v = m ? m(k, w, H) : null;
  return v == null ? null : v + (k.caption ? CAPTION_H : 0);
}
/** Block capacity height. null if the block is not measured */
function blockCap(k, w, H) {
  const m = MEASURE[k.kind];
  const nat = m ? m(k, w, H) : null;
  if (nat == null) return null;
  const c = CAPACITY[k.kind];
  return (c ? c(k, w, nat, H) : nat * SIBLING_STRETCH) + (k.caption ? CAPTION_H : 0);
}
/** Block minimum height (needed content height without growth). null if the block is not measured */
function blockMin(k, w, H) {
  growFactor = 1;
  try { return blockNeed(k, w, H); } finally { growFactor = FILL_EXPAND; }
}
/** Cell caption: one bold left-aligned line. Returns the box left below the caption */
function caption(slide, box, text) {
  A.text(slide, { x: box.x, y: box.y, w: box.w, h: CAPTION_H }, text, { sz: T.SIZE.body, bold: true, color: T.COLOR.textDark, align: "left", valign: "top", mg: [0, 0, 0, 0] });
  return { x: box.x, y: box.y + CAPTION_H, w: box.w, h: box.h - CAPTION_H };
}
/** Area height (title, note and block gaps included). null if any block is not measured
 *  mode is natural height (default), capacity height ("cap") or minimum height ("min") */
function regionNeed(rg, w, H, mode) {
  const blocks = rg.blocks || (rg.block ? [rg.block] : []);
  const measure = mode === "cap" ? blockCap : mode === "min" ? blockMin : blockNeed;
  const needs = blocks.map((k) => measure(k, w, H));
  if (!blocks.length || needs.some((v) => v == null)) return null;
  return (rg.title ? T.PANEL.SUBHEAD_H : rg.caption ? CAPTION_H : 0) + (rg.note || rg.noteBand ? NOTE_H + 0.04 : 0) + needs.reduce((a, v) => a + v, 0) + sumGap(blocks.length, GAP_BLOCK);
}

// ---------------------------------------------------------------- Grid
function gridSpec(s, nRegions) {
  if (Array.isArray(s.rows) && s.rows.length) return s.rows.map((r) => ({ h: r.h || 1, cols: r.cols && r.cols.length ? r.cols : [1] }));
  if (Array.isArray(s.cols) && s.cols.length) return [{ h: 1, cols: s.cols }];
  return [{ h: 1, cols: Array(Math.max(1, nRegions)).fill(1) }];
}

/** Per-row cell width list (shared so area measurement and drawing use the same widths) */
function rowWidths(r, areaW, colGap) {
  const wSum = r.cols.reduce((a, c) => a + c, 0);
  const availW = areaW - colGap * (r.cols.length - 1);
  return r.cols.map((c) => (availW * c) / wSum);
}

/** Row height distribution
 *  Text box rows target natural height (FILL_EXPAND times the needed content height); diagram rows target their set ratio height
 *  If the targets add up to more than the body, secure minimum heights first (needed content height for text box rows, 70% of the set height for diagram rows) and share the rest in proportion
 *  If the targets add up to less than the body, share leftover height in this order: diagram rows, row gaps, vertical centering margin */
function planRows(spec, regions, area, rowGap, colGap, H) {
  const hSum = spec.reduce((a, r) => a + r.h, 0);
  const availH = area.h - rowGap * (spec.length - 1);
  let idx = 0;
  const plan = spec.map((r) => {
    const assigned = (availH * r.h) / hSum;
    const widths = rowWidths(r, area.w, colGap);
    const rgs = widths.map((w) => ({ rg: regions[idx++], w }));
    const needs = rgs.map(({ rg, w }) => (rg ? regionNeed(rg, w, H) : 0));
    const natural = needs.some((v) => v == null) ? null : Math.max(0, ...needs);
    if (natural == null) return { elastic: true, assigned, target: assigned, min: assigned * ELASTIC_MIN, cap: assigned };
    // Row capacity height: up to the height every cell can fill (the minimum of per-cell capacity heights), never below the largest natural height
    const present = rgs.filter(({ rg }) => rg);
    const caps = present.map(({ rg, w }) => regionNeed(rg, w, H, "cap"));
    const cap = Math.max(natural, caps.length ? Math.min(...caps) : natural);
    // Minimum height is the needed content height without growth (fixed-height parts such as cell titles, captions and table heads do not shrink)
    const min = Math.max(0, ...present.map(({ rg, w }) => regionNeed(rg, w, H, "min")));
    return { elastic: false, assigned, target: natural, min, cap };
  });
  const tSum = plan.reduce((a, p) => a + p.target, 0);
  let freed = 0;
  if (tSum > availH) {
    const mSum = plan.reduce((a, p) => a + p.min, 0);
    const k = availH > mSum ? (availH - mSum) / Math.max(0.01, tSum - mSum) : 0;
    plan.forEach((p) => { p.h = availH > mSum ? p.min + (p.target - p.min) * k : (p.min * availH) / mSum; });
  } else {
    plan.forEach((p) => { p.h = p.target; });
    freed = availH - tSum;
  }
  const elastic = plan.filter((p) => p.elastic);
  const wSum = elastic.reduce((a, p) => a + p.assigned, 0);
  elastic.forEach((p) => { p.h += (freed * p.assigned) / (wSum || 1); });
  if (elastic.length) freed = 0;
  // Without diagram rows, give leftover height to rows up to their capacity height first (table row height, gaps between boxes, diagram size)
  const room = plan.reduce((a, p) => a + (p.elastic ? 0 : Math.max(0, p.cap - p.h)), 0);
  if (freed > 0 && room > 0) {
    const g = Math.min(freed, room);
    plan.forEach((p) => { if (!p.elastic) p.h += (g * Math.max(0, p.cap - p.h)) / room; });
    freed -= g;
  }
  // Without elastic rows, first share leftover height into the row gaps for breathing room, then use the rest to center the group vertically
  const nGap = spec.length - 1;
  const gapExtra = nGap > 0 ? Math.min(Math.max(0, GAP_ROW_MAX - rowGap), freed / nGap) : 0;
  freed -= gapExtra * nGap;
  return { heights: plan.map((p) => p.h), gap: rowGap + gapExtra, offset: freed / 2 };
}

function composite(ctx, slide, sb, H) {
  const s = sb.slots || {};
  const b = H.body(ctx, sb);
  const spec0 = gridSpec(s, (s.regions || []).length);
  // If a row has a cell with a note, raise the content bottom of its neighbors by the note height so the cells in the row share one bottom edge (the note text shows only in its own cell)
  const regions = (s.regions || []).slice();
  let ri0 = 0;
  spec0.forEach((r) => {
    const n = r.cols.length;
    if (regions.slice(ri0, ri0 + n).some((g) => g && g.note)) for (let j = ri0; j < ri0 + n; j++) if (regions[j] && !regions[j].note) regions[j] = { ...regions[j], noteBand: true };
    ri0 += n;
  });
  const bottom = (s.point ? BOTTOM_BAND_H + BOTTOM_GAP : 0) + (s.conclusion ? BOTTOM_BAND_H + BOTTOM_GAP : 0); // body() excludes the footnote height
  const area = { x: b.x, y: b.y, w: b.w, h: b.h - bottom };
  const spec = gridSpec(s, regions.length);
  const slots = spec.reduce((a, r) => a + r.cols.length, 0);
  if (slots !== regions.length) ctx.warn(`composite grid has ${slots} cells but ${regions.length} regions`);
  const rowGap = s.rowFlow ? GAP_ROW_FLOW : s.dividers ? GAP_ROW_DIV : GAP_ROW;
  const colGap = s.flow ? GAP_COL_FLOW : s.dividers ? GAP_COL_DIV : GAP_COL;
  const { heights, gap, offset } = planRows(spec, regions, area, rowGap, colGap, H);
  let y = area.y + offset, idx = 0;
  const rowBoxes = [];
  const divV = []; // per-row vertical dividers {x, y1, y2}
  // Content horizontal range: the drawn range a block returns for cells without a title, the cell width otherwise. The bands below (conclusion, 수행 Point) align their left and right ends to this range
  let exL = Infinity, exR = -Infinity;
  const extend = (x, w) => { exL = Math.min(exL, x); exR = Math.max(exR, x + w); };
  spec.forEach((r, ri) => {
    const rh = heights[ri];
    let x = area.x;
    const cells = rowWidths(r, area.w, colGap).map((w) => { const cell = { x, y, w, h: rh }; x += w + colGap; return cell; });
    const inners = [];
    cells.forEach((cell, ci) => {
      const rg = regions[idx++];
      const gapR = ci < cells.length - 1 && regions[idx] ? colGap : 0; // column gap to the neighbor cell on the right (diagram blocks use it to shape their ends)
      if (!rg) return;
      let box = cell;
      if (rg.title || rg.caption) extend(cell.x, cell.w);
      if (rg.title) box = H.subhead(ctx, slide, cell, s.numbered ? `${CIRCLED[idx - 1] || idx} ${rg.title}` : rg.title);
      else if (rg.caption) box = caption(slide, cell, rg.caption);
      if (rg.note || rg.noteBand) box = { ...box, h: box.h - NOTE_H - 0.04 };
      const blocks = (rg.blocks || (rg.block ? [rg.block] : [])).slice();
      // Block heights: if all blocks are measurable, set natural heights first and share leftover height up to capacity heights; otherwise share by the set weights (h)
      const needs = blocks.map((k) => blockNeed(k, box.w, H));
      const measured = needs.every((v) => v != null);
      const caps = measured ? blocks.map((k) => blockCap(k, box.w, H)) : null;
      const bGaps = GAP_BLOCK * (blocks.length - 1);
      // A cell with less capacity height than its neighbors grows only to its capacity height and sits vertically centered in the height left under the cell title
      // A cell holding one table, short by CELL_SNAP or less, stretches the row height slightly so its top and bottom edges match the neighbors
      if (measured) {
        const capH = caps.reduce((a, v) => a + v, 0) + bGaps;
        const snap = blocks.length === 1 && blocks[0].kind === "table" && box.h - capH <= CELL_SNAP;
        if (snap && capH < box.h) blocks[0] = { ...blocks[0], _fill: true };
        else if (capH < box.h) box = { ...box, y: box.y + (box.h - capH) / 2, h: capH };
      }
      if (rg.note) A.text(slide, { x: box.x, y: box.y + box.h + 0.04, w: box.w, h: NOTE_H }, /^\s*(※|\*)/.test(rg.note) ? rg.note : `※ ${rg.note}`, { sz: T.SIZE.note, color: T.COLOR.textMuted, align: "left", valign: "middle", mg: [0, 0, 0, 0] });
      const bAvail = box.h - bGaps;
      const nSum = measured ? needs.reduce((a, v) => a + v, 0) : 0;
      const growSum = measured ? caps.reduce((a, v, j) => a + Math.max(0, v - needs[j]), 0) : 0;
      // If the cell is smaller than natural height, set minimum heights first and share the rest in proportion to (natural height - minimum height)
      const mins = measured ? blocks.map((k) => blockMin(k, box.w, H)) : null;
      const mSum = measured ? mins.reduce((a, v) => a + v, 0) : 0;
      if (measured && bAvail < mSum - 0.02) ctx.warn(`composite cell '${rg.title || rg.caption || ""}' height ${bAvail.toFixed(2)}in < content needs ${mSum.toFixed(2)}in (overflow risk; trim items or adjust the grid)`);
      const wts = measured ? needs : blocks.map((k) => k.h || 1);
      const wtSum = wts.reduce((a, v) => a + v, 0) || 1;
      const squeeze = (j) => (bAvail >= mSum && nSum > mSum ? mins[j] + ((bAvail - mSum) * (needs[j] - mins[j])) / (nSum - mSum) : (bAvail * mins[j]) / (mSum || 1));
      // In a cell mixing diagram blocks (not measured) and text box blocks, text box blocks get natural height first (minimum height if short) and diagram blocks share the rest by weight (h)
      const mixedFixed = !measured ? blocks.map((k, j) => (needs[j] == null ? null : needs[j])) : null;
      const mixed = (j) => {
        const fixedSum = mixedFixed.reduce((a, v) => a + (v || 0), 0);
        const minSum = blocks.reduce((a, k, i) => a + (mixedFixed[i] != null ? blockMin(k, box.w, H) : 0), 0);
        const flexW = blocks.reduce((a, k, i) => a + (mixedFixed[i] == null ? k.h || 1 : 0), 0) || 1;
        const flexMin = blocks.reduce((a, k, i) => a + (mixedFixed[i] == null ? ELASTIC_BLOCK_MIN : 0), 0);
        // Text box block height: natural height, or if short, a value between minimum and natural height that leaves the diagram block floor
        const room = Math.max(minSum, Math.min(fixedSum, bAvail - flexMin));
        const fixedH = (i) => (fixedSum > minSum ? blockMin(blocks[i], box.w, H) + ((room - minSum) * (mixedFixed[i] - blockMin(blocks[i], box.w, H))) / (fixedSum - minSum) : mixedFixed[i]);
        if (mixedFixed[j] != null) return fixedH(j);
        return ((bAvail - room) * (blocks[j].h || 1)) / flexW;
      };
      const hOf = (j) => (!measured ? mixed(j) : bAvail > nSum && growSum > 0 ? needs[j] + ((bAvail - nSum) * Math.max(0, caps[j] - needs[j])) / growSum : bAvail > nSum ? (bAvail * wts[j]) / wtSum : squeeze(j));
      let by = box.y;
      blocks.forEach((k, j) => {
        const bh = hOf(j);
        const fn = BLOCKS[k.kind];
        if (!fn) { ctx.warn(`composite block kind '${k.kind}' not supported (${Object.keys(BLOCKS).join(", ")})`); extend(box.x, box.w); }
        else {
          const kb = { x: box.x, y: by, w: box.w, h: bh, gapR };
          // image blocks typeset caption as a description under the image, so skip the caption above the block (avoids repeating the same text)
          const topCaption = k.caption && k.kind !== "image";
          const ex = fn(ctx, H, slide, topCaption ? caption(slide, kb, k.caption) : kb, k);
          if (ex && ex.w > 0 && !topCaption) extend(ex.x, ex.w); else extend(kb.x, kb.w);
        }
        by += bh + GAP_BLOCK;
      });
      inners.push(box);
    });
    // Arrows between cells sit at the vertical middle of the two neighboring cells' content
    if (s.flow) inners.slice(0, -1).forEach((bx, i) => { const nx = inners[i + 1]; const top = Math.min(bx.y, nx.y), bot = Math.max(bx.y + bx.h, nx.y + nx.h); arrowShape(ctx, slide, bx.x + bx.w + colGap / 2, (top + bot) / 2, "right"); });
    if (s.dividers) cells.slice(0, -1).forEach((c) => divV.push({ x: c.x + c.w + colGap / 2, y1: c.y, y2: c.y + c.h }));
    rowBoxes.push({ y, h: rh });
    y += rh + gap;
  });
  if (s.rowFlow) rowBoxes.slice(0, -1).forEach((r) => arrowShape(ctx, slide, area.x + area.w / 2, r.y + r.h + gap / 2, "down"));
  if (s.dividers) {
    // When vertical dividers in neighboring rows share an x position, join them across the row gap into one line so they cross the horizontal divider
    const lines = [];
    divV.forEach((d) => {
      const up = lines.find((g) => Math.abs(g.x - d.x) < DIV_JOIN_TOL && Math.abs(g.y2 + gap - d.y1) < DIV_JOIN_TOL);
      if (up) up.y2 = d.y2; else lines.push({ ...d });
    });
    lines.forEach((g) => vline(ctx, slide, g.x, g.y1, g.y2 - g.y1));
    rowBoxes.slice(0, -1).forEach((r) => hline(ctx, slide, area.x, r.y + r.h + gap / 2, area.w));
  }
  let by = y - gap + BOTTOM_GAP;
  const bandX = exL < exR ? Math.max(b.x, exL) : b.x, bandW = exL < exR ? Math.min(b.x + b.w, exR) - bandX : b.w;
  if (s.conclusion) { H.label(ctx, slide, { x: bandX, y: by, w: bandW, h: BOTTOM_BAND_H }, s.conclusion, { fill: T.COLOR.navyDeep, sz: T.SIZE.panelHead }); by += BOTTOM_BAND_H + BOTTOM_GAP; }
  if (s.point) H.callout(ctx, slide, { x: bandX, y: by, w: bandW, h: BOTTOM_BAND_H }, H.pointLabel(ctx, sb), s.point);
  H.source(ctx, slide, sb);
}

module.exports = { composite, BLOCK_KINDS: Object.keys(BLOCKS) };
