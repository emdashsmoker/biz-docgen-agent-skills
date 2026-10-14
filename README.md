# biz-docgen-agent-skills

Agent Skills that typeset HWPX, DOCX and PPTX document files. Every skill ships as a Korean original and an English translation.

HWPX, DOCX, PPTX 문서 파일을 직접 조판하는 에이전트 스킬 모음입니다. 모든 스킬은 한국어 원본과 영어 번역본을 함께 제공합니다.

<details>
<summary><b>English</b></summary>

## Skills

- [`blockwriter`](skills/blockwriter/): Typesets a Markdown manuscript into an HWPX (Hangul) or DOCX report and reviews the pages by rendering. [Samples](skills/blockwriter/demo/)
- [`ieum-deck`](skills/ieum-deck/): Designs a planning or consulting deck as a storyboard.json and typesets it as an editable PPTX. [Samples](skills/ieum-deck/demo/)
- [`juja-builder`](skills/juja-builder/): Writes proposals, pre-diagnosis reports and planning reports for research and policy service contracts, from the RFP to HWPX and DOCX files. [Samples](skills/juja-builder/demo/)

## Installation

Each skill folder holds the install packages, the source folders and sample pages.

```
skills/juja-builder/
├── juja-builder-ko.skill    Korean install package
├── juja-builder-en.skill    English install package
├── ko/juja-builder/         Korean source
├── en/juja-builder/         English source
└── demo/                    sample pages
```

- A `.skill` file is a zip archive of the skill folder. Where only `.zip` uploads are accepted, rename the extension to `.zip`.
- To install from source, copy the folder named after the skill (for example `ko/juja-builder/`) into your agent's skills folder.
- The Korean and English editions share one skill name, so only one of them can be installed at a time.

## Limitations

- Testing used Claude Opus 5.5 and Claude Fable 5.1. Results may differ with other models and environments.
- Testing did not cover every edge case, and some skills have had limited testing.
- Some skills may duplicate functions of other skills.
- The skills work through whole RFPs and manuscripts over many steps, so token use is high.
- The skills need a code execution environment, Python packages and a page review renderer (rhwp or LibreOffice). `ieum-deck` also uses Node.js.
- The page review renderers approximate the layout, so the review images may differ from the final layout in Hancom Office or Microsoft Word.
- Laws, public programs and methods in the skills reflect the time of writing.
- The English editions also produce documents that follow Korean public-sector conventions.

## Disclaimer

The skills come as they are, without any warranty. Correct operation in every environment is not guaranteed. The end user bears responsibility for using the skills and their output. The organizations in the demo pages are fictional.

The HWPX writers were developed with reference to Hancom's published HWP document file (.hwp) specification. Hangul, Hancom Office and HWPX are trademarks of Hancom Inc. The skills in this repository have no affiliation with Hancom Inc.

## License

[AGPL-3.0-or-later](LICENSE). Copyright (C) 2026 Em Dash Smoker.

Each skill carries its own `LICENSE` and `NOTICE.md`. Under the output exception in `NOTICE.md`, the proposals, reports and decks you make with a skill are free of AGPL terms. Packages, fonts and programs that a skill installs at run time keep their own licenses, listed in the skill's `NOTICE.md`.

</details>

<details>
<summary><b>한국어</b></summary>

## 스킬 목록

- [`blockwriter`](skills/blockwriter/): 마크다운 원고를 HWPX(한/글) 또는 DOCX 보고서로 조판하고 렌더링으로 검수합니다. [예시](skills/blockwriter/demo/)
- [`ieum-deck`](skills/ieum-deck/): 기획과 컨설팅 발표자료를 storyboard.json으로 설계해 편집 가능한 PPTX로 조판합니다. [예시](skills/ieum-deck/demo/)
- [`juja-builder`](skills/juja-builder/): 연구용역과 정책연구용역의 제안서, 사전진단보고서, 기획보고서를 RFP 입력부터 HWPX, DOCX 납품본까지 작성합니다. [예시](skills/juja-builder/demo/)

## 설치

스킬 폴더마다 설치용 패키지, 소스 폴더, 예시 쪽 이미지가 들어 있습니다.

```
skills/juja-builder/
├── juja-builder-ko.skill    한국어판 설치용 패키지
├── juja-builder-en.skill    영어판 설치용 패키지
├── ko/juja-builder/         한국어판 소스
├── en/juja-builder/         영어판 소스
└── demo/                    예시 쪽 이미지
```

- `.skill` 파일은 스킬 폴더를 묶은 zip 파일입니다. `.zip` 파일만 올릴 수 있는 환경에서는 확장자를 `.zip`으로 바꿔 업로드하면 됩니다.
- 소스로 설치할 때는 스킬 이름과 같은 폴더(예를 들어 `ko/juja-builder/`)를 에이전트의 스킬 폴더에 복사합니다.
- 한국어판과 영어판은 스킬 이름이 같아서 둘 중 하나만 설치할 수 있습니다.

## 한계

- 테스트는 Claude Opus 5.5와 Claude Fable 5.1에서 진행했습니다. 다른 모델과 실행 환경에서는 결과가 달라질 수 있습니다.
- 모든 예외 상황을 테스트하지는 못했습니다. 일부 스킬은 테스트가 충분하지 않습니다.
- 일부 스킬은 기능이 중복될 수 있습니다.
- 모든 스킬은 RFP와 원고 전체를 여러 단계에 걸쳐 다루므로 토큰 사용량이 많습니다.
- 모든 스킬은 코드 실행 환경, 파이썬 패키지, 페이지 검수용 렌더러(rhwp나 LibreOffice)가 있어야 작동합니다. `ieum-deck`은 Node.js도 씁니다.
- 페이지 검수용 렌더러는 배치를 근사해서 그리므로 검수 이미지가 한컴오피스나 Microsoft Word에서 연 최종 배치와 다를 수 있습니다.
- 스킬에 수록한 법령, 제도, 방법론은 작성 시점을 기준으로 합니다.
- 영어판도 한국 공공 문서 관행을 따르는 문서를 만듭니다.

## 면책 고지

이 저장소의 스킬은 어떠한 보증 없이 있는 그대로 제공합니다. 모든 환경에서 정상 작동을 보장하지 않습니다. 스킬 사용과 결과물에 대한 책임은 최종 사용자에게 있습니다. 예시 쪽 이미지에 나오는 기관은 모두 가상입니다.

본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다. 한/글, 한컴오피스, HWPX는 한글과컴퓨터의 상표입니다. 이 저장소의 스킬은 한글과컴퓨터와 제휴 관계가 없습니다.

## 라이선스

[AGPL-3.0-or-later](LICENSE)를 따릅니다. Copyright (C) 2026 Em Dash Smoker.

스킬마다 `LICENSE`와 `NOTICE.md`가 들어 있습니다. `NOTICE.md`의 출력물 예외 조항에 따라 스킬로 만든 제안서, 보고서, 발표자료는 AGPL 조건 없이 쓸 수 있습니다. 스킬이 실행 중에 설치하는 패키지, 글꼴, 프로그램은 각자의 라이선스를 따르며 그 목록은 스킬의 `NOTICE.md`에 있습니다.

</details>

## References

Thanks to the developers and contributors of these projects.

이 프로젝트들의 개발자와 기여자분들께 감사드립니다.

- [rhwp](https://github.com/edwardkim/rhwp)
- [python-hwpx](https://github.com/airmang/python-hwpx)
- [python-docx](https://github.com/python-openxml/python-docx)
- [python-pptx](https://github.com/scanny/python-pptx)
- [PptxGenJS](https://github.com/gitbrent/PptxGenJS)
- [LibreOffice](https://www.libreoffice.org/)
- [H2Orestart](https://github.com/ebandal/H2Orestart)
- [Poppler](https://poppler.freedesktop.org/)
- [Nanum fonts](https://hangeul.naver.com/font)
