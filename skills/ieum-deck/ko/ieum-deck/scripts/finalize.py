#!/usr/bin/env python3
"""finalize.py - build.js 산출 PPTX를 PowerPoint 개방 가능 상태로 후처리

WHY: pptxgenjs가 만든 패키지는 LibreOffice에서 열리지만 PowerPoint(Windows)와
     iOS 미리보기는 개방을 거부. LibreOffice 재직렬화본은 개방됨이 실측으로 확인.
     재직렬화를 빌드 파이프라인에 편입하고 재직렬화 전후에 OPC 규격 위반을 제거.

HOW: 1) OPC 정규화 - 디렉터리 엔트리 제거, [Content_Types].xml 선두 배치,
        실재하지 않는 부품의 Override 제거, 내장 xlsx에 재귀 적용
     2) XML 교정 - cNvPr id 재부여, 누적 차트의 dLblPos 제거, 차트 글자의 동아시아 글꼴 지정, run 과 차트의 언어 태그 지정(meta.labels.language),
        핵심 속성 관계 형식 교정, 작성 프로그램 이름 비움, 문서 언어와 화면 판형 이름 삭제,
        OpenSymbol 불릿 글꼴을 본문 글꼴 따름으로 교체
     3) soffice 재직렬화 후 1과 2 재적용. soffice 부재 시 2단계까지 수행
     4) 처리 전후 수치 출력

사용:
    python scripts/finalize.py 발표자료.pptx
    python scripts/finalize.py 발표자료.pptx --no-soffice
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# 설정값. 조판 상수가 아닌 규격 상수이므로 tokens.js가 아닌 이 파일에 둠
# ---------------------------------------------------------------------------

CONTENT_TYPES_NAME = "[Content_Types].xml"

# 패키지 안에 다시 패키지가 들어가는 부품. 같은 정규화를 재귀 적용
EMBEDDED_PACKAGE_SUFFIXES = (".xlsx",)

# cNvPr id를 재부여할 부품. 도형 트리를 갖는 부품만 대상
SHAPE_TREE_PART_PATTERN = re.compile(
    r"^ppt/(slides|slideLayouts|slideMasters|notesSlides|notesMasters)/[^/]+\.xml$"
)

# 슬라이드 XML의 cNvPr id 부여 규칙
# WHY: 도형 트리 루트(p:spTree의 nvGrpSpPr)는 관례상 1을 사용하고 도형은 2부터 시작.
#      pptxgenjs는 표(graphicFrame)에 별도 카운터를 써서 도형 id와 충돌시킴
SHAPE_TREE_ROOT_ID = 1
SHAPE_ID_START = 2

# 누적 계열 차트의 묶음 방식. 이 값이면 데이터 레이블 위치를 지정할 수 없음
STACKED_GROUPINGS = ("stacked", "percentStacked")

# 묶음 방식을 갖는 차트 종류. 누적 판정 대상
GROUPING_CHART_TAGS = (
    "c:barChart",
    "c:bar3DChart",
    "c:lineChart",
    "c:line3DChart",
    "c:areaChart",
    "c:area3DChart",
)

# 누적 차트에서 제거할 데이터 레이블 위치값
FORBIDDEN_STACKED_LABEL_POSITION = "outEnd"

# 슬라이드 부품 판정. id 중복 집계 대상
SLIDE_PART_PATTERN = re.compile(r"^ppt/slides/slide\d+\.xml$")

# LibreOffice 변환 제한 시간. 초 단위
SOFFICE_TIMEOUT_SEC = 300

SOFFICE_COMMAND = "soffice"

CNVPR_ID_PATTERN = re.compile(r'(<p:cNvPr\s+id=")(\d+)(")')

OVERRIDE_PATTERN = re.compile(r"<Override\s[^>]*?/>")

PART_NAME_PATTERN = re.compile(r'PartName="([^"]+)"')

# 패키지 관계 부품과 확장 속성 부품
PACKAGE_RELS_NAME = "_rels/.rels"
APP_PROPS_NAME = "docProps/app.xml"

# 핵심 속성 관계 형식. soffice 재직렬화는 officedocument 경로의 비규격 형식을 기록하여
# 규격 형식으로 핵심 속성을 찾는 도구가 제목과 작성자를 읽지 못함
NONSTANDARD_CORE_REL_TYPE = "http://schemas.openxmlformats.org/officedocument/2006/relationships/metadata/core-properties"
CORE_REL_TYPE = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"

# 작성 프로그램 이름. 재직렬화 도구 이름과 버전이 납품 파일 속성에 남지 않도록 비움
APPLICATION_PATTERN = re.compile(r"<Application>[^<]*</Application>")

# 핵심 속성 부품과 사용자 지정 속성 부품
CORE_PROPS_NAME = "docProps/core.xml"
CUSTOM_PROPS_NAME = "docProps/custom.xml"

# 문서 언어. 원 빌드에는 없고 soffice 재저장이 실행 환경 로캘(LANG 미설정 시 en-US)로 채우므로 지움
DOCUMENT_LANGUAGE_PATTERN = re.compile(r"<dc:language>[^<]*</dc:language>")

# 화면 판형 이름. pptxgenjs 가 판형과 관계없이 "On-screen Show (16:9)" 로 기록하고
# soffice 재저장이 사용자 지정 속성으로 옮기므로 두 위치에서 지움 (올바른 이름을 채우려면 판형별 이름표가 필요하여 지우는 쪽을 택함)
PRESENTATION_FORMAT_PATTERNS = (
    re.compile(r"<PresentationFormat>[^<]*</PresentationFormat>"),
    re.compile(r'<property\b[^>]*\bname="PresentationFormat"[^>]*>.*?</property>', re.S),
)


# ---------------------------------------------------------------------------
# 패키지 입출력
# ---------------------------------------------------------------------------


def read_package(data: bytes) -> list[tuple[str, bytes]]:
    """ZIP 바이트에서 파일 항목만 원래 순서로 추출. 디렉터리 엔트리는 제외"""
    entries = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            entries.append((item.filename, archive.read(item.filename)))
    return entries


def write_package(entries: list[tuple[str, bytes]]) -> bytes:
    """항목 목록을 ZIP 바이트로 직렬화. 입력 순서를 그대로 유지"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries:
            archive.writestr(name, payload)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# 1단계. OPC 정규화
# ---------------------------------------------------------------------------


def strip_ghost_overrides(content_types_xml: str, part_names: set[str]) -> tuple[str, int]:
    """실재하지 않는 부품의 Override 선언을 제거

    WHY: pptxgenjs는 슬라이드 수만큼 slideMaster{N}.xml의 Override를 선언하지만
         실제 부품은 slideMaster1.xml 1개뿐. PowerPoint는 이 불일치에서 개방을 거부
    """
    removed = 0

    def keep(match: re.Match) -> str:
        nonlocal removed
        found = PART_NAME_PATTERN.search(match.group(0))
        if not found:
            return match.group(0)
        if found.group(1).lstrip("/") in part_names:
            return match.group(0)
        removed += 1
        return ""

    return OVERRIDE_PATTERN.sub(keep, content_types_xml), removed


def normalize_package(data: bytes) -> tuple[bytes, dict]:
    """디렉터리 엔트리 제거와 [Content_Types].xml 선두 배치와 유령 Override 제거

    내장 패키지(xlsx)에도 같은 처리를 재귀 적용
    """
    entries = read_package(data)
    part_names = {name for name, _ in entries}
    stats = {"ghost_overrides": 0}

    normalized = []
    for name, payload in entries:
        if name == CONTENT_TYPES_NAME:
            fixed_xml, removed = strip_ghost_overrides(payload.decode("utf-8"), part_names)
            stats["ghost_overrides"] += removed
            payload = fixed_xml.encode("utf-8")
        elif name.lower().endswith(EMBEDDED_PACKAGE_SUFFIXES):
            payload, inner_stats = normalize_package(payload)
            stats["ghost_overrides"] += inner_stats["ghost_overrides"]
        normalized.append((name, payload))

    # WHY: OPC 규격은 [Content_Types].xml을 첫 항목으로 요구. pptxgenjs는 디렉터리
    #      엔트리를 먼저 기록하여 이 조건을 위반
    normalized.sort(key=lambda item: 0 if item[0] == CONTENT_TYPES_NAME else 1)
    return write_package(normalized), stats


# ---------------------------------------------------------------------------
# 2단계. XML 교정
# ---------------------------------------------------------------------------


def renumber_shape_ids(xml: str) -> tuple[str, int]:
    """도형 트리 안의 cNvPr id를 루트 1과 도형 2부터의 순번으로 재부여"""
    counter = {"index": 0}
    changed = {"count": 0}

    def assign(match: re.Match) -> str:
        counter["index"] += 1
        new_id = SHAPE_TREE_ROOT_ID if counter["index"] == 1 else SHAPE_ID_START + counter["index"] - 2
        if str(new_id) != match.group(2):
            changed["count"] += 1
        return f"{match.group(1)}{new_id}{match.group(3)}"

    return CNVPR_ID_PATTERN.sub(assign, xml), changed["count"]


def strip_stacked_label_position(xml: str) -> tuple[str, int]:
    """누적 계열 차트에서 허용되지 않는 데이터 레이블 위치를 제거

    WHY: ECMA-376은 stacked와 percentStacked에서 outEnd를 허용하지 않음.
         PowerPoint는 이 값을 만나면 복구 또는 개방 거부로 대응
    """
    label_pattern = re.compile(
        r'<c:dLblPos\s+val="%s"\s*/>' % FORBIDDEN_STACKED_LABEL_POSITION
    )
    removed = {"count": 0}

    def clean_group(match: re.Match) -> str:
        block = match.group(0)
        grouping = re.search(r'<c:grouping\s+val="([^"]+)"', block)
        if not grouping or grouping.group(1) not in STACKED_GROUPINGS:
            return block
        cleaned, hits = label_pattern.subn("", block)
        removed["count"] += hits
        return cleaned

    for tag in GROUPING_CHART_TAGS:
        group_pattern = re.compile(r"<%s(?:\s[^>]*)?>[\s\S]*?</%s>" % (tag, tag))
        xml = group_pattern.sub(clean_group, xml)
    return xml, removed["count"]


def strip_alien_chart_extensions(xml: str) -> tuple[str, int]:
    """차트의 확장 블록 중 표준 네임스페이스 자식이 없는 것을 제거

    WHY: LibreOffice 재직렬화는 c15 네임스페이스의 showLeaderLines만 담은 c:extLst를
         추가. 스키마 검증기는 표준 밖 네임스페이스 요소를 걷어낸 뒤 검사하므로
         빈 c:ext로 남아 FAIL. 기본값과 같은 설정이라 제거해도 표시가 달라지지 않음
    """
    ext_pattern = re.compile(r"<c:extLst>([\s\S]*?)</c:extLst>")
    standard_child_pattern = re.compile(r"<c:(?!ext\b|extLst\b)[A-Za-z]")
    removed = {"count": 0}

    def drop_if_alien(match: re.Match) -> str:
        if standard_child_pattern.search(match.group(1)):
            return match.group(0)
        removed["count"] += 1
        return ""

    return ext_pattern.sub(drop_if_alien, xml), removed["count"]


# 라틴 글꼴(a:latin)만 지정되고 동아시아 글꼴(a:ea) 지정이 뒤따르지 않는 글자 속성
LATIN_ONLY_FONT_PATTERN = re.compile(r'(<a:latin typeface="([^"]*)"\s*/>)(?!\s*<a:ea\b)')


def add_chart_east_asian_fonts(xml: str) -> tuple[str, int]:
    """차트 글자 속성의 라틴 글꼴 지정 뒤에 같은 글꼴의 동아시아(a:ea), 복합 문자(a:cs) 지정을 추가

    WHY: pptxgenjs 는 차트 범주, 범례, 데이터 레이블에 a:latin 만 기록. 한글은 동아시아 글꼴 지정을 따르므로
         지정이 없으면 테마 기본 글꼴(맑은 고딕)이나 렌더러 대체 글꼴로 표시되어 본문 서체와 어긋남
    """
    return LATIN_ONLY_FONT_PATTERN.subn(r'\1<a:ea typeface="\2"/><a:cs typeface="\2"/>', xml)


# LibreOffice 전용 기호 글꼴(OpenSymbol)을 지정한 불릿 글꼴. 같은 자리(buFont 와 buFontTx 는 택일)에 본문 글꼴 따름을 넣음
OPENSYMBOL_BULLET_FONT_PATTERN = re.compile(r'<a:buFont\s+typeface="OpenSymbol"[^>]*/>')
TEXT_BULLET_FONT = "<a:buFontTx/>"


def use_text_font_for_opensymbol_bullets(xml: str) -> tuple[str, int]:
    """OpenSymbol 불릿 글꼴 지정을 본문 글꼴 따름(a:buFontTx)으로 교체

    WHY: soffice 재직렬화는 PowerPoint 기호 글꼴로 옮기지 못한 불릿 문자(하위 항목의 줄표 "-")에 OpenSymbol 을 지정.
         OpenSymbol 이 없는 PowerPoint 는 이 불릿을 빈 네모로 표시. LibreOffice 렌더 검수에서는 OpenSymbol 이 함께 설치되어 정상으로 보임.
         줄표는 본문 글꼴(나눔고딕)에 있는 문자이므로 본문 글꼴을 따르게 하여 두 프로그램의 표시를 맞춤
    """
    return OPENSYMBOL_BULLET_FONT_PATTERN.subn(TEXT_BULLET_FONT, xml)


PARA_PATTERN = re.compile(r"<a:p>(.*?)</a:p>", re.S)
PPR_PATTERN = re.compile(r"<a:pPr\b[^>]*/>|<a:pPr\b[^>]*>.*?</a:pPr>", re.S)


def strip_duplicate_paragraph_props(xml: str) -> tuple[str, int]:
    """한 문단(a:p) 안의 두 번째 이후 a:pPr 제거.
    pptxgenjs 는 run 마다 pPr 를 내보내므로 스키마 위반이 생기고 PowerPoint 가 복구를 요구한다"""
    removed = 0

    def clean(match: re.Match) -> str:
        nonlocal removed
        body = match.group(1)
        seen = False
        parts = []
        pos = 0
        for m in PPR_PATTERN.finditer(body):
            parts.append(body[pos:m.start()])
            if not seen:
                parts.append(m.group(0))
                seen = True
            else:
                removed += 1
            pos = m.end()
        parts.append(body[pos:])
        return "<a:p>" + "".join(parts) + "</a:p>"

    return PARA_PATTERN.sub(clean, xml), removed

ADJ_NAME_PATTERN = re.compile(r'<p:cNvPr id="(\d+)" name="adj:(\d+)"')

# 한글 run 언어 지정 대상. 한글 음절, 자모, 호환 자모
HANGUL_PATTERN = re.compile(r"[ᄀ-ᇿ㄰-㆏가-힣]")
RUN_PATTERN = re.compile(r"<a:r>(.*?)</a:r>", re.S)
RUN_TEXT_PATTERN = re.compile(r"<a:t(?:\s[^>]*)?>(.*?)</a:t>", re.S)
RUN_LANG_PATTERN = re.compile(r'(<a:rPr\b[^>]*?\blang=")([^"]*)(")')
# 언어 태그. pptxgenjs 는 모든 run, 문단 끝, 차트를 en-US 로 기록하므로 빌드 기록(meta.labels.language)의 태그로 바꿈
# 기본값은 assets/labels.json 의 language (build.js 와 같은 표). latin 은 일반 run, east_asia 는 한글이 든 run 의 태그
PPTXGENJS_LANG = "en-US"
LABELS_PATH = Path(__file__).resolve().parent.parent / "assets" / "labels.json"
RUN_LANGUAGE = dict(json.loads(LABELS_PATH.read_text(encoding="utf-8"))["language"])
LANG_TAG_PATTERN = re.compile(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*")
LATIN_LANG_PATTERN = re.compile(r'(<a:(?:rPr|endParaRPr|defRPr)\b[^>]*?\blang="|<c:lang val=")' + re.escape(PPTXGENJS_LANG) + '(")')


def set_latin_language(xml: str) -> tuple[str, int]:
    """pptxgenjs 가 기록한 en-US 태그(run, 문단 끝, 기본 글자 속성, 차트 언어)를 RUN_LANGUAGE["latin"] 으로 바꿈. 기본값 en-US 는 변경 없음"""
    latin = RUN_LANGUAGE.get("latin") or PPTXGENJS_LANG
    if latin == PPTXGENJS_LANG:
        return xml, 0
    return LATIN_LANG_PATTERN.subn(lambda m: m.group(1) + latin + m.group(2), xml)


def set_hangul_run_language(xml: str) -> tuple[str, int]:
    """한글이 든 run 의 언어(a:rPr lang)를 RUN_LANGUAGE["east_asia"](기본 ko-KR)로 기록

    WHY: pptxgenjs 는 모든 run 을 lang="en-US" 로 기록. LibreOffice 재직렬화는 run 의 동아시아 문자 부분 언어를
         실행 환경 로캘의 기본값으로 채우므로 로캘이 비어 있는 환경에서는 한글이 zh-CN 으로 저장됨.
         한글 run 의 언어를 문서에 직접 기록하면 실행 환경과 관계없이 ko-KR 로 유지됨 (렌더 결과는 같음)
    """
    count = 0
    east = RUN_LANGUAGE["east_asia"]

    def rep(m: re.Match) -> str:
        nonlocal count
        body = m.group(1)
        if not HANGUL_PATTERN.search("".join(RUN_TEXT_PATTERN.findall(body))):
            return m.group(0)
        lang = RUN_LANG_PATTERN.search(body)
        if lang is None or lang.group(2) == east:
            return m.group(0)
        count += 1
        return "<a:r>" + body[:lang.start(2)] + east + body[lang.end(2):] + "</a:r>"

    return RUN_PATTERN.sub(rep, xml), count


def set_korean_word_wrap(xml: str) -> tuple[str, int]:
    """모든 문단 속성에 eaLnBrk="0" 을 두어 한글 단어 중간 줄바꿈을 막음 (PowerPoint 아시아 타이포그래피 옵션)"""
    count = 0
    def rep(m):
        nonlocal count
        tag = m.group(0)
        if "eaLnBrk" in tag:
            return tag
        count += 1
        return tag[:-1].rstrip("/") + ' eaLnBrk="0" hangingPunct="1"' + ("/>" if tag.endswith("/>") else ">")
    xml = re.sub(r"<a:pPr(?:\s[^>]*)?/?>", rep, xml)
    return xml, count


def apply_shape_adjust(xml: str) -> tuple[str, int]:
    """도형 이름 adj:N 을 prstGeom avLst 의 adj 값으로 옮긴다 (pptxgenjs 는 조정값을 지원하지 않아 objectName 으로 전달)
    셰브론과 홈플레이트의 꼭짓점 폭, 둥근 사각형의 반경을 원본과 같게 맞추는 용도"""
    count = 0
    out = []
    pos = 0
    for m in ADJ_NAME_PATTERN.finditer(xml):
        adj = m.group(2)
        # 이 도형(p:sp) 의 prstGeom 위치를 찾아 avLst 치환
        sp_end = xml.find("</p:sp>", m.end())
        seg = xml[m.end():sp_end]
        geom = re.search(r'<a:prstGeom prst="([a-zA-Z0-9]+)">\s*<a:avLst\s*/>|<a:prstGeom prst="([a-zA-Z0-9]+)"><a:avLst></a:avLst>', seg)
        if geom is None:
            continue
        prst = geom.group(1) or geom.group(2)
        new_geom = f'<a:prstGeom prst="{prst}"><a:avLst><a:gd name="adj" fmla="val {adj}"/></a:avLst>'
        out.append(xml[pos:m.end()])
        out.append(seg[:geom.start()] + new_geom + seg[geom.end():])
        pos = sp_end
        count += 1
    out.append(xml[pos:])
    return "".join(out), count


def fix_core_properties_rel_type(xml: str) -> tuple[str, int]:
    """패키지 관계의 핵심 속성 형식을 규격 형식으로 교정"""
    return xml.replace(NONSTANDARD_CORE_REL_TYPE, CORE_REL_TYPE), xml.count(NONSTANDARD_CORE_REL_TYPE)


def clear_application_name(xml: str) -> tuple[str, int]:
    """확장 속성의 작성 프로그램 이름을 비움"""
    return APPLICATION_PATTERN.subn("<Application></Application>", xml)


def clear_document_language(xml: str) -> tuple[str, int]:
    """핵심 속성의 문서 언어를 지움"""
    return DOCUMENT_LANGUAGE_PATTERN.subn("", xml)


def clear_presentation_format(xml: str) -> tuple[str, int]:
    """확장 속성과 사용자 지정 속성의 화면 판형 이름을 지움"""
    removed = 0
    for pattern in PRESENTATION_FORMAT_PATTERNS:
        xml, count = pattern.subn("", xml)
        removed += count
    return xml, removed


def fix_part_xml(name: str, payload: bytes) -> tuple[bytes, dict]:
    """부품 1개에 XML 교정을 적용. 대상이 아니면 원본 그대로 반환"""
    stats = {"renumbered_ids": 0, "stacked_labels": 0, "alien_extensions": 0, "duplicate_ppr": 0, "shape_adjust": 0}

    if name == PACKAGE_RELS_NAME:
        xml, stats["core_rel_type"] = fix_core_properties_rel_type(payload.decode("utf-8"))
        return xml.encode("utf-8"), stats

    if name == APP_PROPS_NAME:
        xml, stats["application"] = clear_application_name(payload.decode("utf-8"))
        xml, stats["presentation_format"] = clear_presentation_format(xml)
        return xml.encode("utf-8"), stats

    if name == CUSTOM_PROPS_NAME:
        xml, stats["presentation_format"] = clear_presentation_format(payload.decode("utf-8"))
        return xml.encode("utf-8"), stats

    if name == CORE_PROPS_NAME:
        xml, stats["document_language"] = clear_document_language(payload.decode("utf-8"))
        return xml.encode("utf-8"), stats

    if SHAPE_TREE_PART_PATTERN.match(name):
        xml, changed = renumber_shape_ids(payload.decode("utf-8"))
        stats["renumbered_ids"] = changed
        xml, dup = strip_duplicate_paragraph_props(xml)
        stats["duplicate_ppr"] = dup
        xml, adj = apply_shape_adjust(xml)
        stats["shape_adjust"] = adj
        xml, cf = fix_table_cell_fills(xml)
        stats["cell_fill"] = cf
        xml, cm = restore_cell_vertical_margins(xml)
        stats["cell_margin"] = cm
        xml, bf = use_text_font_for_opensymbol_bullets(xml)
        stats["opensymbol_bullets"] = bf
        xml, _ = set_korean_word_wrap(xml)
        xml, _ = set_latin_language(xml)
        xml, lang = set_hangul_run_language(xml)
        stats["hangul_lang"] = lang
        return xml.encode("utf-8"), stats

    if name.startswith("ppt/charts/") and name.endswith(".xml"):
        xml, removed = strip_stacked_label_position(payload.decode("utf-8"))
        stats["stacked_labels"] = removed
        xml, dropped = strip_alien_chart_extensions(xml)
        stats["alien_extensions"] = dropped
        xml, fonts = add_chart_east_asian_fonts(xml)
        stats["chart_ea_fonts"] = fonts
        xml, _ = set_latin_language(xml)
        return xml.encode("utf-8"), stats

    return payload, stats


def fix_package_xml(data: bytes) -> tuple[bytes, dict]:
    """패키지 전체에 XML 교정을 적용"""
    entries = read_package(data)
    stats = {"renumbered_ids": 0, "stacked_labels": 0, "alien_extensions": 0, "duplicate_ppr": 0, "shape_adjust": 0}

    fixed = []
    for name, payload in entries:
        payload, part_stats = fix_part_xml(name, payload)
        for key in stats:
            stats[key] += part_stats[key]
        fixed.append((name, payload))

    fixed.sort(key=lambda item: 0 if item[0] == CONTENT_TYPES_NAME else 1)
    return write_package(fixed), stats


# ---------------------------------------------------------------------------
# 3단계. LibreOffice 재직렬화
# ---------------------------------------------------------------------------


def find_soffice() -> str | None:
    return shutil.which(SOFFICE_COMMAND)


def build_soffice_env() -> dict:
    """화면이 없는 실행 환경에서 soffice 가 창 시스템을 찾지 않도록 가상 출력 장치를 지정"""
    env = os.environ.copy()
    env.setdefault("SAL_USE_VCLPLUGIN", "svp")
    return env


def reserialize_with_soffice(pptx_path: Path) -> bool:
    """LibreOffice로 pptx를 다시 저장하여 PowerPoint가 받아들이는 패키지로 교체

    WHY: 규격 위반 3건을 고쳐도 PowerPoint 개방은 실패. 재직렬화본만 개방됨이
         실측으로 확인되었으므로 근본 원인 탐색 대신 재직렬화를 편입
    """
    soffice = find_soffice()
    if not soffice:
        return False

    with tempfile.TemporaryDirectory() as work_dir:
        work = Path(work_dir)
        source = work / pptx_path.name
        shutil.copy2(pptx_path, source)
        profile = work / "soffice_profile"
        profile.mkdir()

        result = subprocess.run(
            [
                soffice,
                "--headless",
                f"-env:UserInstallation=file://{profile}",
                "--convert-to",
                "pptx",
                "--outdir",
                str(work / "out"),
                str(source),
            ],
            env=build_soffice_env(),
            capture_output=True,
            timeout=SOFFICE_TIMEOUT_SEC,
        )

        converted = work / "out" / f"{source.stem}.pptx"
        if result.returncode != 0 or not converted.exists():
            return False
        shutil.copy2(converted, pptx_path)
    return True


# ---------------------------------------------------------------------------
# 4단계. 점검 수치
# ---------------------------------------------------------------------------


def count_package_defects(data: bytes) -> dict:
    """패키지 1개의 구조 결함 수치. 내장 패키지 결함도 합산"""
    counts = {"parts": 0, "dir_entries": 0, "content_types_misplaced": 0, "ghost_overrides": 0}

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        counts["dir_entries"] = sum(1 for item in archive.infolist() if item.is_dir())
        part_names = {item.filename for item in archive.infolist() if not item.is_dir()}
        counts["parts"] = len(part_names)

        if not names or names[0] != CONTENT_TYPES_NAME:
            counts["content_types_misplaced"] = 1

        if CONTENT_TYPES_NAME in part_names:
            declared = PART_NAME_PATTERN.findall(archive.read(CONTENT_TYPES_NAME).decode("utf-8"))
            counts["ghost_overrides"] = sum(
                1 for part in declared if part.lstrip("/") not in part_names
            )

        for name in sorted(part_names):
            if name.lower().endswith(EMBEDDED_PACKAGE_SUFFIXES):
                inner = count_package_defects(archive.read(name))
                for key in ("dir_entries", "content_types_misplaced", "ghost_overrides"):
                    counts[key] += inner[key]
    return counts


def count_xml_defects(data: bytes) -> dict:
    """XML 수준의 결함 수치. id 중복 슬라이드 수, 누적 차트의 레이블 위치 수, 슬라이드의 OpenSymbol 불릿 수"""
    counts = {"duplicate_id_slides": 0, "stacked_label_positions": 0, "opensymbol_bullets": 0}

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            if SLIDE_PART_PATTERN.match(name):
                xml = archive.read(name).decode("utf-8")
                ids = [match.group(2) for match in CNVPR_ID_PATTERN.finditer(xml)]
                if len(ids) != len(set(ids)):
                    counts["duplicate_id_slides"] += 1
                counts["opensymbol_bullets"] += len(OPENSYMBOL_BULLET_FONT_PATTERN.findall(xml))
            elif name.startswith("ppt/charts/") and name.endswith(".xml"):
                xml = archive.read(name).decode("utf-8")
                _, remaining = strip_stacked_label_position(xml)
                counts["stacked_label_positions"] += remaining
    return counts


def inspect(pptx_path: Path) -> dict:
    """PPTX 1개의 결함 수치 전체. validate.py가 같은 함수를 사용하여 판정을 일치시킴"""
    data = pptx_path.read_bytes()
    metrics = count_package_defects(data)
    metrics.update(count_xml_defects(data))
    return metrics


# 점검 항목의 표시 이름. 값이 0이 아니면 FAIL 대상
FAILABLE_METRICS = {
    "dir_entries": "디렉터리 엔트리",
    "content_types_misplaced": "Content_Types 선두 위반",
    "ghost_overrides": "유령 Override",
    "duplicate_id_slides": "id 중복 슬라이드",
    "stacked_label_positions": "누적 차트 레이블 위치",
    "opensymbol_bullets": "OpenSymbol 불릿",
}


def format_metrics(label: str, metrics: dict) -> str:
    items = " ".join(f"{name}={metrics[key]}" for key, name in FAILABLE_METRICS.items())
    return f"[finalize] {label}: 부품={metrics['parts']} {items}"


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------


# 표 셀 채움에 허용되는 기본 색 (navy 와 mono 테마 색, 틴트, 회색, 흰색). 재직렬화가 넣는 표 스타일 강조색을 흰색으로 되돌림
# 사용자 지정 테마 색은 finalize() 가 빌드 기록의 palette 에서 읽어 더함
CELL_PALETTE = {"1F3864", "17294A", "6B8EC2", "A9B9D9", "D5DDEC", "E9EBF0", "F7F8FA", "F2F2F2",
                "C9CDD8", "FFFFFF", "BFBFBF", "A6A6A6", "595959", "333333", "2B2B2B", "4D4D4D",
                "808080", "D9D9D9", "C0392B", "8B93A7", "EBEBEB", "F8F8F8", "939393"}


TC_BLOCK = re.compile(r"<a:tc\b[^>]*>.*?</a:tc>", re.S)
TC_PR_OPEN = re.compile(r"<a:tcPr\b([^>]*?)(/?)>")
BODY_PR_OPEN = re.compile(r"<a:bodyPr\b([^>]*?)/?>")


def restore_cell_vertical_margins(xml: str) -> tuple[str, int]:
    """soffice 재직렬화가 표 셀 위아래 여백(tcPr marT, marB)을 bodyPr tIns, bIns 로 옮기면
    PowerPoint 는 tcPr 기본값(0.05인치)을 적용하여 행이 설계보다 높아지고 표가 본문 아래로 넘침.
    bodyPr 값을 tcPr 에 되돌려 두 프로그램의 행 높이를 맞춤"""
    count = 0

    def fix_cell(m):
        nonlocal count
        block = m.group(0)
        pr = TC_PR_OPEN.search(block)
        if not pr or "marT=" in pr.group(1):
            return block
        bp = BODY_PR_OPEN.search(block)
        ins = dict(re.findall(r'\b([tb]Ins)="(\d+)"', bp.group(1))) if bp else {}
        if "tIns" not in ins or "bIns" not in ins:
            return block
        count += 1
        new_open = f'<a:tcPr{pr.group(1)} marT="{ins["tIns"]}" marB="{ins["bIns"]}"{pr.group(2)}>'
        return block[:pr.start()] + new_open + block[pr.end():]

    return TC_BLOCK.sub(fix_cell, xml), count


def fix_table_cell_fills(xml: str) -> tuple[str, int]:
    count = 0

    def rep(m):
        nonlocal count
        color = m.group(2).upper()
        if color in CELL_PALETTE:
            return m.group(0)
        count += 1
        return f'{m.group(1)}<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'

    xml = re.sub(r'(<a:tcPr[^>]*>(?:(?!</a:tcPr>).)*?)<a:solidFill><a:srgbClr val="([0-9a-fA-F]{6})"\s*/></a:solidFill>', rep, xml, flags=re.S)
    return xml, count


def capture_hole_sizes(data: bytes) -> dict:
    """차트 부품별 도넛 holeSize 값을 기록"""
    out = {}
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            if name.startswith("ppt/charts/") and name.endswith(".xml"):
                m = re.search(r'<c:holeSize val="(\d+)"', zf.read(name).decode("utf-8", "replace"))
                if m:
                    out[name] = m.group(1)
    return out


def restore_hole_sizes(data: bytes, holes: dict) -> bytes:
    if not holes:
        return data
    entries = read_package(data)
    fixed = []
    for name, payload in entries:
        if name in holes:
            xml = payload.decode("utf-8", "replace")
            xml = re.sub(r'<c:holeSize val="\d+"', f'<c:holeSize val="{holes[name]}"', xml)
            payload = xml.encode("utf-8")
        fixed.append((name, payload))
    return write_package(fixed)


def theme_palette(pptx_path: Path) -> set:
    """빌드 기록(<파일명>.build.json)에 남은 테마 색. 사용자 지정 테마 색의 표 셀 채움을 흰색으로 되돌리지 않기 위해 읽음"""
    record = pptx_path.with_suffix(".build.json")
    if not record.is_file():
        return set()
    try:
        return {str(c).upper() for c in json.loads(record.read_text(encoding="utf-8")).get("palette") or []}
    except (OSError, ValueError):
        return set()


def record_language(pptx_path: Path) -> dict:
    """빌드 기록(<파일명>.build.json)의 언어 태그(meta.labels.language). 태그 형식이 아닌 값은 무시하고 기본값 유지"""
    record = pptx_path.with_suffix(".build.json")
    if not record.is_file():
        return {}
    try:
        lang = json.loads(record.read_text(encoding="utf-8")).get("language") or {}
    except (OSError, ValueError):
        return {}
    out = {}
    for key in ("latin", "east_asia"):
        val = lang.get(key)
        if isinstance(val, str) and LANG_TAG_PATTERN.fullmatch(val):
            out[key] = val
        elif val is not None:
            print(f"[finalize] 언어 태그 {key}={val!r} 형식 오류로 기본값 {RUN_LANGUAGE[key]} 유지")
    return out


def finalize(pptx_path: Path, use_soffice: bool = True) -> dict:
    """입력 PPTX를 후처리하여 같은 경로에 덮어쓰고 처리 전후 수치를 반환"""
    CELL_PALETTE.update(theme_palette(pptx_path))
    RUN_LANGUAGE.update(record_language(pptx_path))
    before = inspect(pptx_path)
    print(format_metrics("처리 전", before))

    data = pptx_path.read_bytes()
    data, _ = normalize_package(data)
    data, _ = fix_package_xml(data)
    pptx_path.write_bytes(data)

    reserialized = False
    if use_soffice:
        holes = capture_hole_sizes(data)  # soffice 재직렬화가 도넛 구멍 크기를 50 으로 되돌리므로 보존
        reserialized = reserialize_with_soffice(pptx_path)
        if reserialized:
            data = pptx_path.read_bytes()
            data, _ = normalize_package(data)
            data, _ = fix_package_xml(data)
            data = restore_hole_sizes(data, holes)
            entries = [(n, fix_table_cell_fills(p.decode("utf-8", "replace"))[0].encode("utf-8") if SHAPE_TREE_PART_PATTERN.match(n) else p) for n, p in read_package(data)]
            data = write_package(entries)
            pptx_path.write_bytes(data)
        else:
            print("[finalize] soffice 부재 또는 변환 실패로 재직렬화 생략. "
                  "PowerPoint 개방은 미보증 상태")
    else:
        print("[finalize] --no-soffice 지정으로 재직렬화 생략")

    after = inspect(pptx_path)
    print(format_metrics("처리 후", after))
    return {"before": before, "after": after, "reserialized": reserialized}


def main() -> int:
    parser = argparse.ArgumentParser(description="PPTX를 PowerPoint 개방 가능 상태로 후처리")
    parser.add_argument("pptx", help="처리할 PPTX 경로. 같은 경로에 덮어씀")
    parser.add_argument("--no-soffice", action="store_true", help="LibreOffice 재직렬화 생략")
    args = parser.parse_args()

    pptx_path = Path(args.pptx)
    if not pptx_path.is_file():
        print(f"[finalize] 파일 없음: {pptx_path}")
        return 1

    result = finalize(pptx_path, use_soffice=not args.no_soffice)
    failed = [name for key, name in FAILABLE_METRICS.items() if result["after"][key]]
    if failed:
        print(f"[finalize] 잔여 결함: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
