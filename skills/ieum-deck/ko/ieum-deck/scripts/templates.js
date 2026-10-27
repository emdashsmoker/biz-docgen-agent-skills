"use strict";
// templates.js
// 슬롯 템플릿. storyboard 의 template 이름으로 호출되며 slots(또는 panels, blocks) 값을 밴드 아래 본문에 조판한다.
// 좌표는 tokens.scaled(layout) 의 본문 영역을 기준으로 계산하며 항목 수(모듈 2-5, Task 2-6, 열 2-4, 행 가변)에 따라 재배치한다.
// 커스텀 슬라이드를 등록한 경우 own:N 템플릿(atoms.playOwn)이 원본 좌표로 재생하고, 본 파일은 내용에 따라 배치가 바뀌는 템플릿을 담당한다.

const T = require("./tokens.js");
const A = require("./atoms.js");
const C = require("./composite.js");
const LB = require("./labels.js"); // 고정 라벨 조회 (슬라이드 슬롯, meta.labels, assets/labels.json 순)

// 밴드 모드와 쪽번호 규칙. band: full | noMarker | headerOnly | blank
const SPEC = {
  cover: { band: "blank" }, contents: { band: "blank" }, divider: { band: "blank" }, end: { band: "blank" },
  digest: { band: "full" }, free: { band: "full" }, purpose: { band: "full" }, scope: { band: "full" }, features: { band: "full" },
  strategy: { band: "full" }, process: { band: "full" }, module_overview: { band: "full" }, task: { band: "full" }, task_multi: { band: "full" },
  bullets: { band: "full" }, table: { band: "full" }, chart_text: { band: "full" }, chart_two: { band: "full" }, compare: { band: "full" },
  roadmap: { band: "full" }, gantt: { band: "full" }, org: { band: "full" }, staff_card: { band: "full" }, swot: { band: "full" },
  orgchart: { band: "full" }, cards: { band: "full" }, steps: { band: "full" }, illustrative: { band: "full" }, conclusion: { band: "full" },
  composite: { band: "full" },
};

// ---------------------------------------------------------------- 공용 헬퍼
function body(ctx, sb) {
  const S = ctx.S;
  const top = sb.marker ? S.contentY : S.contentYNoMarker;
  // 출처 행이 있으면 본문을 그 위에서 끝내고 각주가 있으면 각주 줄 수만큼 더 올림
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
  // 네이비 라벨 셀 (표 머리, 패널 제목)
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
  // 채움 없는 영역 제목: 텍스트 + 하단 회색 실선 (라벨 채움보다 한 단계 낮은 위계)
  A.text(slide, { x: box.x, y: box.y, w: box.w, h: 0.34 }, text, { sz: T.SIZE.panelHead, color: T.COLOR.textDark, align: "center", mg: [0, 0, 0, 0] });
  slide.addShape(ctx.pres.ShapeType.line, { x: box.x, y: box.y + 0.36, w: box.w, h: 0, line: { color: T.COLOR.border, width: 0.5 } });
  return { x: box.x, y: box.y + T.PANEL.SUBHEAD_H, w: box.w, h: box.h - T.PANEL.SUBHEAD_H };
}
/** 같은 계층 상자들이 같은 글꼴을 쓰도록 공통 크기를 계산 (가장 빡빡한 상자에 맞춤) */
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

const PP_LINE_RATIO = 1.4; // PowerPoint 의 나눔고딕 줄 높이 근사 (글꼴 크기 대비). 렌더링 판정치 1.2 보다 높음
/** 불릿 목록 문단 구성. bullets 와 bulletFitSize 가 같은 문단으로 높이를 재도록 공유 */
function bulletParas(list, o, sz) {
  const paras = [];
  list.forEach((it) => {
    const tx = typeof it === "string" ? it : it.text;
    // 불릿은 항목 경계를 식별하는 표지이므로 항목이 하나인 상자에는 두 줄로 줄바꿈되어도 붙이지 않음
    const single = !o.forceBullet && list.length === 1 && !(typeof it !== "string" && it.sub && it.sub.length);
    // ※ 나 출처로 시작하는 줄은 주석이므로 불릿을 붙이지 않고 작은 회색으로 표기
    // "자료 수집" 같은 일반 항목과 구분하도록 출처와 자료는 콜론이 붙은 경우만 주석으로 판정 (영문 Source, Note 도 같은 기준)
    // meta.labels.notation.source 로 추가한 토큰("토큰:")도 주석으로 인식
    const isNote = /^\s*(※|출처\s*[:：]|자료\s*[:：]|[Ss]ources?\s*[:：]|[Nn]otes?\s*[:：])/.test(String(tx)) || LB.isExtraNote(tx);
    if (isNote) {
      paras.push({ bullet: false, indent: 0, marL: 0, align: "left", spcBef: o.gapPt || T.PARA.paraGapPt,
                   runs: [{ t: tx, sz: Math.max(T.SIZE.BODY_MIN, T.SIZE.note), color: T.COLOR.textMuted }] });
      return;
    }
    // numbered 목록은 항목 앞 번호(1-1. 등)가 불릿을 대신하므로 불릿을 붙이지 않음 (번호와 기호는 1번만 표기)
    paras.push({ bullet: !single && !o.numbered, indent: T.PARA.bulletIndentIn, align: single ? (o.align || "center") : "left", spcBef: o.gapPt || T.PARA.paraGapPt, runs: [{ t: tx, sz, b: !!o.bold, color: o.color || T.COLOR.textDark }] });
    if (typeof it !== "string" && it.sub) it.sub.forEach((s) => paras.push({ bullet: true, lvl: 1, buChar: "-", indent: T.PARA.bulletIndentIn, align: "left", runs: [{ t: s, sz: o.subSz || Math.max(T.SIZE.BODY_MIN, sz - 1), color: T.COLOR.textGray }] }));
  });
  return paras;
}
/** 상자에 맞춘 불릿 글꼴 크기. 같은 계층의 여러 상자에 공통 크기를 줄 때 상자별 값의 최솟값을 씀 */
function bulletFitSize(box, items, opt) {
  const o = opt || {};
  const sz = o.sz || T.SIZE.body;
  const list = Array.isArray(items) ? items : [items];
  const fitted = A.fitParas(bulletParas(list, o, sz), box.w - 2 * T.PANEL.INSET, box.h - 2 * T.PANEL.INSET, T.SIZE.BODY_MIN);
  const first = fitted.find((p) => p.bullet && !p.lvl) || fitted[0];
  return first ? first.runs[0].sz : sz;
}
/** 불릿 문단 높이 합 (ratio 는 줄 높이 배수, 생략하면 렌더링 판정치) */
function bulletParasH(ps, innerW, ratio) {
  return ps.reduce((h, p) => h + A.estimateLines(p.runs[0].t, innerW - T.PARA.bulletIndentIn, p.runs[0].sz, p.runs[0].b) * A.lineHeightIn(p.runs[0].sz, ratio) + (p.spcBef || 0) / 72, 0);
}
/** 상자에 맞춘 불릿 문단과 상자 안쪽 크기. bullets 와 bulletGap 이 같은 문단으로 간격을 재도록 공유 */
function fitBullets(box, items, o) {
  const list = Array.isArray(items) ? items : [items];
  const innerW = box.w - 2 * T.PANEL.INSET, innerH = box.h - 2 * T.PANEL.INSET;
  return { list, innerW, innerH, fitted: A.fitParas(bulletParas(list, o, o.sz || T.SIZE.body), innerW, innerH, T.SIZE.BODY_MIN) };
}
/** 남는 높이를 문단 사이에 나눠 더할 간격(pt)
 *  기준 높이는 PowerPoint 줄 높이(PP_LINE_RATIO)로 재어 PowerPoint 에서 줄이 높아져도 상자를 넘지 않게 함 */
function slackGapPt(fitted, innerW, innerH) {
  const slack = innerH - bulletParasH(fitted, innerW, PP_LINE_RATIO);
  return Math.min(T.PARA.paraGapMaxPt, Math.max(0, (slack * 72) / (fitted.length + 1)));
}
/** 상자 1개에 홀로 둘 때의 불릿 문단 간격(pt) = 기본 간격 + 남는 높이 분배. 문단이 1개 이하이면 나눌 간격이 없어 null */
function bulletGap(box, items, opt) {
  const o = opt || {};
  const { fitted, innerW, innerH } = fitBullets(box, items, o);
  return fitted.length > 1 ? (o.gapPt || T.PARA.paraGapPt) + slackGapPt(fitted, innerW, innerH) : null;
}
/** 같은 계층 형제 상자 묶음의 공통 문단 간격 (상자별 간격의 최솟값)
 *  상자마다 간격을 따로 나누면 이웃 상자끼리 간격이 어긋나므로 묶음에 하나의 간격을 씀. 가장 빡빡한 상자 기준이라 어느 상자도 높이가 늘지 않음
 *  opt 는 bullets 에 넘길 옵션 (상자마다 다르면 boxes 와 같은 순서의 배열). 빈 자리는 null 상자로 둠. 문단이 2개 이상인 상자가 없으면 undefined */
function groupGap(boxes, itemsList, opt) {
  const gaps = boxes.map((box, i) => (box ? bulletGap(box, itemsList[i] || [], Array.isArray(opt) ? opt[i] : opt) : null)).filter((g) => g != null);
  return gaps.length ? Math.min(...gaps) : undefined;
}
/** 불릿 목록. items: string | {text, sub:[]}. opt.groupGapPt 를 주면 남는 높이 분배 대신 그 값을 문단 간격으로 씀 (groupGap 결과) */
function bullets(ctx, slide, box, items, opt) {
  const o = opt || {};
  const { list, innerW, innerH, fitted: fit0 } = fitBullets(box, items, o);
  let fitted = fit0;
  // 남는 높이는 항목 간격으로만 분배. 글꼴은 계층 기준값을 유지하여 이웃 상자와 크기가 어긋나지 않게 함
  // 형제 상자 묶음은 공통 간격을 받아 본문 문단 간격을 그 값으로 맞춤 (하위 항목은 기본 간격을 넘는 몫만 받음)
  if (fitted.length > 1) {
    const base = o.gapPt || T.PARA.paraGapPt;
    const extra = o.groupGapPt != null ? o.groupGapPt - base : slackGapPt(fitted, innerW, innerH);
    fitted = fitted.map((p) => ({ ...p, spcBef: Math.max(0, (p.spcBef || 0) + extra) }));
  }
  const used = bulletParasH(fitted, innerW);
  if (used < box.h * (1 - T.PANEL.SLACK_WARN) && list.length > 1 && !o.noWarn) ctx.warn(`빈 공간 ${Math.round((1 - used / box.h) * 100)}% (불릿 ${list.length}개, 상자 ${box.h.toFixed(2)}in)`);
  // 가로 채움: 불릿 항목 글줄이 상자 안쪽 폭에서 차지하는 비율의 평균 (짧은 항목만 있으면 오른쪽이 비어 보임)
  const bl = fitted.filter((p) => p.bullet && !p.lvl);
  const placeholder = bl.some((p) => /\[[^\]]+\]/.test(p.runs[0].t));
  if (bl.length > 1 && !placeholder) {
    const aw = innerW - T.PARA.bulletIndentIn;
    const hfill = bl.reduce((a, p) => a + Math.min(1, A.lineWidthIn(p.runs[0].t, p.runs[0].sz, p.runs[0].b) / aw), 0) / bl.length;
    const hmax = Math.max(...bl.map((p) => Math.min(1, A.lineWidthIn(p.runs[0].t, p.runs[0].sz, p.runs[0].b) / aw)));
    if ((hfill < T.LIMIT.boxTextFillMin || hmax < T.LIMIT.boxTextMaxFillMin) && globalThis.process.env.HFILL_DUMP) globalThis.process.stderr.write(`DUMP ${JSON.stringify({ id: ctx.sb.id, aw: +aw.toFixed(2), sz: bl[0].runs[0].sz, items: bl.map((p) => p.runs[0].t) })}\n`);
    if (hfill < T.LIMIT.boxTextFillMin || hmax < T.LIMIT.boxTextMaxFillMin) ctx.warn(`상자 글 채움 평균 ${Math.round(hfill * 100)}%, 최장 ${Math.round(hmax * 100)}% ('${bl[0].runs[0].t.slice(0, 12)}' 외 ${bl.length - 1}항목, 문구 보강이나 칸 폭 축소)`);
  }
  slide.addText(A.runsOf(fitted), { x: box.x, y: box.y, w: box.w, h: box.h, isTextBox: true, valign: o.valign || "middle", margin: A.boxMargin([T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET, T.PANEL.INSET]), fill: o.fill ? { color: o.fill } : undefined, line: o.line ? { color: o.line, width: T.PANEL.LINE_PT } : undefined, autoFit: false });
}
/** 패널 몸체 상자 (라벨 바 아래) */
function panelBody(box, p) {
  const headH = p.head ? T.PANEL.TITLE_H : 0;
  return { x: box.x, y: box.y + headH, w: box.w, h: box.h - headH };
}
/** 패널: 라벨 바 + 테두리 몸체 + 불릿 */
function panel(ctx, slide, box, p) {
  if (p.head) label(ctx, slide, { x: box.x, y: box.y, w: box.w, h: T.PANEL.TITLE_H }, p.head, { fill: p.headFill });
  const bd = panelBody(box, p);
  frame(ctx, slide, bd, { fill: p.fill });
  if (p.items) bullets(ctx, slide, bd, p.items, { noWarn: p.noWarn, sz: p.sz, subSz: p.subSz, groupGapPt: p.groupGapPt });
  else if (p.text) A.text(slide, bd, p.text, { sz: T.SIZE.body, align: "center" });
  return bd;
}
/** 나란한 패널 묶음의 공통 문단 간격. ps 는 boxes 와 같은 순서로 panel 에 넘길 값 (빈 자리는 null) */
function panelsGap(boxes, ps) {
  const has = (p) => !!(p && p.items);
  return groupGap(boxes.map((b, i) => (has(ps[i]) ? panelBody(b, ps[i]) : null)), ps.map((p) => (has(p) ? p.items : [])), ps.map((p) => ({ sz: p && p.sz, subSz: p && p.subSz })));
}
/** 표. head[], rows[][], colW(비율, 생략 시 자동), align[] */
// 표 셀 값 판별. 셀 안 항목은 배열 원소나 줄바꿈으로 구분
const HARVEY = { "●": "full", "◐": "half", "○": "none" };
const cellItems = (v) => (Array.isArray(v) ? v : v && Array.isArray(v.items) ? v.items : null);
// 숫자 셀 값(예: 인원 36)은 문자열로 조판
const cellText = (v) => (typeof v === "string" ? v : typeof v === "number" ? String(v) : v && !Array.isArray(v) && v.text != null ? String(v.text) : "");
const isHarvey = (v) => typeof v === "string" && !!HARVEY[v.trim()];
/** 셀 항목 목록 (배열 원소와 줄바꿈으로 나눈 문구가 각각 항목 1개. 빈 항목 제외) */
const cellList = (v) => (v && v.merged ? [] : (cellItems(v) || [cellText(v)]).flatMap((t) => String(t == null ? "" : t).split("\n")).map((t) => t.trim()).filter(Boolean));
const cellBold = (v) => !!(v && typeof v === "object" && !Array.isArray(v) && v.bold);
const cellSpan = (v) => (v && v.colspan) || 1;
const TABLE_CELL_PAD = T.PANEL.CELL_MG[0]; // 표 셀 좌우 여백
const TABLE_CELL_VPAD = T.PANEL.CELL_MG[1] + T.PANEL.CELL_MG[3]; // 표 셀 위아래 여백 합
const TABLE_HEAD_PAD = 0.12; // 머리 셀 좌우 여백 합
const TABLE_COL_MIN = 0.5; // 열 폭 하한 (기호 한 글자 열과 하베이 볼 열)
const TABLE_BODY_GROUP_MIN = 3; // 남는 폭을 받는 자료 열 묶음의 최소 열 수 (역할 부호, 연도, 대안처럼 표 본체를 이루는 묶음)
const ROW_BREATH = 0.12; // 여러 줄 셀 행의 줄 간격 확대 뒤 남기는 위아래 여유 합
const QUESTION_END = /(는가|인가|은가|한가|던가|을까|할까|는지|\?)\s*$/; // 질문 문장 끝 (진단 질문 열은 왼쪽 정렬)
const DATA_CELL_MAX_CHARS = 2; // 역할 부호처럼 두 글자 이하 기호만 담는 열은 자료 열 (숫자, 하베이 볼 열 포함)
const LNSPC_MAX = 1.3; // 여러 줄 셀의 줄 간격 상한 (행 높이가 남을 때)
const sumOf = (a) => a.reduce((x, y) => x + y, 0);
/** 열 폭(인치). 각 열의 한 줄 폭(nat)과 어절 최대 폭(min)으로 배분
 *  모든 열이 한 줄에 들어가면 남는 폭을 한 줄 폭 비례로 나누고, 넘치면 어절 폭을 보장한 뒤 한 줄 폭까지의 부족분 비례로 나눔 */
function tableColW(tb, w, sz, listCols, dataCols) {
  // dataCols[i]: 자료 열 종류 문자열 (harvey, num, code) 또는 빈 문자열
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
  // 자료 열 묶음: 같은 종류(숫자, 하베이 볼, 두 글자 이하 기호)의 자료 열이 2개 이상 이어진 구간 (역할 부호, 연도별 수치, 대안별 평가)
  const groups = [];
  for (let i = 0; i < ncol; i++) {
    if (!dataCols || !dataCols[i]) continue;
    const last = groups[groups.length - 1];
    if (last && last[last.length - 1] === i - 1 && dataCols[i - 1] === dataCols[i]) last.push(i); else groups.push([i]);
  }
  const grouped = groups.filter((g) => g.length > 1);
  // 남는 폭은 표 본체를 이루는 3열 이상 묶음만 받음 (번호와 유형처럼 2열짜리 기호 묶음이 폭을 가져가지 않게 함)
  const inGroup = new Set(grouped.filter((g) => g.length >= TABLE_BODY_GROUP_MIN).flat());
  // 폭이 남으면 3열 이상 자료 열 묶음이 있을 때는 묶음에만, 없을 때는 모든 열에 한 줄 폭 비례로 배분 (문구 열은 문구 폭에 맞춤)
  // 모자라면 넓은 열부터 같은 폭 C 로 줄여 짧은 열은 한 줄을 유지 (어절 폭은 보장)
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
  // 묶음 안 열은 같은 폭으로 맞춤 (한 줄 폭이 평균보다 큰 열은 제외하고 반복)
  grouped.forEach((g) => {
    let pool = g.slice();
    for (let it = 0; it < g.length; it++) {
      const avg = sumOf(pool.map((i) => cw[i])) / pool.length;
      if (!pool.some((i) => nat[i] > avg + 1e-6)) { pool.forEach((i) => { cw[i] = avg; }); break; }
      pool = pool.filter((i) => nat[i] <= avg + 1e-6);
      if (pool.length < 2) break;
    }
  });
  const out = cw.map((v) => +v.toFixed(3));
  out[ncol - 1] = +(w - sumOf(out.slice(0, -1))).toFixed(3);
  return { cw: out, fill: sN / w };
}
/** 표 열 폭, 열 서식, 행별 필요 높이와 상한
 *  열 서식: 항목 2개 이상 셀이 있는 열은 모든 셀에 불릿과 왼쪽 정렬, 질문 문장 열은 왼쪽 정렬, 그 외 열은 가운데 정렬
 *  행 높이 상한: 글자만 있는 한 줄 행은 ROW_H_TEXT, 여러 줄 행은 줄 간격 확대분, 하베이 볼이 있는 표는 ROW_H_MAX */
function tableMetrics(tb, w, szOpt) {
  const ncol = tb.head ? tb.head.length : tb.rows[0].length;
  const sz = szOpt || (tb.rows.length > 10 ? T.SIZE.tableDense : T.SIZE.tableBody);
  const lh = A.lineHeightIn(sz, T.METRIC.TABLE_LINE_HEIGHT);
  const fixed = tb.colW && tb.colW.length === ncol;
  const colOf = (i) => tb.rows.map((r) => r[i]).filter((c) => c != null && cellSpan(c) === 1 && !c.merged);
  const listCols = Array.from({ length: ncol }, (_, i) => colOf(i).some((c) => cellList(c).length > 1));
  const isNum = (t) => /^[\d.,%+\-~ ]+$/.test(t);
  const textsOf = (i) => colOf(i).map((c) => cellList(c).join(" ")).filter(Boolean);
  // 자료 열 종류: 하베이 볼, 숫자, 두 글자 이하 기호 (그 외 열은 문구 열)
  const kindOf = (ts) => (!ts.length ? "" : ts.every(isHarvey) ? "harvey" : ts.every(isNum) ? "num" : ts.every((t) => t.length <= DATA_CELL_MAX_CHARS) ? "code" : "");
  const dataCols = listCols.map((l, i) => (l ? "" : kindOf(textsOf(i))));
  const colw = fixed ? tb.colW.map((r) => +((w * r) / sumOf(tb.colW)).toFixed(3)) : tableColW(tb, w, sz, listCols, dataCols).cw;
  const innerOf = (cw, i, span) => Math.max(0.3, sumOf(cw.slice(i, i + span)) - 2 * TABLE_CELL_PAD - (listCols[i] ? T.PARA.bulletIndentIn : 0));
  // 숫자 열은 자릿수 대조를 위해 오른쪽 정렬 (모든 표에서 같은 규칙을 적용하여 표 사이 정렬 혼재 방지)
  // 항목 2개 이상 셀이 있는 열과 질문 문장 열은 왼쪽 정렬, 그 외 열(한 줄 문구, 하베이 볼, 기호)은 가운데 정렬
  const aligns = tb.align || listCols.map((l, i) => (dataCols[i] === "num" ? "right" : l || textsOf(i).some((t) => QUESTION_END.test(t)) ? "left" : "center"));
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
  // 글자 채움: 열별 한 줄 폭 합이 표 폭에서 차지하는 비율 (자리 표기 셀이 있는 표는 실제 값 기재 전이므로 제외)
  const placeholder = tb.rows.some((r) => r.some((c) => /^\[[^\]]+\]$/.test(cellText(c).trim())));
  const fill = placeholder ? 1 : tableColW(tb, w, sz, listCols, dataCols).fill;
  return { ncol, colw, sz, lh, lines, need, cap, headH, visual, listCols, aligns, linesOf, fill };
}
/** 높이 h 안의 행 높이. 필요 높이를 먼저 두고 남는 높이는 낮은 행부터 같은 높이가 되도록 상한까지 채움 */
function tableLayout(tb, w, h, szOpt) {
  const M = tableMetrics(tb, w, szOpt);
  const avail = Math.max(0.1, h - M.headH);
  const nSum = M.need.reduce((a, b) => a + b, 0);
  let rows;
  if (avail <= nSum) rows = M.need.map((v) => (v * avail) / nSum);
  else {
    // _fill 은 이웃 칸과 끝을 맞추기 위해 행 높이 상한을 넘어 가용 높이까지 채우는 지정 (composite 가 부족분이 작을 때만 지정)
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
  if (L.fill < T.LIMIT.tableFillMin && !o.noWarn) ctx.warn(`표 글자 채움 ${Math.round(L.fill * 100)}% (셀 문구 보강, 열 추가, 칸 폭 축소 중 선택)`);
  const hts = tb.head ? [headH, ...L.rows] : L.rows.slice();
  const rowHt = (ri) => hts[ri];
  const rowY = (ri) => hts.slice(0, ri).reduce((a, b) => a + b, 0);
  const colX = (ci) => box.x + colw.slice(0, ci).reduce((a, w2) => a + w2, 0);
  const mk = (txt, i, head) => {
    const at = txt && typeof txt === "object" && !Array.isArray(txt) ? txt : {};
    const runOf = (t) => ({ t: String(t), sz, b: head || !!at.bold, color: head ? T.COLOR.white : T.COLOR.textDark });
    const items = head ? [String(txt)] : cellList(txt);
    // 항목 2개 이상 셀만 항목마다 불릿 (항목 경계 식별). 같은 열의 한 항목 셀은 불릿 없이 열 정렬(좌측)을 따름
    const paras = !head && items.length > 1
      ? items.map((t) => ({ align: "left", bullet: true, indent: T.PARA.bulletIndentIn, runs: [runOf(t)] }))
      : [{ align: head ? "center" : aligns[i], runs: [runOf(items.join(" "))] }];
    return { fill: head ? T.COLOR.navy : at.fill || undefined, paras, colspan: at.colspan, rowspan: at.rowspan, merged: at.merged };
  };
  const rowsOut = [];
  if (tb.head) rowsOut.push(tb.head.map((h, i) => mk(h, i, true)));
  tb.rows.forEach((r) => rowsOut.push(r.map((c, i) => mk(c, i, false))));
  // 여러 줄 셀은 행 높이가 남는 만큼 줄 간격을 넓혀 셀 여백을 글줄 사이로 나눔
  tb.rows.forEach((r, ri) => r.forEach((c, ci) => {
    const cell = rowsOut[ri + (tb.head ? 1 : 0)][ci];
    if (!cell || c && c.merged) return;
    const lines = L.linesOf(c, ci);
    if (lines < 2) return;
    const spc = Math.min(LNSPC_MAX, (L.rows[ri] - TABLE_CELL_VPAD - ROW_BREATH) / (lines * lh));
    if (spc > 1.05) cell.paras = cell.paras.map((p) => ({ ...p, lnSpc: +spc.toFixed(2) }));
  }));
  // 하베이 볼: ● ◐ ○ 셀은 글자를 비우고 셀 가운데에 원 도형으로 그림
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
    // 본문 글자와 같은 색을 써서 표 안에서 튀지 않게 함
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
/** 셰브론 행의 칸 폭과 꼭짓점 폭. 기본 adj 50000 에서 꼭짓점 폭은 짧은 변의 절반 */
function chevronGeom(box, n, h) {
  const ov = T.PANEL.CHEVRON_OVERLAP;
  const w = (box.w + ov * (n - 1)) / n;
  return { ov, w, pointW: 0.5 * Math.min(w, h || box.h) };
}
/** 셰브론 아래 상자 열. 상자 좌측은 셰브론 꼬리 모서리, 우측은 꼭짓점이 좁아지기 시작하는 어깨에 맞춤 */
function chevronCols(chev, n, y, h) {
  const g = chevronGeom(chev, n, chev.h);
  return Array.from({ length: n }, (_, i) => ({ x: chev.x + i * (g.w - g.ov), y, w: g.w - g.pointW, h }));
}
/** 셰브론 행. steps: string[] 또는 {title, sub}[] */
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
/** 결론 상자: 좌측 네이비 라벨 + 우측 틴트 메시지 */
/** 결론 밴드 라벨. 슬라이드 pointLabel, meta.pointLabel, meta.labels.common.pointLabel, 기본값 순 */
/** 각주 줄 수에 해당하는 높이 (인치) */
function noteRows(sb) {
  return 0.2 * [].concat((sb && sb.footnotes) || []).filter(Boolean).length;
}
function pointLabel(ctx, sb) {
  return (sb && sb.pointLabel) || (ctx.meta && ctx.meta.pointLabel) || LB.label("common", "pointLabel");
}
const CALLOUT_LABEL_W = 1.2; // 수행 Point 라벨 칸 폭 (16:9 기준 인치, 판형 가로 비율로 환산)
const CALLOUT_MG = [0.12, 0.03, 0.08, 0.03]; // 수행 Point 문구 칸 안 여백 (좌, 위, 우, 아래 인치)
const CALLOUT_H = 0.5; // 수행 Point 띠 높이 (인치)
const CALLOUT_W_STEP = 0.1; // 수행 Point 띠 폭을 넓히는 단위 (인치)
/** 수행 Point 문구의 줄 목록 (배열 항목과 줄바꿈을 줄 단위로 나눔) */
function calloutLines(text) {
  return [].concat(text).flatMap((t) => String(t).split("\n")).filter(Boolean);
}
function callout(ctx, slide, box, lbl, text) {
  const lw = CALLOUT_LABEL_W * ctx.S.sx;
  label(ctx, slide, { x: box.x, y: box.y, w: lw, h: box.h }, lbl || pointLabel(ctx, ctx.sb), { sz: T.SIZE.body });
  // 여러 줄이면 불릿을 붙여 항목 구분을 유지 (1줄은 불릿 없이 문장으로 표기)
  const lines = calloutLines(text);
  const paras = lines.map((t) => ({ align: "left", bullet: lines.length > 1, indent: lines.length > 1 ? T.PARA.bulletIndentIn : 0, marL: lines.length > 1 ? T.PARA.bulletIndentIn : 0, runs: [{ t, sz: T.SIZE.body, b: true, color: T.COLOR.textDark }] }));
  slide.addText(A.runsOf(paras), { x: box.x + lw, y: box.y, w: box.w - lw, h: box.h, shape: ctx.pres.ShapeType.rect, fill: { color: T.COLOR.tintBg }, line: { color: T.COLOR.borderLight, width: T.PANEL.LINE_PT }, valign: "middle", margin: A.boxMargin(CALLOUT_MG), isTextBox: true, autoFit: false });
}
/** 수행 Point 띠 폭. 묶음 폭 w0 에서 시작하여 문구가 띠 높이 안에 들어가는 폭까지 넓힘 (상한 maxW)
 *  패널이나 카드 묶음이 짧은 항목에 맞춰 좁아지면 띠 문구가 상자 밖으로 넘치므로 띠와 묶음을 함께 넓히는 데 씀 */
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
/** 주석 문자열 앞에 ※ 를 붙임 (출처, ※, * 로 시작하면 그대로 둠) */
function noteText(v, joiner) {
  const arr = [].concat(v).filter(Boolean).map((x) => String(x).trim());
  if (joiner === "; ") return `※ ${arr.map((x) => x.replace(/^※\s*/, "")).join("; ")}`;
  // 출처와 자료로 시작해도 ※ 를 앞에 붙임 (당구장 기호 누락 방지)
  return arr.map((x) => (/^(※|\*)/.test(x) ? x : `※ ${x}`)).join("\n");
}
function source(ctx, slide, sb) {
  A.footnotes(slide, ctx.S, sb.footnotes);
  if (!sb.source) return;
  const S = ctx.S;
  A.text(slide, { x: S.bodyX, y: S.noteY, w: S.bodyW, h: 0.24 }, noteText(sb.source, "; "), { sz: T.SIZE.note, color: T.COLOR.textMuted, align: "left", valign: "top", mg: [0, 0, 0, 0] });
}
function tag(ctx, slide, box, text) {
  // Sample, Illustrative 태그: 회전 -27도 테두리 상자
  // 표 위에 겹치면 LibreOffice 가 표를 위에 그려 가려지므로 내용 상자 밖(좌상단)에 두고 흰 채움을 준다
  slide.addText(A.runsOf(A.parasFromString(text, { sz: T.SIZE.tableDense, b: true, color: T.COLOR.navyDeep, align: "center" })), { x: box.x, y: box.y, w: 1.1, h: 0.3, rotate: -15, shape: ctx.pres.ShapeType.rect, fill: { color: T.COLOR.white }, line: { color: T.COLOR.navyDeep, width: 1.25 }, valign: "middle", margin: 0, isTextBox: true, autoFit: false });
}

// ---------------------------------------------------------------- 밴드 4종
const COVER_NAME_W = 6.0; // 표지 회사명 글 상자 폭 (16:9 기준 인치). 18pt 굵은 글자로 약 24자 수용

function cover(ctx, slide, sb) {
  const S = ctx.S, s = sb.slots || {};
  const L = S.layout;
  // 가로선은 제목 위와 아래에 각각 1개 (y 2.03 과 3.76)
  const mx = S.marginX; // 가장자리 여백은 판형과 무관하게 고정
  const rule = (y) => slide.addShape(ctx.pres.ShapeType.line, { x: mx, y: y * S.sy, w: L.W - 2 * mx, h: 0, line: { color: T.COLOR.border, width: 0.5 } });
  rule(2.03);
  // 제목은 두 가로선 사이의 정중앙에 배치
  const tH = 1.1 * S.sy, tMid = (2.03 + 3.76) / 2 * S.sy;
  A.text(slide, { x: 0.66 * S.sx, y: +(tMid - tH / 2).toFixed(3), w: L.W - 1.3 * S.sx, h: tH }, s.title || sb.headline || "", { sz: T.SIZE.coverTitle - 4, bold: true, align: "left", valign: "middle", mg: [0, 0, 0, 0] }); // 2줄 제목 수용
  rule(3.76);
  label(ctx, slide, { x: mx, y: 3.96 * S.sy, w: 1.7 * S.sx, h: 0.4 }, LB.label("cover", "label", s.label), { sz: T.SIZE.body });
  A.text(slide, { x: mx, y: 4.5 * S.sy, w: 4 * S.sx, h: 0.4 }, s.date || "", { sz: T.SIZE.coverSub, align: "left", mg: [0, 0, 0, 0] });
  // 발주기관 표기는 날짜 아래 기본, clientPos "top" 이면 제목 위 라인 위쪽에 작게 표기
  if (s.client) {
    if (s.clientPos === "top") A.text(slide, { x: mx, y: 1.6 * S.sy, w: 8 * S.sx, h: 0.36 }, s.client, { sz: T.SIZE.body, color: T.COLOR.textGray, align: "left", mg: [0, 0, 0, 0] });
    else A.text(slide, { x: mx, y: 4.9 * S.sy, w: 8 * S.sx, h: 0.4 }, s.client, { sz: T.SIZE.coverSub, align: "left", mg: [0, 0, 0, 0] });
  }
  const logoBox = { x: L.W / 2 - 1.1 * S.sx, y: 5.6 * S.sy, w: 2.2 * S.sx, h: 0.6 };
  // 로고가 없으면 회사명 글자를 로고 자리보다 넓은 상자에 한 줄로 조판 (로고 자리 폭에서는 긴 회사명이 줄바꿈됨)
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

// ---------------------------------------------------------------- 제안개요
/** 배경(번호 리드 + 근거) 2열 + 목적 상자 + 이슈와 해결방안. slots: {leftHead, leads:[{title, sub:[]}], rightHead, purposeHead, purpose, issueHead, issues:[]} */
function purpose(ctx, slide, sb) {
  const s = sb.slots || {};
  const b = body(ctx, sb);
  const lw = b.w * 0.62, rw = b.w - lw - 0.5 * ctx.S.sx;
  const L = subhead(ctx, slide, { x: b.x, y: b.y, w: lw, h: b.h }, LB.label("purpose", "leftHead", s.leftHead));
  const R = subhead(ctx, slide, { x: b.x + lw + 0.5 * ctx.S.sx, y: b.y, w: rw, h: b.h }, LB.label("purpose", "rightHead", s.rightHead));
  // 배경 리드 묶음은 홈플레이트 배경 위에 둠. 꼭짓점 폭 adj(16372) 는 finalize 가 avLst 로 적용
  slide.addShape(ctx.pres.ShapeType.homePlate, { x: L.x, y: L.y, w: L.w, h: L.h, fill: { color: T.COLOR.white }, line: { color: T.COLOR.borderLight, width: T.PANEL.LINE_PT }, objectName: "adj:16372" });
  const leads = s.leads || [];
  // 리드마다 필요한 높이를 먼저 재고 남는 높이를 비례 배분하여 리드끼리 겹치지 않게 함
  const twAll = L.w - 0.8 - Math.min(L.w, L.h) * 0.16372 - 0.15;
  const need = leads.map((ld) => {
    const th0 = A.estimateLines(ld.title, twAll - 0.1, T.SIZE.panelHead, true) > 1 ? 0.55 : 0.4;
    const subs0 = (ld.sub || []).filter(Boolean);
    const subH = subs0.reduce((a, t) => a + Math.max(1, A.estimateLines(typeof t === "string" ? t : t.text, twAll - T.PARA.bulletIndentIn, T.SIZE.body)) * A.lineHeightIn(T.SIZE.body) + 0.045, 0);
    const noteH0 = 0.2 * [].concat(ld.note || []).filter(Boolean).length;
    return th0 + 0.12 + subH + noteH0 + 0.12;
  });
  const sum = need.reduce((a, b) => a + b, 0) || 1;
  const availL = L.h - 0.22; // 셰브론 위아래 여백 확보 (마지막 불릿이 하단 선에 닿지 않게)
  const scale = availL / sum;
  const heights = need.map((h) => h * Math.min(1.6, Math.max(0.85, scale)));
  const tot = heights.reduce((a, b) => a + b, 0);
  if (tot > availL) heights.forEach((h, i) => { heights[i] = h * (availL / tot); });
  const tw = L.w - 0.8 - Math.min(L.w, L.h) * 0.16372 - 0.15; // 꼭짓점 안쪽까지만
  let acc = L.y + 0.06;
  const geo = leads.map((ld, i) => {
    const rh = heights[i];
    const y = acc;
    acc += rh;
    const th = A.estimateLines(ld.title, tw - 0.1, T.SIZE.panelHead, true) > 1 ? 0.55 : 0.4;
    // 리드의 근거는 불릿, 주석(note)은 ※ 로 시작하는 작은 회색 줄
    const subs = (ld.sub || []).filter((x) => x != null);
    const notes = [].concat(ld.note || []).filter(Boolean);
    const noteH = notes.length ? 0.2 * notes.length : 0;
    return { ld, y, rh, th, subs, notes, noteH, sbox: { x: L.x + 0.8, y: y + th + 0.1, w: tw, h: rh - th - 0.15 - noteH } };
  });
  // 근거 불릿은 같은 계층이므로 리드 칸마다 맞춘 크기 중 가장 작은 값을 모든 리드에 적용
  const subOpt = { valign: "top", noWarn: true, forceBullet: true, gapPt: 3 };
  geo.forEach((g) => { g.fit = g.subs.length ? bulletFitSize(g.sbox, g.subs, subOpt) : null; });
  const fits = geo.filter((g) => g.fit != null).map((g) => g.fit);
  const subSz = fits.length ? Math.min(...fits) : T.SIZE.body;
  // 공통 크기보다 크게 맞춰지는 리드만 공통 크기로 시작 (공통 크기를 정한 리드는 기존 맞춤을 그대로 사용)
  const subOpts = geo.map((g) => (g.fit > subSz ? { ...subOpt, sz: subSz } : subOpt));
  // 근거 불릿의 문단 간격도 리드 사이에 같은 값을 씀
  const subGap = groupGap(geo.map((g) => (g.subs.length ? g.sbox : null)), geo.map((g) => g.subs), subOpts);
  geo.forEach(({ ld, y, rh, th, subs, notes, noteH, sbox }, i) => {
    label(ctx, slide, { x: L.x + 0.33, y: y + 0.15, w: 0.37, h: 0.36 }, String(i + 1), { sz: T.SIZE.body });
    A.text(slide, { x: L.x + 0.8, y: y + 0.1, w: tw, h: th }, ld.title, { sz: T.SIZE.panelHead, bold: true, align: "left", valign: "middle" });
    // 리드 칸을 넘지 않도록 글꼴을 줄여 맞추고 그래도 넘치면 검수에서 잡음
    if (subs.length) bullets(ctx, slide, sbox, subs, { ...subOpts[i], groupGapPt: subGap });
    // 주석은 근거 불릿 상자 바로 아래에 둠 (불릿은 남는 높이를 항목 간격으로 나누어 상자를 채우므로 항목 수 기준 고정 오프셋이면 겹침)
    // 근거 상자는 주석 높이(noteH)를 뺀 높이로 잡았으므로 주석은 리드 칸 안에 들어감
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
const OUT_ROW_MAX = 5; // 산출물 목록 한 줄의 칸 수 상한 (넘으면 두 줄로 나눔)
const OUT_ROW_GAP = 0.1; // 산출물 줄 사이 간격
/** 산출물 칸 배치. outputs 가 모듈 수와 같은 길이이고 원소에 배열이 있으면 모듈 열 아래에 모듈별 여러 항목(불릿)으로 정렬
 *  문자열 목록이면 개수에 따라 배치: 1-2개는 모듈 열 폭 칸을 가운데 정렬, 3-5개는 한 줄, 6개 이상은 줄당 5칸 이하로 두 줄
 *  칸 높이는 가장 긴 칸의 필요 높이로 통일. 반환값의 y 는 산출물 영역 상단 기준 */
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
/** 비전 밴드 + 목표 + 모듈 N열 범위 + 산출물. slots: {vision, goal, modules:[{title, items:[]}], outputs:[문구 | 모듈별 문구 배열]} */
const SCOPE_TAG_W = 0.7; // 구조 라벨(VISION, SCOPE, OUTPUT) 열 폭 (16:9 기준, 판형 비율로 환산)
const SCOPE_TAG_GAP = 0.1; // 구조 라벨 열과 내용 사이 간격
const SCOPE_TAG_MG = 0.03; // 구조 라벨 좌우 여백 (가운데 정렬이라 여백을 줄여도 글자 위치는 같음)
const SCOPE_TAG_KEYS = ["visionTag", "scopeTag", "outputTag"]; // 구조 라벨 슬롯 (기본 VISION, SCOPE, OUTPUT)
function scope(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb), S = ctx.S;
  // 좁은 판형에서도 구조 라벨 단어가 한 줄에 들어가도록 열 폭 하한을 가장 긴 라벨 폭으로 둠
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
  // 모듈 행과 산출물 행은 행마다 문단 간격을 하나로 맞춤
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
/** 질문 배너 + 역량 타일 3열 (열당 항목 1-4). slots: {question, tiles:[{title, items:[]}]} */
function features(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  // 구성: 질문 배너(전폭 둥근 사각형) 아래 역량 열. 열 머리는 네이비 라벨, 항목은 테두리 상자
  const tiles = s.tiles || [];
  const maxItems = Math.max(...tiles.map((tl) => ((tl && tl.items) || []).length), 1);
  const Q_H = 0.5, Q_GAP = 0.3;
  // 항목이 적어도 본문 밴드를 채우도록 상자 높이와 항목 간격에 남는 높이를 차례로 배분
  const BOX_MIN = 0.44, BOX_MAX = 0.95, GAP_MIN = 0.12, GAP_MAX = 0.25, HEAD_GAP = 0.15;
  const avail = b.h - Q_H - Q_GAP - T.PANEL.TITLE_H - HEAD_GAP;
  let ih = BOX_MIN, gap = GAP_MIN;
  let slack = avail - (maxItems * ih + (maxItems - 1) * gap);
  if (slack > 0) { const a = Math.min(BOX_MAX - ih, slack / maxItems); ih += a; slack -= a * maxItems; }
  if (slack > 0 && maxItems > 1) { const a = Math.min(GAP_MAX - gap, slack / (maxItems - 1)); gap += a; slack -= a * (maxItems - 1); }
  if (slack < 0) { ih = Math.max(0.3, (avail - (maxItems - 1) * GAP_MIN) / maxItems); gap = GAP_MIN; slack = 0; }
  // 그래도 남으면 질문 배너를 포함한 묶음 전체를 본문 밴드의 세로 가운데로 모음
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
const STRAT_ROOF_H = 0.6; // 지붕(목표) 높이 (16pt 한 줄과 위아래 여백)
const STRAT_GAP = 0.16; // 지붕, 기둥, 성과 상자, 기단 사이 세로 간격 (모든 층에 같은 값)
const STRAT_RES_H = 0.42; // 기둥 아래 성과 상자 높이
const STRAT_BASE_H = 0.5; // 기단(결론) 높이 (14pt 한 줄과 위아래 여백. composite 결론 밴드와 같은 값)
const STRAT_EAVE = 0.2; // 지붕과 기단이 기둥 묶음 양옆으로 나오는 폭
/** 지붕(목표) + 전략 기둥 N열 + 기단(결론). slots: {goal, strategies:[{title, items:[], result}], conclusion} */
function strategy(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const st = s.strategies || [];
  // 지붕(목표), 같은 폭의 기둥(전략), 기단(결론)이 한 채의 집으로 읽히도록 지붕과 기단은 본문 전폭, 기둥 묶음은 양옆을 STRAT_EAVE 만큼 들임
  // 지붕 문구는 16pt 에서 시작하여 지붕 안쪽(빗변 제외) 폭에 맞지 않으면 14pt 까지 줄임
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
  // 기둥 열은 문단 간격을 하나로 맞춤
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
/** 모듈 셰브론 N열 + Task 상자 세로 연결. slots: {modules:[{id, title, tasks:[]}]} */
function process(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const mods = s.modules || [];
  cols(b, Math.max(mods.length, 1), 0.45 * ctx.S.sx).forEach((c, i) => {
    const m = mods[i]; if (!m) return;
    A.text(slide, { x: c.x, y: c.y, w: c.w, h: 0.3 }, m.id || LB.format(LB.label("process", "idFormat", s.idFormat), { n: i + 1 }), { sz: T.SIZE.body, color: T.COLOR.textGray, align: "center", mg: [0, 0, 0, 0] });
    // 모듈이 많으면 셰브론 폭이 좁아지므로 높이를 키우고 글꼴을 한 단계 낮춤
    const many = mods.length >= 6;
    chevronRow(ctx, slide, { x: c.x, y: c.y + 0.35, w: c.w, h: many ? 0.62 : 0.5 }, [LB.format(LB.label("process", "titleFormat", s.titleFormat), { n: i + 1, t: `${m.title}` })], { allChevron: i > 0, sz: many ? T.SIZE.body : T.SIZE.panelHead });
    const tasks = m.tasks || [];
    const top0Base = mods.length >= 6 ? 1.22 : 1.1;
    // Task 상자를 본문 아래까지 고르게 배분. 마지막 상자 하단을 본문 하단에 맞추되 간격은 균등 배분 간격의 1.5배까지만 늘림
    const top0 = top0Base, availT = c.h - top0;
    const nT = Math.max(tasks.length, 1);
    const th = Math.max(0.36, Math.min(0.5, availT / nT - 0.3));
    const pitch = nT > 1 ? Math.min((availT - th) / (nT - 1), (availT / nT) * 1.5) : 0;
    tasks.forEach((t, j) => {
      const tb = { x: c.x + c.w * 0.1, y: c.y + top0 + j * pitch, w: c.w * 0.8, h: th };
      frame(ctx, slide, tb); A.text(slide, tb, `${i + 1}-${j + 1}. ${t}`, { sz: T.SIZE.body, align: "center" });
      // 앞 상자 아래에서 다음 상자 위까지 붙여 그려 끊긴 느낌이 없게 함
      if (j > 0) {
        const prevBottom = c.y + top0 + (j - 1) * pitch + th;
        slide.addShape(ctx.pres.ShapeType.line, { x: c.x + c.w / 2, y: prevBottom, w: 0, h: tb.y - prevBottom, line: { color: T.COLOR.border, width: 1, endArrowType: "triangle" } });
      }
    });
    // 모듈 사이는 앞 모듈 마지막 Task 에서 다음 모듈 첫 Task 로 이어지는 ㄱ자 연결
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

// ---------------------------------------------------------------- 수행계획 공통
/** 모듈 개요: 단계 셰브론(Task N열) + 행 라벨(추진과정, 활용자료, 산출물). slots: {tasks:[{title, process:[], data:[], output:[]}], rowLabels} */
const MO_LABEL_W = 0.95; // 모듈 개요 행 라벨 열 폭 (16:9 기준, 판형 비율로 환산)
const MO_GRID_GAP = 0.12; // 행 라벨 열과 단계 격자 사이 간격
function module_overview(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb), S = ctx.S;
  const tasks = s.tasks || [];
  // rowLabels 는 [머리행, 내용행 3개] 4개가 기본. 3개만 주면 머리행 라벨을 앞에 채워 행 어긋남을 막음
  const given = (s.rowLabels || []).filter(Boolean);
  const base = LB.label("module_overview", "rowLabels").slice(0, 4);
  const rl = given.length >= 4 ? given.slice(0, 4) : given.length === 3 ? [base[0]].concat(given) : base;
  // 좁은 판형에서도 행 라벨 어절이 한 줄에 들어가도록 라벨 상자 폭(lw + 격자 간격 - 라벨 간격)의 하한을 어절 폭과 여백으로 둠
  const lw = Math.max(MO_LABEL_W * S.sx, A.wordWidthIn(rl, T.SIZE.body, true) + 2 * T.PANEL.LABEL_MG_X + T.PANEL.LABEL_GAP - MO_GRID_GAP);
  const gy = [0, 0.55, 0.55 + (b.h - 0.55) * 0.5, 0.55 + (b.h - 0.55) * 0.78, b.h];
  rl.forEach((r, i) => label(ctx, slide, { x: b.x, y: b.y + gy[i] + (i ? 0.1 : 0), w: lw + MO_GRID_GAP - T.PANEL.LABEL_GAP, h: gy[i + 1] - gy[i] - (i ? 0.1 : 0.05) }, r, { sz: T.SIZE.body }));
  const grid = { x: b.x + lw + MO_GRID_GAP, y: b.y, w: b.w - lw - MO_GRID_GAP, h: b.h };
  const chev = { x: grid.x, y: grid.y, w: grid.w, h: 0.5 };
  chevronRow(ctx, slide, chev, tasks.map((t) => t.title), {});
  const tcols = chevronCols(chev, Math.max(tasks.length, 1), grid.y, grid.h);
  // 같은 행의 상자는 한 글꼴로 통일 (행마다 공통 크기 계산)
  // 문단 간격도 행마다 하나로 맞춤 (공통 크기를 정한 뒤 그 크기로 상자별 간격을 재어 최솟값 사용)
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
/** Task 1개: 좌 조사 설계 표(대상, 출처, 규모, 방법, 산출물) + 우 실측 표본. slots: {leftHead, head:[열 제목 2개], rows:[[항목, 내용]], sample:{head, table|items|image|chart, tag}, point} */
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
/** Task 묶음 2-3개: 열마다 Task 라벨 + 활용자료, 방법, 산출물 불릿. slots: {tasks:[{id, title, items:[]}], rowLabels, freeLabel, point} */
function task_multi(ctx, slide, sb) {
  // Task 2-4건을 열로 두고 항목 라벨을 행으로 맞춘 매트릭스. 항목은 "라벨 : 값" 으로 파싱하여 행을 정렬
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
  const freeLabel = LB.label("task_multi", "freeLabel", s.freeLabel); // "라벨 : 값" 형식이 아닌 항목을 모으는 행의 라벨
  const rows = labels.concat(hasFree ? [freeLabel] : []);
  const cb = { x: b.x, y: b.y, w: b.w, h: b.h - (s.point ? 0.62 : 0) };
  const labW = 1.0 * ctx.S.sx;
  const headH = 0.42;
  const gridX = cb.x + labW + 0.08;
  const gridW = cb.w - labW - 0.08;
  const colW = (gridW - T.PANEL.GAP * (Math.max(tasks.length, 1) - 1)) / Math.max(tasks.length, 1);
  // 열 머리: Task 셰브론
  tasks.forEach((t, i) => {
    const x = gridX + i * (colW + T.PANEL.GAP);
    label(ctx, slide, { x, y: cb.y, w: colW, h: headH }, `${t.id || LB.format(LB.label("task_multi", "idFormat", s.idFormat), { n: i + 1 })}. ${t.title || ""}`, { sz: T.SIZE.body });
  });
  const rowH = Math.max(0.3, (cb.h - headH - 0.1 - T.PANEL.GAP * (rows.length - 1)) / Math.max(rows.length, 1));
  rows.forEach((rl, r) => {
    const y = cb.y + headH + 0.1 + r * (rowH + T.PANEL.GAP);
    label(ctx, slide, { x: cb.x, y, w: labW + 0.08 - T.PANEL.LABEL_GAP, h: rowH }, rl, { sz: T.SIZE.tableDense, fill: T.COLOR.navyDeep });
    const valsOf = (i) => (rl === freeLabel ? (maps[i].__free || []) : (maps[i][rl] || []));
    // 같은 행의 불릿 칸(값 2개 이상)은 문단 간격을 하나로 맞춤
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

const PANEL_ITEM_SZ = 14; // 패널 템플릿 항목 글자 시작 크기 (패널 제목과 같은 크기, 굵기로 위계 구분)
/** 패널 1-4열. slots: {panels:[{head, items|text}], point} */
function bulletsT(ctx, slide, sb) {
  const b = body(ctx, sb), pn = sb.panels || (sb.slots && sb.slots.panels) || [];
  const point = sb.point || (sb.slots && sb.slots.point);
  const ptH = point ? 0.7 : 0;
  const n = Math.max(pn.length, 1), gap = T.PANEL.GAP;
  const lists = pn.map((p) => (p && (p.items || p.text)) || []);
  // 나란한 패널은 같은 글꼴을 쓰도록 공통 크기를 계산해 전달 (항목 14pt 에서 시작하여 높이가 모자라면 11pt 까지 축소)
  const full = cols({ x: b.x, y: b.y, w: b.w, h: b.h - ptH }, n);
  const psz = groupSize(full.map((c) => ({ ...c, h: c.h - T.PANEL.TITLE_H })), pn.map((p) => (p && p.items) || []), PANEL_ITEM_SZ);
  const ssz = Math.max(T.SIZE.BODY_MIN, psz - 2);
  // 패널 폭은 가장 긴 글줄에 맞춘 같은 폭으로 두고 패널 묶음과 수행 Point 를 가운데 정렬 (짧은 항목에서 오른쪽이 비지 않게 함)
  const pw0 = Math.min(full[0].w, Math.max(...lists.map((l) => itemsNeedW(l, psz, ssz))) + 2 * T.PANEL.INSET + FIT_W_SLACK);
  // 수행 Point 문구가 띠 높이에 들지 않으면 패널 묶음과 띠를 함께 넓힘 (띠는 패널 묶음과 같은 폭)
  const gw0 = pw0 * n + gap * (n - 1);
  const gw = point ? calloutW(ctx, point, gw0, b.w) : gw0;
  const pw = gw === gw0 ? pw0 : Math.min(full[0].w, (gw - gap * (n - 1)) / n), x0 = b.x + (b.w - gw) / 2;
  // 패널 높이는 내용 높이 기준으로 두고 패널과 수행 Point 묶음을 본문 세로 가운데에 둠
  const gh = T.PANEL.TITLE_H + panelBodyH(pn.map(() => pw), lists, psz, b.h - ptH - T.PANEL.TITLE_H, ssz);
  const top = b.y + (b.h - gh - ptH) / 2;
  const pboxes = cols({ x: x0, y: top, w: gw, h: gh }, n, gap);
  const pps = pboxes.map((c, i) => (pn[i] ? { ...pn[i], sz: psz, subSz: ssz } : null));
  const pgap = panelsGap(pboxes, pps); // 나란한 패널은 문단 간격도 하나로 맞춤
  pboxes.forEach((c, i) => { if (pps[i]) panel(ctx, slide, c, { ...pps[i], groupGapPt: pgap }); });
  if (point) callout(ctx, slide, { x: x0, y: top + gh + 0.2, w: gw, h: 0.5 }, pointLabel(ctx, sb), point);
  source(ctx, slide, sb);
}
/** 문구 목록이 폭 w 상자에서 차지하는 높이 (불릿 들여쓰기, 하위 항목, 문단 간격, 상자 안 여백 포함) */
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
/** 문구 목록의 가장 긴 글줄 폭 (불릿 들여쓰기 포함, 상자 안 여백 제외). 하위 항목은 한 단계 더 들여씀 */
function itemsNeedW(items, sz, subSz) {
  const list = (Array.isArray(items) ? items : [items]).filter((x) => x != null && x !== "");
  const ind = T.PARA.bulletIndentIn;
  return Math.max(0, ...list.map((t) => {
    const lead = list.length > 1 || subsOf(t).length ? ind : 0;
    return Math.max(A.lineWidthIn(typeof t === "string" ? t : t.text, sz) + lead, ...subsOf(t).map((u) => A.lineWidthIn(u, subSz || sz) + 2 * ind));
  }));
}
/** 나란한 패널의 몸체 높이 (가용 높이 상한)
 *  항목이 여럿이면 항목 간격을 paraGapMaxPt 까지 넓힌 높이, 한 항목이면 내용 필요 높이의 FILL_EXPAND 배
 *  항목이 적은 패널이 본문 높이까지 늘어나 비어 보이지 않게 하고 남는 높이는 묶음 바깥 여백으로 돌림 */
function panelBodyH(widths, lists, sz, avail, subSz) {
  const cap = (l, i) => {
    const list = (Array.isArray(l) ? l : [l]).filter((x) => x != null && x !== "");
    const need = Math.max(0.5, itemsNeedH(list, widths[i], sz, subSz));
    return list.length > 1 ? need + (list.length + 1) * ((T.PARA.paraGapMaxPt - T.PARA.paraGapPt) / 72) : need * T.PANEL.FILL_EXPAND;
  };
  return Math.min(avail, Math.max(0.5, ...lists.map(cap)));
}
/** 전폭 표. slots: {title, head, rows, colW, align, point} */
function table(ctx, slide, sb) {
  const s = sb.slots || sb, b = body(ctx, sb);
  const titleH = s.title ? T.PANEL.SUBHEAD_H : 0, legH = s.legend ? 0.3 : 0, ptH = s.point ? 0.7 : 0;
  // 행 높이 상한에 걸려 표가 본문보다 짧으면 제목, 표, 수행 Point 묶음을 본문 세로 가운데에 둠 (각주 높이는 body() 가 이미 제외)
  const availT = b.h - titleH - legH - ptH;
  const shift = Math.max(0, (availT - tableLayout(s, b.w, availT).total) / 2);
  const g = { x: b.x, y: b.y + shift, w: b.w, h: b.h - 2 * shift };
  let box = s.title ? subhead(ctx, slide, g, s.title) : g;
  // 범례는 표 위 우측에 한 줄로 배치 (하베이 볼 등)
  if (s.legend) {
    A.text(slide, { x: box.x, y: box.y, w: box.w, h: 0.26 }, s.legend, { sz: T.SIZE.tableDense, color: T.COLOR.textGray, align: "right", mg: [0, 0, 0, 0] });
    box = { ...box, y: box.y + 0.3, h: box.h - 0.3 };
  }
  const used = tableBlock(ctx, slide, { ...box, h: box.h - ptH }, s);
  if (s.point) callout(ctx, slide, { x: b.x, y: box.y + used + 0.2, w: b.w, h: 0.5 }, pointLabel(ctx, sb), s.point);
  if (s.rows && s.rows.length > T.LIMIT.tableRowsPerSlide) ctx.warn(`표 ${s.rows.length}행: 상한 ${T.LIMIT.tableRowsPerSlide} 초과, 분할 필요`);
  source(ctx, slide, sb);
  return used;
}
/** 차트 1개 + 우측 시사점. slots: {chartTitle, chart, findings:[{head, items}]} */
function chart_text(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const lw = b.w * 0.55;
  const L = subhead(ctx, slide, { x: b.x, y: b.y, w: lw, h: b.h }, s.chartTitle || "");
  A.chart(ctx.pres, slide, { x: L.x, y: L.y, w: L.w, h: Math.max(T.PANEL.CHART_MIN_H, L.h - 0.1) }, s.chart || { type: "bar", barDir: "bar", categories: [], series: [] });
  const R = { x: b.x + lw + 0.3, y: b.y, w: b.w - lw - 0.3, h: b.h };
  const f = s.findings || [];
  // 발견 패널은 내용 높이 기준으로 두고 패널 묶음을 차트 높이의 세로 가운데에 둠
  const nf = Math.max(f.length, 1);
  const fAvail = (R.h - T.PANEL.GAP * (nf - 1)) / nf - T.PANEL.TITLE_H;
  const fh = T.PANEL.TITLE_H + panelBodyH(f.map(() => R.w), f.map((x) => (x && x.items) || []), T.SIZE.body, fAvail);
  const fH = fh * nf + T.PANEL.GAP * (nf - 1);
  const fboxes = rows({ ...R, y: R.y + (R.h - fH) / 2, h: fH }, nf);
  const fps = fboxes.map((r, i) => (f[i] ? { head: f[i].head, items: f[i].items, noWarn: true } : null));
  const fgap = panelsGap(fboxes, fps); // 발견 패널은 문단 간격도 하나로 맞춤
  fboxes.forEach((r, i) => { if (fps[i]) panel(ctx, slide, r, { ...fps[i], groupGapPt: fgap }); });
  source(ctx, slide, sb);
}
/** 차트 2개 나란히 + 각 발견. slots: {left:{title, chart, items}, right:{...}} */
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
/** AS-IS / TO-BE 대비 + 갭. slots: {asis:{head, items}, tobe:{head, items}, gap:[]} */
// 행 대응 비교: 현행 항목, 격차, 개선 항목이 1:1 로 짝지어지면 행마다 현행 상자, 격차 화살표, 개선 상자를 배치
const CMP_SIZES = [[14, 12, 13], [13, 12, 12], [12, 11, 12]]; // [항목, 근거, 격차] 글자 크기. 본문 높이를 넘으면 다음 단계로 축소
const CMP_COL_GAP = 0.16; // 상자와 격차 화살표 사이 간격
const CMP_ROW_GAP = 0.14; // 행 간격
const CMP_HEAD_GAP = 0.1; // 열 제목과 첫 행 사이 간격
const CMP_ROW_PAD = 0.16; // 행 상자 글 위아래 여유 합
const CMP_PAD_X = 0.14; // 행 상자 글 좌우 여백
const CMP_ARROW_W = [1.5, 2.6]; // 격차 화살표 폭 하한과 상한 (상한을 넘는 문구는 두 줄로 줄바꿈)
const CMP_ARROW_H_RATIO = 0.62; // 행 높이 대비 격차 화살표 높이
const CMP_ARROW_ADJ = 30000; // 화살표 뾰족한 끝 비율 (도형 높이의 30%)
const pairLead = (it) => (typeof it === "string" ? it : it.text);
/** 비교 상자 문단. 항목은 굵은 제목, 근거는 줄표 불릿 (근거가 1개면 불릿 없이 제목 아래 한 줄) */
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
    const ah0 = A.lineHeightIn(gSz) + 2 * ins; // 한 줄 격차 문구의 화살표 높이 (끝 폭 추정용)
    const tip = ah0 * (CMP_ARROW_ADJ / 100000);
    const gw = Math.min(CMP_ARROW_W[1], Math.max(CMP_ARROW_W[0], ...G.map((g) => A.lineWidthIn(g, gSz, true) + 2 * ins + tip + FIT_W_SLACK)));
    // 현행과 개선 상자는 같은 폭. 가장 긴 글줄에 맞추고 본문 폭을 넘으면 본문 폭 안으로 줄임
    const w = Math.min((b.w - gw - 2 * CMP_COL_GAP) / 2, Math.max(...[...pl, ...pr].map(parasNeedW)) + 2 * CMP_PAD_X + FIT_W_SLACK);
    const gh = Math.max(...G.map((g) => A.estimateLines(g, gw - 2 * ins - tip, gSz, true))) * A.lineHeightIn(gSz) + 2 * ins;
    const rowH = Math.max(gh / CMP_ARROW_H_RATIO, Math.max(...[...pl, ...pr].map((ps) => parasNeedH(ps, w - 2 * CMP_PAD_X))) + 2 * ins + CMP_ROW_PAD);
    const total = T.PANEL.TITLE_H + CMP_HEAD_GAP + n * rowH + (n - 1) * CMP_ROW_GAP;
    lay = { gSz, pl, pr, gw, w, rowH, total, tip };
    if (total <= b.h) break;
  }
  if (lay.total > b.h) ctx.warn(`compare 행 높이 합 ${lay.total.toFixed(2)} > 본문 ${b.h.toFixed(2)}in (항목이나 근거 축약)`);
  const gwTot = 2 * lay.w + lay.gw + 2 * CMP_COL_GAP;
  const x0 = b.x + (b.w - gwTot) / 2, y0 = b.y + Math.max(0, (b.h - lay.total) / 2);
  const xs = [x0, x0 + lay.w + CMP_COL_GAP, x0 + lay.w + lay.gw + 2 * CMP_COL_GAP];
  const ws = [lay.w, lay.gw, lay.w];
  // 열 제목은 현행 회색, 격차 연한 네이비, 개선 네이비로 두어 왼쪽에서 오른쪽으로 진해지게 함
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
  // 패널 높이는 내용 높이 기준으로 두고 대비 패널과 GAP 띠 묶음을 본문 세로 가운데에 둠
  const ph = T.PANEL.TITLE_H + panelBodyH([pw, pw], [(s.asis && s.asis.items) || [], (s.tobe && s.tobe.items) || []], T.SIZE.body, b.h - gh - T.PANEL.TITLE_H);
  const top = b.y + (b.h - ph - gh) / 2;
  const cb = { x: b.x, y: top, w: b.w, h: ph };
  const [L, R] = cols(cb, 2, 0.8);
  const lp = { head: LB.label("compare", "asis.head", s.asis && s.asis.head), items: s.asis && s.asis.items, headFill: T.COLOR.textMuted, noWarn: true };
  const rp = { head: LB.label("compare", "tobe.head", s.tobe && s.tobe.head), items: s.tobe && s.tobe.items, noWarn: true };
  const pgap = panelsGap([L, R], [lp, rp]); // 대비 패널은 문단 간격을 하나로 맞춤
  panel(ctx, slide, L, { ...lp, groupGapPt: pgap });
  panel(ctx, slide, R, { ...rp, groupGapPt: pgap });
  slide.addShape(ctx.pres.ShapeType.rightArrow, { x: L.x + L.w + 0.15, y: cb.y + cb.h / 2 - 0.25, w: 0.5, h: 0.5, fill: { color: T.COLOR.navy }, line: { color: "FFFFFF", width: 0, transparency: 100 } });
  if (s.gap) { const gy = top + ph + 0.2; label(ctx, slide, { x: b.x, y: gy, w: 1.2 * ctx.S.sx, h: 0.8 }, LB.label("compare", "gapHead", s.gapHead), { sz: T.SIZE.body }); const gb = { x: b.x + 1.2 * ctx.S.sx, y: gy, w: b.w - 1.2 * ctx.S.sx, h: 0.8 }; frame(ctx, slide, gb, { fill: T.COLOR.tintBg }); bullets(ctx, slide, gb, s.gap, { noWarn: true }); }
  source(ctx, slide, sb);
}
/** 로드맵: 전략 행 × 연차 열. slots: {periods:[], lanes:[{title, tasks:[{text, from, to}]}], note} */
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
    // 막대 묶음이 레인 구분선을 넘지 않도록 간격을 포함해 높이를 계산
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
/** 간트: 구분, 과업 열 + 월별 주 격자. slots: {months:N, weeks:4, groups:[{name, tasks:[{name, from, to}]}], reports:[{name, at}], groupHead, taskHead, reportHead} */
function gantt(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const months = s.months || 4, weeks = s.weeks || 4;
  const groups = s.groups || [];
  // 과업 열 머리와 보고 행 묶음 이름 (기본값은 제안 용어. 일반 기획은 슬롯으로 바꿈)
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
  // 좁은 판형에서 구분 열과 과업 열의 어절이 중간에서 끊기지 않도록 두 열 폭 하한을 가장 긴 어절 폭으로 두고 부족분은 주 열에서 균등하게 덜어냄
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
  // 행 높이 상한에 걸려 본문 높이가 남으면 표를 본문 세로 가운데에 둠
  A.table(slide, { x: b.x, y: b.y + Math.max(0, (b.h - rh * nrow) / 2), w: b.w, h: rh * nrow, table: { colw, rowh: Array(nrow).fill(rh), rows: [head1.map((c) => mk(c, true)), head2.map((c) => mk(c, true)), ...rowsOut.map((r) => r.map((c) => mk(c, false)))] } }, { sz: T.SIZE.tableDense });
  source(ctx, slide, sb);
}
/** 수행 조직도: 발주기관, PM, 품질관리, 자문, 모듈 팀. slots: {client, pm, qa, advisory, teams:[{name, members:[], share}], note} */
/** 수행조직도. 발주기관 → 총괄책임자(PM) → 품질관리자(PL) → 모듈 팀의 수직 계선.
 * 자문위원회(총괄위원회)는 총괄책임자 우측에 수평 연결. slots: {client, pm, pmTitle, qa, qaTitle, advisory, advisoryTitle, advisoryNote, teams[{name, members[], share}], note} */
function org(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb), S = ctx.S;
  const many = (s.teams || []).length > 6; // 모듈이 많으면 상단 계선을 압축하여 하단 공간 확보
  const cx = b.x + b.w / 2, bw = 2.78 * S.sx, h1 = many ? 0.36 : 0.44, h2 = many ? 0.5 : 0.64, vgap = many ? 0.22 : 0.33;
  const line = (x, y, w, h, dash) => slide.addShape(ctx.pres.ShapeType.line, { x, y, w, h, line: { color: T.COLOR.border, width: 1, dashType: dash ? "dash" : undefined } });
  const box = (x, y, w, h, tx, fill) => {
    const o = { x, y, w, h };
    if (fill === "navy") label(ctx, slide, o, tx, { sz: T.SIZE.body });
    else { frame(ctx, slide, o, { fill: fill === "tint" ? T.COLOR.tintHead : undefined }); A.text(slide, o, tx, { sz: T.SIZE.body, align: "center" }); }
  };
  // 1단 발주기관
  let y = b.y;
  box(cx - bw / 2, y, bw, h1, LB.label("org", "client", s.client), "navy");
  if (s.clientNote) { // 발주기관 역할 설명은 상자 우측에 붙여 불릿 목록으로 배치. 자문위원회 상자와 겹치지 않도록 폭과 높이를 제한
    const items = Array.isArray(s.clientNote) ? s.clientNote : String(s.clientNote).split("\n").filter(Boolean);
    const nx = cx + bw / 2 + 0.04;
    const advY = y + h1 + vgap; // 자문위원회 상자 상단
    const nw = Math.min(2.1 * S.sx, b.x + b.w - nx);
    const nh = Math.min(0.26 * items.length, Math.max(0.3, advY - (y - 0.13) - 0.06)); // 자문위원회 상자와 겹치지 않는 높이
    bullets(ctx, slide, { x: nx, y: y - 0.13, w: nw, h: nh }, items, { noWarn: true, valign: "top", sz: T.SIZE.body });
  }
  line(cx, y + h1, 0, vgap);
  // 2단 총괄책임자와 우측 자문위원회
  y += h1 + vgap;
  box(cx - bw / 2, y, bw, h2, `${LB.label("org", "pmTitle", s.pmTitle)}\n${s.pm || "[인력A]"}`, "navy");
  if (s.advisory) {
    line(cx + bw / 2, y + h2 / 2, 1.0 * S.sx, 0);
    box(cx + bw / 2 + 1.0 * S.sx, y, bw, h2, `${LB.label("org", "advisoryTitle", s.advisoryTitle)}\n${s.advisory}`);
    if (s.advisoryNote) { // 자문위원회 역할 설명은 상자 우측에 붙여 배치
      const items = Array.isArray(s.advisoryNote) ? s.advisoryNote : String(s.advisoryNote).split("\n").filter(Boolean);
      bullets(ctx, slide, { x: cx + bw / 2 + 1.0 * S.sx, y: y + h2 + 0.04, w: bw, h: 0.26 * items.length }, items, { noWarn: true, valign: "top", fixedSize: true, sz: T.SIZE.body });
    }
  }
  line(cx, y + h2, 0, vgap);
  // 3단 품질관리자 (총괄책임자와 모듈 팀 사이의 수직 계선)
  y += h2 + vgap;
  if (s.qa) { box(cx - bw / 2, y, bw, h2, `${LB.label("org", "qaTitle", s.qaTitle)}\n${s.qa}`, "tint"); line(cx, y + h2, 0, vgap + 0.03); y += h2 + vgap + 0.03; }
  // 4단 모듈 팀 (4-6개는 1행, 7개 이상은 2행)
  const teams = s.teams || [];
  const n = Math.max(teams.length, 1);
  const rowN = n > 6 ? 2 : 1;
  const perRow = Math.ceil(n / rowN);
  const gap = perRow >= 5 ? 0.12 : perRow >= 4 ? 0.18 : 0.22;
  const areaH = b.y + b.h - y - 0.22 - (s.note ? 0.32 : 0);
  const rowGap = rowN > 1 ? 0.45 : 0.25; // 2행 배치는 행 사이에 계선이 보이도록 간격 확보
  const rowH = (areaH - (rowN - 1) * rowGap) / rowN;
  const tc = [];
  for (let r = 0; r < rowN; r++) cols({ x: b.x, y: y + 0.22 + r * (rowH + rowGap), w: b.w, h: rowH }, perRow, gap).forEach((c) => tc.push(c));
  // 행마다 수평 연결선과 상자로 내려가는 수직선. 2행이면 중앙 척추선을 아랫행까지 연장
  let prevRy = y;
  for (let r = 0; r < rowN; r++) {
    const rowBoxes = tc.slice(r * perRow, (r + 1) * perRow).filter((c, i) => teams[r * perRow + i]);
    if (!rowBoxes.length) continue;
    const ry = rowBoxes[0].y - 0.22;
    if (r > 0) line(cx, prevRy, 0, ry - prevRy); // 윗행 수평선에서 아랫행 수평선까지 중앙 척추선을 끊김 없이 연결
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
    // 인력은 불릿 없이 가운데 정렬. 상자가 낮으면 한 줄로 이어 붙임
    const mem = t.members || [];
    const small = bd.h < 0.7;
    const sz = perRow >= 5 || small ? T.SIZE.tableDense : T.SIZE.body;
    if (small) A.text(slide, bd, mem.join(", "), { sz, align: "center", valign: "middle" });
    else {
      // 인력 줄 사이에 남는 높이를 나눠 간격을 두되 상한을 두어 과도한 벌어짐을 방지
      const need = mem.length * A.lineHeightIn(sz);
      const extra = Math.max(0, Math.min(T.PARA.paraGapMaxPt, ((bd.h - 0.16 - need) * 72) / Math.max(mem.length, 1)));
      const paras = mem.map((m, k) => ({ align: "center", spcBef: k ? extra : 0, runs: [{ t: m, sz, color: T.COLOR.textDark }] }));
      slide.addText(A.runsOf(paras), { x: bd.x, y: bd.y, w: bd.w, h: bd.h, isTextBox: true, valign: "middle", margin: A.boxMargin([0.06, 0.04, 0.06, 0.04]), autoFit: false });
    }
    // 분담 문구는 본문 정보이므로 본문 하한(11pt)으로 조판 (10pt 는 check_layout 이 주석 크기로 판정)
    if (t.share) A.text(slide, { x: c.x, y: bd.y + bd.h, w: c.w, h: 0.28 }, t.share, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textMuted, align: "center" });
  });
  if (s.note) A.text(slide, { x: b.x, y: b.y + b.h - 0.28, w: b.w, h: 0.28 }, noteText(s.note), { sz: T.SIZE.note, color: T.COLOR.textMuted, align: "left" });
  source(ctx, slide, sb);
}

/** 인력 카드 2-4열: 역할, 이름 슬롯, 경력, 실적 3건. slots: {people:[{role, name, career:[], records:[], photo}], recordsHead} */
function staff_card(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const people = s.people || [];
  // 5명 이상이면 사진을 생략하고 텍스트 폭을 확보 (조직도의 모듈 수 증가에 대응)
  const dense = people.length >= 4;
  const pcols = cols(b, Math.max(people.length, 1), dense ? 0.12 : T.PANEL.GAP);
  const pxOf = (p) => (dense && !p.photo ? 0 : 1.0); // 사진 열 폭
  const careerBox = (c, p) => ({ x: c.x + 0.1 + pxOf(p), y: c.y + T.PANEL.TITLE_H + 0.5, w: c.w - 0.2 - pxOf(p), h: 0.75 });
  const recordBox = (c) => ({ x: c.x + 0.12, y: c.y + T.PANEL.TITLE_H + 1.68, w: c.w - 0.24, h: c.h - T.PANEL.TITLE_H - 1.8 });
  const copt = { noWarn: true, valign: "top" }, ropt = { noWarn: true, valign: "top", sz: dense ? T.SIZE.tableDense : T.SIZE.body };
  // 경력 칸끼리, 실적 칸끼리 문단 간격을 하나로 맞춤
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
/** SWOT: 내부와 외부 요인 + 매트릭스 + 전략 방향. slots: {S:[], W:[], O:[], T:[], so, st, wo, wt, labels:{S, W, O, T}} */
const SWOT_GAP = 0.5; // 요인 열과 전략 칸 사이 간격 (요인에서 전략 칸으로 모이는 화살표 자리)
const SWOT_ARROW = { w: 0.3, h: 0.34 }; // 요인 칸에서 전략 칸으로 향하는 화살표 크기
const SWOT_SIDE_SHARE = 0.27; // 요인 열 1개의 폭 비율 (전략 칸 폭 0.46)
function swot(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  // 전략 칸(가운데)은 두 칸이 나란히 들어가므로 좌우 요인 열보다 넓게 둠
  const sideW = (b.w - 2 * SWOT_GAP) * SWOT_SIDE_SHARE, midW = b.w - 2 * SWOT_GAP - 2 * sideW;
  const L = { x: b.x, y: b.y, w: sideW, h: b.h }, M = { x: b.x + sideW + SWOT_GAP, y: b.y, w: midW, h: b.h }, R = { x: M.x + midW + SWOT_GAP, y: b.y, w: sideW, h: b.h };
  const lb = LB.labels("swot", "labels", s.labels); // 요인 칸 제목 (labels 로 바꿈)
  // 네 요인 칸은 문단 간격을 하나로 맞춤 (그리는 순서는 S, W, O, T)
  const fboxes = rows(L, 2).concat(rows(R, 2));
  const fps = [{ head: lb.S, items: s.S, noWarn: true }, { head: lb.W, items: s.W, noWarn: true }, { head: lb.O, items: s.O, noWarn: true }, { head: lb.T, items: s.T, noWarn: true }];
  const fgap = panelsGap(fboxes, fps);
  fboxes.forEach((r, i) => panel(ctx, slide, r, { ...fps[i], groupGapPt: fgap }));
  // 네 요인 칸에서 가운데 전략 칸으로 모이는 화살표 (왼쪽 열은 오른쪽으로, 오른쪽 열은 왼쪽으로)
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
  const qgap = groupGap(qboxes.map(qbody), q.map(([, v]) => v || []), qopt); // 네 전략 칸은 문단 간격을 하나로 맞춤
  q.forEach(([k, v], i) => {
    const bx = qboxes[i];
    frame(ctx, slide, bx);
    A.text(slide, { x: bx.x, y: bx.y, w: bx.w, h: 0.3 }, k, { sz: T.SIZE.body, bold: true, color: T.COLOR.navy, align: "center" });
    bullets(ctx, slide, qbody(bx), v || [], { ...qopt, groupGapPt: qgap });
  });
  source(ctx, slide, sb);
}
/** 카드 N열 (제목 + 본문). slots: {cards:[{title, items|text}], point} */
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
  // 카드 폭은 가장 긴 글줄에 맞춘 같은 폭으로 두고 카드 묶음과 수행 Point 를 가운데 정렬 (짧은 항목에서 오른쪽이 비지 않게 함)
  const cw0 = Math.min(full[0].w, Math.max(...lists.map((l) => itemsNeedW(l, csz, ssz))) + 2 * T.PANEL.INSET + FIT_W_SLACK);
  // 수행 Point 문구가 띠 높이에 들지 않으면 카드 묶음과 띠를 함께 넓힘 (띠는 카드 묶음과 같은 폭)
  const gw0 = cw0 * ncol + T.PANEL.GAP * (ncol - 1);
  const gw = s.point ? calloutW(ctx, s.point, gw0, b.w) : gw0;
  const cw = gw === gw0 ? cw0 : Math.min(full[0].w, (gw - T.PANEL.GAP * (ncol - 1)) / ncol), x0 = b.x + (b.w - gw) / 2;
  // 카드 높이는 내용 높이 기준으로 두고 카드와 수행 Point 묶음을 본문 세로 가운데에 둠
  const rowAvail = full[0].h - T.PANEL.TITLE_H;
  const ch = T.PANEL.TITLE_H + panelBodyH(cd.map(() => cw), lists, csz, rowAvail, ssz);
  const gridH = ch * nrow + T.PANEL.GAP * (nrow - 1);
  const top = b.y + (b.h - gridH - ptH) / 2;
  const cboxes = rows({ x: x0, y: top, w: gw, h: gridH }, nrow).flatMap((r) => cols(r, ncol));
  const cps = cboxes.map((c, k) => (cd[k] ? { head: cd[k].title, items: cd[k].items, text: cd[k].text, noWarn: true, sz: csz, subSz: ssz } : null));
  const cgap = panelsGap(cboxes, cps); // 카드는 문단 간격도 하나로 맞춤
  cboxes.forEach((c, k) => { if (cps[k]) panel(ctx, slide, c, { ...cps[k], groupGapPt: cgap }); });
  if (s.point) callout(ctx, slide, { x: x0, y: top + gridH + 0.2, w: gw, h: 0.5 }, pointLabel(ctx, sb), s.point);
  source(ctx, slide, sb);
}
/** 방법론 단계 셰브론 4-5단 + 단계별 설명. slots: {steps:[{title, items:[]}], point} */
function steps(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const st = s.steps || [];
  // 상자 높이는 항목 수에 맞추고 남는 높이는 비워 빈 상자가 길게 늘어지지 않게 함
  const maxItems = Math.max(...st.map((x) => (x.items || []).length), 1);
  const availH = b.h - 0.7 - (s.point ? 0.7 : 0);
  const need = 0.36 * maxItems + 0.34;
  // 항목이 적으면 상자를 항목 높이의 1.3배까지만 두고 묶음 전체를 본문 가운데로 모아 상하 여백을 균등 분배
  const bodyH = Math.min(availH, need * 1.3);
  const groupH = 0.7 + bodyH + (s.point ? 0.75 : 0);
  // body() 가 출처 행과 각주 높이를 이미 제외하므로 본문 높이 안에서 가운데 정렬
  const shift = Math.max(0, (b.h - groupH) / 2);
  // 셰브론 접두는 stepLabel 로 조정하며 빈 문자열이면 제목만 표기
  const lab = LB.labelKeep("steps", "stepLabel", s.stepLabel);
  const chev = { x: b.x, y: b.y + shift, w: b.w, h: 0.55 };
  chevronRow(ctx, slide, chev, st.map((x, i) => (lab ? `${lab} ${i + 1}. ${x.title}` : x.title)));
  const scols = chevronCols(chev, Math.max(st.length, 1), b.y + 0.7 + shift, bodyH);
  const sopts = scols.map((c, i) => ({ noWarn: true, valign: "middle", gapPt: Math.min(14, Math.max(8, (c.h - 0.3) / Math.max(((st[i] && st[i].items) || []).length, 1) * 24)) }));
  // 단계 상자는 문단 간격을 하나로 맞춤 (상자별 기본 간격과 남는 높이 분배를 합한 값의 최솟값)
  const sgap = groupGap(scols.map((c, i) => (st[i] ? c : null)), st.map((x) => (x && x.items) || []), sopts);
  scols.forEach((c, i) => { if (st[i]) { frame(ctx, slide, c); bullets(ctx, slide, c, st[i].items || [], { ...sopts[i], groupGapPt: sgap }); } });
  if (s.point) callout(ctx, slide, { x: b.x, y: Math.min(b.y + 0.7 + shift + bodyH + 0.25, b.y + b.h - 0.5), w: b.w, h: 0.5 }, pointLabel(ctx, sb), s.point); // 상자 바로 아래
  source(ctx, slide, sb);
}

/** 회사 조직도. slots: {ceo, advisory{name,note}, staff{name,note}, units[{name,teams[]}], people[{label,count,ratio}], peopleHead[], network[], leftHead, rightHead, netHead} */
function orgchart(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb), P = ctx.pres;
  const allUnits = s.units || [];
  const units = allUnits.slice(0, 8);
  if (allUnits.length > units.length) ctx.warn(`본부 ${allUnits.length}개: 상한 8개를 넘는 ${allUnits.length - units.length}개 미표시`);
  const people = (s.people || []).slice(0, 8);
  const net = (s.network || []).slice(0, 6);
  const netH = net.length ? 0.68 : 0;
  // 본부가 7개 이상이면 조직도 폭을 넓혀 팀 이름이 한 줄로 들어가게 함
  const leftW = people.length ? b.w * (units.length >= 7 ? 0.76 : 0.62) : b.w;
  const L = subhead(ctx, slide, { x: b.x, y: b.y, w: leftW, h: b.h - netH }, LB.label("orgchart", "leftHead", s.leftHead));
  const line = (x, y, w, h) => slide.addShape(P.ShapeType.line, { x, y, w, h, line: { color: T.COLOR.border, width: 1 } });
  const ceoW = Math.min(2.4, L.w * 0.26);
  const sideW = Math.min(2.2, L.w * 0.26);
  const cx = L.x + L.w / 2;
  const CEO_H = 0.42;
  // 본부 상자는 본부 수로 높이를 정하고 행 전체에 같은 값을 적용
  const many = units.length >= 5;
  const unitH = many ? 0.5 : 0.36;
  const unitSz = many ? T.SIZE.tableDense : T.SIZE.body;
  // 부서 설명은 조판하지 않고 부서 이름과 팀 이름만 표기 (설명과 이름이 섞이는 것을 방지)
  const teamsOf = (u) => ((u && u.teams) || []).filter(Boolean);
  const maxTeams = Math.max(...units.map((u) => teamsOf(u).length), 0);
  const DROP_MIN = 0.4, DROP_MAX = 1.0;
  // 본부가 많으면 열 간격을 좁혀 팀 이름이 들어갈 폭을 확보
  const colGap = units.length >= 7 ? 0.07 : 0.1;
  const colW = (L.w - colGap * (Math.max(units.length, 1) - 1)) / Math.max(units.length, 1);
  const teamInnerW = Math.max(0.3, colW - 0.1 - 0.18);
  // 팀 이름의 실제 줄 수를 재어 상자 높이를 정함 (긴 이름이 한 줄 상자에서 넘치는 것을 방지)
  const teamLines = Math.max(1, ...units.flatMap((u) => teamsOf(u).map((x) => A.estimateLines(x, teamInnerW, T.SIZE.tableDense, true))));
  const TEAM_MIN = Math.max(0.28, teamLines * A.lineHeightIn(T.SIZE.tableDense) + 0.12);
  const TEAM_MAX = Math.max(TEAM_MIN + 0.04, 0.38);
  const GAP_MIN = 0.03, GAP_MAX = 0.14;
  const UNIT_PAD = 0.08;
  const need = (n, th, gap, drop) => drop + unitH + (n ? UNIT_PAD + n * th + (n - 1) * gap : 0);
  const avail = L.h - CEO_H;
  // 팀은 전건을 개별 상자로 조판하며 자리가 모자라면 축약 대신 경고로 알림
  const showTeams = maxTeams;
  const minNeed = need(showTeams, TEAM_MIN, GAP_MIN, DROP_MIN);
  if (minNeed > avail) ctx.warn(`조직도 세로 공간 부족: 필요 ${minNeed.toFixed(2)}in, 가용 ${avail.toFixed(2)}in. 팀 수를 줄이거나 협력 네트워크 또는 인력 표를 생략할 것`);
  let teamH = TEAM_MIN, gap = GAP_MIN, drop = DROP_MIN;
  let slack = avail - need(showTeams, teamH, gap, drop);
  if (slack > 0 && showTeams) { const a = Math.min(TEAM_MAX - teamH, slack / showTeams); teamH += a; slack -= a * showTeams; }
  if (slack > 0 && showTeams > 1) { const a = Math.min(GAP_MAX - gap, slack / (showTeams - 1)); gap += a; slack -= a * (showTeams - 1); }
  if (slack > 0) { const a = Math.min(DROP_MAX - drop, slack); drop += a; slack -= a; }
  // 자리가 모자라면 상자를 본문 밴드 안으로 맞춤 (글자가 넘치면 검수 도구가 다시 알림)
  if (minNeed > avail && showTeams) {
    const cap = (avail - DROP_MIN - unitH - UNIT_PAD - GAP_MIN * (showTeams - 1)) / showTeams;
    if (cap > 0.2) { teamH = Math.min(teamH, cap); gap = GAP_MIN; drop = DROP_MIN; }
  }
  // 그래도 남으면 묶음 전체를 소제목 아래 영역의 세로 가운데로 모음
  const top = L.y + Math.max(0, slack / 2);
  const ceoBox = { x: cx - ceoW / 2, y: top, w: ceoW, h: CEO_H };
  const sideMid = top + CEO_H / 2;
  slide.addText(A.runsOf(A.parasFromString(LB.label("orgchart", "ceo", s.ceo), { sz: T.SIZE.body, b: true, color: T.COLOR.white, align: "center" })),
    { ...ceoBox, shape: P.ShapeType.rect, fill: { color: T.COLOR.navy }, line: { color: T.COLOR.navy, width: 0.75 }, valign: "middle", margin: 0, isTextBox: true, autoFit: false });
  // 경영지원은 대표 좌측, 자문위원회는 대표 우측에 같은 행으로 두어 계선을 수평 1줄로 유지
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
  // 본부 행
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
  // 우측 인력 구성 표
  if (people.length) {
    const R = subhead(ctx, slide, { x: b.x + leftW + 0.25, y: b.y, w: b.w - leftW - 0.25, h: b.h - netH }, LB.label("orgchart", "rightHead", s.rightHead));
    const head = LB.label("orgchart", "peopleHead", s.peopleHead);
    const rows2 = people.map((p) => [p.label || "", p.count || "", p.ratio || ""]);
    tableBlock(ctx, slide, R, { head, rows: rows2 });
  }
  // 하단 네트워크 띠
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

/** 산출물 예시(Illustrative 태그) : 전폭 표 또는 이미지. slots: {title, table|image} */
function illustrative(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  // 표가 행 높이 상한에 걸려 짧으면 제목과 표 묶음을 본문 세로 가운데에 둠
  const shift = s.table ? Math.max(0, (b.h - 0.45 - tableLayout(s.table, b.w, b.h - 0.45).total) / 2) : 0;
  A.text(slide, { x: b.x, y: b.y + shift, w: b.w, h: 0.35 }, LB.label("illustrative", "title", s.title), { sz: T.SIZE.panelHead, align: "center" });
  const box = { x: b.x, y: b.y + 0.45 + shift, w: b.w, h: b.h - 0.45 - 2 * shift };
  if (s.table) tableBlock(ctx, slide, box, s.table); else A.image(ctx.pres, slide, box, s.image, { label: "산출물 화면" });
  tag(ctx, slide, { x: b.x + 0.05, y: b.y + 0.05 + shift }, LB.label("illustrative", "tag", s.tag));
  source(ctx, slide, sb);
}
/** 종합: 상단 패널 + 하단 결론 밴드. slots: {panels, conclusion} */
const CONC_ITEM_SZ = 14; // 종합 패널 항목 글자 (패널 제목과 같은 크기, 굵기로 위계 구분)
const CONC_SUB_SZ = 12; // 종합 패널 근거 글자
const FIT_W_SLACK = 0.1; // 글줄 폭 추정 오차를 흡수하는 상자 폭 여유
function conclusion(ctx, slide, sb) {
  const s = sb.slots || {}, b = body(ctx, sb);
  const pn = s.panels || [];
  const n = Math.max(pn.length, 1), bandH = 0.55, bandGap = 0.2, gap = T.PANEL.GAP;
  const lists = pn.map((p) => (p && (p.items || p.text)) || []);
  // 패널 폭은 가장 긴 글줄에 맞춘 같은 폭으로 두고 패널 묶음과 결론 밴드를 가운데 정렬 (짧은 항목에서 오른쪽이 비지 않게 함)
  const needW = Math.max(...lists.map((l) => itemsNeedW(l, CONC_ITEM_SZ, CONC_SUB_SZ))) + 2 * T.PANEL.INSET + FIT_W_SLACK;
  const pw = Math.min((b.w - gap * (n - 1)) / n, needW);
  const gw = pw * n + gap * (n - 1), x0 = b.x + (b.w - gw) / 2;
  // 패널 높이는 내용 높이 기준으로 두고 패널과 결론 밴드 묶음을 본문 세로 가운데에 둠
  const gh = T.PANEL.TITLE_H + panelBodyH(pn.map(() => pw), lists, CONC_ITEM_SZ, b.h - bandH - bandGap - T.PANEL.TITLE_H, CONC_SUB_SZ);
  const top = b.y + (b.h - gh - bandGap - bandH) / 2;
  const pboxes = cols({ x: x0, y: top, w: gw, h: gh }, n, gap);
  const pps = pboxes.map((c, i) => (pn[i] ? { ...pn[i], sz: CONC_ITEM_SZ, subSz: CONC_SUB_SZ, noWarn: true } : null));
  const pgap = panelsGap(pboxes, pps); // 나란한 패널은 문단 간격도 하나로 맞춤
  pboxes.forEach((c, i) => { if (pps[i]) panel(ctx, slide, c, { ...pps[i], groupGapPt: pgap }); });
  label(ctx, slide, { x: x0, y: top + gh + bandGap, w: gw, h: bandH }, s.conclusion || "", { fill: T.COLOR.navyDeep, sz: T.SIZE.panelHead });
  source(ctx, slide, sb);
}
/** 자유 배치: blocks 를 본문 밴드 기준 비율 좌표(0-1)로 배치. blocks:[{kind, x, y, w, h, ...}] */
function free(ctx, slide, sb) {
  const b = body(ctx, sb);
  const abs = (k) => ({ x: b.x + k.x * b.w, y: b.y + k.y * b.h, w: k.w * b.w, h: k.h * b.h });
  ((sb.blocks || (sb.slots && sb.slots.blocks)) || []).forEach((k) => { // blocks 는 슬라이드 최상위와 slots 양쪽 허용
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
      default: ctx.warn(`free 블록 종류 ${k.kind} 미지원`);
    }
  });
  source(ctx, slide, sb);
}
/** 영역 격자와 블록 조합. 구성 규칙은 composite.js, 방법별 구성은 references/recipes.md */
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
