# Deciphering HYBRID

An English critical reconstruction of Matthew/C++’s HYBRID RPG, using the v0.30 witness archived on February 13, 2003. [Read the edition](https://al-geroth.github.io/hybrid-rpg-reconstruction/).

## Learn and play

Start with [HYBRID in Plain English](https://al-geroth.github.io/hybrid-rpg-reconstruction/handbook.html), then [make a character](https://al-geroth.github.io/hybrid-rpg-reconstruction/builder.html) or [sit in on a session](https://al-geroth.github.io/hybrid-rpg-reconstruction/session.html). Five worked sheets, printable forms and a mathematical playground put names and actions beside the numbers. The [experimental game](https://al-geroth.github.io/hybrid-rpg-reconstruction/adaptation.html) and [its replay](https://al-geroth.github.io/hybrid-rpg-reconstruction/replay.html) disclose each added rule.

The [Phase II atlas](https://al-geroth.github.io/hybrid-rpg-reconstruction/atlas.html) gives a disposition for every one of the 205 previously locator-only candidates. The Phase I registers below retain their original counts and stable identifiers. [Research and reference](https://al-geroth.github.io/hybrid-rpg-reconstruction/reference.html) provides a separate route to that evidence.

## What can you play?

You can give a character a scale-labelled rating, express the same rating on another scale, follow a specified route to a superhuman ability, or calculate whether an ordinary runner can maintain a given pace. In one worked example, the difference between a printed conversion and its recalculation changes whether a roll of eight succeeds. When two characters oppose each other, the source supplies several local tests but leaves consequential choices to the referee. The seven trials follow those choices through to injury, recovery and advancement.

## Contents

| Material | Location |
| --- | --- |
| Eleven thematic chapters, quickstart, critical assessment and editorial appendix | [Manuscript](manuscript/) |
| Seven playability trials with inputs, calculations and stopping points | [Scenario records](analysis/playability/scenarios.json) |
| Rules, segments, glossary, equation registry and conflicting readings | [Editorial data](data/) |
| Source forms, text boundaries, selection counts and join diagnostics | [Classification method](analysis/classification/README.md) |
| Numerical examples, variable domains, inverses and candidate inventory | [Mathematical study](analysis/mathematics/README.md) |
| Dated witnesses, retrieval status, resolved URLs and payload digests | [Source manifest](sources/source_manifest.csv) |
| Typed relations with occurrence counts and ranking denominators | [Dependency graph](analysis/dependencies/graph.json) |
| Independent internal review and counterexamples | [Review](analysis/review/independent-reading.md) |
| Release counts and publication checks | [Counts](analysis/edition-counts.json) and [QA](analysis/review/publication-qa.md) |

The reference has 204 rule headings numbered 0–203. The catalogue divides their contents into 246 units and the preceding material into another 58. The Phase I mathematical register contains 54 detailed readings. Its locator index initially left 205 other candidate passages for further study. Phase II investigates those passages and records its results separately.

## Build and check

From the repository root, with Python 3.10 or later, build the static publication from the included editorial data. These steps work offline.

```sh
python scripts/math_check.py
python scripts/build.py
python tests/check_publication.py
python -m http.server 8713 --bind 127.0.0.1 --directory docs
```

Open [the local edition](http://127.0.0.1:8713/). GitHub Pages serves the generated `docs/` directory on `master`. The reader uses native HTML, local fonts, and small JavaScript filters. Every chapter, catalogue segment and glossary entry has a static address. The full-text search index and graph are local assets.

To repeat the Phase II checks, use a Git checkout that includes the Phase I reference commit. The atlas uses its checked-in source locators offline. Passing `--source` additionally checks all 205 spans against the private witness after retrieval.

```sh
python scripts/phase2_atlas.py
python tests/phase2_session_replay.py
node tests/phase2_tools.cjs --numeric
python tests/phase2_edition.py
```

With the preview running and Playwright installed, run `node tests/browser.cjs`, `node tests/phase2_navigation.cjs` and `node tests/phase2_tools.cjs`. Each also accepts the published base URL, including its trailing slash. The [first-reader report](analysis/phase2/comprehension-review.md) records the handbook revisions. The [release checks](analysis/phase2/publication-qa.md) document how the examples, session and publication were verified.

To reconstruct the catalogue from the primary witness, run the following sequence. The first command downloads the payload on a cache miss, checks its SHA-256, then aligns the hand-authored annotations. Later runs can omit `--fetch`. `math_inventory.py` uses the private reference payload to locate mathematical cues. The `--write` flags refresh the numerical derivatives when changing their inputs.

```sh
python scripts/corpus.py --fetch
python scripts/corpus_checks.py
python scripts/math_inventory.py --write
python scripts/math_check.py --write
python scripts/build.py
python tests/check_publication.py
```

Optional reproduction steps

- `python scripts/witnesses.py` retrieves the comparison witnesses, retains their original bytes under ignored `sources/raw/`, and refreshes the retrieval manifest. Live websites and access restrictions can change. The pinned February source has digest `b71d98a0582301d4cb2f83efbb193bfe6c71fa6ccb56e068a4fc14ae553c73ec`.
- `Rscript scripts/plate.R` redraws the cover’s log–log plot using base R. A copy is included so the publication builds without R.
- With Playwright and Chromium available, `node tests/browser.cjs` exercises the local preview at three viewport sizes. Pass the deployment URL as the first argument to run against Pages. Set `EDITION_BROWSER` to use an installed Chrome executable.

## Editorial and rights policy

A identifies an explicit authorial mechanic, B an editorial reconstruction, C a hypothetical reading, and D an editorial addition. Conditioned examples state their assumptions. The register keeps arithmetic checks distinct from claims about actual physical or social processes. All interpretations refer to v0.30 unless an earlier or later witness is explicitly named.

The host and author described HYBRID as free to read. The disclaimer discusses third-party rights and possible hard-copy publication. We found no general redistribution licence for the archived work. This repository contains original descriptions and analysis, identifiers, mathematical expressions, and private-cache retrieval code. Read the complete text at the [archived reference edition](https://web.archive.org/web/20030213163300/http://perso.wanadoo.fr/philippe.tromeur/hybrid.htm). Instrument Serif and Instrument Sans are distributed with their [font licences](web/fonts/).
