# Dense SVG Figure Track

This track produces static, information-dense, paper-style figures as code-generated SVG.
The figure script is the source of truth; the SVG and PNG are derived artifacts.
It complements the draw.io track and shares its semantic rules, but trades in-editor editability for density, typeset math, data sketches, and exact reproducible layout.

## 1. When to choose this track

Choose the dense SVG track when at least one of these holds:

- The user wants a figure that looks like a top-venue paper figure and says the current result is sparse, plain, generic, or looks AI-generated.
- The figure needs many small typeset symbols, sub/superscripts, or inline math next to labels.
- Cards should carry data sketches: thumbnails, trajectory curves, bar strips, attention maps, timelines, or schematic plots.
- Labels mix CJK and Latin text and must render consistently.
- The figure will be regenerated often, or several figures must share one exact visual system.

Choose the draw.io track when the user or venue needs an editable `.drawio` source, when collaborators will hand-edit the figure, or when the figure is a routing-heavy graph that benefits from the draw.io routing contract.
When the choice is unclear, ask once; otherwise default to draw.io for editable deliverables and to dense SVG for "make it look like the paper figure" requests.

## 2. Why generated figures look sparse or AI-made

Compare the draft against strong paper figures on these axes before changing anything.

| Axis | Strong paper figure | Typical generated draft |
|---|---|---|
| Fill | Blocks and text cover most of the canvas; gutters are about 8 to 10 px | Large margins, in-canvas title band, long arrows, boxes two to three times larger than their text |
| Hierarchy | Three nesting levels: stage panel, card, chip or symbol | One level of same-size boxes |
| Content | Symbols, terms, and notation hooks on every card | Prose sentences that read like slides |
| Palette | Three or four muted flat fills with a slightly darker stroke, warm-gray neutrals | Gradients, many saturated hues, thick colored outlines, filled saturated badges |
| Typography | Bold only for panel titles and key words; regular or medium module names; serif italic for data names and language; monospace for tokens and outputs | Bold sans everywhere and uppercase letter-spaced headers, which read as a UI dashboard |
| Shapes | Token pills, trapezoid encoders, bracketed vectors, cylinders, block arrows, circled step numbers, dashed groups | Rounded rectangles and generic UI icons for everything |
| Connectors | Thin near-black wires, braces, fork and merge dots, dashed gray loops with italic labels | Colored arrows on every edge |
| Layout | Wide single-row pipeline on a strict column grid; title lives in the caption | Vertical single columns with empty sides; title inside the canvas |

## 3. Density contract

- Content coverage, measured by `scripts/qa_svg_figure.py`, is at least 0.55 and typically 0.60 to 0.75.
- Framed coverage (panels plus content) is at least 0.90.
- Outer margin is 8 px; gutter between panels is 8 to 10 px; card padding is 6 to 12 px.
- No empty band wider than one card height may remain inside a panel; fill it with a meaningful sketch, notation, or attached term, or shrink the panel.
- Do not put the figure title or a long subtitle inside the canvas; the paper caption carries the title.
- Prefer a wide aspect ratio for pipelines (about 2.4:1 to 3.7:1 at 1400 px width) and stack rows only when the story has parallel variants.
- Shrinking fonts is the last resort; first remove redundant words, then tighten boxes to their content, then reflow.

## 4. Visual language

The defaults in `scripts/figkit.py` follow method figures from CoRL, RSS, and ICRA papers: pi0, OpenVLA, Octo, 3D Diffusion Policy, RT-H, YAY Robot, ReKep, RoboPoint, DexMimicGen, and Hi Robot.
Study a few current method figures from the target venue before a major restyle, and record the palette, weights, and shape vocabulary you adopt.

### 4.1 Composition

- **Stage panel:** flat, very light role tint without an outline, or a dashed warm-gray outline for input groups; left-aligned bold title with a panel label such as `(a)`, followed by a regular gray subtitle on the same line or below it in narrow panels.
- **Card:** pastel role tint with a 1 px stroke one step darker; white cards with a hairline stroke for neutral content.
- **Key module:** exactly the module the reader should find first gets a near-black 1.4 px outline (`key=True`); do not outline everything.
- **Chip:** small light rectangle with a hairline stroke; dashed chips mark derived or linked quantities.
- **Tag:** tint fill with bold deep-color text for a key number; never a saturated filled pill with white text.
- Use a shared column grid across rows so equivalent stages align vertically.
- Every card gets a hook: a symbol, notation, thumbnail, data sketch, or attached technical term.
- Attach technical terms to the component they belong to instead of listing them in a separate legend.

### 4.2 Color roles

Assign one role per concept and reuse it in every figure of the same paper.

| Role key (alias) | Typical meaning |
|---|---|
| `amber` (ochre) | reasoning model, planner, the key module |
| `blue` (teal) | motor policy, perception, main learned policy |
| `green` (sage) | accept, success, closing feedback |
| `red` (terracotta) | contribution highlight, override, error, loss |
| `purple` (lavender) | control, structure, auxiliary models |
| `orange` (clay) | proprioception or a secondary signal |
| `gray` (stone) | inputs, neutral containers, standard components |

Connectors are near-black (`WIRE`) by default; color an edge only when it carries a branch outcome such as accept or override.
Avoid gradients on containers; a gentle gradient is acceptable only inside a token row that blends two modalities.

### 4.3 Typography

- Sans (Helvetica Neue or Arial with a CJK fallback) for labels.
- Bold (700) only for panel titles, branch outcomes, and one or two key words per card.
- Medium (500) for module and card names; light (300) for one large focal word or number.
- Serif italic (`family="serif", italic=True`) for data names, variables in prose, quoted language, and connector labels.
- Monospace (`family="mono"`) for tokens, discrete outputs such as `accept` or `override`, tick labels, and code-like terms.
- Math through `$...$` for every symbol; never fake math with sans italics.
- Sentence case everywhere; no uppercase letter-spaced headers.
- Chinese text stays upright in sans; do not synthesize italic CJK.
- Sizes at 1400 px width: panel title 13.5 to 14 px, card name 12 to 13 px, body 10 to 11.5 px, annotations 9.5 to 10.5 px, one focal symbol 24 to 30 px.

### 4.4 Shape vocabulary

| Meaning | Primitive |
|---|---|
| sequence of tokens or an action chunk | `tokens` |
| encoder or feature extractor | `trapezoid` |
| action or state vector | `bracket` around math symbols |
| stored data, history, dataset | `cylinder` |
| language input or model utterance | `bubble` |
| ordered sub-steps | `step` circled numbers |
| stage transition | `block_arrow` |
| grouped inputs | `brace` |
| task scene | `scene` thumbnail (replace with a task-specific sketch when needed) |

Generic UI icons are not content; use a drawn sketch that carries meaning (for example a kinematic chain for an IK solver) or nothing.

## 5. Content grammar and honesty

- Thumbnails of the task scene belong in input, perception, and execution regions only.
- Data sketches (curves, bars, heatmaps, timelines, progress plots) must be labeled `schematic` when they do not plot real data.
- Plot real numbers only when the source states them; simple derived arithmetic (for example showing a stated 40% reduction as a 60% bar) is allowed and must stay traceable.
- Never invent results, dimensions, module names, or case details; when a case study is only described in words, draw a schematic and say so in the figure.
- A visual restyle must not change content; compare the label inventory before and after.
- Prefer a linked pair of dashed chips with the same color over a long arrow that would cross several cards.

## 6. Connector vocabulary

- Thin near-black arrow with a small filled head for the main flow.
- Dot plus short bus for fork and merge; color only the branch segments that carry an outcome.
- Dashed gray rounded arc routed inside panel gutters for closed loops and feedback, with a serif italic label on a white knock-out.
- Double-headed short arrow with a monospace label (for example `MSE`) for comparisons.
- Curly brace to group several inputs into one consumer.
- Diamond or two-segment pill only for an explicit decision; label branches in serif italic (`yes`, `no`) or monospace (`accept`, `override`).
- No connector may cross a label; move the label or reroute, then rerun QA.

## 7. Workflow

1. Write the semantic brief exactly as in the draw.io track: inputs, stages, contribution, outputs, and allowed facts.
2. Sketch the column grid in numbers: canvas size, panel x-ranges, row y-ranges, card rectangles.
3. Write one build script per figure using `scripts/figkit.py`; keep coordinates explicit and grouped by panel.
4. Run `python scripts/qa_svg_figure.py <figure>.svg --png`.
5. Fix every reported issue, then open the PNG and inspect it at 100 percent and in crops around dense cards, math, and connectors; confirm serif and monospace labels really render in those families.
6. Repeat until QA passes and the visual inspection finds no P0 or P1 defect; perform at least three cycles for a user-critical figure.
7. Deliver the build script, `figkit.py` version in use, SVG, and 2x PNG together.

## 8. QA gate and its limits

The gate fails on any of: text overflowing its container or the canvas, text collisions, partially overlapping sibling boxes, strokes crossing uncovered labels, or coverage below the threshold.
QA cannot judge semantics, arrow direction, icon fit, misleading sketches, font fallback, or aesthetic balance, so the rendered PNG must still be inspected.
Link every text element to its container with `box=` so overflow is checked; freestanding labels are still covered by the collision and line checks.

## 9. Pitfalls observed in practice

- A `text{font-family: ...}` rule inside the SVG `<style>` overrides per-element `font-family` attributes, so serif and monospace labels silently fall back to sans; set the default family on the root `<svg>` instead, as figkit does.
- Heuristic text widths are only estimates; accept a layout only after the browser measurement passes.
- A `text` element with `text-anchor="middle"` stays centered only while its tspans use relative `dy`/`dx`; absolute `x` on a tspan starts a new chunk.
- Serif math glyphs have tall bounding boxes; give large focal symbols about 1.2 times their font size of vertical clearance, and give connector labels a knock-out at least 21 px high.
- Write primes as `a'_t` rather than as a superscript command, so the subscript attaches correctly.
- Unbraced scripts such as `E_\theta` must consume the whole command; figkit handles this, and a regression test covers it.
- Card-bottom chip rows reserve space; sketches placed above them must end at least 6 px earlier.
- Curves in schematic plots often cross their own annotations; place annotations in empty plot regions and use a short leader arrow when needed.
- Gradients, uppercase tracked headers, saturated filled badges, and decorative UI icons are the fastest way to make a figure look machine-generated.
- A decorative element that looks like data invites misreading; either make it schematic and labeled or remove it.

## 10. figkit API summary

| Call | Purpose |
|---|---|
| `Fig(w, h)` then `save(path)` | canvas, defs, and output |
| `panel(x, y, w, h, role, title, sub=None, dashed=False, sub_below=False)` | flat stage panel; returns the content top y; `title=None` for a headerless strip |
| `card(x, y, w, h, role, stack=0, key=False, fill=None, stroke=None, dashed=False)` | pastel or white card; returns an id for `box=` |
| `chip`, `badge`, `pill`, `step` | small labeled containers, quiet number tags, connector labels, circled step numbers |
| `text(x, y, s, size, weight, color, anchor, box=id, family="sans", italic=False)` | rich text with `$math$`; `family` is `sans`, `serif`, or `mono` |
| `tokens`, `trapezoid`, `bracket`, `cylinder`, `bubble`, `block_arrow` | shapes with meaning (section 4.4) |
| `arrow(d, color=WIRE, dashed, start, end, open_)`, `line`, `dot`, `brace` | connectors |
| `scene(x, y, w, h, frame)` | schematic tabletop thumbnail |
| `bars`, `curves`, `strip` | schematic data sketches |
| `icon(name, x, y, size, color)` | small line glyph; avoid as the only content of a card |

See `examples/dense-svg/example_pipeline.py` for a complete figure that exercises the visual language and passes the QA gate.
