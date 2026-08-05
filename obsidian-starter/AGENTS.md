# Wiki instructions

This directory is an Obsidian vault maintained with Codex.

## Structure

- `inbox/`: unprocessed notes and ideas
- `sources/`: immutable source material
- `wiki/`: agent-maintained summaries, entities, concepts and analyses
- `wiki/index.md`: catalog of Wiki pages with one-line descriptions
- `wiki/log.md`: append-only operation history

## Source integrity

- Do not edit or move files in `sources/` unless explicitly asked.
- Cite sources with relative links or stable URLs.
- Keep dates, numbers, names and attribution exact.
- Label inference and unresolved contradictions.
- If the vault does not contain enough evidence, say so.

## Wiki pages

- Use one focused topic per page.
- Search the index before creating a page.
- Update existing pages when new evidence changes them.
- Use `[[wikilinks]]` for useful relationships.
- Avoid empty pages, duplicate aliases and decorative tags.

## Operations

After every ingest, query writeback or lint fix:

1. Update `wiki/index.md`.
2. Append a dated entry to `wiki/log.md`.
3. Report changed files and unresolved questions.

For broad changes, list affected pages before editing.
