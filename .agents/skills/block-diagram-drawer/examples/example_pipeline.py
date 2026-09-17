"""Illustrative paper-style SVG figure: a placeholder multi-view policy method.

The method, module names and sketches are invented to demonstrate the figkit
visual language at print size: a 1400 px text-width canvas, labels from `Fig.fs`,
names instead of sentences, symbols next to module names, a trapezoid encoder,
token pills, bracketed vectors, a key-module outline, braces, loss connectors,
schematic sketches marked as such, and a vendored Tabler outline icon.
It is not a real paper figure and shows no results. Run from any directory:

    python example_pipeline.py
    python ../scripts/qa_svg_figure.py example_pipeline.svg --png
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

from figkit import HAIR, INK, MUTED, PAL, WIRE, Fig

OUT = HERE / "example_pipeline.svg"
B, P, R, G, O, Y = (PAL[k] for k in ("blue", "purple", "red", "green", "orange", "gray"))

f = Fig(1400, 500)
LABEL, MODULE, SMALL = f.fs("label"), f.fs("module"), f.fs("min")


def name(x, y, s, color=INK, box=None, anchor="start"):
    f.text(x, y, s, size=MODULE, weight=500, color=color, box=box, anchor=anchor)


def schematic(x, y, box):
    f.text(x, y, "schematic", size=SMALL, color=MUTED, anchor="middle", box=box, family="serif", italic=True)


# ---------------------------------------------------------------- (a) inputs
top = f.panel(8, 8, 232, 484, "gray", "(a) Inputs", dashed=True)
for k, (label, sym) in enumerate((("view 1", "$x^{(1)}$"), ("view 2", "$x^{(2)}$"))):
    y = top + 6 + 136 * k
    c = f.card(18, y, 212, 128, fill="#FFFFFF", stroke=HAIR)
    name(30, y + 30, label, box=c)
    f.asset(HERE / "assets" / "camera.svg", 106, y + 13, 20, color=MUTED)
    f.text(218, y + 30, sym, size=MODULE, anchor="end", box=c)
    f.scene(30, y + 44, 96, 72)
    f.chip(138, y + 64, 80, 32, "RGB", "gray", size=SMALL, fill="#FFFFFF", family="mono")
c = f.card(18, top + 278, 212, 136, fill="#FFFFFF", stroke=HAIR)
name(30, top + 308, "state", box=c)
f.text(218, top + 308, "$s_t$", size=MODULE, anchor="end", box=c)
f.bars(30, top + 322, 188, 58, [0.6, 0.35, 0.8, 0.5, 0.3, 0.7, 0.45, 0.62, 0.4, 0.74], O.accent)
schematic(124, top + 402, c)
f.brace(244, 60, 476, color="#A8A39A", depth=12)

# ---------------------------------------------------------------- (b) shared encoder
top = f.panel(266, 8, 250, 484, "blue", "(b) Shared encoder")
f.arrow("M258 268H276", WIRE)
c = f.card(278, top + 6, 226, 408, "blue", stack=1)
f.trapezoid(311, top + 26, 160, 76, "blue", "$E_\\theta$", size=34)
for k, (role, sym) in enumerate((("blue", "$z^{(1)}$"), ("purple", "$z^{(2)}$"), ("orange", "$z^{s}$"))):
    f.chip(292 + 68 * k, top + 124, 62, 38, sym, role, size=LABEL, fill="#FFFFFF", stroke=PAL[role].accent, color=INK)
f.add(f'<rect x="292" y="{top + 180}" width="198" height="176" rx="3" fill="#FFFFFF" stroke="#C6DDE4" stroke-width="0.8"/>')
for k, (role, cx, cy) in enumerate((("blue", 346, top + 238), ("purple", 440, top + 226), ("orange", 392, top + 306))):
    for j in range(10):
        ang = j * 2.4 + k
        rad = 0.4 + 0.07 * j
        f.dot(cx + 22 * math.cos(ang) * rad, cy + 18 * math.sin(ang) * rad, PAL[role].accent, 3.2)
f.text(391, top + 390, "latent space", size=LABEL, color=MUTED, anchor="middle", box=c, family="serif", italic=True)

# ---------------------------------------------------------------- (c) proposed fusion
top = f.panel(542, 8, 438, 484, "red", "(c) Fusion")
f.arrow("M506 268H552", WIRE)
c = f.card(552, top + 6, 232, 408, "red", key=True)
name(566, top + 36, "Cross-view attention", color=R.deep, box=c)
for k, sym in enumerate(("$Q$", "$K$", "$V$")):
    f.chip(570 + 68 * k, top + 56, 58, 36, sym, "red", size=MODULE, fill="#FFFFFF", stroke=R.accent, color=INK)
for i in range(8):
    for j in range(8):
        v = 0.12 + 0.88 * math.exp(-((i - j) ** 2) / 3.0) * (0.6 + 0.4 * math.cos(i * 0.7 + j * 0.3))
        f.add(f'<rect x="{588 + 20 * j}" y="{top + 106 + 20 * i}" width="19" height="19" fill="{R.accent}" opacity="{v:.2f}"/>')
schematic(668, top + 290, c)
f.text(668, top + 330, "$A=\\mathrm{softmax}(QK^{\\top}/\\sqrt{d})$", size=LABEL, anchor="middle", box=c)
f.chip(572, top + 354, 192, 42, "$h=\\mathrm{Attn}(Q,K,V)$", "red", size=LABEL, fill="#FFFFFF", stroke=R.accent, color=INK)
f.arrow(f"M785 {top + 210}H795", WIRE)

c = f.card(796, top + 6, 174, 408, "red")
name(810, top + 36, "Adaptive gate", color=R.deep, box=c)
f.text(883, top + 84, "$g=\\sigma(W[h,z])$", size=MODULE, anchor="middle", box=c)
f.add(f'<rect x="808" y="{top + 102}" width="150" height="112" rx="3" fill="#FFFFFF" stroke="#EBC9BE" stroke-width="0.8"/>')
f.curves(814, top + 110, 138, 96, [R.accent, O.accent], seed=0.6, grid=False)
f.bars(812, top + 234, 142, 64, [0.8, 0.45, 0.62, 0.3, 0.7], R.accent, gap=8)
schematic(883, top + 322, c)
f.chip(812, top + 354, 142, 42, "$\\tilde{z}=g\\odot h$", "red", size=LABEL, fill="#FFFFFF", stroke=R.accent, color=INK)

# ---------------------------------------------------------------- (d) heads and objective
top = f.panel(1006, 8, 386, 484, "gray", "(d) Heads")
f.arrow(f"M971 {top + 120}H1016", WIRE)
f.arrow(f"M971 {top + 330}H1016", WIRE)

c = f.card(1016, top + 6, 196, 198, "green")
name(1028, top + 36, "Policy head", color=G.deep, box=c)
f.text(1200, top + 36, "$\\pi_\\phi$", size=MODULE, anchor="end", box=c)
f.tokens(1030, top + 56, 7, "green", w=20, h=12, gap=4.5)
f.bracket(1026, top + 82, 176, 84, WIRE, tick=5)
f.curves(1034, top + 88, 160, 72, [G.accent, B.accent], seed=1.9, grid=False)
f.text(1114, top + 192, "$\\hat{a}_{t:t+H}$", size=LABEL, anchor="middle", box=c)

c = f.card(1016, top + 216, 196, 198, "purple", stack=1)
name(1028, top + 246, "World model", color=P.deep, box=c)
f.text(1200, top + 246, "$F_\\psi$", size=MODULE, anchor="end", box=c)
f.chip(1028, top + 264, 56, 38, "$z_t$", "purple", size=LABEL, fill="#FFFFFF", stroke=P.accent, color=INK)
f.arrow(f"M1085 {top + 283}H1119", WIRE, 1.3, head=7)
f.chip(1120, top + 264, 80, 38, "$\\hat{z}_{t+1}$", "purple", size=LABEL, fill="#FFFFFF", stroke=P.accent, color=INK)
f.arrow(f"M1160 {top + 303}V{top + 355}", R.accent, 1.3, start=True, head=7)
f.text(1150, top + 336, "MSE", size=SMALL, color=R.deep, anchor="end", family="mono")
f.chip(1120, top + 356, 80, 38, "$z_{t+1}$", "gray", size=LABEL, fill="#FFFFFF", color=INK)

c = f.card(1224, top + 6, 158, 408, fill="#FFFFFF", stroke=HAIR)
name(1236, top + 36, "Objective", box=c)
f.text(1303, top + 92, "$\\mathcal{L}$", size=42, anchor="middle", box=c)
for k, (role, sym) in enumerate((("green", "$\\mathcal{L}_{\\mathrm{BC}}$"), ("purple", "$\\lambda\\mathcal{L}_{\\mathrm{pred}}$"),
                                 ("red", "$\\mathcal{R}(z)$"))):
    f.chip(1238, top + 118 + 48 * k, 130, 38, sym, role, size=LABEL, fill="#FFFFFF", stroke=PAL[role].accent, color=INK)
f.line(f"M1244 {top + 276}V{top + 372}H1368", "#9C968A", 0.9)
pts = " L".join(f"{1246 + 120 * t / 60:.1f} {top + 368 - 84 * math.exp(-4 * t / 60) - 3 * math.sin(t):.1f}" for t in range(61))
f.add(f'<path d="M{pts}" fill="none" stroke="{INK}" stroke-width="1.4"/>')
schematic(1303, top + 400, c)
f.arrow(f"M1213 {top + 120}H1223", G.accent, 1.3, head=7)
f.arrow(f"M1213 {top + 330}H1223", P.accent, 1.3, head=7)

f.save(str(OUT))
print(OUT)
