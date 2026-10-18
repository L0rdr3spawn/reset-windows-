# VPAT 2.5 INT — how findings populate the template

This file documents how `vpat-fill.mjs` populates each table in the user-supplied
ITI VPAT 2.5 INT `.docx` template from the `aggregated.json` audit output.

This is the skill's own documentation. It does **not** reproduce ITI's form.
The VPAT template remains a user-supplied file downloaded from
[itic.org/policy/accessibility/vpat](https://www.itic.org/policy/accessibility/vpat).

## VPAT 2.5 INT structure (high level)

The INT ("International") edition of VPAT 2.5 combines three reports:

1. **WCAG 2.x Report** (all 86 SCs for 2.2, or 50 for 2.1, or 38 for 2.0)
2. **Revised Section 508 Report** (US)
3. **EN 301 549 Report** (EU)

Plus required preamble sections (Product Information, Report Date, Contact Information, Evaluation Methods Used, Applicable Standards/Guidelines, Terms, Notes).

## Conformance classifications

Each SC/clause row has one of these values in the "Conformance Level" column:

| Term | Meaning | Skill rule |
|---|---|---|
| **Supports** | Functionality meets the criterion | No violations for any rule mapped to the SC, SC is applicable |
| **Partially Supports** | Some functionality meets; some does not | Some violations for rules mapped to the SC, OR violations on some URLs but not others |
| **Does Not Support** | Functionality does not meet the criterion | Violations on all audited URLs for rules mapped to the SC |
| **Not Applicable** | Criterion is not relevant to the product | SC is not applicable (e.g., 1.2.* for a site with no media), OR criterion is not required by the standard being reported (e.g., WCAG 2.2 criterion in the 508 table) |
| **Not Evaluated** | Only for AAA rows in a non-AAA audit | Skip row |

## Per-SC derivation logic

For each WCAG 2.2 success criterion:

1. **Identify the axe rules mapped to the SC** via `references/axe-rule-mapping.md`
2. **Check if any mapped rule appears in `aggregated.json` violations**
   - **No mapped rules in violations** AND SC is in `axeTags` (automatable) → **Supports**
   - **No mapped rules in violations** AND SC is NOT automatable → **Supports with manual verification** (or **Not Evaluated** if manual pass skipped)
   - **All URLs have violations for this SC** → **Does Not Support**
   - **Some URLs have violations, others don't** → **Partially Supports**
3. **Check manual-check results** (passed in separately by Claude)
   - Manual findings override or supplement axe findings for the SC
4. **Add Remarks**: violation counts + URLs affected + manual-check notes

## Remarks field template

For each row, generate a Remarks string:

```
Supports:
  [axe] <rule-id>: <n> instance(s) pass across <m> URL(s).

Partially Supports:
  [axe] <rule-id>: <violations> violation(s) on <n>/<m> URL(s): <urls>.
  [manual] <SC title>: <manual finding summary>.

Does Not Support:
  [axe] <rule-id>: <violations> violation(s) on all <m> URL(s).
  Example node: <first node selector>.

Not Applicable:
  No applicable content on audited URLs (e.g., no media elements for 1.2.*).
```

## Section 508 derivation

Per `section-508-mapping.md`:

1. **Chapter 3 (FPCs)** — derived from related WCAG SCs. If all mapped WCAG SCs "Support," FPC "Supports"; otherwise propagate worst classification.
2. **Chapter 4 (Hardware)** — **Not Applicable** (rationale: "Audited product is web content; no hardware components.")
3. **Chapter 5 §501.1** — direct inheritance from WCAG 2.0 A/AA rows.
4. **Chapter 5 §502, §503, §504** — Not Applicable for web content (these apply to platform/authoring software).
5. **Chapter 6** — Not Applicable unless docs were audited.
6. **Chapter 7 §702** — inherits from WCAG.

## EN 301 549 derivation

Per `en-301-549-mapping.md`:

1. **Clause 4 (FPSs)** — derived from related WCAG SCs.
2. **Clause 5 (Generic)** — Not Applicable (rationale per clause).
3. **Clause 6 (Two-way voice)** — Not Applicable unless product has voice calling.
4. **Clause 7 (Video)** — inherits from 1.2.* SCs if site has video; else Not Applicable.
5. **Clause 8 (Hardware)** — Not Applicable.
6. **Clause 9 (Web)** — direct inheritance from WCAG 2.1 A/AA rows.
7. **Clause 10 (Non-web documents)** — Not Applicable.
8. **Clause 11 (Non-web software)** — Not Applicable.
9. **Clause 12 (Documentation)** — Not Applicable unless docs audited.
10. **Clause 13 (Emergency)** — Not Applicable.

## Preamble sections

### Product Information
- **Name of Product**: from `--product` flag
- **Version**: from `--version` flag
- **Product Description**: user-supplied (VPAT template placeholder left in)
- **Date**: generation date (ISO)
- **Contact Information**: user-supplied (template placeholder left in)

### Evaluation Methods Used
Populated automatically:
```
Automated testing using axe-core <version> via Playwright, executed against
<N> URLs at viewports <list>. Manual verification performed for success
criteria that cannot be automated (see Remarks per SC). Authentication state
captured via Playwright storageState for authenticated routes.
```

### Applicable Standards/Guidelines
Generated from the audit's scope:
```
- Web Content Accessibility Guidelines 2.2 (Level <level>)
- Revised Section 508 Standards, as published in 36 CFR Part 1194
- EN 301 549 V3.2.1 (2021-03)
```

### Terms
Supports / Partially Supports / Does Not Support / Not Applicable / Not Evaluated (standard VPAT definitions, left in the template unchanged).

## What vpat-fill.mjs writes

`vpat-fill.mjs` reads the user-supplied `.docx` template, locates each table
cell by its column header + row label, and writes the appropriate value. It:

- **Does not** alter the template structure
- **Does not** change ITI's wording, table layout, or boilerplate
- **Only** fills in the cells vendors are expected to complete (Conformance Level + Remarks columns, Preamble fields)

This keeps the skill on the correct side of ITI's "do not alter the form without express written permission" requirement.
