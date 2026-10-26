#!/usr/bin/env node
"use strict";
// build.js
// storyboard.json 을 결정론적으로 pptx 로 조판하는 유일한 생성 경로.
// 사용: node build.js <storyboard.json> <out.pptx> [--layout 16:9|A4|10.83|4:3] [--digest] [--marker square|bar|triangle] [--theme navy|mono]
// --digest : 슬라이드별 headline 과 template 만 남긴 요약본(빠른 구조 검토용)
// 슬라이드의 byLayout 은 지정 판형으로 빌드할 때만 해당 경로의 값을 교체 (판형 전용 문구)
// 템플릿과 블록의 고정 라벨은 슬라이드 슬롯, meta.labels, assets/labels.json 순으로 해석 (labels.js)
// 커스텀 슬라이드(own:N)는 meta.ownDeck 경로(storyboard 기준 상대 경로 허용) 또는 환경변수 IEUM_DECK_OWN 의 own-deck.json 을 재생

const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");
const T = require("./tokens.js");
const A = require("./atoms.js");
const TEMPLATES = require("./templates.js");
const LB = require("./labels.js");

const OWN_ENV = "IEUM_DECK_OWN";
// 줄바꿈 단위(meta.lineBreak). word 는 단어 단위(기본), char 는 글자 단위. finalize.py 가 빌드 기록을 읽어 모든 문단 속성에 기록
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

/** 커스텀 슬라이드 경로. 없으면 null (own:N 을 쓰지 않는 덱은 커스텀 슬라이드 없이 빌드) */
function ownPath(meta, storyPath) {
  const p = meta.ownDeck || process.env[OWN_ENV];
  if (!p) return null;
  return path.isAbsolute(p) ? p : path.resolve(path.dirname(storyPath), p);
}
function loadOwn(p) {
  if (!p) return null;
  if (!fs.existsSync(p)) throw new Error(`커스텀 슬라이드 ${p} 없음. own_extract.py 로 생성`);
  const d = JSON.parse(fs.readFileSync(p, "utf8"));
  const byN = {};
  d.slides.forEach((s) => (byN[s.n] = s));
  byN.__colorMap = d.colorMap || {};
  return byN;
}

/** 슬라이드 1장 조판. 반환: 경고 목록 */
function buildSlide(pres, sb, meta, own, S, index, warnings) {
  const slide = pres.addSlide();
  const tpl = sb.template || sb.type || "free";
  const ctx = { pres, S, T, A, own, meta, sb, index, warn: (m) => warnings.push(`[${sb.id || index}] ${m}`) };
  // 절 번호는 "1." 형태로 정규화 (01, 1 처럼 마침표가 없으면 붙이고 앞의 0 은 제거)
  const secNo = sb.secNo == null ? sb.secNo : String(sb.secNo).trim().replace(/^0+(\d)/, "$1").replace(/^([\dIVXivx①-⑮]+)$/, "$1.");
  const band = { secNo, secTitle: sb.section, tracker: sb.tracker || sb.chapter, headline: sb.headline, marker: sb.marker, markerNote: sb.markerNote };
  // 커스텀 슬라이드 재생: template "own:N"
  const m = /^own:(\d+)$/.exec(tpl);
  if (m) {
    if (!own) throw new Error(`${tpl} 사용: 커스텀 슬라이드 미등록 (meta.ownDeck 또는 ${OWN_ENV} 로 own-deck.json 지정)`);
    const s = own[+m[1]];
    if (!s) throw new Error(`own:${m[1]} 없음`);
    const b0 = { ...s.band, ...stripUndefined(band) };
    // 마커 텍스트가 없으면 마커 밴드를 그리지 않음 (빈 정사각형만 남는 결함 방지)
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
  if (!fn) throw new Error(`알 수 없는 템플릿 ${tpl} (슬라이드 ${sb.id || index})`);
  const spec = TEMPLATES.SPEC[tpl] || {};
  const mode0 = sb.bandMode || spec.band || "full";
  const mode = sb.bandMode || (String(band.marker || "").trim() ? mode0 : bandNoMarker(mode0));
  if (mode !== "blank") A.bodyBand(pres, slide, S, band, mode, { accentHeadline: sb.accent });
  fn(ctx, slide, sb);
  if (mode !== "blank" || spec.pageNo) A.pageNo(slide, S, index + 1);
}
/** 마커 텍스트가 없을 때 마커 밴드를 건너뛰는 모드로 낮춤 */
function bandNoMarker(mode) {
  return mode === "full" ? "noMarker" : mode;
}
/** 판형 전용 문구 적용. sb.byLayout = {"4:3": {"slots.regions.1.block.items": [...]}, "A4,10.83": {...}}
 *  키는 판형 이름(쉼표로 여러 판형), 값은 점 경로(배열은 0부터 번호)와 교체 값. 빌드 판형과 일치하는 키만 적용 */
function applyLayoutPatch(sb, layoutKey) {
  if (!sb.byLayout) return sb;
  const out = JSON.parse(JSON.stringify(sb));
  delete out.byLayout;
  Object.entries(sb.byLayout).forEach(([keys, patch]) => {
    const lays = keys.split(",").map((k) => k.trim());
    lays.forEach((k) => { if (!T.LAYOUTS[k]) throw new Error(`슬라이드 ${sb.id} byLayout 판형 ${k} 미정의. 선택: ${Object.keys(T.LAYOUTS).join(", ")}`); });
    // 경로는 판형과 관계없이 모두 검사하여 다른 판형용 오기도 드러냄
    Object.keys(patch).forEach((p) => pathParent(sb, p));
    if (lays.includes(layoutKey)) Object.entries(patch).forEach(([p, v]) => { const [parent, last] = pathParent(out, p); parent[last] = v; });
  });
  return out;
}
/** 점 경로의 부모 객체와 마지막 키. 중간 경로가 없으면 오류 */
function pathParent(obj, p) {
  const segs = p.split(".");
  let cur = obj;
  for (const s of segs.slice(0, -1)) {
    if (cur == null || typeof cur !== "object" || !(s in cur)) throw new Error(`슬라이드 ${obj.id} byLayout 경로 ${p} 없음`);
    cur = cur[s];
  }
  const last = segs[segs.length - 1];
  // 배열은 있는 칸만 교체 (객체는 새 키 추가 허용)
  if (cur == null || typeof cur !== "object" || (Array.isArray(cur) && !(last in cur))) throw new Error(`슬라이드 ${obj.id} byLayout 경로 ${p} 없음`);
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
  LB.useDeck(meta); // 덱 단위 라벨(meta.labels) 등록
  const layoutKey = argv.layout || meta.layout || "16:9";
  if (!T.LAYOUTS[layoutKey]) throw new Error(`판형 ${layoutKey} 미정의. 선택: ${Object.keys(T.LAYOUTS).join(", ")}`);
  const theme = argv.theme || meta.theme || "navy";
  if (!T.THEMES[theme] && !meta.themeColors) throw new Error(`색 테마 ${theme} 미정의. 선택: ${Object.keys(T.THEMES).join(", ")} 또는 meta.themeColors 지정`);
  const lineBreak = meta.lineBreak || LINE_BREAKS[0];
  if (!LINE_BREAKS.includes(lineBreak)) throw new Error(`줄바꿈 단위 ${lineBreak} 미정의. 선택: ${LINE_BREAKS.join(", ")}`);
  A.setImageBase(path.dirname(path.resolve(inPath)));
  const ownFile = ownPath(meta, inPath);
  const own = loadOwn(ownFile);
  if (own) T.setOwnColorMap(own.__colorMap);
  const themeResult = T.applyTheme(theme, meta.themeColors);
  // 기준 색이 밝아 흰 글자 대비가 모자라면 명도를 낮춰 적용하므로 조정 값을 사용자 보고용으로 출력
  if (themeResult.adjusted) console.log(`THEME 기준 색 명도 조정 #${themeResult.adjusted.from} → #${themeResult.adjusted.to} (라벨 셀 흰 글자 대비 4.5:1 확보)`);
  if (argv.marker) T.MARKER.shape = argv.marker;
  else if (meta.marker) T.MARKER.shape = meta.marker;
  const S = T.scaled(layoutKey);
  const pres = new PptxGenJS();
  pres.defineLayout({ name: S.layout.name, width: S.layout.W, height: S.layout.H });
  pres.layout = S.layout.name; // 슬라이드 추가 전에 설정 (pptxgenjs 규칙)
  pres.title = meta.title || "";
  pres.author = meta.author || "";
  // 문서 속성에 라이브러리 기본값(회사, 주제)이 남지 않도록 지정. pptxgenjs 는 company 를 이스케이프 없이 기록하므로 직접 이스케이프
  pres.company = String(meta.company || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  pres.subject = "";
  const warnings = [];
  let slides = (story.slides || []).map((sb) => applyLayoutPatch(sb, layoutKey));
  if (argv.digest) slides = slides.map((s) => ({ id: s.id, template: "digest", headline: s.headline, section: s.section, chapter: s.chapter, secNo: s.secNo, marker: s.marker, digestOf: s.template || s.type, digest: s.digest }));
  slides.forEach((sb, i) => buildSlide(pres, sb, meta, own, S, i, warnings));
  await pres.writeFile({ fileName: outPath });
  T.writeLimits(path.join(__dirname));
  // 커스텀 슬라이드 재생 슬라이드는 원본 글꼴과 폭 흡수 축소를 따르므로 본문 하한 검사에서 제외 (check_layout 이 읽음)
  const ownSlides = slides.map((s, i) => (String(s.template || "").startsWith("own:") ? i + 1 : 0)).filter(Boolean);
  // palette 는 사용자 지정 테마 색을 표 셀 허용 색으로 인식시키기 위한 기록 (check_layout, finalize 가 읽음)
  // language 는 PPTX 에 기록할 언어 태그 (meta.labels.language, finalize 가 읽음)
  // lineBreak 는 문단 속성에 기록할 줄바꿈 단위 (meta.lineBreak, finalize 와 check_layout 이 읽음)
  const themeLabel = meta.themeColors && meta.themeColors.base ? `custom #${T.COLOR.navy}` : theme;
  const report = { out: outPath, slides: slides.length, layout: layoutKey, theme: themeLabel, palette: T.themePalette(), language: LB.language(), lineBreak, themeAdjusted: themeResult.adjusted, ownDeck: ownFile, ownSlides, warnings };
  fs.writeFileSync(outPath.replace(/\.pptx$/, "") + ".build.json", JSON.stringify(report, null, 1));
  console.log(`built ${outPath} slides=${slides.length} layout=${layoutKey} theme=${themeLabel} warnings=${warnings.length}`);
  warnings.forEach((w) => console.log("WARN " + w));
}

// 입력 오류는 메시지만 출력하고 스택은 IEUM_DECK_DEBUG=1 일 때만 출력 (디버깅용)
main().catch((e) => { console.error(process.env.IEUM_DECK_DEBUG ? e.stack || e : `ERROR ${e.message || e}`); process.exit(1); });
