# External dependencies

> Translated from the Korean original (blockwriter). When results differ, the Korean version is the reference.

The skill does not bundle renderers or fonts. It locates and uses the renderers and fonts installed in the execution environment.

The timing of obtaining renderers and running render tests follows the start order in the Setup section of SKILL.md (before the planning questions).

Two parts come from GitHub: rhwp (owner `edwardkim`, repository name `rhwp`) and the fallback fonts of `fonts --setup` (owner `google`, repository name `fonts`). If the execution environment has a tool that attaches a GitHub repository to the session, call it with the matching repository before each part's first GitHub access. Pass the owner and the repository name as separate values. Apply any access route the tool's reply names to the later steps. Skip this step when no such tool exists or the call is refused.

## Order for obtaining an HWPX renderer

The rhwp release binary is first, an rhwp source build is second, and LibreOffice with H2Orestart is third. Move to the next option only after actually running the previous procedure and failing. A permission denial by the execution environment follows Permission denial handling below.

Run a render test right after obtaining a renderer at any rank. After font preparation (`fonts --setup`), put a one-line manuscript reading `안녕하세요!` in a temporary folder outside the output folder and typeset it with `build test.md render-test.hwpx --profile flat`. Then render it with `render render-test.hwpx --engine rhwp` (`--engine soffice` for the third rank) and open the page PNG (the PDF when poppler is missing) to check that `안녕하세요!` is visible. rhwp writes a PDF without the text when the document's fonts are missing, and render still reports success, so a produced PDF alone is not a pass. If the page is blank, check the fonts with `fonts` first. If the page stays blank with the fonts in place, count that rank as failed even though the renderer was obtained, and move to the next rank. Catching renderer problems before writing keeps the review step from breaking off the work.

Depending on the environment, GitHub's web page paths (`releases/latest`, `releases/expanded_assets`, `api.github.com`) may return 403 while the file delivery path (`releases/download/<tag>/<file name>`) and the git protocol still work. Option 1 counts as failed when step 4 (file download) fails.

Permission denial handling

The permission check of the execution environment (tool approval, automatic approval decisions, and similar) can refuse a command that downloads or runs outside code before the command runs. Such a refusal signals that the execution environment wants the user's confirmation, so the user decides whether to allow it.

- (Judgment) A permission denial is a refusal response from the execution environment without the command running. A 403, a connection error, or a repository access denial after the command ran is a network failure and follows the option order rule above
- (Commands covered) rhwp tag lookup, download, clone, build, and run commands
- (Stop retrying) Stop trying to get the same rhwp code through another route. Other routes include the option 2 source build and other download tools
- (User question) When a denial occurs, stop obtaining rhwp. Then ask the user whether to allow downloading and running rhwp. Do not move on to option 3 before the answer. When to ask and what to present follow rhwp permission denial in the Setup section of SKILL.md and the rhwp permission item of step 1
- (After the answer) If the user allows it, obtain rhwp again from option 1. If the user does not allow it or does not answer, run the render test with option 3 without option 2

Option 1 rhwp release binary (https://github.com/edwardkim/rhwp)

rhwp changes its command set and distribution often, so check the release state every time it is obtained.

1. Run `rhwp --version` or check that scripts/rhwp/rhwp exists. If it exists, go to step 6
2. Take the tag as the highest version among the version tags printed by `git ls-remote --tags --refs https://github.com/edwardkim/rhwp`. Only if git access is blocked, take it from the end of the final URL of the releases/latest redirect. The release page HTML loads the asset list late, so it is not used to decide the tag or the assets
3. Get the asset list by downloading `https://github.com/edwardkim/rhwp/releases/download/<tag>/SHA256SUMS.txt` with `curl -fL` and reading the file name column. If that file does not exist, try `releases/expanded_assets/<tag>` and then the GitHub API `/repos/edwardkim/rhwp/releases/tags/<tag>`. Pick the asset for the current platform (OS, CPU) from the actual file names in the asset list
    - If the highest version tag has no release (SHA256SUMS.txt returns 404), go down to the next version tag and try again
4. Download the asset from `https://github.com/edwardkim/rhwp/releases/download/<tag>/<file name>` with `curl -fL`. If SHA256SUMS.txt exists, verify the file with `sha256sum -c` and stop if it does not match
5. Extract it, make the executable runnable, and check `--version`. Put it in scripts/rhwp/ or pass `--rhwp path`. render searches scripts/rhwp/rhwp, PATH, and ~/.local/bin/rhwp in that order
6. Check the current command set with `rhwp --help`. Command names can change between versions, so search by function
    - The functions needed are PDF export, expectation checking, a glyph-outline output option, and a font folder option. The current values in scripts/config.py are RHWP_PDF_COMMAND (export-pdf), RHWP_VERIFY_COMMAND (verify), RHWP_PDF_OUTLINE_FLAG (--text-as-paths), and RHWP_FONT_PATH_FLAG (--font-path)
    - If a name is missing, find the command or option with the same function in the help and check its argument format with that command's `--help`
    - If a replacement is found, replace the value in config.py. If the argument format differs, also update the to_pdf and rhwp_verify calls in render.py
    - Only when the function exists nowhere, skip it and state the reason in the final report

Option 2 rhwp source build

Some environments block release file downloads with 403 or repository access denial but still allow the git protocol, so try a source build before option 3.

1. `git clone` the rhwp repository and inspect the cloned repository to decide how to build it
2. rhwp also changes its build method often, so read the repository's build settings, workspace layout, toolchain specification, CI settings, and developer documents, and follow the method current at that time
3. Find which target holds the CLI binary and the PDF export function, and build only that target
4. If a profile or feature combination shortens the build, choose it. This is a review binary, so completion time comes before optimization level
5. Put the resulting binary at scripts/rhwp/rhwp, run the same `--version` and `--help` checks as option 1 steps 5 and 6, then confirm it works with render
6. The clone can reach several GB, so check free disk space before starting. The clone folder can be deleted after the build
7. If git access is also blocked or the build fails, move to option 3 and state the failed step in the final report

Option 3 LibreOffice and H2Orestart

Use this when options 1 and 2 both fail or when Permission denial handling points to option 3. State the fallback reason (the failed step of each option or the refused command) in the final report.

1. On Debian-based systems, run `apt-get update`, then `apt-get install -y --no-install-recommends libreoffice-writer libreoffice-java-common default-jre-headless libreoffice-h2orestart python3-uno fonts-nanum poppler-utils`
2. On other operating systems, install the official LibreOffice distribution and register the H2Orestart extension (https://extensions.libreoffice.org/en/extensions/show/27504) with the Extension Manager or `unopkg add`
3. Confirm that H2Orestart is registered in `unopkg list --shared` (or `unopkg list`)
4. Convert with `render document.hwpx --engine soffice`. render applies a dedicated user profile and an ASCII temporary file name automatically

- If all three options fail, skip render and `check --expect`. State this and the reason in the planning question turn and again in the final report
- A conversion failure can signal a document defect, so cross-check it with the check results
- H2Orestart is stricter than rhwp and also exposes element order and reference ID defects

## DOCX renderer

- DOCX is always rendered with LibreOffice. Install it as in option 3 steps 1-2 without H2Orestart
- Run a render test after installing LibreOffice and preparing the fonts (`fonts --setup`). Put the same one-line `안녕하세요!` manuscript as the HWPX render test in a temporary folder outside the output folder and typeset it with `build test.md render-test.docx --profile flat`. Then render it with `render render-test.docx --outdir <temporary folder>/docx` and check that `안녕하세요!` is visible in the page PNG (the PDF when poppler is missing). The separate `--outdir` keeps its PDF name from clashing with the HWPX render test
- If the text is not visible, check the fonts with `fonts`. If the problem cannot be solved, skip the DOCX rendering review and state this and the reason in the planning question turn
- If the LibreOffice Python bridge (uno) is available, render opens the document, updates the TOC and fields, and saves it as PDF. uno is searched in the current Python, the Python bundled with LibreOffice, and /usr/bin/python3 in that order
- Without uno, render converts the document without updating fields and prints a warning. The TOC then shows the values stored in the document
- Without pdftoppm (poppler-utils), render produces only the PDF

## How render works

- (Outputs) `document.pdf` and `document_pages/p-N.png` next to the source (80dpi by default, change with `--dpi`). If the source folder is read-only, they are saved in the current working folder
- (Page PNG names) N is the page number, padded with leading zeros to the digit count of the page total (p-01.png for 10 or more pages)
- (Output folder) With `--outdir`, the PDF and page PNGs (p-N.png) are saved directly in that folder, with no subfolder. The copy used for rendering (the HWPX review copy, or a plain copy of a DOCX) and the LibreOffice conversion folder are also made in that folder and removed afterwards. Use it when rendering a document in the delivery folder so review files do not mix into the delivery folder. render deletes only the existing page PNGs in that folder before saving
- (Name clash) The PDF and the PNG folder use the original's name. Rendering the same document with two engines, or rendering an HWPX and a DOCX with the same name, overwrites the earlier result, so give each render a different `--outdir`
- For HWPX, `--engine auto` uses rhwp if available, otherwise LibreOffice with H2Orestart
- For HWPX, render creates a review-only copy (`_render_copy_*.hwpx`, with a unique suffix per copy), renders it, and deletes it afterward. The delivered file does not change
    - Soft hyphens (U+00AD) are replaced with hyphens. The approximate renderers do not draw U+00AD, so this keeps the hyphen bullets of user forms from showing as blanks. In the bullet definitions (header.xml) only the bullet symbols are replaced, and in the body (section*.xml) every U+00AD is replaced. The replacement glyph is SOFT_HYPHEN_GLYPH in config.py
    - Only for the soffice engine, number-restart controls in the middle of the body are removed
    - With `--keep-soft-hyphen`, render renders the original content unchanged. Both the soft hyphen replacement and the number-restart control removal are skipped
- rhwp review PDFs draw glyphs as outlines so the appearance holds even where fonts are missing. TOC page-number calculation needs text extraction, so it renders without the outline option
- If the substitute font folder created by `fonts --setup` exists, it is passed to rhwp with the font folder option

## Renderer limits

rhwp and H2Orestart approximate Hangul, and LibreOffice approximates Word, as independent implementations. Renderers change their layout and features from version to version, so renderer behaviors are not kept as a list; judge with the method below. The final typesetting is confirmed by what the user sees in Hangul or Word, and the final report states this in one line.

Judgment method

1. When the page PNG shows something that differs from the norms, check the value of that element in the document XML: Contents/header.xml and section*.xml for HWPX, word/styles.xml and document.xml for DOCX
2. If the XML value matches the norms in references/layout.md, treat it as a renderer difference and do not count it as a defect
3. If the XML value differs from the norms, judge it a defect and look for the cause in the manuscript, then the norms (config.py, form.py), then the typesetting code
4. For layout that the XML values alone cannot settle (line break positions, overlaps, page boundaries), compare the rhwp render with the `--engine soffice` render for HWPX. If both show it, treat it as a defect candidate and look for the cause in the order of step 3; if only one shows it, treat it as a renderer difference. When only one renderer is available (DOCX, or an HWPX fallback), judge by the XML values

Items not judged (every renderer)

- Vertical position of the page header, compressed table row heights, long-table split positions and title row repetition, and line break positions caused by font substitution
- How numbers computed by automatic numbering and fields (caption numbers, page numbers) are shown. Check the numbers in the XML's automatic numbers and fields; Hangul and Word compute them

Confirmed examples (as of rhwp v0.8.6 and H2Orestart 0.6.1; behavior may change in later versions)

- rhwp does not apply the keep-with-next setting, so a heading or □ can stay at the bottom of a page. For a TOC-entry heading, build reports it with the `[stranded TOC heading]` WARN
- H2Orestart does not draw caption objects of tables and figures, footnote bodies, or footer page numbers. Check these elements in the rhwp render and the XML

## Fonts

The built-in forms use 나눔고딕 (NanumGothic), which NAVER distributes under the SIL Open Font License 1.1, and use 나눔바른고딕 (NanumBarunGothic) only for flat headings. The font for each role is in the built-in form table of references/layout.md. Documents record the font names as they are. Substitute fonts are used only for review rendering where a font is not installed.

| Form font | Where to get it | Rendering substitute |
|------|------|------|
| 나눔고딕 (NanumGothic) | The NAVER release with Hanja from 공유마당 (Gongu Madang) safe fonts or the operating system package (fonts-nanum). `fonts --setup` downloads the Google Fonts release, which has no Hanja | none |
| 나눔바른고딕 (NanumBarunGothic) | Install the NAVER release from 공유마당 (Gongu Madang) safe fonts or the operating system package (fonts-nanum). It is not in the Google Fonts repository, so it is not downloaded automatically | NanumGothic |

- Both fonts are listed as OFL fonts among the safe fonts (안심글꼴) on 공유마당 (Gongu Madang) of the Korea Copyright Commission (https://gongu.copyright.or.kr/gongu/wrt/wrt/view.do?wrtSn=13288238&menuNo=200023, https://gongu.copyright.or.kr/gongu/wrt/wrt/view.do?wrtSn=13288242&menuNo=200023)
- OFL 1.1 allows bundling the fonts with software on the condition that the copyright notice and license go with them, and it does not allow selling the font files by themselves (https://openfontlicense.org/open-font-license-official-text/). `fonts --setup` downloads OFL.txt together with the font files
- The NAVER release (including the fonts-nanum package) has outlines for all 4,620 KS X 1001 Hanja and the 268 compatibility Hanja in every weight of both fonts. NanumGothic in the Google Fonts repository has no Hanja
- Install the NAVER release of both fonts on computers that open documents with Hanja in Hangul or Word. If a release without Hanja is installed, how Hanja appear depends on each program's font substitution
- If the review rendering environment has the Google release of NanumGothic, Hanja are drawn in another font chosen by the renderer. Do the final check of how Hanja look in Hangul or Word with the NAVER release installed
- The level symbols □, ○, -, ㆍ, and ※ have outlines in every weight of both fonts. The cell bullet symbol ◦ is in the regular and bold files of both fonts

Font installation on the user's computer

Install the NAVER release in the order below on each computer that opens the documents in Hangul or Word. Always install NanumGothic, and also install NanumBarunGothic when there are flat-form documents.

1. Download the zip files with '공유저작물 다운로드' (download shared work) from the 공유마당 (Gongu Madang) safe-font pages for NanumGothic (https://gongu.copyright.or.kr/gongu/wrt/wrt/view.do?wrtSn=13288238&menuNo=200023) and NanumBarunGothic (https://gongu.copyright.or.kr/gongu/wrt/wrt/view.do?wrtSn=13288242&menuNo=200023). A short survey appears the first time
2. If NanumGothic from Google Fonts was installed before, remove it first. That release has no Hanja and shares the font name, so which one is used cannot be known
3. Unzip the files and install them for the operating system
    - (Windows) Select all font files (.ttf or .otf) and choose 'Install for all users' from the right-click menu. Without administrator rights, choose 'Install'
    - (macOS) Double-click the font files and install them in Font Book
    - (Linux) Install the operating system package (fonts-nanum on Debian-based systems), or copy the font files to `~/.local/share/fonts/` and run `fc-cache -f`
4. Close all open Hangul and Word windows and open them again
5. Check that NanumGothic and NanumBarunGothic appear in the font list. On Windows, if they do not, install them again with 'Install for all users'

Fonts of user forms

Windows and Hancom Office fonts common in user forms are rendered for review with the substitutes below where they are not installed.

| User form font | Where to get it | Rendering substitute |
|------|------|------|
| 맑은 고딕 (Malgun Gothic), 돋움 (Dotum), 굴림 (Gulim) | Windows default fonts | NanumGothic |
| 바탕 (Batang) | Windows default font | NanumMyeongjo |
| Arial | Windows default font | Liberation Sans |
| 휴먼명조, 한양신명조, 명조, HCI Poppy | Fonts bundled with Hancom Office | NanumMyeongjo |
| 한컴돋움, 한양중고딕, HCI Hollyhock | Fonts bundled with Hancom Office | NanumGothic |
| HY헤드라인M | Font bundled with Hancom Office | NanumGothic ExtraBold |
| 함초롬바탕 (HCR Batang) | Bundled with Hancom Office, free official distribution by Hancom | NanumMyeongjo |
| 함초롬돋움 (HCR Dotum) | Bundled with Hancom Office, free official distribution by Hancom | NanumGothic |

- Windows default fonts may not be copied to other computers or redistributed (https://learn.microsoft.com/en-us/typography/fonts/font-faq)
- The permitted use of fonts bundled with Hancom Office is creating documents within Hancom Office, and using the font files in other programs is not part of that permission (https://www.hancom.com/news/notice/detail/6117)
- The skill does not download or copy either kind. Use them where the respective program is installed, or the user obtains them directly
- 휴먼명조 exists as a Hancom-only HFT file and a Windows TTF file. When the names are the same, the TTF is loaded first, so its appearance can differ between environments (https://www.hancom.com/support/faqCenter/faq/detail/2680)

fonts command

- (`fonts`) For each built-in form font, prints whether it is installed, whether it covers the 4,620 KS X 1001 Hanja, the rendering substitute, and where to get it
    - Installed fonts are found through the file fontconfig picks when fontconfig exists. Otherwise (usually Windows and macOS), they are found by searching the operating system font folders for a file with the same family name. On Windows both the all-users and the per-user font folders are searched
    - Hanja coverage is judged on the file found (the regular-weight file when several share the name) by whether every Hanja has both a character code and a glyph outline. A font with codes but empty glyphs also shows as missing
    - The Hanja column of a font that is not installed and the substitute column of an installed font show `-`. When there is no way to look fonts up (for example with neither fontconfig nor fonttools), the installed and Hanja columns show `?`
    - The result describes the computer where the command ran. A result from a remote workspace shows only the state of the review rendering environment
- (`fonts --setup`) Downloads NanumGothic and NanumMyeongjo, if they are not installed, with their license file (OFL.txt) to `~/.local/share/fonts/blockwriter/`. NanumMyeongjo is for rendering in place of the serif fonts of user forms. It then writes fontconfig rules that map only the font names not installed to their substitutes to `~/.config/fontconfig/conf.d/60-blockwriter.conf` and runs `fc-cache`. For fonts whose substitute is NanumGothic ExtraBold (HY헤드라인M), the rules also set the weight
- Where downloads are blocked, operating system packages (for example fonts-nanum, fonts-liberation) also work
- Systems without fontconfig (fc-list), usually Windows and macOS, skip writing the rules. Hangul and Word use the installed fonts
- DOCX records the English name, the Hangul character set, and the family in the font table so that Word picks a font of the same family when a form font is missing (DOCX mapping rules in references/layout.md)
