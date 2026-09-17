from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("svgicons", SCRIPTS / "svgicons.py")
assert SPEC and SPEC.loader
svgicons = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = svgicons
SPEC.loader.exec_module(svgicons)

ICON = (b'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
        b'stroke="currentColor" stroke-width="2"><path d="M3 12h18"/></svg>')


class SearchTests(unittest.TestCase):
    def test_exact_and_multi_token_names_rank_first(self) -> None:
        icons = {"tabler": ["robot", "robot-arm", "robot-face", "armchair", "a-b"], "lobe": ["qwen", "qwen-color", "qwen-text"]}
        results = svgicons.search(icons, "robot arm", 3)
        self.assertEqual((results[0].family, results[0].slug), ("tabler", "robot-arm"))
        self.assertNotIn("armchair", [m.slug for m in results])
        self.assertEqual(svgicons.search(icons, "qwen", 1)[0].slug, "qwen")

    def test_aliases_map_figure_nouns_to_icon_names(self) -> None:
        self.assertEqual(svgicons.search({"tabler": ["target", "eye"]}, "goal", 1)[0].slug, "target")

    def test_ref_parser_rejects_unknown_family_and_unsafe_slugs(self) -> None:
        family, slug = svgicons.parse_ref("lobe:qwen-color")
        self.assertEqual((family.name, slug), ("lobe", "qwen-color"))
        for ref in ("robot", "noun:robot", "tabler:../robot", "tabler:robot.svg", "tabler:Robot", "tabler:https://e.com/x"):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                svgicons.parse_ref(ref)

    def test_index_parsers_keep_only_icon_svgs(self) -> None:
        tabler = svgicons.FAMILIES["tabler"]
        tree = {"tree": [{"path": f"icons/outline/i{n}.svg"} for n in range(1000)]
                + [{"path": "icons/filled/robot.svg"}, {"path": "icons/outline/../x.svg"}]}
        slugs = svgicons.parse_index(tabler, json.dumps(tree).encode())
        self.assertEqual(len(slugs), 1000)
        lobe = svgicons.FAMILIES["lobe"]
        meta = {"files": [{"path": f"/icons/brand{n}.svg"} for n in range(100)] + [{"path": "/package.json"}]}
        self.assertEqual(len(svgicons.parse_index(lobe, json.dumps(meta).encode())), 100)
        with self.assertRaises(ValueError):
            svgicons.parse_index(lobe, json.dumps({"files": []}).encode())

    def test_underscore_slugs_and_fill_variants(self) -> None:
        material = svgicons.FAMILIES["material"]
        family, slug = svgicons.parse_ref("material:precision_manufacturing")
        self.assertEqual((family.name, slug), ("material", "precision_manufacturing"))
        meta = {"files": [{"path": f"/outlined/icon_{n}.svg"} for n in range(1000)]
                + [{"path": "/outlined/icon_1-fill.svg"}, {"path": "/outlined/icon_1_fill.svg"}]}
        slugs = svgicons.parse_index(material, json.dumps(meta).encode())
        self.assertEqual(len(slugs), 1000)
        self.assertEqual(svgicons.search({"material": ["precision_manufacturing", "manufacturing"]},
                                         "precision manufacturing", 1)[0].slug, "precision_manufacturing")

    def test_every_family_ships_its_license_and_a_style(self) -> None:
        for name, family in svgicons.FAMILIES.items():
            with self.subTest(family=name):
                self.assertTrue((svgicons.LICENSES / family.license_file).is_file())
                self.assertIn(family.style, ("stroke", "fill", "logo"))
                self.assertTrue(family.index_url.startswith(family.allowed))
                self.assertTrue(family.raw_url.startswith(family.allowed))
        self.assertEqual(svgicons.FAMILIES["material200"].license_name, "material")

    def test_requests_outside_the_allowlist_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            svgicons.request_bytes("https://example.com/robot.svg", svgicons.FAMILIES["tabler"])


class VendorTests(unittest.TestCase):
    def test_vendor_writes_icon_license_and_one_ledger_row_per_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.object(svgicons, "request_bytes", return_value=ICON) as fetch:
            out = Path(tmp) / "assets" / "target.svg"
            result = svgicons.vendor("tabler:target", out)
            svgicons.vendor("tabler:target", out, force=True)
            svgicons.vendor("tabler:eye", out.with_name("eye.svg"))
            self.assertEqual(out.read_bytes(), ICON)
            self.assertTrue((out.parent / "LICENSE-tabler.txt").read_text(encoding="utf-8").startswith("MIT License"))
            ledger = (out.parent / "ASSETS.md").read_text(encoding="utf-8")
            with self.assertRaises(FileExistsError):
                svgicons.vendor("tabler:target", out)
        self.assertIn("icons/outline/target.svg", fetch.call_args_list[0].args[0])
        self.assertEqual(result["license"], "MIT")
        self.assertEqual(ledger.count("| target.svg |"), 1)
        self.assertEqual(ledger.count("| eye.svg |"), 1)

    def test_unsafe_download_is_not_written(self) -> None:
        payload = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><script>x()</script></svg>'
        with tempfile.TemporaryDirectory() as tmp, patch.object(svgicons, "request_bytes", return_value=payload):
            out = Path(tmp) / "bad.svg"
            with self.assertRaises(ValueError):
                svgicons.vendor("tabler:bad", out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
