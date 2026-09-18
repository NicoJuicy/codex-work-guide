#!/usr/bin/env python3
"""Search and vendor open-source SVG icons for block diagrams.

Eight families, all permissively licensed. `stroke` families are line icons whose weight `figkit.asset`
normalizes; `fill` families are solid-shape icons that keep their own optical weight at any size.

- tabler    (MIT, stroke):        5900 pictograms, the broad default for objects and actions.
- lucide    (ISC, stroke):        1800 very plain icons; the calmest line family.
- iconoir   (MIT, stroke):        1600 icons drawn on a 1.5 px grid, a little more geometric.
- phosphor  (MIT, fill):          9000 icons in one solid-outline style; the richest vocabulary and
                                  the best choice when an icon has to carry a card at 60 px or more.
- material  (Apache-2.0, fill):   3700 Material Symbols at weight 400; the only family with real
                                  machine and robotics vocabulary (precision_manufacturing,
                                  conveyor_belt, ...). Use it from 16 to 48 px.
- material200 (Apache-2.0, fill): the same set at weight 200, for an icon that carries a card at
                                  60 px or more, where weight 400 reads as too heavy.
- fluentemoji (MIT, color):        1200 Microsoft Fluent Emoji in the Flat style: colour illustrations of
                                  objects (robot, hot_beverage, door, camera, mechanical_arm, brain, gear).
                                  The best choice for things inside a scene; place them with
                                  `f.asset(..., color=None)` so their own colours are kept.
- fluent    (MIT, fill):          2700 Microsoft Fluent UI System Icons; each icon ships in several sizes
                                  and the largest regular drawing is vendored, so detail holds up at
                                  36 px and more.
- lobe      (MIT, logos):         logos of AI models and providers (qwen, openai, claude, ...).
                                  Logos are trademarks of their owners; use one only for the product
                                  the figure names.

Search spans every family by default so silhouettes can be compared; keep one family per figure, and
prefer the family that has every object the figure needs. Material slugs use underscores.

Only the icons a figure uses are downloaded, from allowlisted official URLs. `get` validates the SVG
with figkit's asset parser, writes it atomically, copies the family license next to it, and records
the source in ASSETS.md in the same folder.

Examples:
  python svgicons.py search "robot arm"
  python svgicons.py search door --family phosphor
  python svgicons.py get material:precision_manufacturing --out figures/src/assets/arm.svg
  python svgicons.py get lobe:qwen --out figures/src/assets/qwen.svg
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from figkit import parse_svg_asset

LICENSES = HERE.parent / "references" / "licenses"
LOBE_VERSION = "1.91.0"
LUCIDE_VERSION = "0.544.0"
PHOSPHOR_VERSION = "2.1.1"
MATERIAL_VERSION = "0.36.0"
ICONOIR_VERSION = "7.11.0"
FLUENT_VERSION = "1.1.292"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
TOKEN_RE = re.compile(r"[a-z0-9]+")
MAX_RESPONSE_BYTES = 12 * 1024 * 1024
CACHE_SECONDS = 7 * 24 * 60 * 60
LEDGER_HEADER = "# Vendored SVG assets\n\n| File | Family | Source | License |\n|---|---|---|---|\n"


@dataclass(frozen=True)
class Family:
    name: str
    index_url: str
    raw_url: str
    page_url: str
    allowed: tuple[str, ...]
    license_file: str
    min_icons: int
    index_re: str
    style: str
    license: str
    license_as: str = ""
    raw_base: str = ""  # set for families whose files are found through the index's slug -> path map

    @property
    def license_name(self) -> str:
        """The name the license copy gets next to the icons; weight variants share one file."""
        return self.license_as or self.name


def _unpkg(name: str, package: str, folder: str, page: str, license_file: str, style: str, license: str,
           min_icons: int, index_re: str | None = None, license_as: str = "") -> Family:
    base = f"https://unpkg.com/{package}/"
    return Family(
        name=name,
        index_url=f"{base}{folder}/?meta",
        raw_url=f"{base}{folder}/{{slug}}.svg",
        page_url=page,
        allowed=(base,),
        license_file=license_file,
        min_icons=min_icons,
        index_re=index_re or rf"/{folder}/([a-z0-9]+(?:[-_][a-z0-9]+)*)\.svg",
        style=style,
        license=license,
        license_as=license_as,
    )


FAMILIES = {
    "tabler": Family(
        name="tabler",
        index_url="https://api.github.com/repos/tabler/tabler-icons/git/trees/main?recursive=1",
        raw_url="https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/{slug}.svg",
        page_url="https://tabler.io/icons/icon/{slug}",
        allowed=("https://api.github.com/repos/tabler/tabler-icons/", "https://raw.githubusercontent.com/tabler/tabler-icons/"),
        license_file="tabler-icons.txt",
        min_icons=1000,
        index_re=r"icons/outline/([a-z0-9]+(?:-[a-z0-9]+)*)\.svg",
        style="stroke",
        license="MIT",
    ),
    "lucide": _unpkg("lucide", f"lucide-static@{LUCIDE_VERSION}", "icons",
                     "https://lucide.dev/icons/{slug}", "lucide-icons.txt", "stroke", "ISC", 900),
    "iconoir": _unpkg("iconoir", f"iconoir@{ICONOIR_VERSION}", "icons/regular",
                      "https://iconoir.com/", "iconoir.txt", "stroke", "MIT", 900,
                      index_re=r"/icons/regular/([a-z0-9]+(?:[-_][a-z0-9]+)*)\.svg"),
    "phosphor": _unpkg("phosphor", f"@phosphor-icons/core@{PHOSPHOR_VERSION}", "assets/regular",
                       "https://phosphoricons.com/?q={slug}", "phosphor-icons.txt", "fill", "MIT", 900,
                       index_re=r"/assets/regular/([a-z0-9]+(?:[-_][a-z0-9]+)*)\.svg"),
    "material": _unpkg("material", f"@material-symbols/svg-400@{MATERIAL_VERSION}", "outlined",
                       "https://fonts.google.com/icons?selected=Material+Symbols+Outlined:{slug}",
                       "material-symbols.txt", "fill", "Apache-2.0", 1000),
    "material200": _unpkg("material200", f"@material-symbols/svg-200@{MATERIAL_VERSION}", "outlined",
                          "https://fonts.google.com/icons?selected=Material+Symbols+Outlined:{slug}",
                          "material-symbols.txt", "fill", "Apache-2.0", 1000, license_as="material"),
    "fluentemoji": Family(
        name="fluentemoji",
        index_url="https://api.github.com/repos/microsoft/fluentui-emoji/git/trees/main?recursive=1",
        raw_url="",
        page_url="https://github.com/microsoft/fluentui-emoji",
        allowed=("https://api.github.com/repos/microsoft/fluentui-emoji/",
                 "https://raw.githubusercontent.com/microsoft/fluentui-emoji/"),
        license_file="fluentui-emoji.txt",
        min_icons=900,
        index_re=r"assets/[^/]+/(?:Default/)?Flat/([a-z0-9_]+?)_flat(?:_default)?\.svg",
        style="color",
        license="MIT",
        raw_base="https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/",
    ),
    "fluent": Family(
        name="fluent",
        index_url=f"https://unpkg.com/@fluentui/svg-icons@{FLUENT_VERSION}/icons/?meta",
        raw_url="",
        page_url="https://github.com/microsoft/fluentui-system-icons",
        allowed=(f"https://unpkg.com/@fluentui/svg-icons@{FLUENT_VERSION}/",),
        license_file="fluentui-system-icons.txt",
        min_icons=1000,
        index_re=r"/icons/([a-z0-9_]+?)_(\d+)_(regular|filled|light)\.svg",
        style="fill",
        license="MIT",
        raw_base=f"https://unpkg.com/@fluentui/svg-icons@{FLUENT_VERSION}/",
    ),
    "lobe": _unpkg("lobe", f"@lobehub/icons-static-svg@{LOBE_VERSION}", "icons",
                   "https://github.com/lobehub/lobe-icons", "lobe-icons.txt", "logo", "MIT", 100),
}

ALIASES = {
    "ai": "brain",
    "dataset": "database",
    "goal": "target",
    "llm": "brain",
    "model": "brain",
    "observation": "eye",
    "observations": "eye",
    "robotics": "robot",
    "simulation": "cube",
}


@dataclass(frozen=True)
class Match:
    family: str
    slug: str
    score: int


def default_cache_dir() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "block-diagram-drawer"


def request_bytes(url: str, family: Family, timeout: float = 20.0) -> bytes:
    """Fetch a bounded response, refusing any URL (or redirect target) outside the family allowlist."""
    if not url.startswith(family.allowed):
        raise ValueError(f"refusing URL outside the {family.name} allowlist: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "block-diagram-drawer/1"})
    # The prefix allowlist excludes file:, custom schemes and arbitrary hosts.
    with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
        if not response.geturl().startswith(family.allowed):
            raise ValueError(f"refusing redirect outside the {family.name} allowlist: {response.geturl()}")
        payload = response.read(MAX_RESPONSE_BYTES + 1)
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError(f"response exceeds {MAX_RESPONSE_BYTES} bytes")
    return payload


def _listing(family: Family, payload: bytes) -> list[str]:
    document = json.loads(payload)
    if "tree" in document:  # a GitHub tree
        if document.get("truncated"):
            raise ValueError("GitHub tree response was truncated")
        return [str(item.get("path", "")) for item in document.get("tree", [])]
    return [str(item.get("path", "")) for item in document.get("files", [])]  # an unpkg listing


def parse_paths(family: Family, payload: bytes) -> dict[str, str]:
    """Slug -> file path for families whose file names are not the slug: Fluent Emoji keeps each emoji in a
    folder named in words, and Fluent System Icons ship every icon in several sizes, of which the largest
    regular one is kept because its drawing is tuned for figure sizes."""
    chosen: dict[str, tuple[tuple[int, int], str]] = {}
    for path in _listing(family, payload):
        m = re.fullmatch(family.index_re, path)
        if not m:
            continue
        rank = (0, 0)
        if family.name == "fluent":
            rank = ({"regular": 2, "light": 1, "filled": 0}[m.group(3)], int(m.group(2)))
        elif "/Default/" not in path:
            rank = (1, 0)
        if m.group(1) not in chosen or rank > chosen[m.group(1)][0]:
            chosen[m.group(1)] = (rank, path.lstrip("/"))
    return {slug: path for slug, (_, path) in chosen.items()}


def parse_index(family: Family, payload: bytes) -> list[str]:
    """Extract icon slugs from a GitHub tree or an unpkg directory listing."""
    if family.raw_base:
        slugs = sorted(parse_paths(family, payload))
    else:
        slugs = sorted({m.group(1) for p in _listing(family, payload) if (m := re.fullmatch(family.index_re, p))
                        and not m.group(1).endswith(("-fill", "_fill"))})
    if len(slugs) < family.min_icons:
        raise ValueError(f"unexpectedly small {family.name} index: {len(slugs)} icons")
    return slugs


def _cached(family: Family, cache_dir: Path, refresh: bool) -> dict:
    cache = cache_dir / f"{family.name}-index.json"
    if cache.exists() and not refresh and time.time() - cache.stat().st_mtime <= CACHE_SECONDS:
        document = json.loads(cache.read_text(encoding="utf-8"))
        icons = document.get("icons", [])
        if isinstance(icons, list) and icons and all(SLUG_RE.fullmatch(str(i)) for i in icons) \
                and (not family.raw_base or isinstance(document.get("paths"), dict)):
            return document
    payload = request_bytes(family.index_url, family)
    document = {"source": family.index_url, "icons": parse_index(family, payload)}
    if family.raw_base:
        document["paths"] = parse_paths(family, payload)
    cache_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(cache, json.dumps(document, indent=1).encode("utf-8"))
    return document


def load_index(family: Family, cache_dir: Path, refresh: bool = False) -> list[str]:
    return [str(i) for i in _cached(family, cache_dir, refresh)["icons"]]


def source_url(family: Family, slug: str, cache_dir: Path | None = None) -> str:
    """Where an icon is downloaded from; path-mapped families look the file up in the cached index."""
    if not family.raw_base:
        return family.raw_url.format(slug=slug)
    paths = _cached(family, cache_dir or default_cache_dir(), False).get("paths", {})
    if slug not in paths:
        raise ValueError(f"{family.name} has no icon {slug!r}; search first")
    return family.raw_base + urllib.parse.quote(paths[slug])


def query_tokens(query: str) -> list[str]:
    return list(dict.fromkeys(ALIASES.get(t, t) for t in TOKEN_RE.findall(query.casefold())))


def score_slug(slug: str, tokens: list[str]) -> int:
    """Rank a slug by exact name, whole-part, prefix and substring matches; penalize unmatched tokens."""
    if not tokens:
        return 0
    parts = re.split(r"[-_]", slug)
    score = 0
    for token in tokens:
        if token == slug:
            score += 100
        elif token in parts:
            score += 35
        elif any((len(token) >= 2 and part.startswith(token)) or (len(part) >= 3 and token.startswith(part)) for part in parts):
            score += 18
        elif token in slug:
            score += 10
        else:
            score -= 20
    if "".join(tokens) == re.sub(r"[-_]", "", slug):
        score += 60
    return score - max(0, len(parts) - len(tokens))


def search(icons: dict[str, list[str]], query: str, limit: int) -> list[Match]:
    tokens = query_tokens(query)
    found = [Match(fam, slug, score_slug(slug, tokens)) for fam, slugs in icons.items() for slug in slugs]
    found = [m for m in found if m.score > 0]
    found.sort(key=lambda m: (-m.score, len(m.slug), m.family, m.slug))
    return found[:limit]


def parse_ref(ref: str) -> tuple[Family, str]:
    """Split `family:slug` and reject unknown families, traversal, URLs and file names."""
    family_name, sep, slug = ref.partition(":")
    if not sep or family_name not in FAMILIES:
        raise ValueError(f"expected family:slug with family in {sorted(FAMILIES)}, got {ref!r}")
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(f"invalid icon slug: {slug!r}")
    return FAMILIES[family_name], slug


def _atomic_write(path: Path, payload: bytes) -> None:
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(payload)
        temp = Path(handle.name)
    temp.replace(path)


def record(ledger: Path, file_name: str, family: Family, source: str) -> None:
    """Add or replace the ledger row for one vendored file."""
    rows = []
    if ledger.exists():
        rows = [line for line in ledger.read_text(encoding="utf-8").splitlines()
                if line.startswith("| ") and not line.startswith(("| File ", f"| {file_name} |"))]
    rows.append(f"| {file_name} | {family.name} | {source} | {family.license}, "
                f"see LICENSE-{family.license_name}.txt |")
    _atomic_write(ledger, (LEDGER_HEADER + "\n".join(sorted(rows)) + "\n").encode("utf-8"))


def vendor(ref: str, out: Path, force: bool = False, cache_dir: Path | None = None) -> dict[str, str]:
    family, slug = parse_ref(ref)
    if out.suffix != ".svg":
        raise ValueError(f"output must be an .svg file, got {out}")
    if out.exists() and not force:
        raise FileExistsError(f"refusing to overwrite {out}; pass --force")
    source = source_url(family, slug, cache_dir)
    payload = request_bytes(source, family)
    try:
        parse_svg_asset(payload.decode("utf-8"), f"{slug}.svg")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{slug}: SVG is not UTF-8") from exc
    out.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(out, payload)
    shutil.copyfile(LICENSES / family.license_file, out.parent / f"LICENSE-{family.license_name}.txt")
    record(out.parent / "ASSETS.md", out.name, family, source)
    return {"family": family.name, "slug": slug, "output": str(out.resolve()), "source": source,
            "style": family.style, "license": family.license}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache-dir", type=Path, default=default_cache_dir())
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("search", help="search icon names")
    s.add_argument("query")
    s.add_argument("--family", choices=[*FAMILIES, "all"], default="all")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--refresh", action="store_true", help="refetch the cached name index")
    s.add_argument("--json", action="store_true")
    g = sub.add_parser("get", help="vendor one icon as family:slug")
    g.add_argument("ref")
    g.add_argument("--out", type=Path, required=True)
    g.add_argument("--force", action="store_true")
    g.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.command == "search":
            if args.limit < 1:
                parser.error("--limit must be positive")
            names = list(FAMILIES) if args.family == "all" else [args.family]
            icons = {n: load_index(FAMILIES[n], args.cache_dir, args.refresh) for n in names}
            matches = search(icons, args.query, args.limit)
            if not matches:
                print(f"no icons matched {args.query!r}; try a synonym or a more concrete noun", file=sys.stderr)
                return 1
            if args.json:
                print(json.dumps([m.__dict__ for m in matches], indent=2))
            else:
                for m in matches:
                    fam = FAMILIES[m.family]
                    print(f"{m.family}:{m.slug:<34} {fam.style:<6} score={m.score:>3}  "
                          f"{fam.page_url.format(slug=m.slug)}")
            return 0
        result = vendor(args.ref, args.out, args.force, args.cache_dir)
        print(json.dumps(result, indent=2) if args.json else result["output"])
        return 0
    except (FileExistsError, ValueError, urllib.error.URLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
