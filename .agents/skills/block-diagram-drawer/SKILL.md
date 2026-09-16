---
name: block-diagram-drawer
description: "Draw dense, publication-quality block diagrams and method figures (framework overviews, pipelines, control loops, system-comparison and concept figures) as code-generated SVG plus 2x PNG in the visual language of CoRL, RSS, ICRA and NeurIPS papers: muted flat palette, typeset math, serif-italic data labels, monospace tokens, schematic thumbnails and data sketches, verified by a headless-Chrome QA gate for text overflow, overlaps, lines through labels and canvas coverage. Use this skill whenever the user asks to draw, redraw, restyle or polish a block diagram, framework figure, method overview, architecture or pipeline figure for a paper, report, slide or case study (框图, 流程图, 方法图, 示意图, 科研绘图, 论文插图, 把这个图画出来), sends a sketch, ASCII diagram or screenshot to turn into a figure, or says a figure has too much blank space, looks plain or looks AI-generated. Prefer academic-figures-drawer only when an editable draw.io source is required, archify for interactive HTML architecture explorers, and a charting skill for plots of real data."
---

# Block Diagram Drawer

Turn a description, sketch, ASCII diagram, or reference image into a dense, paper-style block diagram.
Each figure is a small Python build script using `scripts/figkit.py`; the SVG and a 2x PNG are derived from it and gated by `scripts/qa_svg_figure.py`.
The target look is a CoRL, RSS, or ICRA method figure: every card carries a symbol, term, or sketch, typography carries hierarchy, and little canvas is wasted.

## Setup

Start every new figure with the scaffold; it vendors the kit next to the build script so old figures keep rendering after the skill changes:

```bash
python <skill-dir>/scripts/scaffold.py <project>/figures/src/fig_<name>.py --width 1400 --height 400 --panels 4
cd <project>/figures/src
python fig_<name>.py
python qa_svg_figure.py ../<name>-figure.svg --png
```

The QA gate needs Chrome, Chromium, or Edge; set `CHROME_PATH` if it is not found.
Read `references/visual-contract.md` before the first figure of a session; it holds the palette roles, typography, shape vocabulary, connector grammar, density numbers, and known pitfalls.
`examples/example_pipeline.py` is a complete figure that passes the gate; copy idioms from it.

## Workflow

### 1. Build a content inventory first

List every label, number, relationship, and loop from the user's source before drawing.
This list is the contract for the figure: redraws and restyles must reproduce it exactly.
Never invent results, dimensions, module names, or case details.
When a card needs a data sketch that is not real data (a trajectory, a progress curve, an attention map), label it `schematic · 示意`.
When the user asks for a more detailed figure, add only structure grounded in material already given (other figures, report text, the user's notes) and tell the user what was added.

### 2. Plan the grid

- Prefer one wide row of stage panels (about 2.4:1 to 3.7:1 at 1400 px width); stack rows only for parallel variants such as "Direct" versus "Hybrid".
- Use 8 px outer margins and 8 to 10 px gutters, and share column positions across rows so equivalent stages align.
- Keep the figure title out of the canvas; it belongs in the caption.
- Write the grid down as numbers (panel x-ranges, row y-ranges, card rectangles) before writing code.

### 3. Assign roles, then draw

- Give each concept one color role and keep it across every figure of the same report (for example reasoning model in `amber`, motor policy in `blue`, accept in `green`, override in `red`).
- Outline only the module the reader should find first with `key=True`.
- Use bold only for panel titles and key words, medium weight for module names, serif italic for data names and language, monospace for tokens and discrete outputs, and `$...$` for every symbol.
- Use shapes that carry meaning (token pills, trapezoid encoders, bracketed vectors, cylinders, speech bubbles, circled steps, braces) instead of decorative icons.
- Pass `box=` for every label inside a container so the gate can check overflow.

### 4. Gate, look, fix, repeat

Run the QA gate after every edit; it must report zero overflow, collisions, box overlaps, and lines through labels, with coverage of at least 0.55.
Passing the gate is necessary, not sufficient, so always open the PNG and inspect it, including crops around dense cards, math, and connectors.
Check that serif and monospace labels really render in those families, that arrows point the right way, and that no sketch implies data the source does not have.
Do at least three gate-and-inspect cycles for a figure the user cares about.

### 5. Deliver

- Put the SVG and PNG where the user keeps figures, and the build scripts plus the vendored kit in a `src/` folder beside them.
- Before overwriting figures the user already has, move the previous versions into an archive folder such as `v1/`, and say so.
- Send or show the PNG, summarize what changed, and state which parts are schematic.

## Restyle requests

When the user asks only for a better look (colors, fonts, "less AI", closer to a venue style), keep the content inventory unchanged and edit only the visual layer.
If the user names a venue or the current style is not landing, study five to ten recent method figures from that venue first (arXiv HTML pages expose figure images) and write down palette, weights, italics, and shape habits before editing.
Compare the label inventory before and after the restyle.

## Language

Follow the language of the user's report.
For bilingual figures, use English technical terms and math as the main label with a short Chinese annotation, or the reverse, but keep one pattern per figure.
Keep Chinese text upright in sans; never italicize CJK.

## Resources

| Path | Use |
|---|---|
| `scripts/scaffold.py` | start a figure: vendors the kit and writes a starter build script |
| `scripts/figkit.py` | primitives: panels, cards, chips, tags, text with math, tokens, trapezoids, brackets, cylinders, bubbles, steps, block arrows, connectors, thumbnails, sketches |
| `scripts/qa_svg_figure.py` | headless-Chrome QA gate and 2x PNG export |
| `references/visual-contract.md` | full visual contract, API table, and pitfalls |
| `examples/example_pipeline.py` | complete reference figure |
| `tests/` | unit and browser tests for the kit (`python -m unittest discover -s tests`) |
