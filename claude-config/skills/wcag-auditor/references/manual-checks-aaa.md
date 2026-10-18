# Manual checks — WCAG AAA success criteria

Level AAA is **opt-in** (`audit.mjs --level AAA` / `audit-site.mjs --level AAA`).
Most AAA criteria require manual verification. This file lists the AAA
criteria Claude should walk through in AAA audits, using the same Playwright
MCP tooling as `manual-checks.md`.

⚠️ **AAA is aspirational.** W3C explicitly states: *"It is not recommended that
Level AAA conformance be required as a general policy for entire sites because
it is not possible to satisfy all Level AAA Success Criteria for some content."*
Use AAA findings as targets, not blockers.

---

## Perceivable — AAA

### SC 1.2.6 Sign Language (Prerecorded), SC 1.2.7 Extended Audio Description, SC 1.2.8 Media Alternative, SC 1.2.9 Audio-only (Live)

Review media content for sign-language interpretation, extended audio
description tracks, full text alternatives, and live audio alternatives. Most
web apps: N/A unless they ship substantial media content.

### SC 1.3.6 Identify Purpose (AAA)

Check for ARIA landmarks, `role` attributes, and semantic markup that lets
assistive tech understand UI component purpose (e.g., `role="search"`,
`role="navigation"`, proper heading structure throughout).

### SC 1.4.6 Contrast (Enhanced) (AAA)

Text contrast ratio ≥ 7:1 (4.5:1 for large text). axe with the `color-contrast-enhanced` rule (part of AAA tag set) catches this — verify it was included in the audit.

### SC 1.4.7 Low or No Background Audio (AAA)

Prerecorded audio-only with speech should have no or very quiet background noise.

### SC 1.4.8 Visual Presentation (AAA)

Blocks of text allow user customization: foreground/background colors, width
≤80 characters, no justification, line spacing ≥1.5, paragraph spacing ≥2× line height, resize to 200% without horizontal scroll.

### SC 1.4.9 Images of Text (No Exception) (AAA)

Stricter than 1.4.5 — no images of text permitted except logos and essential cases.

---

## Operable — AAA

### SC 2.1.3 Keyboard (No Exception) (AAA)

All functionality operable via keyboard with no timing requirements. Stricter than 2.1.1.

### SC 2.2.3 No Timing (AAA)

No timing requirements except in real-time events (auctions, live captions).

### SC 2.2.4 Interruptions (AAA)

Users can postpone or suppress interruptions except emergencies.

### SC 2.2.5 Re-authenticating (AAA)

After session expiration, users can re-authenticate without losing data.

### SC 2.2.6 Timeouts (AAA)

Users are warned about inactivity timeouts that could cause data loss, unless data is preserved for ≥20 hours.

### SC 2.3.2 Three Flashes (AAA)

Stricter than 2.3.1 — absolutely no content flashes more than 3 times per second, no threshold exceptions.

### SC 2.3.3 Animation from Interactions (AAA)

Motion animation from interactions can be disabled. Check `prefers-reduced-motion` media query support:
```js
window.matchMedia('(prefers-reduced-motion: reduce)').matches
```

### SC 2.4.8 Location (AAA)

User's location within a set of pages is available (breadcrumbs, current-page indicator in nav).

### SC 2.4.9 Link Purpose (Link Only) (AAA)

Link text alone is sufficient to understand purpose. Stricter than 2.4.4.

### SC 2.4.10 Section Headings (AAA)

Sections of content use headings to organize them.

### SC 2.4.12 Focus Not Obscured (Enhanced) (AAA) ★ new in 2.2

Focused element is **not obscured at all** by author-created content. Stricter than 2.4.11 (Minimum).

### SC 2.4.13 Focus Appearance (AAA) ★ new in 2.2

Focus indicator meets minimum size and contrast:
- Encloses the component (or at least as large as a 2 CSS-pixel-thick perimeter)
- Contrast ratio ≥ 3:1 between focused and unfocused states of the same pixels

Use `browser_take_screenshot` of focused elements to verify.

### SC 2.5.5 Target Size (Enhanced) (AAA)

Pointer targets ≥ 44×44 CSS pixels. Same procedure as SC 2.5.8 with a 44×44 threshold.

### SC 2.5.6 Concurrent Input Mechanisms (AAA)

Content does not restrict input to a single modality (e.g., don't force touch-only on mobile).

---

## Understandable — AAA

### SC 3.1.3 Unusual Words (AAA)

Definitions provided for idioms, jargon, specialized vocabulary.

### SC 3.1.4 Abbreviations (AAA)

Expanded form or meaning available for abbreviations on first use or via `<abbr title>`.

### SC 3.1.5 Reading Level (AAA)

Text requiring reading ability above lower-secondary level has a supplemental simplified version or summary.

### SC 3.1.6 Pronunciation (AAA)

Pronunciation is available where meaning is ambiguous without it (e.g., "record" the verb vs. noun).

### SC 3.2.5 Change on Request (AAA)

Context changes are initiated only by user request, or a mechanism is available to turn off such changes.

### SC 3.3.5 Help (AAA)

Context-sensitive help is available (tooltips, inline help text, help links).

### SC 3.3.6 Error Prevention (All) (AAA)

Stricter than 3.3.4 — **all** submissions are reversible, validated, or confirmed.

### SC 3.3.9 Accessible Authentication (Enhanced) (AAA) ★ new in 2.2

No cognitive function test required in authentication, **with no alternative exceptions**. Stricter than 3.3.8.
