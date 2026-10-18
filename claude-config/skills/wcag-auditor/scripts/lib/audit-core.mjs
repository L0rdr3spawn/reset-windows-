/**
 * audit-core.mjs - shared audit + threshold primitives
 *
 * Used by both audit.mjs (single URL) and audit-site.mjs (multi URL).
 */

import AxeBuilder from '@axe-core/playwright';

export const EXIT_OK = 0;
export const EXIT_THRESHOLD_CROSSED = 1;
export const EXIT_SCRIPT_ERROR = 2;

export const SEVERITY_RANK = {
  minor: 1,
  moderate: 2,
  serious: 3,
  critical: 4,
};
export const VALID_FAIL_ON = new Set([
  'none',
  'minor',
  'moderate',
  'serious',
  'critical',
  'any',
]);

export const DEFAULT_VIEWPORTS = ['1280x800', '375x667'];

const VIEWPORT_RE = /^(\d+)x(\d+)$/;

export function parseViewport(s) {
  const m = s.match(VIEWPORT_RE);
  if (!m) throw new Error(`--viewport must be <width>x<height> (got: ${s})`);
  return { width: Number(m[1]), height: Number(m[2]), label: s };
}

export function axeTagsFor(level, includeBestPractice) {
  const tags = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];
  if (level === 'AAA') {
    tags.push('wcag2aaa', 'wcag21aaa', 'wcag22aaa');
  }
  if (includeBestPractice) {
    tags.push('best-practice');
  }
  return tags;
}

/**
 * Audit a single URL at one or more viewports, using an existing browser.
 * Returns a normalized per-URL report.
 */
export async function auditUrl({
  browser,
  url,
  viewports,
  axeTags,
  storageState,
}) {
  const startedAt = new Date().toISOString();
  const perViewportResults = [];

  for (const viewport of viewports) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      storageState,
    });
    const page = await context.newPage();

    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 45_000 });
    } catch (err) {
      await context.close();
      throw new Error(
        `Failed to load ${url} at viewport ${viewport.label}: ${err.message}`,
      );
    }

    const axeResults = await new AxeBuilder({ page })
      .withTags(axeTags)
      .analyze();

    perViewportResults.push({
      viewport: viewport.label,
      width: viewport.width,
      height: viewport.height,
      violations: axeResults.violations,
      passes: axeResults.passes.length,
      incomplete: axeResults.incomplete,
      inapplicable: axeResults.inapplicable.length,
      testEngine: axeResults.testEngine,
      testRunner: axeResults.testRunner,
      testEnvironment: axeResults.testEnvironment,
    });

    await context.close();
  }

  const merged = mergeViewportResults(perViewportResults);
  return {
    url,
    startedAt,
    finishedAt: new Date().toISOString(),
    viewports: perViewportResults.map((r) => ({
      label: r.viewport,
      width: r.width,
      height: r.height,
      violationCount: r.violations.length,
      incompleteCount: r.incomplete.length,
      passCount: r.passes,
      inapplicableCount: r.inapplicable,
    })),
    violations: merged.violations,
    incomplete: merged.incomplete,
    testEngine: perViewportResults[0]?.testEngine,
  };
}

function mergeViewportResults(perViewportResults) {
  const violationsByKey = new Map();
  const incompleteByKey = new Map();

  for (const vp of perViewportResults) {
    mergeBucket(violationsByKey, vp.violations, vp.viewport);
    mergeBucket(incompleteByKey, vp.incomplete, vp.viewport);
  }

  return {
    violations: [...violationsByKey.values()],
    incomplete: [...incompleteByKey.values()],
  };
}

function mergeBucket(byKey, results, viewportLabel) {
  for (const r of results) {
    let entry = byKey.get(r.id);
    if (!entry) {
      entry = {
        id: r.id,
        impact: r.impact,
        tags: r.tags,
        description: r.description,
        help: r.help,
        helpUrl: r.helpUrl,
        nodes: [],
      };
      byKey.set(r.id, entry);
    }
    for (const node of r.nodes) {
      const targetKey = JSON.stringify(node.target);
      let nodeEntry = entry.nodes.find(
        (n) => JSON.stringify(n.target) === targetKey,
      );
      if (!nodeEntry) {
        nodeEntry = {
          target: node.target,
          html: node.html,
          failureSummary: node.failureSummary,
          any: node.any,
          all: node.all,
          none: node.none,
          viewports: [],
        };
        entry.nodes.push(nodeEntry);
      }
      if (!nodeEntry.viewports.includes(viewportLabel)) {
        nodeEntry.viewports.push(viewportLabel);
      }
    }
  }
}

export function thresholdCrossed(violations, failOn) {
  if (failOn === 'none') return false;
  if (violations.length === 0) return false;
  if (failOn === 'any') return true;
  const minRank = SEVERITY_RANK[failOn];
  return violations.some((v) => {
    const rank = SEVERITY_RANK[v.impact] ?? 0;
    return rank >= minRank;
  });
}
