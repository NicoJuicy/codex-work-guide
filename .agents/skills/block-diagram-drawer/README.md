# Block Diagram Drawer

Block Diagram Drawer turns a description, sketch, ASCII diagram, or reference image into a dense, publication-quality block diagram.
Figures are small Python build scripts that output SVG and a 2x PNG, styled after CoRL, RSS, and ICRA method figures and checked by a headless-Chrome QA gate.

Block Diagram Drawer 把文字描述、草图、ASCII 图或参考图画成信息密集、接近论文质量的框图。
每张图是一个 Python 构建脚本，输出 SVG 和 2x PNG；视觉风格参考 CoRL、RSS、ICRA 的方法图，并用无头 Chrome 做质量检查。

## Quick start / 快速开始

```bash
python <skill-dir>/scripts/scaffold.py figures/src/fig_pipeline.py --panels 4
cd figures/src
python fig_pipeline.py
python qa_svg_figure.py ../pipeline-figure.svg --png
```

The QA gate fails on text overflow, text collisions, overlapping boxes, lines crossing labels, labels smaller than 11 px, or content coverage below 0.55.
Set `CHROME_PATH` if Chrome, Chromium, or Edge is not found.

QA 脚本在出现文字溢出、文字重叠、方框重叠、连线穿过文字、文字小于 11 px，或内容覆盖率低于 0.55 时判为不通过。
找不到浏览器时设置 `CHROME_PATH`。

## What it enforces / 规范要点

- Exact content: every label and number comes from the source; non-data sketches are marked schematic.
- Dense layout: 8 px margins, shared column grid, no title inside the canvas.
- Muted flat palette with one color role per concept and a single outlined key module.
- Typography hierarchy: bold panel titles, medium module names, serif italic data labels, monospace tokens, typeset math.
- Shapes with meaning: token pills, trapezoid encoders, bracketed vectors, cylinders, speech bubbles, circled steps.
- Open-source icons: `scripts/svgicons.py` vendors MIT Tabler outline icons and LobeHub model logos, with license files and a source ledger.

- 内容准确：所有标签和数字来自原始材料，非真实数据的小图标注为示意。
- 排版紧凑：8 px 边距、统一列网格，标题放在图注而不是画布里。
- 低饱和平涂配色，一种颜色对应一个概念，只给最关键的模块加深色描边。
- 字体层级：面板标题加粗、模块名中等字重、数据名用衬线斜体、token 用等宽字体、公式正确排版。
- 图形有含义：token 胶囊、梯形编码器、方括号向量、圆柱存储、对话气泡、圆圈步骤编号。
- 开源图标：`scripts/svgicons.py` 按需下载 MIT 许可的 Tabler outline 图标和 LobeHub 模型 logo，并附带许可证和来源记录。

See `SKILL.md` for the workflow and `references/visual-contract.md` for the full contract.

工作流见 `SKILL.md`，完整规范见 `references/visual-contract.md`。
