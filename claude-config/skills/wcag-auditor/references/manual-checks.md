# Manual checks — WCAG 2.2 criteria axe cannot automate

axe-core catches approximately 30–40% of WCAG failures automatically. The rest
require human judgment or interactive testing. This file lists the Level A and
AA success criteria that need manual verification, with **specific Playwright
MCP procedures** Claude should run during the manual-check pass.

AAA-only manual checks live in `manual-checks-aaa.md`.

## How to use this file

After the automated `audit-site.mjs` pass completes, Claude walks each URL and
runs the relevant checks below, using Playwright MCP tools:

- `mcp__plugin_playwright_playwright__browser_navigate` — load the URL
- `mcp__plugin_playwright_playwright__browser_snapshot` — inspect accessibility tree
- `mcp__plugin_playwright_playwright__browser_press_key` — keyboard navigation (Tab, Shift+Tab, Enter, Escape, arrow keys)
- `mcp__plugin_playwright_playwright__browser_evaluate` — DOM queries, focus checks, computed style
- `mcp__plugin_playwright_playwright__browser_take_screenshot` — visual verification
- `mcp__plugin_playwright_playwright__browser_resize` — viewport/orientation tests
- `mcp__plugin_playwright_playwright__browser_hover` — hover/tooltip tests
- `mcp__plugin_playwright_playwright__browser_click` — interaction tests

Report each manual finding with the same structure as axe violations: cite the
SC, describe the failure, propose a fix.

---

## Perceivable — manual checks

### SC 1.2.1–1.2.5 Time-based Media (A, AA)

**What to check:** every `<video>`, `<audio>`, and embedded media player.

**Procedure:**
1. `browser_evaluate`: `document.querySelectorAll('video, audio, iframe[src*="youtube"], iframe[src*="vimeo"]').length`
2. For each media element, verify:
   - Captions track present (`<track kind="captions">` or platform captions enabled)
   - Transcript linked nearby (for audio-only)
   - Audio description available (for video with meaningful visuals)
3. If the page has no media, mark **N/A**.

### SC 1.3.2 Meaningful Sequence (A)

**What to check:** DOM order matches visual reading order.

**Procedure:**
1. `browser_snapshot` — inspect the accessibility tree order
2. `browser_take_screenshot` — compare visual layout
3. Flag any CSS that reorders content visually (`float`, `flex-direction: row-reverse`, `grid` with explicit placement, `order` property) in a way that breaks reading sequence for screen readers.

### SC 1.3.3 Sensory Characteristics (A)

**What to check:** instructions don't rely on shape, size, position, or sound alone.

**Procedure:** read page text for phrases like "click the button on the right,"
"the round icon," "see below," "press the green button." These instructions
fail when the user can't perceive the sensory characteristic referenced.

### SC 1.3.4 Orientation (AA)

**What to check:** content works in both portrait and landscape.

**Procedure:**
1. `browser_resize` to 375×812 (portrait phone)
2. `browser_take_screenshot` and `browser_snapshot`
3. `browser_resize` to 812×375 (landscape phone)
4. `browser_take_screenshot` and `browser_snapshot`
5. Verify content is not locked, rotated, or hidden in either orientation.
6. Check CSS for `@media (orientation: portrait)` blocks that disable functionality.

### SC 1.4.1 Use of Color (A)

**What to check:** color is not the only means of conveying information.

**Procedure:** look for:
- Required form fields indicated only by red label text
- Error states shown only as red border (no icon, no text)
- Link text that is visually distinguished only by color (needs underline or other)
- Charts/graphs that distinguish series only by color

Each instance is a failure.

### SC 1.4.2 Audio Control (A)

**What to check:** any audio that plays automatically for >3s has pause/stop/volume control.

**Procedure:**
1. `browser_navigate` to the page
2. `browser_evaluate`: check for `<audio autoplay>`, `<video autoplay>` without `muted`, or JS-initiated audio
3. Listen for auto-playing audio; verify controls present.

### SC 1.4.4 Resize Text (AA)

**What to check:** content remains usable at 200% zoom.

**Procedure:**
1. `browser_evaluate`: `document.body.style.zoom = '200%'` (or use `browser_resize` to simulate by halving viewport)
2. `browser_take_screenshot`
3. Verify no content overlaps, no horizontal scroll required for main content, all functionality remains reachable.

### SC 1.4.5 Images of Text (AA)

**What to check:** text rendered as images rather than HTML text.

**Procedure:** review all `<img>` elements and background images. Logos and
essential images (infographics with intrinsic styling) are exempt. Marketing
hero images containing text-heavy content are typically failures.

### SC 1.4.10 Reflow (AA)

**What to check:** no horizontal scrolling at 320 CSS pixels wide.

**Procedure:**
1. `browser_resize` to 320×800
2. `browser_take_screenshot`
3. `browser_evaluate`: `document.documentElement.scrollWidth > window.innerWidth` → should be `false`
4. Scroll the page and verify no content is cut off or requires horizontal scrolling.

Exceptions: data tables, maps, games, slide decks — content that genuinely
requires 2D layout is exempt.

### SC 1.4.13 Content on Hover or Focus (AA)

**What to check:** tooltips and hover-revealed content are dismissible, hoverable, and persistent.

**Procedure:**
1. `browser_hover` over each element that shows hover-triggered content
2. Verify:
   - **Dismissible:** Escape key closes it without moving pointer
   - **Hoverable:** pointer can move onto the revealed content without dismissing it
   - **Persistent:** content stays visible until hover ends, user dismisses, or content becomes invalid

---

## Operable — manual checks

### SC 2.1.1 Keyboard (A)

**What to check:** all functionality is keyboard-operable.

**Procedure:**
1. `browser_press_key('Tab')` repeatedly from page top
2. Record every interactive element reached
3. For each, verify:
   - It can be activated (Enter/Space for buttons, arrow keys for menus, etc.)
   - Custom widgets (dropdowns, date pickers, sliders) respond to expected key patterns

Flag any interactive element that requires mouse/pointer.

### SC 2.1.2 No Keyboard Trap (A)

**What to check:** keyboard focus can always escape.

**Procedure:**
1. `browser_press_key('Tab')` through the page
2. For each widget (modal, dropdown, date picker, embedded iframe), verify Tab/Shift+Tab eventually moves focus out
3. Escape should close modals and return focus to the trigger

If focus gets stuck in any widget, that's a failure.

### SC 2.1.4 Character Key Shortcuts (A)

**What to check:** single-letter shortcuts can be turned off or require a modifier.

**Procedure:** `browser_evaluate` for global keyboard listeners:
```js
// look for addEventListener('keydown' / 'keypress') at document/window scope
```
Test a few single characters ('s', 'j', 'k') — if they trigger actions without a modifier, verify the app exposes a way to disable or remap them.

### SC 2.2.1 Timing Adjustable (A) / SC 2.2.2 Pause, Stop, Hide (A)

**What to check:** auto-refreshing content, carousels, countdown timers.

**Procedure:** look for:
- Carousels auto-advancing — must have pause control
- Session timeouts — must warn user and allow extension
- Countdown timers — must be adjustable or essential

### SC 2.3.1 Three Flashes or Below Threshold (A)

**What to check:** no rapid flashing animations.

**Procedure:** review animated GIFs, video content, and CSS animations for
flashing faster than 3 times per second. Most modern sites pass; flag if
present.

### SC 2.4.1 Bypass Blocks (A)

**What to check:** a skip link exists to bypass repeated navigation.

**Procedure:**
1. Load page, immediately `browser_press_key('Tab')` once
2. Verify first focused element is a visible "Skip to main content" link (or similar)
3. Verify pressing Enter on it moves focus to `<main>` or the primary content

Alternative: multiple `<nav>` and `<main>` landmarks satisfy this at Level A.

### SC 2.4.3 Focus Order (A)

**What to check:** Tab order preserves meaning and operability.

**Procedure:**
1. `browser_press_key('Tab')` from page top to bottom
2. `browser_evaluate`: log `document.activeElement` at each step
3. Verify sequence matches visual layout and logical flow; flag any `tabindex` value > 0 (anti-pattern).

### SC 2.4.4 Link Purpose (In Context) (A)

**What to check:** link text is descriptive.

**Procedure:** review all links for text like "click here," "read more,"
"learn more," "here." Each is a failure unless programmatically associated
with sufficient context (e.g., `aria-labelledby` referencing surrounding text).

### SC 2.4.5 Multiple Ways (AA)

**What to check:** more than one way to find pages (nav menu + search, or nav + sitemap).

**Procedure:** confirm the site has at least two of: navigation menu, search, site map, table of contents, A–Z index.

### SC 2.4.6 Headings and Labels (AA)

**What to check:** headings and labels are descriptive.

**Procedure:** review `<h1>`–`<h6>` text and `<label>` text. Generic labels
like "Section," "Form," or unlabeled sections of content are failures. axe
catches empty labels; only humans judge descriptiveness.

### SC 2.4.7 Focus Visible (AA) ⚠️ CRITICAL

**What to check:** keyboard focus has a visible indicator.

**Procedure:**
1. `browser_press_key('Tab')` through all focusable elements
2. For each focused element, `browser_take_screenshot`
3. `browser_evaluate`: `getComputedStyle(document.activeElement, ':focus').outline` — verify not `none`/`0` with no replacement
4. Flag any element whose focus state is visually indistinguishable from its default state.

**Common failure:** CSS rule `*:focus { outline: none }` without a replacement focus indicator.

### SC 2.4.11 Focus Not Obscured (Minimum) (AA) ★ new in 2.2

**What to check:** focused element is not entirely hidden by sticky headers, footers, or overlays.

**Procedure:**
1. `browser_press_key('Tab')` through the page
2. At each step, `browser_take_screenshot` and verify the focused element is at least partially visible
3. Pay special attention to pages with `position: sticky` or `fixed` headers/footers that might cover focused content as the user tabs past them.

### SC 2.5.1 Pointer Gestures (A)

**What to check:** multipoint / path-based gestures have single-pointer alternatives.

**Procedure:** identify pinch-zoom, swipe, drag gestures; verify each has an
alternative (button, keyboard shortcut).

### SC 2.5.2 Pointer Cancellation (A)

**What to check:** single-pointer actions trigger on up-event, not down.

**Procedure:** test critical buttons — pressing mouse-down then moving off and
releasing should NOT trigger the action.

### SC 2.5.3 Label in Name (A)

**What to check:** visible label text appears in the accessible name.

**Procedure:** `browser_snapshot` and compare each button/link's visible text
to its accessible name. If visible text is "Submit" but accessible name is
"Send form," voice-control users saying "click submit" will fail.

### SC 2.5.4 Motion Actuation (A)

**What to check:** features triggered by device motion (shake, tilt) have UI alternatives and can be disabled.

**Procedure:** most web apps: N/A. If device-motion APIs are used, verify alternative UI.

### SC 2.5.7 Dragging Movements (AA) ★ new in 2.2

**What to check:** drag-and-drop has a click-based alternative.

**Procedure:** identify drag-and-drop UIs (kanban boards, file uploads, sliders). Verify each has a non-dragging alternative (buttons, keyboard, file picker dialog).

### SC 2.5.8 Target Size (Minimum) (AA) ★ new in 2.2

**What to check:** pointer targets are at least 24×24 CSS pixels.

**Procedure:**
```js
// browser_evaluate
const targets = document.querySelectorAll('a, button, input[type="button"], input[type="submit"], input[type="checkbox"], input[type="radio"], [role="button"], [role="link"]');
const small = [...targets].filter(el => {
  const r = el.getBoundingClientRect();
  return r.width < 24 || r.height < 24;
}).map(el => ({ tag: el.tagName, text: el.textContent?.trim().slice(0, 40), w: r.width, h: r.height }));
```
Exceptions: inline links in sentences, targets with ≥24px spacing, user-agent-styled controls.

---

## Understandable — manual checks

### SC 3.1.2 Language of Parts (AA)

**What to check:** content in a non-page-default language has `lang` attribute.

**Procedure:** scan page text for phrases in languages other than the `<html lang>` value. Each should be wrapped with appropriate `lang` attribute.

### SC 3.2.1 On Focus (A) / SC 3.2.2 On Input (A)

**What to check:** focusing or changing a control doesn't cause unexpected context change.

**Procedure:**
1. Tab to each `<select>`, checkbox, radio, input
2. Change the value — verify no navigation happens
3. Flag any form that auto-submits on select change without warning.

### SC 3.2.3 Consistent Navigation (AA) / SC 3.2.4 Consistent Identification (AA) / SC 3.2.6 Consistent Help (A) ★

**What to check:** navigation, icons, and help links appear in the same relative order across pages.

**Procedure:** compare two or more pages; confirm nav, icons, and help entry points don't shuffle between pages.

### SC 3.3.1 Error Identification (A) / SC 3.3.3 Error Suggestion (AA)

**What to check:** form validation errors are identified in text and suggest corrections.

**Procedure:**
1. Fill forms with invalid data and submit
2. Verify error messages appear, are programmatically associated with the field, and suggest how to fix.

### SC 3.3.4 Error Prevention (Legal, Financial, Data) (AA)

**What to check:** submissions that commit legal/financial/data changes are reversible, checked, or confirmed.

**Procedure:** for any destructive action (delete account, purchase, submit tax form), verify one of: reversible action, data validation + confirmation step, or final review/submit step.

### SC 3.3.7 Redundant Entry (A) ★ new in 2.2

**What to check:** multi-step forms don't require re-entering information.

**Procedure:** walk through any multi-step process. Info entered in step 1 should be auto-populated or selectable in step 3, not retyped.

### SC 3.3.8 Accessible Authentication (Minimum) (AA) ★ new in 2.2

**What to check:** authentication does not rely on a cognitive function test without alternative.

**Procedure:** review login flow. CAPTCHA/puzzle/memory tests fail unless:
- Password manager autofill is supported (don't block paste into password fields)
- Alternative auth method is offered (email magic link, biometric, SSO)
- A mechanism helps users complete the test

Check: `browser_evaluate` on the login form — does it block paste? `onpaste="return false"` or similar is a failure.

---

## Robust — manual checks

Level A and AA robust criteria (4.1.2, 4.1.3) are mostly caught by axe.
Manual verification is minimal for this guideline.
