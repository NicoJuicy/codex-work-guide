"""Illustrative dense SVG figure: a placeholder multi-view policy method.

The method, module names and sketches are invented to demonstrate the figkit
visual language (flat muted roles, bold-only-for-titles typography, serif italic
data names, monospace tokens, trapezoid encoder, token pills, bracketed vectors,
circled steps, key-module outline, brace, fork/merge and loss connectors).
It is not a real paper figure and shows no results. Run from any directory:

    python example_pipeline.py
    python ../../scripts/qa_svg_figure.py example_pipeline.svg --png
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))

from figkit import FAINT, HAIR, INK, MUTED, PAL, WIRE, Fig

OUT = HERE / "example_pipeline.svg"
B, P, R, G, A, O, Y = (PAL[k] for k in ("blue", "purple", "red", "green", "amber", "orange", "gray"))
STONE = "#9C968A"

f = Fig(1400, 380)

# ---------------------------------------------------------------- (a) inputs
f.panel(8, 8, 196, 364, "gray", "(a) Inputs", sub="multi-view observation", dashed=True, sub_below=True)
for k, (name, sym, tag) in enumerate((("view 1", "$x^{(1)}$", "front cam"), ("view 2", "$x^{(2)}$", "side cam"))):
    y = 58 + 104 * k
    c = f.card(18, y, 176, 96, fill="#FFFFFF", stroke=HAIR)
    f.text(28, y + 19, name, size=12, weight=500, box=c)
    f.text(184, y + 19, sym, size=14, anchor="end", box=c)
    f.scene(28, y + 27, 84, 60)
    f.chip(120, y + 31, 64, 20, "RGB", "gray", size=10.5, fill="#FFFFFF", family="mono")
    f.chip(120, y + 57, 64, 20, tag, "gray", size=10.5, fill="#FFFFFF", color=MUTED, family="serif", italic=True)
c = f.card(18, 266, 176, 96, fill="#FFFFFF", stroke=HAIR)
f.text(28, 285, "state", size=12, weight=500, box=c)
f.text(184, 285, "$s_t$", size=14, anchor="end", box=c)
f.bars(28, 294, 156, 38, [0.6, 0.35, 0.8, 0.5, 0.3, 0.7, 0.45, 0.62, 0.4, 0.74, 0.5, 0.33], O.accent)
f.text(106, 352, "proprioception", size=10.5, color=MUTED, anchor="middle", box=c, family="serif", italic=True)
f.brace(206, 24, 356, color="#A8A39A", depth=12)
f.arrow("M220 190H250", "#A8A39A", 1.2)

# ---------------------------------------------------------------- (b) shared encoder
f.panel(240, 8, 196, 364, "blue", "(b) Shared encoder", sub="one latent space", sub_below=True)
c = f.card(252, 62, 172, 298, "blue", stack=1)
f.text(262, 81, "Encoder", size=12, weight=500, color=B.deep, box=c)
f.trapezoid(278, 94, 120, 46, "blue", "$E_\\theta$", size=20)
f.text(338, 158, "weights shared across views", size=10.5, color=MUTED, anchor="middle", box=c, family="serif", italic=True)
for k, (role, sym) in enumerate((("blue", "$z^{(1)}$"), ("purple", "$z^{(2)}$"), ("orange", "$z^{s}$"))):
    f.chip(266 + 50 * k, 170, 44, 24, sym, role, size=13, fill="#FFFFFF", stroke=PAL[role].accent, color=INK)
f.add('<rect x="266" y="204" width="144" height="92" rx="3" fill="#FFFFFF" stroke="#C6DDE4" stroke-width="0.8"/>')
for k, (role, cx, cy) in enumerate((("blue", 300, 236), ("purple", 366, 228), ("orange", 334, 270))):
    for j in range(9):
        ang = j * 2.4 + k
        f.dot(cx + 14 * math.cos(ang) * (0.4 + 0.07 * j), cy + 11 * math.sin(ang) * (0.4 + 0.07 * j), PAL[role].accent, 2.2)
f.text(338, 318, "$z^{(v)}=E_\\theta(x^{(v)})\\in\\mathbb{R}^{d}$", size=12, anchor="middle", box=c)
f.text(338, 340, "indexed latent batch", size=10.5, color=MUTED, anchor="middle", box=c, family="serif", italic=True)

# ---------------------------------------------------------------- (c) proposed fusion
f.panel(444, 8, 424, 364, "red", "(c) Proposed fusion", sub="contribution · highlighted in red", sub_below=True)
f.arrow("M424 210H454", WIRE)
c = f.card(456, 62, 200, 298, "red", key=True)
f.step(470, 76, 1, color=R.deep)
f.text(484, 81, "Cross-view attention", size=12, weight=500, color=R.deep, box=c)
for k, sym in enumerate(("$Q$", "$K$", "$V$")):
    f.chip(478 + 54 * k, 94, 48, 22, sym, "red", size=13, fill="#FFFFFF", stroke=R.accent, color=INK)
for i in range(8):
    for j in range(8):
        v = 0.12 + 0.88 * math.exp(-((i - j) ** 2) / 3.0) * (0.6 + 0.4 * math.cos(i * 0.7 + j * 0.3))
        f.add(f'<rect x="{492 + 16 * j}" y="{126 + 16 * i}" width="15" height="15" fill="{R.accent}" opacity="{v:.2f}"/>')
f.text(556, 272, "attention map · schematic", size=10.5, color=FAINT, anchor="middle", box=c, family="serif", italic=True)
f.text(556, 298, "$A=\\mathrm{softmax}(QK^{\\top}/\\sqrt{d})$", size=12.5, anchor="middle", box=c)
f.chip(468, 318, 176, 28, "$h=\\mathrm{Attn}(Q,K,V)$", "red", size=12, fill="#FFFFFF", stroke=R.accent, color=INK)
f.arrow("M656 210H668", WIRE)

c = f.card(670, 62, 186, 298, "red")
f.step(684, 76, 2, color=R.deep)
f.text(698, 81, "Adaptive gate", size=12, weight=500, color=R.deep, box=c)
f.text(763, 116, "$g=\\sigma(W[h,z])$", size=16, anchor="middle", box=c)
f.add('<rect x="682" y="126" width="162" height="74" rx="3" fill="#FFFFFF" stroke="#EBC9BE" stroke-width="0.8"/>')
f.curves(688, 132, 150, 62, [R.accent, O.accent], seed=0.6, grid=False)
f.text(763, 218, "per-view gate weights", size=10.5, color=MUTED, anchor="middle", box=c, family="serif", italic=True)
f.bars(684, 226, 158, 36, [0.8, 0.45, 0.62, 0.3, 0.7, 0.52], R.accent, gap=8)
f.chip(682, 276, 162, 26, "$\\tilde{z}=g\\odot h+(1-g)\\odot z$", "red", size=11.5, fill="#FFFFFF", stroke=R.accent, color=INK)
f.chip(682, 310, 162, 24, "residual · layer norm", "gray", size=10.5, fill="#FFFFFF", family="mono")

# ---------------------------------------------------------------- (d) heads and objective
f.panel(876, 8, 516, 364, "gray", "(d) Heads & objective", sub="training · inference", sub_below=True)
f.arrow("M856 130H886", WIRE)
f.arrow("M856 285H886", WIRE)

c = f.card(888, 62, 240, 138, "green")
f.text(898, 81, "Policy head", size=12, weight=500, color=G.deep, box=c)
f.text(1118, 81, "$\\pi_\\phi$", size=15, anchor="end", box=c)
f.text(898, 108, "$\\hat{a}_{t:t+H}$", size=13, box=c)
f.tokens(962, 100, 8, "green", w=15, h=9, gap=4.2)
f.bracket(894, 118, 228, 56, WIRE, tick=4)
f.curves(902, 122, 212, 48, [G.accent, B.accent], seed=1.9, grid=False)
f.text(1008, 192, "action chunk · schematic", size=10.5, color=FAINT, anchor="middle", box=c, family="serif", italic=True)

c = f.card(888, 214, 240, 146, "purple", stack=1)
f.text(898, 233, "World model", size=12, weight=500, color=P.deep, box=c)
f.text(1118, 233, "$F_\\psi$", size=15, anchor="end", box=c)
f.chip(898, 250, 40, 24, "$z_t$", "purple", size=13, fill="#FFFFFF", stroke=P.accent, color=INK)
f.arrow("M938 262H958", WIRE, 1.2, head=6)
f.chip(960, 250, 56, 24, "$\\hat{z}_{t+1}$", "purple", size=13, fill="#FFFFFF", stroke=P.accent, color=INK)
f.arrow("M1018 262H1058", R.accent, 1.2, start=True, head=6)
f.text(1038, 256, "MSE", size=9.5, color=R.deep, anchor="middle", family="mono")
f.chip(1060, 250, 58, 24, "$z_{t+1}$", "gray", size=13, fill="#FFFFFF", color=INK)
f.text(1008, 296, "latent rollout for $H$ steps", size=11, color=MUTED, anchor="middle", box=c, family="serif", italic=True)
f.chip(898, 310, 220, 26, "repeat $F_\\psi$ · optional replan", "purple", size=11, fill="#FFFFFF", stroke=P.mid, color=INK)

c = f.card(1138, 62, 244, 298, fill="#FFFFFF", stroke=HAIR)
f.text(1148, 81, "Objective", size=12, weight=500, box=c)
f.text(1260, 124, "$\\mathcal{L}$", size=30, anchor="middle", box=c)
f.chip(1150, 138, 220, 26, "$\\mathcal{L}_{\\mathrm{BC}}$ · imitation", "green", size=11.5, fill="#FFFFFF", stroke=G.accent, color=INK)
f.chip(1150, 170, 220, 26, "$\\lambda\\,\\mathcal{L}_{\\mathrm{pred}}$ · latent prediction", "purple", size=11.5, fill="#FFFFFF", stroke=P.accent, color=INK)
f.chip(1150, 202, 220, 26, "$\\mathcal{R}(z)$ · regularizer", "red", size=11.5, fill="#FFFFFF", stroke=R.accent, color=INK)
f.line("M1160 244V320H1360", STONE, 0.9)
pts = " L".join(f"{1162 + 196 * t / 60:.1f} {318 - 70 * math.exp(-4 * t / 60) - 3 * math.sin(t):.1f}" for t in range(61))
f.add(f'<path d="M{pts}" fill="none" stroke="{INK}" stroke-width="1.3"/>')
f.text(1260, 342, "training loss · schematic", size=10.5, color=FAINT, anchor="middle", box=c, family="serif", italic=True)
f.arrow("M1128 130H1136", G.accent, 1.2, head=6)
f.arrow("M1128 290H1136", P.accent, 1.2, head=6)

f.save(str(OUT))
print(OUT)
