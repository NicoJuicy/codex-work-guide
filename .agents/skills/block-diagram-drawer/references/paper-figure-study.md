# Paper Figure Study: Robotics and AI Method Figures

This note records what published robotics and AI method figures actually look like, so figures drawn with this skill are judged against real papers rather than against earlier drafts.
Read it before a restyle, before a first figure for a paper, and whenever a user says a figure "does not look like a paper figure".

## 1. Corpus

About forty system, method and architecture figures were inspected on arXiv HTML pages in September 2026, weighted toward ICRA, IROS and RSS.

| Venue | Papers (figure studied) |
|---|---|
| ICRA | Kimera 2020 (architecture), NLMap 2023, VLMaps 2023 (system overview), Code as Policies 2023, ProgPrompt 2023 (prompt and execution), ConceptGraphs 2024 (pipeline), LOTUS 2024 (method), RoCo 2024 (method), AutoTAMP 2024, LLM-Grounder 2024, RoboAgent 2024, BUMBLE 2025 (architecture) |
| IROS | TidyBot 2023 (system overview), Matcha / Chat with the Environment 2023 (overview), SMART-LLM 2024 (system overview), LLM3 2024 (framework) |
| RSS | Hydra 2022 (scene graph), Octo 2024 (architecture), DROC 2024 (overview), MOKA 2024 (method), HOV-SG 2024 (overview) |
| RA-L, CoRL | LEAGUE (RA-L 2023, overview), VoxPoser (CoRL 2023, method), ReKep (CoRL 2024, method) |
| Other robotics and agent papers | Voyager (framework and skill library), DEPS, JARVIS-1, Text2Motion, ISR-LLM, NOD-TAMP, COME-robot, RoboMatrix, RoboOS, Hi Robot, GR00T N1, pi0 |

## 2. Measured print sizes

Label sizes were measured on the arXiv images of full-width figures (`figure*`, printed at the text width of about 504 to 516 pt), by cap height in image pixels converted to printed points.

| Figure | Element | Printed size |
|---|---|---|
| LOTUS (ICRA 2024) | panel title "Continual Skill Discovery" | 8.8 pt |
| LOTUS | module label "Hierarchical Clustering with DINOv2" | 6.1 pt |
| LOTUS | small caption under an image | 5.9 pt |
| Octo (RSS 2024) | module labels "Language Encoder", "Action Head" | 7.3 to 7.8 pt |
| DROC (RSS 2024) | bold serif module "Knowledge Retriever" | 8.6 pt |
| DROC | stage label "Task Planner" | 7.0 pt |
| LLM3 (IROS 2024) | bold serif module "Motion Planner" | 11 pt |
| LLM3 | example text inside a state card | 7.8 pt |
| BUMBLE (ICRA 2025) | group title "Skill Library" | 8.1 pt |

Conclusions:

- Ordinary labels print at 6 to 8 pt, module names at 7 to 11 pt, panel titles at 9 to 12 pt, and nothing important goes below about 6 pt.
- A 1400 px canvas that fills the text width is about 2.7 px per printed point, so those sizes are about 16 px minimum, 18 px labels, 21 px module names and 24 px titles.
- A 700 px canvas that fills one column has almost the same px per point, so the same pixel sizes apply.
- Drafts that used 11 to 13 px labels on a 1400 px canvas printed at 4 to 5 pt, which is why they read as dense documentation instead of paper figures.

## 3. Recurring patterns

### 3.1 Text

- Labels are names, not sentences: one to four words, often paired with a symbol such as $\mathcal{R}$, $\pi^{L}_{k}$, $s_0$ or $a_t$.
- A text-width figure carries roughly 30 to 80 label words; LOTUS has about 60, Octo about 35.
- Full sentences appear only as example content: a user instruction, a prompt, generated code, a reasoning trace or a feedback message, set in a speech bubble, code card or trace card.
- Explanations, definitions and cardinalities live in the caption, not in annotation text beside the diagram.
- Legends, when present, have two to four entries (GR00T N1: "Embodiment-Specific Module", "Pre-trained and Frozen"; LOTUS: fine-tune, frozen, new).

### 3.2 Imagery

- Almost every robotics figure shows real data: camera frames, simulator renders, point clouds, meshes, value maps or real robot photos.
- Software frameworks without imagery (ISR-LLM, RoboMatrix, RoboOS, Hi Robot) still keep labels short and use a few pictograms or product logos.
- Hand-drawn cartoon scenes are rare; a real render from the project is always preferred.

### 3.3 Layout

- The dominant layout is a left-to-right sequence of two to five stages, each a column with a short title above it or inside a light container.
- Hierarchies are shown as stacked containers with the title inside the container (Kimera dotted groups, RoboMatrix "Modular Scheduling Layer" / "Skill Layer" / "Hardware Layer", LLM3 tinted panels), never as full-width bands with a separate header column and a notes column.
- Two-part figures use panel labels such as "(a) Reasoning and Planning with LLM", placed top-left or centered under the panel, and are often separated by a thin vertical rule (LOTUS, JARVIS-1).
- Full-width figures are wide: aspect ratios between about 2:1 and 4:1 (LLM3 2.1, Octo 2.1, BUMBLE 2.3, ConceptGraphs 2.4, NOD-TAMP 2.8, LOTUS 3.0, VoxPoser 3.5).

### 3.4 Color, shape and lines

- Two to four pastel fills, one per module type, usually borderless or with a slightly darker stroke; white or very light gray for neutral content.
- The key module is marked by a stronger fill (Hi Robot yellow, VoxPoser tinted model blocks) rather than a black outline on many boxes.
- Connectors are thin dark gray lines with small heads, plus thick light block arrows between major stages (ConceptGraphs, RoCo, LEAGUE).
- Colored connectors appear when color encodes a data type or outcome, and then the label next to the line takes the same color (Kimera, Voyager).
- Dashed containers mark optional, future or grouped parts.

### 3.5 Typography

- Sans (Helvetica, Arial, Inter) dominates AI and CoRL-style figures.
- Many IEEE figures set everything in a Times-like serif that matches the paper body (Kimera, LLM3, DROC), with bold serif module names.
- Monospace is reserved for code, prompts, tokens and identifiers, except in figures that use a monospace house style throughout (Hi Robot, pi0).
- Math symbols are italic serif and sit next to or under the module name.

## 4. Why earlier drafts did not look like paper figures

| Draft habit | What papers do instead |
|---|---|
| 11 to 13 px labels on a 1400 px canvas (4 to 5 pt in print) | 16 to 24 px (6 to 9 pt), fewer words |
| Full-width tinted bands with a header column of questions and a notes column | Stage columns or titled group containers, explanations in the caption |
| A legend strip explaining every relation in words | Labels on the edges themselves, legend of at most four entries |
| Sentences such as "every navigate node uses navigate.all" inside the canvas | Caption text |
| Cartoon kitchen drawn from icons | Real render or photo, or no scene at all |
| Black key outlines along a whole example path | One key module with a stronger fill |
| 1400 by 880 canvas (aspect 1.6) for a method overview | Aspect 2 to 3.5 for full width |
| Coverage pushed up with more cards and notes | Fill from imagery and larger type, with honest white space |

## 5. Checklist before delivering a paper figure

1. The canvas maps to a real print width (1400 px for text width, 700 px for one column) and the QA gate passes at the default 6 pt minimum.
2. No label outside example content has more than six words, and the figure stays within the word budget reported by the gate.
3. Every explanation that was removed from the canvas appears in the caption draft delivered with the figure.
4. Real renders or photos replace schematic scenes wherever the project has them; otherwise the scene is omitted or clearly marked as a placeholder and the user is asked for a render.
5. At most one key module is emphasized, at most four legend entries exist, and edges are labeled where they are drawn.
