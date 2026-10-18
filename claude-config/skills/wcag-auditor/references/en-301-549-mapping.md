# EN 301 549 ↔ WCAG crosswalk

Maps EN 301 549 (European ICT accessibility standard) clauses to WCAG
success criteria. Used by `vpat-fill.mjs` to derive EN 301 549 VPAT cells
from WCAG findings.

## Sources

- [ETSI EN 301 549 V3.2.1 (2021-03)](https://www.etsi.org/deliver/etsi_en/301500_301599/301549/03.02.01_60/en_301549v030201p.pdf) — current published version
- [EN 301 549 Annex A (normative) Relationship between this document and the essential requirements of Directive (EU) 2016/2102](https://www.etsi.org/deliver/etsi_en/301500_301599/301549/03.02.01_60/en_301549v030201p.pdf) — the WCAG crosswalk lives here
- [European Accessibility Act (EAA) 2025 update](https://ec.europa.eu/social/main.jsp?catId=1202)

## High-level rule

**EN 301 549 Clause 9** (Web) **requires WCAG 2.1 Level A and AA** — all of
them. Clause 11 (Non-web software) and Clause 10 (Non-web documents) also
reference WCAG 2.1 A/AA.

- ✅ **WCAG 2.1 A and AA** → directly required by EN 301 549 Clause 9
- ⚠️ **WCAG 2.2 additions** → not yet required (EN 301 549 v3.2.1 predates WCAG 2.2). A 2024+ revision is expected to adopt 2.2.
- ❌ **WCAG AAA** → not required
- ❌ **Chapter 5–8, 11.5–11.8, 12, 13** → non-web clauses, **not applicable** to web-content audits

## How vpat-fill.mjs uses this file

The VPAT 2.5 INT template has an EN 301 549 table with these major clauses:

| Clause | Topic | Web-app applicability |
|---|---|---|
| 4 | Functional Performance Statements | Derived from WCAG findings |
| 5 | Generic Requirements (biometrics, privacy, closed func., etc.) | Mostly N/A for web |
| 6 | ICT with Two-Way Voice Communication | Not Applicable |
| 7 | ICT with Video Capabilities | Partial (if site embeds video) |
| 8 | Hardware | Not Applicable |
| **9** | **Web** | **Primary — directly from WCAG findings** |
| 10 | Non-web Documents | N/A for v0.1.0 web audits |
| 11 | Non-web Software | Not Applicable |
| 12 | Documentation and Support Services | N/A unless docs audited |
| 13 | ICT providing Relay or Emergency Service Access | Not Applicable |

## Clause 4 — Functional Performance Statements (derivation)

| Clause | Statement | Derived from WCAG |
|---|---|---|
| 4.2.1 | Usage without vision | 1.1.1, 1.2.*, 1.3.*, 1.4.1, 1.4.2, 2.4.4, 3.3.1, 4.1.2 |
| 4.2.2 | Usage with limited vision | 1.4.3, 1.4.4, 1.4.5, 1.4.10, 1.4.11, 1.4.12, 2.4.7 |
| 4.2.3 | Usage without perception of color | 1.4.1 |
| 4.2.4 | Usage without hearing | 1.2.1, 1.2.2, 1.2.4, 1.4.2 |
| 4.2.5 | Usage with limited hearing | 1.2.1, 1.2.2, 1.2.4, 1.4.2, 1.4.7 |
| 4.2.6 | Usage without vocal capability | N/A for text-based web apps |
| 4.2.7 | Usage with limited manipulation or strength | 2.1.1, 2.5.1–2.5.8 |
| 4.2.8 | Usage with limited reach | 2.5.1, 2.5.7, 2.5.8 |
| 4.2.9 | Minimize photosensitive seizure triggers | 2.3.1 |
| 4.2.10 | Usage with limited cognition, language, or learning | 1.3.1, 2.4.6, 3.1.*, 3.2.*, 3.3.* |
| 4.2.11 | Privacy | Derived from design review (not from WCAG directly) |

## Clause 9 — Web (primary mapping)

EN 301 549 Clause 9 adopts **all WCAG 2.1 Level A and AA** success criteria directly. The clause numbering mirrors WCAG's SC numbering:

- Clause **9.1** = Perceivable (SC 1.1.1 through SC 1.4.13)
- Clause **9.2** = Operable (SC 2.1.1 through SC 2.5.4)
- Clause **9.3** = Understandable (SC 3.1.1 through SC 3.3.4)
- Clause **9.4** = Robust (SC 4.1.1, 4.1.2, 4.1.3)
- Clause **9.5** = Conformance Requirements (from WCAG 2.1 §5)
- Clause **9.6** = WCAG 2.1 Conformance (WCAG-specific)

The **VPAT 2.5 INT EN 301 549 column** populates directly from WCAG A/AA findings for every WCAG 2.1 SC.

### WCAG 2.1 A/AA criteria required by EN 301 549 Clause 9

All 50 WCAG 2.1 A/AA SCs:
```
1.1.1, 1.2.1, 1.2.2, 1.2.3, 1.2.4, 1.2.5,
1.3.1, 1.3.2, 1.3.3, 1.3.4, 1.3.5,
1.4.1, 1.4.2, 1.4.3, 1.4.4, 1.4.5, 1.4.10, 1.4.11, 1.4.12, 1.4.13,
2.1.1, 2.1.2, 2.1.4,
2.2.1, 2.2.2,
2.3.1,
2.4.1, 2.4.2, 2.4.3, 2.4.4, 2.4.5, 2.4.6, 2.4.7,
2.5.1, 2.5.2, 2.5.3, 2.5.4,
3.1.1, 3.1.2,
3.2.1, 3.2.2, 3.2.3, 3.2.4,
3.3.1, 3.3.2, 3.3.3, 3.3.4,
4.1.1, 4.1.2, 4.1.3
```

### WCAG 2.2 additions (supplementary)

These SCs are added in WCAG 2.2. EN 301 549 v3.2.1 does not yet require
them. Mark the EN cell as **"Not Applicable (WCAG 2.2 criterion, not required
by EN 301 549 v3.2.1)"** unless the user requests a forward-looking
conformance statement.

```
2.4.11, 2.4.12, 2.4.13, 2.5.7, 2.5.8,
3.2.6, 3.3.7, 3.3.8, 3.3.9
```

## Clauses that default to Not Applicable for web-content audits

- **Clause 5 (Generic Requirements)** — biometrics (5.3), preservation of
  accessibility info (5.4), operable parts (5.5), locking/toggle controls
  (5.6), key repeat (5.7), double-strike key prevention (5.8), simultaneous
  user actions (5.9) are hardware/closed-functionality concerns
- **Clause 6 (Two-Way Voice)** — unless the audited site includes voice/video calling
- **Clause 7 (Video Capabilities)** — partial: 7.1.1 (Captioning playback) applies if the site plays video
- **Clause 8 (Hardware)** — N/A for web
- **Clause 10 (Non-web Documents)** — N/A unless auditing PDFs/Word
- **Clause 11 (Non-web Software)** — N/A for web-content audits
- **Clause 12 (Documentation)** — N/A unless auditing the user's documentation site
- **Clause 13 (Emergency Services / Relay)** — N/A for web

Each of these should be marked "Not Applicable" with a one-line rationale in the VPAT (e.g., "Not Applicable: the audited product is a web application and does not include non-web software components.").

## EN vs 508 summary

| Standard | WCAG version required | Web clause | Level |
|---|---|---|---|
| Section 508 (USA) | WCAG 2.0 | §501.1 | A + AA |
| EN 301 549 v3.2.1 (EU) | WCAG 2.1 | Clause 9 | A + AA |
| WCAG 2.2 (W3C) | — | — | user-selected |

When the user audits WCAG 2.2 AA, they get 508, EN 301 549 *and* WCAG 2.2 conformance information from a single run.
