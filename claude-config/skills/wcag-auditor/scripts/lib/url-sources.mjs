/**
 * url-sources.mjs - resolve audit URLs from multiple sources
 *
 * Sources (all optional, unioned + deduped):
 *   1. --sitemap <url>    XML sitemap fetched + parsed
 *   2. --urls <path>      newline-delimited text file ('#' comments, blank lines ignored)
 *   3. --crawl-from <url> bounded same-origin BFS from seed, depth N
 *
 * Filters (applied to the union):
 *   --include <glob>  repeatable; if any provided, URL must match at least one
 *   --exclude <glob>  repeatable; URL must not match any
 */

import { readFile } from 'node:fs/promises';
import { XMLParser } from 'fast-xml-parser';

/**
 * Resolve the full list of audit URLs from all configured sources.
 * @returns {Promise<string[]>} sorted, deduped, filtered URL list
 */
export async function resolveUrls({
  sitemap,
  urlsFile,
  crawlFrom,
  crawlDepth,
  includes = [],
  excludes = [],
  storageState,
  fetchPage,
} = {}) {
  const collected = new Set();

  if (sitemap) {
    for (const u of await urlsFromSitemap(sitemap)) collected.add(u);
  }
  if (urlsFile) {
    for (const u of await urlsFromFile(urlsFile)) collected.add(u);
  }
  if (crawlFrom) {
    const crawled = await urlsFromCrawl({
      seed: crawlFrom,
      depth: crawlDepth ?? 1,
      storageState,
      fetchPage,
    });
    for (const u of crawled) collected.add(u);
  }

  const filtered = [...collected]
    .filter((u) => matchesIncludes(u, includes))
    .filter((u) => !matchesAnyGlob(u, excludes));

  return filtered.sort();
}

async function urlsFromSitemap(sitemapUrl) {
  const res = await fetch(sitemapUrl);
  if (!res.ok) {
    throw new Error(`sitemap fetch failed: ${res.status} ${res.statusText}`);
  }
  const xml = await res.text();
  const parser = new XMLParser({ ignoreAttributes: true });
  const doc = parser.parse(xml);

  if (doc.sitemapindex?.sitemap) {
    const children = Array.isArray(doc.sitemapindex.sitemap)
      ? doc.sitemapindex.sitemap
      : [doc.sitemapindex.sitemap];
    const all = [];
    for (const child of children) {
      if (child.loc) {
        const nested = await urlsFromSitemap(child.loc);
        all.push(...nested);
      }
    }
    return all;
  }

  if (doc.urlset?.url) {
    const entries = Array.isArray(doc.urlset.url)
      ? doc.urlset.url
      : [doc.urlset.url];
    return entries.map((e) => e.loc).filter(Boolean);
  }

  return [];
}

async function urlsFromFile(path) {
  const text = await readFile(path, 'utf8');
  return text
    .split(/\r?\n/)
    .map((line) => line.replace(/#.*$/, '').trim())
    .filter((line) => line.length > 0);
}

async function urlsFromCrawl({ seed, depth, storageState, fetchPage }) {
  const seedUrl = new URL(seed);
  const origin = seedUrl.origin;
  const visited = new Map();
  const queue = [{ url: seed, depth: 0 }];

  const getLinks = fetchPage ?? (await defaultPageFetcher(storageState));

  try {
    while (queue.length > 0) {
      const { url, depth: d } = queue.shift();
      const normalized = normalizeUrl(url);
      if (visited.has(normalized)) continue;
      visited.set(normalized, d);

      if (d >= depth) continue;

      let links;
      try {
        links = await getLinks.fetch(normalized);
      } catch {
        continue;
      }

      for (const raw of links) {
        let absolute;
        try {
          absolute = new URL(raw, normalized).toString();
        } catch {
          continue;
        }
        const absUrl = new URL(absolute);
        if (absUrl.origin !== origin) continue;
        absolute = normalizeUrl(absolute);
        if (!visited.has(absolute)) {
          queue.push({ url: absolute, depth: d + 1 });
        }
      }
    }
  } finally {
    if (getLinks.close) await getLinks.close();
  }

  return [...visited.keys()];
}

function normalizeUrl(raw) {
  const u = new URL(raw);
  u.hash = '';
  if (u.pathname !== '/' && u.pathname.endsWith('/')) {
    u.pathname = u.pathname.replace(/\/+$/, '');
  }
  return u.toString();
}

async function defaultPageFetcher(storageState) {
  const { chromium } = await import('playwright');
  const browser = await chromium.launch();
  const context = await browser.newContext({ storageState });
  return {
    async fetch(url) {
      const page = await context.newPage();
      try {
        await page.goto(url, { waitUntil: 'networkidle', timeout: 30_000 });
        const links = await page.$$eval('a[href]', (anchors) =>
          anchors.map((a) => a.getAttribute('href')).filter(Boolean),
        );
        return links;
      } finally {
        await page.close();
      }
    },
    async close() {
      await context.close();
      await browser.close();
    },
  };
}

function matchesIncludes(url, includes) {
  if (includes.length === 0) return true;
  return matchesAnyGlob(url, includes);
}

function matchesAnyGlob(url, patterns) {
  return patterns.some((p) => globMatch(url, p));
}

function globMatch(url, pattern) {
  let re = '';
  let i = 0;
  while (i < pattern.length) {
    const c = pattern[i];
    if (c === '*') {
      if (pattern[i + 1] === '*') {
        re += '.*';
        i += 2;
      } else {
        re += '[^/]*';
        i += 1;
      }
    } else if (c === '?') {
      re += '.';
      i += 1;
    } else if ('\\^$.|+(){}[]'.includes(c)) {
      re += '\\' + c;
      i += 1;
    } else {
      re += c;
      i += 1;
    }
  }
  return new RegExp('^' + re + '$').test(url);
}
