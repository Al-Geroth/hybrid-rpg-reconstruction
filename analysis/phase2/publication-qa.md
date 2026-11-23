# Learn and Play release verification

The release extends Phase I commit `6fbd40e1bb4718b0ccd5b6cf26e9524e3fd94946` using the same v0.30 witness. All 23 prior HTML pages and their 759 existing fragment identifiers resolve. The original rules, segment catalogue, glossary, equations, tensions, source manifest and analytical registers match the reference commit. Eleven new pages bring the publication to 34.

| Check | Result |
| --- | --- |
| Introductory handbook | 3,032 words in the reading text outside expandable notes, counted by splitting rendered text on whitespace. All three rows of the conversion table checked to rounding precision. |
| Beginner transfer | A first-time reader explained all seven requested concepts and independently solved a new running problem after revision. [Review and changes](comprehension-review.md) |
| Candidate accounting | 304 segments → 275 candidates → 70 Phase I direct-evidence segments plus 205 newly reviewed candidates. The latter yielded 20 distinct operations, 52 variants, 38 examples, 52 calibrations, 1 superseded equation, 20 assertions outside gameplay, 18 unresolved passages, and 4 false positives. All 205 source spans verified. Zero unmatched or duplicate disposition keys. [Audit](atlas-audit.json) |
| Arithmetic | All 101 Phase I numerical cases and 54 new atlas cases passed. Rule 172 is counted as a variant; treating dimensional travel as a separate task from manipulation would increase the new-operation count to 21. [Numerical replays](atlas-numerical-replay.csv) |
| Character replay | 5 input characters → 5 reproduced, 32 stored numerical expectations matched. Covered alternate inverse branches, invalid or absent values, and source-specific power limits. [Fixtures](../../data/phase2/worked_characters.json) |
| Original and adapted scene | 16 original plus 16 adapted decisions, each with an evidence layer. All 63 reference occurrences matched, with no duplicate source keys. Five restricted configurations and four editorial rules checked. A changed trade decision or tie changes the lift's destination. [Chronology and counterfactuals](session-replay-audit.json) |
| Links and search | 5,920 candidate link/asset occurrences → 5,560 local occurrences including graph and search destinations, all resolving. Zero duplicate HTML identifiers. Site search includes the Phase II session, terms and reading paths. |
| Browser and print | Chrome at 1366, 390 and 320 pixels. All eleven new pages fitted the viewport. The atlas disposition filter returned 4 of 205 rows, and reset restored the full list. All five presets replayed at each width. Verified source choices, editable fields, alternative trade and conversion branches, error states, reset, generated sheet and isolated A4 PDF output. The original browser suite also passed. |
| Public contents | New pages use new prose, indexed source identifiers, and numerical expressions. A comparison of all eleven new pages to the original HTML found zero matching windows of twelve successive normalized alphanumeric tokens. The original source and browser-test outputs remain in ignored directories. |

## Corrections prompted by the diagnostic reading

A separate pass sampled the source behind selected atlas rows and builder choices. The time-perception sheet now includes the competing 30 C1 example and its inconsistent printed class. The mutant build identifies intermediate stages. A user-entered appearance value remains on the sheet even when the power budget is unknown. Rule 129 now preserves both time-illusion formulas, and rule 174 distinguishes a specific group example's rounding from the unresolved fractional result for a device. The atlas explains its counting choice for rule 172.

The recorded procedures can be replayed with the [repository commands](../../README.md). Viewports emulate screen sizes in Chrome. The reviewers were internal AI readers, and the two session transcripts are constructed tabletop demonstrations.
