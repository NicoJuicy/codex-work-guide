---
name: llm-wiki
description: Maintain a persistent Markdown knowledge base for Codex and Obsidian. Use when the user asks to ingest sources, query the wiki, file a useful answer, update cross-links or run a wiki health check.
---

# LLM Wiki

Maintain a Markdown wiki that separates immutable sources from agent-written knowledge pages.

## Locate the wiki

Use the directory named by the user. If none is given, look for `sources/`, `wiki/index.md` and `wiki/log.md` in the current project. Stop and ask before creating a new wiki outside the current project.

Read the wiki's `AGENTS.md` before changing files. Its local schema overrides this Skill when the two differ.

## Rules

- Never rewrite files in `sources/`.
- Cite source files and URLs for factual claims.
- Separate confirmed facts, source claims and inference.
- Do not hide contradictions. Record both claims and their dates.
- Prefer updating an existing topic page over creating a duplicate.
- Keep `wiki/index.md` current.
- Append one entry to `wiki/log.md` after every completed operation.
- If the wiki cannot support an answer, say so and list what is missing.
- Show the changed-file list at the end.

## Operations

### Ingest

1. Read `wiki/index.md` and the new source.
2. Identify existing pages affected by the source.
3. Create or update the source summary, entity and concept pages.
4. Add `[[wikilinks]]` where the relationship is useful.
5. Mark conflicts, uncertainty and publication dates.
6. Update the index and append an `ingest` log entry.

For a large change, list affected pages before editing. Do not rewrite unrelated pages.

### Query

1. Read the index, then the most relevant pages and cited sources.
2. Answer with page references and a confidence boundary.
3. If the result has lasting value, ask before filing it unless the user already requested writeback.
4. When filing, create or update one focused page, then update the index and log.

### Lint

Check for broken links, orphan pages, duplicate topics, stale claims, contradictions, missing citations and gaps worth researching. Report findings before making broad changes. Safe index and link repairs may be applied when the user requested fixes.

## Log format

```markdown
## [YYYY-MM-DD] ingest | Source title
- Updated: [[page-a]], [[page-b]]
- Notes: short description
```

Use `query` or `lint` in place of `ingest` for those operations.

## Reference

This workflow follows Andrej Karpathy's LLM Wiki pattern:
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
