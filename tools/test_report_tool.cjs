const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const { test } = require("node:test");

const html = readFileSync(path.join(__dirname, "index.html"), "utf8");

test("keeps the report tool self-contained and under 800 lines", () => {
  assert.equal((html.match(/<style\b/gi) || []).length, 1);
  assert.equal((html.match(/<script\s*>/gi) || []).length, 1);
  assert.doesNotMatch(html, /(?:src|href)="(?:\.\/|\.\.\/)(?:css|js)\//);
  assert.ok(html.split("\n").length <= 800);
});

test("keeps Excel and clipboard imports", () => {
  assert.match(html, /XLSX\.read/);
  assert.match(html, /function handlePaste\(\)/);
  assert.match(html, /text\.split\(\/\\r\?\\n\/\)/);
  assert.match(html, /function applyParsedData\(parsed, nameInfo\)/);
});

test("keeps custom charts and export controls", () => {
  assert.match(html, /function addCustomChart\(\)/);
  assert.match(html, /function removeCustomChart\(id\)/);
  assert.match(html, /function syncOutputOrder\(\)/);
  assert.match(html, /function getColumnCounts\(col\)/);
  assert.doesNotMatch(html, /getCustomCounts/);
  assert.match(html, /function getAggregatedData\(targetCol\) \{\s*const counts = getColumnCounts\(targetCol\);/);
  assert.match(html, /function getColumnCounts\(col\)/);
  assert.doesNotMatch(html, /getCustomCounts/);
  assert.match(html, /function getAggregatedData\(targetCol\) \{\s*const counts = getColumnCounts\(targetCol\);/);
  assert.match(html, /pptx\.writeFile/);
  assert.match(html, /id="chart-type"/);
});

test("inline JavaScript parses", () => {
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/gi)];
  assert.equal(scripts.length, 1);
  execFileSync("node", ["-e", "new Function(process.argv[1])", scripts[0][1]]);
});
