# URL discovery recipes

`audit-site.mjs` needs a list of URLs to audit. This file documents how to
produce that list from a framework's router config, from server/analytics logs,
or by hand.

**Goal:** generate a `urls.txt` file the user commits to their repo. The
auditor then runs `audit-site.mjs --urls urls.txt --auth auth.json --out ./audit/`.

## Quick orientation — which recipe should I use?

- **Marketing / public pages:** point `audit-site.mjs` at `--sitemap` directly; no URL list needed.
- **Authenticated SaaS / app routes:** use the framework recipe below to extract the route list, then curate into `urls.txt`. Sitemaps deliberately exclude these routes.
- **Legacy / unknown stack:** use the generic recipes (analytics, access logs, test suite) at the bottom.

## Dynamic segments

Every framework recipe produces **route patterns**, not concrete URLs. A route
like `/users/:id` or `/users/[id]` is a template. To audit it, resolve to a
concrete URL with a real ID — typically:

- a known test user (`/users/1`)
- a seeded fixture record (`/products/test-sku`)
- a canonical public record

Commit the concrete URLs to `urls.txt`. For authenticated routes, the IDs
should match data available to the `auth.json` session.

## `urls.txt` format

```text
# Comments begin with '#'. Blank lines ignored.
https://app.example.com/
https://app.example.com/pricing
https://app.example.com/dashboard
https://app.example.com/settings/profile
```

Commit it to your repo. Review it in PRs like any other config.

---

## Framework recipes

### Next.js (App Router, 13+)

File-system walk:
```bash
find app -type f \( -name "page.tsx" -o -name "page.jsx" -o -name "page.ts" -o -name "page.js" \) \
  | sed 's|^app||;s|/page\.[jt]sx\?$||;s|^$|/|' \
  | sort -u
```

Build-time manifest (after `pnpm build` / `npm run build`):
```bash
cat .next/app-paths-manifest.json | jq -r 'keys[]' | sort -u
```

Route groups `(marketing)` should be stripped; dynamic segments appear as
`[id]` or `[...slug]` — resolve them manually.

### Next.js (Pages Router)

```bash
find pages -type f \( -name "*.tsx" -o -name "*.jsx" -o -name "*.ts" -o -name "*.js" \) \
  | grep -v '_app\|_document\|_error\|api/' \
  | sed 's|^pages||;s|\.[jt]sx\?$||;s|/index$||;s|^$|/|' \
  | sort -u
```

### Nuxt 3

Build-time manifest (after `npx nuxi build`):
```bash
cat .nuxt/routes.json | jq -r '.[].path' | sort -u
```

Or file-system walk:
```bash
find pages -type f -name "*.vue" \
  | sed 's|^pages||;s|\.vue$||;s|/index$||;s|^$|/|' \
  | sort -u
```

### Remix / React Router v7 (framework mode)

File-system routes:
```bash
find app/routes -type f -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" \
  | sed 's|^app/routes||;s|\.[jt]sx\?$||;s|_index$||;s|\._index$||' \
  | sort -u
```

For config-based routes (`app/routes.ts`), export the route table as JSON from
a small script and pipe into `urls.txt`.

### SvelteKit

```bash
find src/routes -type f -name "+page.svelte" \
  | sed 's|^src/routes||;s|/+page\.svelte$||;s|^$|/|' \
  | sort -u
```

Grouped routes `(app)` should be stripped:
```bash
find src/routes -type f -name "+page.svelte" \
  | sed 's|^src/routes||;s|/+page\.svelte$||;s|/([^)]*)||g;s|^$|/|' \
  | sort -u
```

### Astro

```bash
find src/pages -type f \( -name "*.astro" -o -name "*.md" -o -name "*.mdx" \) \
  | sed 's|^src/pages||;s|\.\(astro\|md\|mdx\)$||;s|/index$||;s|^$|/|' \
  | sort -u
```

Astro also emits `dist/sitemap-0.xml` at build time if `@astrojs/sitemap` is
installed — prefer feeding that to `--sitemap` when available.

### Ruby on Rails

Built-in:
```bash
bin/rails routes --expanded | grep -E '^URI Pattern:' | awk '{print $NF}' | sort -u
```

As JSON (Rails 7+):
```bash
bin/rails runner 'puts Rails.application.routes.routes.map { |r| r.path.spec.to_s.sub(/\(\.:format\)$/, "") }.uniq'
```

### Django

With [django-extensions](https://django-extensions.readthedocs.io/):
```bash
python manage.py show_urls --format table | awk 'NR>2 {print $1}' | sort -u
```

Without it, a management command walks `urlpatterns`:
```python
# management/commands/list_urls.py
from django.core.management.base import BaseCommand
from django.urls import get_resolver

def walk(patterns, prefix=''):
    for p in patterns:
        if hasattr(p, 'url_patterns'):
            yield from walk(p.url_patterns, prefix + str(p.pattern))
        else:
            yield prefix + str(p.pattern)

class Command(BaseCommand):
    def handle(self, *args, **opts):
        for u in sorted(set(walk(get_resolver().url_patterns))):
            self.stdout.write('/' + u)
```

### Flask

```bash
flask routes --no-match --sort rule | awk 'NR>2 {print $NF}' | sort -u
```

Or via Python:
```python
python -c "from app import app; [print(r.rule) for r in app.url_map.iter_rules()]"
```

### Laravel

```bash
php artisan route:list --json | jq -r '.[].uri' | sort -u
```

Filter out `api/` routes for a web-only audit:
```bash
php artisan route:list --json | jq -r '.[] | select(.uri | startswith("api/") | not) | .uri' | sort -u
```

### Express / Fastify / Koa

No built-in route introspection. Add a debug endpoint once to dump routes:

```js
// Express
app.get('/__routes', (_, res) => {
  const routes = app._router.stack
    .filter(l => l.route)
    .map(l => l.route.path);
  res.json(routes);
});
```

Then `curl localhost:3000/__routes | jq -r '.[]' > urls.txt` and remove the
debug endpoint.

---

## Generic recipes (any stack)

### From analytics (top N pages)

Export top URLs from Google Analytics, Plausible, Fathom, or PostHog as CSV.
Extract the URL column:
```bash
tail -n +2 gaexport.csv | cut -d, -f1 | sort -u > urls.txt
```

"Audit the pages users actually visit" is usually the right scope — it
prioritizes real user impact over route coverage.

### From server access logs

```bash
awk '{print $7}' access.log \
  | sort -u \
  | grep -Ev '\.(css|js|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|map)$' \
  | sed 's|^|https://example.com|' > urls.txt
```

### From E2E test suite

Playwright:
```bash
grep -rhoE "goto\(['\"]([^'\"]+)" e2e/ tests/ | sed "s/goto(['\"]//" | sort -u
```

Cypress:
```bash
grep -rhoE "cy\.visit\(['\"]([^'\"]+)" cypress/ | sed "s/cy\.visit(['\"]//" | sort -u
```

Tested routes are usually the important routes.

---

## Prepending the host

Framework recipes produce paths (`/dashboard`). Add your origin:
```bash
sed 's|^|https://app.example.com|' paths.txt > urls.txt
```

For local dev audits, use `http://localhost:3000` (or whatever port your dev
server binds to).

## What to exclude

- `api/` endpoints (JSON, not HTML — audit with a different tool)
- Auth callback routes (`/auth/callback`, `/oauth/*`) — they redirect
- Static asset paths (CSS, JS, images)
- Health checks, `robots.txt`, `sitemap.xml`
- Routes that only exist for server-side redirects
