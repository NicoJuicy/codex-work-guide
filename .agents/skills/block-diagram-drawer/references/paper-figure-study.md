# Paper Figure Study: Method Figures in Published Robotics, ML and CV Papers

This note records what published method, architecture and system figures actually look like, so figures drawn with this skill are judged against real papers rather than against earlier drafts.
Read it before a restyle, before the first figure for a paper, and whenever a user says a figure does not look like a paper figure or is hard to read.

## 1. Dataset and method

- Candidates came from twelve scoped searches: RSS, CoRL, ICRA, IROS and RA-L/T-RO, NeurIPS, ICML, ICLR, CVPR, ICCV and ECCV, embodied AI, award papers, and system or framework figures, 2023 to 2026.
- Every paper was confirmed as published in a main track or journal through official proceedings, OpenReview accept decisions, IEEE Xplore or DBLP; arXiv comments alone did not count, and workshop papers were excluded.
- 399 papers passed (RSS 61, CoRL 60, ICRA 49, CVPR 44, NeurIPS 41, IROS 34, ICML 33, ICLR 33, ICCV 22, IEEE journals 13, ECCV 9).
- Method figures were downloaded from the arXiv HTML versions into a local study dataset kept outside this skill (images, publication evidence and license links, per-figure records, statistics and an offline gallery); the figures remain the authors' work and are not redistributed here.
- Print sizes were measured automatically with Apple Vision OCR on every figure: line box heights were converted to font sizes with factors calibrated on 584 labels of known size in rendered figkit figures (figure-median error under 0.4 pt), then to points using each venue template's text width and the figure's LaTeXML width fraction.
- 359 figures, one main method figure per paper (robotics 216, ML 68, CV 64, embodied AI 11), were rated by agents that viewed each image: layout archetype, label style, typography, color, emphasis, imagery, connectors, containers, whitespace, readability and exemplar quality.
- A synthesis agent derived rules from the records, and two adversarial reviewers (evidence and generality) refuted or corrected each rule; only surviving or corrected rules are kept below.

Caveats:

- `pt_median` is the median line size in a figure, `pt_p10` its small labels and `pt_p90` its titles; OCR misses some math and very small text, and SVG sources without raster text were skipped.
- Printed sizes assume the figure is placed at the LaTeX width it was given; figures squeezed into one column print smaller than a text-width layout suggests.
- Readability ratings partly reflect apparent text size, so contrasts between exemplar and low-readability groups overstate size effects; exemplar ratings (4 or 5) cover 222 of 359 figures.

## 2. Print size and text

| Group | Figures | Median line pt | Small labels pt | Title lines pt | Words (median / p75) | Longest label words | Aspect |
|---|---|---|---|---|---|---|---|
| All | 359 | 6.9 | 5.8 | 8.7 | 41 / 69 | 4 | 2.36 |
| Robotics | 216 | 6.9 | 5.8 | 9.1 | 42 / 68 | 4 | 2.29 |
| ML | 68 | 6.4 | 5.3 | 8.6 | 40 / 83 | 4 | 2.35 |
| CV | 64 | 6.6 | 5.7 | 8.1 | 40 / 67 | 4 | 2.50 |
| System or framework figures | 107 | 6.9 | 5.6 | 8.4 | 48 / 84 | 4 | 2.25 |
| Exemplar-rated (4 or 5) | 222 | 7.0 | 5.8 | 8.8 | 39 / 64 | 4 | 2.50 |
| Low readability (1 or 2) | 52 | 4.6 | 3.8 | 6.5 | 85 / 127 | 6 | 2.52 |

- Ordinary labels print near 7 pt, small labels near 5.8 pt and title lines near 9 pt; a 1400 px text-width canvas is about 2.7 px per point, so that is about 19, 16 and 24 px.
- Readable figures have about 40 label words; the low-readability group has twice as many words and prints at 4 to 5 pt.
- Labels are one to four words; 97% of figures have no explanatory sentence on the canvas.
- Example content (a prompt, instruction, dialog, code or reasoning trace) appears in 27% of figures, 41% in ML; long traces and code blocks are over-represented in low-readability figures (prompt 38%, dialog 12%, code 12% versus 23%, 3% and 1% in exemplars).
- Aspect ratio does not separate good from weak figures; choose it from the layout.

## 3. Layout archetypes

| Archetype | Share | Used for | Structure |
|---|---|---|---|
| Left-to-right stages | 33% | pipelines where data transforms at each stage | three to five columns on one baseline, real input at the left and output at the right, thin arrows, at most one block arrow for the key hand-off |
| Overview plus zoom | 20% | an overview whose one or two key internals need detail | compact overview row; a dashed or colored box on the expanded block and two zoom lines to a same-tint detail panel |
| Two panels | 16% (ML 25%) | baseline versus ours, pretraining versus finetuning, method versus deployment | identical geometry in both halves, separated by a thin rule; only the changed element gets color |
| Top-down layers | 12% | transformer or DiT internals, LLM stacks, hierarchies of layers | full-width backbone bars, token rows as small squares above and below, encoders as trapezoids, residual side rails |
| Grid of examples | 8% | task variants, benchmarks, capability teasers | titled columns and labeled rows with identical cell geometry |
| Loop or cycle | 5% | agent-environment loops, self-refinement, data flywheels | three or four nodes clockwise, circled step numbers, one labeled return path around the outside |
| Train versus inference | 4% | distillation, CVAE encoders, motion priors | a divider with a title on each side; training-only paths dashed or in an accent color with a two-entry key |
| Hub and spoke | 3% | a shared controller, map or memory | a central model or render with short spokes; it fails once spokes carry text |

System and framework figures work best with two or three stage columns or horizontal bands, one consistent title position, one pastel family per stage, color identity carried across stages, and a stage ruler or band names instead of deeply nested boxes (examples: 2210.03094 VIMA, 2302.12766, 2505.03738 AMO, 2502.04307, 2506.16475).
Horizontal tinted bands per layer or phase are common and fine when the band carries only its name; what reads as documentation is a separate column of descriptions and notes.

## 4. Style distributions

| Property | All figures | Exemplars | Low readability |
|---|---|---|---|
| Label family | sans 50%, serif 36%, mixed 12% | sans 49%, serif 37% | sans 52%, mixed 17% |
| Module weight | regular 62%, bold 34% | regular 70%, bold 25% | regular 50%, bold 46% |
| Palette | pastel 47%, mixed 31%, saturated 14% | pastel 54%, saturated 9% | pastel 50%, saturated 12% |
| Fill hues | median 3, p75 5 | median 3, p75 4 | median 4, p90 6 |
| Borders | thin 46%, none 30%, thick 15% | thin 49%, none 30% | thin 56%, none 19% |
| Emphasis | color 42%, fill 23%, size 15%, outline 7% | color 45%, fill 20%, outline 8% | fill 29%, color 38%, outline 10% |
| Connectors | thin dark 53%, colored by type 18%, block arrows 11% | thin dark 58%, block 9% | thin dark 44%, block 21% |
| Containers | tinted 28%, none 28%, bordered 18%, dashed 17% | tinted 31%, none 27% | tinted 29%, bordered 23% |
| Nesting depth | median 1 | median 1, p90 2 | median 2, p90 3 |
| Legend entries | median 0, p90 3 | p90 3 | p90 4 |
| Whitespace | balanced 56%, tight 27% | balanced 68%, tight 17% | tight 48%, balanced 38% |
| Imagery | photo 54%, render 44%, icon 42%, plot 23%, point cloud 11%, none 9% | similar | similar, logos 12% |

Field differences:

- Robotics figures are the most image-heavy (median imagery share 0.35; photos 63%, renders 56%, point clouds 16%; only 6% without imagery) and use short phrases and bold module names more often.
- ML figures are the least image-heavy (median share 0.14, 22% without imagery), carry the most example content, and print smallest; the best ML figures are token-level or geometric abstractions with very few words.
- CV figures are the most typographically disciplined: serif labels 48%, regular module weight 80%, thin borders 58%, token or feature blocks 59%, frozen or trainable marks 25%.

## 5. Rules that survived adversarial review

1. Aim the figure's median label at 6.5 to 8 pt in print and keep ordinary labels at 6 pt or more; allow a secondary note tier near 5 to 5.5 pt for tensor shapes, sub-captions and tick labels; treat a figure median below 5 pt as broken.
2. Target about 40 label words for a text-width figure; beyond about 65 the figure is in the range of the weak group, and beyond about 90 it matches their median.
3. Keep example content short: one or two cards, one to three lines each, truncated with an ellipsis, the key word in its entity color; never print full traces, dialogs, JSON or code paragraphs.
4. Write labels as one-to-four-word names, with the method's symbol where one exists; edge labels are a single noun, verb or symbol.
5. Give each entity (modality, data source, view, agent) one hue and reuse it on its tokens, arrows, frames, label text and derived outputs across panels.
6. Use three or four fill hues by default; five are fine when each maps to a named entity; six or more with no semantic role reads as busy.
7. Emphasize the contribution with one accent used nowhere else: a distinct fill or color on a muted or gray scaffold, a thicker outline, or size; never emphasize several modules at once.
8. Mark frozen and trained modules with a snowflake or lock and a flame in the module corner when the method freezes parts.
9. Default to thin dark connectors; reserve block arrows for one or two major hand-offs and give each connector style a single meaning.
10. Label an edge only when what flows is not obvious; when arrows are colored by type, color their labels to match instead of adding a legend.
11. Keep container nesting at two levels (panel, card, chip); three nested bordered or dashed levels are a strong warning sign.
12. Set module names in regular or medium weight and reserve bold for titles.
13. Crop tightly, keep balanced gutters of 8 to 12 px, and leave no blank band taller than a card.
14. Prefer no legend; if one is needed, use three or four entries in a corner.
15. For comparisons (baseline versus ours, training versus deployment) mirror the geometry and change only the differing element.
16. When the figure has physical inputs or outputs, anchor at least one pipeline endpoint with a real render, photo or point cloud; architecture figures may be imagery-free when they use tokens, shapes or glyphs.
17. Name stages with one consistent device across the figure: titles above columns, a bracket ruler under them, or titles inside tinted containers.
18. Show a block's internals with a marked source box and zoom lines to a detail panel in the same tint.
19. Attach symbols to named modules and signals; equations belong on the canvas when they carry the idea.
20. Rotated labels in narrow bars and thin monospace text below 6 pt are soft warnings, not independent failures.

Additional patterns the reviewers found in strong figures:

- One concrete running example threaded through every stage (2211.09800 InstructPix2Pix, 2310.15008, 2308.10848, 2303.12077).
- A full-width backbone bar with per-item chips hanging above and below for layered architectures (2304.08485 LLaVA, 2306.10007).
- Horizontal tinted bands per layer with the band name in the margin or corner (2303.01497, 2503.03045, 2502.20391).
- Hierarchy rates and time scales for robot control stacks, such as Hz labels and low-frequency versus high-frequency brackets (2402.10329, 2505.10547, 2401.17583).
- A gray scaffold with a single accent color for the new part (2303.04137 Diffusion Policy, 2302.05543).
- Shape encodes role consistently: trapezoids for encoders, hourglasses for U-Nets, cylinders for datasets, stacked cards for libraries and batches.
- Faded elements for unselected or rejected options, and check or cross badges for outcomes (2310.06694, 2312.17655, 2309.17453).
- Circled step numbers on arrows or stage headers, and section references in titles, to tie the figure to the text.
- Solid forward paths versus dashed or colored training or gradient paths with a two-entry key (2302.11434, 2305.16213, 2210.09276).

## 6. Anti-patterns

- Paragraph-length example content at 4 to 5 pt dominating the canvas (2303.17760, 2303.17580, 2503.08508).
- Whole-figure small print from an ultra-wide strip or a text-width canvas placed in one column (2406.16793 at 2.3 pt, 2508.12166, 2502.17894).
- Uncropped canvases with large blank bands, and, at the other extreme, tight packing without gutters.
- Three levels of nested bordered or dashed containers with overlapping outlines (2506.14317, 2506.02353, 2509.12379).
- Six or more arbitrary hues, thick saturated borders, and white text on saturated fills.
- Bold on every module name; sentences and sentence-length stage titles as labels.
- Heavy block arrows mixed with thin arrows without a rule, drop shadows, bevels and gradient box fills.
- Legends of six to nine entries instead of labeling in place.
- Repeated decorative logos, mascots and WordArt titles.
- Long connectors that cross whole panels or fan over labels.
- Low-contrast labels (light gray thin text, white text on light fills) and red/green-only status coding.
- Transparent SVG backgrounds that render black, and blurry low-resolution exports.

## 7. Exemplars worth imitating

| arXiv | Venue | Why |
|---|---|---|
| 2305.14314 QLoRA | NeurIPS 2023 | shared row labels so box size encodes memory; flow-colored arrows with a three-entry legend; 34 words at 8 pt |
| 2305.18290 DPO | NeurIPS 2023 | mirrored borderless panels where the removed RL loop is the only visible difference |
| 2402.15391 Genie | ICML 2024 | three saturated modules, output tokens colored like their emitter, 7 words |
| 2304.08485 LLaVA | NeurIPS 2023 | borderless pastel bands named with symbols, modality-shaded tokens, a full-width LLM band |
| 2412.09573 | ICCV 2025 | column titles above, no containers, one hue per input view carried from image border to output frame |
| 2304.02643 SAM | ICCV 2023 | box size encodes compute; a wide strip that works with 17 words at 7 pt |
| 2303.12077 | ICCV 2023 | stage names in a bracket ruler under the canvas; query token colors match their transformer boxes |
| 2210.03094 VIMA | ICML 2023 | robotics architecture with 35 words, token squares, a frozen encoder marked with a snowflake |
| 2307.00117 | CoRL 2023 | train and deploy panels with one pastel per encoder role; the contrastive loss drawn as a similarity grid |
| 2502.04307 | RSS 2025 | train versus inference with a mirrored controller box and one orange arrow carrying the idea |
| 2505.03738 AMO | RSS 2025 | system figure with a bracket timeline of stages, borderless tinted cards, trapezoid networks with snowflakes |
| 2302.12766 | RSS 2023 | pretraining versus adaptation split by a thin rule, modality mix drawn inside the module bar |
| 2211.09800 InstructPix2Pix | CVPR 2023 | one running example through every stage; only models are boxes, data is quoted text and real images |
| 2405.04517 xLSTM | NeurIPS 2024 | an imagery-free ML figure with a grayscale structure and pastel highlights keyed to gate colors |
| 2504.21767 | IROS 2024 | robotics control stack with blue command and orange feedback arrows and single-symbol edge labels |
| 2308.07931 F3RM | CoRL 2023 | numbered serif captions under columns, no boxes, the same scene carried across stages |

Open them on arXiv (the HTML version shows each figure) and compare a draft against them at the same printed width.

## 8. Earlier hand measurements (sanity check)

Before the OCR study, a handful of text-width figures were measured by hand from cap heights: LOTUS (ICRA 2024) module labels 6.1 pt and titles 8.8 pt, Octo (RSS 2024) labels 7.3 to 7.8 pt, DROC (RSS 2024) module names 8.6 pt, LLM3 (IROS 2024) module names 11 pt and example text 7.8 pt, BUMBLE (ICRA 2025) group titles 8.1 pt.
They agree with the OCR medians above.

## 9. Checklist before delivering a paper figure

1. The canvas maps to its real print width (1400 px for text width, 700 px for one column), and the QA gate passes with no failures.
2. The figure median prints at 6.5 pt or more, labels are names of at most six words, and the label word count is near 40 for a text-width figure.
3. Example content is short, and every explanation removed from the canvas appears in the caption draft.
4. Real renders or photos anchor the physical endpoints wherever the project has them; otherwise the user has been asked for one.
5. One accent marks the contribution, hues map to entities, nesting stays at two levels, and any legend has at most four entries.
6. The draft has been compared side by side with two or three exemplars from section 7 at the same printed width.
