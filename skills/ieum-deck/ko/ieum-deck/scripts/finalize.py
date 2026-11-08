#!/usr/bin/env python3
"""finalize.py - build.js 산출 PPTX를 PowerPoint 개방 가능 상태로 후처리

WHY: pptxgenjs가 만든 패키지는 LibreOffice에서 열리지만 PowerPoint(Windows)와
     iOS 미리보기는 개방을 거부. LibreOffice 재직렬화본은 개방됨이 실측으로 확인.
     재직렬화를 빌드 파이프라인에 편입하고 재직렬화 전후에 OPC 규격 위반을 제거.

HOW: 1) OPC 정규화 - 디렉터리 엔트리 제거, [Content_Types].xml 선두 배치,
        실재하지 않는 부품의 Override 제거, 내장 xlsx에 재귀 적용
     2) XML 교정 - cNvPr id 재부여, 누적 차트의 dLblPos 제거, 차트 글자의 동아시아 글꼴 지정, run 과 차트의 언어 태그 지정(meta.labels.language),
        핵심 속성 관계 형식 교정, 작성 프로그램 이름 비움, 문서 언어와 화면 판형 이름 삭제,
        OpenSymbol 불릿 글꼴을 본문 글꼴 따름으로 교체, 모든 문단에 줄바꿈 단위 속성 기록(meta.lineBreak),
        주석과 출처 행의 라벨 뒤 내어쓰기 문단에 marL, indent 기록 (같은 상자의 다른 불릿 없는 문단은 0 으로 기록),
        재직렬화가 0 으로 바꾼 내어쓰기 문단의 탭 위치를 marL 로 복원,
        빌드 기록의 계열 레이블 지정(chartLabels)을 항목 레이블로 기록 (재직렬화 전후 각 1회)
     3) soffice 재직렬화 후 1과 2 재적용. soffice 부재 시 2단계까지 수행
     4) 처리 전후 수치 출력

사용:
    python scripts/finalize.py 발표자료.pptx
    python scripts/finalize.py 발표자료.pptx --no-soffice
"""

from __future__ import annotations

import argparse
import html
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

# 계열 레이블 지정(빌드 기록 chartLabels)의 항목 값 {pos, x, y}. pos 의 none 은 숨김, 나머지는 ECMA-376 데이터 레이블 위치
# x, y 는 기본 위치에서 옮길 거리 (차트 폭과 높이 대비 비율, c:manualLayout)
# 차트 형식별 허용 여부는 lint.py 가 검사하고 여기서는 XML 속성에 넣을 수 있는 값인지만 확인
LABEL_HIDDEN = "none"
LABEL_POSITIONS = (LABEL_HIDDEN, "bestFit", "b", "ctr", "inBase", "inEnd", "l", "outEnd", "r", "t")

CHART_PART_DIR = "ppt/charts/"
SERIES_PATTERN = re.compile(r"<c:ser>.*?</c:ser>", re.S)
SERIES_LABELS_PATTERN = re.compile(r"<c:dLbls>(.*?)</c:dLbls>", re.S)
POINT_LABEL_PATTERN = re.compile(r'<c:dLbl>\s*<c:idx val="(\d+)"/>(.*?)</c:dLbl>', re.S)
LABEL_POSITION_PATTERN = re.compile(r'<c:dLblPos val="[^"]*"/>')
LABEL_LAYOUT_PATTERN = re.compile(r"<c:layout>.*?</c:layout>", re.S)
# 계열 레이블 묶음에만 허용되는 요소. 계열 서식을 항목 레이블에 복사할 때 제외
SERIES_ONLY_LABEL_PATTERN = re.compile(r"<c:showLeaderLines[^>]*/>|<c:leaderLines>.*?</c:leaderLines>|<c:extLst>.*?</c:extLst>", re.S)

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
PPR_WITH_BODY_PATTERN = re.compile(r"<a:pPr\b([^>]*)>(.*?)</a:pPr>", re.S)
TAB_STOP_PATTERN = re.compile(r'<a:tab\b[^>]*\bpos="(\d+)"[^>]*/>')


def set_hanging_indent(xml: str) -> tuple[str, int]:
    """라벨 뒤 내어쓰기 문단의 marL 과 indent 기록. 불릿 없는 문단(buNone)이 pptxgenjs 기본값 marL="0" indent="0" 이고
    탭 위치가 1개(0 보다 큼)이면 marL 을 그 탭 위치로, indent 를 음수 탭 위치로 바꿈

    WHY: 주석과 출처 행의 여러 줄 묶음은 "라벨<탭>내용" 첫 줄 뒤의 줄을 라벨 뒤 위치에 맞춰야 함 (atoms.hangPlan).
         pptxgenjs 는 불릿 없는 문단에 marL="0" indent="0" 만 기록하므로 build.js 가 내어쓰기 위치를 문단의 유일한 탭 위치로 넘김.
         LibreOffice 24.2 는 탭 위치만 있는 문단의 탭을 기본 탭 간격(1인치)으로 보내고, 내어쓰기 문단은 첫 줄 탭과 둘째 줄 이후를 marL 에 맞춤.
         soffice 재직렬화본은 0 인 marL, indent 를 기록하지 않고 탭 위치를 pos="0" 으로 남기므로 재적용 단계에서 다른 문단은 바뀌지 않음
    """
    count = 0

    def fix(m: re.Match) -> str:
        nonlocal count
        attrs, body = m.group(1), m.group(2)
        tabs = TAB_STOP_PATTERN.findall(body)
        if "<a:buNone/>" not in body or len(tabs) != 1 or int(tabs[0]) <= 0:
            return m.group(0)
        if not (re.search(r'\smarL="0"', attrs) and re.search(r'\sindent="0"', attrs)):
            return m.group(0)
        count += 1
        pos = tabs[0]
        attrs = re.sub(r'\smarL="0"', f' marL="{pos}"', re.sub(r'\sindent="0"', f' indent="-{pos}"', attrs))
        return f"<a:pPr{attrs}>{body}</a:pPr>"

    return PPR_WITH_BODY_PATTERN.sub(fix, xml), count


def restore_hanging_tab_stop(xml: str) -> tuple[str, int]:
    """내어쓰기 문단(불릿 없음, marL 이 M, indent 가 -M)의 유일한 탭 위치를 pos="0" 에서 pos="M" 으로 복원

    WHY: soffice 재직렬화는 LibreOffice 내부의 marL 기준 탭 위치(0)를 글 상자 왼쪽 기준으로 변환하지 않은 채 pos="0" 으로 기록.
         PowerPoint 는 탭 위치를 글 상자 왼쪽 끝에서 측정.
         첫 줄이 0 에서 시작하는 "<탭>내용" 문단(출처 행과 번호 주석의 둘째 줄 이후)은 0 위치의 탭에서 이동이 없으므로 내용이 라벨 위치에서 시작.
         라벨 뒤 탭(첫 줄)은 PowerPoint 에서도 marL 까지 이동하므로 첫 줄의 내용 위치는 정상.
         LibreOffice 는 두 경우 모두 marL 에 맞추므로 검수 PDF 에는 이 결함이 나타나지 않음
    """
    count = 0

    def fix(m: re.Match) -> str:
        nonlocal count
        attrs, body = m.group(1), m.group(2)
        if attrs.rstrip().endswith("/") or "<a:buChar" in body or "<a:buAutoNum" in body:
            return m.group(0)
        marl, ind = re.search(r'\smarL="(\d+)"', attrs), re.search(r'\sindent="-(\d+)"', attrs)
        if not (marl and ind and int(marl.group(1)) > 0 and marl.group(1) == ind.group(1)):
            return m.group(0)
        if TAB_STOP_PATTERN.findall(body) != ["0"]:
            return m.group(0)
        count += 1
        body = re.sub(r'(<a:tab\b[^>]*\bpos=")0(")', rf"\g<1>{marl.group(1)}\g<2>", body)
        return f"<a:pPr{attrs}>{body}</a:pPr>"

    return PPR_WITH_BODY_PATTERN.sub(fix, xml), count


TXBODY_PATTERN = re.compile(r"<(p|a):txBody>(.*?)</\1:txBody>", re.S)
PPR_OPEN_TAG_PATTERN = re.compile(r"<a:pPr\b[^>]*?(/?)>")


def pin_indent_after_hanging(xml: str) -> tuple[str, int]:
    """내어쓰기 문단이 있는 글 상자에서 marL 이 없는 불릿 없는 문단에 marL="0" indent="0" 을 기록

    WHY: soffice 재직렬화본은 0 인 marL, indent 를 기록하지 않음. LibreOffice 24.2 는 marL 이 없는 문단을 가져올 때
         앞 문단의 왼쪽 여백을 이어받으므로 내어쓰기 묶음 뒤의 일반 문단(커스텀 슬라이드 원문의 ※ 묶음 뒤 본문)이 들여 써짐.
         불릿 문단의 여백은 목록 수준 속성이라 이어받지 않으므로 불릿 없는 내어쓰기 문단이 있는 상자에만 적용
    """
    count = 0

    def is_hanging(para: str) -> bool:
        m = PPR_OPEN_TAG_PATTERN.search(para)
        if not m or "<a:buChar" in para or "<a:buAutoNum" in para:
            return False
        marl, ind = re.search(r'\smarL="(\d+)"', m.group(0)), re.search(r'\sindent="-(\d+)"', m.group(0))
        return bool(marl and ind and int(marl.group(1)) > 0)

    def pin(para: str) -> str:
        nonlocal count
        m = PPR_OPEN_TAG_PATTERN.search(para)
        if not m or "marL=" in m.group(0) or "<a:buChar" in para or "<a:buAutoNum" in para:
            return para
        count += 1
        tag = m.group(0)
        fixed = tag[:len("<a:pPr")] + ' marL="0" indent="0"' + tag[len("<a:pPr"):]
        return para[:m.start()] + fixed + para[m.end():]

    def fix_body(m: re.Match) -> str:
        body = m.group(2)
        paras = PARA_PATTERN.findall(body)
        if not any(is_hanging(p) for p in paras):
            return m.group(0)
        return m.group(0).replace(body, PARA_PATTERN.sub(lambda pm: "<a:p>" + pin(pm.group(1)) + "</a:p>", body), 1)

    return TXBODY_PATTERN.sub(fix_body, xml), count


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


# 줄바꿈 단위(meta.lineBreak)별 문단 속성 값. word 는 한글 어절과 영문 단어를 줄 끝에서 나누지 않고, char 는 줄 끝 글자에서 나눔
LINE_BREAK_ATTRS = {
    "word": {"eaLnBrk": "0", "latinLnBrk": "0"},
    "char": {"eaLnBrk": "1", "latinLnBrk": "1"},
}
DEFAULT_LINE_BREAK = "word"
# 실행 중 적용할 줄바꿈 단위. finalize() 가 빌드 기록(lineBreak)으로 갱신
LINE_BREAK = {"mode": DEFAULT_LINE_BREAK}
PPR_OPEN_PATTERN = re.compile(r"<a:pPr(?:\s[^>]*)?/?>")
PARA_WITHOUT_PPR_PATTERN = re.compile(r"<a:p>(?!\s*<a:pPr\b)")


def line_break_attrs() -> dict:
    """빌드 기록의 줄바꿈 단위(LINE_BREAK["mode"])에 해당하는 문단 속성 값"""
    return LINE_BREAK_ATTRS[LINE_BREAK["mode"]]


def set_paragraph_line_break(xml: str) -> tuple[str, int]:
    """모든 문단 속성(a:pPr)에 줄바꿈 단위 속성(eaLnBrk, latinLnBrk)을 기록. 문단 속성이 없는 문단에는 문단 속성을 만들어 기록

    WHY: 두 속성은 PowerPoint 가 문단마다 읽는 줄바꿈 옵션(한글 단어 잘림 허용, 영문 단어 잘림 허용).
         soffice 재직렬화는 마스터의 txStyles 와 presentation.xml 의 defaultTextStyle 을 지우므로
         상속에 맡긴 값은 PowerPoint 의 프로그램 기본값으로 바뀜. 문단마다 직접 기록해야 PowerPoint 에서 같은 결과가 나옴.
         기존 값도 덮어써서 빌드 기록의 줄바꿈 단위와 어긋난 값이 남지 않게 함
    """
    attrs = line_break_attrs()
    count = 0

    def set_attrs(m: re.Match) -> str:
        nonlocal count
        tag = m.group(0)
        closing = "/>" if tag.endswith("/>") else ">"
        body = tag[:-len(closing)]
        for name, val in attrs.items():
            body = re.sub(rf'\s{name}="[^"]*"', "", body) + f' {name}="{val}"'
        if "hangingPunct=" not in body:
            body += ' hangingPunct="1"'
        count += 1
        return body + closing

    xml = PARA_WITHOUT_PPR_PATTERN.sub("<a:p><a:pPr/>", xml)
    return PPR_OPEN_PATTERN.sub(set_attrs, xml), count


def count_line_break_unset(xml: str) -> int:
    """줄바꿈 단위 속성이 빌드 기록 값과 다르거나 빠진 문단 수 (문단 속성이 없는 문단 포함)"""
    attrs = line_break_attrs()
    unset = 0
    for m in PARA_PATTERN.finditer(xml):
        ppr = PPR_OPEN_PATTERN.search(m.group(1))
        if ppr is None or any(f'{name}="{val}"' not in ppr.group(0) for name, val in attrs.items()):
            unset += 1
    return unset


# 직선 도형의 짧은 변 복원
# WHY: soffice 재직렬화는 가로선 높이 0 과 세로선 폭 0 을 LibreOffice 내부 최소 단위 1칸(1/100mm = 360 EMU)으로 기록.
#      line 도형은 상자의 왼쪽 위에서 오른쪽 아래로 그려지므로 PowerPoint 는 이 선을 0.01mm 기울어진 사선으로 표시
LO_UNIT_EMU = 360
STRAIGHT_LINE_SHAPE_PATTERN = re.compile(r"<p:(sp|cxnSp)\b.*?</p:\1>", re.S)
STRAIGHT_LINE_PRESET_PATTERN = re.compile(r'<a:prstGeom prst="(?:line|straightConnector1)"')
SHAPE_EXT_PATTERN = re.compile(r'<a:ext cx="(\d+)" cy="(\d+)"\s*/>')


def straighten_lines(xml: str) -> tuple[str, int]:
    """직선 도형의 짧은 변이 LibreOffice 최소 단위 이하이면 0 으로 되돌려 수평선과 수직선을 복원.
    짧은 변이 0.01mm 이하인 사선은 수평선, 수직선과 구별되지 않으므로 의도된 사선은 영향 없음"""
    count = 0

    def fix_ext(m):
        nonlocal count
        cx, cy = int(m.group(1)), int(m.group(2))
        if 0 < cy <= LO_UNIT_EMU < cx:
            cy = 0
        elif 0 < cx <= LO_UNIT_EMU < cy:
            cx = 0
        else:
            return m.group(0)
        count += 1
        return f'<a:ext cx="{cx}" cy="{cy}"/>'

    def fix_shape(m):
        body = m.group(0)
        if not STRAIGHT_LINE_PRESET_PATTERN.search(body):
            return body
        return SHAPE_EXT_PATTERN.sub(fix_ext, body, count=1)  # 첫 a:ext 가 도형 자신의 xfrm

    return STRAIGHT_LINE_SHAPE_PATTERN.sub(fix_shape, xml), count


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
        xml, _ = set_hanging_indent(xml)
        xml, _ = restore_hanging_tab_stop(xml)
        xml, adj = apply_shape_adjust(xml)
        stats["shape_adjust"] = adj
        xml, sl = straighten_lines(xml)
        stats["straightened_lines"] = sl
        xml, cm = restore_cell_vertical_margins(xml)
        stats["cell_margin"] = cm
        xml, bf = use_text_font_for_opensymbol_bullets(xml)
        stats["opensymbol_bullets"] = bf
        xml, _ = set_paragraph_line_break(xml)
        xml, _ = pin_indent_after_hanging(xml)
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
    """XML 수준의 결함 수치. id 중복 슬라이드 수, 누적 차트의 레이블 위치 수, 슬라이드의 OpenSymbol 불릿 수, 슬라이드의 줄바꿈 단위 미기록 문단 수, 슬라이드의 기울어진 직선 수"""
    counts = {"duplicate_id_slides": 0, "stacked_label_positions": 0, "opensymbol_bullets": 0, "line_break_unset": 0, "slanted_lines": 0}

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            if SLIDE_PART_PATTERN.match(name):
                xml = archive.read(name).decode("utf-8")
                ids = [match.group(2) for match in CNVPR_ID_PATTERN.finditer(xml)]
                if len(ids) != len(set(ids)):
                    counts["duplicate_id_slides"] += 1
                counts["opensymbol_bullets"] += len(OPENSYMBOL_BULLET_FONT_PATTERN.findall(xml))
                counts["line_break_unset"] += count_line_break_unset(xml)
                counts["slanted_lines"] += straighten_lines(xml)[1]
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
    "line_break_unset": "줄바꿈 단위 미기록 문단",
    "slanted_lines": "기울어진 직선",
}


def format_metrics(label: str, metrics: dict) -> str:
    items = " ".join(f"{name}={metrics[key]}" for key, name in FAILABLE_METRICS.items())
    return f"[finalize] {label}: 부품={metrics['parts']} {items}"


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------


TC_BLOCK = re.compile(r"<a:tc\b[^>]*>.*?</a:tc>", re.S)
TC_PR_OPEN = re.compile(r"<a:tcPr\b([^>]*?)(/?)>")
BODY_PR_OPEN = re.compile(r"<a:bodyPr\b([^>]*?)/?>")
# 셀 채움 = tcPr 직계 채움 요소(noFill, solidFill 등 이름이 Fill 로 끝남). 스키마 순서상 테두리(lnL, lnR, lnT, lnB, lnTlToBr, lnBlToTr)가
# 채움보다 앞서고 테두리마다 선 색 solidFill 을 품으므로 테두리 요소를 통째로 건너뜀
CELL_FILL = re.compile(r'<a:tcPr\b[^>]*>(?:<a:(ln\w*)\b(?:[^>]*?/>|.*?</a:\1>))*'
                       r'(?P<fill><a:(?P<kind>\w+Fill)\b(?:[^>]*?/>|.*?</a:(?P=kind)>))', re.S)
CELL_TEXT = re.compile(r"<a:t\b[^>]*>([^<]*)</a:t>")
WHITE_FILL = '<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'


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


def cell_text(block: str) -> str:
    """셀 글자. soffice 는 탭 등을 문자 참조(&#9;)로 다시 쓰므로 참조를 풀어 재직렬화 전후를 같은 기준으로 비교"""
    return html.unescape("".join(CELL_TEXT.findall(block)))


def capture_cell_fills(data: bytes) -> dict:
    """soffice 재직렬화 전 부품별 표 셀의 (글자, 직계 채움 유무) 목록"""
    out = {}
    for name, payload in read_package(data):
        if SHAPE_TREE_PART_PATTERN.match(name):
            cells = [(cell_text(b), bool(CELL_FILL.search(b))) for b in TC_BLOCK.findall(payload.decode("utf-8", "replace"))]
            if cells:
                out[name] = cells
    return out


def reset_injected_cell_fills(xml: str, before: list | None) -> tuple[str, int | None]:
    """재직렬화 전에 채움이 없던 셀에 soffice 가 넣은 단색 채움(표 스타일 강조색)만 흰색으로 되돌림.
    빌드가 쓴 채움은 팔레트 밖 색이어도 그대로 두어 check_layout 이 WARN 으로 알리게 함.
    셀은 부품 안 순서로 대응하며, 셀 글자 순서가 재직렬화 전과 다르면 대응을 확정할 수 없으므로 고치지 않고 None 을 반환"""
    blocks = TC_BLOCK.findall(xml)
    if not blocks:
        return xml, 0
    if before is None or [cell_text(b) for b in blocks] != [text for text, _ in before]:
        return xml, None
    had_fill = iter(fill for _, fill in before)
    count = 0

    def fix_cell(m):
        nonlocal count
        block = m.group(0)
        was_empty = not next(had_fill)
        fill = CELL_FILL.search(block)
        if not (was_empty and fill and fill.group("kind") == "solidFill"):
            return block
        count += 1
        return block[:fill.start("fill")] + WHITE_FILL + block[fill.end("fill"):]

    return TC_BLOCK.sub(fix_cell, xml), count


def restore_cell_fills(data: bytes, before: dict) -> bytes:
    fixed = []
    for name, payload in read_package(data):
        if SHAPE_TREE_PART_PATTERN.match(name):
            xml, count = reset_injected_cell_fills(payload.decode("utf-8", "replace"), before.get(name))
            if count is None:
                print(f"[finalize] 재직렬화 전후 표 셀 대응 실패로 셀 채움 유지: {name}")
            payload = xml.encode("utf-8")
        fixed.append((name, payload))
    return write_package(fixed)


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


def point_label(index: int, template: str, label: dict) -> str:
    """항목 1개의 데이터 레이블(c:dLbl). pos 가 none 이면 숨김, 그 밖은 template 서식에 위치와 이동 거리만 바꿔 기록"""
    if label["pos"] == LABEL_HIDDEN:
        return f'<c:dLbl><c:idx val="{index}"/><c:delete val="1"/></c:dLbl>'
    body = LABEL_LAYOUT_PATTERN.sub("", template)  # 이전 기록이나 soffice 가 남긴 이동 거리는 빌드 기록 값으로 교체
    if label["pos"]:
        tag = f'<c:dLblPos val="{label["pos"]}"/>'
        if LABEL_POSITION_PATTERN.search(body):
            body = LABEL_POSITION_PATTERN.sub(tag, body)
        else:  # 위치를 생략한 계열(묶은 막대)은 스키마 순서상 showLegendKey 앞에 위치를 넣음
            body = body.replace("<c:showLegendKey", tag + "<c:showLegendKey", 1)
    if label["x"] or label["y"]:  # 스키마 순서상 c:layout 은 idx 바로 뒤
        body = f'<c:layout><c:manualLayout><c:x val="{label["x"]}"/><c:y val="{label["y"]}"/></c:manualLayout></c:layout>' + body
    return f'<c:dLbl><c:idx val="{index}"/>{body}</c:dLbl>'


def set_series_labels(series_xml: str, positions: list) -> tuple[str, int]:
    """계열 1개(c:ser)의 레이블 묶음에 항목별 지정을 기록. 같은 항목의 기존 c:dLbl 은 그 서식을 바탕으로 교체

    WHY: 기존 c:dLbl 이 없으면 계열 서식(글꼴, 숫자 서식, 표시 항목)을 복사해야 지정하지 않은 속성이 계열과 같게 표시됨
    """
    found = SERIES_LABELS_PATTERN.search(series_xml)
    if not found:
        return series_xml, 0
    body = found.group(1)
    points = {int(m.group(1)): m for m in POINT_LABEL_PATTERN.finditer(body)}
    rest = POINT_LABEL_PATTERN.sub("", body)
    series_format = SERIES_ONLY_LABEL_PATTERN.sub("", rest)
    labels = {i: m.group(0) for i, m in points.items()}
    changed = 0
    for index, label in enumerate(positions):
        if label is None:
            continue
        template = points[index].group(2) if index in points else series_format
        labels[index] = point_label(index, template, label)
        changed += 1
    # 스키마 순서상 항목 레이블(c:dLbl)이 계열 서식보다 앞
    new_body = "".join(labels[i] for i in sorted(labels)) + rest
    return series_xml[:found.start(1)] + new_body + series_xml[found.end(1):], changed


def apply_chart_labels(xml: str, series_positions: list) -> tuple[str, int]:
    """차트 XML 의 계열을 문서 순서(storyboard series 순서)로 대응시켜 항목별 레이블 지정을 기록"""
    out, last, count = [], 0, 0
    for match, positions in zip(SERIES_PATTERN.finditer(xml), series_positions):
        fixed, changed = set_series_labels(match.group(0), positions or [])
        out.append(xml[last:match.start()] + fixed)
        last, count = match.end(), count + changed
    return "".join(out) + xml[last:], count


def apply_label_overrides(data: bytes, chart_labels: dict) -> tuple[bytes, int]:
    """빌드 기록의 계열 레이블 지정을 차트 부품에 기록. 지정이 없으면 패키지를 그대로 반환"""
    if not chart_labels:
        return data, 0
    fixed, total = [], 0
    for name, payload in read_package(data):
        series_positions = chart_labels.get(name[len(CHART_PART_DIR):]) if name.startswith(CHART_PART_DIR) else None
        if series_positions:
            xml, changed = apply_chart_labels(payload.decode("utf-8"), series_positions)
            payload, total = xml.encode("utf-8"), total + changed
        fixed.append((name, payload))
    return write_package(fixed), total


def valid_label(label) -> dict | None:
    """빌드 기록의 항목 지정 1개. 위치가 허용 값이고 이동 거리가 숫자이면 {pos, x, y}, 아니면 None"""
    if not isinstance(label, dict):
        return None
    pos, x, y = label.get("pos"), label.get("x", 0), label.get("y", 0)
    numbers = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (x, y))
    return {"pos": pos, "x": x, "y": y} if numbers and (pos is None or pos in LABEL_POSITIONS) else None


def record_chart_labels(pptx_path: Path) -> dict:
    """빌드 기록(<파일명>.build.json)의 계열 레이블 지정(chartLabels). 차트 파일 이름 -> 계열별 항목 지정 배열
    XML 에 넣을 수 없는 값은 지정 없음(None)으로 바꾸고 개수를 출력"""
    record = pptx_path.with_suffix(".build.json")
    if not record.is_file():
        return {}
    try:
        labels = json.loads(record.read_text(encoding="utf-8")).get("chartLabels") or {}
    except (OSError, ValueError):
        return {}
    if not isinstance(labels, dict):
        return {}
    out, dropped = {}, 0
    for part, series in labels.items():
        if not isinstance(series, list):
            continue
        out[part] = []
        for positions in series:
            positions = positions if isinstance(positions, list) else []
            valid = [valid_label(p) for p in positions]
            dropped += sum(1 for p, v in zip(positions, valid) if p is not None and v is None)
            out[part].append(valid)
    if dropped:
        print(f"[finalize] 계열 레이블 지정 {dropped}개는 허용 값({', '.join(LABEL_POSITIONS)})이 아니어서 무시")
    return out


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


def record_line_break(pptx_path: Path) -> str:
    """빌드 기록(<파일명>.build.json)의 줄바꿈 단위(meta.lineBreak). 기록이 없거나 정의되지 않은 값이면 기본값 word"""
    record = pptx_path.with_suffix(".build.json")
    if not record.is_file():
        return DEFAULT_LINE_BREAK
    try:
        mode = json.loads(record.read_text(encoding="utf-8")).get("lineBreak") or DEFAULT_LINE_BREAK
    except (OSError, ValueError):
        return DEFAULT_LINE_BREAK
    if not isinstance(mode, str) or mode not in LINE_BREAK_ATTRS:
        print(f"[finalize] 줄바꿈 단위 lineBreak={mode!r} 미정의로 기본값 {DEFAULT_LINE_BREAK} 적용")
        return DEFAULT_LINE_BREAK
    return mode


def finalize(pptx_path: Path, use_soffice: bool = True) -> dict:
    """입력 PPTX를 후처리하여 같은 경로에 덮어쓰고 처리 전후 수치를 반환"""
    RUN_LANGUAGE.update(record_language(pptx_path))
    LINE_BREAK["mode"] = record_line_break(pptx_path)
    before = inspect(pptx_path)
    print(format_metrics("처리 전", before))

    data = pptx_path.read_bytes()
    data, _ = normalize_package(data)
    data, _ = fix_package_xml(data)
    # 계열 레이블 지정은 재직렬화 전에 기록하고 재직렬화 후에 다시 기록 (soffice 는 원형 레이블의 이동 거리를 지우고 저장)
    chart_labels = record_chart_labels(pptx_path)
    data, labeled = apply_label_overrides(data, chart_labels)
    if labeled:
        print(f"[finalize] 차트 항목 레이블 지정 {labeled}개 기록 (빌드 기록 chartLabels)")
    pptx_path.write_bytes(data)

    reserialized = False
    if use_soffice:
        holes = capture_hole_sizes(data)  # soffice 재직렬화가 도넛 구멍 크기를 50 으로 되돌리므로 보존
        cell_fills = capture_cell_fills(data)  # soffice 재직렬화가 채움 없는 셀(병합으로 가려진 셀 등)에 표 스타일 강조색을 넣으므로 전 상태를 기록
        reserialized = reserialize_with_soffice(pptx_path)
        if reserialized:
            data = pptx_path.read_bytes()
            data, _ = normalize_package(data)
            data, _ = fix_package_xml(data)
            data = restore_hole_sizes(data, holes)
            data, _ = apply_label_overrides(data, chart_labels)
            data = restore_cell_fills(data, cell_fills)
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
