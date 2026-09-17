from __future__ import annotations

import base64
import importlib.util
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("svg2drawio", SCRIPTS / "svg2drawio.py")
assert SPEC and SPEC.loader
svg2drawio = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = svg2drawio
SPEC.loader.exec_module(svg2drawio)

import figkit
import qa_svg_figure as qa


def _browser_or_none() -> str | None:
    try:
        return qa.find_browser()
    except SystemExit:
        return None


def span(text: str, family: str = "Helvetica", off: float = 0.0) -> dict:
    return {"t": text, "ff": family, "fs": 12, "fw": "400", "fst": "normal", "fill": "rgb(31, 31, 31)", "off": off}


class ParsingTests(unittest.TestCase):
    def test_path_points_handles_orthogonal_segments_and_subpaths(self) -> None:
        self.assertEqual(svg2drawio.path_points("M10 20H30V40M5 5L6 7"), [[(10, 20), (30, 20), (30, 40)], [(5, 5), (6, 7)]])

    def test_colors_and_markers(self) -> None:
        self.assertEqual(svg2drawio.hex_color("rgb(59, 142, 165)"), "#3B8EA5")
        self.assertEqual(svg2drawio.hex_color("rgba(0, 0, 0, 0)"), "none")
        self.assertIn("endArrow=open", svg2drawio.marker_style("url(#ah3A3A3A7o)", "end"))
        self.assertIn("startArrow=block", svg2drawio.marker_style("url(#ah3A3A3A6)", "start"))
        self.assertEqual(svg2drawio.marker_style(None, "end"), ["endArrow=none"])

    def test_script_offsets_become_vertical_align(self) -> None:
        self.assertIn("vertical-align:-3px", svg2drawio.span_html(span("t", off=3)))


class ConvertTests(unittest.TestCase):
    def data(self) -> dict:
        chip = {"kind": "rect", "x": 10, "y": 10, "w": 80, "h": 20, "rx": 3, "fill": "rgb(255, 255, 255)", "stroke": "rgb(0, 0, 0)",
                "sw": 1, "dash": "none", "fo": 1, "so": 1, "op": 1, "box": "c1", "bkind": "chip"}
        offset_chip = dict(chip, y=40, box="c2")
        # a tall card with an icon above a horizontally centered caption
        captioned = dict(chip, x=100, y=10, h=60, box="c3")
        return {"W": 200, "H": 100, "items": [
            chip, {"kind": "text", "x": 30, "y": 13, "w": 40, "h": 14, "anchor": "middle", "spans": [span("pick")], "din": "c1"},
            offset_chip, {"kind": "text", "x": 44, "y": 43, "w": 40, "h": 14, "anchor": "middle", "spans": [span("all")], "din": "c2"},
            captioned, {"kind": "text", "x": 120, "y": 52, "w": 40, "h": 14, "anchor": "middle", "spans": [span("sim")], "din": "c3"},
            {"kind": "path", "d": "M10 80H100V90", "stroke": "rgb(58, 58, 58)", "sw": 1.3, "dash": "4px, 3px",
             "ms": None, "me": "url(#ah3A3A3A7)", "so": 1, "op": 1},
            {"kind": "image", "x": 150, "y": 10, "w": 20, "h": 20, "svg": "<svg xmlns='http://www.w3.org/2000/svg'/>"},
        ]}

    def test_centered_chip_label_merges_and_offset_label_stays_free(self) -> None:
        root = svg2drawio.convert(self.data(), "t").getroot()
        cells = root.findall(".//mxCell")
        chips = [c for c in cells if "rounded=1" in c.get("style", "")]
        self.assertIn("pick", chips[0].get("value"))
        self.assertEqual(chips[1].get("value"), "")
        self.assertEqual(chips[2].get("value"), "")
        for word in ("all", "sim"):
            self.assertTrue(any(c.get("style", "").startswith("text;") and word in c.get("value") for c in cells))

    def test_edges_keep_waypoints_arrows_and_dashes(self) -> None:
        root = svg2drawio.convert(self.data(), "t").getroot()
        edge = next(c for c in root.findall(".//mxCell") if c.get("edge") == "1")
        style = edge.get("style")
        for token in ("endArrow=block", "dashed=1", "dashPattern=4 3"):
            self.assertIn(token, style)
        self.assertEqual(len(edge.findall(".//Array/mxPoint")), 1)

    def test_images_are_embedded_without_a_base64_marker(self) -> None:
        root = svg2drawio.convert(self.data(), "t").getroot()
        image = next(c for c in root.findall(".//mxCell") if "shape=image" in c.get("style", ""))
        payload = image.get("style").split("image=data:image/svg+xml,")[1].rstrip(";")
        self.assertNotIn(";base64", image.get("style"))
        self.assertTrue(base64.b64decode(payload).startswith(b"<svg"))


class BrowserTests(unittest.TestCase):
    @unittest.skipUnless(_browser_or_none(), "Chrome/Chromium/Edge not available")
    def test_figkit_figure_round_trips_into_drawio_cells(self) -> None:
        f = figkit.Fig(400, 160)
        f.panel(4, 4, 392, 152, "blue", "(a) Stage")
        f.chip(20, 50, 90, 24, "pick.all", "blue", family="mono")
        f.text(20, 100, "mixed $a_t$", size=12)
        f.arrow("M120 62H200V100", "#3A3A3A")
        f.asset(Path(__file__).parents[1] / "examples" / "assets" / "camera.svg", 240, 50, 18)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fig.svg"
            f.save(str(path))
            data = svg2drawio.extract(path, _browser_or_none())
        root = svg2drawio.convert(data, "fig").getroot()
        ET.tostring(root)
        cells = root.findall(".//mxCell")
        self.assertTrue(any("pick.all" in (c.get("value") or "") and "rounded=1" in c.get("style", "") for c in cells))
        self.assertEqual(sum(1 for c in cells if c.get("edge") == "1"), 1)
        self.assertTrue(any("shape=image" in c.get("style", "") for c in cells))
        self.assertTrue(any("vertical-align" in (c.get("value") or "") for c in cells))


if __name__ == "__main__":
    unittest.main()
