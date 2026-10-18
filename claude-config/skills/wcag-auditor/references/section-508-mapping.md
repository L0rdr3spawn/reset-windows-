# Section 508 ↔ WCAG crosswalk

Maps US Section 508 requirements (ICT Refresh, effective January 18, 2018) to
WCAG success criteria. Used by `vpat-fill.mjs` to derive Section 508 VPAT
cells from the WCAG findings.

## Sources

- [US Access Board Section 508 Standards](https://www.access-board.gov/ict/)
- [36 CFR Part 1194](https://www.access-board.gov/law/ra.html#section-508-federal-electronic-and-information-technology) — legal text
- [ICT Accessibility 508 Standards and 255 Guidelines, E207.2](https://www.access-board.gov/ict/#E207.2) — core WCAG reference

## High-level rule

**Section 508 § E207.2** requires that ICT that is web content or electronic
content (non-web) conform to **WCAG 2.0 Level A and Level AA** success criteria
and conformance requirements.

- ✅ **WCAG 2.0 A and AA criteria** → directly apply to 508 (map 1:1)
- ⚠️ **WCAG 2.1 and 2.2 additions** → **not** required by current 508, but
  commonly audited together because EN 301 549 and procurement practice
  expect them
- ❌ **WCAG AAA** → not required by 508

## How vpat-fill.mjs uses this file

The VPAT 2.5 INT template has a Section 508 table with these chapters:

| Chapter | Topic | Web-app applicability |
|---|---|---|
| Chapter 3 (Functional Performance Criteria) | 302.1–302.9 | Partial — derived from WCAG |
| Chapter 4 (Hardware) | 402–410 | Not applicable to web apps |
| Chapter 5 (Software) | 501–504 | 501.1 = all WCAG 2.0 A/AA (primary web reqs) |
| Chapter 6 (Support Documentation and Services) | 601–603 | Depends — usually N/A for v0.1.0 audits |
| Chapter 7 (Referenced Standards) | 702 | Incorporates WCAG 2.0 by reference |

For the web-content audits this skill produces:

1. **Chapter 5, §501.1** cells are populated from WCAG 2.0 A/AA results directly
2. **Chapter 3** (Functional Performance Criteria) is derived from the related WCAG findings
3. **Chapters 4 and 6** are marked **Not Applicable** with rationale (hardware and support docs are out of scope for a web-content audit)

## Chapter 3 — Functional Performance Criteria (derivation)

Each FPC is supported if the related WCAG SCs are supported.

| FPC | Topic | Supported when |
|---|---|---|
| 302.1 | Without Vision | SC 1.1.1, 1.3.1, 1.3.2, 1.3.3, 1.4.1, 1.4.2, 2.4.4, 3.3.1, 3.3.2, 4.1.2 supported |
| 302.2 | With Limited Vision | SC 1.4.3, 1.4.4, 1.4.5, 1.4.10, 1.4.11, 1.4.12, 2.4.7 supported |
| 302.3 | Without Perception of Color | SC 1.4.1 supported |
| 302.4 | Without Hearing | SC 1.2.1, 1.2.2, 1.2.4 supported |
| 302.5 | With Limited Hearing | SC 1.2.1, 1.2.2, 1.2.4 supported |
| 302.6 | Without Speech | N/A for text-based web apps (no speech input required) |
| 302.7 | With Limited Manipulation | SC 2.1.1, 2.1.2, 2.5.1, 2.5.2, 2.5.7, 2.5.8 supported |
| 302.8 | With Limited Reach and Strength | SC 2.5.1, 2.5.7, 2.5.8 supported |
| 302.9 | With Limited Language, Cognitive, and Learning Abilities | SC 1.3.1, 2.4.6, 3.1.1, 3.2.3, 3.2.4, 3.3.1, 3.3.2 supported |

## Chapter 5 — Software (501.1 WCAG mapping)

**§501.1** directly adopts all WCAG 2.0 Level A and AA criteria. So for the
WCAG-2.0-era SCs, the VPAT Section 508 column inherits directly from the
WCAG column.

### WCAG 2.0 A/AA criteria required by 508 §501.1

```
1.1.1, 1.2.1, 1.2.2, 1.2.3, 1.2.4, 1.2.5,
1.3.1, 1.3.2, 1.3.3,
1.4.1, 1.4.2, 1.4.3, 1.4.4, 1.4.5,
2.1.1, 2.1.2,
2.2.1, 2.2.2,
2.3.1,
2.4.1, 2.4.2, 2.4.3, 2.4.4, 2.4.5, 2.4.6, 2.4.7,
3.1.1, 3.1.2,
3.2.1, 3.2.2, 3.2.3, 3.2.4,
3.3.1, 3.3.2, 3.3.3, 3.3.4,
4.1.2
```

WCAG 2.0 had 38 A/AA SCs. (4.1.1 Parsing is WCAG 2.0 Level A but was obsoleted in WCAG 2.2; if the user's audit level is 2.2, treat 4.1.1 as "Not Applicable — obsoleted in WCAG 2.2" in the 508 VPAT column.)

### WCAG 2.1 and 2.2 additions (supplementary, not required by 508)

These SCs are added in 2.1 and 2.2. Current US Section 508 does not mandate
them. Mark the 508 cell as **"Not Applicable (WCAG 2.1/2.2 criterion, not
required by Section 508)"** unless the user requests a forward-looking VPAT
that voluntarily conforms to updated WCAG.

```
2.1 additions: 1.3.4, 1.3.5, 1.4.10, 1.4.11, 1.4.12, 1.4.13,
               2.1.4, 2.5.1, 2.5.2, 2.5.3, 2.5.4, 4.1.3
2.2 additions: 2.4.11, 2.4.12, 2.4.13, 2.5.7, 2.5.8,
               3.2.6, 3.3.7, 3.3.8, 3.3.9
```

## Chapters 4 and 6 — default to N/A

For web-content audits:

- **Chapter 4 (Hardware)** — "Not Applicable: this product is web content and does not include hardware components."
- **Chapter 6 (Support Documentation and Services)** — either "Not Applicable: this report evaluates the web product only; support documentation is out of scope" OR, if the user's audit includes their documentation site, populate from WCAG findings for those URLs.
