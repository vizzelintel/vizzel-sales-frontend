#!/usr/bin/env node
/** Parse-check inline scripts in index.html and upload.html (ignores external script src). */
const fs = require("fs");

function extractInlineScript(html, useLastBlock) {
  const parts = html.split("<script>");
  const chunk = useLastBlock ? parts[parts.length - 1] : parts.pop();
  return chunk.split("</script>")[0];
}

function checkFile(file, useLastBlock) {
  const html = fs.readFileSync(file, "utf8");
  const src = extractInlineScript(html, useLastBlock);
  new Function(src);
  console.log(`${file} OK`);
}

checkFile("index.html", false);
checkFile("upload.html", true);
