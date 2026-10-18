# WCAG 2.2 success criteria — source of truth

This file enumerates **all 86 WCAG 2.2 success criteria**. It is the authoritative
index the skill uses for scoring and VPAT generation.

- WCAG 2.2 = WCAG 2.0 (38 SCs) + WCAG 2.1 additions (17) + WCAG 2.2 additions (9) − WCAG 2.2 obsolete (1) = **86 SCs**
- SCs **new in 2.2** are flagged with ★
- SC 4.1.1 Parsing was **obsoleted** in WCAG 2.2 and is not included here
- Each SC links to its W3C Understanding document

See also:
- [WCAG 2.2 Recommendation](https://www.w3.org/TR/WCAG22/)
- [How to Meet WCAG 2.2 (quick reference)](https://www.w3.org/WAI/WCAG22/quickref/)

## Guideline 1: Perceivable

### 1.1 Text Alternatives

| SC | Level | Title | Intent |
|---|---|---|---|
| [1.1.1](https://www.w3.org/WAI/WCAG22/Understanding/non-text-content) | A | Non-text Content | All non-text content has a text alternative that serves the equivalent purpose (images have alt text, icons have labels, etc.). |

### 1.2 Time-based Media

| SC | Level | Title | Intent |
|---|---|---|---|
| [1.2.1](https://www.w3.org/WAI/WCAG22/Understanding/audio-only-and-video-only-prerecorded) | A | Audio-only and Video-only (Prerecorded) | Prerecorded audio has a transcript; prerecorded silent video has a transcript or audio description. |
| [1.2.2](https://www.w3.org/WAI/WCAG22/Understanding/captions-prerecorded) | A | Captions (Prerecorded) | Synchronized captions are provided for all prerecorded audio content in video. |
| [1.2.3](https://www.w3.org/WAI/WCAG22/Understanding/audio-description-or-media-alternative-prerecorded) | A | Audio Description or Media Alternative (Prerecorded) | Prerecorded video has either an audio description or a full text media alternative. |
| [1.2.4](https://www.w3.org/WAI/WCAG22/Understanding/captions-live) | AA | Captions (Live) | Live audio content in synchronized media is captioned. |
| [1.2.5](https://www.w3.org/WAI/WCAG22/Understanding/audio-description-prerecorded) | AA | Audio Description (Prerecorded) | All prerecorded video content has audio description. |
| [1.2.6](https://www.w3.org/WAI/WCAG22/Understanding/sign-language-prerecorded) | AAA | Sign Language (Prerecorded) | Sign-language interpretation is provided for prerecorded audio in synchronized media. |
| [1.2.7](https://www.w3.org/WAI/WCAG22/Understanding/extended-audio-description-prerecorded) | AAA | Extended Audio Description (Prerecorded) | Extended audio description is provided where pauses in foreground audio are insufficient. |
| [1.2.8](https://www.w3.org/WAI/WCAG22/Understanding/media-alternative-prerecorded) | AAA | Media Alternative (Prerecorded) | Alternative for time-based media provided for all prerecorded synchronized and video-only content. |
| [1.2.9](https://www.w3.org/WAI/WCAG22/Understanding/audio-only-live) | AAA | Audio-only (Live) | Alternative for time-based media provided for live audio-only content. |

### 1.3 Adaptable

| SC | Level | Title | Intent |
|---|---|---|---|
| [1.3.1](https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships) | A | Info and Relationships | Information, structure, and relationships conveyed through presentation are programmatically determinable (semantic HTML, labels, headings, table markup). |
| [1.3.2](https://www.w3.org/WAI/WCAG22/Understanding/meaningful-sequence) | A | Meaningful Sequence | Content sequence that affects meaning is programmatically determinable (DOM order matches reading order). |
| [1.3.3](https://www.w3.org/WAI/WCAG22/Understanding/sensory-characteristics) | A | Sensory Characteristics | Instructions do not rely solely on sensory characteristics (shape, color, position, sound). |
| [1.3.4](https://www.w3.org/WAI/WCAG22/Understanding/orientation) | AA | Orientation | Content is not locked to portrait or landscape unless orientation is essential. |
| [1.3.5](https://www.w3.org/WAI/WCAG22/Understanding/identify-input-purpose) | AA | Identify Input Purpose | Input fields collecting user info use appropriate `autocomplete` values. |
| [1.3.6](https://www.w3.org/WAI/WCAG22/Understanding/identify-purpose) | AAA | Identify Purpose | Purpose of UI components, icons, and regions can be programmatically determined. |

### 1.4 Distinguishable

| SC | Level | Title | Intent |
|---|---|---|---|
| [1.4.1](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color) | A | Use of Color | Color is not the only visual means of conveying information or indicating action. |
| [1.4.2](https://www.w3.org/WAI/WCAG22/Understanding/audio-control) | A | Audio Control | Audio that plays automatically for more than 3 seconds can be paused, stopped, or its volume controlled independently. |
| [1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum) | AA | Contrast (Minimum) | Text has a contrast ratio of at least 4.5:1 (3:1 for large text) against its background. |
| [1.4.4](https://www.w3.org/WAI/WCAG22/Understanding/resize-text) | AA | Resize Text | Text can be resized up to 200% without loss of content or functionality. |
| [1.4.5](https://www.w3.org/WAI/WCAG22/Understanding/images-of-text) | AA | Images of Text | Text is used to convey information rather than images of text, except where essential. |
| [1.4.6](https://www.w3.org/WAI/WCAG22/Understanding/contrast-enhanced) | AAA | Contrast (Enhanced) | Text has a contrast ratio of at least 7:1 (4.5:1 for large text). |
| [1.4.7](https://www.w3.org/WAI/WCAG22/Understanding/low-or-no-background-audio) | AAA | Low or No Background Audio | Prerecorded audio-only content with speech has no or low background noise. |
| [1.4.8](https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation) | AAA | Visual Presentation | Blocks of text support user-adjustable foreground/background colors, width, spacing, etc. |
| [1.4.9](https://www.w3.org/WAI/WCAG22/Understanding/images-of-text-no-exception) | AAA | Images of Text (No Exception) | Images of text are used only for decoration or where essential. |
| [1.4.10](https://www.w3.org/WAI/WCAG22/Understanding/reflow) | AA | Reflow | Content can be presented at 320 CSS pixels wide without horizontal scrolling (loss of info). |
| [1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast) | AA | Non-text Contrast | UI components and meaningful graphics have a contrast ratio of at least 3:1 against adjacent colors. |
| [1.4.12](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing) | AA | Text Spacing | No loss of content/functionality when user overrides line height, letter/word/paragraph spacing. |
| [1.4.13](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus) | AA | Content on Hover or Focus | Content revealed on hover/focus is dismissible, hoverable, and persistent. |

## Guideline 2: Operable

### 2.1 Keyboard Accessible

| SC | Level | Title | Intent |
|---|---|---|---|
| [2.1.1](https://www.w3.org/WAI/WCAG22/Understanding/keyboard) | A | Keyboard | All functionality is operable through a keyboard interface. |
| [2.1.2](https://www.w3.org/WAI/WCAG22/Understanding/no-keyboard-trap) | A | No Keyboard Trap | Keyboard focus is not trapped on any component; user can navigate away with standard keystrokes. |
| [2.1.3](https://www.w3.org/WAI/WCAG22/Understanding/keyboard-no-exception) | AAA | Keyboard (No Exception) | All functionality operable via keyboard without timing requirements. |
| [2.1.4](https://www.w3.org/WAI/WCAG22/Understanding/character-key-shortcuts) | A | Character Key Shortcuts | Single-character keyboard shortcuts can be turned off, remapped, or are active only on focus. |

### 2.2 Enough Time

| SC | Level | Title | Intent |
|---|---|---|---|
| [2.2.1](https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable) | A | Timing Adjustable | Users can turn off, adjust, or extend time limits. |
| [2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide) | A | Pause, Stop, Hide | Moving, blinking, scrolling, or auto-updating content can be paused, stopped, or hidden. |
| [2.2.3](https://www.w3.org/WAI/WCAG22/Understanding/no-timing) | AAA | No Timing | Timing is not essential to the event or activity. |
| [2.2.4](https://www.w3.org/WAI/WCAG22/Understanding/interruptions) | AAA | Interruptions | Interruptions can be postponed or suppressed by the user. |
| [2.2.5](https://www.w3.org/WAI/WCAG22/Understanding/re-authenticating) | AAA | Re-authenticating | After a session expires, user can continue without losing data upon re-authentication. |
| [2.2.6](https://www.w3.org/WAI/WCAG22/Understanding/timeouts) | AAA | Timeouts | Users are warned about user-inactivity timeouts that could cause data loss. |

### 2.3 Seizures and Physical Reactions

| SC | Level | Title | Intent |
|---|---|---|---|
| [2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold) | A | Three Flashes or Below Threshold | No content flashes more than 3 times per second or flashes are below general/red flash thresholds. |
| [2.3.2](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes) | AAA | Three Flashes | No content flashes more than 3 times per second. |
| [2.3.3](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions) | AAA | Animation from Interactions | Motion animation from interactions can be disabled unless essential. |

### 2.4 Navigable

| SC | Level | Title | Intent |
|---|---|---|---|
| [2.4.1](https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks) | A | Bypass Blocks | A mechanism exists to bypass blocks of content repeated on multiple pages (skip link). |
| [2.4.2](https://www.w3.org/WAI/WCAG22/Understanding/page-titled) | A | Page Titled | Pages have titles that describe topic or purpose. |
| [2.4.3](https://www.w3.org/WAI/WCAG22/Understanding/focus-order) | A | Focus Order | Components receive focus in a sequence that preserves meaning and operability. |
| [2.4.4](https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context) | A | Link Purpose (In Context) | Purpose of each link can be determined from the link text alone or with its context. |
| [2.4.5](https://www.w3.org/WAI/WCAG22/Understanding/multiple-ways) | AA | Multiple Ways | More than one way is available to locate a web page within a set. |
| [2.4.6](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels) | AA | Headings and Labels | Headings and labels describe topic or purpose. |
| [2.4.7](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible) | AA | Focus Visible | Keyboard-operable UI has a visible focus indicator. |
| [2.4.8](https://www.w3.org/WAI/WCAG22/Understanding/location) | AAA | Location | User's location within a set of pages is available. |
| [2.4.9](https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-link-only) | AAA | Link Purpose (Link Only) | Link purpose is identifiable from link text alone. |
| [2.4.10](https://www.w3.org/WAI/WCAG22/Understanding/section-headings) | AAA | Section Headings | Section headings are used to organize content. |
| [2.4.11](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum) | AA | ★ Focus Not Obscured (Minimum) | Focused component is not entirely hidden by author-created content (e.g., sticky headers). |
| [2.4.12](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-enhanced) | AAA | ★ Focus Not Obscured (Enhanced) | Focused component is not obscured at all by author-created content. |
| [2.4.13](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance) | AAA | ★ Focus Appearance | Focus indicator meets minimum size and contrast requirements. |

### 2.5 Input Modalities

| SC | Level | Title | Intent |
|---|---|---|---|
| [2.5.1](https://www.w3.org/WAI/WCAG22/Understanding/pointer-gestures) | A | Pointer Gestures | Multipoint or path-based gestures have a single-pointer alternative. |
| [2.5.2](https://www.w3.org/WAI/WCAG22/Understanding/pointer-cancellation) | A | Pointer Cancellation | Functions triggered by single-pointer are cancelable (up-event, abort, reversible). |
| [2.5.3](https://www.w3.org/WAI/WCAG22/Understanding/label-in-name) | A | Label in Name | Visible label text is contained in the accessible name of the component. |
| [2.5.4](https://www.w3.org/WAI/WCAG22/Understanding/motion-actuation) | A | Motion Actuation | Functions operated by device motion can also be operated by UI and can be disabled. |
| [2.5.5](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced) | AAA | Target Size (Enhanced) | Pointer targets are at least 44×44 CSS pixels. |
| [2.5.6](https://www.w3.org/WAI/WCAG22/Understanding/concurrent-input-mechanisms) | AAA | Concurrent Input Mechanisms | Content does not restrict input to a single modality. |
| [2.5.7](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements) | AA | ★ Dragging Movements | Functions using dragging have a single-pointer non-dragging alternative. |
| [2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum) | AA | ★ Target Size (Minimum) | Pointer targets are at least 24×24 CSS pixels (with exceptions). |

## Guideline 3: Understandable

### 3.1 Readable

| SC | Level | Title | Intent |
|---|---|---|---|
| [3.1.1](https://www.w3.org/WAI/WCAG22/Understanding/language-of-page) | A | Language of Page | Default human language of each page is programmatically determinable (`<html lang>`). |
| [3.1.2](https://www.w3.org/WAI/WCAG22/Understanding/language-of-parts) | AA | Language of Parts | Language of passages differing from page default is programmatically determinable. |
| [3.1.3](https://www.w3.org/WAI/WCAG22/Understanding/unusual-words) | AAA | Unusual Words | Definitions of idioms and jargon are provided. |
| [3.1.4](https://www.w3.org/WAI/WCAG22/Understanding/abbreviations) | AAA | Abbreviations | Expanded form or meaning of abbreviations is available. |
| [3.1.5](https://www.w3.org/WAI/WCAG22/Understanding/reading-level) | AAA | Reading Level | Text requiring reading above lower-secondary level has a supplemental version. |
| [3.1.6](https://www.w3.org/WAI/WCAG22/Understanding/pronunciation) | AAA | Pronunciation | Pronunciation is available where meaning is ambiguous without it. |

### 3.2 Predictable

| SC | Level | Title | Intent |
|---|---|---|---|
| [3.2.1](https://www.w3.org/WAI/WCAG22/Understanding/on-focus) | A | On Focus | Receiving focus does not initiate a change of context. |
| [3.2.2](https://www.w3.org/WAI/WCAG22/Understanding/on-input) | A | On Input | Changing a control's setting does not automatically cause a change of context unless warned. |
| [3.2.3](https://www.w3.org/WAI/WCAG22/Understanding/consistent-navigation) | AA | Consistent Navigation | Navigational mechanisms repeated across pages occur in the same relative order. |
| [3.2.4](https://www.w3.org/WAI/WCAG22/Understanding/consistent-identification) | AA | Consistent Identification | Components with the same functionality are identified consistently. |
| [3.2.5](https://www.w3.org/WAI/WCAG22/Understanding/change-on-request) | AAA | Change on Request | Changes of context are initiated only by user request, or a mechanism to turn them off. |
| [3.2.6](https://www.w3.org/WAI/WCAG22/Understanding/consistent-help) | A | ★ Consistent Help | Help mechanisms (contact, chat, etc.) appear in the same relative order across pages. |

### 3.3 Input Assistance

| SC | Level | Title | Intent |
|---|---|---|---|
| [3.3.1](https://www.w3.org/WAI/WCAG22/Understanding/error-identification) | A | Error Identification | Input errors are identified and described to the user in text. |
| [3.3.2](https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions) | A | Labels or Instructions | Labels or instructions are provided when content requires user input. |
| [3.3.3](https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion) | AA | Error Suggestion | Suggestions for correcting input errors are provided if known. |
| [3.3.4](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data) | AA | Error Prevention (Legal, Financial, Data) | Submissions causing legal/financial/data changes are reversible, checked, or confirmed. |
| [3.3.5](https://www.w3.org/WAI/WCAG22/Understanding/help) | AAA | Help | Context-sensitive help is available. |
| [3.3.6](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-all) | AAA | Error Prevention (All) | All submissions are reversible, checked, or confirmed. |
| [3.3.7](https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry) | A | ★ Redundant Entry | Information previously entered in a process is auto-populated or selectable. |
| [3.3.8](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum) | AA | ★ Accessible Authentication (Minimum) | Authentication does not require a cognitive function test without alternative. |
| [3.3.9](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-enhanced) | AAA | ★ Accessible Authentication (Enhanced) | Authentication does not require any cognitive function test. |

## Guideline 4: Robust

### 4.1 Compatible

| SC | Level | Title | Intent |
|---|---|---|---|
| ~~4.1.1~~ | — | ~~Parsing~~ | **OBSOLETED in WCAG 2.2** (no longer a requirement). |
| [4.1.2](https://www.w3.org/WAI/WCAG22/Understanding/name-role-value) | A | Name, Role, Value | For all UI components, name, role, and value are programmatically determinable. |
| [4.1.3](https://www.w3.org/WAI/WCAG22/Understanding/status-messages) | AA | Status Messages | Status messages can be determined programmatically without receiving focus (ARIA live regions). |

## Summary counts

| Level | Count |
|---|---|
| A | 31 |
| AA | 24 |
| AAA | 31 |
| **Total** | **86** |

New-in-2.2 (★): 9 SCs — 2.4.11, 2.4.12, 2.4.13, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8, 3.3.9.
