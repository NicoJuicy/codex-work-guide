# Block Diagram Drawer

Block Diagram Drawer turns a description, sketch, README, ASCII diagram, or reference image into a block diagram that reads like a robotics or AI paper figure.
Figures are small Python build scripts that output SVG and a 2x PNG, sized and styled after measured ICRA, IROS, RSS and CoRL method figures, and checked by a headless-Chrome QA gate.

Block Diagram Drawer 把文字描述、草图、README、ASCII 图或参考图画成像机器人和 AI 论文插图的框图。
每张图是一个 Python 构建脚本，输出 SVG 和 2x PNG；字号和风格来自对 ICRA、IROS、RSS、CoRL 方法图的实测，并用无头 Chrome 做质量检查。

## Quick start / 快速开始

```bash
python <skill-dir>/scripts/scaffold.py figures/src/fig_pipeline.py --panels 4
cd figures/src
python fig_pipeline.py
python qa_svg_figure.py ../pipeline-figure.svg --png
```

The QA gate fails on text overflow, text collisions, overlapping boxes, lines crossing labels, labels that print below 6 pt, labels longer than six words outside example content, more label words than the canvas budget, or content coverage below 0.40.
Set `CHROME_PATH` if Chrome, Chromium, or Edge is not found.

QA 脚本在以下情况判为不通过：文字溢出、文字重叠、方框重叠、连线穿过文字、印刷后小于 6 pt 的文字、示例内容以外超过六个词的标签、标签总词数超过画布预算，或内容覆盖率低于 0.40。
找不到浏览器时设置 `CHROME_PATH`。

## What it enforces / 规范要点

- Exact content: every label and number comes from the source; non-data sketches are marked schematic.
- Print size: a 1400 px canvas prints at text width and `f.fs()` gives labels 6 to 9 pt; labels are names, and explanations go in the caption draft delivered with the figure.
- Real imagery: `f.image()` embeds renders and photos; verbatim prompts and code go in `f.example()` cards.
- Paper layout: stage columns or titled group containers, 8 px margins, shared column grid, no title inside the canvas.
- Muted flat palette with one color role per concept and a single outlined key module.
- Typography hierarchy: bold panel titles, medium module names, serif italic data labels, monospace tokens, typeset math.
- Shapes with meaning: token pills, trapezoid encoders, bracketed vectors, cylinders, speech bubbles, circled steps.
- Open-source icons: `scripts/svgicons.py` vendors MIT Tabler outline icons and LobeHub model logos, with license files and a source ledger.
- Editable export: `scripts/svg2drawio.py` turns a finished figure into a `.drawio` file with native shapes, text and edges.

- 内容准确：所有标签和数字来自原始材料，非真实数据的小图标注为示意。
- 印刷尺寸：1400 px 画布对应论文通栏宽度，`f.fs()` 给出印刷后 6 到 9 pt 的字号；标签只写名称，解释性文字放进随图交付的图注草稿。
- 真实图像：`f.image()` 嵌入渲染图和照片；原样的提示词和代码放进 `f.example()` 卡片。
- 论文式布局：按阶段分列，或用带标题的分组容器，8 px 边距、统一列网格，标题放在图注而不是画布里。
- 低饱和平涂配色，一种颜色对应一个概念，只给最关键的模块加深色描边。
- 字体层级：面板标题加粗、模块名中等字重、数据名用衬线斜体、token 用等宽字体、公式正确排版。
- 图形有含义：token 胶囊、梯形编码器、方括号向量、圆柱存储、对话气泡、圆圈步骤编号。
- 开源图标：`scripts/svgicons.py` 按需下载 MIT 许可的 Tabler outline 图标和 LobeHub 模型 logo，并附带许可证和来源记录。
- 可编辑导出：`scripts/svg2drawio.py` 把画好的图转成 `.drawio` 文件，矩形、文字和连线都是 draw.io 原生对象。

See `SKILL.md` for the workflow, `references/paper-figure-study.md` for the measured paper figures, and `references/visual-contract.md` for the full contract.

工作流见 `SKILL.md`，论文插图实测结论见 `references/paper-figure-study.md`，完整规范见 `references/visual-contract.md`。
