# How to read the catalogue

The witness is the 13 February 2003 capture of Philippe Tromeur's page. The local audit operates on the Internet Archive identity replay of that capture. The printed version banner says v0.30, while the author's own masthead says v0.3. The front matter explicitly reidentifies a different earlier v0.3 as v0.15. Neither a shared title nor a shared decimal label proves that two documents are the same edition.

## Text and locators

The file digest is checked before any annotation is applied. The HTML is decoded using Windows-1252, the HTML decoding of the declared Latin-1 label. The extractor discards scripts and an advertising iframe. Paragraphs, line breaks and structural wrappers delimit blocks. It retains the source's sometimes missing spaces at inline font changes, preserving searchable boundaries. It collapses whitespace inside each nonempty block, then excludes the final host advertising credit. The first 92 retained blocks (0–91) precede rule 0. Numbered entries occupy blocks 92–296.

Offsets address zero-based Unicode characters in the retained blocks joined by a single newline, with the end offset excluded. The printed heading, document position, editorial rule key and editorial segment key are separate fields. A split within a paragraph usually marks a change of subject, a procedure embedded in commentary or two incompatible calculations. A short continuous statement and its numerical illustration can stay together. Paragraph breaks and the repeated disclaimer continuation labels do not create additional rules. The linked character glossary consists primarily of pointers to numbered rules.

Every retained character belongs to one segment. Editorial units are interpretive and coarser than sentences. A segment can contain several examples. The front of the source includes the host's title, credit and navigation alongside the authorial work. The first catalogue entry identifies that distinction. These items remain in document order. No numbered identifier has been invented for them.

## Reading the annotations

The two plain-text annotation files contain original editorial titles, paraphrases and judgements. They are aligned by source position and do not store the original passages. An entry starting with a number belongs to that printed rule. An entry starting with **f** refers to an unnumbered block. A locator suffix after **@** is an offset within the local block or the joined text of the parent rule. Physical order of records in the annotation files does not determine their published order.

Each record has five pipe-separated fields. They hold its locator, category codes, judgement codes, title and paraphrase. The first category is primary and the rest are secondary. The first judgement code is E for executable, P for partially executable, A for ambiguous, X for non-executable and N for non-mechanical. The second code is H, M or L for confidence in the interpretation. The expanded vocabulary is in the extractor and in each generated segment.

A local calculation is executable when the indicated inputs and branch are sufficient for the stated operation. This includes the four-step low-powered mutant example in rule 123. A category marked partially executable yields a real output but leaves an input choice, linkage or subsequent operation material to the passage unspecified. Ambiguity identifies competing readings or outputs. Non-executable identifies a purported procedure for which indispensable steps cannot be recovered. A non-mechanical judgement means the passage by itself describes no game procedure. It can still explain an important design choice. Judgements concern the task identified by the segment title, so counts depend on the editorial unit of analysis. Empirical support and game executability are independent questions.

Terms and game names use explicit spellings and aliases in each span. They supplement editorial topic assignments and do not establish which ideas the author borrowed. Generic words, fused text and inconsistent spelling limit automated detection. The absence of a term from this field is not negative evidence. Editorial dependencies record selected computational relationships. An explicit cross-reference may recommend reading, return to an earlier topic, cite itself or point to the wrong subject.

The layer field describes how the catalogue entry reports its passage. An A entry paraphrases a clearly stated source claim, including a claim about a fictional setting. A B entry describes an editorial interpretation or assessment of a source passage. The critical rulebook and mathematical registry separately grade their reconstructed assertions. No confidence rating certifies the truth of a social, scientific or demographic claim.

## Document forms

The HTML contains **13 layout tables**. They enclose hosting controls, banners, sections of prose and a final spacer. None is an HTML grid of gameplay statistics. Numerical tables are instead written into paragraphs. Rule 21 lists materials, rule 93 lists environmental coefficients, rule 142 aligns heights with masses, and rule 146 lists damage pools. The reader would miss these tables by looking only for HTML row tags. A mention of an external table points to a separate work. In rule 186 the plural word for tables occurs in an idiom.

The separate forms inventory records the layout tables at original byte offsets, inline tabulations, examples, introductions, reading indexes and selected recognisably enumerated procedures. For example, rule 5 has four locally numbered cases, rule 103 has seven inline steps, rule 163 numbers historical alternatives, and rule 189 has three DCV conventions. These are not printed rules 5.1–5.4 or 103.1–103.7. No letter-suffixed or decimal rule heading and no named appendix were found. The six introductory examples belong to a separate sequence.

The same inventory points to segments containing equality, exponent or common-log notation. A hit can be a formula, a substitution, a repeated value or a loose identification. It is a locator for inspecting the mathematics, not a count of independent equations. The editorial equation registry examines selected significant relations. The author's claimed 203 equations has no corresponding sequence of 203 independently labelled mathematical statements.

## Numbering and reference audit

There are 204 printed headings, from 0 through 203, in ascending document order. Heading 109 omits the hash. Rule 151 continues beyond its first paragraph. Within this witness there is no absent or duplicated number in that interval. The author's count of 203 coincides with the maximum identifier. Counting headings is the reproducible way to resolve the total for this edition.

The cross-reference table preserves repeat mentions at different positions. A range in rule 177 is expanded, with its nine interior and terminal tokens marked as range-derived rows. Seven manually checked shorthand references supplement the explicit rule and list grammar. The local second equation in rule 140 and the warp number in rule 130 do not name rules. Bare numeric identifiers actually identified as rule references resolve to headings. A resolved number can still be a wrong reference. Rule 84 attributes cloning to 17, which concerns dice, while rule 18 describes cloning. Rule 51 cites 37 for shape-changing and rule 38 explicitly names that operation. Relative phrases such as “previous” and “next” do not create numeric edges. Other editions may have different gaps.

## Reproduction

From the project root, run the following commands. The first fetches the identity replay into the ignored source cache only if the file is absent. The checksum is validated before writing it. If the file is already present, omitting the switch rebuilds offline. The contradiction register is an input to the per-rule tension links.

```text
python scripts/corpus.py --fetch
python scripts/corpus_checks.py
```

The workflow writes the rule and segment arrays, reference occurrence table, form register and audit. The audit records the before-and-after counts for row selections, unmatched keys, unreferenced lookup keys, repeated foreign keys and duplicate parent checks. Repeated references are expected and are retained. A normalized character offset is distinct from an offset in the original HTML bytes. Reproducing the numerical study does not require republishing the archival payload.
