// BUG-10 / BUG-11: upload.html reads the JWT from the URL query string and
// posts messages back to window.opener with targetOrigin '*'. Both are
// static source checks (no browser/jsdom in this test env): they assert the
// exact patterns flagged in BUG_REPORT.md so the tests flip to green once the
// token moves out of the query string / postMessage targets a real origin.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

function readUploadHTML() {
  return fs.readFileSync(path.join(__dirname, "..", "upload.html"), "utf8");
}

// BUG-10: JWT pulled from ?token=... leaks via browser history, Referer
// headers, and proxy/CDN access logs.
test("upload.html does not read the auth token from the URL query string (BUG-10)", () => {
  const src = readUploadHTML();
  const tokenFromQuery = /params\.get\(\s*["']token["']\s*\)/;
  assert.ok(
    !tokenFromQuery.test(src),
    "upload.html still reads the JWT via params.get(\"token\") — pass it via postMessage " +
      "or a URL fragment (#...) instead so it isn't logged in history/Referer/proxy logs (BUG-10)"
  );
});

// BUG-11: postMessage(..., '*') broadcasts to any origin that can open this
// popup/window.
test("upload.html postMessage() targets a specific origin, not '*' (BUG-11)", () => {
  const src = readUploadHTML();
  const wildcardPostMessage = /postMessage\([^)]*,\s*["']\*["']\s*\)/;
  assert.ok(
    !wildcardPostMessage.test(src),
    "upload.html calls postMessage(..., '*') — target the known frontend origin " +
      "(e.g. FRONTEND_BASE_URL) instead of broadcasting to any origin (BUG-11)"
  );
});
