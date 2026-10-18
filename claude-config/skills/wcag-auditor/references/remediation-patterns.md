# Remediation patterns

Fix library for the most common axe rules. Each entry contains the failing
pattern, two or three corrected snippets (HTML, JSX, ARIA), and the WCAG SC
it addresses.

Claude uses this file during the **conversational triage** step to propose
concrete Edit-tool diffs against the user's source. For every violation, Claude:

1. Locates the offending code in the user's repo (matching axe's CSS selector /
   HTML snippet)
2. Picks the closest matching pattern from this file
3. Proposes an Edit diff the user can apply

---

## `image-alt` (SC 1.1.1, Level A)

Every `<img>` needs an `alt` attribute. Decorative images use `alt=""`.

**Bad:**
```html
<img src="/hero.jpg" />
```

**Good (informative image):**
```html
<img src="/hero.jpg" alt="Team of engineers collaborating at a whiteboard" />
```

**Good (decorative image):**
```html
<img src="/decorative-swoosh.svg" alt="" role="presentation" />
```

**JSX equivalent:**
```jsx
<img src="/hero.jpg" alt="Team of engineers collaborating at a whiteboard" />
```

Rule of thumb: if the image conveys information or functionality, describe it.
If it's purely decorative (background art, divider graphics), use `alt=""`.

---

## `input-image-alt` (SC 1.1.1 + 4.1.2, Level A)

`<input type="image">` needs `alt` describing its function.

**Bad:**
```html
<input type="image" src="/search.png" />
```

**Good:**
```html
<input type="image" src="/search.png" alt="Search" />
```

---

## `color-contrast` (SC 1.4.3, Level AA)

Text needs a contrast ratio of at least 4.5:1 (3:1 for text ≥18pt or ≥14pt bold).

**Bad:**
```css
.muted { color: #aaaaaa; background: #ffffff; }  /* 2.3:1 */
```

**Good:**
```css
.muted { color: #595959; background: #ffffff; }  /* 7.0:1 */
```

**Tailwind equivalent:**
```jsx
// Bad: text-gray-400 on white → ~2.9:1
<p className="text-gray-400 bg-white">...</p>
// Good: text-gray-600 on white → ~7.6:1
<p className="text-gray-600 bg-white">...</p>
```

Verify with a contrast checker. Common culprits: placeholder text, disabled states, footer copy.

---

## `label` (SC 3.3.2 + 4.1.2, Level A)

Every form input needs an accessible label.

**Bad:**
```html
<input type="email" name="email" placeholder="you@example.com" />
```

**Good (explicit label):**
```html
<label for="email">Email address</label>
<input id="email" type="email" name="email" />
```

**Good (wrapping label):**
```html
<label>
  Email address
  <input type="email" name="email" />
</label>
```

**Good (aria-label, when visible label is undesirable):**
```html
<input type="search" name="q" aria-label="Search" />
```

**JSX:**
```jsx
<label htmlFor="email">Email address</label>
<input id="email" type="email" name="email" />
```

**Do not** rely on `placeholder` as a label — it disappears on input and often has contrast issues.

---

## `button-name` (SC 4.1.2, Level A)

Every `<button>` needs accessible text content.

**Bad:**
```html
<button><svg>...</svg></button>
```

**Good (visible text):**
```html
<button>Submit</button>
```

**Good (icon button with aria-label):**
```html
<button aria-label="Close dialog">
  <svg aria-hidden="true">...</svg>
</button>
```

**Good (visually hidden text):**
```html
<button>
  <svg aria-hidden="true">...</svg>
  <span class="sr-only">Close dialog</span>
</button>
```

---

## `link-name` (SC 2.4.4 + 4.1.2, Level A)

Every `<a>` needs accessible text describing the link's purpose.

**Bad:**
```html
<a href="/docs"><img src="/icon.svg" /></a>
```

**Good:**
```html
<a href="/docs" aria-label="Documentation">
  <img src="/icon.svg" alt="" />
</a>
```

**Also bad** (ambiguous text — caught by manual review, not always axe):
```html
<a href="/pricing">click here</a>
```

**Good:**
```html
<a href="/pricing">See our pricing plans</a>
```

---

## `list` / `listitem` (SC 1.3.1, Level A)

`<ul>` and `<ol>` must contain only `<li>` children (plus `<script>` and
`<template>`). `<li>` must be inside a list.

**Bad:**
```html
<ul>
  <div>Item one</div>
  <div>Item two</div>
</ul>
```

**Good:**
```html
<ul>
  <li>Item one</li>
  <li>Item two</li>
</ul>
```

**If the list is styled as blocks:** keep semantic `<li>` and restyle:
```css
ul { list-style: none; padding: 0; }
li { display: block; padding: 1rem; border: 1px solid #ccc; }
```

---

## `html-has-lang` / `html-lang-valid` (SC 3.1.1, Level A)

`<html>` needs a valid `lang` attribute.

**Bad:**
```html
<html>
```

**Good:**
```html
<html lang="en">
```

**JSX (Next.js App Router `app/layout.tsx`):**
```jsx
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

---

## `document-title` (SC 2.4.2, Level A)

Every page needs a non-empty `<title>`.

**Bad:**
```html
<head><title></title></head>
```

**Good:**
```html
<head><title>Pricing — Acme</title></head>
```

**JSX (Next.js App Router):**
```jsx
export const metadata = { title: 'Pricing — Acme' };
```

---

## `form-field-multiple-labels` (SC 3.3.2, Level A)

A form field should have exactly one label association.

**Bad:**
```html
<label for="name">Name</label>
<label for="name">Required</label>
<input id="name" />
```

**Good:**
```html
<label for="name">Name <span>(required)</span></label>
<input id="name" required />
```

---

## `frame-title` (SC 2.4.1 + 4.1.2, Level A)

`<iframe>` needs a descriptive `title` attribute.

**Bad:**
```html
<iframe src="/embed/video"></iframe>
```

**Good:**
```html
<iframe src="/embed/video" title="Product demo video"></iframe>
```

---

## `meta-viewport` (SC 1.4.4, Level AA)

Don't block pinch-to-zoom. The `user-scalable=no` and `maximum-scale<2` values fail.

**Bad:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
```

**Good:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1" />
```

---

## Table rules — `td-has-header`, `th-has-data-cells`, `td-headers-attr` (SC 1.3.1, Level A)

Data tables need `<th>` headers properly associated with data cells.

**Bad:**
```html
<table>
  <tr><td>Alice</td><td>Engineering</td></tr>
  <tr><td>Bob</td><td>Design</td></tr>
</table>
```

**Good (simple data table):**
```html
<table>
  <thead>
    <tr><th scope="col">Name</th><th scope="col">Department</th></tr>
  </thead>
  <tbody>
    <tr><td>Alice</td><td>Engineering</td></tr>
    <tr><td>Bob</td><td>Design</td></tr>
  </tbody>
</table>
```

**Good (complex table with headers/id):**
```html
<table>
  <tr>
    <th id="name">Name</th>
    <th id="dept">Department</th>
  </tr>
  <tr>
    <td headers="name">Alice</td>
    <td headers="dept">Engineering</td>
  </tr>
</table>
```

Do not use tables for layout. If the content is not tabular data, use
`<div>` / flexbox / grid instead.

---

## `aria-valid-attr` / `aria-valid-attr-value` (SC 4.1.2, Level A)

ARIA attributes must exist in the spec and have valid values.

**Bad:**
```html
<button aria-labeledby="heading">Submit</button>   <!-- typo: should be aria-labelledby -->
<div role="headline">...</div>                      <!-- invalid role -->
<button aria-pressed="yes">Toggle</button>          <!-- must be "true"/"false"/"mixed" -->
```

**Good:**
```html
<button aria-labelledby="heading">Submit</button>
<div role="banner">...</div>
<button aria-pressed="true">Toggle</button>
```

---

## `aria-required-attr` (SC 4.1.2, Level A)

Elements with certain ARIA roles require specific attributes.

**Bad:**
```html
<div role="checkbox">Subscribe</div>   <!-- missing aria-checked -->
<div role="slider">Volume</div>         <!-- missing aria-valuenow/min/max -->
```

**Good:**
```html
<div role="checkbox" aria-checked="false" tabindex="0">Subscribe</div>
<div role="slider" aria-valuenow="50" aria-valuemin="0" aria-valuemax="100" tabindex="0">Volume</div>
```

Better: use native `<input type="checkbox">` or `<input type="range">` when possible.

---

## `aria-required-children` / `aria-required-parent` (SC 1.3.1, Level A)

ARIA composite widgets require specific parent/child relationships.

**Bad:**
```html
<div role="listbox">
  <div>Apple</div>       <!-- should be role="option" -->
  <div>Banana</div>
</div>
```

**Good:**
```html
<div role="listbox" aria-label="Fruit">
  <div role="option" aria-selected="false">Apple</div>
  <div role="option" aria-selected="false">Banana</div>
</div>
```

---

## `select-name` (SC 4.1.2, Level A)

`<select>` elements need an accessible name.

**Bad:**
```html
<select><option>A</option></select>
```

**Good:**
```html
<label for="plan">Plan</label>
<select id="plan"><option>A</option></select>
```

---

## `nested-interactive` (SC 4.1.2, Level A)

Interactive elements cannot nest.

**Bad:**
```html
<button><a href="/learn">Learn more</a></button>
```

**Good (pick one):**
```html
<a href="/learn" class="button-styled">Learn more</a>
```

---

## `object-alt` (SC 1.1.1, Level A)

`<object>` needs alternative text as fallback content.

**Bad:**
```html
<object data="/chart.svg" type="image/svg+xml"></object>
```

**Good:**
```html
<object data="/chart.svg" type="image/svg+xml">
  Quarterly sales chart showing 12% growth YoY.
</object>
```

---

## `video-caption` / `audio-caption` (SC 1.2.1, 1.2.2, Level A)

Media needs captions.

**Bad:**
```html
<video src="/demo.mp4" controls></video>
```

**Good:**
```html
<video src="/demo.mp4" controls>
  <track kind="captions" src="/demo.vtt" srclang="en" label="English" default />
</video>
```

---

## `autocomplete-valid` (SC 1.3.5, Level AA)

`autocomplete` values must match the spec ([HTML autofill tokens](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#autofill)).

**Bad:**
```html
<input name="email" autocomplete="yes" />
<input name="phone" autocomplete="telephone" />
```

**Good:**
```html
<input name="email" autocomplete="email" />
<input name="phone" autocomplete="tel" />
```

Common correct values: `email`, `tel`, `name`, `given-name`, `family-name`,
`street-address`, `postal-code`, `country`, `cc-number`, `cc-exp`, `current-password`,
`new-password`, `one-time-code`, `username`.

---

## `target-size` (SC 2.5.8, Level AA) ★ new in 2.2

Pointer targets must be at least 24×24 CSS pixels.

**Bad:**
```css
.icon-btn { width: 16px; height: 16px; padding: 0; }
```

**Good:**
```css
.icon-btn {
  width: 24px;
  height: 24px;
  padding: 4px;  /* total hit area 32×32 */
}
```

**Alternative:** increase hit area with padding or spacing between adjacent targets (≥24px spacing exempts smaller targets).

---

## `scrollable-region-focusable` (SC 2.1.1, Level A)

Scrollable regions must be keyboard-focusable.

**Bad:**
```html
<div style="overflow: auto; max-height: 200px;">
  <!-- long content -->
</div>
```

**Good:**
```html
<div style="overflow: auto; max-height: 200px;" tabindex="0" role="region" aria-label="Release notes">
  <!-- long content -->
</div>
```

---

## Universal React pattern: accessible icon button

```jsx
function IconButton({ icon, label, onClick }) {
  return (
    <button type="button" onClick={onClick} aria-label={label}>
      {icon}
    </button>
  );
}
// Usage:
<IconButton icon={<TrashIcon aria-hidden />} label="Delete item" onClick={handleDelete} />
```

## Universal React pattern: labeled form field

```jsx
function Field({ id, label, error, ...inputProps }) {
  const describedBy = error ? `${id}-error` : undefined;
  return (
    <div>
      <label htmlFor={id}>{label}</label>
      <input id={id} aria-invalid={!!error} aria-describedby={describedBy} {...inputProps} />
      {error && <p id={`${id}-error`} role="alert">{error}</p>}
    </div>
  );
}
```
