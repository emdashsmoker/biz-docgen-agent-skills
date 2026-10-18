# 외부 의존 요소

스킬은 렌더러와 글꼴을 포함하지 않으며 실행 환경에 설치된 렌더러와 글꼴을 찾아 쓴다.

## HWPX 렌더러 확보 순서

rhwp 릴리스 바이너리가 1순위, rhwp 소스 빌드가 2순위, LibreOffice와 H2Orestart가 3순위다. 앞 순위 절차를 실제로 수행하고 실패한 경우에만 다음 순위로 이동한다.

실행 환경에 따라 GitHub의 웹 화면 경로(`releases/latest`, `releases/expanded_assets`, `api.github.com`)는 403이어도 파일 전달 경로(`releases/download/<태그>/<파일명>`)와 git 프로토콜은 통과할 수 있다. 1순위 실패는 4단계(파일 수신)의 실패로 판정한다.

1순위 rhwp 릴리스 바이너리 (https://github.com/edwardkim/rhwp)

rhwp는 명령 체계와 배포 방식이 자주 바뀌는 프로젝트이므로 확보할 때마다 릴리스 상태를 확인한다.

1. `rhwp --version` 실행 또는 scripts/rhwp/rhwp 존재 확인. 있으면 6단계로 이동
2. 태그는 `git ls-remote --tags --refs https://github.com/edwardkim/rhwp` 출력의 버전 태그 중 최고 버전으로 정함. git 접근이 막힌 경우에만 releases/latest 리다이렉트의 최종 URL 끝에서 취득. 릴리스 페이지 HTML은 자산 목록을 늦게 불러오므로 태그와 자산 판단에 쓰지 않음
3. 자산 목록은 `https://github.com/edwardkim/rhwp/releases/download/<태그>/SHA256SUMS.txt`를 `curl -fL`로 받아 파일명 열에서 취득. 이 파일이 없으면 `releases/expanded_assets/<태그>`, GitHub API `/repos/edwardkim/rhwp/releases/tags/<태그>` 순으로 시도. 자산 목록의 실제 파일명에서 현재 플랫폼(OS, CPU)에 맞는 자산을 선택
    - 최고 버전 태그에 릴리스가 없으면(SHA256SUMS.txt 404) 다음 버전 태그로 내려가서 다시 시도
4. 자산을 `https://github.com/edwardkim/rhwp/releases/download/<태그>/<파일명>`에서 `curl -fL`로 수신. SHA256SUMS.txt가 있으면 `sha256sum -c`로 대조하고 불일치하면 확보를 중단
5. 압축을 풀고 실행 파일에 실행 권한을 준 뒤 `--version` 확인. scripts/rhwp/에 두거나 `--rhwp 경로`로 지정. render는 scripts/rhwp/rhwp, PATH, ~/.local/bin/rhwp 순으로 자동 탐색
6. `rhwp --help`로 현재 버전의 명령 체계를 확인. 명령 이름은 버전마다 바뀔 수 있으므로 기능 기준으로 탐색
    - 필요한 기능은 PDF 출력, 기대 조건 검증, 글자 윤곽선 출력 옵션, 글꼴 폴더 지정 옵션. 현재 설정값은 scripts/config.py의 RHWP_PDF_COMMAND(export-pdf), RHWP_VERIFY_COMMAND(verify), RHWP_PDF_OUTLINE_FLAG(--text-as-paths), RHWP_FONT_PATH_FLAG(--font-path)
    - 같은 이름이 없으면 도움말에서 같은 기능의 명령이나 옵션을 찾고 해당 명령의 `--help`로 인자 형식을 확인
    - 대체 명령을 찾으면 config.py의 값을 교체. 인자 형식이 다르면 render.py의 to_pdf와 rhwp_verify 호출부도 수정
    - 같은 기능이 어디에도 없을 때에만 해당 기능을 생략하고 생략 사유를 최종 보고에 기재

2순위 rhwp 소스 빌드

릴리스 파일 수신이 403이나 저장소 접근 거부로 막혀도 git 프로토콜은 통과하는 환경이 있으므로 3순위로 가기 전에 소스 빌드를 시도한다.

1. rhwp 저장소를 `git clone` 한 뒤 클론한 저장소를 직접 살펴 빌드 방법을 판단
2. rhwp는 빌드 방식도 자주 바뀌므로 저장소의 빌드 설정, 워크스페이스 구성, 툴체인 지정, CI 설정, 개발 문서를 읽고 그 시점의 방법을 따름
3. CLI 바이너리 타깃과 PDF 내보내기 기능이 어느 타깃에 있는지 확인한 뒤 그 타깃만 빌드
4. 빌드 시간을 줄이는 프로파일이나 기능 조합이 있으면 선택. 검수용 바이너리이므로 최적화 수준보다 완료 시간을 우선
5. 산출 바이너리를 scripts/rhwp/rhwp에 두고 1순위 5단계와 6단계의 `--version`, `--help` 확인을 똑같이 수행한 뒤 render로 동작 확인
6. 클론 용량이 수 GB에 이를 수 있으므로 착수 전 여유 디스크를 확인. 빌드 후 클론 폴더는 삭제해도 무방
7. git 접근도 막히거나 빌드가 실패하면 3순위로 이동하고 실패한 단계를 최종 보고에 기재

3순위 LibreOffice와 H2Orestart

1순위와 2순위가 모두 실패한 경우에만 사용하고 폴백 사유(순위별 실패 단계)를 최종 보고에 기재한다.

1. Debian 계열은 `apt-get update` 후 `apt-get install -y --no-install-recommends libreoffice-writer libreoffice-java-common default-jre-headless libreoffice-h2orestart python3-uno fonts-nanum poppler-utils`
2. 다른 운영체제는 LibreOffice 공식 배포판을 설치하고 H2Orestart 확장(https://extensions.libreoffice.org/en/extensions/show/27504)을 확장 관리자 또는 `unopkg add`로 등록
3. `unopkg list --shared`(또는 `unopkg list`)에서 H2Orestart 등록 확인
4. `render 문서.hwpx --engine soffice`로 변환. render는 전용 사용자 프로필과 ASCII 임시 파일명을 자동 적용

- 세 순위 모두 실패하면 render와 `check --expect`를 생략하고 최종 보고에 사유 기재
- 변환 실패는 문서 결함 신호일 수 있으므로 check 결과와 교차 확인
- H2Orestart는 rhwp보다 엄격하여 요소 순서와 참조 ID 결함을 추가로 드러냄

## DOCX 렌더러

- DOCX는 항상 LibreOffice로 렌더링. 설치는 위 3순위 1-2단계에서 H2Orestart를 제외한 구성
- LibreOffice 파이썬 연동(uno)이 있으면 문서를 연 뒤 목차와 필드를 갱신하고 PDF로 저장. 현재 파이썬, LibreOffice 동봉 파이썬, /usr/bin/python3 순으로 uno를 찾음
- uno가 없으면 필드 갱신 없이 변환하고 경고. 이때 목차는 문서에 저장된 값으로 보임
- pdftoppm(poppler-utils)이 없으면 render는 PDF까지만 산출

## render 명령의 동작

- (산출물) 원본 옆에 `문서.pdf`와 `문서_pages/p-N.png`(기본 80dpi, `--dpi`로 변경). 원본 폴더가 읽기 전용이면 현재 작업 폴더에 저장
- (쪽 PNG 이름) N은 쪽번호이며 쪽 수의 자릿수에 맞춰 앞자리를 0으로 채움 (10쪽 이상이면 p-01.png)
- (산출 폴더) `--outdir`를 주면 PDF와 쪽 PNG(p-N.png)를 하위 폴더 없이 그 폴더에 저장. 렌더링에 쓰는 사본(HWPX 검수 사본, DOCX는 원본 복사본)과 LibreOffice 변환 폴더도 그 폴더에서 만들었다가 지움. 납품 폴더의 문서를 렌더링할 때 검수 파일이 납품 폴더에 섞이지 않게 지정. render는 그 폴더의 기존 쪽 PNG만 지운 뒤 새로 저장
- (이름 겹침) PDF와 PNG 폴더는 원본 이름을 씀. 같은 문서를 두 엔진으로 렌더링하거나 이름이 같은 HWPX와 DOCX를 렌더링하면 뒤 결과가 앞 결과를 덮어쓰므로 렌더링마다 다른 `--outdir`를 지정
- HWPX `--engine auto`는 rhwp가 있으면 rhwp, 없으면 LibreOffice와 H2Orestart
- HWPX는 검수 전용 사본(`_render_copy_*.hwpx`, 이름마다 고유 접미사)을 만들어 렌더링하고 렌더링 후 사본을 지움. 납품 파일은 바뀌지 않음
    - 소프트 하이픈(U+00AD)을 하이픈으로 치환. 근사 렌더러가 U+00AD를 그리지 않아 유저 양식의 하이픈 글머리가 빈칸으로 보이는 현상을 막음. 글머리 정의(header.xml)에서는 글머리 기호만, 본문(section*.xml)에서는 모든 U+00AD를 치환. 치환 글리프는 config.py의 SOFT_HYPHEN_GLYPH
    - soffice 엔진일 때만 본문 중간의 번호 새로 시작 컨트롤을 제거
    - `--keep-soft-hyphen`이면 원본 내용을 바꾸지 않고 렌더링. 소프트 하이픈 치환과 번호 새로 시작 컨트롤 제거를 모두 생략
- rhwp 검수 PDF는 글꼴이 없는 환경에서도 모양이 유지되도록 글자를 윤곽선으로 출력. 목차 쪽번호 산정은 글자 추출이 필요하므로 윤곽선 옵션 없이 렌더링
- `fonts --setup`으로 만든 대체 글꼴 폴더가 있으면 rhwp에 글꼴 폴더 옵션으로 전달

## 렌더러 한계

rhwp와 H2Orestart는 한/글을, LibreOffice는 Word를 독립적으로 근사하는 렌더러다. 렌더러는 버전마다 배치와 기능이 바뀌므로 렌더러별 동작을 목록으로 두지 않고 아래 방법으로 판정한다. 조판의 최종 확정은 유저가 한/글이나 Word에서 확인한 결과를 기준으로 하며 최종 보고에 이 사실을 1줄 고지한다.

판정 방법

1. 렌더 PNG에서 규범과 다른 모양을 찾으면 해당 요소의 값을 문서 XML에서 확인. HWPX는 Contents/header.xml과 section*.xml, DOCX는 word/styles.xml과 document.xml
2. XML 값이 references/layout.md의 규범과 맞으면 렌더러 차이로 보고 결함에서 제외
3. XML 값이 규범과 다르면 결함으로 판정하고 원고, 규범(config.py, form.py), 조판 코드 순으로 원인을 찾음
4. XML 값만으로 판단하기 어려운 배치(줄바꿈 위치, 겹침, 쪽 경계)는 HWPX에서 rhwp 렌더와 `--engine soffice` 렌더를 대조. 두 렌더에서 같게 나타나면 결함 후보로 보고 3번 순서로 원인을 찾으며 한쪽에서만 나타나면 렌더러 차이로 봄. 렌더러가 하나뿐인 경우(DOCX, HWPX 폴백)는 XML 값으로 판정

판정 제외 항목 (모든 렌더러)

- 머리말의 세로 위치, 표 행 높이 눌림, 장표 분할 위치와 제목 행 반복, 글꼴 대체에 따른 줄바꿈 위치
- 자동번호와 필드로 계산되는 번호(캡션 번호, 쪽번호)의 표시. 번호는 XML의 자동번호와 필드로 확인하며 한/글과 Word가 계산함

확인된 사례 (rhwp v0.8.6, H2Orestart 0.6.1 기준 예시, 버전 업데이트 시 동작 변동 가능)

- rhwp는 다음 문단과 같은 쪽에 두는 설정을 반영하지 않아 제목이나 □가 쪽 끝에 남을 수 있음. 목차 항목 제목이면 build가 `[목차 제목 고립]` WARN으로 알림
- H2Orestart는 표와 그림의 캡션 개체, 각주 본문, 꼬리말 쪽번호를 그리지 않음. 이 요소는 rhwp 렌더와 XML로 확인

## 글꼴

내장 양식은 네이버가 SIL Open Font License 1.1로 배포하는 나눔고딕을 쓰고 flat 제목에만 나눔바른고딕을 쓴다. 역할별 글꼴은 references/layout.md의 내장 양식 표에 있다. 문서에는 글꼴 이름을 그대로 기록한다. 대체 글꼴은 글꼴이 설치되지 않은 환경의 검수 렌더링에만 쓴다.

| 양식 글꼴 | 확보 경로 | 렌더링 대체 글꼴 |
|------|------|------|
| 나눔고딕 | 한자가 든 네이버 배포본은 공유마당 안심글꼴 또는 운영체제 패키지(fonts-nanum). `fonts --setup`은 한자 없는 Google Fonts 배포본을 내려받음 | 없음 |
| 나눔바른고딕 | 네이버 배포본을 공유마당 안심글꼴 또는 운영체제 패키지(fonts-nanum)로 설치. Google Fonts 저장소에 없어 자동으로 내려받지 않음 | 나눔고딕 |

- 두 글꼴 모두 한국저작권위원회 공유마당의 안심글꼴에 OFL 글꼴로 등록되어 있음 (https://gongu.copyright.or.kr/gongu/wrt/wrt/view.do?wrtSn=13288238&menuNo=200023, https://gongu.copyright.or.kr/gongu/wrt/wrt/view.do?wrtSn=13288242&menuNo=200023)
- OFL 1.1은 저작권 고지와 라이선스를 함께 두는 조건으로 소프트웨어와의 묶음 배포를 허용하며 글꼴 파일만 따로 판매하는 행위는 허용하지 않음 (https://openfontlicense.org/open-font-license-official-text/). `fonts --setup`은 글꼴 파일과 함께 OFL.txt를 내려받아 둠
- 네이버 배포본(fonts-nanum 패키지 포함)은 두 글꼴의 모든 굵기에 KS X 1001 한자 4,620자와 호환 한자 268자의 글자 모양을 담음. Google Fonts 저장소의 나눔고딕은 한자가 없음
- 한자가 든 문서를 한/글이나 Word로 열 컴퓨터에는 두 글꼴의 네이버 배포본을 설치. 한자가 없는 배포본이 깔려 있으면 한자 표시는 각 프로그램의 대체 글꼴 처리를 따름
- 검수 렌더링 환경의 나눔고딕이 Google 배포본이면 한자가 렌더러가 고른 다른 글꼴로 찍힘. 한자 모양의 최종 확인은 네이버 배포본이 설치된 한/글 또는 Word에서 수행
- 계위 기호 □, ○, -, ㆍ, ※는 두 글꼴의 모든 굵기에 글자 모양이 있음. 셀 글머리 기호 ◦는 두 글꼴의 보통과 굵게 파일에 있음

유저 컴퓨터 글꼴 설치

문서를 한/글이나 Word로 여는 컴퓨터에 아래 순서로 네이버 배포본을 설치한다. 나눔고딕은 항상 설치하고 flat 양식 문서가 있으면 나눔바른고딕도 설치한다.

1. 공유마당 안심글꼴의 나눔고딕 페이지(https://gongu.copyright.or.kr/gongu/wrt/wrt/view.do?wrtSn=13288238&menuNo=200023)와 나눔바른고딕 페이지(https://gongu.copyright.or.kr/gongu/wrt/wrt/view.do?wrtSn=13288242&menuNo=200023)에서 '공유저작물 다운로드'로 zip 파일을 받음. 처음 한 번 짧은 설문이 뜸
2. Google Fonts에서 받은 나눔고딕을 설치한 적이 있으면 먼저 제거. 이 배포본은 한자가 없고 글꼴 이름이 같아 어느 쪽이 쓰일지 알 수 없음
3. zip 파일의 압축을 풀고 운영체제별로 설치
    - (Windows) 글꼴 파일(.ttf 또는 .otf)을 모두 선택하고 마우스 오른쪽 메뉴에서 '모든 사용자용으로 설치'. 관리자 권한이 없으면 '설치'
    - (macOS) 글꼴 파일을 더블클릭하여 서체 관리자에서 설치
    - (Linux) 운영체제 패키지(Debian 계열은 fonts-nanum)를 설치하거나 글꼴 파일을 `~/.local/share/fonts/`에 복사한 뒤 `fc-cache -f` 실행
4. 열려 있는 한/글과 Word를 모두 닫았다가 다시 열기
5. 글꼴 목록에서 나눔고딕과 나눔바른고딕을 확인. Windows에서 목록에 없으면 '모든 사용자용으로 설치'로 다시 설치

유저 양식의 글꼴

유저 양식에 흔한 Windows와 한컴오피스 글꼴은 설치되지 않은 환경에서 아래 대체 글꼴로 검수 렌더링한다.

| 유저 양식 글꼴 | 확보 경로 | 렌더링 대체 글꼴 |
|------|------|------|
| 맑은 고딕, 돋움, 굴림 | Windows 기본 글꼴 | 나눔고딕 |
| 바탕 | Windows 기본 글꼴 | 나눔명조 |
| Arial | Windows 기본 글꼴 | Liberation Sans |
| 휴먼명조, 한양신명조, 명조, HCI Poppy | 한컴오피스 동봉 글꼴 | 나눔명조 |
| 한컴돋움, 한양중고딕, HCI Hollyhock | 한컴오피스 동봉 글꼴 | 나눔고딕 |
| HY헤드라인M | 한컴오피스 동봉 글꼴 | 나눔고딕 ExtraBold |
| 함초롬바탕 | 한컴오피스 동봉, 한컴 공식 무료 배포 | 나눔명조 |
| 함초롬돋움 | 한컴오피스 동봉, 한컴 공식 무료 배포 | 나눔고딕 |

- Windows 기본 글꼴은 다른 컴퓨터로 복사하거나 재배포할 수 없음 (https://learn.microsoft.com/en-us/typography/fonts/font-faq)
- 한컴오피스 동봉 글꼴의 사용 허용 범위는 한컴오피스 안의 문서 작성이며 다른 프로그램에서의 글꼴 파일 사용은 이 범위에 들지 않음 (https://www.hancom.com/news/notice/detail/6117)
- 위 두 종류는 스킬이 내려받거나 복사하지 않음. 해당 프로그램이 설치된 환경에서 쓰거나 유저가 직접 확보
- 휴먼명조는 한컴 전용 HFT 파일과 Windows TTF 파일이 따로 있고 이름이 같으면 TTF를 먼저 불러오므로 환경에 따라 모양이 다를 수 있음 (https://www.hancom.com/support/faqCenter/faq/detail/2680)

fonts 명령

- (`fonts`) 내장 양식 글꼴마다 설치 여부, KS X 1001 한자 4,620자 포함 여부, 렌더링 대체 글꼴, 확보 경로를 출력
    - 설치 글꼴은 fontconfig가 있으면 fontconfig가 고르는 파일로, 없으면(보통 Windows와 macOS) 운영체제 글꼴 폴더에서 가족 이름이 같은 파일로 찾음. Windows는 모든 사용자용과 사용자별 설치 폴더를 모두 봄
    - 한자 포함 여부는 찾은 파일(같은 이름이 여럿이면 보통 굵기 파일)에서 한자마다 문자 코드와 글자 모양이 모두 있는지로 판정. 코드만 있고 모양이 빈 글꼴도 빠짐으로 표시
    - 설치되지 않은 글꼴의 한자 칸과 설치된 글꼴의 대체 글꼴 칸은 `-`. 글꼴을 찾을 방법이 없으면(fontconfig와 fonttools가 모두 없는 등) 설치 여부와 한자 칸을 `?`로 표시
    - 결과는 명령을 실행한 컴퓨터의 상태. 원격 작업 공간에서 실행한 결과는 검수 렌더링 환경의 상태만 보여 줌
- (`fonts --setup`) 설치되지 않은 나눔고딕과 나눔명조를 라이선스 파일(OFL.txt)과 함께 `~/.local/share/fonts/blockwriter/`에 내려받음. 나눔명조는 유저 양식의 명조 계열 글꼴을 대신하는 렌더링용. 이어서 설치되지 않은 글꼴 이름만 대체 글꼴로 잇는 fontconfig 규칙을 `~/.config/fontconfig/conf.d/60-blockwriter.conf`에 기록하고 `fc-cache` 실행. 대체 글꼴이 나눔고딕 ExtraBold인 글꼴(HY헤드라인M)은 굵기까지 지정
- 내려받기가 막힌 환경은 운영체제 패키지(예 fonts-nanum, fonts-liberation)로 대체 가능
- fontconfig(fc-list)가 없는 환경(보통 Windows와 macOS)은 규칙 기록을 생략. 한/글과 Word는 설치된 글꼴을 사용
- DOCX는 글꼴 표에 영문 이름, 한글 문자 집합, 계열을 기록하여 Word가 양식 글꼴이 없을 때 같은 계열의 글꼴을 고르게 함 (references/layout.md의 DOCX 대응 규칙)
