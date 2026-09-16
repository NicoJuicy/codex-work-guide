from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


figkit = _load("figkit")
qa = _load("qa_svg_figure")


def _browser_or_none() -> str | None:
    try:
        return qa.find_browser()
    except SystemExit:
        return None


class MathMarkupTests(unittest.TestCase):
    def test_unbraced_command_subscript_is_one_token(self) -> None:
        out = figkit.rich("$E_\\theta$", 12)
        self.assertIn("θ", out)
        self.assertIn(">E<", out)

    def test_relations_are_spaced_only_at_base_level(self) -> None:
        out = figkit.rich("$a=b_{c=d}$", 12)
        self.assertIn(" = ", out)
        self.assertEqual(out.count(" = "), 1)

    def test_hyphen_becomes_minus_sign(self) -> None:
        self.assertIn("−", figkit.rich("$a_{t-1}$", 12))

    def test_baseline_is_restored_after_scripts(self) -> None:
        out = figkit.rich("x $a_t^{2}$ y", 12)
        total = sum(float(v) for v in re.findall(r'dy="(-?[0-9.]+)"', out))
        self.assertAlmostEqual(total, 0.0, places=6)

    def test_prime_calligraphic_and_blackboard(self) -> None:
        out = figkit.rich("$a'_t\\in\\mathcal{L}\\times\\mathbb{R}$", 12)
        for glyph in ("′", "ℒ", "ℝ", "×"):
            self.assertIn(glyph, out)

    def test_accent_attaches_combining_mark(self) -> None:
        atoms, _ = figkit._parse("\\hat{\\tau}")
        self.assertEqual(atoms[0]["t"], "τ̂")

    def test_plain_text_is_escaped(self) -> None:
        self.assertIn("&lt;b&gt;", figkit.rich("<b>", 12))


class FigureTests(unittest.TestCase):
    def build(self) -> figkit.Fig:
        f = figkit.Fig(400, 200)
        top = f.panel(4, 4, 392, 192, "blue", "(a) Stage", sub="subtitle")
        self.assertEqual(top, 38)
        card = f.card(12, 60, 150, 120, "green", stack=1, topbar=True)
        f.text(20, 80, "Card $x_t$", box=card)
        f.chip(20, 90, 60, 20, "chip", "purple")
        f.badge(90, 90, "12%", "red")
        f.pill(120, 150, "loop", "gray")
        f.icon("spark", 20, 120, 18, "#000")
        f.icon("spark", 40, 120, 18, "#000")
        f.scene(200, 60, 80, 60, frame="#333")
        f.arrow("M170 100H190", "#123456")
        f.arrow("M170 110H190", "#123456", dashed=True)
        f.brace(290, 60, 180)
        f.bars(300, 60, 80, 40, [0.2, 0.8, 0.5], "#999")
        f.curves(300, 110, 80, 40, ["#111", "#222"])
        f.strip(300, 160, 80, 10, 10, 3, "#0A0")
        return f

    def test_svg_is_well_formed(self) -> None:
        root = ET.fromstring(self.build().svg())
        self.assertTrue(root.tag.endswith("svg"))

    def test_markers_and_symbols_are_deduplicated(self) -> None:
        svg = self.build().svg()
        self.assertEqual(svg.count('id="ah1234567"'), 1)
        self.assertEqual(svg.count('id="i-spark"'), 1)

    def test_text_is_linked_to_its_container(self) -> None:
        svg = self.build().svg()
        box_ids = set(re.findall(r'data-box="([^"]+)"', svg))
        linked = set(re.findall(r'data-in="([^"]+)"', svg))
        self.assertTrue(linked)
        self.assertTrue(linked <= box_ids)

    def test_headerless_panel(self) -> None:
        f = figkit.Fig(100, 60)
        self.assertEqual(f.panel(0, 0, 100, 60, "gray", None), 10)

    def test_subtitle_below_reserves_second_line(self) -> None:
        f = figkit.Fig(200, 100)
        self.assertEqual(f.panel(0, 0, 200, 100, "gray", "(a) Inputs", sub="narrow panel", sub_below=True), 48)

    def test_default_font_is_inherited_so_family_attributes_win(self) -> None:
        f = figkit.Fig(200, 60)
        f.text(10, 20, "obs", family="serif", italic=True)
        f.text(10, 40, "accept", family="mono")
        svg = f.svg()
        self.assertNotRegex(svg, r"text\{[^}]*font-family")
        root = ET.fromstring(svg)
        self.assertIn("Helvetica", root.get("font-family", ""))
        families = [el.get("font-family", "") for el in root.iter() if el.tag.endswith("text")]
        self.assertTrue(any("STIX" in fam for fam in families))
        self.assertTrue(any("Menlo" in fam for fam in families))

    def test_meaningful_shapes_are_well_formed(self) -> None:
        f = figkit.Fig(400, 200)
        f.tokens(10, 10, 6, "blue", lit=4, to_role="amber")
        f.trapezoid(10, 30, 80, 40, "blue", "$E_\\theta$")
        f.bracket(100, 30, 80, 40)
        f.cylinder(200, 30, 50, 40, "green", "$h_t$")
        f.bubble(270, 30, 100, 30, "“fold shirt”")
        f.step(20, 120, 3)
        f.block_arrow(40, 120, 120, 120, width=10)
        f.block_arrow(200, 100, 200, 180, width=10)
        f.card(250, 100, 100, 60, "amber", key=True)
        root = ET.fromstring(f.svg())
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn('stroke="#1F1F1F"', f.svg())

    def test_palette_aliases_share_roles(self) -> None:
        self.assertIs(figkit.PAL["teal"], figkit.PAL["blue"])
        self.assertIs(figkit.PAL["ochre"], figkit.PAL["amber"])
        for role in figkit.PAL.values():
            for color in (role.accent, role.tint, role.deep, role.mid):
                self.assertRegex(color, r"^#[0-9A-F]{6}$")


class QaGateTests(unittest.TestCase):
    def report(self, **overrides) -> dict:
        base = {key: [] for key in qa.CHECKS}
        base["coverage"] = 0.7
        base.update(overrides)
        return base

    def test_clean_report_passes(self) -> None:
        self.assertEqual(qa.failures(self.report(), 0.55), [])

    def test_any_issue_or_low_coverage_fails(self) -> None:
        self.assertEqual(qa.failures(self.report(lineText=[["a", "M0 0"]]), 0.55), ["lineText=1"])
        self.assertEqual(qa.failures(self.report(coverage=0.3), 0.55), ["coverage=0.3 < 0.55"])

    @unittest.skipUnless(_browser_or_none(), "Chrome/Chromium/Edge not available")
    def test_browser_detects_overflow_and_line_through_label(self) -> None:
        f = figkit.Fig(300, 120)
        card = f.card(10, 10, 80, 40, "blue")
        f.text(20, 34, "this label is far too long for its card", size=12, box=card)
        f.text(150, 92, "label", size=14)
        f.line("M140 88H220", "#000", 1.5)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.svg"
            f.save(str(path))
            report = qa.measure(path, _browser_or_none())
        self.assertEqual(len(report["overflow"]), 1)
        self.assertEqual(len(report["lineText"]), 1)

    @unittest.skipUnless(_browser_or_none(), "Chrome/Chromium/Edge not available")
    def test_browser_applies_monospace_family(self) -> None:
        # Narrow glyphs fit a 60 px box in sans; the same string only overflows if monospace really renders.
        f = figkit.Fig(300, 120)
        sans_box = f.card(10, 10, 60, 30, "gray")
        f.text(15, 30, "iiiiiiiiii", size=14, box=sans_box)
        mono_box = f.card(10, 60, 60, 30, "gray")
        f.text(15, 80, "iiiiiiiiii", size=14, box=mono_box, family="mono")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fonts.svg"
            f.save(str(path))
            report = qa.measure(path, _browser_or_none())
        self.assertEqual(len(report["overflow"]), 1)


if __name__ == "__main__":
    unittest.main()
