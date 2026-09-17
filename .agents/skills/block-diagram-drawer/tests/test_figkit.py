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


def label_markup(fig, s: str) -> str:
    """The <text> element whose content is `s` (figkit wraps label runs in tspans)."""
    return next(m for m in re.findall(r"<text[^>]*>.*?</text>", fig.svg()) if f">{s}<" in m)


class LayoutTests(unittest.TestCase):
    def test_columns_and_rows_are_exact_and_snapped(self) -> None:
        f = figkit.Fig(1400, 500)
        cols = f.cols(8, 1392, 4, 12)
        self.assertEqual([x for x, _ in cols], [8, 357, 706, 1055])
        self.assertEqual({w for _, w in cols}, {337})
        gaps = [cols[i + 1][0] - (cols[i][0] + cols[i][1]) for i in range(3)]
        self.assertEqual(set(gaps), {12})
        self.assertEqual(f.rows(0, 100, 2, 10), [(0, 45), (55, 45)])
        with self.assertRaises(ValueError):
            f.cols(0, 50, 5, 20)

    def test_place_centers_a_run_of_widths(self) -> None:
        f = figkit.Fig(1400, 500)
        self.assertEqual(f.place(0, 600, [100, 120, 80], gap=20), [130, 250, 390])

    def test_containers_register_their_rectangle(self) -> None:
        f = figkit.Fig(1400, 500)
        card = f.card(10, 20, 100, 40, "blue")
        chip = f.chip(200, 30, 60, 24, "x", "gray")
        self.assertEqual(f.rect(card), (10, 20, 100, 40))
        self.assertEqual(f.rect(chip), (200, 30, 60, 24))
        with self.assertRaises(KeyError):
            f.rect("nope")

    def test_ports_sit_on_the_edges(self) -> None:
        f = figkit.Fig(1400, 500)
        card = f.card(100, 100, 200, 60, "blue")
        self.assertEqual(f.port(card, "left"), (100, 130))
        self.assertEqual(f.port(card, "right", out=2), (302, 130))
        self.assertEqual(f.port(card, "top", t=0.25), (150, 100))
        self.assertEqual(f.port(card, "bottom"), (200, 160))
        with self.assertRaises(ValueError):
            f.port(card, "middle")

    def test_connect_anchors_on_edges_and_elbows_when_offset(self) -> None:
        f = figkit.Fig(1400, 500)
        a = f.card(40, 100, 200, 60, "blue")
        b = f.card(400, 100, 200, 60, "green")
        c = f.card(400, 300, 200, 60, "amber")
        self.assertEqual(f.connect(a, b), "M241.0 130.0H399.0")
        self.assertEqual(f.connect(a, c, mid=320), "M241.0 130.0H320.0V330.0H399.0")
        self.assertEqual(f.connect(b, c), "M500.0 161.0V299.0")
        f.connect(a, b, label="then")
        self.assertIn(">then<", f.svg())

    def test_bus_forks_through_one_trunk(self) -> None:
        f = figkit.Fig(1400, 500)
        src = f.card(40, 40, 200, 60, "blue")
        targets = [f.card(400, 200 + 80 * k, 160, 50, "purple") for k in range(3)]
        trunk = f.bus(src, targets, side="bottom")
        svg = f.svg()
        self.assertEqual(trunk, 150)
        for top in ("V199.0", "V279.0", "V359.0"):
            self.assertIn(top, svg)
        self.assertIn("H480.0", svg)  # one trunk spanning the targets

    def test_arc_bends_to_one_side(self) -> None:
        f = figkit.Fig(1400, 500)
        a = f.card(40, 40, 120, 40, "blue")
        b = f.card(600, 40, 120, 40, "green")
        cx, cy = f.arc(a, b, bulge=50)
        self.assertAlmostEqual(cx, 380.0, places=1)
        self.assertAlmostEqual(cy, 110.0, places=1)
        self.assertIn("Q380.0 110.0", f.svg())

    def test_arc_label_sits_outside_the_bend(self) -> None:
        f = figkit.Fig(1400, 500)
        a = f.card(40, 40, 120, 40, "blue")
        b = f.card(600, 40, 120, 40, "green")
        f.arc(a, b, bulge=60, label="retry", label_size=16)
        apex_y = 90.0  # midpoint y 60, control y 120, so the curve peaks at 90
        y = float(re.search(r'y="([\d.]+)"', label_markup(f, "retry")).group(1))
        self.assertGreater(y, apex_y + 10)  # below the apex, never on the curve

    def test_arc_label_flips_inward_at_the_canvas_edge(self) -> None:
        f = figkit.Fig(600, 500)
        a = f.card(500, 400, 80, 40, "blue")
        b = f.card(500, 60, 80, 40, "green")
        f.arc(a, b, sides=("right", "right"), bulge=30, label="next", label_size=16)
        x = float(re.search(r'x="([\d.]+)"', label_markup(f, "next")).group(1))
        self.assertLess(x, 581)  # the outside would leave the canvas, so the label moves inward

    def test_route_wraps_through_its_lanes(self) -> None:
        f = figkit.Fig(1400, 600)
        a = f.card(100, 400, 200, 60, "blue")
        b = f.card(100, 60, 200, 60, "green")
        self.assertEqual(f.route(a, b, (520, 60), sides=("bottom", "left")),
                         "M200.0 461.0V520.0H60.0V90.0H99.0")
        self.assertEqual(f.route(a, b, (360,), sides=("right", "right")),
                         "M301.0 430.0H360.0V90.0H301.0")

    def test_route_labels_the_segment_asked_for(self) -> None:
        f = figkit.Fig(1400, 600)
        a = f.card(100, 400, 200, 60, "blue")
        b = f.card(100, 60, 200, 60, "green")
        f.route(a, b, (520, 60), sides=("bottom", "left"), label="back", label_seg=1, label_size=16)
        y = float(re.search(r'y="([\d.]+)"', label_markup(f, "back")).group(1))
        self.assertAlmostEqual(y, 513.0, places=1)  # above the lane at y 520

    def test_zone_anchors_connectors_without_drawing(self) -> None:
        f = figkit.Fig(1400, 500)
        z = f.zone(100, 100, 200, 60)
        card = f.card(500, 100, 200, 60, "blue")
        self.assertEqual(f.rect(z), (100, 100, 200, 60))
        self.assertEqual(f.connect(z, card), "M301.0 130.0H499.0")
        self.assertNotIn(z, f.svg())


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

    def test_strict_tidy_turns_geometry_reports_into_failures(self) -> None:
        clean = self.report(tidy={key: [] for key in qa.TIDY_CHECKS})
        self.assertEqual(qa.failures(clean, 0.4, strict_tidy=True), [])
        sloppy = self.report(tidy={**{key: [] for key in qa.TIDY_CHECKS}, "edgeGap": [{"gap": 6}], "misalign": [{"spread": 3}]})
        self.assertEqual(qa.failures(sloppy, 0.4), [])
        self.assertEqual(qa.failures(sloppy, 0.4, strict_tidy=True), ["tidy.edgeGap=1", "tidy.misalign=1"])

    def test_word_budget_is_enforced(self) -> None:
        self.assertEqual(qa.failures(self.report(words=40, wordBudget=56), 0.4), [])
        self.assertEqual(qa.failures(self.report(words=90, wordBudget=56), 0.4), ["words=90 > budget 56"])

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
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "small.svg"
            f.save(str(path))
            report = qa.measure(path, _browser_or_none())
            relaxed = qa.measure(path, _browser_or_none(), min_font=9)
        self.assertEqual([item["s"] for item in report["smallText"]], ["tiny annotation"])
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
            tight = qa.measure(path, _browser_or_none(), words_per_10k=0.02)
        self.assertEqual([item["words"] for item in report["longText"]], [7])
        self.assertEqual(report["words"], 9)
        self.assertEqual(report["wordBudget"], 42)
        self.assertIn("words=9 > budget 1", qa.failures(tight, 0.0))

    @unittest.skipUnless(_browser_or_none(), "Chrome/Chromium/Edge not available")
    def test_browser_reports_sloppy_geometry(self) -> None:
        f = figkit.Fig(1400, 300)
        a = f.card(40, 60, 200, 60, "blue")
        f.card(300, 63, 200, 60, "green")  # top off by 3 px
        c = f.card(560, 60, 200, 60, "amber")
        f.card(860, 60, 200, 60, "purple")  # uneven gap
        f.arrow("M245 90H292", "#333", 1.4)  # stops short of the next card
        tidy_arrow = f.connect(a, c, ta=0.5, tb=0.5)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sloppy.svg"
            f.save(str(path))
            report = qa.measure(path, _browser_or_none())
        tidy = report["tidy"]
        self.assertIn("M241.0 90.0H559.0", tidy_arrow)
        self.assertTrue(any(item["issue"] == "short of the edge" for item in tidy["edgeGap"]))
        self.assertTrue(any(item["axis"] == "top" and item["spread"] == 3 for item in tidy["misalign"]))
        self.assertTrue(any(item["kind"] == "row" for item in tidy["gapUneven"]))
        self.assertEqual(qa.failures(report, 0.0, strict_tidy=True) and True, True)

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
