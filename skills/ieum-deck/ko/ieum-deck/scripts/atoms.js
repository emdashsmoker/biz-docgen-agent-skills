"use strict";
// atoms.js
// pptxgenjs 위의 원자 요소. 텍스트, 도형, 선, 표, 차트, 이미지와 밴드 4종, 커스텀 슬라이드 재생(playOwn).
// 좌표 단위는 인치, 색상은 tokens 의 6자리. 수치 상수는 tokens.js 에서만 가져온다.

const T = require("./tokens.js");
const LB = require("./labels.js"); // meta.labels.notation.source 로 추가한 주석 토큰 판정
const fs = require("fs");
const path = require("path");
// 나눔고딕 실측 폭(em). 없으면 tokens.METRIC 근사값 사용
// 재현: ASCII 글자 폭은 NanumGothic.ttf, NanumGothicBold.ttf 의 hmtx 전진폭을 head.unitsPerEm 으로 나눈 값(fontTools 로 확인)
//       범주 키(hangul, cjkpunct, fullwidth, enclosed, other)는 범주별 대표 폭
let METRICS = null;
try { METRICS = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "assets", "font-metrics.json"), "utf8")); } catch (e) { METRICS = null; }

// ---------------------------------------------------------------- 색상과 서체
function remap(hex) {
  if (!hex || hex === "none") return hex;
  const h = String(hex).replace("#", "").toUpperCase();
  return T.COLOR_REMAP[h] || h;
}
function face(bold) {
  return bold ? T.FONT.bold : T.FONT.regular;
}

// ---------------------------------------------------------------- 텍스트 폭 추정
/** 한자 코드 범위: 통합 한자, 확장 A, 호환 한자(한글 입력기가 동자이음 한자를 입력하는 영역) */
const isHanja = (c) => (c >= 0x4e00 && c <= 0x9fff) || (c >= 0x3400 && c <= 0x4dbf) || (c >= 0xf900 && c <= 0xfaff);
/** 전각 폭 기호: 화살표, 괘선, 도형(○ ● ◐ □ ■), 기타 기호, ※. 나눔고딕에서 한글과 같은 0.94em */
const isWideSymbol = (c) => (c >= 0x2190 && c <= 0x21ff) || (c >= 0x2500 && c <= 0x27bf) || c === 0x203b;
function charEm(ch, bold) {
  const c = ch.codePointAt(0);
  if (METRICS) {
    const m = METRICS[bold ? "bold" : "regular"];
    if (m[ch] != null) return m[ch];
    if (c >= 0xac00 && c <= 0xd7a3) return m.hangul;
    if (c >= 0x3000 && c <= 0x303f) return m.cjkpunct;
    if (c >= 0xff00 && c <= 0xffef) return m.fullwidth;
    if (c >= 0x2460 && c <= 0x24ff) return m.enclosed;
    if (isHanja(c)) return m.hangul; // 한자(통합, 확장 A, 호환)는 나눔고딕에서 한글과 같은 전각 폭
    if (isWideSymbol(c)) return m.hangul;
    return m.other;
  }
  if (ch === " ") return T.METRIC.EM_SPACE;
  const wide = (c >= 0xac00 && c <= 0xd7a3) || (c >= 0x3000 && c <= 0x303f) || (c >= 0xff00 && c <= 0xffef) || isHanja(c) || (c >= 0x2460 && c <= 0x24ff) || (c >= 0x3130 && c <= 0x318f) || isWideSymbol(c);
  return wide ? T.METRIC.EM_HANGUL : T.METRIC.EM_LATIN;
}
function textEm(s, bold) {
  let n = 0;
  for (const ch of String(s)) n += charEm(ch, bold);
  return n;
}
/** widthIn 폭 상자에서 fontPt 로 차지하는 줄 수 */
function estimateLines(str, widthIn, fontPt, bold) {
  if (!str) return 0;
  const cap = ((widthIn * 72) / fontPt) * (METRICS ? T.METRIC.SAFETY_METRIC : T.METRIC.SAFETY);
  let lines = 0;
  for (const para of String(str).split("\n")) {
    let cur = 0, n = 1;
    for (const w of para.split(" ")) {
      const we = textEm(w, bold);
      const need = we + (cur > 0 ? charEm(" ", bold) : 0);
      if (cur > 0 && cur + need > cap) { n += 1; cur = we; } else cur += need;
      if (cur > cap) { n += Math.floor(cur / cap); cur = cur % cap; }
    }
    lines += n;
  }
  return lines;
}
const LINE_FIT_EPS = 0.01; // 폭 반올림으로 한 줄 판정이 두 줄로 바뀌지 않게 두는 여유 (인치)
/** 문구를 한 줄에 담는 최소 폭(인치). estimateLines 가 1줄로 판정하는 폭과 같은 기준 */
function lineWidthIn(str, pt, bold) {
  return (textEm(str, bold) * pt) / 72 / (METRICS ? T.METRIC.SAFETY_METRIC : T.METRIC.SAFETY) + LINE_FIT_EPS;
}
/** 문구 목록에서 가장 넓은 어절(공백 단위)의 한 줄 폭(인치). 좁은 판형에서 라벨 열과 상자 폭의 하한으로 써서 어절 중간 줄바꿈을 막음 */
function wordWidthIn(texts, pt, bold) {
  const words = [].concat(texts || []).flatMap((t) => String(t == null ? "" : t).split(/\s+/)).filter(Boolean);
  return words.length ? Math.max(...words.map((w) => lineWidthIn(w, pt, bold))) : 0;
}
function lineHeightIn(pt, ratio) {
  return (pt * (ratio || T.METRIC.LINE_HEIGHT)) / 72;
}

/**
 * 문단 묶음이 상자(inner w,h)에 들어가도록 글꼴 크기를 균일 축소. 원본 장표의 서체보다 나눔고딕이 넓으면
 * 같은 크기에서 줄바꿈이 늘어나는 현상을 상자 안에서 흡수한다. 하한은 minPt (본문 11pt).
 * 반환: 새 paras (원본 불변)
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
  // 줄바꿈이 전혀 없으면(모든 문단 1줄) 높이 부족은 원본과 같은 넘침 허용 상태이므로 축소하지 않음
  const wraps = paras.some((p) => {
    const txt = p.runs.filter((r) => !r.br).map((r) => r.t).join("");
    const r0 = p.runs.find((r) => !r.br) || { sz: T.SIZE.body };
    const indent = p.bullet ? (p.indent != null ? Math.abs(p.indent) : T.PARA.bulletIndentIn) : (p.marL || 0);
    return estimateLines(txt, innerW - indent, r0.sz || T.SIZE.body, r0.b) > 1;
  });
  if (!wraps && paras.length <= 3) return paras;
  let scale = 1.0;
  while (scale > 0.6 && need(scale) > innerH + 0.1) scale -= 0.04; // PowerPoint 는 여백 안 넘침을 허용하므로 0.1인치 허용
  let out = scale >= 0.999 ? paras : paras.map((p) => ({ ...p, runs: p.runs.map((r) => ({ ...r, sz: Math.max(floor, +(((r.sz || T.SIZE.body) * scale)).toFixed(1)) })) }));
  // 글꼴 하한에 걸려 여전히 넘치면 문단 사이 간격을 줄여 상자 안에 넣음
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

// ---------------------------------------------------------------- 기본 옵션
const DEFAULT_MG_IN = [0.1, 0.05, 0.1, 0.05]; // OOXML bodyPr 기본 inset (l,t,r,b). 커스텀 슬라이드 원문에 없는 여백 값을 채움
const TEXT_MG_IN = [0.075, 0.05, 0.075, 0.05]; // 여백을 지정하지 않은 생성 글 상자의 여백 (l,t,r,b). 좌우 합 0.15
/** 글 상자 여백 [좌, 상, 우, 하](인치) → [좌, 상, 우, 하](pt). 빈 값은 기본 여백 */
function mgPt(mg) {
  const m = mg && mg.length === 4 ? mg.map((v, i) => (v == null ? DEFAULT_MG_IN[i] : v)) : DEFAULT_MG_IN;
  return m.map((v) => +(v * 72).toFixed(1));
}
/** 글 상자 여백 [좌, 상, 우, 하](인치) → pptxgenjs 글 상자 margin 인자. pptxgenjs 는 [좌, 우, 하, 상] 순서로 읽음 */
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

// ---------------------------------------------------------------- 텍스트 실행 목록 변환
/**
 * paras: [{align, bullet, buChar, lvl, marL, indent, spcBef, spcAft, lnSpc, runs:[{t,sz,b,color,u,br}]}]
 * → pptxgenjs text 배열. 문단 속성은 문단 첫 run 에 부여
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
      // 불릿 없는 들여쓰기는 indentLevel 로 근사
      pOpt.indentLevel = Math.min(4, Math.round(p.marL / 0.25));
    }
    if (p.spcBef != null) pOpt.paraSpaceBefore = p.spcBef;
    if (p.spcAft != null) pOpt.paraSpaceAfter = p.spcAft;
    if (p.lnSpc != null) pOpt.lineSpacingMultiple = p.lnSpc;
    const runs = p.runs && p.runs.length ? p.runs : [{ t: "", sz: d.sz || T.SIZE.body }];
    // 같은 서식의 인접 run 을 병합 (pptxgenjs 가 run 마다 pPr 를 내보내는 결함을 줄이기 위함)
    const merged = [];
    runs.forEach((r) => {
      const prev = merged[merged.length - 1];
      if (prev && !prev.br && !r.br && prev.sz === r.sz && !!prev.b === !!r.b && prev.color === r.color && !!prev.u === !!r.u) prev.t += r.t;
      else merged.push({ ...r });
    });
    merged.forEach((r, ri) => {
      if (r.br) return; // 줄바꿈 run 은 앞 run 의 breakLine 으로 처리
      const o = {
        fontSize: r.sz || d.sz || T.SIZE.body,
        bold: !!(r.b != null ? r.b : d.bold),
        color: remap(r.color || d.color || T.COLOR.textDark),
        fontFace: face(r.b != null ? r.b : d.bold),
      };
      if (r.u) o.underline = { style: "sng" };
      // 문단 속성은 첫 run 에 부여. 정렬과 들여쓰기는 모든 run 에 복사 (pptxgenjs 는 정렬 변화나 bullet 출현을 문단 분리 신호로 삼음)
      // run 마다 생기는 여분의 pPr 는 finalize.py 가 제거
      const first = out.length === 0 || out[out.length - 1].options.breakLine;
      Object.assign(o, first ? pOpt : { align: pOpt.align, indentLevel: pOpt.indentLevel, lineSpacingMultiple: pOpt.lineSpacingMultiple });
      const prev = merged[ri - 1];
      if (prev && prev.br) o.softBreakBefore = true; // 문단 안 줄바꿈(a:br)은 번호와 정렬을 유지
      if (ri === merged.length - 1 && !last) o.breakLine = true;
      out.push({ text: r.t, options: o });
    });
  });
  return out;
}
/** 문자열 → paras (줄바꿈으로 문단 분리) */
function parasFromString(s, base) {
  const b = base || {};
  return String(s).split("\n").map((line) => ({ ...b, runs: [{ t: line, sz: b.sz, b: b.b, color: b.color }] }));
}

// ---------------------------------------------------------------- 원자 요소
/** 텍스트 상자. paras 또는 문자열 */
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

/** 도형(채움, 선, 내부 텍스트). atom 은 own-deck 의 shape 원자 형식 */
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
  // 조정값(꼭짓점 폭 등)은 pptxgenjs 가 지원하지 않아 도형 이름에 실어 finalize.py 가 avLst 로 옮김
  if (atom.adj != null && atom.preset !== "roundRect" && atom.preset !== "round2SameRect") base.objectName = `adj:${atom.adj}`;
  let paras = ov.paras !== undefined ? ov.paras : atom.paras;
  if (paras) {
    // 작은 상자(번호 원, 단일 문자 라벨)는 기본 여백이 폭을 잠식하므로 여백 0
    const small = atom.w < T.PANEL.SMALL_BOX_W;
    const narrowChevron = (atom.preset === "chevron" || atom.preset === "homePlate") && atom.w < 1.6 * atom.h; // 꼭짓점이 텍스트 폭을 잠식하는 짧은 셰브론
    const mgArr = small || narrowChevron ? [0, 0, 0, 0] : mgPt(atom.mg);
    const mg = mgArr.map((v) => v / 72);
    // 셰브론과 홈플레이트는 꼭짓점 폭만큼 텍스트 영역이 줄어듦 (OOXML 텍스트 사각형 정의)
    const pointW = atom.preset === "chevron" || atom.preset === "homePlate" ? Math.min(atom.w, atom.h) * (atom.adj != null ? atom.adj / 100000 : 0.5) : 0;
    const innerW = atom.w - mg[0] - mg[2] - (atom.preset === "chevron" ? 2 * pointW : pointW);
    if (ov.scale != null && ov.scale < 1) paras = paras.map((p) => ({ ...p, runs: p.runs.map((r) => ({ ...r, sz: Math.max(ov.minPt || T.SIZE.BODY_MIN, +((r.sz || T.SIZE.body) * ov.scale).toFixed(1)) })) }));
    if (ov.fillText) { paras = growParas(paras, innerW, atom.h - mg[1] - mg[3], 1.0); atom = { ...atom, va: "middle" }; } // 빈 면적을 흡수한 상자는 간격만 키워 채우고 글꼴은 계층 기준값을 유지
    paras = fitParas(paras, innerW, atom.h - mg[1] - mg[3], ov.minPt);
    // 1문단 1줄로 판정된 텍스트는 줄바꿈을 끄고 렌더러의 자간 오차에 따른 예기치 않은 줄바꿈을 막음
    const oneLine = paras.length === 1 && !paras[0].runs.some((r) => r.br) && estimateLines(paras[0].runs.map((r) => r.t).join(""), innerW, paras[0].runs[0].sz || T.SIZE.body, paras[0].runs[0].b) <= 1;
    slide.addText(runsOf(paras, { color: ov.textColor }), {
      ...base, shape: st, isTextBox: true,
      valign: ov.fillText ? "middle" : (ov.va || atom.va || "middle"),
      margin: boxMargin(mgArr.map((v) => v / 72)),
      wrap: !(small || oneLine) || narrowChevron, // 짧은 셰브론은 항상 줄바꿈 (텍스트 사각형이 좁아 넘침)
      vert: atom.vert || undefined,
      autoFit: false,
    });
  } else {
    slide.addShape(st, base);
  }
}

/** 원문 앞부분 키 "~원문" 으로 슬롯을 찾음 (t{k} 번호를 세지 않아도 되는 치환 방식). 공백 무시, 앞부분 일치 */
function textKey(sl, cur) {
  const norm = (v) => String(v).replace(/\s+/g, "");
  const c = norm(cur);
  if (!c) return null;
  for (const k of Object.keys(sl)) {
    if (k[0] === "~" && k.length > 1 && c.startsWith(norm(k.slice(1)))) return sl[k];
  }
  return null;
}

/** 텍스트 상자 안 글자가 실제로 차지하는 폭과 높이 (인치) */
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

/** 형제 상자 판정 키: 원본 글꼴 크기 + 상자 폭과 높이(0.1인치 단위). 같은 키의 상자는 같은 축소율 */
function sizeKey(atom, paras) {
  return `${Math.round(paras[0].runs[0].sz || T.SIZE.body)}|${Math.round(atom.w * 10)}|${Math.round(atom.h * 10)}`;
}

/** 상자를 채우도록 글꼴을 키움 (상한 maxScale). 줄 간격도 spcBef 로 분배 */
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
  return out.map((p, i) => (i === 0 ? p : { ...p, spcBef: (p.spcBef || 0) + extra })); // 문단 사이에만 간격 (세로 가운데 정렬 유지)
}

/** 상자에 맞추기 위해 필요한 글꼴 축소율 (1 이면 축소 불필요) */
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

/** 아이콘 이미지 대체: 주변 라벨의 키워드로 종류를 정해 도형으로 조합 (글리프 서체 의존 없음)
 * kinds: lock(물리·출입), shield(기술·네트워크·VPN), clipboard(관리·교육·점검), calendar(일정·보고·WBS), data(데이터·DB), gear(시사점·도구), check(기본). 한글과 영문 키워드 모두 인식 */
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
  const d = Math.min(box.w, box.h) * 0.82; // 원본 그림보다 작게 그려 인접 텍스트와 간격 확보
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
  if (k === "dashboard") { // 모니터 + 상승 막대 3개 + 받침
    slide.addShape(pres.ShapeType.roundRect, { x: x + d * 0.05, y: y + d * 0.08, w: d * 0.9, h: d * 0.62, rectRadius: d * 0.06, fill: navy, line: noLine });
    [[0.2, 0.38, 0.2], [0.4, 0.28, 0.3], [0.6, 0.18, 0.4]].forEach(([rx, ry, rh]) => slide.addShape(pres.ShapeType.rect, { x: x + d * rx, y: y + d * ry, w: d * 0.14, h: d * rh, fill: { color: T.COLOR.white }, line: noLine }));
    slide.addShape(pres.ShapeType.rect, { x: x + d * 0.42, y: y + d * 0.72, w: d * 0.16, h: d * 0.1, fill: navy, line: noLine });
    slide.addShape(pres.ShapeType.roundRect, { x: x + d * 0.25, y: y + d * 0.82, w: d * 0.5, h: d * 0.08, rectRadius: d * 0.03, fill: navy, line: noLine });
    return;
  }
  if (k === "shredder") { // 문서 + 투입구 + 본체 + 파쇄 조각
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

/** 선. bentConnector 는 직선 2-3개로 분해 (pptxgenjs 미지원) */
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
    // 구간마다 진행 방향(flip)을 지정하여 화살촉이 실제 끝점(마지막 구간 끝)에만 붙게 함
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

/** 네이티브 표. atom.table = {colw, rowh, rows:[[cell]]}. cell = {colspan,rowspan,merged,fill,va,mg,borders,paras} */
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
      // 채움을 지정하지 않으면 렌더러가 표 스타일의 강조색을 넣으므로 흰색으로 고정
      co.fill = c.fill && c.fill !== "none" ? { color: remap(c.fill) } : { color: T.COLOR.white };
      co.valign = c.va || "middle";
      // pptxgenjs 표 셀 margin 은 [상, 우, 하, 좌] 이며 첫 값이 1 미만이면 인치로 해석
      const m = (c.mg && c.mg.length === 4 ? c.mg : []).map((v, i) => (v == null ? T.PANEL.CELL_MG[i] : v));
      const cm = m.length ? m : T.PANEL.CELL_MG;
      co.margin = [cm[1], cm[2], cm[3], cm[0]].map((v) => Math.min(0.99, v));
      const border = ["T", "R", "B", "L"].map((side) => {
        const b = c.borders && c.borders[side];
        if (b && b.color === "none") return { type: "none" };
        if (b) return { type: "solid", pt: b.pt || T.PANEL.LINE_PT, color: remap(b.color || T.COLOR.borderLight) };
        // 원본 셀이 테두리를 명시한 경우 미지정 변은 선 없음(단위 행 투명 처리). 생성 템플릿(미명시)은 기본 회색 선
        if (c.borders) return { type: "none" };
        return { type: "solid", pt: T.PANEL.LINE_PT, color: T.COLOR.borderLight };
      });
      co.border = border;
      let paras = c.paras || [{ runs: [{ t: "", sz: o.sz || T.SIZE.tableBody }] }];
      // 셀 안 강제 줄바꿈은 한 줄에 들어가면 공백으로 합쳐 행 높이 팽창을 막음
      paras = paras.map((p) => {
        if (!p.runs.some((r) => r.br)) return p;
        const joined = p.runs.map((r) => (r.br ? " " : r.t)).join("").replace(/\s+/g, " ").trim();
        const r0 = p.runs.find((r) => !r.br) || p.runs[0];
        const cwTmp = tb.colw.slice(colIdx, colIdx + (c.colspan || 1)).reduce((x, y) => x + y, 0) - 0.16;
        return estimateLines(joined, cwTmp, r0.sz || T.SIZE.tableBody, r0.b) <= 1 ? { ...p, runs: [{ ...r0, t: joined }] } : p;
      });
      // 셀 폭(병합 포함)과 행 높이에 맞춰 글꼴 축소. 열 인덱스는 병합 셀을 건너뛰며 누적
      const span = c.colspan || 1;
      const cw = tb.colw.slice(colIdx, colIdx + span).reduce((a, b) => a + b, 0);
      const rh = tb.rowh.slice(rowIdx, rowIdx + (c.rowspan || 1)).reduce((a, b) => a + b, 0);
      // 행 높이 팽창 방지: 나눔고딕 행간이 높아 여유 0.05인치와 행간 1.35 로 판정. 표 전체에서 같은 원본 크기는 같은 축소율 (셀마다 크기가 따로 놀지 않게)
      // 여러 줄 셀(문단 2개 이상 또는 원본 크기에서 줄바꿈)은 원본처럼 행이 늘어나도록 두고, 1줄 셀만 행 높이에 맞춰 축소
      const r00 = paras[0].runs.find((x) => !x.br) || paras[0].runs[0];
      const multi = paras.length >= 2 || estimateLines(paras[0].runs.filter((x) => !x.br).map((x) => x.t).join(""), cw - cm[0] - cm[2], r00.sz || T.SIZE.tableBody, r00.b) > 1;
      const fitted = fitParas(paras, cw - cm[0] - cm[2], multi ? 99 : rh - cm[1] - cm[3] - 0.05, o.minPt || T.SIZE.OWN_MIN - 1, T.METRIC.TABLE_LINE_HEIGHT);
      const sz0 = Math.round((paras[0].runs[0] && paras[0].runs[0].sz) || o.sz || T.SIZE.tableBody);
      const r = ((fitted[0].runs[0] && fitted[0].runs[0].sz) || sz0) / sz0;
      if (pass === 0) { (ratioBySz[sz0] = ratioBySz[sz0] || []).push(r); return; }
      // 대다수(80%) 셀이 맞는 축소율로 통일하고 극소수 좁은 셀만 개별 축소 (전체가 최소 셀에 끌려가지 않게)
      const arr = (ratioBySz[sz0] || [1]).slice().sort((p, q) => p - q);
      const uni = Math.min(arr[Math.floor(arr.length * 0.2)], 1);
      const own = r;
      const use = Math.min(uni, own < uni ? own : uni);
      paras = paras.map((p) => ({ ...p, runs: p.runs.map((x) => ({ ...x, sz: Math.max(o.minPt || T.SIZE.OWN_MIN - 1, +(((x.sz || sz0) * use)).toFixed(1)) })) }));
      const runs = runsOf(paras, { sz: o.sz || T.SIZE.tableBody });
      // 셀 정렬은 첫 문단 align, 없으면 열 규칙(호출부가 opt.align 으로 지정)
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

/** 네이티브 차트. spec = {type: bar|line|pie|doughnut, barDir, categories, series:[{name, values}], holeSize, showLegend, highlight} */
const COL_GAP_SINGLE = 130; // 단일 계열 세로 막대의 막대 간격 (막대 폭 대비 %)
const NEG_LABEL_ROOM = 0.22, POS_LABEL_ROOM = 0.12; // 음수가 있는 막대 차트의 값 축 여유 (값 범위 대비. 음수 막대 아래와 양수 막대 위 수치 자리)
/** 두 색 사이를 같은 간격으로 나눈 n 색 (양 끝 색 포함) */
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
      // 항목 비교는 큰 값이 위: 내림차순 정렬 후 범주 축을 역순으로
      const pairs = cats.map((c, i) => [c, series[0].values[i]]).sort((a, b) => b[1] - a[1]);
      cats = pairs.map((p) => p[0]);
      series[0].labels = cats;
      series[0].values = pairs.map((p) => p[1]);
      opt.catAxisOrientation = "maxMin";
    }
    // 단일 계열 세로 막대는 막대 사이를 넓혀 굵기를 줄임 (막대 길이 차이가 눈에 띄도록)
    opt.barGapWidthPct = series.length === 1 && opt.barDir === "col" ? COL_GAP_SINGLE : 60;
    if (spec.grouping === "stacked" || spec.grouping === "percentStacked") {
      opt.barGrouping = spec.grouping; opt.dataLabelPosition = "ctr";
      // 조각 안 레이블은 어두운 글자 1색이므로 가장 진한 네이비를 빼고 밝은 쪽 색만 사용
      // 계열이 밝은 색 수보다 많으면 가장 짙은 색과 가장 밝은 색 사이를 같은 간격으로 나눔 (배경 틴트는 흰 바탕과 구분되지 않아 계열 색으로 쓰지 않음)
      if (series.length > 1) {
        const light = T.COLOR.navyRamp.slice(1);
        opt.chartColors = series.length > light.length ? rampBetween(light[0], light[light.length - 1], series.length) : light;
      }
    }
    // 음수 막대가 있으면 0 기준선이 보여야 증감 방향이 읽히므로 범주 축 선을 표시
    if (series.some((sr) => sr.values.some((v) => v < 0))) {
      opt.catAxisLineShow = true; opt.catAxisLineColor = T.COLOR.border; opt.catAxisLabelPos = "low";
      // 범주 이름이 도표 아래 끝(low)에 붙으므로 가장 긴 음수 막대 끝 바깥 수치가 범주 이름 줄을 침범하지 않도록 값 축 하한과 상한에 수치 자리를 둠
      if (!opt.barGrouping) {
        const all = series.flatMap((sr) => sr.values);
        const lo = Math.min(0, ...all), hi = Math.max(0, ...all), span = hi - lo || 1;
        opt.valAxisMinVal = +(lo - span * NEG_LABEL_ROOM).toFixed(4);
        if (hi > 0) opt.valAxisMaxVal = +(hi + span * POS_LABEL_ROOM).toFixed(4);
      }
    }
    // 범주가 1개인 누적 막대(구성비 막대)는 범주 축 이름이 칸 캡션과 겹치므로 축을 숨김
    if (cats.length === 1) opt.catAxisHidden = true;
    if (spec.highlight != null && series.length === 1) {
      opt.chartColors = series[0].values.map((_, i) => (i === spec.highlight ? T.COLOR.navy : T.COLOR.navyPastel));
    }
  }
  if (spec.type === "pie" || spec.type === "doughnut") {
    opt.chartColors = series[0].values.map((_, i) => T.COLOR.navyRamp[i % T.COLOR.navyRamp.length]);
    opt.showLegend = true; opt.legendPos = "r";
    // WHY: pptxgenjs 는 차트 전체에 레이블 색 1개만 지정 가능. 조각 안쪽 흰 글자는 옅은 조각에서 읽히지 않으므로
    //      레이블을 조각 바깥에 어두운 글자로 둔다
    opt.dataLabelPosition = "outEnd"; opt.showPercent = true; opt.showValue = false;
    opt.dataLabelColor = T.COLOR.textDark;
    if (spec.type === "doughnut") { opt.holeSize = spec.holeSize || 78; opt.showLegend = false; opt.showPercent = false; opt.showValue = false; opt.showLabel = false; } // 중앙 수치 텍스트는 별도 텍스트 상자가 담당
  }
  if (spec.type === "line") { opt.lineSize = 2; opt.lineDataSymbol = "circle"; opt.lineDataSymbolSize = 6; opt.chartColors = [T.COLOR.navy, T.COLOR.navyPastel, T.COLOR.navyPastel2]; opt.dataLabelPosition = "t"; } // 레이블이 선과 겹치지 않도록 표식 위에 배치
  slide.addChart(ctype, series, opt);
}

let IMAGE_BASE = null; // storyboard 폴더. 빌드한 위치와 관계없이 같은 storyboard 가 같은 이미지를 찾도록 상대 경로의 기준으로 사용

/** 이미지 상대 경로의 기준 폴더 지정 (build.js 가 storyboard 폴더로 설정) */
function setImageBase(dir) { IMAGE_BASE = dir; }

/** 이미지 경로 해석. 상대 경로는 storyboard 폴더 기준 파일이 있으면 그 경로, 없으면 실행 폴더 기준 (이전 동작 유지) */
function resolveImage(src) {
  if (!src || /^data:/.test(src) || path.isAbsolute(src) || !IMAGE_BASE) return src;
  const p = path.resolve(IMAGE_BASE, src);
  return fs.existsSync(p) ? p : src;
}

/** 이미지. 경로 없으면 자리 상자 (틴트 채움, 점선, "이미지" 라벨) */
function image(pres, slide, box, srcIn, opt) {
  const o = opt || {};
  const src = resolveImage(srcIn);
  if (src) {
    // 원본 비율을 읽어 상자 안에 맞춤(contain) 후 가운데 배치. pptxgenjs sizing 은 렌더러별 해석이 달라 직접 계산
    const dim = imageDims(src);
    let { x, y, w, h } = box;
    if (dim && dim.w && dim.h && o.fit !== "stretch") {
      const r = Math.min(box.w / dim.w, box.h / dim.h);
      w = +(dim.w * r).toFixed(3); h = +(dim.h * r).toFixed(3);
      x = +(box.x + (box.w - w) / 2).toFixed(3); y = +(box.y + (box.h - h) / 2).toFixed(3);
    }
    const im = { x, y, w, h };
    if (/^data:/.test(src)) im.data = src; else im.path = src;
    if (src !== srcIn) im.altText = srcIn; // 대체 텍스트는 storyboard 에 적은 경로 그대로 (작업 폴더 절대 경로가 파일에 남지 않도록)
    slide.addImage(im);
  } else {
    slide.addText([{ text: o.label || "이미지", options: { fontSize: T.SIZE.note, color: T.COLOR.textMuted, fontFace: T.FONT.regular } }], {
      x: box.x, y: box.y, w: box.w, h: box.h, shape: pres.ShapeType.rect, fill: { color: T.COLOR.tintLight },
      line: { color: T.COLOR.borderLight, width: 0.5, dashType: "dash" }, align: "center", valign: "middle", margin: 0,
    });
  }
  // 캡션은 이미지를 설명하는 본문 계열 글이므로 본문 하한 크기(11pt)와 본문 글자색(textDark)으로 조판 (주석의 작은 회색 글씨와 구분)
  if (o.caption) text(slide, { x: box.x, y: box.y + box.h + 0.03, w: box.w, h: 0.25 }, o.caption, { sz: T.SIZE.BODY_MIN, color: T.COLOR.textDark, align: "center", mg: [0, 0, 0, 0] });
}

/** PNG, JPEG, GIF 의 픽셀 크기 (경로 또는 data URI). 실패 시 null */
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
  } catch (e) { /* 크기 미상 */ }
  return null;
}

// ---------------------------------------------------------------- 밴드
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
 * 본문 슬라이드 밴드. mode: full(마커 있음) | noMarker | headerOnly
 * band = {secNo, secTitle, tracker, headline, marker}
 */
function bodyBand(pres, slide, S, band, mode, opt) {
  const o = opt || {};
  const hl = band.headline || "";
  // 절 번호와 절 제목은 한 문단의 두 글자 묶음으로 조판하여 번호 자릿수와 글꼴 폭이 달라도 제목이 번호 뒤에 이어지게 함
  // (번호 상자와 제목 상자를 따로 두면 "10." 처럼 번호가 길어질 때 렌더러의 글자 폭에 따라 마침표와 제목이 겹침)
  const no = band.secNo || "";
  if (no) {
    const runs = [{ t: `${no} `, sz: T.SIZE.secNo, color: T.COLOR.textDark }, { t: band.secTitle || "", sz: T.SIZE.secTitle, color: T.COLOR.textDark }];
    text(slide, { x: S.secNo.x, y: S.secNo.y, w: S.secTitle.x + S.secTitle.w - S.secNo.x, h: S.secNo.h }, [{ align: "left", runs }], { valign: "middle", mg: [0, 0, 0, 0] });
  } else text(slide, S.secTitle, band.secTitle || "", { sz: T.SIZE.secTitle, color: T.COLOR.textDark, valign: "middle", mg: [0, 0, 0, 0] });
  text(slide, S.tracker, band.tracker || "", { sz: T.SIZE.tracker, color: T.COLOR.textDark, align: "right", valign: "middle", mg: [0, 0, 0, 0] });
  if (mode === "headerOnly") return;
  const hlParas = o.accentHeadline ? headlineWithAccent(hl, o.accentHeadline) : parasFromString(hl, { sz: T.SIZE.headline, b: true, color: T.COLOR.textDark, align: "center" });
  text(slide, S.headline, hlParas, { valign: "middle", mg: [0, 0, 0, 0] });
  // 헤드라인은 위아래 선 사이에 놓여야 소속이 확정되므로 선 2개를 한 쌍으로 그림
  for (const ry of [S.ruleTopY, S.ruleY]) {
    slide.addShape(pres.ShapeType.line, { x: S.marginX, y: ry, w: S.ruleW, h: 0, line: { color: T.COLOR.textDark, width: T.BAND.RULE_PT } });
  }
  if (mode === "noMarker") return;
  markerGlyph(pres, slide, S);
  text(slide, S.markerText, band.marker || "", { sz: T.SIZE.marker, bold: true, color: T.COLOR.textDark, valign: "middle", mg: [0, 0, 0, 0] });
  // 마커 밴드 우측에 각주 번호를 붙인 부제(옵션)
  if (band.markerNote) {
    const x = S.markerText.x + textEm(band.marker || "", true) * T.SIZE.marker / 72 + 0.25;
    text(slide, { x, y: S.markerText.y, w: Math.max(1.0, S.marginX + S.ruleW - x), h: S.markerText.h }, band.markerNote,
      { sz: T.SIZE.note, color: T.COLOR.textMuted, valign: "middle", mg: [0, 0, 0, 0] });
  }
}
/** 헤드라인의 핵심 어구 1곳을 강조색으로 */
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
/** 각주 목록. 슬라이드 하단 출처 행 위에 1) 2) 형식으로 배치 */
function footnotes(slide, S, items) {
  const arr = [].concat(items || []).filter(Boolean);
  if (!arr.length) return;
  const paras = arr.map((t, i) => ({ align: "left", runs: [{ t: /^\d+\)/.test(String(t).trim()) ? String(t) : `${i + 1}) ${t}`, sz: T.SIZE.note, color: T.COLOR.textMuted }] }));
  text(slide, { x: S.bodyX, y: S.noteY - 0.2 * arr.length, w: S.bodyW, h: 0.2 * arr.length }, paras, { valign: "top", mg: [0, 0, 0, 0] });
}
function pageNo(slide, S, n) {
  text(slide, S.pageNo, String(n), { sz: T.SIZE.pageNo, color: T.COLOR.textGray, align: "right", valign: "middle", mg: [0, 0, 0, 0] });
}

// ---------------------------------------------------------------- 커스텀 슬라이드 재생
/**
 * own-deck 의 슬라이드 원자를 순서대로 조판. slots 로 텍스트와 표 셀과 이미지 치환
 * slots 키: t{k} (k번째 텍스트 원자), tb{k}.r{i}c{j}, img{k}, ch{k} (차트 spec)
 * 반환: {textIds:[{id, text}], imageIds, chartIds} (templates.md 문서화와 lint 용)
 */
function playOwn(pres, slide, ownSlideSrc, slots, ctx) {
  const ownSlide = { ...ownSlideSrc, atoms: ownSlideSrc.atoms.map((a) => ({ ...a })) }; // 좌표 조정이 원본 geometry 에 누적되지 않게 얕은 복제
  const sl = slots || {};
  const ids = { texts: [], tables: [], images: [], charts: [] };
  let tk = 0, bk = 0, ik = 0, ck = 0;
  const sx = ctx && ctx.S ? ctx.S.sx : 1;
  const sy = ctx && ctx.S ? ctx.S.sy : 1;
  const sc = (a) => (sx === 1 && sy === 1 ? a : { ...a, x: +(a.x * sx).toFixed(3), y: +(a.y * sy).toFixed(3), w: +(a.w * sx).toFixed(3), h: +(a.h * sy).toFixed(3) });
  // 사전 패스: 동일 원본 글꼴 크기 계열의 최소 축소율 (형제 상자 간 글자 크기가 따로 놀지 않게 함). 슬롯 치환 텍스트는 원문 기준으로 근사
  const ratioBySize = {};
  const skippedBoxes = []; // 빈 문자열 슬롯으로 생략된 상자. 여기에 닿는 연결선도 생략
  const widen = {}; // 표 인덱스 → 새 우측 끝 x (삽화 자리 흡수)
  const widenLeft = {}; // 표 인덱스 → 새 좌측 시작 x
  const skipImage = new Set();
  const tinyCount = ownSlide.atoms.filter((o) => o.kind === "image" && o.w < 0.45 && o.h < 0.45).length;
  const skipShape = new Set();
  // 화살표는 위아래 상자의 가운데에 맞춤 (원본의 미세한 치우침 보정)
  const ARROW = new Set(["downArrow", "upArrow", "leftArrow", "rightArrow"]);
  ownSlide.atoms.forEach((a) => {
    if (a.kind !== "shape" || !ARROW.has(a.preset)) return;
    const cx0 = a.x + a.w / 2, cy0 = a.y + a.h / 2;
    // 좌우로 나란한 상자 사이에 세로 화살표가 놓였으면 가로 화살표로 바꿈 (반대도 동일)
    const yOverlap = (b) => Math.min(b.y + b.h, a.y + a.h) - Math.max(b.y, a.y) > a.h * 0.4;
    const xOverlap = (b) => Math.min(b.x + b.w, a.x + a.w) - Math.max(b.x, a.x) > a.w * 0.4;
    const cand = ownSlide.atoms.filter((b) => b !== a && b.kind === "shape" && !ARROW.has(b.preset) && b.w > a.w * 2);
    const rowMates = cand.filter((b) => yOverlap(b) && Math.abs(b.x + b.w / 2 - cx0) < b.w + 0.8);
    const colMates = cand.filter((b) => xOverlap(b) && Math.abs(b.y + b.h / 2 - cy0) < b.h + 0.8);
    // 양옆에 상자가 있으면 가로, 위아래에 있으면 세로로 방향을 맞춤
    const hasLeft = rowMates.some((b) => b.x + b.w <= cx0 + 0.05);
    const hasRight = rowMates.some((b) => b.x >= cx0 - 0.05);
    const hasUp = colMates.some((b) => b.y + b.h <= cy0 + 0.05);
    const hasDown = colMates.some((b) => b.y >= cy0 - 0.05);
    // 양쪽 모두 상자가 있으면 더 가까운 쪽을 따름
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
      // 교차축은 상자 중심, 진행축은 위아래 상자 사이 간격의 한가운데
      const target = near.reduce((s2, b) => s2 + b.x + b.w / 2, 0) / near.length;
      if (Math.abs(target - cx) < 0.25) a.x = +(target - a.w / 2).toFixed(3);
      // 진행축(세로) 위치는 원본을 그대로 두어 가리키는 대상이 바뀌지 않게 함
    } else {
      const target = near.reduce((s2, b) => s2 + b.y + b.h / 2, 0) / near.length;
      if (Math.abs(target - cy) < 0.25) a.y = +(target - a.h / 2).toFixed(3);
      // 진행축(가로) 위치는 원본 유지
    }
  });
  const panelFrames = []; // 원본 크기로 따로 그릴 패널 테두리
  const chevronStrip = [];
  const bigIcons = [];
  const fillBox = new Set();
  const narrowTo = {};
  const shrinkTo = {};
  const grow = {}; // 텍스트 상자 → 새 높이 (아래 아이콘 띠 자리 흡수)
  if (tinyCount >= 4) {
    const strip = ownSlide.atoms.filter((o) => o.kind === "image" && o.w < 0.45 && o.h < 0.45);
    const bottom = Math.max(...strip.map((o) => o.y + o.h)), top = Math.min(...strip.map((o) => o.y)), sx0 = Math.min(...strip.map((o) => o.x)), sx1 = Math.max(...strip.map((o) => o.x + o.w));
    const above = ownSlide.atoms.filter((o) => o.paras && o.y < top - 0.3 && o.y + o.h > top - 0.6 && o.x < sx1 && o.x + o.w > sx0).sort((p, q) => (q.y + q.h) - (p.y + p.h))[0];
    if (above) {
      if (above.y + above.h > top) shrinkTo[ownSlide.atoms.indexOf(above)] = top - above.y - 0.05; // 띠를 품은 텍스트 상자는 띠 위까지로 줄임
      // 위 텍스트의 괄호 라벨("(도구 연결) …")을 단계 셰브론으로 그려 띠 자리를 채움
      const labels = [];
      above.paras.forEach((p) => { const m = p.runs.map((r) => r.t).join("").match(/^\s*[\(（]([^)）]{2,12})[\)）]/); if (m) labels.push(m[1]); });
      delete shrinkTo[ownSlide.atoms.indexOf(above)];
      grow[ownSlide.atoms.indexOf(above)] = bottom - above.y + 0.05; // 텍스트 상자를 띠 자리까지 넓히고 글꼴을 키워 채움 (fill)
      fillBox.add(ownSlide.atoms.indexOf(above));
      // 같은 높이의 큰 아이콘(달력 등)이 상자 안에 있으면 텍스트 폭을 그 앞까지로 제한
      const bigIcon = ownSlide.atoms.find((o) => o.kind === "image" && o.w >= 0.45 && o.x > above.x + above.w * 0.5 && o.x < above.x + above.w && o.y < bottom && o.y + o.h > above.y);
      if (bigIcon) { // 패널 테두리는 원본 크기로 따로 그리고 글자 상자만 아이콘 앞까지 줄임
        if (above.fill || (above.line && above.line.color && above.line.color !== "none")) {
          panelFrames.push({ x: above.x, y: above.y, w: above.w, h: bottom - above.y + 0.05, fill: above.fill, line: above.line, preset: above.preset });
          above.fill = "none"; above.line = { color: "none" };
        }
        narrowTo[ownSlide.atoms.indexOf(above)] = bigIcon.x - above.x - 0.1;
        bigIcon.y = +((above.y + bottom + 0.05) / 2 - bigIcon.h / 2).toFixed(3);
      }
    }
    // 띠와 같은 높이의 작은 연결 도형(화살표, 라벨)도 생략
    ownSlide.atoms.forEach((o) => { if (o !== above && o.kind !== "image" && o.y >= top - 0.15 && o.y + o.h <= bottom + 0.15 && o.x >= sx0 - 0.3 && o.x + o.w <= sx1 + 1.5) skipShape.add(o); });
  }
  // 아이콘으로 대체될 이미지가 덮는 텍스트 상자는 아이콘 왼쪽까지로 폭을 줄여 겹침을 막음 (그리기 전에 적용)
  ownSlide.atoms.forEach((im, k) => {
    if (im.kind !== "image" || im.identity) return;
    const id = "img" + ownSlide.atoms.slice(0, k + 1).filter((o) => o.kind === "image").length;
    if (sl[id] || im.w >= T.PANEL.ICON_MAX || im.h >= T.PANEL.ICON_MAX) return;
    ownSlide.atoms.forEach((o) => {
      if (narrowTo[ownSlide.atoms.indexOf(o)] || fillBox.has(ownSlide.atoms.indexOf(o))) return; // 띠 흡수 규칙이 이미 조정한 상자는 제외
      if (!o.paras || o.kind === "table") return;
      const ox = Math.min(o.x + o.w, im.x + im.w) - Math.max(o.x, im.x);
      const oy = Math.min(o.y + o.h, im.y + im.h) - Math.max(o.y, im.y);
      if (ox <= 0.05 || oy <= 0.05 || o.x >= im.x - 0.2) return;
      // 패널 테두리는 원본 크기로 따로 그리고, 글자 상자만 아이콘 앞까지 줄여 겹침을 막음
      const nw = im.x - 0.1 - o.x;
      if (nw < o.w * 0.5) return;
      if (o.fill || (o.line && o.line.color && o.line.color !== "none")) {
        panelFrames.push({ x: o.x, y: o.y, w: o.w, h: o.h, fill: o.fill, line: o.line, preset: o.preset });
        o.fill = "none"; o.line = { color: "none" };
      }
      o.w = +nw.toFixed(3);
    });
  });
  // 글자 상자 안의 "시각자료" 자리 상자는 슬롯으로 채우지 않으면 생략하고 글자가 전체를 쓰게 함
  ownSlide.atoms.forEach((o) => {
    const t = ((o.paras || []).flatMap((p) => p.runs.map((r) => r.t)).join("") || "").trim();
    if (o.kind !== "shape" || !/^(시각자료|이미지|사진|도식|산출물 화면)$/.test(t)) return;
    if (sl["~" + t] || sl[t]) return; // 사용자가 내용을 지정하면 유지
    skipShape.add(o);
  });
  // 큰 삽화(이미지)가 글자 상자 안에 놓이면 글자 영역을 그 위까지로 줄임
  ownSlide.atoms.forEach((im) => {
    if (im.kind !== "image" || im.identity || im.w < T.PANEL.ICON_MAX) return;
    ownSlide.atoms.forEach((o, oi) => {
      if (!o.paras || o.kind === "table" || narrowTo[oi] || fillBox.has(oi) || shrinkTo[oi]) return;
      const ox = Math.min(o.x + o.w, im.x + im.w) - Math.max(o.x, im.x);
      const oy = Math.min(o.y + o.h, im.y + im.h) - Math.max(o.y, im.y);
      if (ox <= 0.1 || oy <= 0.1) return;
      if (im.y - o.y < 0.3) return; // 이미지가 상자 위쪽을 덮으면 폭 조정 규칙이 담당
      shrinkTo[oi] = im.y - o.y - 0.08; // 삽화 위까지만 글자를 배치
    });
  });
  let ik0 = 0;
  for (const raw of ownSlide.atoms) {
    if (raw.kind !== "image") continue;
    ik0 += 1;
    if (sl["img" + ik0] || raw.identity || raw.w <= 1.5 || raw.h <= 0.9) continue;
    const tbL = ownSlide.atoms.find((o) => o.kind === "table" && o.y < raw.y + raw.h && o.y + o.h > raw.y && o.x > raw.x + raw.w - 0.5 && !ownSlide.atoms.some((m) => m !== o && m !== raw && m.kind !== "line" && m.x > raw.x + raw.w - 0.1 && m.x < o.x && m.y < o.y + o.h && m.y + m.h > o.y));
    if (tbL) { // 표 왼쪽의 삽화 자리(인증서 등)는 생략하고 표를 왼쪽으로 넓힘
      widenLeft[ownSlide.atoms.indexOf(tbL)] = raw.x * sx; skipImage.add(raw); continue;
    }
    const tb = ownSlide.atoms.find((o) => o.kind === "table" && o.y < raw.y + raw.h && o.y + o.h > raw.y && o.x + o.w < raw.x + 0.5);
    if (tb) {
      // 표와 삽화 사이에 다른 요소가 있으면 그 요소 앞까지만 넓힘
      const between = ownSlide.atoms.filter((o) => o !== tb && o !== raw && o.kind !== "line" && o.x > tb.x + tb.w - 0.1 && o.x < raw.x && o.y < tb.y + tb.h + 0.6 && o.y + o.h > tb.y - 0.6);
      // 사이 요소(절차 목록 등)를 삽화의 우측 끝까지 밀고 표를 그 앞까지 넓혀 빈 면적을 없앰
      // 전폭 제목 텍스트는 제외하고 목록 상자만 이동 대상으로 삼음
      const movable = between.filter((o) => o.w < (raw.x + raw.w - tb.x - tb.w) * 0.6);
      // 목록 상자는 원본 폭을 유지하고 삽화 자리는 주제 아이콘과 캡션으로 채움
      if (movable.length) {
        const near = ownSlide.atoms.filter((o) => o.paras).map((o) => o.paras.map((p) => p.runs.map((r) => r.t).join("")).join(" ")).join(" ");
        bigIcons.push({ x: raw.x * sx, y: raw.y * sy, w: raw.w * sx, h: raw.h * sy, kind: iconKind(raw, [near]), caption: /파쇄/.test(near) ? "현장 파쇄 후 파쇄확인서 제출" : "" });
      }
      // 사이 요소를 표의 세로 범위에 맞춰 고르게 분배 (아래 빈 면적 제거)
      if (movable.length > 1) {
        const top0 = Math.min(...movable.map((o) => o.y)), bot0 = Math.max(...movable.map((o) => o.y + o.h));
        const span0 = bot0 - top0, span1 = tb.y + tb.h - top0;
        if (span1 > span0 + 0.2) movable.forEach((o) => { o.y = +(top0 + (o.y - top0) * (span1 - o.h) / Math.max(0.01, span0 - o.h)).toFixed(3); });
      }
      if (!movable.length) widen[ownSlide.atoms.indexOf(tb)] = (raw.x + raw.w) * sx; // 사이 요소가 없으면 표를 넓힘
      if (movable.length > 1) { // 목록 상자를 표의 세로 범위에 고르게 분배
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
  // 열 생략으로 생긴 빈 면적 흡수: 같은 행 띠(y, h 동일)에서 남은 상자를 원래 폭 전체에 재배분
  if (skippedBoxes.length) {
    const band = (a) => `${Math.round(a.y * 20)}|${Math.round(a.h * 20)}|${Math.round(a.w * 20)}`; // 같은 y, h, w 의 반복 열
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
    // 재배분된 상자 안의 연결선과 작은 도형도 같은 비율로 이동
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
      if (atom.identity && !sl[id]) continue; // 로고: 미제공 시 생략
      if (!sl[id] && raw.w < 0.45 && raw.h < 0.45 && tinyCount >= 4) continue; // 도구 아이콘 띠(0.45인치 미만이 4개 이상)는 생략 (위 텍스트 상자가 그 영역까지 확장됨)
      if (skipImage.has(raw)) continue; // 표 오른쪽의 삽화 자리 (표를 넓혀 흡수)
      if (!sl[id] && raw.w < T.PANEL.ICON_MAX && raw.h < T.PANEL.ICON_MAX) { // 판정은 원본 좌표 기준 (판형 축소 시에도 같은 결과)
        // 아이콘이 덮는 텍스트 상자는 아이콘 왼쪽까지로 폭을 줄여 겹침을 막음
        ownSlide.atoms.forEach((o) => {
          if (!o.paras || o.kind === "table") return;
          const overlapX = Math.min(o.x + o.w, raw.x + raw.w) - Math.max(o.x, raw.x);
          const overlapY = Math.min(o.y + o.h, raw.y + raw.h) - Math.max(o.y, raw.y);
          if (overlapX > 0.05 && overlapY > 0.05 && o.x < raw.x - 0.2) o.w = +(raw.x - 0.08 - o.x).toFixed(3);
        }); // 아이콘 이미지는 주변 라벨 키워드로 종류를 정해 도형 조합으로 대체
        const near = ownSlide.atoms.filter((o) => o.paras && Math.abs(o.x + o.w / 2 - raw.x - raw.w / 2) < 3.2 && Math.abs(o.y + o.h / 2 - raw.y - raw.h / 2) < 1.0).map((o) => o.paras.map((p) => p.runs.map((r) => r.t).join("")).join(" "));
        iconGlyph(pres, slide, atom, iconKind(raw, near));
        continue;
      }
      if (!sl[id] && raw.h < 0.7 && raw.w > 1.0) { // 로고 1개는 [기관명], 프로세스 예시 띠는 ○○○ → ○○○ 형식
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
        // 렌더러가 holeSize 를 무시하는 경우에도 링 두께를 유지하도록 중앙에 흰 원을 덮음
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
      // 표 슬롯이 일부 행만 채워졌으면 빈 행을 제거하고 표 높이를 줄임 (투입인력표 등)
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
      const hit = (px, py) => skippedBoxes.find((b) => px >= b.x - 0.08 && px <= b.x + b.w + 0.08 && py >= b.y - 0.08 && py <= b.y + b.h + 0.9); // 생략 상자와 그 아래 연결 구간
      const p0 = [raw.flipH ? raw.x + raw.w : raw.x, raw.flipV ? raw.y + raw.h : raw.y];
      const p1 = [raw.flipH ? raw.x : raw.x + raw.w, raw.flipV ? raw.y : raw.y + raw.h];
      const b0 = hit(p0[0], p0[1]), b1 = hit(p1[0], p1[1]);
      if (b0 || b1) {
        // 생략된 상자에서 나가는 연결선은 같은 열의 마지막 남은 상자로 시작점을 옮김 (모듈 간 연결 유지)
        const bx = b0 || b1;
        const survivors = ownSlide.atoms.filter((o) => o.paras && !skippedBoxes.includes(o) && o.y < bx.y && Math.min(o.x + o.w, bx.x + bx.w) - Math.max(o.x, bx.x) > bx.w * 0.5 && o.w < bx.w * 1.5);
        if (!survivors.length || (b0 && b1)) continue;
        if (raw.w < 0.15 && raw.h < 0.5) continue; // 생략 상자로 내려가던 짧은 세로 화살표는 제거
        const last = survivors.sort((p, q) => (q.y + q.h) - (p.y + p.h))[0];
        const other = b0 ? p1 : p0;
        // 다른 끝점이 오른쪽(다음 모듈)에 있으면 마지막 상자의 우측 중앙에서 출발, 아니면 하단 중앙에서 출발
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
        atom.va = "top"; // 줄인 상자는 위쪽 정렬로 두어 넘침이 위로 삐져나가지 않게 함
      }
      if (narrowTo[ownSlide.atoms.indexOf(raw)]) atom.w = +(narrowTo[ownSlide.atoms.indexOf(raw)] * sx).toFixed(3);
      let ov = {};
      if (fillBox.has(ownSlide.atoms.indexOf(raw))) ov.fillText = true;
      // 도넛 차트 안 중앙 텍스트는 링과 겹치지 않도록 85% 로 축소
      const donut = raw.paras && ownSlide.atoms.find((c) => c.kind === "chart" && c.chart.type === "doughnut" && raw.x >= c.x && raw.x + raw.w <= c.x + c.w && raw.y >= c.y && raw.y + raw.h <= c.y + c.h);
      if (donut) { // 도넛 안 텍스트는 구멍 영역을 세로로 나눠 순서대로 배치 (겹침 방지)
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
        if (v === "") continue; // 빈 문자열 치환은 상자 자체를 생략 (항목 수가 원본보다 적을 때)
        if (v != null) ov.paras = substitute(atom.paras, v);
        else if (scrub(cur, company) !== cur) ov.paras = substitute(atom.paras, scrub(cur, company));
      }
      // 원문 그대로면 서체 폭 차이만 흡수하면 되므로 하한을 낮추고, 치환한 텍스트는 본문 하한을 지켜 글꼴이 따로 놀지 않게 함
      ov.minPt = ov.paras ? T.SIZE.BODY_MIN : T.SIZE.OWN_MIN;
      // 치환 텍스트가 원문보다 줄 수가 늘면 위쪽 정렬로 두어 윗 요소를 덮지 않게 함
      if (ov.paras && raw.paras) {
        // 상자 위에 놓인 아이콘만큼 글자 영역이 좁아지는 점을 반영
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
        // 줄 수가 늘었거나 상자를 70% 이상 채우면 위쪽 정렬 (렌더러 줄바꿈 차이로 위로 넘치는 것을 막음)
        // 여유가 남으면 문단 간격을 넓혀 상자를 고르게 채움 (최대 10pt)
        if (ov.paras.length > 1 && need < raw.h * 0.8) {
          const slack = (raw.h - 0.12 - need) / (ov.paras.length - 1) * 72;
          const gap = Math.max(2.5, Math.min(10, slack * 0.8));
          ov.paras = ov.paras.map((p, i) => (i === 0 ? p : { ...p, spcBef: +gap.toFixed(1) }));
        }
        // 상자를 넘길 것으로 보이면 문단 간격부터 줄여 글꼴은 유지
        if (need > raw.h - 0.08) {
          // 문단 간격과 줄 간격만 축소 (글꼴은 유지)
          ov.paras = ov.paras.map((p, i) => ({ ...p, spcBef: i === 0 ? p.spcBef : 2, lnSpc: Math.min(p.lnSpc || 1.25, 1.05) }));
          // 간격 축소로도 넘치면 글꼴을 줄이지 않고 lint 경고로 문구 축약을 유도
        }
      }
      if (atom.rot && atom.paras && /Illustrative|Sample|시안/i.test(atom.paras.map((p) => p.runs.map((r) => r.t).join("")).join(""))) {
        // 회전 태그: 표 위에 놓이면 렌더러가 표를 위에 그리므로 표 밖 좌상단으로 옮기고 흰 채움
        const tb = ownSlide.atoms.find((o) => o.kind === "table" && atom.x < o.x + o.w && atom.x + atom.w > o.x && atom.y < o.y + o.h && atom.y + atom.h > o.y);
        const a2 = { ...atom, fill: "FFFFFF", rot: 345 };
        if (tb) { a2.x = tb.x * sx + 0.05; a2.y = tb.y * sy - atom.h - 0.02; }
        shape(pres, slide, a2, ov);
        continue;
      }
      if (ov.paras || atom.paras) {
        const paras = ov.paras || atom.paras;
        ov.scale = ratioBySize[sizeKey(atom, paras)]; // 형제 상자는 같은 축소율 (긴 슬롯 텍스트는 lint 가 경고)
      }
      // 한 줄짜리 상자가 같은 행에 나란히 있으면 글꼴이 달라도 기준선이 맞도록 세로 가운데로 둠
      if (!ov.va && raw.paras && raw.paras.length === 1) {
        const mate = ownSlide.atoms.some((b) => b !== raw && b.paras && b.paras.length === 1
          && Math.abs(b.y - raw.y) < 0.06 && Math.abs(b.h - raw.h) < 0.06 && Math.abs(b.x - raw.x) > 0.1);
        if (mate) ov.va = "middle";
      }
      shape(pres, slide, atom, ov); // 원본 z-order 유지 (도형 뒤로 밀리면 흰 상자가 기호와 그림을 가림)
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
// 회사명 자리 토큰 치환. meta.company 값을 __COMPANY__ 자리에 넣는다
// 그 외 텍스트는 그대로 두며 텍스트 치환 규칙은 추출 단계(own_extract.py)에서만 적용
function scrub(textValue, company) {
  return String(textValue).replace(/__COMPANY__/g, company || LB.label("common", "company"));
}
/** 기존 문단 서식을 유지하며 텍스트만 치환. 줄바꿈은 문단 분리. 문단 수가 부족하면 마지막 문단 서식 반복 */
function substitute(paras, value) {
  const lines = String(value).split("\n");
  const base = paras && paras.length ? paras : [{ runs: [{ t: "", sz: T.SIZE.body }] }];
  return lines.map((ln, i) => {
    const src = base[Math.min(i, base.length - 1)];
    const r0 = src.runs.find((r) => !r.br) || { sz: T.SIZE.body };
    // 원본의 ※ 문단은 예시 주석 자리이므로 작성자의 선택을 따름
    const srcText = src.runs.map((r) => r.t).join("").trim();
    if (/^※/.test(srcText) && ln.trim() && !/^\s*(※|\*|출처|자료|[Ss]ources?\s*[:：]|[Nn]otes?\s*[:：])/.test(ln) && !LB.isExtraNote(ln)) {
      // 주석이 아닌 문구를 넣으면 바로 위 불릿 문단의 서식으로 맞춰 일반 항목으로 표기
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
