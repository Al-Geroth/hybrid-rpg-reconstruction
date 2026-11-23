# Publication verification

| Check | Result |
| --- | --- |
| Identity of reference witness | The 431,957 bytes from February 13 match the February 11 Free.fr capture. Both have the SHA-256 recorded in the manifest. |
| Heading and segment coverage | All 204 headings and 304 contiguous editorial spans validated. All 246 numbered segments match a parent. The other 58 precede the numbered series. No missing heading, duplicate heading identifier or offset gap. |
| Explicit numerical references | All 528 expanded reference rows match a heading. Occurrences include repeated targets and the expansion of one range. Some resolved numbers are semantic misdirections. |
| Equation and glossary joins | All 13 equation-dependency rows and all 217 glossary-relation rows matched. Zero duplicate keys and zero unmatched links in these checks. |
| Numerical replay | 54 detailed records, 101 numerical cases, 16 class-table inputs, both branches of the inverse, and a complete enumeration of 216 outcomes for three dice. Under the stated trial assumption 81 meet its threshold. |
| Calculation inventory | 304 input segments, 275 candidates after screening, 70 selected as direct evidence and 205 locator-only candidates. All 82 equation-to-segment evidence pairs match. |
| Build replay | Reran the extractor, boundary audit, mathematical checks, locator audit and site generator. All 53 registered or generated files in the comparison were byte-identical before and after. |
| Static HTML | 23 English pages, one main heading per page, zero duplicate HTML identifiers. Of 4,120 link and asset occurrences in the HTML, search index and graph, 3,774 were local and all resolved. Repeated link occurrences were retained. |
| Browser interaction | Chrome at 1366 × 900, 390 × 844 and 320 × 640. Rule filter reduced 304 segments to the two for #188 on each viewport. Tested combining all remaining filters, a no-match search, reset, glossary search, site search, graph selection and navigation. |
| Layout | Ten reading and apparatus pages checked for horizontal overflow at each of those widths. Zero overflow, script errors or failed asset responses. Inspected the desktop and mobile title pages visually. Mobile checks used emulated viewports. |
| Public tree | Original source payloads, normalized full text, screenshots and browser state stay in ignored directories. The generated site packages original analyses and plots, source locators, and the typefaces with their licences. |

The segment count is an editorial decision. The independently repeated heading count is a property of the pinned witness. The independent review sampled interpretive decisions and put counterexamples back through the catalogue and rulebook. It was an internal review, with authorship boundaries documented in the [review report](independent-reading.md).

Run [the static validator](../../tests/check_publication.py) and [the browser test](../../tests/browser.cjs) to repeat the publication checks. The [classification audit](../classification/audit.json), [mathematical checks](../mathematics/checks.json), [locator audit](../mathematics/locator_audit.json) and [graph audit](../dependencies/graph.json) retain the subordinate selection and key diagnostics.
