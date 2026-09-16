"""Illustrative dense SVG figure: a placeholder multi-view policy method.

The method, module names and sketches are invented to demonstrate the figkit
vocabulary (stage panels, stacked cards, chips, math, thumbnails, data sketches,
brace, fork/merge and loss connectors). It is not a real paper figure and shows
no results. Run from any directory:

    python example_pipeline.py
    python ../../scripts/qa_svg_figure.py example_pipeline.svg --png
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))

from figkit import FAINT, INK, MUTED, PAL, Fig

OUT = HERE / "example_pipeline.svg"
B, P, R, G, A, O = (PAL[k] for k in ("blue", "purple", "red", "green", "amber", "orange"))

f = Fig(1400, 380)

# ---------------------------------------------------------------- inputs
f.panel(8, 8, 196, 364, "gray", "INPUTS", sub="multi-view observation", dashed=True)
for k, (role, name, sym, tag) in enumerate((("blue", "view 1", "$x^{(1)}$", "front cam"), ("purple", "view 2", "$x^{(2)}$", "side cam"))):
    y = 56 + 108 * k
    c = f.card(18, y, 176, 100, role, topbar=True)
    f.text(28, y + 20, name, size=12, weight=700, box=c)
    f.text(184, y + 20, sym, size=13, color=PAL[role].deep, anchor="end", box=c)
    f.scene(28, y + 28, 84, 62, frame=PAL[role].accent)
    f.chip(120, y + 32, 64, 20, "RGB", role, size=10)
    f.chip(120, y + 58, 64, 20, tag, role, size=10)
c = f.card(18, 272, 176, 90, "orange", topbar=True)
f.text(28, 292, "state", size=12, weight=700, box=c)
f.text(184, 292, "$s_t$", size=13, color=O.deep, anchor="end", box=c)
f.bars(28, 300, 156, 34, [0.6, 0.35, 0.8, 0.5, 0.3, 0.7, 0.45, 0.62, 0.4, 0.74, 0.5, 0.33], O.accent)
f.text(106, 352, "proprioception", size=10, color=MUTED, anchor="middle", box=c)
f.brace(206, 24, 356, color="#9AA3AF", depth=12)
f.arrow("M220 190H250", "#9AA3AF", 1.6)

# ---------------------------------------------------------------- shared encoder
f.panel(240, 8, 196, 364, "blue", "SHARED ENCODER", sub="one latent space")
c = f.card(252, 62, 172, 298, "blue", stack=1, sw=1.5)
f.text(338, 84, "ENCODER", size=10.5, weight=700, color=B.deep, anchor="middle", ls=0.5, box=c)
f.text(338, 126, "$E_\\theta$", size=30, anchor="middle", box=c)
f.text(338, 164, "weights shared across views", size=10, color=MUTED, anchor="middle", box=c)
for k, (role, sym) in enumerate((("blue", "$z^{(1)}$"), ("purple", "$z^{(2)}$"), ("orange", "$z^{s}$"))):
    f.chip(266 + 50 * k, 174, 44, 24, sym, role, size=12)
f.add('<rect x="266" y="208" width="144" height="88" rx="4" fill="#FFFFFF" stroke="#DCE6F2"/>')
for k, (role, cx, cy) in enumerate((("blue", 300, 240), ("purple", 366, 232), ("orange", 334, 272))):
    for j in range(9):
        ang = j * 2.4 + k
        f.dot(cx + 14 * math.cos(ang) * (0.4 + 0.07 * j), cy + 11 * math.sin(ang) * (0.4 + 0.07 * j), PAL[role].accent, 2.4)
f.text(338, 318, "$z^{(v)}=E_\\theta(x^{(v)})\\in\\mathbb{R}^{d}$", size=11.5, anchor="middle", box=c)
f.text(338, 340, "indexed latent batch", size=9.5, color=MUTED, anchor="middle", box=c)

# ---------------------------------------------------------------- proposed fusion
f.panel(444, 8, 424, 364, "red", "PROPOSED FUSION", sub="contribution · highlighted in red")
f.arrow("M424 210H454", B.accent)
c = f.card(456, 62, 200, 298, "red", sw=1.8)
f.text(556, 82, "CROSS-VIEW ATTENTION", size=10.5, weight=700, color=R.deep, anchor="middle", ls=0.4, box=c)
for k, (role, sym) in enumerate((("blue", "$Q$"), ("purple", "$K$"), ("purple", "$V$"))):
    f.chip(478 + 54 * k, 94, 48, 22, sym, role, size=12)
for i in range(8):
    for j in range(8):
        v = 0.15 + 0.85 * math.exp(-((i - j) ** 2) / 3.0) * (0.6 + 0.4 * math.cos(i * 0.7 + j * 0.3))
        f.add(f'<rect x="{492 + 16 * j}" y="{126 + 16 * i}" width="15" height="15" fill="{R.accent}" opacity="{v:.2f}"/>')
f.text(556, 272, "attention map · schematic", size=9.5, color=FAINT, anchor="middle", box=c)
f.text(556, 298, "$A=\\mathrm{softmax}(QK^{\\top}/\\sqrt{d})$", size=12, anchor="middle", box=c)
f.chip(468, 318, 176, 28, "$h=\\mathrm{Attn}(Q,K,V)$", "red", size=11.5)
f.arrow("M656 210H668", R.accent)

c = f.card(670, 62, 186, 298, "red", sw=1.5)
f.text(763, 82, "ADAPTIVE GATE", size=10.5, weight=700, color=R.deep, anchor="middle", ls=0.4, box=c)
f.text(763, 114, "$g=\\sigma(W[h,z])$", size=16, anchor="middle", box=c)
f.curves(684, 128, 158, 68, [R.accent, O.accent], seed=0.6)
f.text(763, 216, "per-view gate weights", size=9.5, color=MUTED, anchor="middle", box=c)
f.bars(684, 224, 158, 36, [0.8, 0.45, 0.62, 0.3, 0.7, 0.52], R.accent, gap=8)
f.chip(682, 276, 162, 26, "$\\tilde{z}=g\\odot h+(1-g)\\odot z$", "red", size=11)
f.chip(682, 310, 162, 24, "residual · layer norm", "gray", size=10)

# ---------------------------------------------------------------- heads and objective
f.panel(876, 8, 516, 364, "green", "HEADS & OBJECTIVE", sub="training · inference")
f.arrow("M856 130H886", R.accent)
f.arrow("M856 285H886", R.accent)

c = f.card(888, 62, 240, 138, "green", sw=1.5)
f.icon("traj", 898, 70, 18, G.accent)
f.text(922, 84, "POLICY HEAD", size=11, weight=700, color=G.deep, ls=0.4, box=c)
f.text(1118, 84, "$\\pi_\\phi$", size=14, anchor="end", box=c)
f.text(898, 110, "$\\hat{a}_{t:t+H}$", size=13, box=c)
f.strip(962, 100, 156, 12, 16, 16, G.accent, gap=1.5)
f.curves(898, 120, 220, 56, [G.accent, B.accent], seed=1.9)
f.text(1008, 192, "action chunk · schematic", size=9.5, color=FAINT, anchor="middle", box=c)

c = f.card(888, 214, 240, 146, "amber", stack=1, sw=1.5)
f.icon("recover", 898, 222, 18, A.accent)
f.text(922, 236, "WORLD MODEL", size=11, weight=700, color=A.deep, ls=0.4, box=c)
f.text(1118, 236, "$F_\\psi$", size=14, anchor="end", box=c)
f.chip(898, 250, 40, 24, "$z_t$", "amber", size=12)
f.arrow("M938 262H958", A.accent, 1.4, head=6)
f.chip(960, 250, 56, 24, "$\\hat{z}_{t+1}$", "amber", size=12)
f.arrow("M1018 262H1058", R.accent, 1.4, start=True, head=6)
f.text(1038, 257, "MSE", size=9.5, weight=700, color=R.deep, anchor="middle")
f.chip(1060, 250, 58, 24, "$z_{t+1}$", "gray", size=12)
f.text(1008, 296, "latent rollout for $H$ steps", size=10, color=MUTED, anchor="middle", box=c)
f.chip(898, 310, 220, 26, "repeat $F_\\psi$ · optional replan", "amber", size=10.5)

c = f.card(1138, 62, 244, 298, "gray", sw=1.3)
f.text(1260, 82, "OBJECTIVE", size=10.5, weight=700, color=INK, anchor="middle", ls=0.4, box=c)
f.text(1260, 124, "$\\mathcal{L}$", size=30, anchor="middle", box=c)
f.chip(1150, 138, 220, 26, "$\\mathcal{L}_{\\mathrm{BC}}$ · imitation", "green", size=11)
f.chip(1150, 170, 220, 26, "$\\lambda\\,\\mathcal{L}_{\\mathrm{pred}}$ · latent prediction", "amber", size=11)
f.chip(1150, 202, 220, 26, "$\\mathcal{R}(z)$ · regularizer", "red", size=11)
f.line("M1160 244V320H1360", "#AAB2BE", 1.0)
pts = " L".join(f"{1162 + 196 * t / 60:.1f} {318 - 70 * math.exp(-4 * t / 60) - 3 * math.sin(t):.1f}" for t in range(61))
f.add(f'<path d="M{pts}" fill="none" stroke="{INK}" stroke-width="1.5"/>')
f.text(1260, 342, "training loss · schematic", size=9.5, color=FAINT, anchor="middle", box=c)
f.arrow("M1128 130H1136", G.accent, 1.4, head=6)
f.arrow("M1128 290H1136", A.accent, 1.4, head=6)

f.save(str(OUT))
print(OUT)
