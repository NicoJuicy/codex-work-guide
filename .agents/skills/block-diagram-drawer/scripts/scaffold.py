"""Start a new block-diagram build script next to vendored copies of the kit.

Vendoring figkit.py and qa_svg_figure.py beside the figure scripts keeps every
figure reproducible even after the skill itself changes.

Usage:
    python scaffold.py <project>/figures/src/fig_pipeline.py [--width 1400] [--height 500] [--panels 4]
                       [--force] [--update-kit]

The build script writes <project>/figures/pipeline-figure.svg (the "fig_" prefix
is dropped). Then run:
    python fig_pipeline.py
    python qa_svg_figure.py ../pipeline-figure.svg --png
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

KIT = ("figkit.py", "qa_svg_figure.py")
HERE = Path(__file__).resolve().parent

TEMPLATE = '''"""Figure: {title}."""

from pathlib import Path

from figkit import FAINT, HAIR, INK, MUTED, PAL, WIRE, Fig

OUT = Path(__file__).resolve().parent.parent / "{output}"

# 1400 px prints at text width (figure*), 700 px at one column; f.fs() gives print-size fonts in px.
f = Fig({width}, {height})
B, P, R, G, A, O, Y = (PAL[k] for k in ("blue", "purple", "red", "green", "amber", "orange", "gray"))
LABEL, MODULE = f.fs("label"), f.fs("module")

# Column grid from the kit: 8 px outer margin, 8 px gutters, exact and equal by construction.
# Keep every x and w in COLS instead of typing coordinates, and anchor arrows with f.connect.
COLS = f.cols(8, {right}, {panels_n}, gap=8)
CARDS = []

# Labels are names (at most six words); explanations go in the caption, prompts and code in f.example().
{panels}

for a, b in zip(CARDS, CARDS[1:]):  # anchored flow: both ends land exactly on a card edge
    f.connect(a, b, color=WIRE, sw=1.4)

f.save(str(OUT))
print(OUT)
'''

PANEL = '''# ---------------------------------------------------------------- ({label}) stage {n}
x, w = COLS[{i}]
top = f.panel(x, 8, w, {h}, "{role}", "({label}) Stage {n}")
c = f.card(x + 10, top + 4, w - 20, {bottom} - top - 4, "{role}")
CARDS.append(c)
f.text(x + 22, top + 34, "Module", size=MODULE, weight=500, box=c)
f.text(x + 22, top + 64, "$x_t$ input", size=LABEL, color=MUTED, box=c, family="serif", italic=True)
'''

ROLES = ("gray", "blue", "amber", "green", "purple", "red", "orange")


def panel_code(width: int, height: int, count: int) -> str:
    blocks = []
    for i in range(count):
        blocks.append(PANEL.format(
            label=chr(ord("a") + i), n=i + 1, i=i, h=height - 16, role=ROLES[i % len(ROLES)], bottom=height - 18,
        ))
    return "\n".join(blocks)


def scaffold(target: Path, width: int, height: int, panels: int, force: bool, update_kit: bool) -> list[Path]:
    if target.suffix != ".py":
        raise SystemExit(f"target must be a .py build script, got {target}")
    if not 1 <= panels <= 8:
        raise SystemExit("--panels must be between 1 and 8")
    target.parent.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name in KIT:
        dest = target.parent / name
        if update_kit or not dest.exists():
            shutil.copy2(HERE / name, dest)
            written.append(dest)
    if target.exists() and not force:
        raise SystemExit(f"{target} already exists; pass --force to overwrite it")
    stem = target.stem.removeprefix("fig_")
    output = f"{stem}-figure.svg"
    target.write_text(TEMPLATE.format(
        title=stem.replace("_", " "), output=output, width=width, height=height, right=width - 8, panels_n=panels,
        panels=panel_code(width, height, panels),
    ), encoding="utf-8")
    written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start a block-diagram build script with a vendored kit.")
    parser.add_argument("target", type=Path)
    parser.add_argument("--width", type=int, default=1400)
    parser.add_argument("--height", type=int, default=500)
    parser.add_argument("--panels", type=int, default=4)
    parser.add_argument("--force", action="store_true", help="overwrite an existing build script")
    parser.add_argument("--update-kit", action="store_true", help="refresh vendored figkit.py and qa_svg_figure.py")
    args = parser.parse_args(argv)
    for path in scaffold(args.target, args.width, args.height, args.panels, args.force, args.update_kit):
        print(f"wrote {path}")
    print(f"next: python {args.target.name}  then  python qa_svg_figure.py ../{args.target.stem.removeprefix('fig_')}-figure.svg --png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
