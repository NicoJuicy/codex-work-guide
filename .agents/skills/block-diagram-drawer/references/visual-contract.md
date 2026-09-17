# Block Diagram Visual Contract

This contract governs static, paper-style block diagrams built as code-generated SVG.
The figure build script is the source of truth; the SVG and PNG are derived artifacts.
It trades in-editor editability for print-size typography, typeset math, real imagery, data sketches, and exact reproducible layout.
Its numbers come from measured robotics and AI method figures; see `paper-figure-study.md`.

## 1. When this skill is the right tool

Use it when at least one of these holds:

- The user wants a figure that looks like a top-venue paper figure and says the current result is sparse, plain, hard to read, generic, or looks AI-generated.
- The figure needs many small typeset symbols, sub/superscripts, or inline math next to labels.
- Cards should carry data sketches: thumbnails, trajectory curves, bar strips, attention maps, timelines, or schematic plots.
- Labels mix CJK and Latin text and must render consistently.
- The figure will be regenerated often, or several figures must share one exact visual system.

Use `academic-figures-drawer` instead when the user or venue needs an editable `.drawio` source, when collaborators will hand-edit the figure, or when the figure is a routing-heavy graph that benefits from the draw.io routing contract.
Use `archify` for interactive HTML architecture explorers, and a charting skill when the figure plots real data.
When the choice is unclear, ask once; otherwise default to this skill for "make it look like the paper figure" requests.

## 2. Why generated figures do not look like paper figures

Compare the draft against strong paper figures on these axes before changing anything.

| Axis | Strong paper figure | Typical generated draft |
|---|---|---|
| Print size | Median label 6.9 pt, small labels 5.8 pt, title lines 8.7 pt (about 19, 16 and 24 px on a 1400 px text-width canvas) | 11 to 13 px labels that print at 4 to 5 pt, the level of hard-to-read published figures |
| Words | About 40 label words in a text-width figure (hard-to-read figures: 85); labels of one to four words; short example prompts only | Explanatory sentences, questions, notes and pasted traces beside every part |
| Structure | Stage columns, mirrored panels, or named bands and containers; explanations in the caption | Bands with a column of descriptions and a column of notes, plus a legend strip explaining every symbol |
| Imagery | Real renders, camera frames, point clouds or photos | Cartoon scenes drawn from icons, or no task context at all |
| Fill | Content and imagery cover most of the canvas at readable size; gutters about 8 to 12 px | Large margins, in-canvas title band, long arrows, boxes two to three times larger than their text |
| Hierarchy | At most two nesting levels below the canvas (panel, card, chip) | One level of same-size boxes, or three nested bordered and dashed levels |
| Content | Names paired with symbols, terms, and notation hooks on every card | Prose sentences that read like slides |
| Palette | Three or four muted fills, each hue mapped to an entity and carried across panels; one accent for the contribution | Six or more arbitrary hues, gradients, drop shadows, thick saturated borders, white text on saturated fills |
| Typography | Regular or medium module names (70% of exemplars), bold only for titles; one label family, sans or the paper's serif | Bold on every module name (46% of hard-to-read figures), mixed families, uppercase letter-spaced headers |
| Shapes | Token pills, trapezoid encoders, bracketed vectors, cylinders, block arrows, circled step numbers, dashed groups | Rounded rectangles and generic UI icons for everything |
| Connectors | Thin near-black wires, braces, fork and merge dots, dashed gray loops with italic labels | Colored arrows on every edge |
| Layout | Wide single-row pipeline on a strict column grid; title lives in the caption | Vertical single columns with empty sides; title inside the canvas |

## 3. Print size and density contract

- The canvas maps to a print width: 1400 px for a text-width `figure*` (516 pt) and 700 px for one column (252 pt), about 2.7 px per point either way; `Fig` stores it as `data-print-width-pt`.
- No label prints below 6 pt (16.3 px at 1400 px), except note-tier annotations (tensor shapes, sub-captions, tick labels) down to 5 pt; math scripts inside a label are exempt.
- The figure's median label prints at 6.5 pt or more; the gate warns below 6 pt and fails below 5 pt.
- No label outside example content has more than six words; label words stay near 40 for a text-width figure, with a warning above 65 and a failure above 90, scaled by printed area.
- Example content stays short: one or two cards of one to three lines; the gate warns above 30 words and fails above 60.
- Label text keeps a contrast of at least 4.5:1 against its container (the gate fails below 3:1).
- Content coverage, measured by `scripts/qa_svg_figure.py`, is at least 0.40 and typically 0.55 to 0.75 once imagery is in place; framed coverage is usually above 0.85.
- Outer margin is 8 px; gutter between panels is 8 to 12 px; card padding is 10 to 14 px.
- No empty band wider than one card height may remain inside a panel; fill it with an image, sketch, notation, or example content, or shrink the panel.
- Do not put the figure title, a long subtitle, or explanatory notes inside the canvas; the paper caption carries them.
- Choose the aspect ratio from the layout archetype, not from a fixed range: published text-width figures have a median of 2.36, with pipelines wider and layered stacks taller; the ratio does not separate good from weak figures.
- Panel title rows are shared space: cards beside the title may start at its top, and loop lanes with their labels may run through the row.
- Density never comes from small text: first move explanations into the caption, then remove redundant words, then tighten boxes to their content, then reflow, then grow the canvas.

## 4. Visual language

The defaults in `scripts/figkit.py` follow a study of 359 method figures from papers confirmed as published at robotics, ML and CV venues; `paper-figure-study.md` lists the measurements, layout archetypes, verified rules and exemplars such as LLaVA, VIMA, DPO, InstructPix2Pix, AMO and Diffusion Policy.
Study a few current method figures from the target venue before a major restyle, and record the palette, weights, and shape vocabulary you adopt.

### 4.1 Composition

- **Stage panel:** flat, very light role tint without an outline, or a dashed warm-gray outline for input groups; left-aligned bold title with a panel label such as `(a)`, followed by a regular gray subtitle on the same line or below it in narrow panels.
- **Card:** pastel role tint with a 1 px stroke one step darker; white cards with a hairline stroke for neutral content.
- **Group container or band:** a layer or subsystem is a light tinted container or a full-width band carrying only its name (inside the top-left corner, in a title bar, or in the left margin); descriptions of what it does go in the caption, not in a side column.
- **Stage names:** use one device for the whole figure: titles above columns, a `stage_ruler()` bracket under them, or titles inside tinted containers.
- **Key module:** the contribution gets one accent used nowhere else: a distinct fill on a muted or gray scaffold, a near-black 1.4 px outline (`key=True`), or size; do not emphasize several modules or a whole path.
- **Zoom inset:** show a block's internals with `zoom()`: a dashed box on the block and two lines to a detail panel in the same tint.
- **Example card:** verbatim prompts, instructions, generated code and reasoning traces sit in `example()` cards or bubbles; these are the only places for sentences.
- **Image:** renders, camera frames, point clouds and photos are embedded with `image()` in a thin frame; they are the default way to show the task.
- **Chip:** small light rectangle with a hairline stroke; dashed chips mark derived or linked quantities.
- **Tag:** tint fill with bold deep-color text for a key number; never a saturated filled pill with white text.
- Use a shared column grid across rows so equivalent stages align vertically.
- Every card gets a hook: a symbol, notation, thumbnail, data sketch, or attached technical term.
- Attach technical terms to the component they belong to instead of listing them in a separate legend; when a legend is unavoidable, keep it to four entries in a corner.

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

Connectors are near-black (`WIRE`) by default; color an edge when it carries a branch outcome or when color encodes an entity or flow type, and then color its label to match instead of adding a legend.

Provenance color: give each entity (a modality, data source, camera view, agent, or query type) one hue and reuse it on its tokens, arrows, frame borders, label text and every output derived from it, across all panels.
Stage tints and the contribution accent share the same budget: three or four fill hues per figure, five only when every hue maps to a named entity; the gate warns at six.
Never code status with red and green alone; pair color with a check or cross (`outcome()`), a dash pattern, or a label.
Avoid gradients on containers; a gentle gradient is acceptable only inside a token row that blends two modalities.

### 4.3 Typography

- Sans (Helvetica Neue or Arial with a CJK fallback) for labels.
- Bold (600 to 700) only for panel titles, stage names, branch outcomes, and one or two key words per card; the gate warns when more than 35% of labels are bold.
- Regular (400) or medium (500) for module and card names; light (300) for one large focal word or number.
- Serif italic (`family="serif", italic=True`) for data names, variables in prose, quoted language, and connector labels.
- Monospace (`family="mono"`) for tokens, discrete outputs such as `accept` or `override`, tick labels, and code-like terms.
- Math through `$...$` for every symbol; never fake math with sans italics.
- Sentence case everywhere; no uppercase letter-spaced headers.
- Chinese text stays upright in sans; do not synthesize italic CJK.
- Sizes come from `f.fs(role)`, which converts measured printed sizes to canvas pixels: `note` 5.5 pt (14.9 px at 1400 px) for secondary annotations only, `min` 6 pt (16.3 px), `label` 6.7 pt (18.2 px), `module` 7.8 pt (21.2 px), `title` 9 pt (24.4 px), `hero` 12 pt (32.6 px) for one focal symbol or number.
- Sans labels appear in 50% of published figures and serif labels in 36% (48% in CV); use `Fig(..., family="serif")` when the paper body is Times, and keep one family for labels (mixed families are common in hard-to-read figures).
- Avoid rotated labels inside narrow bars when horizontal space exists, and thin monospace text below 6 pt.
- Nothing prints below 6 pt: figures are read at column or text width, where smaller labels become unreadable. The QA gate enforces this with `smallText`.

### 4.4 Shape vocabulary

| Meaning | Primitive |
|---|---|
| sequence of tokens or an action chunk | `tokens` |
| encoder or feature extractor | `trapezoid` |
| action or state vector | `bracket` around math symbols |
| stored data, history, dataset | `cylinder` |
| encoder-decoder (U-Net) | `hourglass` |
| library, batch, N parallel copies | `card(stack=n)` |
| frozen or trainable module | `mark("frozen")` snowflake, `mark("trainable")` flame, in the module corner |
| accept or reject, success or failure branch | `outcome(ok=True/False)` check or cross badge |
| baseline versus ours, training versus deployment | mirrored panels split by `divider()` |
| stage names under or above columns | `stage_ruler()` |
| internals of one block | `zoom()` inset |
| part of a render or photo | `callout()` leader line with a dot |
| language input or model utterance | `bubble` |
| ordered sub-steps | `step` circled numbers |
| stage transition | `block_arrow` |
| grouped inputs | `brace` |
| task scene, camera frame, point cloud, robot photo | `image` with a real render or photo; `scene` only as a labeled placeholder |
| user instruction, prompt, generated code, reasoning trace | `example` card or `bubble` |
| recognizable object (robot, camera, door, goal, checklist) | vendored Tabler outline icon via `asset` |
| named model or provider | vendored LobeHub mono logo via `asset` |

Icons label objects; they are not content.
Method-specific structure (graphs, token rows, kinematic chains, curves) stays a drawn sketch, while recognizable objects use a vendored open-source icon instead of a hand-drawn imitation.

### 4.5 Open-source icons

- Source icons with `scripts/svgicons.py`: `tabler` for pictograms, `lobe` for model and provider logos; both are MIT and only selected files are downloaded.
- Compare two or three candidates per noun on a contact sheet rendered with `asset`, and choose the silhouette that names the object.
- Use one outline family per figure; do not mix Tabler with built-in `icon()` glyphs in the same row.
- Display stroke 1.5 px (the `sw` default), size 18 to 28 px on a 1400 px canvas, color from the role's deep tone or ink; `asset` rescales the stroke so every size matches.
- An icon sits beside a label or inside a chip and never replaces the label; do not put an icon on every card.
- Logos are trademarks: use one only for the product the figure names, prefer the mono variant, and keep it smaller than the module name.
- `asset` rejects scripts, stylesheets, event handlers, embedded documents, entities and external references, and namespaces internal ids, because symbols share the figure document.
- Keep `assets/` with the build script: the SVGs, the copied `LICENSE-*.txt`, and `ASSETS.md` with each source URL.

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
- One meaning per connector style: thin dark wires by default, block arrows only for one or two major hand-offs, dashed or accent-colored paths for training-only, gradient or feedback flows, explained by a two-entry key when needed.
- Label an edge only when what flows is not obvious from its endpoints; use a symbol, a noun or a verb.
- Circled step numbers on arrows or stage headers tie a loop or pipeline to the text; section references such as §3.1 in stage titles are fine.
- Double-headed short arrow with a monospace label (for example `MSE`) for comparisons.
- Curly brace to group several inputs into one consumer.
- Diamond or two-segment pill only for an explicit decision; label branches in serif italic (`yes`, `no`) or monospace (`accept`, `override`).
- No connector may cross a label; move the label or reroute, then rerun QA.

## 7. Workflow

1. Write the content inventory: inputs, stages, contribution, outputs, every label and number, and which parts may only be schematic.
2. Sketch the column grid in numbers: canvas size, panel x-ranges, row y-ranges, card rectangles.
3. Start each figure with `scripts/scaffold.py`, then write one build script per figure with the vendored `figkit.py`; keep coordinates explicit and grouped by panel.
4. Run `python scripts/qa_svg_figure.py <figure>.svg --png`.
5. Fix every reported issue, then open the PNG and inspect it at 100 percent and in crops around dense cards, math, and connectors; confirm serif and monospace labels really render in those families.
6. Repeat until QA passes and the visual inspection finds no P0 or P1 defect; perform at least three cycles for a user-critical figure.
7. Deliver the build script, `figkit.py` version in use, SVG, and 2x PNG together.

## 8. QA gate and its limits

The gate fails on any of: text overflowing its container or the canvas, text collisions, partially overlapping sibling boxes, strokes crossing uncovered labels, labels that print below 6 pt (5 pt for the note tier), labels longer than six words outside example content, label contrast below 3:1, a figure median label below 5 pt, label words above the printed-area budget, example content above 60 words, or coverage below the threshold.
It warns on a median label below 6 pt, label words above about 65, example words above 30, six or more fill hues, containers nested three deep, more than 35% bold labels, and contrast below 4.5:1.
Every limit has a flag (`--min-pt`, `--note-min-pt`, `--print-width-pt`, `--max-words`, `--word-warn`, `--word-fail`, `--example-fail`, `--min-coverage`); relax one only deliberately and report why.
QA cannot judge semantics, arrow direction, icon fit, misleading sketches, font fallback, or aesthetic balance, so the rendered PNG must still be inspected.
Link every text element to its container with `box=` so overflow is checked; freestanding labels are still covered by the collision and line checks.

## 9. Pitfalls observed in practice

- A `text{font-family: ...}` rule inside the SVG `<style>` overrides per-element `font-family` attributes, so serif and monospace labels silently fall back to sans; set the default family on the root `<svg>` instead, as figkit does.
- Heuristic text widths are only estimates; accept a layout only after the browser measurement passes.
- A `text` element with `text-anchor="middle"` stays centered only while its tspans use relative `dy`/`dx`; absolute `x` on a tspan starts a new chunk.
- Serif math glyphs have tall bounding boxes; give large focal symbols about 1.2 times their font size of vertical clearance, and give connector labels a knock-out at least 21 px high.
- A subscripted symbol such as $t_1$ or $\pi_{0.5}$ overflows a chip shorter than about 1.9 times its font size; at `fs("label")` use chips at least 36 px tall.
- Layer bands with a column of descriptions, a notes column and a legend strip of meanings look like documentation even when every check passes; keep only the band names and move the prose to the caption.
- Pasting a full reasoning trace, dialog or code block into an example card makes the whole figure read small; truncate to one to three lines.
- Light gray labels on tinted cards fail contrast; use `MUTED` or the role's deep color for secondary text.
- SVG sources with transparent backgrounds render black in some viewers and converters; figkit always paints a white background rectangle, so keep it.
- Raising coverage by adding notes, legends or extra cards makes a figure denser but less like a paper figure; fill space with imagery, examples or larger type instead.
- `scene()` keeps its own 4:3 artwork, so a much wider frame shows empty side bars; keep scene frames near 4:3 or use a real image with `fit="cover"`.
- Outlining every step of an example path in black removes the single focal point; emphasize one module.
- A connector that must cross another connector should break the secondary (dashed feedback) line for a few pixels at the crossing rather than hide the primary flow.
- An arrow that crosses a panel gutter must be drawn after both panels; otherwise the later panel's fill hides the arrowhead.
- A label pill centered on a short connector hides the line and its direction; place the pill beside the connector instead.
- Write primes as `a'_t` rather than as a superscript command, so the subscript attaches correctly.
- Unbraced scripts such as `E_\theta` must consume the whole command; figkit handles this, and a regression test covers it.
- Card-bottom chip rows reserve space; sketches placed above them must end at least 6 px earlier.
- Curves in schematic plots often cross their own annotations; place annotations in empty plot regions and use a short leader arrow when needed.
- Gradients, uppercase tracked headers, saturated filled badges, and decorative UI icons are the fastest way to make a figure look machine-generated.
- A decorative element that looks like data invites misreading; either make it schematic and labeled or remove it.
- Tabler sets `stroke-width="2"` on a 24 px grid, which renders thinner at 16 px and heavier at 32 px; place icons with `asset` so the display stroke stays constant.
- LobeHub color variants carry brand gradients that clash with a muted palette; use the mono variant tinted with ink.
- A hand-drawn glyph next to a vendored icon of the same kind reads as two styles; replace the whole row.

## 10. figkit API summary

| Call | Purpose |
|---|---|
| `Fig(w, h, print_width_pt=None, family="sans")` then `save(path)` | canvas, defs, and output; print width defaults to 516 pt for canvases at least 1000 px wide and 252 pt otherwise; `family="serif"` for Times papers |
| `fs(role)` | print-size font in px for `note`, `min`, `label`, `module`, `title`, `hero` |
| `panel(x, y, w, h, role, title, sub=None, dashed=False, sub_below=False)` | flat stage panel; returns the content top y; `title=None` for a headerless strip |
| `card(x, y, w, h, role, stack=0, key=False, fill=None, stroke=None, dashed=False)` | pastel or white card; returns an id for `box=` |
| `example(x, y, w, h, role=None, fill=None, stroke=None, dashed=False)` | card for verbatim prompts, code and traces; its labels are exempt from word limits |
| `image(path, x, y, w, h, fit="cover", r=3, frame=HAIR)` | embed a PNG, JPEG or WebP render or photo (up to 8 MB) as a data URI with a thin frame |
| `chip`, `badge`, `pill`, `step` | small labeled containers, quiet number tags, connector labels, circled step numbers |
| `text(x, y, s, size, weight, color, anchor, box=id, family=None, italic=False, note=False)` | rich text with `$math$`; `family` overrides the figure family with `sans`, `serif`, or `mono`; `note=True` marks a secondary annotation |
| `tokens`, `trapezoid`, `hourglass`, `bracket`, `cylinder`, `bubble`, `block_arrow` | shapes with meaning (section 4.4) |
| `mark(kind, x, y)`, `outcome(x, y, ok)` | frozen, trainable or locked marks; check or cross outcome badges |
| `divider(x, y0, y1)`, `stage_ruler(spans, y)`, `zoom(src, dst)`, `callout(ax, ay, lx, ly, s)` | mirrored-panel rule, bracket stage names, zoom insets, leader-line labels |
| `arrow(d, color=WIRE, dashed, start, end, open_)`, `line`, `dot`, `brace` | connectors |
| `scene(x, y, w, h, frame)` | schematic tabletop thumbnail |
| `bars`, `curves`, `strip` | schematic data sketches |
| `asset(path, x, y, size, color, sw=1.5)` | vendored open-source SVG icon or logo as a shared symbol with a QA box |
| `icon(name, x, y, size, color)` | built-in line glyph; offline fallback when no vendored icon fits |

See `examples/example_pipeline.py` for a complete figure that exercises the visual language and passes the QA gate.
