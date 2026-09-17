from __future__ import annotations

import base64
import importlib.util
import re
import subprocess
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

    def test_set_and_mapping_notation(self) -> None:
        out = figkit.rich("$\\kappa: V\\to\\mathcal{C},\\ \\mathrm{pre}(c)\\subseteq F_t,\\ \\langle\\theta,\\ldots\\rangle,\\ \\mathcal{B}\\subseteq\\mathcal{C}\\times\\Pi$", 12)
        for glyph in ("κ", "𝒞", "⊆", "⟨", "…", "⟩", "ℬ", "Π"):
            self.assertIn(glyph, out)
        self.assertIn("\u2005⊆\u2005", out)

    def test_accent_attaches_combining_mark(self) -> None:
        atoms, _ = figkit._parse("\\hat{\\tau}")
        self.assertEqual(atoms[0]["t"], "τ̂")

    def test_plain_text_is_escaped(self) -> None:
        self.assertIn("&lt;b&gt;", figkit.rich("<b>", 12))


class FigureTests(unittest.TestCase):
    def build(self) -> figkit.Fig:
        f = figkit.Fig(400, 200)
        top = f.panel(4, 4, 392, 192, "blue", "(a) Stage", sub="subtitle", title_size=15)
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
        self.assertEqual(f.panel(0, 0, 200, 100, "gray", "(a) Inputs", sub="narrow panel", sub_below=True, title_size=15), 48)

    def test_font_sizes_follow_the_print_width(self) -> None:
        wide, column = figkit.Fig(1400, 400), figkit.Fig(700, 400)
        self.assertEqual(wide.print_width_pt, figkit.TEXT_WIDTH_PT)
        self.assertEqual(column.print_width_pt, figkit.COLUMN_WIDTH_PT)
        self.assertAlmostEqual(wide.fs("min"), 16.3, places=1)
        self.assertAlmostEqual(column.fs("label"), 18.6, places=1)
        self.assertAlmostEqual(figkit.Fig(1400, 400, print_width_pt=252).fs("label"), 37.2, places=1)
        wide.text(10, 30, "label")
        svg = wide.svg()
        self.assertIn('font-size="18.2"', svg)
        self.assertEqual(ET.fromstring(svg).get("data-print-width-pt"), "516")

    def test_study_conventions_render(self) -> None:
        f = figkit.Fig(1400, 400)
        f.mark("frozen", 10, 10)
        f.mark("trainable", 40, 10)
        f.outcome(70, 10, ok=False)
        f.divider(700, 10, 390)
        f.stage_ruler([(20, 300, "Pretraining", "blue"), (320, 600, "Finetuning", None)], 380)
        f.zoom((100, 100, 80, 40), (100, 200, 300, 120))
        f.callout(500, 100, 600, 80, "gripper")
        f.hourglass(800, 100, 120, 90, "purple", "U-Net")
        f.text(10, 300, "224x224", note=True)
        svg = f.svg()
        ET.fromstring(svg)
        for token in ('id="i-snowflake"', 'id="i-flame"', 'id="i-x"', 'data-tier="note"', 'font-size="14.9"', ">Finetuning<"):
            self.assertIn(token, svg)
        serif = figkit.Fig(700, 200, family="serif")
        serif.text(10, 20, "inherits serif")
        serif.text(10, 50, "explicit sans", family="sans")
        root = ET.fromstring(serif.svg())
        self.assertIn("STIX", root.get("font-family"))
        self.assertIn("Helvetica", serif.svg().split("explicit sans")[0].rsplit("<text", 1)[1])
        with self.assertRaises(ValueError):
            figkit.Fig(100, 100, family="mono")

    def test_example_cards_and_bubbles_are_marked(self) -> None:
        f = figkit.Fig(400, 200)
        f.example(10, 10, 200, 60)
        f.bubble(10, 100, 200, 40, "Set the table")
        self.assertEqual(f.svg().count('data-kind="example"'), 2)

    def test_image_embeds_raster_bytes(self) -> None:
        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==")
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "render.png"
            good.write_bytes(png)
            fake = Path(tmp) / "fake.png"
            fake.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            f = figkit.Fig(400, 200)
            f.image(good, 10, 10, 120, 80)
            svg = f.svg()
            self.assertIn('href="data:image/png;base64,', svg)
            self.assertIn('data-kind="thumb"', svg)
            ET.fromstring(svg)
            with self.assertRaises(ValueError):
                f.image(fake, 10, 10, 120, 80)
            old = figkit.MAX_IMAGE_BYTES
            figkit.MAX_IMAGE_BYTES = 10
            try:
                with self.assertRaises(ValueError):
                    f.image(good, 10, 10, 120, 80)
            finally:
                figkit.MAX_IMAGE_BYTES = old

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


TABLER_LIKE = """<!-- tags: [focus] -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon">
  <title>target</title>
  <path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
</svg>"""

GRADIENT_LOGO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 24" height="1em" style="flex:none">
<defs><linearGradient id="a"><stop offset="0" stop-color="#000"/></linearGradient></defs>
<path fill="url(#a)" d="M0 0h48v24H0z"/><use href="#a"/></svg>"""


class SvgAssetTests(unittest.TestCase):
    def write(self, tmp: str, name: str, text: str) -> Path:
        path = Path(tmp) / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_symbol_is_shared_and_stroke_is_normalized_per_use(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            icon = self.write(tmp, "target.svg", TABLER_LIKE)
            f = figkit.Fig(200, 60)
            box = f.asset(icon, 10, 10, 16, color="#7A5506")
            f.asset(icon, 40, 10, 24)
            svg = f.svg()
        root = ET.fromstring(svg)
        symbols = [el for el in root.iter() if el.tag.endswith("symbol")]
        self.assertEqual(len(symbols), 1)
        group = symbols[0][0]
        self.assertEqual(group.get("stroke"), "currentColor")
        self.assertIsNone(group.get("stroke-width"))
        self.assertNotIn("<title>", svg)
        uses = [el for el in root.iter() if el.tag.endswith("use")]
        self.assertEqual([u.get("stroke-width") for u in uses], ["2.250", "1.500"])
        self.assertEqual(uses[0].get("color"), "#7A5506")
        self.assertIn(f'data-box="{box}" data-kind="icon"', svg)

    def test_ids_are_namespaced_and_aspect_is_kept(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            logo = self.write(tmp, "logo.svg", GRADIENT_LOGO)
            f = figkit.Fig(200, 60)
            f.asset(logo, 0, 0, 40)
            svg = f.svg()
        ids = re.findall(r'<linearGradient id="([^"]+)"', svg)
        self.assertEqual(len(ids), 1)
        self.assertTrue(ids[0].startswith("logo-") and ids[0].endswith("-a"))
        self.assertIn(f'fill="url(#{ids[0]})"', svg)
        self.assertIn(f'href="#{ids[0]}"', svg)
        self.assertIn('height="20.00"', svg)
        ET.fromstring(svg)

    def test_unsafe_or_invalid_svg_is_rejected(self) -> None:
        bad = {
            "script": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><script>alert(1)</script></svg>',
            "handler": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" onload="x()"/>',
            "remote": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use href="https://e.com/a.svg#b"/></svg>',
            "css": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><style>text{fill:red}</style></svg>',
            "entity": '<!DOCTYPE svg [<!ENTITY a "b">]><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"/>',
            "no-viewbox": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"/>',
            "not-svg": '<html xmlns="http://www.w3.org/1999/xhtml"/>',
        }
        for name, text in bad.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                figkit.parse_svg_asset(text, f"{name}.svg")


class QaGateTests(unittest.TestCase):
    def report(self, **overrides) -> dict:
        base = {key: [] for key in qa.CHECKS}
        base["coverage"] = 0.7
        base.update(overrides)
        return base

    def test_clean_report_passes(self) -> None:
        self.assertEqual(qa.failures(self.report()), [])
        self.assertEqual(qa.warnings(self.report()), [])

    def test_any_issue_or_low_coverage_fails(self) -> None:
        self.assertEqual(qa.failures(self.report(lineText=[["a", "M0 0"]])), ["lineText=1"])
        self.assertEqual(qa.failures(self.report(coverage=0.3)), ["coverage=0.3 < 0.4"])

    def test_study_thresholds_fail_and_warn(self) -> None:
        base = {"size": [1400, 583], "printWidthPt": 516, "words": 40, "exampleWords": 0, "medianPt": 6.9, "fillHues": 3,
                "maxNesting": 1, "boldShare": 0.1, "contrastWarn": []}
        report = self.report(**base)
        report["wordWarn"], report["wordFail"] = qa.word_budget(report, qa.Limits())
        self.assertEqual((report["wordWarn"], report["wordFail"]), (65, 90))
        self.assertEqual(qa.failures(report), [])
        noisy = dict(report, words=80, medianPt=5.5, exampleWords=45, fillHues=6, maxNesting=3, boldShare=0.5)
        self.assertEqual(qa.failures(noisy), [])
        self.assertEqual(len(qa.warnings(noisy)), 6)
        broken = dict(report, words=120, medianPt=4.2, exampleWords=90)
        self.assertEqual(qa.failures(broken), ["medianPt=4.2 < 5.0", "words=120 > 90", "exampleWords=90 > 60"])

    def test_word_budget_scales_with_printed_area(self) -> None:
        limits = qa.Limits()
        tall = {"size": [1400, 1000], "printWidthPt": 516}
        column = {"size": [700, 500], "printWidthPt": 252}
        self.assertEqual(qa.word_budget(tall, limits), (104, 144))
        self.assertEqual(qa.word_budget(column, limits), (32, 45))

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
    def test_browser_flags_small_labels_but_not_math_scripts(self) -> None:
        f = figkit.Fig(1400, 120)
        f.text(20, 40, "tiny annotation", size=12.5)
        f.text(20, 80, "readable $a_t^{2}$ label", size=18)
        f.text(400, 40, "224x224", note=True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "small.svg"
            f.save(str(path))
            report = qa.measure(path, _browser_or_none())
            relaxed = qa.measure(path, _browser_or_none(), qa.Limits(min_px=9))
        self.assertEqual([item["s"] for item in report["smallText"]], ["tiny annotation"])
        self.assertFalse(any(item["note"] for item in report["smallText"]))
        self.assertEqual(relaxed["smallText"], [])

    @unittest.skipUnless(_browser_or_none(), "Chrome/Chromium/Edge not available")
    def test_browser_flags_sentences_outside_example_content(self) -> None:
        f = figkit.Fig(1400, 300)
        f.text(20, 40, "every navigate node uses the same contract")
        f.text(20, 80, "Skill graph")
        note = f.example(20, 120, 900, 60)
        f.text(30, 160, "Pick up the apple and place it on the table", box=note)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "words.svg"
            f.save(str(path))
            report = qa.measure(path, _browser_or_none())
            tight = qa.measure(path, _browser_or_none(), qa.Limits(word_fail=2))
        self.assertEqual([item["words"] for item in report["longText"]], [7])
        self.assertEqual((report["words"], report["exampleWords"]), (9, 10))
        self.assertEqual(report["wordFail"], 46)
        self.assertIn("words=9 > 1", qa.failures(tight, qa.Limits(min_coverage=0)))

    @unittest.skipUnless(_browser_or_none(), "Chrome/Chromium/Edge not available")
    def test_browser_reports_contrast_hues_nesting_and_median(self) -> None:
        f = figkit.Fig(1400, 300)
        outer = f.card(10, 10, 600, 280, "gray")
        mid = f.card(20, 20, 400, 200, "blue")
        inner = f.card(30, 30, 300, 100, "green")
        f.chip(40, 40, 120, 40, "deep", "purple")
        f.text(200, 70, "pale label", color="#E3EEDA", box=inner)
        for k, role in enumerate(("red", "amber", "orange")):
            f.card(700 + 120 * k, 20, 100, 60, role)
        f.text(40, 260, "median label", box=outer)
        f.text(300, 260, "second label", box=outer)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "style.svg"
            f.save(str(path))
            report = qa.measure(path, _browser_or_none())
        self.assertEqual([item["s"] for item in report["lowContrast"]], ["pale label"])
        self.assertGreaterEqual(report["fillHues"], 6)
        self.assertEqual(report["maxNesting"], 3)
        self.assertAlmostEqual(report["medianPt"], 6.7, delta=0.1)
        self.assertTrue(any(w.startswith("maxNesting") for w in qa.warnings(report)))
        del mid

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


class ScaffoldTests(unittest.TestCase):
    def test_scaffold_vendors_kit_and_writes_a_runnable_script(self) -> None:
        scaffold = _load("scaffold")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "figures" / "src" / "fig_demo_pipeline.py"
            written = scaffold.scaffold(target, 1400, 400, 3, force=False, update_kit=False)
            self.assertIn(target, written)
            for name in ("figkit.py", "qa_svg_figure.py"):
                self.assertTrue((target.parent / name).exists())
            subprocess.run([sys.executable, str(target)], cwd=target.parent, check=True, capture_output=True)
            svg = target.parent.parent / "demo_pipeline-figure.svg"
            self.assertTrue(ET.parse(svg).getroot().tag.endswith("svg"))
            with self.assertRaises(SystemExit):
                scaffold.scaffold(target, 1400, 400, 3, force=False, update_kit=False)


if __name__ == "__main__":
    unittest.main()
