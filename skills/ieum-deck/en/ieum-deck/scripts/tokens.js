"use strict";
// tokens.js
// The only file that defines the design system values. The base page size for coordinates is 16:9 (13.333×7.5 inches),
// and scaled(layout) converts other page sizes by width and height ratios. Font sizes are not converted.

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------- Page sizes
// Page size item of the kickoff questions. Default 16:9, A4 landscape for printed submission, 10.83 and 4:3 for older screens
const LAYOUTS = {
  "16:9": { name: "LAYOUT_16x9_WIDE", W: 13.333, H: 7.5 },
  "A4": { name: "LAYOUT_A4_LAND", W: 11.69, H: 8.27 },
  "10.83": { name: "LAYOUT_10_83", W: 10.83, H: 7.5 },
  "4:3": { name: "LAYOUT_4x3", W: 10.0, H: 7.5 },
};
const BASE_W = 13.333;
const BASE_H = 7.5;

// ---------------------------------------------------------------- Band coordinates (16:9 base, inches)
const BAND = {
  MARGIN_X: 0.42, // Left start of the headline and rules. The right end is W - 0.42
  SECNO: { x: 0.39, y: 0.29, w: 0.49, h: 0.44 }, // Section number 32pt
  SECTITLE: { x: 0.93, y: 0.43, w: 6.49, h: 0.31 }, // Section title 20pt
  TRACKER: { x: 7.55, y: 0.44, w: 5.36, h: 0.31 }, // Chapter tracker 18pt right-aligned
  RULE_TOP_Y: 1.05, // Top rule of the headline band
  HEADLINE: { x: 0.42, y: 1.05, w: 12.5, h: 0.75 }, // Headline 18pt Bold centered between the two band rules
  // Vertical centering in a box works on line boxes, so glyphs can sit high or low depending on the font
  // Measured at 200dpi, NanumGothic glyphs sit about 2.3pt low, so half of that (0.016in) is corrected upward
  HEADLINE_NUDGE: 0.016,
  RULE_Y: 1.8, // Bottom rule of the headline band. 0.75pt thick
  RULE_PT: 0.75,
  MARKER_SHAPE: { x: 0.54, y: 2.05, w: 0.31, h: 0.26 }, // Where the marker symbol sits. The shape kind is MARKER.shape
  MARKER_TEXT: { x: 0.85, y: 2.02, w: 11.99, h: 0.26 }, // Marker title 18pt Bold
  CONTENT_Y: 2.32, // Bottom of the marker band (baseline of the body area)
  // The body group is placed so the space under the marker title equals the space above the page number (measured on the original standard slides: 0.17 above, 0.2 below, in inches)
  BODY_PAD: 0.1, // Gap from the baseline to the top of the body group
  CONTENT_BOTTOM: 6.92, // Body bottom (0.16 inch above the page number row)
  CONTENT_Y_NO_MARKER: 2.07, // Body top for layouts without a marker band (3_blank screen)
  PAGENO: { x: 10.33, y: 7.1, w: 3.0, h: 0.4 }, // Page number 11pt right-aligned
  NOTE_Y: 6.78, // Baseline of the footnote and source row
  BODY_X: 0.98, // Left start of the body group (indented by the marker symbol width to set it apart from the headline band)
  BODY_RIGHT: 12.36, // Right end of the body group (symmetric side margins)
  EDGE_MIN: 0.42, // Minimum slide edge margin (check_layout check value)
};

// Marker shape. Square by default. Choose bar or triangle with meta.marker or --marker
const MARKER = {
  shape: "square", // square | bar | triangle
  square: { w: 0.16, h: 0.16 },
  bar: { w: 0.08, h: 0.22 },
  triangle: { w: 0.18, h: 0.18 },
};

// ---------------------------------------------------------------- Shape specs (inches)
const PANEL = {
  GAP: 0.2, // Minimum gap between shapes
  INSET: 0.07, // Inset inside shapes (0.05-0.09)
  INSET_MIN: 0.05,
  INSET_MAX: 0.09,
  HEAD_H: 0.32, // 12pt title bar height (composite box titles, flow box titles)
  TITLE_H: 0.42, // 14pt panel title bar height (parametric panels, strategy pillars, capability tiles, staff cards). 0.09 inch above and below the text line
  SUBHEAD_H: 0.5, // Height taken by an unfilled area title (text and underline)
  ROW_H_MIN: 0.3, // Minimum table row height
  ROW_H_MAX: 0.8, // Row height cap when a table fills the body (tables with Harvey balls or multi-line cells)
  FILL_EXPAND: 1.6, // Cap multiplier for text box height (against the needed content height). Extra height goes to the margin outside the box
  LABEL_MG_X: 0.045, // Left and right insets of navy label cells (each)
  LABEL_MG_Y: 0.02, // Top and bottom insets of navy label cells (each)
  LABEL_GAP: 0.14, // Gap between the row label box and the content box (made by narrowing the label box while the content stays put)
  ROW_H_TEXT: 0.5, // Row height cap for tables with single-line text only (a height at which cells do not look empty. Median body row on the original standard slides is 0.44)
  TABLE_HEAD_H: 0.4, // Header row height when body rows grow (measured 0.33-0.39 inch on the original standard slides)
  LINE_PT: 0.5, // Box border
  LINE_PT_STRONG: 0.75, // Panel border
  CHEVRON_OVERLAP: 0.06,
  CHART_MIN_H: 1.6,
  CHART_MIN_W: 3.0,
  PIE_MIN: 2.4,
  ROUND_RADIUS: 0.05, // Rounded rectangle radius cap
  SLACK_WARN: 0.45, // Warning threshold for the empty space ratio inside a box
  FILL_RATIO_MIN: 0.78,
  SMALL_BOX_W: 0.6,
  ICON_MAX: 0.95, // Images below this size count as icons and are replaced with symbols
  CELL_MG: [0.05, 0.03, 0.05, 0.03], // Default table cell insets (left, top, right, bottom) in inches // boxes narrower than this get zero inset and no wrapping // minimum share the group must take in the body band
};

// ---------------------------------------------------------------- Colors (pptxgenjs takes 6 digits without #)
// Black-and-white base. Navy is used only for label cells, chevrons, the conclusion band, markers and figure emphasis
const COLOR = {
  navy: "1F3864", // Label fill, panel title text, emphasis
  navyDeep: "17294A", // Question banner and conclusion band
  navyPastel: "6B8EC2", // Default chart data color
  navyPastel2: "A9B9D9",
  navyRamp: ["1F3864", "6B8EC2", "A9B9D9", "D5DDEC"],
  textDark: "333333",
  textMuted: "8B93A7",
  textGray: "595959",
  tintHead: "E9EBF0", // Header tint
  tintBg: "F7F8FA", // Background tint
  tintLight: "F2F2F2",
  tintNavy: "C9CDD8",
  border: "A6A6A6",
  borderLight: "BFBFBF",
  accent: "C0392B", // One place per slide
  white: "FFFFFF",
  black: "000000",
};
// Color themes. Two are provided, navy (default) and mono (achromatic). applyTheme overwrites them when the user sets other colors
// Tints (tintHead, tintBg) and the secondary gray (textMuted) are theme keys too, so reapplying a theme leaves no values from the previous theme
// mono tints and secondary gray are achromatic grays with the same luminance as the navy values (the navy values are blue-gray and look mixed in an achromatic theme)
const THEMES = {
  navy: { navy: "1F3864", navyDeep: "17294A", navyPastel: "6B8EC2", navyPastel2: "A9B9D9", navyRamp: ["1F3864", "6B8EC2", "A9B9D9", "D5DDEC"], tintNavy: "C9CDD8", tintHead: "E9EBF0", tintBg: "F7F8FA", textMuted: "8B93A7" },
  mono: { navy: "2B2B2B", navyDeep: "111111", navyPastel: "7F7F7F", navyPastel2: "BFBFBF", navyRamp: ["2B2B2B", "7F7F7F", "BFBFBF", "E0E0E0"], tintNavy: "D0D0D0", tintHead: "EBEBEB", tintBg: "F8F8F8", textMuted: "939393" },
};

// Rules that compute all theme keys from one base color. The hue stays that of the base color
// Saturation is a ratio multiplied by the base saturation, and lightness is fixed. Both come from measured relations in the default navy palette (1F3864 family)
const THEME_DERIVE = {
  navyPastel: { s: 0.79, l: 0.59 },
  navyPastel2: { s: 0.73, l: 0.757 },
  ramp4: { s: 0.72, l: 0.88 },
  tintNavy: { s: 0.31, l: 0.818 },
  tintHead: { s: 0.36, l: 0.927 },
  tintBg: { s: 0.44, l: 0.975 },
};
const THEME_DEEP_L_RATIO = 0.74; // navyDeep lightness = base lightness × ratio (lightness ratio of 17294A to 1F3864)
const LABEL_CONTRAST_MIN = 4.5; // Minimum white text contrast for label cells and the conclusion band (WCAG AA body text)
// navyPastel carries bold white text on pyramid tier 2 and funnel stage 2, so a contrast minimum applies (the default 6B8EC2 has 3.35)
// High-luminance hues such as yellow and orange bury white text even at the same lightness, so lightness is lowered to compensate
const PASTEL_CONTRAST_MIN = 3.0;
const CONTRAST_STEP_L = 0.01; // Step by which lightness drops when contrast is below the minimum
const DARK_TEXT_CONTRAST_MIN = 3.0; // Contrast minimum for diagram fills carrying body text color (pyramid tier 3, light funnel band, outer market size circle)
const TINT_TEXT_CONTRAST_MIN = 4.5; // Contrast minimum for tint backgrounds carrying body text (WCAG AA body text)
// The muted gray fills the AS-IS head cell (white text) and colors source, footnote and axis end text on white (default 8B93A7 has 3.08 contrast with white)
const MUTED_CONTRAST_MIN = 3.0;
// Text contrast rules per theme color key. on is the text color typeset on that color (white is white, textDark is the body text color)
// Values computed from a base color are built to meet the rules, so lint checks only directly set color keys against the limits.json copy (below the minimum is a WARN, which passes with a stated reason)
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
const TEXT_DARK_DEFAULT = COLOR.textDark; // Body text color at module load (recorded in limits.json as a theme-independent value)
// Fix guidance attached to rule warnings
const THEME_TEXT_HINT = "Assign light colors to keys that carry body text (navyPastel2, navyRamp 3rd-4th, tints) and dark colors to keys that carry white text (navy, navyDeep, navyPastel, textMuted)";
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

/** WCAG relative luminance */
function luminance(hex) {
  const lin = [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

/** Luminance contrast of two colors (WCAG, 1-21) */
function contrast(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

/** Contrast with white text */
function contrastWithWhite(hex) {
  return contrast(hex, "FFFFFF");
}

/** Color with lightness lowered until white text contrast reaches the minimum */
function darkenForWhite(hsl, min) {
  const c = { ...hsl };
  let hex = hslToHex(c);
  while (contrastWithWhite(hex) < min && c.l > 0) {
    c.l = Math.max(0, c.l - CONTRAST_STEP_L);
    hex = hslToHex(c);
  }
  return { hex, l: c.l };
}

/** Normalizes a color code (drops #, uppercase). Error if it is not a 6-digit color code */
function normHex(v, field) {
  const hex = String(v || "").replace("#", "").toUpperCase();
  if (!HEX6.test(hex)) throw new Error(`meta.themeColors.${field} must be a 6-digit color code (e.g. 1B4332). Input: ${v}`);
  return hex;
}

/** Computes all theme keys from a base color. If white text contrast is below the minimum, lowers the base lightness and returns the values before and after */
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

/** Applies a color theme. key is navy or mono. custom is an object overwriting COLOR keys, and with base the deriveTheme result applies first
 *  adjusted in the return value is the base color changed by contrast correction (null without correction) */
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
  // In a computed theme, if keys such as navyPastel are set separately and navyRamp is not, rebuild the chart series colors from the final values
  if (derived && !keys.navyRamp) COLOR.navyRamp = [COLOR.navy, COLOR.navyPastel, COLOR.navyPastel2, derived.colors.navyRamp[3]];
  Object.keys(COLOR_REMAP).forEach((k) => { delete COLOR_REMAP[k]; });
  Object.assign(COLOR_REMAP, buildRemap());
  return { color: COLOR, adjusted };
}

/** Current theme colors to add to the allowed table cell colors (check_layout and finalize read them from the build record) */
function themePalette() {
  const keys = ["navy", "navyDeep", "navyPastel", "navyPastel2", "tintNavy", "tintHead", "tintBg", "textMuted"];
  return [...new Set([...keys.map((k) => COLOR[k]), ...COLOR.navyRamp].map((c) => String(c).toUpperCase()))];
}

// Custom slide source color → COLOR key mapping (colorMap in own-deck.json). Changes along with the theme
const OWN_COLOR_MAP = {};
function setOwnColorMap(m) {
  Object.keys(OWN_COLOR_MAP).forEach((k) => { delete OWN_COLOR_MAP[k]; });
  Object.entries(m || {}).forEach(([hex, key]) => { OWN_COLOR_MAP[String(hex).replace("#", "").toUpperCase()] = key; });
}

/** Source color replacement table. Maps default navy palette values to current theme values and adds the custom slide colorMap */
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

// ---------------------------------------------------------------- Fonts
// fontFace is the family name inside the TTF (nameID 1, 16). The bold file (NanumGothicBold.ttf) also has the family name "NanumGothic"; "NanumGothic Bold" is its full name (nameID 4)
// Bold text is set with the family name plus the bold attribute (b="1"), the same way PowerPoint saves bold formatting
// With the full name, programs that look fonts up by family name, such as LibreOffice, typeset a fallback font (confirmed as DejaVu Sans Bold for Latin text)
const FONT = {
  regular: "NanumGothic",
  bold: "NanumGothic",
  INSTALL: "apt-get install -y fonts-nanum (Debian/Ubuntu) or install NanumGothic from https://hangeul.naver.com",
};

// Sizes (pt). Custom slide playback (own template) keeps the source font sizes
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
  headline: 18, // Same size for 1 and 2 lines. Keeps the hierarchy constant across slides
  marker: 18,
  goalBand: 16, // Strategy roof (goal) text. One step below the headline (18) and one step above pillar titles (14)
  panelHead: 14,
  body: 12,
  tableBody: 12,
  tableDense: 11,
  note: 10,
  pageNo: 11,
  stat: 28,
  BODY_MIN: 11, // Body text minimum. Footnotes, sources and page numbers excluded
  OWN_MIN: 9, // Shrink minimum when custom slide playback absorbs font width differences
};

const PARA = {
  lineSpacing: 1.15,
  paraGapPt: 4,
  paraGapMaxPt: 18,
  bulletIndentIn: 0.18,
};

// ---------------------------------------------------------------- Character and count limits (shared by Node and Python, also written to limits.json)
const LIMIT = {
  // Values with a margin under the 53 and 106 pure Hangul characters that 18pt NanumGothic (Hangul 0.94em) fits in the 12.493in headline width
  headlineOneLine: 50,
  headlineTwoLine: 100,
  markerTitle: 30,
  panelHead: 16,
  bulletItem: 45,
  bulletsPerPanel: 5,
  tableCell: 24,
  chevronStep: 10,
  cardTitle: 16,
  tasksPerSlideMax: 4, // Maximum Tasks on one slide (1 by default, 3-4 under a page limit)
  moduleSlidesMin: 2, // Minimum execution plan slides per module (1 overview and 1 Task slide)
  moduleSlidesMax: 8, // Maximum execution plan slides per module
  panelsPerSlide: 4,
  panelsPerSlideReport: 5,
  tableRowsPerSlide: 16,
  tasksPerMulti: 3,
  freeSlidesMax: 8, // Maximum original slides (free, free headline)
  tableFillMin: 0.6, // Minimum share of the per-column one-line width sum in the table width (below it the table looks empty)
  boxTextFillMin: 0.65, // Minimum average share of bullet box item lines in the inner box width (below it the right side looks empty)
  boxTextMaxFillMin: 0.8, // Minimum share of the longest bullet box item line in the inner width (below it every line looks empty on the right)
  summaryFillMin: 0.9, // Minimum average line share of synthesis box (agenda box) items (higher than bullet boxes because it is a conclusion cell)
  summaryMaxFillMin: 0.95, // Minimum share of the longest synthesis box item line
  boxFillMin: 0.45, // Minimum share of text inside a bordered box (estimated from widths, so it reads lower than reality)
  bandBottomGapMax: 0.15, // Maximum bottom margin of the body band (how far content is crowded upward)
  bodyCoverMin: 0.7, // Minimum share of the body band height taken by content (judges space left after boxes shrink to content)
  bulletOnlyShareMax: 0.5, // Maximum share of body slides using only bullet panels
  deckVarietyRatio: 0.3, // Minimum template kinds against body slides
  deckTemplateShareMax: 0.4, // Maximum share of one template in the body
  taskVarietyRatio: 0.5, // Recommended minimum of Task slide template kinds / slide count
  sameTemplateRun: 3, // Maximum run of the same template (a rhythm warning from 4 in a row)
  accentPerSlide: 1,
};

// ---------------------------------------------------------------- Text width estimation (measure)
const METRIC = {
  EM_HANGUL: 1.0,
  EM_LATIN: 0.55,
  EM_SPACE: 0.3,
  LINE_HEIGHT: 1.2,
  SAFETY: 0.92,
  SAFETY_METRIC: 0.9, // Margin for the renderer's automatic spacing around brackets and between Korean and Latin text
  DONUT_PLOT: 0.9, // Box size ratio against the donut chart plot diameter (for the center white circle)
  TABLE_LINE_HEIGHT: 1.35, // Line spacing judgment in table cells (measured NanumGothic spacing is higher than the body value)
};

/** Band coordinates fitted to the page size. x and w scale by the width ratio, y and h by the height ratio */
function scaled(layoutKey) {
  const L = LAYOUTS[layoutKey] || LAYOUTS["16:9"];
  const sx = L.W / BASE_W;
  const sy = L.H / BASE_H;
  const box = (b) => ({ x: +(b.x * sx).toFixed(3), y: +(b.y * sy).toFixed(3), w: +(b.w * sx).toFixed(3), h: +(b.h * sy).toFixed(3) });
  return {
    layout: L,
    sx,
    sy,
    marginX: BAND.MARGIN_X, // Fixed at 0.42 inch regardless of page size
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
    contentX: BAND.MARGIN_X, // The edge margin is fixed at 0.42 inch regardless of page size
    contentW: +(L.W - 2 * BAND.MARGIN_X).toFixed(3),
    bodyX: +(BAND.BODY_X * sx).toFixed(3),
    bodyW: +((BAND.BODY_RIGHT - BAND.BODY_X) * sx).toFixed(3),
    // The page number keeps the right edge margin (0.42 inch) regardless of page size
    pageNo: { x: +(L.W - 3.0 * sx - (BAND.EDGE_MIN - (BASE_W - (BAND.PAGENO.x + BAND.PAGENO.w)) * sx)).toFixed(3), y: +(BAND.PAGENO.y * sy).toFixed(3), w: +(3.0 * sx).toFixed(3), h: BAND.PAGENO.h },
    noteY: +(BAND.NOTE_Y * sy).toFixed(3),
  };
}

/** Writes limits.json (shared with lint.py) */
function writeLimits(dir) {
  // Headline 1-line limit per page size (Hangul-equivalent characters): the 16:9 limit verified by rendering (LIMIT.headlineOneLine) scaled by the page size's headline width ratio
  // lint measures headline length in units of one Hangul character width, so the same unit is used (a value based on the average character width misses wraps to 2 lines on narrow page sizes)
  const baseW = scaled("16:9").headline.w;
  const HEADLINE_LINE_CHARS = Object.fromEntries(Object.keys(LAYOUTS).map((k) => [k, Math.floor((LIMIT.headlineOneLine * scaled(k).headline.w) / baseW)]));
  fs.writeFileSync(path.join(dir, "limits.json"), JSON.stringify({ LIMIT, HEADLINE_LINE_CHARS, SIZE: { BODY_MIN: SIZE.BODY_MIN }, LAYOUTS, BAND: { EDGE_MIN: BAND.EDGE_MIN, CONTENT_Y: BAND.CONTENT_Y, BODY_PAD: BAND.BODY_PAD, CONTENT_BOTTOM: BAND.CONTENT_BOTTOM }, PANEL: { GAP: PANEL.GAP }, THEME_TEXT: { RULES: THEME_TEXT_RULES, HINT: THEME_TEXT_HINT, TEXT_DARK: TEXT_DARK_DEFAULT } }, null, 1));
}

module.exports = { LAYOUTS, BASE_W, BASE_H, BAND, MARKER, PANEL, COLOR, COLOR_REMAP, THEMES, applyTheme, deriveTheme, themePalette, contrast, TINT_TEXT_CONTRAST_MIN, setOwnColorMap, FONT, SIZE, PARA, LIMIT, METRIC, scaled, writeLimits };
