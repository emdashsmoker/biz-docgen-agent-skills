# Notice

ieum-deck
Copyright (C) 2026 Em Dash Smoker

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program in the file LICENSE. If not, see <https://www.gnu.org/licenses/>.

SPDX-License-Identifier: AGPL-3.0-or-later

## Output exception

As an additional permission under section 7 of the GNU Affero General Public License version 3, the copyright holder grants the following.

Files that this program produces when you run it, such as documents, slides, spreadsheets, charts, images, audio and data (the "Output"), are not covered by the GNU Affero General Public License. This applies even when the Output contains text, templates, layouts, styles or other material taken from this program.

This permission covers the Output only. The program itself, including its instructions, references, scripts and templates, remains under AGPL-3.0-or-later.

If you modify this program, you may extend this permission to your version, but you are not obligated to do so. If you do not wish to do so, delete this permission from your version.

## Third-party software

This program bundles no third-party code, fonts or binaries. The components below are installed or downloaded at run time. They are not part of this program and keep their own licenses.

| Component | Use | License |
|---|---|---|
| [PptxGenJS](https://github.com/gitbrent/PptxGenJS) and its npm dependencies | PPTX writing | MIT, ISC, (MIT OR GPL-3.0-or-later) for JSZip, (MIT AND Zlib) for pako |
| [python-pptx](https://github.com/scanny/python-pptx) | PPTX reading and layout checks | MIT |
| [python-hwpx](https://github.com/airmang/python-hwpx) | HWPX input reading | Apache-2.0 |
| [pyhwp](https://github.com/mete0r/pyhwp) | HWP 5.0 input reading | AGPL-3.0-or-later |
| [python-docx](https://github.com/python-openxml/python-docx) | DOCX input reading | MIT |
| [MarkItDown](https://github.com/microsoft/markitdown) | Input conversion to Markdown | MIT |
| [pdfplumber](https://github.com/jsvine/pdfplumber) | PDF text and table extraction | MIT |
| [pypdf](https://github.com/py-pdf/pypdf) | PDF image extraction | BSD-3-Clause |
| [lxml](https://lxml.de/) | XML processing | BSD-3-Clause |
| [Pillow](https://python-pillow.org/) | Image processing | MIT-CMU |
| [NumPy](https://numpy.org/) | Image comparison | BSD-3-Clause |
| [rhwp](https://github.com/edwardkim/rhwp) | HWPX page rendering for review | MIT |
| [LibreOffice](https://www.libreoffice.org/) | Document conversion and page rendering | MPL-2.0 |
| [H2Orestart](https://github.com/ebandal/H2Orestart) | HWP and HWPX import for LibreOffice | GPL-3.0 |
| [Poppler](https://poppler.freedesktop.org/) (pdftoppm) | PDF page images | GPL-2.0 or GPL-3.0 |
| [Nanum fonts](https://hangeul.naver.com/font) by NAVER | Rendering and layout fonts | OFL-1.1 |

`assets/font-metrics.json` holds glyph advance widths measured from NanumGothic (NAVER, SIL Open Font License 1.1). It contains no font data.
