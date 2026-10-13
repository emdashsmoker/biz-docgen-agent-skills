# biz-docgen-agent-skills

[한국어](README.ko.md)

Agent Skills that typeset HWPX, DOCX and PPTX document files. Every skill ships as a Korean original and an English translation.

## Skills

- [`blockwriter`](skills/blockwriter/): Typesets a Markdown manuscript into an HWPX (Hangul) or DOCX report and reviews the pages by rendering.
- [`ieum-deck`](skills/ieum-deck/): Designs a planning or consulting deck as a storyboard.json and typesets it as an editable PPTX.
- [`juja-builder`](skills/juja-builder/): Writes proposals, pre-diagnosis reports and planning reports for research and policy service contracts, from the RFP to HWPX and DOCX files.

## Installation

Each skill folder holds the install packages and the source folders.

```
skills/juja-builder/
├── juja-builder-ko.skill    Korean install package
├── juja-builder-en.skill    English install package
├── ko/juja-builder/         Korean source
└── en/juja-builder/         English source
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

The skills come as they are, without any warranty. Correct operation in every environment is not guaranteed. The end user bears responsibility for using the skills and their output.

The HWPX writers were developed with reference to Hancom's published HWP document file (.hwp) specification. Hangul, Hancom Office and HWPX are trademarks of Hancom Inc. The skills in this repository have no affiliation with Hancom Inc.

## License

[AGPL-3.0-or-later](LICENSE). Copyright (C) 2026 Em Dash Smoker.

Each skill carries its own `LICENSE` and `NOTICE.md`. Under the output exception in `NOTICE.md`, the proposals, reports and decks you make with a skill are free of AGPL terms. Packages, fonts and programs that a skill installs at run time keep their own licenses.
