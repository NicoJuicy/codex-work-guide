"""figkit - primitives for dense, paper-style SVG block diagrams.

Visual language (v2), distilled from CoRL / RSS / ICRA method figures
(pi0, OpenVLA, Octo, DP3, RT-H, YAY Robot, ReKep, RoboPoint, DexMimicGen, Hi Robot):
- Muted flat palette: a few pastel role fills with a slightly darker stroke,
  warm-gray neutrals, near-black thin connectors. No gradients on containers.
- Typography carries hierarchy: bold only for panel titles and key words,
  regular or medium weight for module names, serif italic for data names,
  variables and quoted language, monospace for tokens, code and model output.
- Shape carries meaning: token pills for sequences, trapezoids for encoders,
  bracketed vectors for actions, cylinders for stored data, block arrows for
  stage transitions, circled numbers for steps, dashed outlines for groups.
- Dense layout: tight margins and gutters; the title lives in the caption.

All geometry is explicit. `qa_svg_figure.py` renders the SVG in headless Chrome
and gates text overflow, text collisions, box overlap, lines through labels and
canvas coverage. See `references/visual-contract.md` for the full contract.

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
SERIF = "STIXGeneral, 'Times New Roman', Times, 'Songti SC', serif"
MONO = "'SF Mono', Menlo, 'Roboto Mono', Consolas, 'PingFang SC', monospace"
MATH = "STIXGeneral, 'STIX Two Math', 'Times New Roman', serif"
FAMILIES = {"sans": SANS, "serif": SERIF, "mono": MONO}

INK = "#1F1F1F"
MUTED = "#5C5C5C"
FAINT = "#8C8C8C"
HAIR = "#D8D4CA"
WIRE = "#3A3A3A"


class Role:
    """A semantic color role: accent stroke, tint fill, deep text, mid fill (tokens, bars)."""

    def __init__(self, accent: str, tint: str, deep: str, mid: str):
        self.accent, self.tint, self.deep, self.mid = accent, tint, deep, mid
        self.g0, self.g1 = mid, tint  # kept for scripts written against v1


def _mix(a: str, b: str, t: float) -> str:
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


PAL = {
    "blue": Role("#3B8EA5", "#DCEEF3", "#1F5E70", "#A9D0DC"),  # teal: motor policy, perception
    "purple": Role("#8870B8", "#EAE4F4", "#54408A", "#C8BAE5"),  # lavender: control, structure
    "red": Role("#C4583C", "#F8E1D9", "#8A3421", "#E9AE9C"),  # terracotta: override, error, loss
    "green": Role("#6F9E57", "#E3EEDA", "#3F6630", "#B9D6A6"),  # sage: accept, success, feedback
    "amber": Role("#CF9A22", "#FBEDC6", "#7A5506", "#F3CF72"),  # ochre: reasoning model, key module
    "orange": Role("#C9824A", "#F6E6D7", "#85522A", "#E5BE9C"),  # clay: proprioception, secondary signal
    "gray": Role("#9C968A", "#EEECE6", "#46423B", "#D6D2C4"),  # stone: inputs, neutral containers
}
for _alias, _key in (("teal", "blue"), ("lavender", "purple"), ("terracotta", "red"), ("sage", "green"),
                     ("ochre", "amber"), ("clay", "orange"), ("stone", "gray")):
    PAL[_alias] = PAL[_key]

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


_REL = set("=∈∉≤≥→≈≠∼←")
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
# Icons (24x24 line glyphs; use sparingly, never as the only content of a card)
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
    "person": '<circle cx="12" cy="7.5" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>',
}

# Schematic bimanual tabletop scene: muted, photo-like tones rather than clip-art colors.
SCENE = """<symbol id="scene" viewBox="0 0 130 96">
<rect width="130" height="96" fill="#D3D6D8"/>
<rect width="130" height="20" fill="#C8CBCE"/>
<path d="M0 58H130V96H0z" fill="#E4DCCB"/><path d="M0 58H130" stroke="#C9BCA3" stroke-width="1"/>
<path d="M0 90H130" stroke="#D4C8B1" stroke-width="1"/>
<ellipse cx="105" cy="78" rx="19" ry="3" fill="#000" opacity="0.14"/>
<ellipse cx="68" cy="72" rx="8" ry="2" fill="#000" opacity="0.14"/>
<ellipse cx="76" cy="88" rx="8" ry="2" fill="#000" opacity="0.14"/>
<path d="M89 55H121L118 77H92z" fill="#34383E"/><path d="M89 55H121" stroke="#50555C" stroke-width="2"/>
<path d="M62 60l3-3h12l-3 3z" fill="#CF6B5F"/><rect x="62" y="60" width="12" height="11" rx="0.8" fill="#B4473B"/>
<path d="M70 76l3-3h12l-3 3z" fill="#6E93C8"/><rect x="70" y="76" width="12" height="12" rx="0.8" fill="#3E67A6"/>
<g fill="none" stroke-linecap="round" stroke-linejoin="round">
<path d="M14-4L20 26L42 36L48 49" stroke="#9AA0A6" stroke-width="8.5"/><path d="M14-4L20 26L42 36L48 49" stroke="#ECEEEF" stroke-width="5.5"/>
<path d="M116-4L110 26L90 34L82 46" stroke="#9AA0A6" stroke-width="8.5"/><path d="M116-4L110 26L90 34L82 46" stroke="#ECEEEF" stroke-width="5.5"/>
</g>
<circle cx="20" cy="26" r="3.4" fill="#5C6167"/><circle cx="42" cy="36" r="3.4" fill="#5C6167"/>
<circle cx="110" cy="26" r="3.4" fill="#5C6167"/><circle cx="90" cy="34" r="3.4" fill="#5C6167"/>
<path d="M45 50l1 7M51 50l-1 7M79 47l1 7M85 47l-1 7" stroke="#3E4247" stroke-width="2.4" stroke-linecap="round"/>
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

    def _marker(self, color: str, size: float = 7.0, open_: bool = False) -> str:
        mid = f"ah{color.strip('#')}{int(size)}{'o' if open_ else ''}"
        if mid not in self.defs:
            shape = (
                f'<path d="M1 1.2L9 5L1 8.8" fill="none" stroke="{color}" stroke-width="1.6" stroke-linejoin="miter"/>'
                if open_
                else f'<path d="M0 1L10 5L0 9z" fill="{color}"/>'
            )
            self.defs[mid] = (
                f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="{size}" '
                f'markerHeight="{size}" markerUnits="userSpaceOnUse" orient="auto-start-reverse">{shape}</marker>'
            )
        return mid

    def svg(self) -> str:
        defs = "".join(self.defs.values())
        return (
            # Default family on the root (inherited) rather than a `text{}` CSS rule: a stylesheet rule
            # would override per-element font-family attributes and silently drop serif/mono labels.
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
            f'font-family="{SANS}">'
            f"<style>text{{white-space:pre;font-kerning:normal}}text:not([fill]){{fill:{INK}}}"
            f".ic{{fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}}</style>"
            f"<defs>{defs}</defs>"
            f'<rect width="{self.w}" height="{self.h}" fill="{self.bg}"/>' + "".join(self.body) + "</svg>"
        )

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.svg())

    # -- text --------------------------------------------------------------
    def text(self, x, y, s, size=11.0, weight=400, color=INK, anchor="start", ls=0.0, box=None,
             italic=False, opacity=None, family="sans"):
        """Rich text. family: sans (labels), serif (data names, quoted language), mono (tokens, code)."""
        attrs = f'x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}"'
        if family != "sans":
            attrs += f' font-family="{FAMILIES[family]}"'
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
    def panel(self, x, y, w, h, role, title, sub=None, dashed=False, horizontal=False, r=8, title_size=14, fill=None,
              sub_below=False):
        """Flat stage panel with a left-aligned bold title and a regular gray subtitle on the same line
        (or on the next line with sub_below=True for narrow panels).

        Returns the content top y. `title=None` draws a headerless container.
        """
        p = PAL[role]
        bid = self.uid("panel")
        if dashed:
            body = f'fill="{fill or "#FFFFFF"}" stroke="{p.accent}" stroke-opacity="0.75" stroke-width="1.2" stroke-dasharray="5 4"'
        else:
            body = f'fill="{fill or _mix(p.tint, "#FFFFFF", 0.45)}" stroke="none"'
        self.add(f'<rect data-box="{bid}" data-kind="panel" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" {body}/>')
        if not title:
            return y + 10
        markup = f'<tspan font-weight="700">{rich(title, title_size)}</tspan>'
        if sub and not sub_below:
            markup += f'<tspan dx="9" font-size="{title_size - 3}" fill="{MUTED}">{rich(sub, title_size - 3)}</tspan>'
        self.add(f'<text x="{x + 12}" y="{y + 22}" font-size="{title_size}" fill="{INK}" data-in="{bid}">{markup}</text>')
        if sub and sub_below:
            self.text(x + 12, y + 38, sub, size=title_size - 3, color=MUTED, box=bid)
            return y + 48
        return y + 34

    def card(self, x, y, w, h, role=None, fill=None, sw=1.0, r=5, stack=0, topbar=False, dashed=False,
             stroke=None, kind="card", key=False):
        """Pastel card: role tint fill with a slightly darker stroke. key=True draws the near-black outline
        used for the one module the reader should find first."""
        p = PAL[role] if role else None
        fl = fill or (p.tint if p else "#FFFFFF")
        st = stroke or (INK if key else (p.accent if p else HAIR))
        sw = 1.4 if key and sw == 1.0 else sw
        cid = self.uid("c")
        dash = ' stroke-dasharray="4 3"' if dashed else ""
        for k in range(stack, 0, -1):
            o = 4 * k
            self.add(f'<rect x="{x + o}" y="{y - o}" width="{w}" height="{h}" rx="{r}" fill="{_mix(fl, "#FFFFFF", 0.35)}" '
                     f'stroke="{st}" stroke-opacity="0.45" stroke-width="{sw}"/>')
        self.add(f'<rect data-box="{cid}" data-kind="{kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
                 f'fill="{fl}" stroke="{st}" stroke-width="{sw}"{dash}/>')
        if topbar and p:
            self.add(f'<path d="M{x + r} {y + 1.5}H{x + w - r}" stroke="{p.accent}" stroke-width="3" stroke-linecap="round"/>')
        return cid

    def chip(self, x, y, w, h, s, role=None, size=10.5, fill=None, color=None, weight=400, r=3, stroke=None,
             dashed=False, family="sans", italic=False):
        p = PAL[role] if role else None
        cid = self.card(x, y, w, h, fill=fill or (p.tint if p else "#FFFFFF"), stroke=stroke or (p.mid if p else HAIR),
                        sw=0.9, r=r, dashed=dashed, kind="chip")
        self.text(x + w / 2, y + h / 2 + size * 0.36, s, size=size, weight=weight, color=color or (p.deep if p else INK),
                  anchor="middle", box=cid, family=family, italic=italic)
        return cid

    def badge(self, x, y, s, role, size=10, h=17, w=None):
        """Quiet tag for a key number: tint fill, bold deep text, no outline."""
        p = PAL[role]
        w = w or text_w(s, size, bold=True) + 12
        cid = self.uid("b")
        self.add(f'<rect data-box="{cid}" data-kind="chip" x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="3" fill="{p.tint}" '
                 f'stroke="{p.mid}" stroke-width="0.8"/>')
        self.text(x + w / 2, y + h / 2 + size * 0.36, s, size=size, weight=700, color=p.deep, anchor="middle", box=cid)
        return w

    def pill(self, cx, cy, s, role="gray", size=11, h=21, fill="#FFFFFF", weight=400, italic=True, family="serif"):
        """Label that sits on a connector: white knock-out background, serif italic text."""
        p = PAL[role]
        w = text_w(s, size) + 12
        cid = self.uid("p")
        self.add(f'<rect data-box="{cid}" data-kind="chip" x="{cx - w / 2:.1f}" y="{cy - h / 2}" width="{w:.1f}" height="{h}" '
                 f'rx="3" fill="{fill}"/>')
        self.text(cx, cy + size * 0.34, s, size=size, color=p.deep, anchor="middle", box=cid, weight=weight,
                  italic=italic, family=family)
        return w

    def step(self, cx, cy, n, r=7.5, color=INK):
        """Circled step number (thin outline)."""
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="{color}" stroke-width="1"/>')
        self.text(cx, cy + 3.6, str(n), size=10, color=color, anchor="middle")

    # -- shapes with meaning ----------------------------------------------------
    def tokens(self, x, y, n, role, w=16, h=8, gap=4, lit=None, dashed=False, to_role=None):
        """Row of token pills (a sequence). `lit` pills use the role color, the rest stay neutral;
        `to_role` blends the fill across the row."""
        p = PAL[role]
        q = PAL[to_role] if to_role else None
        for i in range(n):
            on = lit is None or i < lit
            fillc = (_mix(p.mid, q.mid, i / max(1, n - 1)) if q else p.mid) if on else "#EEECE6"
            st = p.accent if on else "#C9C5BA"
            dash = ' stroke-dasharray="2 1.5"' if dashed else ""
            self.add(f'<rect x="{x + i * (w + gap):.1f}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="{fillc}" '
                     f'stroke="{st}" stroke-width="0.9"{dash}/>')
        return n * w + (n - 1) * gap

    def trapezoid(self, x, y, w, h, role, s=None, size=12, inset=0.16, wide_bottom=True, family="sans", italic=False):
        p = PAL[role]
        d = w * inset
        pts = (f"{x + d},{y} {x + w - d},{y} {x + w},{y + h} {x},{y + h}" if wide_bottom
               else f"{x},{y} {x + w},{y} {x + w - d},{y + h} {x + d},{y + h}")
        cid = self.uid("t")
        self.add(f'<polygon data-box="{cid}" data-kind="card" points="{pts}" fill="{p.tint}" stroke="{p.accent}" stroke-width="1"/>')
        if s:
            self.text(x + w / 2, y + h / 2 + size * 0.36, s, size=size, color=p.deep, anchor="middle", box=cid,
                      family=family, italic=italic)
        return cid

    def bracket(self, x, y, w, h, color=INK, sw=1.1, tick=5):
        """Square brackets around a region (a vector or a grouped output)."""
        self.add(f'<path d="M{x + tick} {y}H{x}V{y + h}H{x + tick}M{x + w - tick} {y}H{x + w}V{y + h}H{x + w - tick}" '
                 f'fill="none" stroke="{color}" stroke-width="{sw}"/>')

    def cylinder(self, x, y, w, h, role, s=None, size=11, family="serif", italic=True):
        """Stored data (history, dataset)."""
        p = PAL[role]
        ry = min(6.0, h * 0.18)
        cid = self.uid("cy")
        self.add(
            f'<path data-box="{cid}" data-kind="card" d="M{x} {y + ry}A{w / 2} {ry} 0 0 1 {x + w} {y + ry}V{y + h - ry}'
            f'A{w / 2} {ry} 0 0 1 {x} {y + h - ry}Z" fill="{p.tint}" stroke="{p.accent}" stroke-width="1"/>'
        )
        self.add(f'<path d="M{x} {y + ry}A{w / 2} {ry} 0 0 0 {x + w} {y + ry}" fill="none" stroke="{p.accent}" stroke-width="1"/>')
        if s:
            self.text(x + w / 2, y + h / 2 + ry / 2 + size * 0.36, s, size=size, color=p.deep, anchor="middle", box=cid,
                      family=family, italic=italic)
        return cid

    def block_arrow(self, x1, y1, x2, y2, width=12, color="#D6D2C4", head=None):
        """Thick chevron arrow for a stage transition (horizontal or vertical)."""
        head = head or width * 1.25
        if abs(y2 - y1) < 1e-6:
            s = 1 if x2 > x1 else -1
            xb = x2 - s * head
            pts = f"{x1},{y1 - width / 2} {xb},{y1 - width / 2} {xb},{y1 - width} {x2},{y1} {xb},{y1 + width} {xb},{y1 + width / 2} {x1},{y1 + width / 2}"
        else:
            s = 1 if y2 > y1 else -1
            yb = y2 - s * head
            pts = f"{x1 - width / 2},{y1} {x1 - width / 2},{yb} {x1 - width},{yb} {x1},{y2} {x1 + width},{yb} {x1 + width / 2},{yb} {x1 + width / 2},{y1}"
        self.add(f'<polygon points="{pts}" fill="{color}"/>')

    def bubble(self, x, y, w, h, s, role="gray", size=12, tail="left", family="serif", italic=True, weight=400, stroke=None):
        """Speech bubble for language (instructions, model utterances)."""
        p = PAL[role]
        r = 8
        cy = y + h / 2
        if tail == "left":
            d = (f"M{x + r} {y}H{x + w - r}A{r} {r} 0 0 1 {x + w} {y + r}V{y + h - r}A{r} {r} 0 0 1 {x + w - r} {y + h}"
                 f"H{x + r}A{r} {r} 0 0 1 {x} {y + h - r}V{cy + 5}L{x - 9} {cy}L{x} {cy - 5}V{y + r}A{r} {r} 0 0 1 {x + r} {y}Z")
        else:
            d = (f"M{x + r} {y}H{x + w - r}A{r} {r} 0 0 1 {x + w} {y + r}V{y + h - r}A{r} {r} 0 0 1 {x + w - r} {y + h}"
                 f"H{x + r}A{r} {r} 0 0 1 {x} {y + h - r}V{y + r}A{r} {r} 0 0 1 {x + r} {y}Z")
        cid = self.uid("bb")
        self.add(f'<path data-box="{cid}" data-kind="card" d="{d}" fill="#FFFFFF" stroke="{stroke or p.accent}" stroke-width="1.1"/>')
        self.text(x + w / 2, cy + size * 0.36, s, size=size, color=p.deep, anchor="middle", box=cid, family=family,
                  italic=italic, weight=weight)
        return cid

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
        self.defs[clip] = f'<clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2"/></clipPath>'
        self.add(f'<g clip-path="url(#{clip})"><use href="#scene" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"/></g>')
        self.add(f'<rect data-box="{cid}" data-kind="thumb" x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="none" '
                 f'stroke="{frame or "#B9B4A8"}" stroke-width="1"/>')
        return cid

    def arrow(self, d, color=WIRE, sw=1.3, dashed=False, start=False, end=True, head=7.0, opacity=None, open_=False):
        mk = self._marker(color, head, open_)
        attrs = f'd="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
        if dashed:
            attrs += ' stroke-dasharray="4 3"'
        if end:
            attrs += f' marker-end="url(#{mk})"'
        if start:
            attrs += f' marker-start="url(#{mk})"'
        if opacity is not None:
            attrs += f' stroke-opacity="{opacity}"'
        self.add(f"<path {attrs}/>")

    def dot(self, x, y, color=WIRE, r=2.4):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

    def brace(self, x, y1, y2, color=FAINT, depth=12, sw=1.2):
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
    def bars(self, x, y, w, h, values, color, gap=2.0, base="#B9B4A8", box=None):
        n = len(values)
        bw = (w - gap * (n - 1)) / n
        self.line(f"M{x} {y + h}H{x + w}", base, 1)
        for i, v in enumerate(values):
            bh = max(1.5, v * h)
            self.add(f'<rect x="{x + i * (bw + gap):.1f}" y="{y + h - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                     f'fill="{color}" opacity="{0.5 + 0.4 * v:.2f}"/>')

    def curves(self, x, y, w, h, colors, seed=1.0, grid=True, n=60, sw=1.4):
        if grid:
            for k in range(1, 4):
                self.line(f"M{x} {y + h * k / 4:.1f}H{x + w}", "#ECEAE4", 0.8)
            self.line(f"M{x} {y}V{y + h}H{x + w}", "#9C968A", 0.9)
        for j, c in enumerate(colors):
            pts = []
            for i in range(n + 1):
                t = i / n
                v = 0.5 + 0.28 * math.sin(2.2 * t * math.pi + seed * (j + 1) * 1.7) + 0.12 * math.sin(5.3 * t * math.pi + j * 0.9 + seed)
                pts.append(f"{x + t * w:.1f} {y + (1 - v) * h:.1f}")
            self.add(f'<path d="M{"L".join(pts)}" fill="none" stroke="{c}" stroke-width="{sw}" stroke-linecap="round"/>')

    def strip(self, x, y, w, h, n, lit, color, off="#ECEAE4", gap=1.0):
        cw = (w - gap * (n - 1)) / n
        for i in range(n):
            fill = color if i < lit else off
            self.add(f'<rect x="{x + i * (cw + gap):.2f}" y="{y}" width="{cw:.2f}" height="{h}" rx="0.6" fill="{fill}"/>')
