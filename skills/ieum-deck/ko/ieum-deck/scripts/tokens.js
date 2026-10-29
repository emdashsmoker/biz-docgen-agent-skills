"use strict";
// tokens.js
// 디자인 시스템의 수치를 정의하는 유일한 파일. 좌표의 기준 판형은 16:9(13.333×7.5인치)이며
// 다른 판형은 scaled(layout) 가 폭과 높이 비율로 환산한다. 글꼴 크기는 환산하지 않는다.

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------- 판형
// 착수 질의 판형 항목. 기본 16:9, 인쇄 제출용 A4 가로, 구형 화면용 10.83 과 4:3
const LAYOUTS = {
  "16:9": { name: "LAYOUT_16x9_WIDE", W: 13.333, H: 7.5 },
  "A4": { name: "LAYOUT_A4_LAND", W: 11.69, H: 8.27 },
  "10.83": { name: "LAYOUT_10_83", W: 10.83, H: 7.5 },
  "4:3": { name: "LAYOUT_4x3", W: 10.0, H: 7.5 },
};
const BASE_W = 13.333;
const BASE_H = 7.5;

// ---------------------------------------------------------------- 밴드 좌표 (16:9 기준, 인치)
const BAND = {
  MARGIN_X: 0.42, // 헤드라인과 구분선의 좌측 시작. 우측 종료는 W - 0.42
  SECNO: { x: 0.39, y: 0.29, w: 0.49, h: 0.44 }, // 절 번호 32pt
  SECTITLE: { x: 0.93, y: 0.43, w: 6.49, h: 0.31 }, // 절 제목 20pt
  TRACKER: { x: 7.55, y: 0.44, w: 5.36, h: 0.31 }, // 장 추적기 18pt 우측 정렬
  RULE_TOP_Y: 1.05, // 헤드라인 밴드 상단 선
  HEADLINE: { x: 0.42, y: 1.05, w: 12.5, h: 0.75 }, // 밴드 두 선 사이의 헤드라인 18pt Bold 가운데
  // 상자 세로 중앙 정렬은 행 상자 기준이므로 서체에 따라 글자가 위아래로 치우칠 수 있음
  // 나눔고딕 200dpi 실측에서 글자가 아래로 약 2.3pt 치우쳐 절반인 0.016in 을 위로 보정
  HEADLINE_NUDGE: 0.016,
  RULE_Y: 1.8, // 헤드라인 밴드 하단 선. 두께 0.75pt
  RULE_PT: 0.75,
  MARKER_SHAPE: { x: 0.54, y: 2.05, w: 0.31, h: 0.26 }, // 마커 기호가 놓이는 자리. 도형 종류는 MARKER.shape
  MARKER_TEXT: { x: 0.85, y: 2.02, w: 11.99, h: 0.26 }, // 마커 제목 18pt Bold
  CONTENT_Y: 2.32, // 마커 밴드 하단 (본문 영역의 기준선)
  // 본문 묶음은 마커 제목 아래와 쪽번호 위의 여백이 같아지도록 배치 (원본 표준장표 실측: 위 0.17, 아래 0.2 인치)
  BODY_PAD: 0.1, // 기준선에서 본문 묶음 상단까지 간격
  CONTENT_BOTTOM: 6.92, // 본문 하단 (쪽번호 행 위 여백 0.16 인치)
  CONTENT_Y_NO_MARKER: 2.07, // 마커 밴드가 없는 레이아웃(3_빈 화면)의 본문 상단
  PAGENO: { x: 10.33, y: 7.1, w: 3.0, h: 0.4 }, // 쪽번호 11pt 우측 정렬
  NOTE_Y: 6.78, // 각주와 출처 행 기준선
  BODY_X: 0.98, // 본문 묶음의 좌측 시작 (마커 기호 폭만큼 들여 헤드라인 밴드와 구분)
  BODY_RIGHT: 12.36, // 본문 묶음의 우측 종료 (좌우 여백 대칭)
  EDGE_MIN: 0.42, // 슬라이드 가장자리 최소 여백 (check_layout 검사값)
};

// 마커 도형. 기본은 정사각형이며 meta.marker 나 --marker 로 막대, 삼각형 선택
const MARKER = {
  shape: "square", // square | bar | triangle
  square: { w: 0.16, h: 0.16 },
  bar: { w: 0.08, h: 0.22 },
  triangle: { w: 0.18, h: 0.18 },
};

// ---------------------------------------------------------------- 도형 규격 (인치)
const PANEL = {
  GAP: 0.2, // 도형 사이 간격 하한
  INSET: 0.07, // 도형 안 여백 (0.05-0.09)
  INSET_MIN: 0.05,
  INSET_MAX: 0.09,
  HEAD_H: 0.32, // 12pt 제목 바 높이 (composite 상자 제목, 흐름 상자 제목)
  TITLE_H: 0.42, // 14pt 패널 제목 바 높이 (파라메트릭 패널, 추진전략 기둥, 역량 타일, 인력 카드). 글줄 위아래 여백 0.09인치
  SUBHEAD_H: 0.5, // 채움 없는 영역 제목(글자와 밑줄)이 차지하는 높이
  ROW_H_MIN: 0.3, // 표 행 최소 높이
  ROW_H_MAX: 0.8, // 표가 본문을 채울 때 행 높이 상한 (하베이 볼이나 여러 줄 셀이 있는 표)
  FILL_EXPAND: 1.6, // 글 상자 높이 상한 배수 (내용 필요 높이 대비). 넘는 높이는 상자 바깥 여백으로 돌림
  LABEL_MG_X: 0.045, // 네이비 라벨 셀의 좌우 여백 (각각)
  LABEL_MG_Y: 0.02, // 네이비 라벨 셀의 위아래 여백 (각각)
  LABEL_GAP: 0.14, // 행 라벨 상자와 내용 상자 사이 간격 (내용 위치는 두고 라벨 상자 폭을 줄여 확보)
  ROW_H_TEXT: 0.5, // 한 줄 글자만 있는 표의 행 높이 상한 (셀 안이 비어 보이지 않는 높이. 원본 표준장표 본문 행 중앙값 0.44)
  TABLE_HEAD_H: 0.4, // 본문 행이 늘어날 때 머리 행 높이 (원본 표준장표 실측 0.33-0.39 인치)
  LINE_PT: 0.5, // 상자 테두리
  LINE_PT_STRONG: 0.75, // 패널 테두리
  CHEVRON_OVERLAP: 0.06,
  CHART_MIN_H: 1.6,
  CHART_MIN_W: 3.0,
  PIE_MIN: 2.4,
  ROUND_RADIUS: 0.05, // 둥근 사각형 반경 상한
  SLACK_WARN: 0.45, // 상자 안 빈 공간 비율 경고 기준
  FILL_RATIO_MIN: 0.78,
  SMALL_BOX_W: 0.6,
  ICON_MAX: 0.95, // 이 크기 미만의 이미지는 아이콘으로 보고 기호로 대체
  CELL_MG: [0.05, 0.03, 0.05, 0.03], // 표 셀 기본 여백 (좌, 상, 우, 하) 인치 // 이 폭 미만 상자는 내부 여백 0, 줄바꿈 없음 // 묶음이 본문 밴드에서 차지해야 하는 최소 비율
};

// ---------------------------------------------------------------- 색상 (pptxgenjs 는 # 없는 6자리)
// 흑백 기조. 네이비는 라벨 셀, 셰브론, 결론 밴드, 마커, 수치 강조에만 사용
const COLOR = {
  navy: "1F3864", // 라벨 채움, 패널 제목 문자, 강조
  navyDeep: "17294A", // 질문 배너와 결론 밴드
  navyPastel: "6B8EC2", // 차트 데이터 기본색
  navyPastel2: "A9B9D9",
  navyRamp: ["1F3864", "6B8EC2", "A9B9D9", "D5DDEC"],
  textDark: "333333",
  textMuted: "8B93A7",
  textGray: "595959",
  tintHead: "E9EBF0", // 머리글 틴트
  tintBg: "F7F8FA", // 배경 틴트
  tintLight: "F2F2F2",
  tintNavy: "C9CDD8",
  border: "A6A6A6",
  borderLight: "BFBFBF",
  accent: "C0392B", // 슬라이드당 1곳
  white: "FFFFFF",
  black: "000000",
};
// 색 테마. navy(기본)와 mono(무채색) 2종을 제공하며 사용자가 다른 색을 지정하면 applyTheme 로 덮어씀
// 틴트(tintHead, tintBg)와 보조 회색(textMuted)도 테마 키에 포함하여 테마를 다시 적용할 때 이전 테마 값이 남지 않게 함
// mono 의 틴트와 보조 회색은 navy 값과 같은 휘도의 무채색 (navy 값은 청회색이라 무채색 테마에서 색이 섞여 보임)
const THEMES = {
  navy: { navy: "1F3864", navyDeep: "17294A", navyPastel: "6B8EC2", navyPastel2: "A9B9D9", navyRamp: ["1F3864", "6B8EC2", "A9B9D9", "D5DDEC"], tintNavy: "C9CDD8", tintHead: "E9EBF0", tintBg: "F7F8FA", textMuted: "8B93A7" },
  mono: { navy: "2B2B2B", navyDeep: "111111", navyPastel: "7F7F7F", navyPastel2: "BFBFBF", navyRamp: ["2B2B2B", "7F7F7F", "BFBFBF", "E0E0E0"], tintNavy: "D0D0D0", tintHead: "EBEBEB", tintBg: "F8F8F8", textMuted: "939393" },
};

// 기준 색 1개로 테마 키 전체를 계산하는 규칙. 색상(hue)은 기준 색을 유지
// 채도는 기준 색 채도에 곱하는 비율, 명도는 고정값. 두 값은 기본 navy 팔레트(1F3864 계열)의 실측 관계
const THEME_DERIVE = {
  navyPastel: { s: 0.79, l: 0.59 },
  navyPastel2: { s: 0.73, l: 0.757 },
  ramp4: { s: 0.72, l: 0.88 },
  tintNavy: { s: 0.31, l: 0.818 },
  tintHead: { s: 0.36, l: 0.927 },
  tintBg: { s: 0.44, l: 0.975 },
};
const THEME_DEEP_L_RATIO = 0.74; // navyDeep 명도 = 기준 색 명도 × 비율 (17294A 와 1F3864 의 명도 비)
const LABEL_CONTRAST_MIN = 4.5; // 라벨 셀과 결론 밴드의 흰 글자 대비 하한 (WCAG AA 본문 기준)
// navyPastel 은 피라미드 2층과 깔때기 2단계에서 흰 굵은 글자를 얹으므로 대비 하한 적용 (기본 6B8EC2 의 대비는 3.35)
// 노랑, 주황처럼 휘도가 높은 색상은 같은 명도에서도 흰 글자가 묻히므로 명도를 낮춰 보정
const PASTEL_CONTRAST_MIN = 3.0;
const CONTRAST_STEP_L = 0.01; // 대비 하한 미달 시 명도를 낮추는 단위
const DARK_TEXT_CONTRAST_MIN = 3.0; // 본문 글자색을 얹는 도식 채움(피라미드 3층, 깔때기 옅은 띠, 시장 규모 바깥 원)의 대비 하한
const TINT_TEXT_CONTRAST_MIN = 4.5; // 본문 글자를 얹는 틴트 배경의 대비 하한 (WCAG AA 본문 기준)
// 보조 회색은 AS-IS 머리 칸 채움(흰 글자)과 흰 바탕 위 출처, 각주, 축 양끝 표기 글자에 쓰임 (기본 8B93A7 의 흰색 대비 3.08)
const MUTED_CONTRAST_MIN = 3.0;
// 테마 색 키별 글자 대비 규칙. on 은 그 색 위에 조판하는 글자색 (white 는 흰색, textDark 는 본문 글자색)
// 기준 색 계산값은 규칙을 충족하도록 만들어지므로 lint 가 직접 지정한 색 키만 limits.json 사본으로 검사 (미달은 WARN, 유지 사유를 적으면 통과)
const THEME_TEXT_RULES = [
  { key: "navy", on: "white", min: LABEL_CONTRAST_MIN },
  { key: "navyDeep", on: "white", min: LABEL_CONTRAST_MIN },
  { key: "navyPastel", on: "white", min: PASTEL_CONTRAST_MIN },
  { key: "navyRamp.0", on: "white", min: LABEL_CONTRAST_MIN },
  { key: "navyRamp.1", on: "white", min: PASTEL_CONTRAST_MIN },
  { key: "navyPastel2", on: "textDark", min: DARK_TEXT_CONTRAST_MIN },
  { key: "navyRamp.2", on: "textDark", min: DARK_TEXT_CONTRAST_MIN },
  { key: "navyRamp.3", on: "textDark", min: DARK_TEXT_CONTRAST_MIN },
  { key: "tintNavy", on: "textDark", min: TINT_TEXT_CONTRAST_MIN },
  { key: "tintHead", on: "textDark", min: TINT_TEXT_CONTRAST_MIN },
  { key: "tintBg", on: "textDark", min: TINT_TEXT_CONTRAST_MIN },
  { key: "textMuted", on: "white", min: MUTED_CONTRAST_MIN },
];
const TEXT_DARK_DEFAULT = COLOR.textDark; // 모듈 적재 시점의 본문 글자색 (limits.json 에 테마와 무관한 값으로 기록)
// 규칙 미달 경고에 붙이는 조치 안내
const THEME_TEXT_HINT = "밝은 색은 본문 글자를 얹는 키(navyPastel2, navyRamp 3-4번째, 틴트)에, 짙은 색은 흰 글자를 얹는 키(navy, navyDeep, navyPastel, textMuted)에 지정";
const HEX6 = /^[0-9A-F]{6}$/;

function hexToHsl(hex) {
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn;
  if (d === 0) return { h: 0, s: 0, l };
  const s = d / (1 - Math.abs(2 * l - 1));
  const h = mx === r ? ((g - b) / d + 6) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return { h: h * 60, s, l };
}

function hslToHex({ h, s, l }) {
  const c = (1 - Math.abs(2 * l - 1)) * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m = l - c / 2;
  const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x] : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x];
  return [r, g, b].map((v) => Math.round((v + m) * 255).toString(16).padStart(2, "0")).join("").toUpperCase();
}

/** WCAG 상대 휘도 */
function luminance(hex) {
  const lin = [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

/** 두 색의 명도 대비 (WCAG 기준, 1-21) */
function contrast(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

/** 흰 글자 대비 */
function contrastWithWhite(hex) {
  return contrast(hex, "FFFFFF");
}

/** 흰 글자 대비가 하한 이상이 될 때까지 명도를 낮춘 색 */
function darkenForWhite(hsl, min) {
  const c = { ...hsl };
  let hex = hslToHex(c);
  while (contrastWithWhite(hex) < min && c.l > 0) {
    c.l = Math.max(0, c.l - CONTRAST_STEP_L);
    hex = hslToHex(c);
  }
  return { hex, l: c.l };
}

/** 색상 코드 표기 정규화 (# 제거, 대문자). 6자리 색상 코드가 아니면 오류 */
function normHex(v, field) {
  const hex = String(v || "").replace("#", "").toUpperCase();
  if (!HEX6.test(hex)) throw new Error(`meta.themeColors.${field} 는 6자리 색상 코드 (예: 1B4332). 입력값: ${v}`);
  return hex;
}

/** 기준 색으로 테마 키 전체를 계산. 흰 글자 대비가 하한 미달이면 기준 색 명도를 낮추고 조정 전후 값을 반환 */
function deriveTheme(baseInput) {
  const base = normHex(baseInput, "base");
  const hsl = hexToHsl(base);
  const label = darkenForWhite(hsl, LABEL_CONTRAST_MIN);
  const navy = label.hex;
  hsl.l = label.l;
  const at = (k) => hslToHex({ h: hsl.h, s: Math.min(1, hsl.s * THEME_DERIVE[k].s), l: THEME_DERIVE[k].l });
  const pastel = darkenForWhite({ h: hsl.h, s: Math.min(1, hsl.s * THEME_DERIVE.navyPastel.s), l: THEME_DERIVE.navyPastel.l }, PASTEL_CONTRAST_MIN).hex;
  const colors = {
    navy,
    navyDeep: hslToHex({ ...hsl, l: hsl.l * THEME_DEEP_L_RATIO }),
    navyPastel: pastel,
    navyPastel2: at("navyPastel2"),
    navyRamp: [navy, pastel, at("navyPastel2"), at("ramp4")],
    tintNavy: at("tintNavy"),
    tintHead: at("tintHead"),
    tintBg: at("tintBg"),
  };
  return { colors, adjusted: navy === base ? null : { from: base, to: navy } };
}

/** 색 테마 적용. key 는 navy 또는 mono. custom 은 COLOR 키를 덮어쓰는 객체이며 base 가 있으면 deriveTheme 결과를 먼저 적용
 *  반환값의 adjusted 는 대비 보정으로 바뀐 기준 색 (보정이 없으면 null) */
function applyTheme(key, custom) {
  const t = THEMES[key] || THEMES.navy;
  Object.assign(COLOR, t);
  const { base, ...raw } = custom || {};
  const keys = Object.fromEntries(Object.entries(raw).map(([k, v]) => [k, Array.isArray(v) ? v.map((x) => normHex(x, k)) : normHex(v, k)]));
  let adjusted = null;
  let derived = null;
  if (base) {
    derived = deriveTheme(base);
    Object.assign(COLOR, derived.colors);
    adjusted = derived.adjusted;
  }
  Object.assign(COLOR, keys);
  // 계산 테마에서 navyPastel 등을 따로 지정하고 navyRamp 는 지정하지 않으면 차트 계열 색을 최종 값으로 다시 구성
  if (derived && !keys.navyRamp) COLOR.navyRamp = [COLOR.navy, COLOR.navyPastel, COLOR.navyPastel2, derived.colors.navyRamp[3]];
  Object.keys(COLOR_REMAP).forEach((k) => { delete COLOR_REMAP[k]; });
  Object.assign(COLOR_REMAP, buildRemap());
  return { color: COLOR, adjusted };
}

/** 표 셀 허용 색 검사에 더할 현재 테마 색 목록 (check_layout 과 finalize 가 빌드 기록에서 읽음) */
function themePalette() {
  const keys = ["navy", "navyDeep", "navyPastel", "navyPastel2", "tintNavy", "tintHead", "tintBg", "textMuted"];
  return [...new Set([...keys.map((k) => COLOR[k]), ...COLOR.navyRamp].map((c) => String(c).toUpperCase()))];
}

// 커스텀 슬라이드의 원본 색 → COLOR 키 대응 (own-deck.json 의 colorMap). 테마를 바꾸면 함께 바뀜
const OWN_COLOR_MAP = {};
function setOwnColorMap(m) {
  Object.keys(OWN_COLOR_MAP).forEach((k) => { delete OWN_COLOR_MAP[k]; });
  Object.entries(m || {}).forEach(([hex, key]) => { OWN_COLOR_MAP[String(hex).replace("#", "").toUpperCase()] = key; });
}

/** 원본 색 치환표. 기본 네이비 팔레트 값을 현재 테마 값으로 바꾸고 커스텀 슬라이드 colorMap 을 더함 */
function buildRemap() {
  const r = {
    "1F3864": COLOR.navy,
    "17294A": COLOR.navyDeep,
    "6B8EC2": COLOR.navyPastel,
    "A9B9D9": COLOR.navyPastel2,
  };
  Object.entries(OWN_COLOR_MAP).forEach(([hex, key]) => { if (COLOR[key]) r[hex] = COLOR[key]; });
  return r;
}

const COLOR_REMAP = {};

// ---------------------------------------------------------------- 서체
// fontFace 는 TTF 내부 패밀리명(nameID 1, 16). 굵은체 파일(NanumGothicBold.ttf)도 패밀리명은 "NanumGothic" 이고 "NanumGothic Bold" 는 전체 이름(nameID 4)
// 굵은 글자는 패밀리명과 굵게 속성(b="1")으로 지정 (PowerPoint 가 굵게 서식을 저장하는 방식과 같음)
// 전체 이름으로 지정하면 LibreOffice 등 패밀리명으로 찾는 프로그램이 대체 글꼴로 조판함 (영문은 DejaVu Sans Bold 로 확인)
const FONT = {
  regular: "NanumGothic",
  bold: "NanumGothic",
  INSTALL: "apt-get install -y fonts-nanum (Debian/Ubuntu) 또는 https://hangeul.naver.com 나눔고딕 설치",
};

// 크기(pt). 커스텀 슬라이드 재생(own 템플릿)은 원본 글꼴 크기를 그대로 사용
const SIZE = {
  coverTitle: 40,
  coverSub: 16,
  dividerNo: 32,
  dividerTitle: 32,
  dividerItem: 18,
  contentsTitle: 32,
  contentsItem: 20,
  secNo: 32,
  secTitle: 20,
  tracker: 18,
  headline: 18, // 1줄과 2줄 모두 동일 크기. 슬라이드 간 위계를 일정하게 유지
  marker: 18,
  goalBand: 16, // 추진전략 지붕(목표) 문구. 헤드라인(18)보다 한 단계 낮고 기둥 제목(14)보다 한 단계 높음
  panelHead: 14,
  body: 12,
  tableBody: 12,
  tableDense: 11,
  note: 10,
  pageNo: 11,
  stat: 28,
  BODY_MIN: 11, // 본문 계열 하한. 각주와 출처와 쪽번호는 제외
  OWN_MIN: 9, // 커스텀 슬라이드 재생에서 서체 폭 차이를 흡수할 때의 축소 하한
};

const PARA = {
  lineSpacing: 1.15,
  paraGapPt: 4,
  paraGapMaxPt: 18,
  bulletIndentIn: 0.18,
};

// ---------------------------------------------------------------- 글자 수와 개수 상한 (Node 와 Python 공용: limits.json 으로도 기록)
const LIMIT = {
  // 18pt 나눔고딕(한글 0.94em)이 헤드라인 폭 12.493in 에 수용하는 순수 한글 53자와 106자에 여유를 둔 값
  headlineOneLine: 50,
  headlineTwoLine: 100,
  markerTitle: 30,
  panelHead: 16,
  bulletItem: 45,
  bulletsPerPanel: 5,
  tableCell: 24,
  chevronStep: 10,
  cardTitle: 16,
  tasksPerSlideMax: 4, // 한 슬라이드에 담는 Task 상한 (기본은 1건, 분량 제한 시 3-4건)
  moduleSlidesMin: 2, // 모듈당 수행계획 슬라이드 하한 (개요 1장과 Task 슬라이드 1장)
  moduleSlidesMax: 8, // 모듈당 수행계획 슬라이드 상한
  panelsPerSlide: 4,
  panelsPerSlideReport: 5,
  tableRowsPerSlide: 16,
  tasksPerMulti: 3,
  freeSlidesMax: 8, // 오리지널 장표(free, 자유 헤드라인) 상한
  tableFillMin: 0.6, // 표 열별 한 줄 폭 합이 표 폭에서 차지해야 하는 최소 비율 (미만이면 표가 비어 보임)
  boxTextFillMin: 0.65, // 불릿 상자 항목 글줄이 상자 안쪽 폭에서 차지하는 평균 비율의 하한 (미만이면 오른쪽이 비어 보임)
  boxTextMaxFillMin: 0.8, // 불릿 상자에서 가장 긴 항목 글줄이 안쪽 폭에서 차지하는 비율의 하한 (미만이면 모든 줄의 오른쪽이 비어 보임)
  summaryFillMin: 0.9, // 종합 상자(아젠다 박스) 항목 글줄 평균 비율의 하한 (결론 칸이므로 불릿 상자보다 높게 둠)
  summaryMaxFillMin: 0.95, // 종합 상자에서 가장 긴 항목 글줄 비율의 하한
  boxFillMin: 0.45, // 테두리 상자 안 텍스트가 차지해야 하는 최소 비율 (추정 폭 기반이라 실제보다 낮게 잡힘)
  bandBottomGapMax: 0.15, // 본문 밴드 하단 여백 상한 (내용이 위로 몰리는 정도)
  bodyCoverMin: 0.7, // 본문 밴드 높이 가운데 내용이 차지해야 하는 최소 비율 (상자를 내용에 맞춰 줄인 뒤 남는 공간 판정)
  bulletOnlyShareMax: 0.5, // 불릿 패널만 쓴 슬라이드의 본문 내 최대 비중
  deckVarietyRatio: 0.3, // 본문 슬라이드 대비 템플릿 종류 하한
  deckTemplateShareMax: 0.4, // 한 템플릿이 본문에서 차지하는 최대 비중
  taskVarietyRatio: 0.5, // Task 슬라이드 템플릿 종류 / 슬라이드 수 권장 하한
  sameTemplateRun: 3, // 같은 템플릿 연속 허용 상한 (4장 연속부터 리듬 경고)
  accentPerSlide: 1,
};

// ---------------------------------------------------------------- 텍스트 폭 추정 (measure)
const METRIC = {
  EM_HANGUL: 1.0,
  EM_LATIN: 0.55,
  EM_SPACE: 0.3,
  LINE_HEIGHT: 1.2,
  SAFETY: 0.92,
  SAFETY_METRIC: 0.9, // 렌더러의 괄호·한영 자동 간격 여유
  SAFETY_LINES: 0.94, // 줄 수 추정(estimateLines) 여유. 폭 90-100% 문구는 LibreOffice 나눔고딕 렌더에서 대부분 1줄. 글 폭 판정(lineWidthIn, wordWidthIn)은 SAFETY_METRIC 유지 (전역 0.94 는 도형 라벨 줄바꿈 발생)
  DONUT_PLOT: 0.9, // 도넛 차트의 플롯 지름 대비 상자 크기 비율 (중앙 흰 원 계산)
  TABLE_LINE_HEIGHT: 1.35, // 표 셀 행간 판정 (나눔고딕 실측 행간이 본문 판정치보다 높음)
};

/** 판형에 맞춘 밴드 좌표. x 와 w 는 폭 비율, y 와 h 는 높이 비율로 환산 */
function scaled(layoutKey) {
  const L = LAYOUTS[layoutKey] || LAYOUTS["16:9"];
  const sx = L.W / BASE_W;
  const sy = L.H / BASE_H;
  const box = (b) => ({ x: +(b.x * sx).toFixed(3), y: +(b.y * sy).toFixed(3), w: +(b.w * sx).toFixed(3), h: +(b.h * sy).toFixed(3) });
  return {
    layout: L,
    sx,
    sy,
    marginX: BAND.MARGIN_X, // 판형과 무관하게 0.42인치 고정
    secNo: box(BAND.SECNO),
    secTitle: box(BAND.SECTITLE),
    tracker: { ...box(BAND.TRACKER), x: +((BAND.TRACKER.x) * sx).toFixed(3), w: +((L.W - BAND.MARGIN_X * sx) - BAND.TRACKER.x * sx).toFixed(3) },
    headline: { ...box(BAND.HEADLINE), y: +((BAND.HEADLINE.y - BAND.HEADLINE_NUDGE) * sy).toFixed(3), w: +(L.W - 2 * BAND.MARGIN_X * sx).toFixed(3) },
    ruleTopY: +(BAND.RULE_TOP_Y * sy).toFixed(3),
    ruleY: +(BAND.RULE_Y * sy).toFixed(3),
    ruleW: +(L.W - 2 * BAND.MARGIN_X * sx).toFixed(3),
    markerShape: box(BAND.MARKER_SHAPE),
    markerText: { ...box(BAND.MARKER_TEXT), w: +(L.W - BAND.MARGIN_X * sx - BAND.MARKER_TEXT.x * sx).toFixed(3) },
    contentY: +(BAND.CONTENT_Y * sy).toFixed(3),
    contentYNoMarker: +(BAND.CONTENT_Y_NO_MARKER * sy).toFixed(3),
    contentBottom: +(BAND.CONTENT_BOTTOM * sy).toFixed(3),
    contentX: BAND.MARGIN_X, // 가장자리 여백은 판형과 무관하게 0.42인치 고정
    contentW: +(L.W - 2 * BAND.MARGIN_X).toFixed(3),
    bodyX: +(BAND.BODY_X * sx).toFixed(3),
    bodyW: +((BAND.BODY_RIGHT - BAND.BODY_X) * sx).toFixed(3),
    // 쪽번호는 판형과 무관하게 우측 가장자리 여백(0.42인치)을 지킴
    pageNo: { x: +(L.W - 3.0 * sx - (BAND.EDGE_MIN - (BASE_W - (BAND.PAGENO.x + BAND.PAGENO.w)) * sx)).toFixed(3), y: +(BAND.PAGENO.y * sy).toFixed(3), w: +(3.0 * sx).toFixed(3), h: BAND.PAGENO.h },
    noteY: +(BAND.NOTE_Y * sy).toFixed(3),
  };
}

/** limits.json 기록 (lint.py 와 공유) */
function writeLimits(dir) {
  // 판형별 헤드라인 1줄 상한(한글 환산 글자 수): 렌더링으로 검증한 16:9 상한(LIMIT.headlineOneLine)을 판형의 헤드라인 폭 비율로 환산
  // lint 가 헤드라인 길이를 한글 1자 폭 단위로 재므로 같은 단위를 씀 (평균 글자 폭 기준 값은 좁은 판형에서 2줄 넘김을 놓침)
  const baseW = scaled("16:9").headline.w;
  const HEADLINE_LINE_CHARS = Object.fromEntries(Object.keys(LAYOUTS).map((k) => [k, Math.floor((LIMIT.headlineOneLine * scaled(k).headline.w) / baseW)]));
  fs.writeFileSync(path.join(dir, "limits.json"), JSON.stringify({ LIMIT, HEADLINE_LINE_CHARS, SIZE: { BODY_MIN: SIZE.BODY_MIN }, LAYOUTS, BAND: { EDGE_MIN: BAND.EDGE_MIN, CONTENT_Y: BAND.CONTENT_Y, BODY_PAD: BAND.BODY_PAD, CONTENT_BOTTOM: BAND.CONTENT_BOTTOM }, PANEL: { GAP: PANEL.GAP }, THEME_TEXT: { RULES: THEME_TEXT_RULES, HINT: THEME_TEXT_HINT, TEXT_DARK: TEXT_DARK_DEFAULT } }, null, 1));
}

module.exports = { LAYOUTS, BASE_W, BASE_H, BAND, MARKER, PANEL, COLOR, COLOR_REMAP, THEMES, applyTheme, deriveTheme, themePalette, contrast, TINT_TEXT_CONTRAST_MIN, setOwnColorMap, FONT, SIZE, PARA, LIMIT, METRIC, scaled, writeLimits };
