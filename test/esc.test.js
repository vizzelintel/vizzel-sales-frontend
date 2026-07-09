// BUG-12: esc() escapes & < > " but not the single quote, even though
// several call sites interpolate esc()'d values inside single-quoted
// attributes/JS strings (e.g. onclick="showDetail('${esc(p.id)}')" in
// index.html). Values are currently server-controlled (uuid/id) so the risk
// is low today, but any future user-supplied field placed in a single-quote
// context becomes an XSS vector. See BUG_REPORT.md BUG-12.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

function loadEsc() {
  const src = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
  const match = src.match(/function esc\(s\) \{[\s\S]*?\n\}/);
  assert.ok(match, "could not find function esc(s) {...} in index.html");
  const fn = new Function(`${match[0]}\nreturn esc;`)();
  return fn;
}

test("esc() escapes & < > \" (baseline)", () => {
  const esc = loadEsc();
  assert.equal(esc(`&<>"`), "&amp;&lt;&gt;&quot;");
});

test("esc() escapes single quotes (BUG-12)", () => {
  const esc = loadEsc();
  const out = esc(`it's a test`);
  assert.ok(
    !out.includes("'"),
    `esc("it's a test") = ${JSON.stringify(out)} still contains an unescaped ' — ` +
      `values are interpolated into single-quoted attributes like onclick="...('${"${esc(m.id)}"}')" (BUG-12)`
  );
});
