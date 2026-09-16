"""figkit - primitives for dense, paper-style SVG block diagrams.

Design contract (why these defaults exist):
- Figures are read at paper-column width, so margins/gutters are tight (8/10 px)
  and text is small but dense; titles belong in the caption, not the canvas.
- Three nesting levels carry hierarchy: stage panel (gradient) -> white card -> chip.
- Every card should carry a symbol, term, thumbnail or data sketch, not prose.
- Colors are semantic roles reused across badges, borders and connectors.

All geometry is explicit. `qa_svg_figure.py` renders the SVG in headless Chrome
and gates text overflow, text collisions, box overlap, lines through labels and
canvas coverage. See `references/dense-svg-figures.md` for the full contract.

Text API: plain text with `$...$` math islands, for example
"FK → $\\hat{\\tau}_{\\mathrm{EEF}}$". Math supports _ ^ {} \\hat \\bar \\tilde
\\mathrm \\mathbb \\mathcal, Greek letters, relations (= \\in \\le \\to \\gets)
with TeX-like spacing, and primes written as a'_t.
"""

from __future__ import annotations

import math
import re
from html import escape

SANS = "'Helvetica Neue', Helvetica, Arial, 'PingFang SC', 'Hiragino Sans GB', sans-serif"
MATH = "STIXGeneral, 'STIX Two Math', 'Times New Roman', serif"
INK = "#1F2937"
MUTED = "#5B6573"
FAINT = "#8A94A3"
HAIR = "#D5DAE1"


class Role:
    """A semantic color role: accent stroke, tint fill, deep text, panel gradient."""

    def __init__(self, accent: str, tint: str, deep: str, g0: str, g1: str):
        self.accent, self.tint, self.deep, self.g0, self.g1 = accent, tint, deep, g0, g1


PAL = {
    "blue": Role("#3D6FB4", "#E6EFFA", "#1E4C8A", "#D6E4F5", "#F3F7FC"),
    "purple": Role("#7A5BB5", "#EEE8F8", "#4B3290", "#E4DBF5", "#F7F4FC"),
    "orange": Role("#E07A2F", "#FCEBDC", "#A24E12", "#FADFC9", "#FEF6EF"),
    "green": Role("#3B9468", "#E2F2E9", "#1F6644", "#D3ECDD", "#F2F9F5"),
    "red": Role("#D04A3E", "#FBE4E1", "#9E2A21", "#F8D9D5", "#FDF3F2"),
    "amber": Role("#C98A12", "#FBF1D9", "#855A05", "#F6E8C6", "#FDF9EE"),
    "gray": Role("#7A8594", "#EEF1F4", "#374151", "#E6EAF0", "#F7F9FB"),
}

# ---------------------------------------------------------------------------
# Text measurement (estimate only; qa_svg_figure.py measures the real render)
# ---------------------------------------------------------------------------


def _cw(ch: str) -> float:
    o = ord(ch)
    if 0x2E80 <= o <= 0x9FFF or 0xFF00 <= o <= 0xFFEF or 0x3000 <= o <= 0x303F:
        return 1.0
    if ch == " ":
        return 0.28
    if ch in "il.,:;|!'·":
        return 0.26
    if ch in "fjtrI()[]{}/-":
        return 0.35
    if ch in "mwMW%":
        return 0.85
    if ch.isupper():
        return 0.68
    if ch.isdigit():
        return 0.56
    return 0.54


def text_w(s: str, size: float, bold: bool = False, ls: float = 0.0) -> float:
    plain = re.sub(r"\$[^$]*\$", lambda m: "x" * max(1, len(_math_plain(m.group(0)[1:-1]))), s)
    return sum(_cw(c) for c in plain) * size * (1.06 if bold else 1.0) + ls * len(plain)


# ---------------------------------------------------------------------------
# Mini TeX-like math: _ ^ {} \hat \bar \mathrm \mathbb \mathcal + symbols
# ---------------------------------------------------------------------------

_SYM = {
    "pi": "π", "tau": "τ", "theta": "θ", "eta": "η", "psi": "ψ", "phi": "φ", "ell": "ℓ",
    "alpha": "α", "beta": "β", "sigma": "σ", "epsilon": "ε", "Delta": "Δ", "Sigma": "Σ",
    "in": "∈", "times": "×", "le": "≤", "ge": "≥", "to": "→", "approx": "≈", "neq": "≠",
    "cdot": "·", "mid": "∣", "notin": "∉", "uparrow": "↑", "downarrow": "↓", "star": "⋆",
    "top": "⊤", "sqrt": "√", "odot": "⊙", "oplus": "⊕", "otimes": "⊗", "lambda": "λ", "mu": "μ", "partial": "∂", "nabla": "∇", "prime": "′", "infty": "∞", "sim": "∼", "gets": "←",
    ";": " ", ",": " ", " ": " ", "quad": "  ",
}
_ITALIC_GREEK = {"pi", "tau", "theta", "eta", "psi", "phi", "ell", "alpha", "beta", "sigma", "epsilon", "lambda", "mu"}
_BB = {"R": "ℝ", "N": "ℕ", "E": "𝔼"}
_CAL = {"L": "ℒ", "J": "𝒥", "D": "𝒟", "O": "𝒪", "A": "𝒜", "V": "𝒱", "R": "ℛ", "N": "𝒩", "M": "ℳ", "F": "ℱ", "S": "𝒮", "T": "𝒯"}


def _math_plain(src: str) -> str:
    return re.sub(r"\\[a-zA-Z]+|[{}_^]", "", src)


def _single_token(src: str, i: int) -> str:
    """One unbraced script/accent argument: a command such as \\theta, or one character."""
    if i >= len(src):
        return ""
    m = re.match(r"\\[a-zA-Z]+|\\.", src[i:])
    return m.group(0) if m else src[i]


def _parse(src: str, i: int = 0, upright: bool = False, stop: str | None = None):
    atoms: list[dict] = []
    while i < len(src):
        ch = src[i]
        if stop and ch == stop:
            return atoms, i + 1
        if ch == "{":
            grp, i = _parse(src, i + 1, upright, "}")
            atoms.extend(grp)
            continue
        if ch in "_^":
            i += 1
            if i < len(src) and src[i] == "{":
                arg, i = _parse(src, i + 1, upright, "}")
            else:
                token = _single_token(src, i)
                arg, _ = _parse(token, 0, upright)
                i += len(token)
            if not atoms:
                atoms.append({"t": "", "it": False})
            atoms[-1]["sub" if ch == "_" else "sup"] = arg
            continue
        if ch == "\\":
            m = re.match(r"\\([a-zA-Z]+|.)", src[i:])
            cmd = m.group(1)
            i += len(m.group(0))
            if cmd in ("hat", "bar", "tilde", "mathrm", "mathbb", "mathcal", "text"):
                if i < len(src) and src[i] == "{":
                    arg, i = _parse(src, i + 1, cmd in ("mathrm", "text") or upright, "}")
                else:
                    token = _single_token(src, i)
                    arg, _ = _parse(token, 0, upright)
                    i += len(token)
                if cmd == "mathbb":
                    arg = [{"t": "".join(_BB.get(c, c) for c in a["t"]), "it": False} for a in arg]
                elif cmd == "mathcal":
                    arg = [{"t": "".join(_CAL.get(c, c) for c in a["t"]), "it": False} for a in arg]
                elif cmd in ("hat", "bar", "tilde") and arg:
                    mark = {"hat": "\u0302", "bar": "\u0304", "tilde": "\u0303"}[cmd]
                    arg[-1] = dict(arg[-1], t=arg[-1]["t"] + mark)
                atoms.extend(arg)
                continue
            atoms.append({"t": _SYM.get(cmd, cmd), "it": cmd in _ITALIC_GREEK and not upright})
            continue
        if ch == "'":
            atoms.append({"t": "′", "it": False})
            i += 1
            continue
        if ch == " ":
            i += 1
            continue
        t = "\u2212" if ch == "-" else ch
        atoms.append({"t": t, "it": ch.isalpha() and not upright})
        i += 1
    return atoms, i


_REL = set("=∈≤≥→≈≠∼←")
_BIN = set("+\u2212×")


def _spaced(t: str, script: bool) -> str:
    """TeX-like spacing: relations get a medium space, binaries/commas a thin one (base level only)."""
    if script:
        return t
    if t in _REL:
        return f"\u2005{t}\u2005"
    if t in _BIN:
        return f"\u2009{t}\u2009"
    if t == ",":
        return ",\u2009"
    if t == "∣":
        return f"\u2005{t}\u2005"
    return t


def _emit(atoms, size, base_off, cur, out, script=False):
    for a in atoms:
        if a["t"]:
            dy = base_off - cur[0]
            cur[0] = base_off
            style = "italic" if a["it"] else "normal"
            out.append(
                f'<tspan font-family="{MATH}" font-style="{style}" font-size="{size:.2f}"'
                + (f' dy="{dy:.2f}"' if abs(dy) > 1e-6 else "")
                + f">{escape(_spaced(a['t'], script))}</tspan>"
            )
        sup, sub = a.get("sup"), a.get("sub")
        s2 = size * 0.7
        if sup:
            _emit(sup, s2, base_off - size * 0.38, cur, out, True)
        if sub:
            if sup:
                back = -sum(_cw(c) for c in _math_plain("".join(x["t"] for x in sup))) * s2 * 0.95
                out.append(f'<tspan font-size="{s2:.2f}" dx="{back:.2f}"></tspan>')
            _emit(sub, s2, base_off + size * 0.28, cur, out, True)


def rich(s: str, size: float) -> str:
    """Plain text with $math$ islands -> tspans (baseline restored at the end)."""
    out: list[str] = []
    cur = [0.0]
    for part in re.split(r"(\$[^$]*\$)", s):
        if not part:
            continue
        if part.startswith("$") and part.endswith("$") and len(part) > 1:
            atoms, _ = _parse(part[1:-1])
            _emit(atoms, size * 1.08, 0.0, cur, out)
        else:
            dy = -cur[0]
            cur[0] = 0.0
            out.append("<tspan" + (f' dy="{dy:.2f}"' if abs(dy) > 1e-6 else "") + f">{escape(part)}</tspan>")
    if abs(cur[0]) > 1e-6:
        out.append(f'<tspan dy="{-cur[0]:.2f}"></tspan>')
    return "".join(out)


# ---------------------------------------------------------------------------
# Icons (24x24 line glyphs; use sparingly as header markers)
# ---------------------------------------------------------------------------

ICONS = {
    "spark": '<path d="M11 3c.6 4.3 2.7 6.4 7 7-4.3.6-6.4 2.7-7 7-.6-4.3-2.7-6.4-7-7 4.3-.6 6.4-2.7 7-7z"/><path d="M18.5 15c.3 1.7 1 2.4 2.7 2.7-1.7.3-2.4 1-2.7 2.7-.3-1.7-1-2.4-2.7-2.7 1.7-.3 2.4-1 2.7-2.7z"/>',
    "check": '<circle cx="12" cy="12" r="9.5"/><path d="M7.5 12.3l3 3 6-6.3"/>',
    "x": '<circle cx="12" cy="12" r="9.5"/><path d="M8.5 8.5l7 7M15.5 8.5l-7 7"/>',
    "wrench": '<path d="M14.7 4.2a4.6 4.6 0 0 0-5.6 5.9L3.7 15.5a1.9 1.9 0 0 0 2.7 2.7l5.4-5.4a4.6 4.6 0 0 0 5.9-5.6l-2.8 2.8-2.5-.4-.4-2.5z"/>',
    "joint": '<circle cx="12" cy="12" r="3.2"/><circle cx="12" cy="12" r="7.5"/><path d="M12 1.8v2.7M12 19.5v2.7M1.8 12h2.7M19.5 12h2.7M4.8 4.8l1.9 1.9M17.3 17.3l1.9 1.9M4.8 19.2l1.9-1.9M17.3 6.7l1.9-1.9"/>',
    "eye": '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
    "chat": '<path d="M4 4.5h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1h-9l-5 4v-4H4a1 1 0 0 1-1-1v-10a1 1 0 0 1 1-1z"/><path d="M7.5 9.5h9M7.5 12.5h5.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "plan": '<rect x="4" y="3.5" width="16" height="17" rx="2"/><path d="M7.5 8.5l1.5 1.5 2.5-2.5M7.5 14.5l1.5 1.5 2.5-2.5M14.5 9h2.5M14.5 15h2.5"/>',
    "recover": '<path d="M19.5 10.5A8 8 0 0 0 5.2 7.3"/><path d="M4.5 3.5v4.3h4.3"/><path d="M4.5 13.5a8 8 0 0 0 14.3 3.2"/><path d="M19.5 20.5v-4.3h-4.3"/>',
    "gripper": '<path d="M12 2.5v5"/><rect x="6.5" y="7.5" width="11" height="4" rx="1"/><path d="M8.5 11.5v4l2.3 5M15.5 11.5v4l-2.3 5"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
    "cube": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',
    "bot": '<rect x="4.5" y="8" width="15" height="11.5" rx="3"/><path d="M12 8V5"/><circle cx="12" cy="3.6" r="1.3"/><circle cx="9.2" cy="13.2" r="1.2"/><circle cx="14.8" cy="13.2" r="1.2"/><path d="M2.5 12.2v3M21.5 12.2v3"/>',
    "trend": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "brain": '<path d="M11.3 5.2A3 3 0 0 0 6.2 6.4 3 3 0 0 0 4 11.5a3 3 0 0 0 1.6 4.8 3 3 0 0 0 3.2 3.5 2.6 2.6 0 0 0 2.5-1.4z"/><path d="M12.7 5.2a3 3 0 0 1 5.1 1.2 3 3 0 0 1 2.2 5.1 3 3 0 0 1-1.6 4.8 3 3 0 0 1-3.2 3.5 2.6 2.6 0 0 1-2.5-1.4z"/>',
    "contact": '<path d="M12 2.5v9"/><path d="M8.5 8l3.5 3.5L15.5 8"/><path d="M3 15h18"/><path d="M5.5 19l2.5-2.5M10 19l2.5-2.5M14.5 19l2.5-2.5M19 19l1.5-1.5"/>',
    "target": '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.3"/><path d="M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4"/>',
    "dist": '<path d="M2 19.5h20"/><path d="M2 19c3 0 4.2-11 7-11s4 11 7 11"/><path d="M8 19c3 0 4.2-11 7-11s4 11 7 11" stroke-dasharray="2 2"/>',
    "eyeoff": '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/><path d="M4 20L20 4"/>',
    "zigzag": '<path d="M2.5 17.5l4-6 3 4 4-9 3 6 5-5"/>',
    "traj": '<circle cx="4.5" cy="18.5" r="1.8"/><circle cx="19.5" cy="5.5" r="1.8"/><path d="M6.3 17.6c3.2-1.2 3.4-5.4 6.2-6.4 2.4-.9 3.9-2.4 5.3-4.3" stroke-dasharray="2.2 2.4"/>',
}

SCENE = """<symbol id="scene" viewBox="0 0 130 96">
<rect width="130" height="96" fill="#D8DEE4"/>
<path d="M0 60H130V96H0z" fill="#F5F5F2"/><path d="M0 60H130" stroke="#C4C9CE"/>
<path d="M88 55H121L118 77H91z" fill="#23272E"/><path d="M88 55H121" stroke="#454B55" stroke-width="2"/>
<path d="M62 60l3-3h12l-3 3z" fill="#F2766D"/><rect x="62" y="60" width="12" height="11" rx="1" fill="#E2483D"/>
<path d="M69 75l3-3h12l-3 3z" fill="#6A95EC"/><rect x="69" y="75" width="12" height="12" rx="1" fill="#3569D6"/>
<g fill="none" stroke-linecap="round" stroke-linejoin="round">
<path d="M14-4L20 26L42 36L48 49" stroke="#8C96A1" stroke-width="9"/><path d="M14-4L20 26L42 36L48 49" stroke="#F7F8FA" stroke-width="5.5"/>
<path d="M116-4L110 26L90 34L82 46" stroke="#8C96A1" stroke-width="9"/><path d="M116-4L110 26L90 34L82 46" stroke="#F7F8FA" stroke-width="5.5"/>
</g>
<circle cx="20" cy="26" r="3.6" fill="#5E6873"/><circle cx="42" cy="36" r="3.6" fill="#5E6873"/>
<circle cx="110" cy="26" r="3.6" fill="#5E6873"/><circle cx="90" cy="34" r="3.6" fill="#5E6873"/>
<path d="M45 50l1 7M51 50l-1 7M79 47l1 7M85 47l-1 7" stroke="#4A525C" stroke-width="2.4" stroke-linecap="round"/>
</symbol>"""


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------


class Fig:
    def __init__(self, w: int, h: int, bg: str = "#FFFFFF"):
        self.w, self.h, self.bg = w, h, bg
        self.defs: dict[str, str] = {}
        self.body: list[str] = []
        self._n = 0

    # -- plumbing ----------------------------------------------------------
    def uid(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}{self._n}"

    def add(self, *parts: str) -> None:
        self.body.extend(parts)

    def _marker(self, color: str, size: float = 8.0) -> str:
        mid = f"ah{color.strip('#')}{int(size)}"
        if mid not in self.defs:
            self.defs[mid] = (
                f'<marker id="{mid}" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="{size}" '
                f'markerHeight="{size}" markerUnits="userSpaceOnUse" orient="auto-start-reverse">'
                f'<path d="M0 0.6L10 5L0 9.4L2.6 5z" fill="{color}"/></marker>'
            )
        return mid

    def svg(self) -> str:
        defs = "".join(self.defs.values())
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">'
            f"<style>text{{font-family:{SANS};fill:{INK};white-space:pre}}"
            f".ic{{fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}}</style>"
            f"<defs>{defs}</defs>"
            f'<rect width="{self.w}" height="{self.h}" fill="{self.bg}"/>' + "".join(self.body) + "</svg>"
        )

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.svg())

    # -- text --------------------------------------------------------------
    def text(self, x, y, s, size=11.5, weight=400, color=INK, anchor="start", ls=0.0, box=None, italic=False, opacity=None):
        attrs = f'x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}"'
        if weight != 400:
            attrs += f' font-weight="{weight}"'
        if anchor != "start":
            attrs += f' text-anchor="{anchor}"'
        if ls:
            attrs += f' letter-spacing="{ls}"'
        if italic:
            attrs += ' font-style="italic"'
        if opacity is not None:
            attrs += f' opacity="{opacity}"'
        if box:
            attrs += f' data-in="{box}"'
        self.add(f"<text {attrs}>{rich(s, size)}</text>")

    # -- containers ----------------------------------------------------------
    def panel(self, x, y, w, h, role, title, sub=None, dashed=False, horizontal=False, r=10, title_size=13.5):
        """Stage panel with gradient fill and centered uppercase header. Returns content top y."""
        p = PAL[role]
        gid = self.uid("g")
        x2, y2 = ("1", "0") if horizontal else ("0", "1")
        self.defs[gid] = (
            f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
            f'<stop offset="0" stop-color="{p.g0}"/><stop offset="1" stop-color="{p.g1}"/></linearGradient>'
        )
        bid = self.uid("panel")
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        fill = "#FFFFFF" if dashed else f"url(#{gid})"
        self.add(
            f'<rect data-box="{bid}" data-kind="panel" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
            f'fill="{fill}" stroke="{p.accent}" stroke-opacity="{0.55 if dashed else 0.8}" stroke-width="1.5"{dash}/>'
        )
        if not title:
            return y + 10
        self.text(x + w / 2, y + 21, title, size=title_size, weight=700, color=p.deep, anchor="middle", ls=0.6, box=bid)
        if sub:
            self.text(x + w / 2, y + 36, sub, size=10.5, color=MUTED, anchor="middle", box=bid)
            return y + 46
        return y + 32

    def card(self, x, y, w, h, role=None, fill="#FFFFFF", sw=1.3, r=6, stack=0, topbar=False, dashed=False, stroke=None, kind="card"):
        p = PAL[role] if role else None
        st = stroke or (p.accent if p else HAIR)
        cid = self.uid("c")
        dash = ' stroke-dasharray="5 3"' if dashed else ""
        for k in range(stack, 0, -1):
            o = 4 * k
            self.add(f'<rect x="{x + o}" y="{y - o}" width="{w}" height="{h}" rx="{r}" fill="#FFFFFF" stroke="{st}" stroke-opacity="0.55" stroke-width="{sw}"/>')
        self.add(f'<rect data-box="{cid}" data-kind="{kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{st}" stroke-width="{sw}"{dash}/>')
        if topbar and p:
            self.add(
                f'<path d="M{x} {y + r}A{r} {r} 0 0 1 {x + r} {y}H{x + w - r}A{r} {r} 0 0 1 {x + w} {y + r}" '
                f'fill="none" stroke="{p.accent}" stroke-width="4"/>'
            )
        return cid

    def chip(self, x, y, w, h, s, role=None, size=11, fill=None, color=None, weight=400, r=4, stroke=None, dashed=False):
        p = PAL[role] if role else None
        cid = self.card(x, y, w, h, fill=fill or (p.tint if p else "#FFFFFF"), stroke=stroke or (p.accent if p else HAIR), sw=1.1, r=r, dashed=dashed, kind="chip")
        self.text(x + w / 2, y + h / 2 + size * 0.36, s, size=size, weight=weight, color=color or (p.deep if p else INK), anchor="middle", box=cid)
        return cid

    def badge(self, x, y, s, role, size=10.5, h=18, w=None):
        p = PAL[role]
        w = w or text_w(s, size, bold=True) + 12
        cid = self.uid("b")
        self.add(f'<rect data-box="{cid}" data-kind="chip" x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{p.accent}"/>')
        self.text(x + w / 2, y + h / 2 + size * 0.36, s, size=size, weight=700, color="#FFFFFF", anchor="middle", box=cid)
        return w

    def pill(self, cx, cy, s, role="gray", size=10.5, h=20, fill="#FFFFFF", weight=400):
        p = PAL[role]
        w = text_w(s, size) + 18
        cid = self.uid("p")
        self.add(f'<rect data-box="{cid}" data-kind="chip" x="{cx - w / 2:.1f}" y="{cy - h / 2}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill}" stroke="{p.accent}" stroke-width="1.1"/>')
        self.text(cx, cy + size * 0.36, s, size=size, color=p.deep, anchor="middle", box=cid, weight=weight)
        return w

    # -- glyphs --------------------------------------------------------------
    def icon(self, name, x, y, size, color):
        sid = f"i-{name}"
        if sid not in self.defs:
            self.defs[sid] = f'<symbol id="{sid}" viewBox="0 0 24 24" class="ic">{ICONS[name]}</symbol>'
        self.add(f'<use href="#{sid}" x="{x}" y="{y}" width="{size}" height="{size}" color="{color}"/>')

    def scene(self, x, y, w, h, frame=None, marker=None):
        if "scene" not in self.defs:
            self.defs["scene"] = SCENE
        cid = self.uid("s")
        clip = self.uid("clip")
        self.defs[clip] = f'<clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3"/></clipPath>'
        self.add(f'<g clip-path="url(#{clip})"><use href="#scene" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"/></g>')
        self.add(f'<rect data-box="{cid}" data-kind="thumb" x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="none" stroke="{frame or HAIR}" stroke-width="1.6"/>')
        return cid

    def arrow(self, d, color=INK, sw=1.6, dashed=False, start=False, end=True, head=8.0, opacity=None):
        mk = self._marker(color, head)
        attrs = f'd="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
        if dashed:
            attrs += ' stroke-dasharray="5 3.5"'
        if end:
            attrs += f' marker-end="url(#{mk})"'
        if start:
            attrs += f' marker-start="url(#{mk})"'
        if opacity is not None:
            attrs += f' stroke-opacity="{opacity}"'
        self.add(f"<path {attrs}/>")

    def dot(self, x, y, color=INK, r=2.8):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

    def brace(self, x, y1, y2, color=FAINT, depth=12, sw=1.6):
        """Right-pointing curly brace spanning y1..y2 at x (opens to the left)."""
        m = (y1 + y2) / 2
        d = depth / 2
        self.add(
            f'<path d="M{x} {y1}C{x + d} {y1} {x + d} {y1 + 6} {x + d} {y1 + 14}V{m - 10}C{x + d} {m - 3} {x + depth} {m} {x + depth} {m}'
            f'C{x + depth} {m} {x + d} {m + 3} {x + d} {m + 10}V{y2 - 14}C{x + d} {y2 - 6} {x + d} {y2} {x} {y2}" '
            f'fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round"/>'
        )

    def line(self, d, color=HAIR, sw=1.0, dashed=False):
        dash = ' stroke-dasharray="3 3"' if dashed else ""
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{dash}/>')

    # -- data sketches -------------------------------------------------------
    def bars(self, x, y, w, h, values, color, gap=2.0, base=HAIR, box=None):
        n = len(values)
        bw = (w - gap * (n - 1)) / n
        self.line(f"M{x} {y + h}H{x + w}", base, 1)
        for i, v in enumerate(values):
            bh = max(1.5, v * h)
            self.add(f'<rect x="{x + i * (bw + gap):.1f}" y="{y + h - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="1" fill="{color}" opacity="{0.55 + 0.45 * v:.2f}"/>')

    def curves(self, x, y, w, h, colors, seed=1.0, grid=True, n=60):
        if grid:
            for k in range(1, 4):
                self.line(f"M{x} {y + h * k / 4:.1f}H{x + w}", "#E6EAF0", 0.8)
            self.line(f"M{x} {y}V{y + h}H{x + w}", "#AAB2BE", 1.0)
        for j, c in enumerate(colors):
            pts = []
            for i in range(n + 1):
                t = i / n
                v = 0.5 + 0.28 * math.sin(2.2 * t * math.pi + seed * (j + 1) * 1.7) + 0.12 * math.sin(5.3 * t * math.pi + j * 0.9 + seed)
                pts.append(f"{x + t * w:.1f} {y + (1 - v) * h:.1f}")
            self.add(f'<path d="M{"L".join(pts)}" fill="none" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>')

    def strip(self, x, y, w, h, n, lit, color, off="#E6EAF0", gap=1.0):
        cw = (w - gap * (n - 1)) / n
        for i in range(n):
            fill = color if i < lit else off
            self.add(f'<rect x="{x + i * (cw + gap):.2f}" y="{y}" width="{cw:.2f}" height="{h}" rx="0.8" fill="{fill}"/>')
