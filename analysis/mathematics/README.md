# How to read a HYBRID calculation

The mathematical unit of this edition is a **claim with a specified input and output**. One numbered rule can make several claims, and multiple rules can reuse one operation for different purposes. The register selects recurring transformations, character-building decisions, dice procedures, and counterexamples that can change play. Its record count measures these editorial entries. The rule catalogue also covers passages whose equations have not been normalized in the register.

All rule numbers on this page refer to the [February 13, 2003 reference witness](https://web.archive.org/web/20030213163300/http://perso.wanadoo.fr/philippe.tromeur/hybrid.htm). [Read the equation register in the publication](../../docs/mathematics.html).

## Why 20 can equal 49.28

In #45, a character with 20 C2 DP can be described as having 49.28095 C3 DP. Both numbers describe the same Default Psyche. The conversion changes the class coordinate. The preface calls the same expression a foundation for distributing points, but to spend points a player also needs a budget, choices, and prices. One can find examples of those steps elsewhere, such as #123’s sequence of fractional advantages. They do not follow from the conversion alone.

Let `u = log10(x)`. The expression `f(x) = x^log10(x)` then becomes `10^(u²)`. In logarithmic coordinates, one class step squares a number. Two steps raise it to the fourth power. After four steps from 100 CA, the result is ten raised to 65,536. Arithmetic can reproduce #200's enormous class figure without calculating it as a floating-point value. The rule's separate use of an infinite exponent for a finite fictional rank fails if read as an ordinary limit.

| Starting x | One step | Same output from | What it illustrates |
| ---: | ---: | ---: | --- |
| 0.1 | 10 | 10 | The reciprocal branch |
| 1 | 1 | 1 | Minimum value |
| 2 | 1.23202 | 0.5 | A class step can lower the written numeral |
| 10 | 10 | 0.1 | A fixed point on the increasing branch |
| 20 | 49.28095 | 0.05 | Common character-scale example |
| 100 | 10,000 | 0.01 | Rapid growth at large ratings |

Fractional inputs in this table probe the mathematical expression. They do not establish a source rule permitting a character to start at 0.1 DP. The real domain is strictly positive. The output is at least one. For any output greater than one, there are two possible inputs, one on either side of one. Their product is one. The two roots coincide at an output of one. The function decreases on (0,1) and increases on (1,∞). Its real fixed points are 1 and 10.

The inverse is `10^(±sqrt(log10(y)))`. The positive sign recovers inputs above one. Rule 188 needs just such a backwards lookup for a roll-under threshold. The printed conversion of 35 C3 to 17.7 C2 changes the outcome. The calculated value is 17.48257. After subtracting ten and rounding, the published example gives 8 or less and the recalculation gives 7 or less. This error matters at the table whenever the dice show eight.

## Three operations on a character sheet

| Operation | Input for an example | Output | Source |
| --- | --- | --- | --- |
| Change the representation | 20 C2 DP | 49.28095 C3 DP for the same character | #45 |
| Change the character’s standing | Creator pays for permanence at 75 C2 DP | Creator becomes 75 C3 DP until the status can be restored | #45 |
| Redistribute lifespan and power | Baseline 40 C2, initially equal LS and PL | Choosing the factor of two yields LS 20 and PL 80, still at 40 C2 DP | #3, #183 |

The multiplicative trade preserves `LS × PL`. The additive trade preserves `LS + PL`. At LS = PL = 40, both can yield LS = 20, with PL respectively 80 and 60. It is possible to set DP equal to a geometric mean for the first trade or an arithmetic mean for the second. Applying either as a universal formula for DP would change what the other example permits. Rule 3 also lists square-root/square and logarithm/exponential operations. It gives no measure of equivalence between the different operations.

## What reduces, and what does not

- **Adjacent classes** genuinely share one transform. Rules 45, 46, 161 and the repeated cartography in #200 provide the clearest family. Doubling before and after converting a class produces different results, as #46 itself illustrates.
- **A sequence of advantages** in #123 has its own simple algebra. Starting from 9 C2 DP, multiplying by 2, 3/2, 4/3 and 5/4 gives 18, 27, 36 and 45. In this particular sequence the intermediary factors cancel, so after four choices the original rating is multiplied by five. The text supplies sample choices at each stage. The class transform neither supplies those choices nor makes this a session reward.
- **Ratios, roots and local calibrations** do other work. The writing-time comparison in #96 gives 25 years from a five-year reference and a fivefold difference in assumed ability. The AMBS formula in #49 takes a square root. The phasing expression in #53 takes a triangular number. Those operations can be evaluated using the supplied numbers even if every class is already fixed. Sharing logarithms, exponents or a scale label is insufficient evidence of derivation.
- **Numerical self-consistency** is a weaker test than prediction. Rule 142 is unusually easy to check because it states a formula, two unit conversions and a table. Three rows agree with the formula to their printed precision. At one meter its table lists the result for two meters, eight times the result of cubing the stated height. This is an arithmetic discrepancy even on the author's own assumptions. Rule 25 poses a different problem. It accepts a diameter numeral in miles or kilometers, so the same body can receive different ratings under a unit change. Reproducing the printed number does not validate either the proposed astronomy or the proposed human physiology.

Rule 155 supplies a particularly revealing check on the preface’s claim of a single equation. It deducts the ship's body rating before converting spare power to speed. The author explicitly acknowledges that this relation does not unify the system. Rule 158 returns to it enthusiastically, while #132 uses a hull-dependent base and an engine-to-hull ratio, and #178 multiplies natural and common logarithms of different class coordinates. The common subject is fictional motion. The equations cannot be interchanged without additional assumptions.

## What the locator index counts

The [passage index](equation_locators.csv) gives one row for each of the 304 analytical segments, including segments without an equation cue. A candidate has at least one of four signals: mathematical notation in the normalized witness, a mathematical-model tag assigned in the catalogue, a manually identified verbal rating relation, or a checked citation to a detailed registry entry. This deliberately broad search finds numerical examples, cross-system analogies and even arithmetic in the recipe.

The filter goes from 304 segments to 275 candidates. Of these, 70 directly support one or more of the 54 detailed records through 82 individually identified equation-to-segment links. The remaining 205 candidate rows have their subject, location and detection basis recorded. A locator-only passage can contain important mathematics. It has not received a separate normalized or numerically tested register entry solely by appearing in the index. Likewise the 29 rows without a selected cue remain available for inspection. None of these counts verifies the masthead's own statement about its number of equations.

## Missing and circular inputs

Rules 14 and 113 illustrate a trap. The first gives creature length from a C3 rating and a divisor. The second expresses the divisor through the same C3 rating and length. If those are the only two relations used, substituting the second into the first merely returns the starting length. A separately chosen damage/environment model in #14 or the C2-based length in #113 can supply independent information. Specifying which one was used is essential to making an example reproducible.

The field model in #7 presents a related issue when a radius-dependent parameter is used to infer spatial extent. The passage offers particular numerical calibrations. A particular calibration can close a calculation, while trying to infer the missing parameter from the very extent being predicted makes it circular. A dependency arrow records which value enters an expression. It does not guarantee that a character sheet, an encounter or even another equation provides that value independently.

## Running the numerical checks

Run `python scripts/math_check.py` from the repository root. It replays the worked numerical cases, checks the real branches at sixteen inputs, enumerates all 216 outcomes of three fair six-sided dice, and verifies that the recorded CSV and JSON outputs match. It checks the class identity, reciprocal symmetry and the applicable inverse at each test input. Use `python scripts/math_check.py --write` to regenerate the outputs following an intentional registry change.

The high-roll example assumes that 66% means a fraction of the pool’s maximum. At 3d6 this calls for 12 or more and leaves 81 successful outcomes out of 216, or 37.5%. The assumption receives layer C. Even with that assumption the preface’s two thirds and #35’s 66% separate at some pool sizes. On a hypothetical 25d6 they require 100 and 99 respectively. These counts describe die outcomes under a specified reading. They do not estimate how often HYBRID characters actually succeed.

The [case ledger](equation_cases.csv) contains the executable expressions and reference values. The [class table](class_conversion.csv) keeps both inverse branches, and the [check report](checks.json) lists before/after counts, duplicate-key checks, missing references, and registry entries with no incoming editorial links. A computed example in layer A verifies arithmetic under the stated source procedure. Example inputs and inverse derivations introduced by this edition remain editorial.

To replay the source-span search, first acquire the pinned witness through the corpus workflow. Then run `python scripts/math_inventory.py`. It verifies the witness checksum, recovers the normalized segment spans, and compares the full locator table and its [join audit](locator_audit.json) with the checked-in outputs.
