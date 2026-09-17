---
name: block-diagram-drawer
description: "Draw publication-quality block diagrams and method figures (framework overviews, system architectures, pipelines, control loops, skill libraries, comparison and concept figures) as code-generated SVG plus 2x PNG that look like figures in ICRA, IROS, RSS, CoRL and NeurIPS robotics and AI papers: labels that print at 6 to 9 pt, names instead of sentences, symbols next to module names, real renders and photos, a muted flat palette and typeset math, calibrated on 359 figures from published papers and verified by a headless-Chrome QA gate for overflow, overlaps, lines through labels, print-size text, label contrast, sentence-length labels and a word budget. Use this skill whenever the user asks to draw, redraw, restyle or polish a block diagram, framework figure, method overview, architecture or pipeline figure for a paper, report, slide or case study (框图, 流程图, 方法图, 架构图, 示意图, 科研绘图, 论文插图, 把这个图画出来), sends a sketch, ASCII diagram, README or screenshot to turn into a figure, or says a figure does not look like a paper figure, is hard to read, has too much blank space, looks plain or looks AI-generated. Prefer academic-figures-drawer only when an editable draw.io source is the primary deliverable, archify for interactive HTML architecture explorers, and a charting skill for plots of real data."
---

# Block Diagram Drawer

Turn a description, sketch, README, ASCII diagram, or reference image into a block diagram that reads like a figure in a robotics or AI paper.
Each figure is a small Python build script using `scripts/figkit.py`; the SVG and a 2x PNG are derived from it and gated by `scripts/qa_svg_figure.py`.
The target look comes from a study of 359 method figures in 399 papers confirmed as published at robotics, ML and CV venues (`references/paper-figure-study.md`): the median label prints at 6.9 pt, small labels at 5.8 pt and title lines at 8.7 pt; a readable text-width figure carries about 40 label words, each label a one-to-four-word name, often with a symbol; real renders or photos anchor physical inputs and outputs; explanations live in the caption.

## Setup

Start every new figure with the scaffold; it vendors the kit next to the build script so old figures keep rendering after the skill changes:

```bash
python <skill-dir>/scripts/scaffold.py <project>/figures/src/fig_<name>.py --width 1400 --height 500 --panels 4
cd <project>/figures/src
python fig_<name>.py
python qa_svg_figure.py ../<name>-figure.svg --png
```

The QA gate needs Chrome, Chromium, or Edge; set `CHROME_PATH` if it is not found.
Before the first figure of a session, read `references/paper-figure-study.md` (what real figures look like, with measured sizes) and `references/visual-contract.md` (palette roles, typography, shapes, connectors, pitfalls, API).
`examples/example_pipeline.py` is a complete figure that passes the gate; copy idioms from it.

## Workflow

### 1. Build a content inventory and a caption draft

List every label, number, relationship, and loop from the user's source before drawing.
This list is the contract for the figure: redraws and restyles must reproduce it exactly.
Split it into what the canvas shows (module names, symbols, structure, example inputs and outputs) and what the caption says (definitions, cardinalities, explanations, why a part exists), and write the caption draft now.
A paper figure is read together with its caption, so moving a sentence into the caption keeps the content while keeping the canvas readable.
Never invent results, dimensions, module names, or case details.
When a card needs a data sketch that is not real data (a trajectory, a progress curve, an attention map), label it `schematic`.

### 2. Fix the print target, then plan the grid

- Decide where the figure will print: a text-width `figure*` uses a 1400 px canvas and a single column uses 700 px; both are about 2.7 px per printed point, so `f.fs()` sizes work for either.
- Pick the layout archetype before the aspect ratio (study shares in parentheses): left-to-right stages (33%), overview plus zoom (20%), two mirrored panels (16%), top-down layers (12%), grid of examples (8%), loop (5%), train versus inference (4%), hub and spoke (3%). Aspect ratio does not separate good from weak figures; published text-width figures have a median of 2.36, pipelines run wider and layered stacks taller.
- Draw a hierarchy as horizontal tinted bands or stacked group containers that carry only their name (in a corner or the margin), as in LLaVA, Kimera and RoboMatrix; do not add a column of descriptions or notes beside them, because that reads as documentation, not as a paper figure.
- For system and framework figures, prefer two or three stages or bands, one consistent title device, one pastel family per stage, and color identity carried across stages; add time scales (for example Hz labels) when layers of a robot control stack run at different rates.
- Split a two-part figure into panels `(a)` and `(b)` with short titles; for comparisons (baseline versus ours, training versus deployment) mirror the geometry across a `divider()` and change only the differing element.
- Use 8 px outer margins and 8 to 12 px gutters, share column positions across rows, and keep the figure title out of the canvas.
- Write the grid down as numbers (panel x-ranges, row y-ranges, card rectangles) before writing code.

### 3. Assign roles, then draw

- Take every font size from `f.fs(role)`: `note` 15 px, `min` 16 px, `label` 18 px, `module` 21 px, `title` 24 px, `hero` 33 px on a 1400 px canvas; primitives default to these sizes. Use `note=True` only for secondary annotations such as tensor shapes, sub-captions and tick labels.
- Aim for about 40 label words in a text-width figure; the gate warns above about 65 and fails above about 90 (scaled by printed area), the range of hard-to-read published figures.
- Write labels as names of one to four words, pair them with a symbol where the method has one (for example "World model $F_\psi$"), keep edge labels to one noun, verb or symbol, and never write explanatory sentences on the canvas.
- Keep example content (a user instruction, prompt, generated code, reasoning trace, feedback message) in one or two `f.example()` cards or `f.bubble()`, one to three lines each, truncated with an ellipsis and with the key word in its entity color; never paste whole traces, dialogs, JSON or code.
- Thread one concrete running example through every stage when the method processes an input, as strong published figures do.
- Anchor physical inputs and outputs with real imagery: embed renders, camera frames, point clouds or robot photos from the project with `f.image(path, x, y, w, h)`, and ask the user for a render when none is available; a drawn `scene()` is only a placeholder labeled `schematic`. Architecture figures without physical endpoints may stay imagery-free and use tokens, shapes and glyphs.
- Give each entity (modality, data source, view, agent) one hue and reuse it on its tokens, arrows, frames, label text and outputs; use three or four fill hues, five only when each maps to a named entity, and keep roles consistent across every figure of the same report.
- Emphasize the contribution with one accent used nowhere else (a distinct fill on a muted or gray scaffold, `key=True`, or size) and never emphasize several modules at once.
- Set module names in regular or medium weight and reserve bold for titles; use serif labels (`Fig(..., family="serif")`) when the paper body is Times, as 36% of published figures do.
- Keep nesting to two levels (panel, card, chip), prefer no legend (at most three or four entries in a corner), label an edge only when what flows is not obvious, and give each connector style one meaning: thin dark wires by default, block arrows for one or two major hand-offs, dashed or accent paths for training-only or feedback flows.
- Use shapes that carry meaning: token pills, trapezoid encoders, `hourglass()` U-Nets, bracketed vectors, cylinders for datasets, stacked cards for libraries and batches, speech bubbles, circled steps, braces, `mark("frozen" | "trainable")` in module corners, `outcome()` check and cross badges, `zoom()` insets for internals, `stage_ruler()` for stage names, `callout()` leader lines on renders, and vendored open-source icons for recognizable objects and named products.
- Avoid dated effects (drop shadows, bevels, gradient box fills, heavy black frames), low-contrast labels (light gray or white text on light fills), red/green-only status coding, and repeated decorative logos.
- Pass `box=` for every label inside a container so the gate can check overflow and exempt example content.

### 4. Gate, look, fix, repeat

Run the QA gate after every edit.
It fails on overflow, collisions, box overlaps, lines through labels, labels printing below 6 pt (5 pt for the note tier), labels longer than six words outside example content, label contrast below 3:1, a figure median label below 5 pt, label words above the printed-area budget (90 at 516 by 215 pt), more than 60 words of example content, and coverage below 0.40.
It warns on a figure median below 6 pt, more than about 65 label words, more than 30 example words, six or more fill hues, containers nested three deep, more than 35% bold labels, and contrast below 4.5:1; treat warnings as design feedback and fix them unless the user wants otherwise.
When text does not fit, cut words and move explanations to the caption first, then enlarge boxes or the canvas; never shrink type below `f.fs("min")`.
Relax a limit only on purpose (`--word-fail`, `--max-words`, `--min-coverage`), and report the measured value and the reason to the user.
Passing the gate is necessary, not sufficient, so always open the PNG and inspect it, including crops around dense cards, math, and connectors.
Compare the PNG with two or three exemplars from section 7 of `references/paper-figure-study.md` at the same printed width: if it has more words, smaller type, more hues or deeper nesting than they do, simplify before delivering.
Check that serif and monospace labels really render in those families, that arrows point the right way, and that no sketch implies data the source does not have.
Do at least three gate-and-inspect cycles for a figure the user cares about.

### 5. Deliver

- Put the SVG and PNG where the user keeps figures, and the build scripts plus the vendored kit in a `src/` folder beside them; keep `src/assets/` (icons, license files, `ASSETS.md`, and any renders) with the scripts.
- Before overwriting figures the user already has, move the previous versions into an archive folder such as `v1/`, and say so.
- Send or show the PNG together with the caption draft, summarize what changed, and state which parts are schematic or still need a real render.

## Open-source icons

Readers recognize a robot, camera, door, target, or checklist faster than the word, so figures should use real open-source icons for such objects instead of hand-drawn glyphs.
`scripts/svgicons.py` searches two MIT families and vendors only the icons a figure uses: `tabler` (Tabler Icons outline, 5000+ pictograms) and `lobe` (LobeHub logos of AI models and providers).

```bash
python <skill-dir>/scripts/svgicons.py search "robot arm"
python <skill-dir>/scripts/svgicons.py search qwen --family lobe
python <skill-dir>/scripts/svgicons.py get tabler:target --out <project>/figures/src/assets/target.svg
```

Place an icon with `f.asset(HERE / "assets" / "target.svg", x, y, 20, color=A.deep)`; figkit validates the file, embeds it once as a symbol, and normalizes the display stroke.

- Search two or three synonyms and compare silhouettes on a contact sheet before choosing; pick the icon whose shape names the object, not a loosely related metaphor.
- Keep one outline family (Tabler) per figure, a 1.5 px display stroke, and 18 to 28 px sizes on a 1400 px canvas; tint icons with the role's deep color or ink.
- Put an icon beside a label or inside a chip; it never replaces the label, never stands in for model internals, data, or math, and never becomes decoration on every card.
- Use a `lobe` logo only for the exact model or provider the figure names, prefer the mono variant, and keep it smaller than the module name.
- `get` copies the family license and records the source in `assets/ASSETS.md`; ship both with the figure.
- Without network access, fall back to figkit's built-in `icon()` glyphs and say so.

## Editable draw.io export

When the user wants to edit a figure by hand, convert the finished SVG instead of redrawing it:

```bash
python <skill-dir>/scripts/svg2drawio.py <project>/figures/<name>-figure.svg --png
```

The converter renders the SVG in headless Chrome and writes `<name>-figure.drawio`: panels, cards and chips become rounded rectangles (a chip's centered label becomes its vertex label), circles become ellipses, text keeps its spans (family, size, weight, italics, color, script offsets), orthogonal connectors become edges with waypoints, arrowheads and dashes, and icons, embedded images, curves and sketches are embedded as SVG images with no external files.
`--png` renders the result with the draw.io desktop CLI (set `DRAWIO_PATH` if needed); compare it with the figure PNG before handing it over.
Edges are free-standing rather than glued to shapes, so moving a card does not drag its connectors; say so when you deliver.

## Compaction requests

When the user asks for a more compact figure, keep the content inventory and the column grid, archive the current version, and reclaim height before width.

- Move explanatory words into the caption before touching geometry.
- Tighten card heights to their content and put connector labels in bands that already exist, such as the strip above a row of cards.
- Route feedback lanes and their labels through panel title rows, and start cards beside a panel title at the title's top.
- Shrink sketch frames and images before shrinking any font; type never goes below `f.fs("min")` (or `f.fs("note")` for secondary annotations), and the gate rejects it.
- Rerun the gate after every step; math with subscripts needs chips at least 1.9 times the font size tall.

## Restyle requests

When the user asks only for a better look (colors, fonts, "less AI", "more like a paper"), keep the content inventory unchanged and edit only the visual layer, except that sentences may move into the caption.
If the user names a venue or the current style is not landing, study five to ten recent method figures from that venue on arXiv HTML pages (the figure images are linked from each `figure` element) and compare them with `references/paper-figure-study.md` before editing; add durable findings to that file.
Compare the label inventory and caption before and after the restyle.

## Language

Follow the language of the user's report.
For bilingual figures, use English technical terms and math as the main label with a short Chinese annotation, or the reverse, but keep one pattern per figure.
Keep Chinese text upright in sans; never italicize CJK.

## Resources

| Path | Use |
|---|---|
| `scripts/scaffold.py` | start a figure: vendors the kit and writes a starter build script |
| `scripts/figkit.py` | primitives: print-size fonts (`fs`, note tier, serif option), panels, cards, example cards, chips, tags, text with math, real images, tokens, trapezoids, hourglasses, brackets, cylinders, bubbles, steps, frozen/trainable marks, outcome badges, dividers, stage rulers, zoom insets, callouts, block arrows, connectors, thumbnails, sketches |
| `scripts/qa_svg_figure.py` | headless-Chrome QA gate (layout, print size, words, contrast, hues, nesting) and 2x PNG export |
| `scripts/svg2drawio.py` | convert a finished SVG into an editable `.drawio` file, with an optional draw.io-rendered PNG for checking |
| `scripts/svgicons.py` | search and vendor open-source SVG icons (Tabler outline, LobeHub logos) with license and ledger |
| `references/paper-figure-study.md` | 359-figure study of published robotics, ML and CV method figures: print sizes, word counts, layout archetypes, verified rules, anti-patterns, exemplars |
| `references/licenses/` | MIT license texts copied beside vendored icons |
| `references/visual-contract.md` | full visual contract, API table, and pitfalls |
| `examples/example_pipeline.py` | complete reference figure |
| `tests/` | unit and browser tests for the kit (`python -m unittest discover -s tests`) |
