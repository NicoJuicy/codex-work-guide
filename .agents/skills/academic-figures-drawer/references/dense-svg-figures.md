# Dense SVG Figure Track

This track produces static, information-dense, paper-style figures as code-generated SVG.
The figure script is the source of truth; the SVG and PNG are derived artifacts.
It complements the draw.io track and shares its semantic rules, but trades in-editor editability for density, typeset math, data sketches, and exact reproducible layout.

## 1. When to choose this track

Choose the dense SVG track when at least one of these holds:

- The user wants a figure that looks like a top-venue paper figure and says the current result is sparse, plain, or has too much blank space.
- The figure needs many small typeset symbols, sub/superscripts, or inline math next to labels.
- Cards should carry data sketches: thumbnails, trajectory curves, bar strips, attention maps, timelines, or schematic plots.
- Labels mix CJK and Latin text and must render consistently.
- The figure will be regenerated often, or several figures must share one exact visual system.

Choose the draw.io track when the user or venue needs an editable `.drawio` source, when collaborators will hand-edit the figure, or when the figure is a routing-heavy graph that benefits from the draw.io routing contract.
When the choice is unclear, ask once; otherwise default to draw.io for editable deliverables and to dense SVG for "make it look like the paper figure" requests.

## 2. Why generated figures look sparse

Compare the draft against a strong paper figure on these axes before changing anything.

| Axis | Strong paper figure | Typical sparse draft |
|---|---|---|
| Fill | Blocks and text cover most of the canvas; gutters are about 8 to 10 px | Large outer margins, in-canvas title band, long arrows, boxes two to three times larger than their text |
| Hierarchy | Three nesting levels: stage panel, card, chip or symbol | One level of same-size pastel boxes |
| Content | Symbols, terms, and notation hooks on every card | Prose sentences that read like slides |
| Visual anchors | Real or schematic thumbnails, one large focal symbol, numbered badges | Generic UI line icons that carry no information |
| Color | Each color is a semantic role reused in borders, badges, and connectors | Colors used as decoration; all arrows the same gray |
| Connectors | Braces, buses, fork and merge dots, curved loss or feedback arcs, double-headed comparisons, dashed data containers, stacked cards for repetition | Only straight gray arrows |
| Typography | Uppercase tracked stage headers, colored keywords, serif italic math, small but dense text | Large sans text everywhere, no math |
| Layout | Wide single-row pipeline on a strict column grid; title lives in the caption | Vertical single columns with empty sides; title inside the canvas |

## 3. Density contract

- Content coverage, measured by `scripts/qa_svg_figure.py`, is at least 0.55 and typically 0.60 to 0.75.
- Framed coverage (panels plus content) is at least 0.90.
- Outer margin is 8 px; gutter between panels is 8 to 10 px; card padding is 6 to 12 px.
- No empty band wider than one card height may remain inside a panel; fill it with a meaningful sketch, notation, or attached term, or shrink the panel.
- Do not put the figure title or a long subtitle inside the canvas; the paper caption carries the title.
- Prefer a wide aspect ratio for pipelines (about 2.4:1 to 3.7:1 at 1400 px width) and stack rows only when the story has parallel variants.
- Shrinking fonts is the last resort; first remove redundant words, then tighten boxes to their content, then reflow.

## 4. Composition grammar

- **Stage panel:** rounded rectangle with a light gradient in its semantic role color, a centered uppercase header with slight tracking, and an optional one-line subtitle.
- **Card:** white rounded rectangle with a role-colored stroke; optional top color bar for dataset-like inputs; optional stacked copies (offset 4 px) to show multiplicity or shared weights.
- **Chip:** small tinted rounded rectangle holding a symbol, a term, or a short label; dashed chips mark derived or linked quantities.
- **Badge:** filled pill with white bold text for a key number or a category.
- Use a shared column grid across rows so equivalent stages align vertically.
- Every card gets a hook: a symbol, notation, thumbnail, data sketch, or attached technical term.
- Attach technical terms to the component they belong to as chips inside or directly under that card, instead of listing them in a separate legend.

## 5. Content grammar and honesty

- Write math with `$...$` islands; figkit renders TeX-like sub/superscripts, hats, calligraphic and blackboard letters, and relation spacing.
- Thumbnails of the task scene belong in input, perception, and execution regions only.
- Data sketches (curves, bars, heatmaps, timelines, progress plots) must be labeled `schematic` when they do not plot real data.
- Plot real numbers only when the source states them; simple derived arithmetic (for example showing a stated 40% reduction as a 60% bar) is allowed and must stay traceable.
- Never invent results, dimensions, module names, or case details; when a case study is only described in words, draw a schematic and say so in the figure.
- Prefer a linked pair of dashed chips with the same color over a long arrow that would cross several cards.

## 6. Color roles

Assign one role per concept and reuse it everywhere that concept appears.

| Role | Typical meaning |
|---|---|
| blue | main data flow, perception, proposed policy output |
| purple | reasoning, language model, planning |
| red | contribution highlight, override, error, loss |
| green | accept, success, results, feedback that closes a loop |
| amber | control, execution, auxiliary models |
| orange | proprioception or a secondary signal |
| gray | inputs, neutral containers, standard components |

The same role color must be used for the card border, its badge, and the connector that leaves it.

## 7. Connector vocabulary

- Solid arrow in the source role color for the main flow.
- Dot plus short bus for fork and merge; keep arrowheads on the final short segment only.
- Dashed rounded arc routed inside panel gutters for closed loops and feedback, with a white pill label on the arc.
- Double-headed short arrow with a label (for example `MSE`) for comparisons.
- Curly brace to group several inputs into one consumer.
- Dashed diamond or pill only for an explicit decision; label branch arrows (`yes`, `no`, `accept`, `override`).
- No connector may cross a label; move the label or reroute, then rerun QA.

## 8. Typography

- Sans: Helvetica Neue or Arial with PingFang SC, Hiragino Sans GB, or Noto Sans CJK as CJK fallback.
- Math: STIXGeneral or Times New Roman italic through figkit tspans.
- Stage header about 13 to 14 px bold uppercase with 0.5 to 0.6 px tracking; card title 11 to 13 px bold; body 10 to 11.5 px; annotations 9 to 10 px at 1400 px canvas width.
- One large focal symbol per key module (24 to 40 px math) is encouraged.

## 9. Workflow

1. Write the semantic brief exactly as in the draw.io track: inputs, stages, contribution, outputs, and allowed facts.
2. Sketch the column grid in numbers: canvas size, panel x-ranges, row y-ranges, card rectangles.
3. Write one build script per figure using `scripts/figkit.py`; keep coordinates explicit and grouped by panel.
4. Run `python scripts/qa_svg_figure.py <figure>.svg --png`.
5. Fix every reported issue, then open the PNG and inspect it at 100 percent and in crops around dense cards and connectors.
6. Repeat until QA passes and the visual inspection finds no P0 or P1 defect; perform at least three cycles for a user-critical figure.
7. Deliver the build script, `figkit.py` version in use, SVG, and 2x PNG together.

## 10. QA gate and its limits

The gate fails on any of: text overflowing its container or the canvas, text collisions, partially overlapping sibling boxes, strokes crossing uncovered labels, or coverage below the threshold.
QA cannot judge semantics, arrow direction, icon fit, misleading sketches, or aesthetic balance, so the rendered PNG must still be inspected.
Link every text element to its container with `box=` so overflow is checked; freestanding labels are still covered by the collision and line checks.

## 11. Pitfalls observed in practice

- Heuristic text widths are only estimates; accept a layout only after the browser measurement passes.
- A `text` element with `text-anchor="middle"` stays centered only while its tspans use relative `dy`/`dx`; absolute `x` on a tspan starts a new chunk.
- Serif math glyphs have tall bounding boxes; give large focal symbols about 1.2 times their font size of vertical clearance.
- Write primes as `a'_t` rather than as a superscript command, so the subscript attaches correctly.
- Unbraced scripts such as `E_\theta` must consume the whole command; figkit handles this, and a regression test covers it.
- Card-bottom chip rows reserve space; sketches placed above them must end at least 6 px earlier.
- Curves in schematic plots often cross their own annotations; place annotations in empty plot regions and use a short leader arrow when needed.
- Generic UI icons do not replace content; use them only as small header markers next to a real symbol or term.
- A decorative element that looks like data invites misreading; either make it schematic and labeled or remove it.

## 12. figkit API summary

| Call | Purpose |
|---|---|
| `Fig(w, h)` then `save(path)` | canvas, defs, and output |
| `panel(x, y, w, h, role, title, sub=None, dashed=False)` | stage panel; returns the content top y; `title=None` for a headerless strip |
| `card(x, y, w, h, role, stack=0, topbar=False, dashed=False)` | white card; returns an id for `box=` |
| `chip`, `badge`, `pill` | small labeled containers |
| `text(x, y, s, size, weight, color, anchor, box=id)` | rich text with `$math$` |
| `arrow(d, color, dashed, start, end)`, `line`, `dot`, `brace` | connectors |
| `icon(name, x, y, size, color)` | small line glyph from the built-in set |
| `scene(x, y, w, h, frame)` | schematic tabletop thumbnail (replace with a task-specific symbol when needed) |
| `bars`, `curves`, `strip` | schematic data sketches |

See `examples/dense-svg/example_pipeline.py` for a complete figure that exercises every primitive and passes the QA gate.
