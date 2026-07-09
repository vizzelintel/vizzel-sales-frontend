// BUG-13: directoryRowH()/rowH() render
// `${STATUS[pipelineStatusKey(p.status)]?.short || p.status}` as the fallback
// badge label without passing it through esc(). p.status is currently a
// server-controlled enum so the practical risk is low, but any raw,
// un-escaped interpolation into innerHTML is a latent XSS hole the moment the
// value stops being trusted. This is a static source check (no DOM/browser
// available in this test env) — it greps for the exact unescaped fallback
// pattern rather than executing the render. See BUG_REPORT.md BUG-13.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

test("status fallback in row renderers is escaped (BUG-13)", () => {
  const src = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");

  // Matches the exact unescaped fallback used today:
  //   `${STATUS[pipelineStatusKey(p.status)]?.short || p.status}`
  const unescapedFallback = /\?\.short \|\| p\.status\}/g;
  const hits = src.match(unescapedFallback) || [];

  assert.equal(
    hits.length,
    0,
    `found ${hits.length} occurrence(s) of the unescaped "|| p.status" fallback in index.html — ` +
      `wrap it as esc(p.status) so an unrecognized/future-untrusted status can't inject HTML (BUG-13)`
  );
});
