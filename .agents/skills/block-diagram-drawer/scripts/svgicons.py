#!/usr/bin/env python3
"""Search and vendor open-source SVG icons for block diagrams.

Families (both MIT):
- tabler: Tabler Icons outline set, 5000+ pictograms for recognizable objects
  (robot, camera, door, database, target, list-check, ...).
- lobe:   LobeHub icons, logos of AI models and providers (qwen, openai, claude, ...).
          Logos are trademarks of their owners; use one only for the product the figure names.

Only the icons a figure uses are downloaded, from allowlisted official URLs. `get` validates the SVG
with figkit's asset parser, writes it atomically, copies the family license next to it, and records
the source in ASSETS.md in the same folder.

Examples:
  python svgicons.py search "robot arm"
  python svgicons.py search qwen --family lobe
  python svgicons.py get tabler:target --out figures/src/assets/target.svg
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
import urllib.request
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from figkit import parse_svg_asset

LICENSES = HERE.parent / "references" / "licenses"
LOBE_VERSION = "1.91.0"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
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


FAMILIES = {
    "tabler": Family(
        name="tabler",
        index_url="https://api.github.com/repos/tabler/tabler-icons/git/trees/main?recursive=1",
        raw_url="https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/{slug}.svg",
        page_url="https://tabler.io/icons/icon/{slug}",
        allowed=("https://api.github.com/repos/tabler/tabler-icons/", "https://raw.githubusercontent.com/tabler/tabler-icons/"),
        license_file="tabler-icons.txt",
        min_icons=1000,
    ),
    "lobe": Family(
        name="lobe",
        index_url=f"https://unpkg.com/@lobehub/icons-static-svg@{LOBE_VERSION}/icons/?meta",
        raw_url=f"https://unpkg.com/@lobehub/icons-static-svg@{LOBE_VERSION}/icons/{{slug}}.svg",
        page_url="https://github.com/lobehub/lobe-icons",
        allowed=(f"https://unpkg.com/@lobehub/icons-static-svg@{LOBE_VERSION}/",),
        license_file="lobe-icons.txt",
        min_icons=100,
    ),
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


def parse_index(family: Family, payload: bytes) -> list[str]:
    """Extract icon slugs from a GitHub tree (tabler) or an unpkg directory listing (lobe)."""
    document = json.loads(payload)
    if family.name == "tabler":
        if document.get("truncated"):
            raise ValueError("GitHub tree response was truncated")
        paths = [str(item.get("path", "")) for item in document.get("tree", [])]
        pattern = r"icons/outline/([a-z0-9]+(?:-[a-z0-9]+)*)\.svg"
    else:
        paths = [str(item.get("path", "")) for item in document.get("files", [])]
        pattern = r"/icons/([a-z0-9]+(?:-[a-z0-9]+)*)\.svg"
    slugs = sorted({m.group(1) for p in paths if (m := re.fullmatch(pattern, p))})
    if len(slugs) < family.min_icons:
        raise ValueError(f"unexpectedly small {family.name} index: {len(slugs)} icons")
    return slugs


def load_index(family: Family, cache_dir: Path, refresh: bool = False) -> list[str]:
    cache = cache_dir / f"{family.name}-index.json"
    if cache.exists() and not refresh and time.time() - cache.stat().st_mtime <= CACHE_SECONDS:
        icons = json.loads(cache.read_text(encoding="utf-8")).get("icons", [])
        if isinstance(icons, list) and icons and all(SLUG_RE.fullmatch(str(i)) for i in icons):
            return [str(i) for i in icons]
    icons = parse_index(family, request_bytes(family.index_url, family))
    cache_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(cache, json.dumps({"source": family.index_url, "icons": icons}, indent=1).encode("utf-8"))
    return icons


def query_tokens(query: str) -> list[str]:
    return list(dict.fromkeys(ALIASES.get(t, t) for t in TOKEN_RE.findall(query.casefold())))


def score_slug(slug: str, tokens: list[str]) -> int:
    """Rank a slug by exact name, whole-part, prefix and substring matches; penalize unmatched tokens."""
    if not tokens:
        return 0
    parts = slug.split("-")
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
    if "".join(tokens) == slug.replace("-", ""):
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
    rows.append(f"| {file_name} | {family.name} | {source} | MIT, see LICENSE-{family.name}.txt |")
    _atomic_write(ledger, (LEDGER_HEADER + "\n".join(sorted(rows)) + "\n").encode("utf-8"))


def vendor(ref: str, out: Path, force: bool = False) -> dict[str, str]:
    family, slug = parse_ref(ref)
    if out.suffix != ".svg":
        raise ValueError(f"output must be an .svg file, got {out}")
    if out.exists() and not force:
        raise FileExistsError(f"refusing to overwrite {out}; pass --force")
    source = family.raw_url.format(slug=slug)
    payload = request_bytes(source, family)
    try:
        parse_svg_asset(payload.decode("utf-8"), f"{slug}.svg")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{slug}: SVG is not UTF-8") from exc
    out.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(out, payload)
    shutil.copyfile(LICENSES / family.license_file, out.parent / f"LICENSE-{family.name}.txt")
    record(out.parent / "ASSETS.md", out.name, family, source)
    return {"family": family.name, "slug": slug, "output": str(out.resolve()), "source": source, "license": "MIT"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache-dir", type=Path, default=default_cache_dir())
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("search", help="search icon names")
    s.add_argument("query")
    s.add_argument("--family", choices=[*FAMILIES, "all"], default="tabler")
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
                    print(f"{m.family}:{m.slug:<34} score={m.score:>3}  {FAMILIES[m.family].page_url.format(slug=m.slug)}")
            return 0
        result = vendor(args.ref, args.out, args.force)
        print(json.dumps(result, indent=2) if args.json else result["output"])
        return 0
    except (FileExistsError, ValueError, urllib.error.URLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
