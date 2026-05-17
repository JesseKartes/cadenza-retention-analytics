#!/usr/bin/env bash
# Build a browser-friendly HTML version of the Tableau build plan.
#
# Output lands at tableau/build-guide.html (gitignored).
# Open with: open tableau/build-guide.html
#
# Features:
#   - Sticky table of contents on the left
#   - Clickable checkboxes with localStorage persistence (survives reloads)
#   - Wide, readable code blocks for calc-field copy-paste
#   - Cadenza brand palette accents

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INPUT="$ROOT/docs/superpowers/plans/2026-05-17-tableau-version.md"
OUTPUT_DIR="$ROOT/tableau"
OUTPUT="$OUTPUT_DIR/build-guide.html"

mkdir -p "$OUTPUT_DIR"

# Pandoc converts the markdown; we pipe through sed to enable checkboxes
# (pandoc renders them disabled by default).
pandoc \
  --standalone \
  --toc \
  --toc-depth=2 \
  --metadata title="Cadenza Tableau Build Guide" \
  --highlight-style=tango \
  -H /dev/stdin \
  "$INPUT" <<'HEAD_EOF' \
  | sed 's/<input type="checkbox" disabled=""/<input type="checkbox"/g' \
  > "$OUTPUT"
<style>
  :root {
    --cadenza-primary: #1F3A8A;
    --cadenza-accent: #06B6D4;
    --cadenza-good: #10B981;
    --cadenza-bad: #EF4444;
    --cadenza-neutral: #94A3B8;
    --cadenza-bg: #FAFBFD;
    --cadenza-code-bg: #F1F5F9;
    --cadenza-border: #E2E8F0;
  }
  html { scroll-behavior: smooth; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    color: #1E293B;
    background: var(--cadenza-bg);
    margin: 0;
    display: grid;
    grid-template-columns: 280px 1fr;
    min-height: 100vh;
  }
  /* TOC sidebar */
  nav#TOC {
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
    padding: 1.5rem 1rem;
    background: white;
    border-right: 1px solid var(--cadenza-border);
    font-size: 0.875rem;
  }
  nav#TOC::before {
    content: "Build Guide";
    display: block;
    font-weight: 700;
    color: var(--cadenza-primary);
    font-size: 1rem;
    margin-bottom: 1rem;
    letter-spacing: 0.02em;
  }
  nav#TOC ul { list-style: none; padding-left: 0.75rem; margin: 0; }
  nav#TOC > ul { padding-left: 0; }
  nav#TOC li { margin: 0.25rem 0; }
  nav#TOC a {
    color: #475569;
    text-decoration: none;
    display: block;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
  }
  nav#TOC a:hover {
    background: var(--cadenza-code-bg);
    color: var(--cadenza-primary);
  }
  /* Content area */
  main, body > h1, body > p, body > h2, body > h3, body > ul, body > ol,
  body > pre, body > blockquote, body > table, body > hr {
    max-width: 900px;
    padding: 0 2rem;
  }
  body > * { grid-column: 2; }
  nav#TOC { grid-column: 1; grid-row: 1 / 999; }
  header#title-block-header {
    grid-column: 2;
    padding: 2rem 2rem 0;
    max-width: 900px;
  }
  header#title-block-header h1.title {
    color: var(--cadenza-primary);
    font-size: 2rem;
    margin: 0;
  }
  h1, h2, h3, h4 { color: var(--cadenza-primary); }
  h2 {
    margin-top: 2.5rem;
    padding-top: 1rem;
    border-top: 2px solid var(--cadenza-border);
  }
  h3 { margin-top: 1.75rem; }
  a { color: var(--cadenza-accent); }
  /* Code blocks */
  pre {
    background: var(--cadenza-code-bg);
    border: 1px solid var(--cadenza-border);
    border-left: 4px solid var(--cadenza-accent);
    border-radius: 4px;
    padding: 0.75rem 1rem;
    overflow-x: auto;
    font-size: 0.875rem;
    line-height: 1.5;
  }
  code {
    font-family: "SF Mono", Monaco, "Cascadia Mono", Menlo, monospace;
    font-size: 0.85em;
    background: var(--cadenza-code-bg);
    padding: 0.1em 0.35em;
    border-radius: 3px;
  }
  pre code { background: none; padding: 0; }
  /* Checkboxes — interactive */
  input[type="checkbox"] {
    width: 1.1em;
    height: 1.1em;
    margin-right: 0.5em;
    cursor: pointer;
    accent-color: var(--cadenza-good);
    vertical-align: middle;
  }
  /* Bullet list with checkbox: dim when checked */
  ul li.task-list-item { list-style: none; margin-left: -1.5em; }
  /* Tables */
  table {
    border-collapse: collapse;
    margin: 1rem 0;
    font-size: 0.9rem;
  }
  th, td {
    border: 1px solid var(--cadenza-border);
    padding: 0.5rem 0.75rem;
    text-align: left;
  }
  th { background: var(--cadenza-code-bg); color: var(--cadenza-primary); }
  /* Blockquote */
  blockquote {
    border-left: 4px solid var(--cadenza-neutral);
    margin-left: 0;
    padding: 0.5rem 1rem;
    color: #475569;
    background: white;
  }
  hr { border: none; border-top: 1px solid var(--cadenza-border); margin: 2rem 0; }
  /* Responsive */
  @media (max-width: 800px) {
    body { grid-template-columns: 1fr; }
    nav#TOC { position: static; height: auto; }
    body > * { grid-column: 1; }
  }
</style>
<script>
  // Persist checkbox state in localStorage so progress survives reloads.
  document.addEventListener("DOMContentLoaded", () => {
    const STORAGE_KEY = "cadenza-tableau-checklist";
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    const boxes = document.querySelectorAll('input[type="checkbox"]');
    boxes.forEach((box, i) => {
      const key = `box-${i}`;
      if (saved[key]) box.checked = true;
      box.addEventListener("change", () => {
        saved[key] = box.checked;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
        // Dim parent <li> when checked
        const li = box.closest("li");
        if (li) li.style.opacity = box.checked ? "0.55" : "1";
      });
      // Apply initial dim
      const li = box.closest("li");
      if (li && box.checked) li.style.opacity = "0.55";
    });
  });
</script>
HEAD_EOF

echo "Wrote $OUTPUT"
echo "Open with: open \"$OUTPUT\""
