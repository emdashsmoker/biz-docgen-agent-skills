"use strict";
// composite.js
// 영역 격자와 블록으로 분석 장표를 조판하는 composite 템플릿.
// 모델은 격자 비율과 블록 종류와 문구만 지정하고 좌표는 이 파일이 계산한다.
// 격자: rows[{h, cols[]}] 또는 cols[] (1행). 영역: regions[{title, block 또는 blocks[], note}]
// 블록 종류: table, bullets, text, stack, summary, labeled, grid, vsteps, chevrons, flow, flowchart, valuechain, porter, zones, logicmodel, goalsystem, house, canvas, market, matrix, pyramid, cycle, tree, governance, timeline, funnel, numbers, chart, image
// 블록은 자연 높이(내용 필요 높이 기준)에서 수용 높이(표 행, 상자 사이 간격, 도식 크기)까지 늘어나며 남는 높이는 행 사이 간격과 묶음 바깥 여백으로 돌림

const T = require("./tokens.js");
const A = require("./atoms.js");
const LB = require("./labels.js"); // 블록 고정 라벨 조회 (블록 필드, meta.labels, assets/labels.json 순)

const GAP_COL = 0.3; // 영역 사이 가로 간격
const GAP_COL_FLOW = 0.6; // 영역 사이 화살표가 들어갈 때의 가로 간격
const GAP_ROW = 0.3; // 행 사이 세로 간격
const GAP_ROW_MAX = 0.55; // 남는 높이를 행 사이에 나눌 때의 간격 상한
const GAP_ROW_FLOW = 0.45; // 행 사이 화살표가 들어갈 때의 세로 간격
const GAP_COL_DIV = 0.6, GAP_ROW_DIV = 0.5; // 칸 사이 구분선이 들어갈 때의 간격 (선 양쪽 여백 확보)
const CAPTION_H = 0.34; // 칸 캡션(굵은 좌측 정렬 한 줄) 높이
const ELASTIC_MIN = 0.7; // 도식 행이 줄어들 수 있는 하한 (지정 높이 대비)
const ELASTIC_BLOCK_MIN = 1.9; // 글 상자 블록과 한 칸에 쌓인 도식 블록의 높이 하한 (차트 레이블이 겹치지 않는 높이)
const SIBLING_STRETCH = 1.2; // 글 상자 블록이 이웃 칸 높이에 맞춰 늘어날 수 있는 배수 (자연 높이 대비)
const GAP_BLOCK = 0.2; // 한 영역 안 블록 사이 간격
const GAP_ITEM = 0.14; // 블록 안 상자 사이 간격
const LABEL_GAP = T.PANEL.LABEL_GAP; // 행 라벨 상자와 내용 상자 사이 간격
const GAP_ITEM_MAX = 0.36; // 상자 사이 간격이 늘어날 수 있는 상한 (칸 높이가 남을 때)
const HIER_GAP_X = 0.2, HIER_GAP_Y = 0.2; // 계층도(grid style hierarchy)의 칸 사이 가로와 세로 간격
const HIER_ROW_MIN = 0.5; // 계층도 행 높이 하한
const CELL_GAP_V = 0.1; // 라벨 행과 격자 행 사이 세로 간격 (가로 간격 0.06 은 라벨과 내용의 짝을 보이기 위해 좁게 유지)
const CELL_GAP_V_MAX = 0.24, HIER_GAP_Y_MAX = 0.4; // 칸 높이가 남을 때 행 사이 간격 상한 (일반 격자, 계층도)
const CELL_GAP_H = 0.14; // 일반 격자 칸 사이 가로 간격 (테두리 칸이 붙어 보이지 않도록 행 라벨 간격과 같은 값)
const GRID_FLOW_GAP = 0.46; // flow 격자의 열 사이 간격 (오른쪽 화살표 폭 0.28과 좌우 여백)
const STEP_GAP = 0.26, STEP_GAP_MAX = 0.5; // 세로 단계 사이 화살표 간격과 상한
const FLOW_GAP = 0.42, FLOW_GAP_MAX = 0.6; // 흐름 상자 사이 화살표 간격과 상한
const NOTE_H = 0.26; // 영역 주석(※) 높이
const CELL_SNAP = 0.3; // 표 칸이 이웃 칸보다 이만큼 이하로 짧으면 행 높이를 늘려 위아래 끝을 맞춤
const BOTTOM_BAND_H = 0.5; // 결론 밴드와 수행 Point 높이
const BOTTOM_GAP = 0.2;
const ARROW_W = 0.28, ARROW_H = 0.34; // 영역 사이 화살표
const CHART_MIN_H = 1.2, CHART_MIN_W = 2.4; // 4분면 배치까지 수용하는 차트 영역 하한 (그보다 작으면 레이블이 겹침)
const PIE_ASPECT_MAX = 2.0; // 원형 차트 칸의 폭 상한 (높이 대비)
const MATRIX_AXIS_PAD = 0.42; // 매트릭스 축 이름 자리
const MATRIX_ASPECT_MAX = 1.25; // 매트릭스 평면 폭 상한 (높이 대비)
const MARKER_D = 0.3, MARKER_D_WIDE = 0.38; // 매트릭스 번호 표식 지름 (한 자리 번호, 두 자리 번호가 있을 때 모든 표식)
const CIRCLED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"];

// ---------------------------------------------------------------- 측정
const itemsOf = (x) => (x == null ? [] : Array.isArray(x.items) ? x.items : x.text != null ? [x.text] : typeof x === "string" ? [x] : []);
const textOf = (it) => (typeof it === "string" ? it : (it && it.text) || "");
/** 본문 문구 목록. 줄바꿈으로 나뉜 문구는 항목 여러 개로 보아 항목마다 불릿을 붙임 (라벨과 제목의 줄바꿈은 개행 유지) */
const splitItems = (items) => (items || [])
  .flatMap((t) => (typeof t === "string" ? t.split("\n") : t && typeof t.text === "string" && t.text.includes("\n") ? t.text.split("\n").map((x) => ({ ...t, text: x })) : [t]))
  .filter((x) => x != null && (typeof x === "string" ? x.trim() !== "" : !(typeof x.text === "string" && x.text.trim() === "")));

/** 문구 목록이 폭 w 상자에서 차지하는 높이 (불릿 들여쓰기와 문단 간격 포함) */
function needH(items, w, sz, bullet) {
  // 불릿 항목 목록만 줄바꿈을 항목 구분으로 봄 (라벨, 제목, 결론 띠는 개행)
  const list = bullet ? splitItems(items) : (items || []).filter((x) => x != null && x !== "");
  if (!list.length) return 0;
  const indent = bullet && list.length > 1 ? T.PARA.bulletIndentIn : 0;
  const innerW = Math.max(0.3, w - 2 * T.PANEL.INSET - indent);
  const lines = list.reduce((a, t) => a + Math.max(1, A.estimateLines(textOf(t), innerW, sz)), 0);
  return lines * A.lineHeightIn(sz) + (list.length - 1) * (T.PARA.paraGapPt / 72) + 2 * T.PANEL.INSET;
}

/** 필요 높이 비율로 가용 높이를 배분. 모자라면 비례 축소, 남으면 비례 확대 */
function share(needs, avail, minEach) {
  const n = needs.map((v) => Math.max(minEach || 0.3, v));
  const sum = n.reduce((a, b) => a + b, 0) || 1;
  return n.map((v) => (v / sum) * avail);
}

/** 상자 열 배분. 가용 높이가 자연 높이 합보다 크면 상자는 자연 높이로 두고 남는 높이를 상자 사이 간격(상한 gapMax)에 먼저 배분
 *  간격이 상한에 닿은 뒤 남는 높이는 상자에 비례 배분. 가용 높이가 모자라면 기본 간격으로 두고 필요 높이 비율로 배분 */
function spread(needs, nats, avail, gap0, gapMax, minEach) {
  const n = needs.length;
  const nSum = nats.reduce((a, b) => a + b, 0);
  if (n < 2 || nSum + gap0 * (n - 1) >= avail) return { hs: share(needs, avail - gap0 * Math.max(0, n - 1), minEach), gap: gap0 };
  const gap = Math.min(gapMax, (avail - nSum) / (n - 1));
  const rest = avail - nSum - gap * (n - 1);
  return { hs: nats.map((v) => v + (rest * v) / (nSum || 1)), gap };
}

/** 행 높이 균등화: 가장 긴 행의 필요 높이가 평균 높이 안에 들면 모든 행을 같은 높이로 맞춤 (정보량이 비슷한 행의 크기 차이 제거) */
function evenRows(hs, needs) {
  if (hs.length < 2) return hs;
  const eq = hs.reduce((a, v) => a + v, 0) / hs.length;
  return Math.max(...needs) <= eq + 1e-6 ? hs.map(() => eq) : hs;
}

/** 형제 상자의 필요 높이 묶기. 큰 값부터 본문 한 줄 이내의 값을 한 묶음으로 보고 묶음 최댓값으로 올림
 *  줄 수 추정은 한 줄 경계에서 오차가 나므로 분량이 비슷한 상자가 한 줄 차이로 크기가 갈리지 않게 함. eligible 이 false 인 상자는 그대로 둠 */
function snapNeeds(needs, eligible) {
  const tol = A.lineHeightIn(T.SIZE.body) + 1e-6;
  const ok = (i) => !eligible || eligible[i];
  const out = needs.slice();
  let top = null;
  needs.map((v, i) => i).filter(ok).sort((a, b) => needs[b] - needs[a]).forEach((i) => {
    if (top === null || top - needs[i] > tol) top = needs[i];
    out[i] = top;
  });
  return out;
}

/** 본문 필요 높이(raw)를 snapNeeds 로 묶어 spread 로 배분. needsOf, natsOf 는 본문 높이 목록을 상자 단위 needs, nats 로 바꾸는 함수
 *  묶은 배분에서 원래 필요 높이보다 작아지는 상자가 있으면 묶지 않은 배분을 씀
 *  가용 높이가 모자라면 묶음으로 커진 상자가 가장 큰 상자의 몫을 가져가고 commonSize 가 묶음 전체 글꼴을 줄이기 때문 */
function spreadSnapped(needsOf, natsOf, raw, eligible, avail, gap0, gapMax, minEach) {
  const run = (body) => spread(needsOf(body), natsOf(body), avail, gap0, gapMax, minEach);
  const sp = run(snapNeeds(raw, eligible));
  const floor = needsOf(raw);
  return sp.hs.every((h, i) => h + 1e-6 >= floor[i]) ? sp : run(raw);
}

/** 같은 계층 상자들의 공통 글꼴 크기 (본문 12pt 에서 하한 11pt 까지) */
function commonSize(boxes, lists) {
  for (let sz = T.SIZE.body; sz >= T.SIZE.BODY_MIN; sz--) {
    const ok = boxes.every((b, i) => !lists[i] || !lists[i].length || needH(lists[i], b.w, sz, true) <= b.h + 0.02);
    if (ok) return sz;
  }
  return T.SIZE.BODY_MIN;
}

/** 같은 계층 칸들의 공통 문단 간격 (commonSize 와 같은 묶음). writeItems 와 같은 문구 분할로 칸마다 간격을 재어 최솟값을 씀
 *  불릿으로 그리지 않는 칸(라벨, 원통 등)은 boxes 에 null 로 둠 */
function commonGap(H, boxes, lists, sz) {
  return H.groupGap(boxes, lists.map(splitItems), { sz, forceBullet: true });
}

// ---------------------------------------------------------------- 공용 그리기
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
/** 두 점을 잇는 직선. 왼쪽이나 위쪽으로 향하는 선은 뒤집기로 방향을 표현하여 화살촉이 끝점에 오게 함 */
function seg(ctx, slide, x1, y1, x2, y2, arrow) {
  slide.addShape(ctx.pres.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1, line: { color: T.COLOR.textGray, width: 1, endArrowType: arrow ? "triangle" : undefined } });
}
function hline(ctx, slide, x, y, w, opt) {
  slide.addShape(ctx.pres.ShapeType.line, { x, y, w, h: 0, line: { color: T.COLOR.border, width: 1, dashType: opt && opt.dash ? "dash" : undefined, endArrowType: opt && opt.arrow ? "triangle" : undefined } });
}
/** 저장소 원통 (데이터베이스, 문서 저장소처럼 자료가 쌓이는 요소). 원통 윗면 아래 영역에 이름을 둠 */
function dbBox(ctx, slide, b, text, sz) {
  slide.addText(A.runsOf(A.parasFromString(text || "", { sz, color: T.COLOR.textDark, align: "center" })), {
    x: b.x, y: b.y, w: b.w, h: b.h, shape: ctx.pres.ShapeType.can, fill: { color: T.COLOR.tintBg }, line: { color: T.COLOR.border, width: T.PANEL.LINE_PT },
    valign: "middle", margin: A.boxMargin([T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET]), isTextBox: true, autoFit: false, objectName: `adj:${DB_CAN_ADJ}`,
  });
}
const DB_CAN_ADJ = 25000; // 원통 윗면 타원 높이 (도형 짧은 변 대비 25%)
const DB_ZONE_PAD_W = 0.8; // 구간 구성도의 원통 폭 = 이름 글줄 폭 + 좌우 여유 (넓은 칸에서 원판처럼 납작해지지 않게 함)
const isDb = (c) => !!(c && typeof c === "object" && c.shape === "db");
function vline(ctx, slide, x, y, h, opt) {
  slide.addShape(ctx.pres.ShapeType.line, { x, y, w: 0, h, line: { color: T.COLOR.border, width: 1, dashType: opt && opt.dash ? "dash" : undefined, endArrowType: opt && opt.arrow ? "triangle" : undefined } });
}

// ---------------------------------------------------------------- 블록
const BLOCKS = {};

/** 표. {head, rows, colW?, align?} (colW, align 생략 시 열 폭과 정렬 자동 산정) */
BLOCKS.table = (ctx, H, slide, box, k) => {
  if (!k.rows || !k.rows.length) { ctx.warn("composite table 행 없음"); return; }
  H.tableBlock(ctx, slide, box, k);
};

/** 불릿 상자. {head?, items} */
BLOCKS.bullets = (ctx, H, slide, box, k) => {
  const items = itemsOf(k);
  if (k.head) { H.panel(ctx, slide, box, { head: k.head, items, noWarn: true }); return; }
  H.frame(ctx, slide, box, { fill: k.fill === "tint" ? T.COLOR.tintBg : undefined });
  writeItems(ctx, H, slide, box, items, commonSize([box], [items]));
};

/** 메시지 상자. {text, style: navy | tint | box | plain} */
BLOCKS.text = (ctx, H, slide, box, k) => {
  const style = k.style || "box";
  const sz = k.sz || (box.h >= 0.7 ? T.SIZE.panelHead : T.SIZE.body);
  if (style === "navy") { H.label(ctx, slide, box, k.text || "", { sz }); return; }
  if (style === "tint") H.frame(ctx, slide, box, { fill: T.COLOR.tintHead });
  else if (style === "box") H.frame(ctx, slide, box);
  A.text(slide, box, k.text || "", { sz, bold: style !== "plain", align: k.align || "center", valign: "middle" });
};

/** 제목 상자 세로 적층. {items:[{head, items|text}]} */
BLOCKS.stack = (ctx, H, slide, box, k) => {
  const list = k.items || [];
  if (!list.length) return;
  const head = (i) => (list[i].head ? T.PANEL.HEAD_H : 0);
  const { hs, gap } = spreadSnapped((b) => b.map((v, i) => head(i) + v), (b) => b.map((v, i) => head(i) + grow(v, 0.4)), list.map((x) => needH(itemsOf(x), box.w, T.SIZE.body, true)), list.map((x) => itemsOf(x).length > 0), box.h, GAP_ITEM, GAP_ITEM_MAX, 0.55);
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

/** 종합 상자. 한 문장 결론 띠와 대응 항목을 네이비 테두리 하나에 담음 (영역별 분석 칸 오른쪽의 종합 열)
 *  {lead, items:[{head, items|text}]} 항목 사이는 가는 구분선, 항목 칸은 남는 높이를 같은 몫으로 나눠 가짐 */
const SUM_LEAD_MIN = 0.5; // 결론 띠 높이 하한 (한 줄 결론 14pt 와 위아래 여백)
const SUM_HEAD_GAP_PT = 3; // 항목 제목과 내용 사이 간격 (pt)
const SUM_RULE_INSET = 0.14; // 항목 구분선 좌우 들여쓰기
const SUMMARY_FILL_H = 4.6; // 종합 상자 수용 높이 (본문 높이 이상으로 두어 이웃 칸 높이를 따라감)
const sumLeadH = (k, w) => (k.lead ? Math.max(SUM_LEAD_MIN, needH([k.lead], w, T.SIZE.panelHead, false) + 0.08) : 0);
/** 항목 칸 필요 높이: 제목 줄과 내용 문구 (상자 여백 포함) */
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
  // 항목 칸은 같은 높이로 나누고 (가장 긴 항목이 들어가지 않으면 필요 높이에 남는 높이를 같은 몫으로 더함)
  const even = bodyH / list.length;
  const hs = tot > bodyH ? needs.map((v) => (v * bodyH) / tot) : Math.max(...needs) <= even ? needs.map(() => even) : needs.map((v) => v + (bodyH - tot) / list.length);
  // 가로 채움: 불릿 항목 글줄이 상자 안쪽 폭에서 차지하는 비율의 평균 (불릿 상자와 같은 하한)
  const aw = box.w - 2 * T.PANEL.INSET - T.PARA.bulletIndentIn;
  const bl = list.flatMap((x) => (itemsOf(x).length > 1 ? itemsOf(x).map(textOf) : []));
  if (bl.length > 1 && !bl.some((t) => /\[[^\]]+\]/.test(t))) {
    const hfill = bl.reduce((a, t) => a + Math.min(1, A.lineWidthIn(t, sz, false) / aw), 0) / bl.length;
    const hmax = Math.max(...bl.map((t) => Math.min(1, A.lineWidthIn(t, sz, false) / aw)));
    const wrapped = bl.filter((t) => A.lineWidthIn(t, sz, false) > aw);
    if (wrapped.length) ctx.warn(`종합 상자 항목 줄바꿈 ${wrapped.length}건 ('${wrapped[0].slice(0, 12)}', 한 줄 길이로 축약하거나 열 폭 확대)`);
    const dump = globalThis.process.env.HFILL_DUMP; // "all" 이면 기준 통과 상자도 기록 (채움 분포 점검용)
    if (dump && (dump === "all" || hfill < T.LIMIT.summaryFillMin || hmax < T.LIMIT.summaryMaxFillMin)) globalThis.process.stderr.write(`DUMP ${JSON.stringify({ id: ctx.sb.id, aw: +aw.toFixed(2), bw: +box.w.toFixed(2), sz, fill: +hfill.toFixed(3), max: +hmax.toFixed(3), items: bl })}\n`);
    if (hfill < T.LIMIT.summaryFillMin || hmax < T.LIMIT.summaryMaxFillMin) ctx.warn(`종합 상자 글 채움 평균 ${Math.round(hfill * 100)}%, 최장 ${Math.round(hmax * 100)}% ('${bl[0].slice(0, 12)}' 외 ${bl.length - 1}항목, 문구 보강이나 열 폭 축소)`);
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

/** 좌측 라벨과 우측 내용의 행. {rows:[{label, items|text}], labelW} */
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

/** 격자 칸 폭과 행별 필요 높이 (그리기와 자연 높이 측정이 같은 계산을 쓰도록 공용) */
const DIV_JOIN_TOL = 0.01; // 행별 세로 구분선을 한 줄로 잇는 위치 허용 오차 (인치)
const GRID_LABEL_W_MAX = 1.6; // 격자 라벨 열 폭 상한
function gridGeom(k, box) {
  const rows = k.rows || [];
  const hasLabel = rows.some((r) => r.label);
  const ncol = Math.max(...rows.map((r) => (r.cells || []).reduce((a, c) => a + ((c && c.span) || 1), 0)), (k.head || []).length, 1);
  // hierarchy 는 비전체계와 목표체계 같은 계층도: 라벨은 글자만 두고 칸 사이를 넓혀 층위를 여백으로 구분
  const hier = k.style === "hierarchy";
  const lg = hier ? HIER_GAP_X : 0.06; // 라벨과 칸 사이
  // 라벨 열 폭 하한: 가장 긴 라벨 어절이 한 줄에 들어가는 폭 (계층도 라벨은 여백 없는 글자, 그 외는 네이비 라벨 상자 폭 lw + lg - LABEL_GAP 기준)
  const labelMin = hasLabel ? A.wordWidthIn(rows.map((r) => r.label || ""), T.SIZE.body, true) + (hier ? 0 : 2 * T.PANEL.LABEL_MG_X + LABEL_GAP - lg) : 0;
  const lw = hasLabel ? Math.min(Math.max(k.labelW ? box.w * k.labelW : box.w * (hier ? 0.1 : 0.18), labelMin), GRID_LABEL_W_MAX) : 0;
  const gx = box.x + (hasLabel ? lw + lg : 0);
  const gw = box.w - (hasLabel ? lw + lg : 0);
  const cg = hier ? HIER_GAP_X : k.flow ? GRID_FLOW_GAP : CELL_GAP_H;
  const vg = hier ? HIER_GAP_Y : CELL_GAP_V;
  const cw = (gw - cg * (ncol - 1)) / ncol;
  const headH = k.head ? 0.34 : 0;
  // 행 sz 는 위계를 두는 행(비전, 미션 등)의 지정 크기. 미지정 행은 공통 크기
  const rowPt = (r) => (r.sz ? Math.max(T.SIZE.BODY_MIN, Math.min(r.sz, T.SIZE.headline)) : T.SIZE.body);
  const cellsOf = (r) => (r.cells || []).map((c) => ({ w: cw * ((c && c.span) || 1) + cg * (((c && c.span) || 1) - 1), items: itemsOf(typeof c === "string" ? { text: c } : c) }));
  const needs = rows.map((r) => Math.max(0.34, needH([r.label || ""], hier ? lw : lw + lg - LABEL_GAP, T.SIZE.body, false), ...cellsOf(r).map((c) => needH(c.items, c.w, rowPt(r), true))));
  return { rows, hier, hasLabel, lw, lg, gx, gw, cg, vg, cw, ncol, headH, rowPt, cellsOf, needs };
}

/** tintHead 채움 위 navy 글자의 대비 확인. 그 조합을 실제로 그리는 요소에서만 호출
 *  사용자 지정 색 조합이 하한 미달이어도 색은 바꾸지 않고 경고만 남김 (색 선택은 사용자 지정을 우선) */
function warnNavyOnTint(ctx, where) {
  const r = T.contrast(T.COLOR.navy, T.COLOR.tintHead);
  if (r < T.TINT_TEXT_CONTRAST_MIN) ctx.warn(`${where}: navy #${T.COLOR.navy} 글자와 tintHead #${T.COLOR.tintHead} 채움의 대비 ${r.toFixed(1)} < ${T.TINT_TEXT_CONTRAST_MIN}`);
}

/** 라벨 열과 칸 격자. {head?:[], rows:[{label?, sz?, cells:[text | {text|items, fill, span, bold, color, shape}]}], labelW, flow}
 *  칸 shape 값 db 는 저장소 원통
 *  flow 가 true 이면 열 사이를 넓혀 행 묶음 세로 가운데에 오른쪽 화살표를 둠 (현행, 기준, 개선처럼 열이 순서로 이어질 때) */
BLOCKS.grid = (ctx, H, slide, box, k) => {
  if (!(k.rows || []).length) return;
  if (k.rows.some((r) => (r.cells || []).some((c) => c && c.fill === "tint" && c.color === "navy"))) warnNavyOnTint(ctx, "grid tint 칸");
  const { rows, hier, hasLabel, lw, lg, gx, cg, vg: vg0, cw, ncol, headH, rowPt, cellsOf, needs } = gridGeom(k, box);
  const rowMin = hier ? HIER_ROW_MIN : 0.34;
  // 머리 행 아래 간격도 행 사이 간격과 같이 늘림
  const sp = spreadSnapped((b) => b, (b) => b.map((v) => grow(v, rowMin)), needs, rows.map((r) => !r.sz), box.h - (k.head ? headH + vg0 : 0), vg0, hier ? HIER_GAP_Y_MAX : CELL_GAP_V_MAX, rowMin);
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
  // 문단 간격도 글꼴 묶음과 같은 단위로 하나로 맞춤 (sz 를 따로 준 행은 행마다). 라벨 칸과 원통 칸은 불릿이 아니므로 제외
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

/** 세로 단계. {steps:[{title, items|text}], arrows, label} 좌측 단계 라벨과 우측 설명 */
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
    // 접두(Round 1. 등)가 붙은 제목이 한 줄을 넘으면 접두 뒤에서 줄을 바꿔 어절 중간 끊김을 막음
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

/** 가로 셰브론과 단계별 설명 상자. {steps:[{title, items|text}]} */
BLOCKS.chevrons = (ctx, H, slide, box, k) => {
  const st = k.steps || [];
  if (!st.length) return;
  const anyItems = st.some((s) => itemsOf(s).length);
  const chH = anyItems ? Math.min(0.55, box.h * 0.3) : Math.min(0.8, box.h);
  const top = anyItems ? box.y : box.y + (box.h - chH) / 2;
  const chev = { x: box.x, y: top, w: box.w, h: chH };
  H.chevronRow(ctx, slide, chev, st.map((s) => s.title || ""), { sz: T.SIZE.body });
  if (!anyItems) return;
  // 상자 우측을 셰브론 어깨(꼭짓점이 좁아지기 시작하는 지점)에 맞춤
  const cs = H.chevronCols(chev, st.length, box.y + chH + 0.12, box.h - chH - 0.12);
  const sz = commonSize(cs, st.map(itemsOf));
  const cgap = commonGap(H, cs, st.map(itemsOf), sz);
  cs.forEach((c, i) => { H.frame(ctx, slide, c); writeItems(ctx, H, slide, c, itemsOf(st[i]), sz, { groupGapPt: cgap }); });
};

/** 화살표로 잇는 상자 흐름. {nodes:[{title?, items|text, fill}], dir: h | v} */
BLOCKS.flow = (ctx, H, slide, box, k) => {
  const nodes = k.nodes || [];
  if (!nodes.length) return;
  const vertical = k.dir === "v";
  const headOf = (n) => (n.title && itemsOf(n).length ? T.PANEL.HEAD_H : 0);
  const sp = vertical ? spreadSnapped((b) => b.map((v, i) => headOf(nodes[i]) + (itemsOf(nodes[i]).length ? v : 0)), (b) => b.map((v, i) => headOf(nodes[i]) + grow(v, 0.4)), nodes.map((n) => needH(n.title && !itemsOf(n).length ? [n.title] : itemsOf(n), box.w, T.SIZE.body, true)), nodes.map((n) => itemsOf(n).length > 0), box.h, FLOW_GAP, FLOW_GAP_MAX, 0.4) : null;
  const gap = vertical ? sp.gap : FLOW_GAP;
  const parts = vertical
    ? (() => { let y = box.y; return sp.hs.map((h) => { const r = { x: box.x, y, w: box.w, h }; y += h + gap; return r; }); })()
    : H.cols(box, nodes.length, gap);
  const bodies = parts.map((p, i) => ({ w: p.w, h: p.h - (nodes[i].title && itemsOf(nodes[i]).length ? T.PANEL.HEAD_H : 0) }));
  const sz = commonSize(bodies, nodes.map(itemsOf));
  // 네이비 라벨 상자는 불릿이 아니므로 간격 묶음에서 제외
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

/** 2×2 매트릭스. {x:{label, low, high}, y:{label}, quadrants:[좌상, 우상, 좌하, 우하], items:[{label, x, y}], focus, legend}
 *  y 축 라벨은 세로 글자이므로 양끝 표기 칸을 두지 않고 방향 표기는 label 에 포함 */
BLOCKS.matrix = (ctx, H, slide, box, k) => {
  const items = k.items || [];
  const legend = k.legend != null ? k.legend : items.length > 0;
  // 번호 표식: 범례 상자를 두거나 같은 슬라이드의 표가 번호별 항목을 담을 때(numbered) 사용
  const numbered = k.numbered != null ? k.numbered : legend;
  const lgW = legend ? Math.min(box.w * 0.38, 3.0) : 0;
  const axisPad = MATRIX_AXIS_PAD;
  const ph = box.h - axisPad;
  // 사분면이 가로로 눌려 보이지 않도록 평면 폭을 높이의 MATRIX_ASPECT_MAX 배로 제한하고 평면과 범례 묶음을 칸 가운데에 둠
  const pw = Math.min(box.w - lgW - (legend ? 0.2 : 0) - axisPad, ph * MATRIX_ASPECT_MAX);
  const groupW = axisPad + pw + (legend ? 0.2 + lgW : 0);
  const ox = box.x + (box.w - groupW) / 2;
  const px = ox + axisPad, py = box.y, pW = pw, pH = ph;
  const qw = pW / 2, qh = pH / 2;
  const q = k.quadrants || [];
  if (k.focus != null && q[k.focus]) warnNavyOnTint(ctx, "matrix 초점 사분면");
  [[0, 0], [1, 0], [0, 1], [1, 1]].forEach(([c, r], i) => {
    const qb = { x: px + c * qw, y: py + r * qh, w: qw, h: qh };
    slide.addShape(ctx.pres.ShapeType.rect, { ...qb, fill: { color: k.focus === i ? T.COLOR.tintHead : T.COLOR.white }, line: { color: T.COLOR.borderLight, width: 0.5 } });
    if (q[i]) A.text(slide, { x: qb.x + 0.06, y: r === 0 ? qb.y + 0.04 : qb.y + qb.h - 0.34, w: qb.w - 0.12, h: 0.3 }, q[i], { sz: T.SIZE.body, bold: true, color: k.focus === i ? T.COLOR.navy : T.COLOR.textGray, align: c === 0 ? "left" : "right", mg: [0, 0, 0, 0] });
  });
  // 축: 좌측 세로축과 하단 가로축에 화살촉
  vline(ctx, slide, px, py + pH, -pH, { arrow: true });
  hline(ctx, slide, px, py + pH, pW + 0.05, { arrow: true });
  const xa = k.x || {}, ya = k.y || {};
  A.text(slide, { x: px, y: py + pH + 0.04, w: pW, h: 0.3 }, xa.label || "", { sz: T.SIZE.body, bold: true, align: "center", mg: [0, 0, 0, 0] });
  if (xa.low) A.text(slide, { x: px, y: py + pH + 0.04, w: 1.2, h: 0.3 }, xa.low, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textMuted, align: "left", mg: [0, 0, 0, 0] });
  if (xa.high) A.text(slide, { x: px + pW - 1.2, y: py + pH + 0.04, w: 1.2, h: 0.3 }, xa.high, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textMuted, align: "right", mg: [0, 0, 0, 0] });
  A.text(slide, { x: ox - 0.02, y: py, w: 0.34, h: pH }, ya.label || "", { sz: T.SIZE.body, bold: true, align: "center", vert: "vert270", mg: [0, 0, 0, 0] });
  // 번호가 두 자리(10 이상)면 원 안에서 줄바꿈되지 않도록 모든 표식을 같은 크기로 키움
  const d = numbered && items.length >= 10 ? MARKER_D_WIDE : MARKER_D;
  items.forEach((it, i) => {
    const cx = px + Math.max(0.05, Math.min(0.95, it.x != null ? it.x : 0.5)) * pW;
    const cy = py + (1 - Math.max(0.05, Math.min(0.95, it.y != null ? it.y : 0.5))) * pH;
    slide.addText(A.runsOf(A.parasFromString(numbered ? String(i + 1) : it.label || "", { sz: T.SIZE.BODY_MIN, b: true, color: numbered ? T.COLOR.white : T.COLOR.textDark, align: "center" })),
      numbered ? { x: cx - d / 2, y: cy - d / 2, w: d, h: d, shape: ctx.pres.ShapeType.ellipse, fill: { color: T.COLOR.navy }, line: { color: "FFFFFF", width: 0.75 }, valign: "middle", margin: 0, isTextBox: true, wrap: d !== MARKER_D_WIDE }
        : { x: cx - 0.8, y: cy - 0.16, w: 1.6, h: 0.32, shape: ctx.pres.ShapeType.rect, fill: { color: T.COLOR.white }, line: { color: T.COLOR.navy, width: 0.75 }, valign: "middle", margin: 0, isTextBox: true });
  });
  if (legend && items.length) {
    // 범례 상자는 항목 수에 맞는 높이로 두고 매트릭스의 세로 가운데에 맞춤
    const lh = Math.min(pH, needH(items.map((it, i) => `${i + 1}. ${it.label || ""}`), lgW, T.SIZE.body, false) + 0.1 * items.length + 0.1);
    const lb = { x: px + pW + 0.2, y: py + (pH - lh) / 2, w: lgW, h: lh };
    H.frame(ctx, slide, lb);
    const paras = items.map((it, i) => ({ align: "left", spcBef: i ? 6 : 0, runs: [{ t: `${i + 1}. ${it.label || ""}`, sz: T.SIZE.body, color: T.COLOR.textDark }] }));
    slide.addText(A.runsOf(A.fitParas(paras, lb.w - 0.2, lb.h - 0.16, T.SIZE.BODY_MIN)), { ...lb, isTextBox: true, valign: "middle", margin: A.boxMargin([0.1, 0.08, 0.1, 0.08]), autoFit: false });
  }
  return { x: ox, w: groupW }; // 그린 가로 범위 (아래 띠 폭 맞춤용)
};

/** 피라미드. {levels:[위에서 아래 순서], side?:[층별 설명]} */
const PYR_APEX_MG = 0.1; // 꼭짓점 삼각형 글의 좌우 여백 합
const PYR_APEX_TEXT_W = 0.6; // 꼭짓점 글 상자 아래쪽 글줄이 놓이는 높이의 삼각형 폭 비율 (글줄이 삼각형 밖으로 나가지 않는 폭)
BLOCKS.pyramid = (ctx, H, slide, box, k) => {
  const lv = k.levels || [];
  if (!lv.length) return;
  const side = k.side || [];
  const pw = side.length ? box.w * 0.46 : box.w;
  const n = lv.length, gap = 0.06;
  const lh = (box.h - gap * (n - 1)) / n;
  // 단계별 설명 칸은 문단 간격을 하나로 맞춤
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
    // 꼭짓점 삼각형의 글 영역은 밑변 폭의 절반이므로 좁은 판형에서 어절이 들어가지 않으면 삼각형 아래쪽 절반에 밑변 폭의 글 상자를 겹쳐 둠
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

/** 순환. {stages:[{title, text?}], center} 원 둘레에 단계 상자를 두고 진행 방향 화살촉 표시 */
BLOCKS.cycle = (ctx, H, slide, box, k) => {
  const st = k.stages || [];
  const n = st.length;
  if (n < 2) return;
  const cx = box.x + box.w / 2, cy = box.y + box.h / 2;
  const nw = Math.min(box.w * 0.34, 2.4), nh = Math.min(box.h * 0.26, 1.1);
  const rx = Math.max(0.5, box.w / 2 - nw / 2), ry = Math.max(0.4, box.h / 2 - nh / 2);
  slide.addShape(ctx.pres.ShapeType.ellipse, { x: cx - rx, y: cy - ry, w: 2 * rx, h: 2 * ry, fill: { color: T.COLOR.white, transparency: 100 }, line: { color: T.COLOR.border, width: 1.25 } });
  const ang = (i) => -Math.PI / 2 + (2 * Math.PI * i) / n;
  // 진행 방향 화살촉: 이웃 단계 사이 원호 중앙에 접선 방향으로 회전한 삼각형
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

/** 트리. {root, children:[{text, children:[text]}], top?, sides?:[{side, text, dash}]} 위에서 아래로 2단 전개
 *  top 은 root 위의 상위 주체(화살표로 연결), sides 는 root 좌우의 협력 주체(가로선 연결, dash 가 true 이면 점선) */
const TREE_TOP_DROP = 0.3; // 상위 주체와 root 사이 화살표 구간
const TREE_SIDE_GAP = 0.32; // root 와 좌우 주체 사이 가로선 길이
const TREE_SIDE_W_MAX = 2.4; // 좌우 주체 상자 폭 상한
const TREE_ROOT_H = 0.44, TREE_DROP = 0.36, TREE_L1_H = 0.44, TREE_L2_TOP = 0.22, TREE_L2_H = 0.42, TREE_L2_GAP = 0.1;
const TREE_DROP_EXTRA = 0.24, TREE_L2_GAP_EXTRA = 0.12; // 칸 높이가 남을 때 1단 연결선과 2단 상자 간격의 추가 상한
const TREE_L2_H_MIN = 0.34; // 칸 높이가 모자랄 때 2단 상자 높이 하한 (11pt 한 줄과 여백)
BLOCKS.tree = (ctx, H, slide, box, k) => {
  const ch = k.children || [];
  const rootH = TREE_ROOT_H, l1H = TREE_L1_H, l2H = TREE_L2_H;
  const rootW = Math.min(box.w * 0.4, 3.2);
  const rx = box.x + (box.w - rootW) / 2;
  const maxL2 = Math.max(0, ...ch.map((c) => (c.children || []).length));
  const topH = k.top ? rootH + TREE_TOP_DROP : 0;
  const needHAll = topH + rootH + TREE_DROP + l1H + (maxL2 ? TREE_L2_TOP + maxL2 * l2H + nGaps(maxL2) * TREE_L2_GAP : 0);
  // 칸 높이가 남으면 1단 연결선 길이와 2단 상자 간격을 늘리고 위쪽에 맞춤
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

/** 추진체계도. 가운데 세로 계선(연구개발비 전달과 관리 경로)과 좌우 심의, 협력 주체
 *  {spine:[주체], sides:[{at, side, text, dash}]}
 *  spine 은 위에서 아래로 연구개발비가 전달되는 주체 순서 (첫 주체는 네이비 채움)
 *  sides 는 at 번째 계선 주체와 같은 높이의 왼쪽(left) 또는 오른쪽(right)에 두고 가로선으로 연결 (dash 가 true 이면 점선) */
const GOV_NODE_H = 0.5, GOV_NODE_H_MAX = 0.62; // 계선 상자 높이와 상한
const GOV_GAP = 0.36, GOV_GAP_MAX = 0.6; // 계선 상자 사이 화살표 구간과 상한
const GOV_SPINE_W = 0.36, GOV_SPINE_W_MAX = 2.4; // 계선 상자 폭 (칸 폭 대비 비율, 상한)
const GOV_LINK_MIN = 0.3; // 좌우 주체 상자와 계선 상자 사이 연결선 최소 길이
const GOV_SIDE_W_MAX = 2.0; // 좌우 주체 상자 폭 상한
const GOV_TEXT_MG = A.TEXT_MG_IN[0]; // 계선 상자와 좌우 주체 상자의 문구 좌우 여백 (여백 미지정 글 상자와 같은 값)
BLOCKS.governance = (ctx, H, slide, box, k) => {
  const sp = (k.spine || []).map(textOf);
  if (!sp.length) return;
  const n = sp.length;
  const need = n * GOV_NODE_H + nGaps(n) * GOV_GAP;
  const scale = Math.min(1, box.h / need);
  // 남는 높이는 화살표 구간(상한까지), 상자 높이(상한까지) 순으로 배분하고 나머지는 세로 가운데 여백
  const gap = n > 1 ? Math.min(GOV_GAP_MAX, GOV_GAP * scale + Math.max(0, box.h - need) / (n - 1)) : 0;
  const nh = Math.min(GOV_NODE_H_MAX, Math.max(GOV_NODE_H * scale, (box.h - nGaps(n) * gap) / n));
  const top = box.y + Math.max(0, (box.h - n * nh - nGaps(n) * gap) / 2);
  const sides = (k.sides || []).filter((s) => s && sp[s.at] != null);
  // 어절 폭 하한: 좌우 주체 상자와 계선 상자가 가장 긴 어절을 본문 하한 크기로 한 줄에 담는 폭 (단일 문구 상자 기본 좌우 여백 포함)
  const wordMin = (ts, bold) => (ts.length ? A.wordWidthIn(ts, T.SIZE.BODY_MIN, bold) + 2 * GOV_TEXT_MG : 0);
  const spineMin = wordMin(sp, true), sideMin = wordMin(sides.map(textOf), false);
  let sw = Math.min(box.w * GOV_SPINE_W, GOV_SPINE_W_MAX);
  let side = Math.min(GOV_SIDE_W_MAX, (box.w - sw) / 2 - GOV_LINK_MIN);
  // 좌우 주체 상자가 어절 폭보다 좁으면 계선 상자 폭을 어절 폭 하한까지 줄여 좌우 상자에 넘김
  if (side < sideMin) {
    sw = Math.max(spineMin, box.w - 2 * (sideMin + GOV_LINK_MIN));
    side = Math.min(GOV_SIDE_W_MAX, (box.w - sw) / 2 - GOV_LINK_MIN);
    if (side < sideMin) ctx.warn(`governance 칸 폭 ${box.w.toFixed(2)}in 에서 좌우 주체 어절이 줄 중간에서 끊길 수 있음 (주체명 축약이나 칸 폭 확대)`);
  }
  const sx = box.x + (box.w - sw) / 2;
  const nodes = sp.map((t, i) => ({ x: sx, y: top + i * (nh + gap), w: sw, h: nh }));
  const seen = new Set();
  sides.forEach((s) => { const key = `${s.at}${s.side}`; if (seen.has(key)) ctx.warn(`governance 같은 자리의 좌우 주체 중복 (at ${s.at}, ${s.side})`); seen.add(key); });
  const sideBox = (s) => { const nd = nodes[s.at]; return { x: s.side === "left" ? box.x : box.x + box.w - side, y: nd.y, w: side, h: nh }; };
  // 높이 기준 공통 크기에서 어절이 상자 폭을 넘으면 본문 하한까지 한 단계씩 줄임
  const wordFits = (z) => nodes.every((nd, i) => A.wordWidthIn(sp[i], z, true) + 2 * GOV_TEXT_MG <= nd.w) && sides.every((s) => A.wordWidthIn(textOf(s), z, false) + 2 * GOV_TEXT_MG <= side);
  let sz = commonSize(nodes.concat(sides.map(sideBox)), sp.map((t) => [t]).concat(sides.map((s) => [textOf(s)])));
  while (sz > T.SIZE.BODY_MIN && !wordFits(sz)) sz--;
  // 맨 위 라벨 상자는 불릿이 아니므로 간격 묶음에서 제외
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

/** 타임라인. 가로 시간축 위에 시점 표식을 두고 표식 아래에 사건 상자를 배치
 *  {events:[{when, title?, items|text, mark}]}. mark 가 true 인 사건(현재 시점)은 채운 표식과 틴트 상자로 표시 */
const TL_WHEN_H = 0.3; // 시점 글자 줄 높이
const TL_AXIS_GAP = 0.14; // 시점 글자와 시간축 사이
const TL_DOT = 0.18; // 시점 표식 지름
const TL_DROP = 0.2; // 시간축과 사건 상자 사이
const TL_GAP = 0.2; // 사건 상자 사이 가로 간격
const TL_TITLE_H = 0.34; // 사건 상자 안 제목 줄 높이
const TL_HEAD = TL_WHEN_H + TL_AXIS_GAP + TL_DROP; // 사건 상자 위 고정 높이
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
  // 시간축: 첫 표식 왼쪽에서 시작하여 마지막 표식 오른쪽 끝에서 화살촉으로 시간 방향을 표시
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

/** 깔때기. 위에서 아래로 좁아지는 단계 띠와 단계별 설명 칸을 같은 높이로 대응
 *  {head?:[열 제목], stages:[{label, value, cells?:[items|text], items|text}]}. 위 단계(후보)는 옅은 색, 아래 단계(최종)는 짙은 색
 *  head 가 있으면 설명 칸을 열로 나누고 머리 행을 둠 (cells 의 순서가 head 의 순서). head 가 없으면 items 1열 */
const FN_W_SHARE = 0.38; // 칸 폭 대비 깔때기 폭
const FN_LEAD = 0.36; // 깔때기와 설명 칸 사이 연결 구간 폭
const FN_GAP = 0.08; // 단계 띠 사이 간격
const FN_COL_GAP = 0.14; // 설명 칸 열 사이 간격
const FN_HEAD_H = 0.34, FN_HEAD_GAP = 0.1; // 머리 행 높이와 아래 간격
const FN_BAND_H = 0.62, FN_BAND_H_MAX = 0.9; // 단계 띠 높이와 상한
const FN_NARROW = 0.42; // 맨 아래 띠 아랫변 폭 비율 (윗변 대비)
// 밝은 띠의 대상 수는 테마 색 글자로 강조. 사용자 지정 테마에서 띠 색과 대비가 이 값 미만이면 본문 글자색으로 조판
const FN_VALUE_CONTRAST_MIN = 3.0;
const fnDescW = (w) => w - w * FN_W_SHARE - FN_LEAD;
const fnCols = (k) => Math.max(1, (k.head || []).length);
const fnColW = (k, w) => (fnDescW(w) - FN_COL_GAP * (fnCols(k) - 1)) / fnCols(k);
const fnCells = (k, s) => (k.head ? (s.cells || []).map((c) => itemsOf(typeof c === "string" ? { text: c } : Array.isArray(c) ? { items: c } : c)) : [itemsOf(s)]);
const fnNeed = (k, s, w) => Math.max(0, ...fnCells(k, s).map((c) => needH(c, fnColW(k, w), T.SIZE.body, true)));
BLOCKS.funnel = (ctx, H, slide, box, k) => {
  const st = k.stages || [];
  if (st.length < 2) { ctx.warn("funnel 단계 2개 이상 필요"); return; }
  const n = st.length, nc = fnCols(k);
  const fw = box.w * FN_W_SHARE, dx = box.x + fw + FN_LEAD, cw = fnColW(k, box.w);
  const headH = k.head ? FN_HEAD_H + FN_HEAD_GAP : 0;
  // 띠 높이는 상한(설명 문구가 길면 그 높이)까지 늘리고 남는 높이는 위아래 여백으로 둠
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
    // 단계 띠: 윗변 wt, 아랫변 wb 의 사다리꼴을 자유 도형 점으로 그림 (도형 조절값에 의존하지 않음)
    slide.addShape(ctx.pres.ShapeType.custGeom, { x: cx - wt / 2, y, w: wt, h: bh, fill: { color: fillOf(i) }, line: { color: T.COLOR.white, width: 0.75 },
      points: [{ x: 0, y: 0 }, { x: wt, y: 0 }, { x: (wt + wb) / 2, y: bh }, { x: (wt - wb) / 2, y: bh }, { close: true }] });
    const paras = [{ align: "center", runs: [{ t: s.label || "", sz: T.SIZE.body, b: true, color: darkOf(i) ? T.COLOR.white : T.COLOR.textDark }] }];
    const valueColor = darkOf(i) ? T.COLOR.white : T.contrast(T.COLOR.navy, fillOf(i)) >= FN_VALUE_CONTRAST_MIN ? T.COLOR.navy : T.COLOR.textDark;
    if (s.value) paras.push({ align: "center", runs: [{ t: s.value, sz: T.SIZE.panelHead, b: true, color: valueColor }] });
    slide.addText(A.runsOf(paras), { x: cx - wb / 2, y, w: wb, h: bh, isTextBox: true, valign: "middle", margin: 0 });
    // 설명 칸과 연결선
    lists[i].forEach((its, c) => {
      const db = { x: dx + c * (cw + FN_COL_GAP), y, w: cw, h: bh };
      H.frame(ctx, slide, db);
      writeItems(ctx, H, slide, db, its, sz, { forceBullet: its.length > 1, groupGapPt: cgap });
    });
    for (let c = lists[i].length; c < nc; c++) H.frame(ctx, slide, { x: dx + c * (cw + FN_COL_GAP), y, w: cw, h: bh });
    hline(ctx, slide, cx + (wt + wb) / 4, y + bh / 2, dx - (cx + (wt + wb) / 4), { dash: true });
  });
};

/** 수치 강조 타일. {items:[{value, label, note?}]} */
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

/** 차트. {chart:{type, categories, series}} */
BLOCKS.chart = (ctx, H, slide, box, k) => {
  const spec = k.chart || k;
  if (box.h < CHART_MIN_H || box.w < CHART_MIN_W) ctx.warn(`composite chart 영역 ${box.w.toFixed(2)}x${box.h.toFixed(2)}in (권장 하한 ${CHART_MIN_W}x${CHART_MIN_H})`);
  // 원형은 높이가 지름을 정하므로 넓은 칸에서는 폭을 줄여 범례를 원 가까이 둠
  const round = spec.type === "pie" || spec.type === "doughnut";
  const w = round ? Math.min(box.w, box.h * PIE_ASPECT_MAX) : box.w;
  A.chart(ctx.pres, slide, { ...box, x: box.x + (box.w - w) / 2, w }, spec);
};

/** 이미지. {src, caption, label} */
BLOCKS.image = (ctx, H, slide, box, k) => {
  const capH = k.caption ? 0.3 : 0;
  A.image(ctx.pres, slide, { x: box.x, y: box.y, w: box.w, h: box.h - capH }, k.src, { caption: k.caption, label: k.label || "이미지" });
};

/** 가치사슬. 지원 기능 띠(선택), 단계 셰브론, 단계별 행, 공통 기반 띠(선택)를 위에서 아래로 배치
 *  기능 가치사슬은 지원 기능 띠를 본원적 기능 셰브론 위에 두어 지원 기능이 전 단계에 걸치는 구조를 표현
 *  산업 가치사슬은 공급 단계 셰브론 아래에 세부 분야 행을 두고 공통 기반 띠로 마감
 *  {stageLabel, stages:[], support:{label, bands:[{title, items|text}]}, rows:[{label, cells:[text | {items|text, mark}]}], base:{label, text}, labelW}
 *  mark 칸은 틴트 채움과 굵은 글자로 진단 대상 구간(중복, 공백, 취약)을 표시 */
const VC_CHEV_H = 0.6; // 단계 셰브론 높이 (단계명 14pt 1줄과 위아래 여백)
const VC_GAP = 0.14; // 띠, 셰브론, 행 사이 간격
const VC_BAND_TW = 1.5; // 지원 기능 띠 안 제목 칸 폭 상한
function vcGeom(k, box, H) {
  const stages = k.stages || [];
  const lw = Math.min(box.w * (k.labelW || 0.13), 1.5);
  const gx = box.x + lw + 0.06, gw = box.w - lw - 0.06;
  const bands = (k.support && k.support.bands) || [];
  const rows = k.rows || [];
  const bandTW = Math.min(gw * 0.2, VC_BAND_TW);
  const cols0 = H.chevronCols({ x: gx, y: 0, w: gw, h: VC_CHEV_H }, Math.max(1, stages.length), 0, 1);
  const colW = cols0.map((c) => c.w);
  // 칸 격자의 오른쪽 끝 (지원 기능 띠와 공통 기반 띠를 이 끝선에 맞춰 셰브론 꼭짓점만 밖으로 나가게 함)
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
  if (!g.stages.length) { ctx.warn("valuechain 단계(stages) 없음"); return; }
  const hs = share(g.needs, box.h - g.fixed, 0.4);
  const nb = g.bands.length, nr = g.rows.length;
  let y = box.y;
  if (nb) {
    const spanH = hs.slice(0, nb).reduce((a, h) => a + h, 0) + VC_GAP * (nb - 1);
    H.label(ctx, slide, { x: box.x, y, w: g.lw + 0.06 - LABEL_GAP, h: spanH }, LB.label("valuechain", "support.label", k.support.label), { sz: T.SIZE.body });
    // 지원 활동 띠는 문단 간격을 하나로 맞춤
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

/** 전통형 가치사슬 (Porter). 지원 활동 띠를 위에, 본원적 활동 열을 아래에 두고 오른쪽 화살촉으로 가치 창출 방향을 표시
 *  {support:[{title, text 또는 items}], primary:[{title, items, owner, mark}], supportLabel, primaryLabel, ownerLabel, tip}
 *  owner 는 활동별 담당 부서. mark 가 true 인 활동은 담당 칸을 틴트 채움과 굵은 글자로 표시 (중복, 공백 구간)
 *  tip 은 화살촉 안 문구 (예: 사업 성과). 지원 활동 띠와 본원적 활동 열의 오른쪽 끝을 화살촉 밑변에 맞춤 */
const PT_TIP_W = 0.85; // 화살촉 폭
const PT_TIP_GAP = 0.1; // 활동 묶음과 화살촉 밑변 사이 간격
const PT_TIP_NEXT_GAP = 0.2; // 화살촉 꼭짓점과 오른쪽 이웃 칸 사이 간격
const PT_GAP = 0.08; // 본원적 활동 열 사이와 영역 사이 간격
const PT_SUP_H = 0.3; // 지원 활동 띠 높이 (한 줄 문구. 본원적 활동보다 얇게 두어 보조 활동임을 표시)
const PT_SUP_GAP = 0.04; // 지원 활동 띠 사이 간격
const PT_LABEL_W = 0.9; // 왼쪽 라벨 열 폭 상한 (본원적 활동 열 폭 확보)
const PT_OWNER_H = 0.48; // 담당 부서 칸 높이 (좁은 라벨 열에서 "담당 부서" 두 줄을 담는 높이)
const PT_TITLE_W = 1.35; // 지원 활동 띠 안 제목 칸 폭 상한
const PT_TIP_TEXT_RATIO = 0.62; // 화살촉 폭 대비 문구 상자 폭 (밑변 쪽에 둠)
BLOCKS.porter = (ctx, H, slide, box, k) => {
  const sup = k.support || [], pri = k.primary || [];
  if (!pri.length) { ctx.warn("porter 본원적 활동(primary) 없음"); return; }
  // 라벨 상자 폭은 lw + 0.06 - LABEL_GAP. 좁은 판형에서도 라벨 어절이 한 줄에 들어가도록 어절 폭과 여백을 하한으로 둠 (상한 PT_LABEL_W 우선)
  const labels = [LB.label("porter", "supportLabel", k.supportLabel), LB.label("porter", "primaryLabel", k.primaryLabel), LB.label("porter", "ownerLabel", k.ownerLabel)];
  const lw = Math.min(PT_LABEL_W, Math.max(box.w * 0.1, A.wordWidthIn(labels, T.SIZE.body, true) + 2 * T.PANEL.LABEL_MG_X + LABEL_GAP - 0.06));
  // 오른쪽 이웃 칸이 있으면 꼭짓점을 열 간격 안으로 내어 이웃 칸과의 간격을 PT_TIP_NEXT_GAP 으로 둠 (이웃이 없으면 칸 오른쪽 끝)
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
  if (M.total > box.h + 0.01) ctx.warn(`porter 칸 높이 ${box.h.toFixed(2)}in < 내용 필요 ${M.total.toFixed(2)}in (문구 축소)`);
  // 남는 높이는 모두 본원적 활동 열에 배분 (지원 활동 띠는 한 줄 높이 유지)
  const supH = M.supH;
  const bodyH = M.bodyH + Math.max(0, box.h - M.total);
  const top = box.y;
  let y = top;
  if (sup.length) {
    const span = supH.reduce((a, v) => a + v, 0) + PT_SUP_GAP * (sup.length - 1);
    // 지원 활동 라벨은 틴트, 본원적 활동 라벨은 네이비로 두어 본원적 활동을 주 영역으로 표시
    H.label(ctx, slide, { x: box.x, y, w: lw + 0.06 - LABEL_GAP, h: span }, labels[0], { sz: T.SIZE.body, fill: T.COLOR.tintHead, color: T.COLOR.textDark });
    const sgap = commonGap(H, supH.map((h) => ({ w: gw - titleW, h })), sup.map(itemsOf), sz); // 지원 활동 띠는 문단 간격을 하나로 맞춤
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
  // 화살촉: 밑변을 활동 묶음 오른쪽 끝에 붙이고 꼭짓점을 묶음 세로 가운데에 둠
  const tx = gx + gw + PT_TIP_GAP, th = y - top;
  slide.addShape(ctx.pres.ShapeType.custGeom, { x: tx, y: top, w: PT_TIP_W, h: th, points: [{ x: 0, y: 0 }, { x: PT_TIP_W, y: th / 2 }, { x: 0, y: th }, { close: true }], fill: { color: T.COLOR.navy }, line: { color: "FFFFFF", width: 0, transparency: 100 } });
  if (k.tip) A.text(slide, { x: tx, y: top + th / 2 - 0.4, w: PT_TIP_W * PT_TIP_TEXT_RATIO, h: 0.8 }, k.tip, { sz: T.SIZE.body, bold: true, color: T.COLOR.white, align: "center", valign: "middle", mg: [0, 0, 0, 0] });
  return { x: box.x, w: tx + PT_TIP_W - box.x };
};

/** 구간 구성도. 구간별 머리 상자 아래에 구성요소 상자를 세로로 쌓고 구간 사이에 점선 구분선을 둠
 *  {zones:[{title, items:[text | {text, fill, shape}]}], band:{label, items:[]}}
 *  구성요소는 상자 1개에 이름 1개. shape 값 db 는 저장소 원통, fill 값 tint 는 성격이 다른 요소 표시. band 는 전 구간에 걸친 공통 요소(보안 등) */
const ZONE_HEAD_H = 0.4, ZONE_HEAD_GAP = 0.2; // 구간 머리 상자 높이와 아래 간격
const ZONE_ITEM_H = 0.42, ZONE_ITEM_GAP = 0.16, ZONE_ITEM_GAP_MAX = 0.3; // 구성요소 상자 높이와 간격
const ZONE_ITEM_W = 0.82; // 구간 폭 대비 구성요소 상자 폭
const ZONE_GAP = 0.5; // 구간 사이 간격 (점선 구분선 자리)
const ZONE_BAND_H = 0.46, ZONE_BAND_GAP = 0.3; // 공통 띠 높이와 위 간격
function zonesNeed(k) {
  const maxN = Math.max(1, ...(k.zones || []).map((z) => (z.items || []).length));
  return ZONE_HEAD_H + ZONE_HEAD_GAP + maxN * ZONE_ITEM_H + (maxN - 1) * ZONE_ITEM_GAP + (k.band ? ZONE_BAND_GAP + ZONE_BAND_H : 0);
}
BLOCKS.zones = (ctx, H, slide, box, k) => {
  const zones = k.zones || [];
  if (!zones.length) { ctx.warn("zones 구간 없음"); return; }
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

/** 사업 논리모형. 국가연구개발사업 예비타당성조사 수행 세부지침(2024) [그림 3-3] 구조를 고정 배치
 *  상하 방향은 사업 논리의 흐름, 좌우 방향은 사업 추진의 시간 흐름
 *  {issue, goal, beneficiary, input, activity, output, outcome, assumption, labels} 각 값은 문구 배열. labels 는 같은 키로 항목 제목을 바꿈 */
// 항목 제목 기본값은 assets/labels.json 의 logicmodel.labels (meta.labels.logicmodel.labels, 블록 labels 순으로 덮어씀)
const LM_ARROW_GAP = 0.26; // 행 사이 화살표 간격
const LM_PAD = 0.07; // 점선 묶음 안쪽 여백
const LM_HEAD_H = 0.28; // 항목 제목 띠 높이 (항목 8개를 한 장에 담기 위해 패널 제목보다 낮춤)
const LM_COL_GAP = 0.42; // 묶음 안 가로 화살표 간격
const LM_GOAL_SHARE = 0.5; // 목표와 수혜자 행에서 목표 상자 폭 비율 (지침 원형의 1:1 배치)
BLOCKS.logicmodel = (ctx, H, slide, box, k) => {
  const LML = LB.labels("logicmodel", "labels", k.labels); // 항목 제목 (labels 로 바꿈)
  const its = (key) => [].concat(k[key] || []).filter(Boolean);
  const HH = LM_HEAD_H;
  const inW = box.w - 2 * LM_PAD;
  const wGoal = (inW - LM_COL_GAP) * LM_GOAL_SHARE, wBen = inW - LM_COL_GAP - wGoal;
  const w4 = (inW - 3 * LM_COL_GAP) / 4;
  const four = ["input", "activity", "output", "outcome"];
  const nd = (key, w) => needH(its(key), w, T.SIZE.body, true);
  // 전폭 칸(문제/이슈, 가정)은 항목을 가로 칸으로 나란히 배치 (전폭 상자 오른쪽이 비지 않게 함)
  const wideCols = (key) => Math.max(1, its(key).length);
  const wideW = (key) => (box.w - LM_COL_GAP * (wideCols(key) - 1)) / wideCols(key);
  const ndWide = (key) => Math.max(0, ...its(key).map((t) => needH([t], wideW(key), T.SIZE.body, true)));
  const needs = [HH + ndWide("issue"), HH + Math.max(nd("goal", wGoal), nd("beneficiary", wBen)) + 2 * LM_PAD,
    HH + Math.max(...four.map((key) => nd(key, w4))) + 2 * LM_PAD, HH + ndWide("assumption")];
  const hs = share(needs, box.h - 3 * LM_ARROW_GAP, 0.6);
  const ys = hs.reduce((a, h, i) => a.concat(i ? a[i - 1] + hs[i - 1] + LM_ARROW_GAP : box.y), []);
  // 칸 위치: [키, x, y, w, h]
  const cells = [["issue", box.x, ys[0], box.w, hs[0]],
    ["goal", box.x + LM_PAD, ys[1] + LM_PAD, wGoal, hs[1] - 2 * LM_PAD], ["beneficiary", box.x + LM_PAD + wGoal + LM_COL_GAP, ys[1] + LM_PAD, wBen, hs[1] - 2 * LM_PAD],
    ...four.map((key, i) => [key, box.x + LM_PAD + i * (w4 + LM_COL_GAP), ys[2] + LM_PAD, w4, hs[2] - 2 * LM_PAD]),
    ["assumption", box.x, ys[3], box.w, hs[3]]];
  const sz = commonSize(cells.map((c) => ({ w: c[3], h: c[4] - HH })), cells.map((c) => its(c[0])));
  // 문단 간격은 그려지는 칸 단위(넓은 칸은 나뉜 열)로 재어 하나로 맞춤
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
  // 묶음 사이 화살표: 문제/이슈에서 아래로, 가정에서 위로
  arrowShape(ctx, slide, box.x + box.w / 2, ys[1] - LM_ARROW_GAP / 2, "down", 0.18, 0.2);
  arrowShape(ctx, slide, box.x + box.w / 2, ys[2] - LM_ARROW_GAP / 2, "down", 0.18, 0.2);
  arrowShape(ctx, slide, box.x + box.w / 2, ys[3] - LM_ARROW_GAP / 2, "up", 0.18, 0.2);
  // 묶음 안 시간 흐름 화살표
  arrowShape(ctx, slide, box.x + LM_PAD + wGoal + LM_COL_GAP / 2, ys[1] + hs[1] / 2, "right", 0.2, 0.24);
  [0, 1, 2].forEach((i) => arrowShape(ctx, slide, box.x + LM_PAD + (i + 1) * w4 + i * LM_COL_GAP + LM_COL_GAP / 2, ys[2] + hs[2] / 2, "right", 0.2, 0.24));
};

// ---------------------------------------------------------------- 사업목표체계와 비전하우스 (왼쪽 행 라벨 열과 위계 행)
const LV_LABEL_W = 0.95; // 행 라벨 열 폭
const LV_LABEL_GAP = 0.08; // 행 라벨 열과 내용 사이
const LV_BAND_H = 0.36; // 미션, 핵심가치 띠 높이
const LV_BAND_GAP = 0.06; // 비전하우스 층 사이 간격 (한 채의 집으로 읽히도록 좁게 유지)
/** 행 라벨: 회색 굵은 글자 (위계는 오른쪽 도형이 표현) */
function lvLabel(slide, x, y, h, text, w) {
  A.text(slide, { x, y, w: w || LV_LABEL_W, h }, text || "", { sz: T.SIZE.body, bold: true, color: T.COLOR.textGray, align: "center", valign: "middle", mg: [0, 0, 0, 0] });
}
/** 지붕 띠: 네이비 사다리꼴과 흰 굵은 글자 */
function lvRoof(ctx, slide, b, text) {
  const paras = A.fitParas(A.parasFromString(text || "", { sz: T.SIZE.panelHead, b: true, color: T.COLOR.white, align: "center" }), b.w - 2 * b.h, b.h - 0.04, T.SIZE.body);
  slide.addText(A.runsOf(paras), { x: b.x, y: b.y, w: b.w, h: b.h, shape: ctx.pres.ShapeType.trapezoid, fill: { color: T.COLOR.navyDeep }, line: { color: "FFFFFF", width: 0, transparency: 100 }, valign: "middle", margin: 0, isTextBox: true, autoFit: false });
}
/** 문단 묶음 상자 (제목 문단과 불릿 문단을 한 글 상자에 담음) */
function lvParasBox(ctx, H, slide, b, paras, fill, line) {
  H.frame(ctx, slide, b, { fill, line });
  slide.addText(A.runsOf(paras), { x: b.x, y: b.y, w: b.w, h: b.h, isTextBox: true, valign: "middle", margin: A.boxMargin([T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET]), autoFit: false });
}
/** 문단 묶음의 필요 높이 (상자 안 여백 포함). 문단마다 줄 수, 불릿 들여쓰기, 문단 앞 간격을 반영 */
function parasNeedH(paras, w) {
  const inner = w - 2 * T.PANEL.INSET;
  return paras.reduce((h, p) => h + Math.max(1, A.estimateLines(p.runs[0].t, inner - (p.bullet ? T.PARA.bulletIndentIn : 0), p.runs[0].sz, p.runs[0].b)) * A.lineHeightIn(p.runs[0].sz) + (p.spcBef || 0) / 72, 0) + 2 * T.PANEL.INSET;
}

/** 사업목표체계. 비전, 사업 목적, 사업 목표 띠와 성과 목표, 전략분야, 전략과제와 세부과제 열을 위에서 아래로 배치
 *  {vision, purpose, goal, performance:[{title, quant, qual} 또는 {title, items}], strategies:[{title, text}], tasks:[[{title, text}]], labels}. labels 는 행 라벨과 quant, qual 접두어를 바꿈
 *  열 수는 strategies 수. 같은 순번의 성과 목표, 전략분야, 전략과제가 한 열로 대응
 *  서식은 계층도 격자(grid style hierarchy)와 같음: 회색 굵은 행 라벨, 비전 네이비 칸, 목표 틴트 칸, 나머지 흰 칸, 층 사이 여백 */
// 행 라벨과 정량, 정성 접두어 기본값은 assets/labels.json 의 goalsystem.labels
const GS_BAND_MIN = 0.42; // 비전, 목적, 목표 띠 높이 하한
const GS_BOX_GROW = 1.3; // 칸 높이가 남을 때 열 상자가 늘어나는 배율 상한
const GS_TASK_GAP_PT = 8; // 전략과제 사이 문단 간격
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
  if (M.total > box.h + 0.01) ctx.warn(`goalsystem 칸 높이 ${box.h.toFixed(2)}in < 내용 필요 ${M.total.toFixed(2)}in (문구 축소나 행 비율 조정)`);
  // 남는 높이: 층 사이 간격을 상한까지 넓히고 열 상자를 배율 상한까지 늘린 뒤 나머지는 위아래 여백
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

/** 비전하우스. 미션 띠, 비전 지붕, 전략목표 기둥 머리, 전략과제 기둥 몸체, 핵심가치 기단(선택)을 한 채의 집으로 배치
 *  {mission, vision, pillars:[{title, items}], base:[문구], labels, numbered}. 기둥 묶음은 지붕보다 양옆을 들여 처마를 만듦
 *  numbered 가 false 가 아니면 전략목표 앞에 1., 전략과제 앞에 1-1. 번호를 붙임 (번호가 불릿을 대신함)
 *  base 는 핵심가치별 칸으로 나눠 조판하고 생략하면 기둥 아래를 바닥 띠로 닫음 */
// 행 라벨 기본값은 assets/labels.json 의 house.labels
const HOUSE_ROOF_H = 0.5; // 비전 지붕 높이
const HOUSE_EAVE = 0.18; // 기둥 묶음의 좌우 들임 (처마)
const HOUSE_PILLAR_GAP = 0.14; // 기둥 사이 간격
const HOUSE_FLOOR_H = 0.08; // 핵심가치 기단이 없을 때 기둥 아래 바닥 띠
const HOUSE_HEAD_PAD = 0.16; // 기둥 머리(전략목표) 글 위아래 여유 합
const HOUSE_TASK_GAP_PT = 10; // 전략과제 사이 문단 간격
const HOUSE_TASK_GAP_MAX_PT = 26; // 기둥 몸체 높이가 남을 때 전략과제 사이 간격 상한
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
  if (top + need(sz) + bottom > box.h + 0.01) ctx.warn(`house 칸 높이 ${box.h.toFixed(2)}in < 내용 필요 ${(top + need(sz) + bottom).toFixed(2)}in (문구 축소나 행 비율 조정)`);
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
    // 기둥 몸체가 남으면 과제 사이 간격을 넓혀 몸체 높이를 고르게 채움 (기둥 사이 간격은 가장 긴 기둥 기준으로 통일)
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

/** 순서도. 시작과 종료는 타원, 처리는 사각형, 판단은 마름모 (KS X ISO 5807 기호)
 *  {lanes?:[수행 주체], nodes:[{id, type: start|end|process|decision, text, lane, col, fill}], edges:[{from, to, label, route: hv|vh}]}
 *  lane 은 행(수행 주체), col 은 열(처리 순서). 좌표를 지정하여 같은 입력에서 같은 배치를 보장 */
const FC_NODE_H = { process: 0.5, decision: 0.72, start: 0.46, end: 0.46 };
const FC_NODE_W_MAX = 2.0; // 기호 폭 상한
const FC_NODE_W_RATIO = 0.74; // 열 폭 대비 기호 폭 (기호 사이 틈에 분기 라벨이 들어가는 폭 확보)
const FC_NODE_LANE_RATIO = 0.66; // 수행 주체 행 높이 대비 기호 높이 상한 (기호 위아래 여백 확보)
const FC_LANE_GAP = 0.1; // 수행 주체 행 사이 간격
const FC_BACK_DROP = 0.2; // 되돌림 선이 기호 아래로 내려가는 깊이
const FC_BACK_MIN = 0.08; // 되돌림 선과 기호 아래 끝 사이 최소 간격
const FC_LANE_EDGE = 0.06; // 되돌림 선과 수행 주체 행 아래 테두리 사이 여백
const FC_LABEL_W = 0.62, FC_LABEL_H = 0.22; // 분기 라벨(예, 아니오) 상자
const FC_LABEL_MIN_W = 0.46; // 기호 사이 틈에 두는 분기 라벨 폭 하한 (11pt 세 글자)
BLOCKS.flowchart = (ctx, H, slide, box, k) => {
  const nodes = k.nodes || [], edges = k.edges || [];
  if (!nodes.length) return;
  const hasLane = Array.isArray(k.lanes) && k.lanes.length > 0;
  // lanes 를 생략하면 라벨 없는 행을 node.lane 최댓값까지 둠 (lane 은 행 번호)
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
    // 마름모와 타원은 글상자가 기호 안쪽 사각형이므로 실제 글 폭 기준으로 크기를 맞춤
    const textW = type === "decision" ? nw * 0.5 : terminal ? nw * 0.7 : nw - 0.1;
    const textH = type === "decision" ? h * 0.5 : terminal ? h * 0.7 : h - 0.06;
    const paras = A.fitParas(A.parasFromString(n.text || "", { sz: T.SIZE.body, b: terminal, color: terminal ? T.COLOR.white : T.COLOR.textDark, align: "center" }), textW, textH, T.SIZE.BODY_MIN);
    slide.addText(A.runsOf(paras), { x: g.l, y: g.t, w: nw, h, shape: ctx.pres.ShapeType[SHAPE[type]], fill: { color: terminal ? T.COLOR.navy : n.fill === "tint" ? T.COLOR.tintHead : T.COLOR.white }, line: { color: terminal ? T.COLOR.navy : T.COLOR.border, width: 1 }, valign: "middle", margin: 0, isTextBox: true, autoFit: false });
  });
  // 같은 칸(lane, col)에 놓인 기호는 서로 겹치므로 빌드 경고 (col 을 생략하면 모두 0열)
  const cells = {};
  nodes.forEach((n) => { const key = `${G[n.id].lane},${n.col || 0}`; (cells[key] = cells[key] || []).push(n.id); });
  Object.entries(cells).filter(([, ids]) => ids.length > 1).forEach(([key, ids]) => ctx.warn(`flowchart 기호 위치 중복 (lane,col ${key}): ${ids.join(", ")}`));
  const lbl = (x, y, t) => t && A.text(slide, { x, y, w: FC_LABEL_W, h: FC_LABEL_H }, t, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textGray, align: "left", valign: "middle", mg: [0, 0, 0, 0] });
  edges.forEach((e) => {
    const a = G[e.from], b = G[e.to];
    if (!a || !b) { ctx.warn(`flowchart 연결 대상 없음 ${e.from} → ${e.to}`); return; }
    const sameRow = Math.abs(a.cy - b.cy) < 0.01, sameCol = Math.abs(a.cx - b.cx) < 0.01;
    if (sameRow && b.cx > a.cx) { seg(ctx, slide, a.r, a.cy, b.l, b.cy, true); lbl(a.r + 0.04, a.cy - FC_LABEL_H, e.label); return; }
    // 되돌림: 바로 왼쪽 기호로 가면 직선으로 잇고 사이에 기호가 있으면 기호 아래로 돌아감 (돌아가는 선은 수행 주체 행 안에 둠)
    const between = sameRow && Object.values(G).some((g) => g !== a && g !== b && g.lane === a.lane && g.cx > Math.min(a.cx, b.cx) + 0.01 && g.cx < Math.max(a.cx, b.cx) - 0.01);
    if (sameRow && !between) {
      seg(ctx, slide, a.l, a.cy, b.r, b.cy, true);
      // 분기 라벨은 두 기호 사이 틈의 선 아래 가운데에 둠 (기호와 겹치지 않게 틈 폭 안으로 제한)
      const gap = a.l - b.r, lw2 = Math.max(FC_LABEL_MIN_W, Math.min(FC_LABEL_W, gap - 0.04));
      if (e.label) A.text(slide, { x: b.r + (gap - lw2) / 2, y: a.cy + 0.03, w: lw2, h: FC_LABEL_H }, e.label, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textGray, align: "center", valign: "middle", mg: [0, 0, 0, 0] });
      return;
    }
    if (sameRow) {
      const yy = Math.min(Math.max(a.b, b.b) + FC_BACK_DROP, a.laneB - FC_LANE_EDGE);
      if (yy < Math.max(a.b, b.b) + FC_BACK_MIN) ctx.warn(`flowchart 되돌림 선 ${e.from} → ${e.to} 이 수행 주체 행 안에 들어가지 않음 (행 높이 비율 확대)`);
      seg(ctx, slide, a.cx, a.b, a.cx, yy, false); seg(ctx, slide, a.cx, yy, b.cx, yy, false); seg(ctx, slide, b.cx, yy, b.cx, b.b, true);
      lbl(a.cx + 0.04, a.b, e.label); return;
    }
    if (sameCol) { const down = b.cy > a.cy; seg(ctx, slide, a.cx, down ? a.b : a.t, b.cx, down ? b.t : b.b, true); lbl(a.cx + 0.04, down ? a.b : a.t - FC_LABEL_H, e.label); return; }
    const down = b.cy > a.cy, right = b.cx > a.cx;
    if (e.route === "vh") { // 세로 먼저, 가로 나중
      seg(ctx, slide, a.cx, down ? a.b : a.t, a.cx, b.cy, false); seg(ctx, slide, a.cx, b.cy, right ? b.l : b.r, b.cy, true);
      lbl(a.cx + 0.04, down ? a.b : a.t - FC_LABEL_H, e.label); return;
    }
    const sx = right ? a.r : a.l; // 가로 먼저, 세로 나중
    seg(ctx, slide, sx, a.cy, b.cx, a.cy, false); seg(ctx, slide, b.cx, a.cy, b.cx, down ? b.t : b.b, true);
    lbl(right ? sx + 0.04 : sx - FC_LABEL_W - 0.04, a.cy - FC_LABEL_H, e.label);
  });
};

/** 비즈니스 모델 캔버스. 원형 배치를 고정하여 조판 (블록 이름과 자리는 바꾸지 않음)
 *  상단 5열: 핵심 파트너 | 핵심 활동, 핵심 자원 | 가치 제안 | 고객 관계, 채널 | 고객 세그먼트. 하단 2칸: 비용 구조 | 수익원
 *  {partners, activities, resources, value, relationships, channels, segments, cost, revenue, numbered, labels}. 각 값은 문구 배열 또는 {items|text}. labels 는 같은 키로 블록 제목을 바꿈
 *  numbered 가 true 이면 캔버스 작성 순서(고객 세그먼트 1 ... 비용 구조 9) 번호를 블록 제목 오른쪽에 표기 */
const BMC = [ // 블록 제목 기본값은 assets/labels.json 의 canvas.labels
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
const BMC_TOP_SHARE = 0.68; // 상단 5열 높이 비율 (캔버스 원형의 상하 비율)
const BMC_GAP = 0.1; // 블록 사이 간격 (한 장의 캔버스로 읽히도록 좁게 유지)
const BMC_TITLE_H = 0.36; // 블록 제목 줄 높이
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
  // 같은 모양의 칸(긴 열, 반 칸, 아래 칸)끼리 문단 간격을 하나로 맞춤. 칸 높이가 배치로 정해지므로 모양이 다른 칸까지 묶으면 긴 열이 비어 보임
  const shapeOf = (d) => (d.bottom != null ? "bottom" : d.half == null ? "tall" : "half");
  const cgap = Object.fromEntries(["tall", "half", "bottom"].map((sh) => [sh, H.groupGap(BMC.map((d, i) => (shapeOf(d) === sh ? bodies[i] : null)), BMC.map(itemsFor), copt)]));
  const own = k.labels || {}, titles = LB.labels("canvas", "labels"); // 블록 제목 (labels 의 블록 키로 바꿈)
  BMC.forEach((d, i) => {
    const r = rectOf(d);
    H.frame(ctx, slide, r, { fill: d.core ? T.COLOR.tintBg : undefined });
    // 블록 제목: 네이비 굵은 글자와 제목 아래 짧은 구분선 (칸 채움 머리띠 대신 글자 위계로 구분)
    A.text(slide, { x: r.x + 0.1, y: r.y + 0.04, w: r.w - 0.2, h: BMC_TITLE_H - 0.04 }, own[d.key] || titles[d.key], { sz: T.SIZE.body, bold: true, color: T.COLOR.navy, align: "left", valign: "middle", mg: [0, 0, 0, 0] });
    if (k.numbered) A.text(slide, { x: r.x + r.w - 0.4, y: r.y + 0.04, w: 0.3, h: BMC_TITLE_H - 0.04 }, String(d.order), { sz: T.SIZE.body, bold: true, color: T.COLOR.textMuted, align: "right", valign: "middle", mg: [0, 0, 0, 0] });
    hline(ctx, slide, r.x + 0.1, r.y + BMC_TITLE_H, Math.min(r.w - 0.2, 0.9));
    const its = itemsFor(d);
    if (its.length) H.bulletsBlock(ctx, slide, { x: r.x, y: r.y + BMC_TITLE_H + 0.04, w: r.w, h: bodies[i].h }, its, { ...copt, groupGapPt: cgap[shapeOf(d)] });
  });
};

/** 시장 규모(TAM, SAM, SOM). 하단을 맞춘 원 3개와 시장별 설명 행을 수평 연결선으로 대응
 *  {levels:[{label, name, value, items[]}]} 바깥 원(전체 시장)부터 안쪽 원(수익 시장) 순서
 *  원 안에는 약칭과 규모, 오른쪽 행에는 시장 이름과 정의, 산출 근거를 둠
 *  설명 행은 원 영역 높이를 같은 몫으로 나누고 원 안 약칭은 행 가운데 높이에 두어 연결선을 한 줄 수평선으로 그음
 *  설명 칸 폭은 가장 긴 문구에 맞추고 묶음 전체를 칸 가운데에 둠 */
const MKT_RATIO = { 2: [1, 0.55], 3: [1, 0.7, 0.38] }; // 바깥 원 대비 지름 비율 (단계 수별. 원 띠 안에 행 가운데 높이가 들어오는 비율)
const MKT_W_SHARE = 0.4; // 칸 폭 대비 원 영역 폭 상한
const MKT_LEAD = 0.5; // 원 영역과 설명 행 사이 연결선 구간 폭
const MKT_CHIP_W = 1.4; // 설명 행의 시장 이름 칸 폭
const MKT_TAG_W = 1.4, MKT_TAG_H = 0.5; // 원 안 약칭과 규모 글상자
const MKT_DOT_X = 0.62; // 연결선 시작 표식의 원 중심 대비 가로 위치 상한
const MKT_FIT_STEP = 0.02; // 설명 칸 폭을 문구에 맞출 때 넓혀 가는 단위
/** 문구 목록을 한 줄씩 담는 설명 칸 폭 (불릿 들여쓰기와 상자 여백 포함). 칸 폭 상한을 넘으면 상한 */
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
  if (lv.length < 2) { ctx.warn("market 시장 단계 2개 이상 필요"); return; }
  const D = Math.min(box.h, box.w * MKT_W_SHARE);
  const y0 = box.y + (box.h - D) / 2;
  // 설명 행: 원 영역 높이를 같은 몫으로 나눔 (행 위아래 끝을 원의 위아래 끝에 맞춤)
  const gap = GAP_ITEM_MAX, rh = Math.min(1.3, (D - gap * (lv.length - 1)) / lv.length);
  const top = y0 + (D - (rh * lv.length + gap * (lv.length - 1))) / 2;
  const rows = lv.map((_, i) => ({ y: top + i * (rh + gap), h: rh }));
  // 설명 칸 폭은 가장 긴 문구에 맞추고 원, 연결선, 설명 칸 묶음을 칸 가운데에 둠
  const fixedW = D + MKT_LEAD + MKT_CHIP_W + 0.06;
  const cwMax = box.w - fixedW;
  const sz = commonSize(rows.map((r) => ({ w: cwMax, h: r.h })), lv.map((m) => m.items || []));
  const cw = Math.max(...lv.map((m) => fitItemsW(m.items, sz, cwMax)));
  const cgap = commonGap(H, rows.map((r) => ({ w: cw, h: r.h })), lv.map((m) => m.items || []), sz); // 설명 칸은 문단 간격을 하나로 맞춤
  const x0 = box.x + (box.w - fixedW - cw) / 2, cx = x0 + D / 2;
  const fills = [T.COLOR.navyPastel2, T.COLOR.navyPastel, T.COLOR.navy];
  const dia = MKT_RATIO[lv.length].map((r) => D * r);
  dia.forEach((d, i) => slide.addShape(ctx.pres.ShapeType.ellipse, { x: cx - d / 2, y: y0 + D - d, w: d, h: d, fill: { color: fills[i] }, line: { color: T.COLOR.white, width: 1 } }));
  const rx = x0 + D + MKT_LEAD;
  // 원 안 약칭 높이: 행 가운데 높이를 원 띠(바깥 원 윗부분에서 다음 원 윗부분까지) 안으로 제한
  const bandTop = dia.map((d) => y0 + D - d);
  const bandBot = dia.map((d, i) => (i < dia.length - 1 ? y0 + D - dia[i + 1] : y0 + D));
  const tagY = rows.map((r, i) => Math.min(Math.max(r.y + r.h / 2, bandTop[i] + MKT_TAG_H / 2 + 0.04), bandBot[i] - MKT_TAG_H / 2 - 0.04));
  // 연결선 시작 표식: 모든 단계가 같은 세로선 위에 오도록 가장 좁은 원 폭에 맞춘 가로 위치
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
    // 연결선: 원 안 표식에서 행 왼쪽까지 수평선 (약칭이 원 띠 끝에 걸려 높이가 다르면 꺾은선)
    const ink = { color: T.COLOR.textGray, width: 0.75 };
    const sy = tagY[i];
    slide.addShape(ctx.pres.ShapeType.ellipse, { x: dotX - 0.04, y: sy - 0.04, w: 0.08, h: 0.08, fill: { color: i === 0 ? T.COLOR.textDark : T.COLOR.white }, line: { color: i === 0 ? T.COLOR.textDark : T.COLOR.white, width: 0.5 } });
    if (Math.abs(ry - sy) < 0.01) { slide.addShape(ctx.pres.ShapeType.line, { x: dotX, y: ry, w: rx - dotX, h: 0, line: ink }); return; }
    const tx = x0 + D + MKT_LEAD / 2;
    slide.addShape(ctx.pres.ShapeType.line, { x: dotX, y: sy, w: tx - dotX, h: 0, line: ink });
    slide.addShape(ctx.pres.ShapeType.line, { x: tx, y: Math.min(sy, ry), w: 0, h: Math.abs(ry - sy), line: ink });
    slide.addShape(ctx.pres.ShapeType.line, { x: tx, y: ry, w: rx - tx, h: 0, line: ink });
  });
  return { x: x0, w: fixedW + cw }; // 그린 가로 범위 (아래 띠 폭 맞춤용)
};

// ---------------------------------------------------------------- 자연 높이와 수용 높이
// 글 상자 위주 블록이 내용보다 훨씬 큰 상자로 늘어나면 상자 안이 비어 보임
// 블록마다 내용 필요 높이의 FILL_EXPAND 배를 상한으로 하는 자연 높이와
// 상자 안을 비우지 않고 늘어날 수 있는 수용 높이(표 행 높이, 상자 사이 간격, 도식 크기)를 계산
// composite 는 행 높이를 자연 높이로 산정한 뒤 남는 높이를 도식 행, 수용 높이, 행 사이 간격, 세로 가운데 여백 순으로 배분 (planRows)
// 차트, 순서도, 논리모형, 그림처럼 주어진 공간에 맞춰 그리는 블록은 측정 대상에서 제외 (null)
// 피라미드, 매트릭스, 순환은 선호 높이를 자연 높이로 사용
const FILL_EXPAND = T.PANEL.FILL_EXPAND; // 상자 높이 상한 배수 (내용 필요 높이 대비)
const PYR_LEVEL_H = 0.62, MATRIX_PREF_H = 2.9, CYCLE_PREF_H = 3.8; // 피라미드 층 높이, 매트릭스와 순환 도식의 선호 높이
const PYR_LEVEL_MAX = 0.9, MATRIX_MAX_H = 4.6, CYCLE_MAX_H = 4.6; // 피라미드 층 높이, 매트릭스와 순환 도식의 수용 높이 상한
const TABLE_ROW_FIT = 0.38; // 표 행 높이 하한 (11pt 1줄과 셀 여백)
const TABLE_EXPAND = 1.2; // 표 행 자연 높이 배수 (1줄 행 0.38 인치를 0.46 인치로 산정)
// 최소 높이(내용 필요 높이) 측정 때는 확대 배수를 1 로 두어 같은 측정 함수를 재사용
let growFactor = FILL_EXPAND;
// 최소 높이 측정에서 종합 상자 항목을 재는 글꼴 크기. 기본은 하한(11pt), blockKeep 측정 동안만 본문(12pt)
let sumMinSz = T.SIZE.BODY_MIN;
const grow = (need, min) => Math.max(min, need * growFactor);
const sumGap = (n, gap) => gap * Math.max(0, n - 1);
const MEASURE = {
  bullets: (k, w) => (k.head ? T.PANEL.TITLE_H : 0) + grow(needH(itemsOf(k), w, T.SIZE.body, true), 0.5),
  text: (k, w) => grow(needH([k.text || ""], w, T.SIZE.body, false), 0.46),
  stack: (k, w) => (k.items || []).reduce((a, x) => a + (x.head ? T.PANEL.HEAD_H : 0) + grow(needH(itemsOf(x), w, T.SIZE.body, true), 0.4), 0) + sumGap((k.items || []).length, GAP_ITEM),
  // 종합 상자는 이웃 분석 칸 높이를 따라가므로 자연 높이를 확대 없는 필요 높이로 둠
  // 종합 상자는 칸이 모자라면 본문 하한(11pt)까지 줄여 담으므로 최소 높이 측정(growFactor 1)은 하한 크기로 산정 (blockKeep 은 본문 크기로 산정)
  summary: (k, w) => sumLeadH(k, w) + (k.items || []).reduce((a, x) => a + Math.max(0.5, sumItemNeed(x, w, growFactor > 1 ? T.SIZE.body : sumMinSz)), 0),
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
  // 표는 templates.tableMetrics 의 행별 필요 높이를 공유 (그리기와 측정이 같은 규칙)
  table: (k, w, H) => {
    if (!(k.rows || []).length) return TABLE_ROW_FIT;
    const M = H.tableMetrics(k, w);
    return M.headH + M.need.reduce((a, v, i) => a + (growFactor > 1 ? Math.min(M.cap[i], Math.max(v, TABLE_ROW_FIT) * TABLE_EXPAND) : v), 0);
  },
  // 최소 높이 측정(growFactor 1)에서는 2단 상자를 하한 높이로 산정
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
  // 도식은 칸을 채우지만 선호 높이를 두어 이웃 글 상자 칸과 높이를 맞춤
  pyramid: (k) => (k.levels || []).length * PYR_LEVEL_H + sumGap((k.levels || []).length, 0.06),
  matrix: () => MATRIX_PREF_H,
  cycle: () => CYCLE_PREF_H,
  valuechain: (k, w, H) => {
    const g = vcGeom(k, { x: 0, y: 0, w, h: 1 }, H);
    return g.fixed + g.needs.reduce((a, v) => a + grow(v, 0.4), 0);
  },
};
// 수용 높이: 자연 높이에서 상자 안을 비우지 않고 늘어날 수 있는 높이
// 표는 행 높이(ROW_H_MAX 까지), 상자 열은 상자 사이 간격, 도식은 도형 크기로 늘어나고 나머지 글 상자는 SIBLING_STRETCH 배까지 늘어남
const nGaps = (n) => Math.max(0, n - 1);
const CAPACITY = {
  // 표는 글자만 있는 한 줄 행이면 ROW_H_TEXT, 여러 줄 행이면 줄 간격 확대분, 하베이 볼이 있으면 ROW_H_MAX 까지 (templates.tableLayout 과 같은 규칙)
  table: (k, w, nat, H) => {
    if (!(k.rows || []).length) return nat;
    const M = H.tableMetrics(k, w);
    return Math.max(nat, M.headH + M.cap.reduce((x, v) => x + v, 0));
  },
  stack: (k, w, nat) => nat + nGaps((k.items || []).length) * (GAP_ITEM_MAX - GAP_ITEM),
  // 종합 상자는 이웃 분석 칸의 높이에 맞춰 칸 높이를 채움 (항목 칸이 남는 높이를 나눠 가짐)
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
  // 매트릭스는 평면이 정사각형에 가까워질 때까지 늘어남
  matrix: (k, w, nat) => {
    const legend = k.legend != null ? k.legend : (k.items || []).length > 0;
    const pw = Math.min(w - (legend ? Math.min(w * 0.38, 3.0) + 0.2 : 0) - MATRIX_AXIS_PAD, MATRIX_MAX_H);
    return Math.max(nat, Math.min(MATRIX_MAX_H, pw + MATRIX_AXIS_PAD));
  },
  cycle: () => CYCLE_MAX_H,
};
/** 블록 자연 높이. 측정 대상이 아니면 null */
function blockNeed(k, w, H) {
  const m = MEASURE[k.kind];
  const v = m ? m(k, w, H) : null;
  return v == null ? null : v + (k.caption ? CAPTION_H : 0);
}
/** 블록 수용 높이. 측정 대상이 아니면 null */
function blockCap(k, w, H) {
  const m = MEASURE[k.kind];
  const nat = m ? m(k, w, H) : null;
  if (nat == null) return null;
  const c = CAPACITY[k.kind];
  return (c ? c(k, w, nat, H) : nat * SIBLING_STRETCH) + (k.caption ? CAPTION_H : 0);
}
/** 블록 최소 높이 (확대 없는 내용 필요 높이). 측정 대상이 아니면 null */
function blockMin(k, w, H) {
  growFactor = 1;
  try { return blockNeed(k, w, H); } finally { growFactor = FILL_EXPAND; }
}
/** 종합 상자 12pt 유지 높이. 종합 상자 항목만 본문 크기로 재고 나머지는 최소 높이와 같음
 *  planRows 가 행을 줄일 때 종합 상자가 이웃 행 몫 때문에 11pt 로 내려가지 않게 하는 하한 */
function blockKeep(k, w, H) {
  sumMinSz = T.SIZE.body;
  try { return blockMin(k, w, H); } finally { sumMinSz = T.SIZE.BODY_MIN; }
}
/** 칸 캡션: 굵은 좌측 정렬 한 줄. 캡션 아래 남는 상자를 반환 */
function caption(slide, box, text) {
  A.text(slide, { x: box.x, y: box.y, w: box.w, h: CAPTION_H }, text, { sz: T.SIZE.body, bold: true, color: T.COLOR.textDark, align: "left", valign: "top", mg: [0, 0, 0, 0] });
  return { x: box.x, y: box.y + CAPTION_H, w: box.w, h: box.h - CAPTION_H };
}
/** 영역 높이 (제목, 주석, 블록 간격 포함). 블록 하나라도 측정 대상이 아니면 null
 *  mode 는 자연 높이(기본), 수용 높이("cap"), 최소 높이("min"), 종합 상자 12pt 유지 높이("keep") */
function regionNeed(rg, w, H, mode) {
  const blocks = rg.blocks || (rg.block ? [rg.block] : []);
  const measure = mode === "cap" ? blockCap : mode === "min" ? blockMin : mode === "keep" ? blockKeep : blockNeed;
  const needs = blocks.map((k) => measure(k, w, H));
  if (!blocks.length || needs.some((v) => v == null)) return null;
  return (rg.title ? T.PANEL.SUBHEAD_H : rg.caption ? CAPTION_H : 0) + (rg.note || rg.noteBand ? NOTE_H + 0.04 : 0) + needs.reduce((a, v) => a + v, 0) + sumGap(blocks.length, GAP_BLOCK);
}

// ---------------------------------------------------------------- 격자
function gridSpec(s, nRegions) {
  if (Array.isArray(s.rows) && s.rows.length) return s.rows.map((r) => ({ h: r.h || 1, cols: r.cols && r.cols.length ? r.cols : [1] }));
  if (Array.isArray(s.cols) && s.cols.length) return [{ h: 1, cols: s.cols }];
  return [{ h: 1, cols: Array(Math.max(1, nRegions)).fill(1) }];
}

/** 행별 칸 폭 목록 (영역 측정과 그리기가 같은 폭을 쓰도록 공용) */
function rowWidths(r, areaW, colGap) {
  const wSum = r.cols.reduce((a, c) => a + c, 0);
  const availW = areaW - colGap * (r.cols.length - 1);
  return r.cols.map((c) => (availW * c) / wSum);
}

/** 행 높이 배분
 *  글 상자 행은 자연 높이(내용 필요 높이의 FILL_EXPAND 배), 도식 행은 지정 비율 높이를 목표로 삼음
 *  목표 합이 본문보다 크면 최소 높이(글 상자 행은 내용 필요 높이, 도식 행은 지정 높이의 70%)를 먼저 확보하고 나머지를 비례 배분
 *  이때 본문이 종합 상자 12pt 유지 높이(keep) 합보다 크면 최소 높이 대신 keep 을 먼저 확보 (이웃 행 압축 몫으로 종합 상자가 11pt 로 내려가지 않게 함)
 *  목표 합이 본문보다 작으면 남는 높이를 도식 행, 행 사이 간격, 세로 가운데 여백 순으로 배분 */
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
    if (natural == null) { const elasticMin = assigned * ELASTIC_MIN; return { elastic: true, assigned, target: assigned, min: elasticMin, keep: elasticMin, cap: assigned }; }
    // 행 수용 높이: 칸들이 모두 채울 수 있는 높이(칸별 수용 높이의 최소)까지. 가장 큰 자연 높이보다 작아지지 않음
    const present = rgs.filter(({ rg }) => rg);
    const caps = present.map(({ rg, w }) => regionNeed(rg, w, H, "cap"));
    const cap = Math.max(natural, caps.length ? Math.min(...caps) : natural);
    // 최소 높이는 확대 없는 내용 필요 높이 (칸 제목, 캡션, 표 머리처럼 고정 높이 부분은 줄이지 않음)
    const min = Math.max(0, ...present.map(({ rg, w }) => regionNeed(rg, w, H, "min")));
    // 종합 상자를 12pt 로 담는 높이 (종합 상자가 없는 행은 min 과 같음)
    const keep = Math.max(min, ...present.map(({ rg, w }) => regionNeed(rg, w, H, "keep")));
    return { elastic: false, assigned, target: natural, min, keep, cap };
  });
  const tSum = plan.reduce((a, p) => a + p.target, 0);
  let freed = 0;
  if (tSum > availH) {
    const mSum = plan.reduce((a, p) => a + p.min, 0);
    const kSum = plan.reduce((a, p) => a + p.keep, 0);
    // 하한: keep 합이 본문 안에 들면 keep, 아니면 min (keep 을 지킬 수 없으면 기존 동작)
    const floorOf = (p) => (availH > kSum ? p.keep : p.min);
    const fSum = plan.reduce((a, p) => a + floorOf(p), 0);
    const k = availH > fSum ? (availH - fSum) / Math.max(0.01, tSum - fSum) : 0;
    plan.forEach((p) => { p.h = availH > fSum ? floorOf(p) + (p.target - floorOf(p)) * k : (p.min * availH) / mSum; });
  } else {
    plan.forEach((p) => { p.h = p.target; });
    freed = availH - tSum;
  }
  const elastic = plan.filter((p) => p.elastic);
  const wSum = elastic.reduce((a, p) => a + p.assigned, 0);
  elastic.forEach((p) => { p.h += (freed * p.assigned) / (wSum || 1); });
  if (elastic.length) freed = 0;
  // 도식 행이 없으면 남는 높이를 행 수용 높이까지 먼저 배분 (표 행 높이, 상자 사이 간격, 도식 크기)
  const room = plan.reduce((a, p) => a + (p.elastic ? 0 : Math.max(0, p.cap - p.h)), 0);
  if (freed > 0 && room > 0) {
    const g = Math.min(freed, room);
    plan.forEach((p) => { if (!p.elastic) p.h += (g * Math.max(0, p.cap - p.h)) / room; });
    freed -= g;
  }
  // 신축 행이 없으면 남는 높이를 먼저 행 사이 간격으로 나누어 숨 쉴 여백을 두고 나머지로 묶음을 세로 가운데에 둠
  const nGap = spec.length - 1;
  const gapExtra = nGap > 0 ? Math.min(Math.max(0, GAP_ROW_MAX - rowGap), freed / nGap) : 0;
  freed -= gapExtra * nGap;
  return { heights: plan.map((p) => p.h), gap: rowGap + gapExtra, offset: freed / 2 };
}

function composite(ctx, slide, sb, H) {
  const s = sb.slots || {};
  const b = H.body(ctx, sb);
  const spec0 = gridSpec(s, (s.regions || []).length);
  // 같은 행에 주석 칸이 있으면 이웃 칸도 주석 높이만큼 내용 하단을 올려 행 안 칸들의 하단을 맞춤 (주석 문구는 해당 칸에만 표기)
  const regions = (s.regions || []).slice();
  let ri0 = 0;
  spec0.forEach((r) => {
    const n = r.cols.length;
    if (regions.slice(ri0, ri0 + n).some((g) => g && g.note)) for (let j = ri0; j < ri0 + n; j++) if (regions[j] && !regions[j].note) regions[j] = { ...regions[j], noteBand: true };
    ri0 += n;
  });
  const bottom = (s.point ? BOTTOM_BAND_H + BOTTOM_GAP : 0) + (s.conclusion ? BOTTOM_BAND_H + BOTTOM_GAP : 0); // 각주 높이는 body() 가 제외
  const area = { x: b.x, y: b.y, w: b.w, h: b.h - bottom };
  const spec = gridSpec(s, regions.length);
  const slots = spec.reduce((a, r) => a + r.cols.length, 0);
  if (slots !== regions.length) ctx.warn(`composite 격자 칸 ${slots}개와 영역 ${regions.length}개 불일치`);
  const rowGap = s.rowFlow ? GAP_ROW_FLOW : s.dividers ? GAP_ROW_DIV : GAP_ROW;
  const colGap = s.flow ? GAP_COL_FLOW : s.dividers ? GAP_COL_DIV : GAP_COL;
  const { heights, gap, offset } = planRows(spec, regions, area, rowGap, colGap, H);
  let y = area.y + offset, idx = 0;
  const rowBoxes = [];
  const divV = []; // 행별 세로 구분선 {x, y1, y2}
  // 내용 가로 범위: 칸 제목이 없는 칸은 블록이 돌려준 그린 범위, 그 외는 칸 폭. 아래 띠(결론, 수행 Point)의 좌우 끝을 이 범위에 맞춤
  let exL = Infinity, exR = -Infinity;
  const extend = (x, w) => { exL = Math.min(exL, x); exR = Math.max(exR, x + w); };
  spec.forEach((r, ri) => {
    const rh = heights[ri];
    let x = area.x;
    const cells = rowWidths(r, area.w, colGap).map((w) => { const cell = { x, y, w, h: rh }; x += w + colGap; return cell; });
    const inners = [];
    cells.forEach((cell, ci) => {
      const rg = regions[idx++];
      const gapR = ci < cells.length - 1 && regions[idx] ? colGap : 0; // 오른쪽 이웃 칸까지의 열 간격 (도식 블록이 끝 모양을 맞출 때 사용)
      if (!rg) return;
      let box = cell;
      if (rg.title || rg.caption) extend(cell.x, cell.w);
      if (rg.title) box = H.subhead(ctx, slide, cell, s.numbered ? `${CIRCLED[idx - 1] || idx} ${rg.title}` : rg.title);
      else if (rg.caption) box = caption(slide, cell, rg.caption);
      if (rg.note || rg.noteBand) box = { ...box, h: box.h - NOTE_H - 0.04 };
      const blocks = (rg.blocks || (rg.block ? [rg.block] : [])).slice();
      // 블록 높이: 모두 측정 가능하면 자연 높이를 먼저 두고 남는 높이를 수용 높이까지 배분, 아니면 지정 가중치(h) 비율로 배분
      const needs = blocks.map((k) => blockNeed(k, box.w, H));
      const measured = needs.every((v) => v != null);
      const caps = measured ? blocks.map((k) => blockCap(k, box.w, H)) : null;
      const bGaps = GAP_BLOCK * (blocks.length - 1);
      // 이웃 칸보다 수용 높이가 작은 칸은 수용 높이까지만 늘리고 칸 제목 아래 남는 높이의 세로 가운데에 둠
      // 표 한 개만 담은 칸은 부족분이 CELL_SNAP 이하이면 행 높이를 조금 늘려 이웃 칸과 위아래 끝을 맞춤
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
      // 칸이 자연 높이보다 작으면 최소 높이를 먼저 두고 남는 높이를 (자연 높이 - 최소 높이) 비율로 배분
      const mins = measured ? blocks.map((k) => blockMin(k, box.w, H)) : null;
      const mSum = measured ? mins.reduce((a, v) => a + v, 0) : 0;
      if (measured && bAvail < mSum - 0.02) ctx.warn(`composite 칸 '${rg.title || rg.caption || ""}' 높이 ${bAvail.toFixed(2)}in < 내용 필요 ${mSum.toFixed(2)}in (넘침 위험. 항목 축소나 격자 조정)`);
      const wts = measured ? needs : blocks.map((k) => k.h || 1);
      const wtSum = wts.reduce((a, v) => a + v, 0) || 1;
      const squeeze = (j) => (bAvail >= mSum && nSum > mSum ? mins[j] + ((bAvail - mSum) * (needs[j] - mins[j])) / (nSum - mSum) : (bAvail * mins[j]) / (mSum || 1));
      // 도식 블록(측정 대상 아님)과 글 상자 블록이 섞인 칸은 글 상자 블록에 자연 높이(모자라면 최소 높이)를 먼저 주고 남는 높이를 도식 블록에 가중치(h) 비율로 배분
      const mixedFixed = !measured ? blocks.map((k, j) => (needs[j] == null ? null : needs[j])) : null;
      const mixed = (j) => {
        const fixedSum = mixedFixed.reduce((a, v) => a + (v || 0), 0);
        const minSum = blocks.reduce((a, k, i) => a + (mixedFixed[i] != null ? blockMin(k, box.w, H) : 0), 0);
        const flexW = blocks.reduce((a, k, i) => a + (mixedFixed[i] == null ? k.h || 1 : 0), 0) || 1;
        const flexMin = blocks.reduce((a, k, i) => a + (mixedFixed[i] == null ? ELASTIC_BLOCK_MIN : 0), 0);
        // 글 상자 블록 높이: 자연 높이, 부족하면 최소 높이와 자연 높이 사이에서 도식 블록 하한을 남기는 값
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
        if (!fn) { ctx.warn(`composite 블록 종류 '${k.kind}' 미지원 (${Object.keys(BLOCKS).join(", ")})`); extend(box.x, box.w); }
        else {
          const kb = { x: box.x, y: by, w: box.w, h: bh, gapR };
          // image 블록은 caption 을 이미지 아래 설명으로 조판하므로 블록 위 캡션을 생략 (같은 문구의 중복 방지)
          const topCaption = k.caption && k.kind !== "image";
          const ex = fn(ctx, H, slide, topCaption ? caption(slide, kb, k.caption) : kb, k);
          if (ex && ex.w > 0 && !topCaption) extend(ex.x, ex.w); else extend(kb.x, kb.w);
        }
        by += bh + GAP_BLOCK;
      });
      inners.push(box);
    });
    // 칸 사이 화살표는 이웃한 두 칸 내용의 세로 가운데에 둠
    if (s.flow) inners.slice(0, -1).forEach((bx, i) => { const nx = inners[i + 1]; const top = Math.min(bx.y, nx.y), bot = Math.max(bx.y + bx.h, nx.y + nx.h); arrowShape(ctx, slide, bx.x + bx.w + colGap / 2, (top + bot) / 2, "right"); });
    if (s.dividers) cells.slice(0, -1).forEach((c) => divV.push({ x: c.x + c.w + colGap / 2, y1: c.y, y2: c.y + c.h }));
    rowBoxes.push({ y, h: rh });
    y += rh + gap;
  });
  if (s.rowFlow) rowBoxes.slice(0, -1).forEach((r) => arrowShape(ctx, slide, area.x + area.w / 2, r.y + r.h + gap / 2, "down"));
  if (s.dividers) {
    // 이웃한 행의 세로 구분선이 같은 가로 위치이면 행 사이 간격을 건너 한 줄로 이어 가로 구분선과 십자로 만나게 함
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
