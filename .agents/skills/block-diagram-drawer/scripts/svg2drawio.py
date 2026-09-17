#!/usr/bin/env python3
"""Convert a figkit SVG figure into an editable draw.io (.drawio) diagram.

The SVG is rendered in headless Chrome so every element keeps its real geometry and computed style.
Mapping:
- rects (panels, cards, chips, badges) -> rounded rectangle vertices; a chip's single centered label
  becomes the vertex label, so the chip and its text move together;
- circles -> ellipse vertices;
- text -> text vertices with HTML spans that keep family, size, weight, italics, color and script offsets;
- straight or orthogonal connectors (M/L/H/V paths) -> free edges with waypoints, arrowheads and dashes;
- icons, curves, filled paths, polygons and sketch groups -> embedded SVG image cells (no external files).

Usage:
    python svg2drawio.py figure.svg [-o figure.drawio] [--png]
`--png` also exports figure.drawio.png with the draw.io desktop CLI (set DRAWIO_PATH if needed) for a visual check.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from qa_svg_figure import find_browser

JS = r"""
const svg=document.querySelector('svg');
const W=svg.viewBox.baseVal.width,H=svg.viewBox.baseVal.height;
const origin=svg.getBoundingClientRect();
const styleEl=svg.querySelector('style');
const rootStyle=styleEl?styleEl.outerHTML:'';
const defsById={};
svg.querySelectorAll('defs > *').forEach(d=>{if(d.id) defsById[d.id]=d;});
function refs(el){
  const acc=new Set();
  const add=id=>{if(acc.has(id)||!defsById[id]) return; acc.add(id); walk(defsById[id]);};
  const walk=n=>{
    if(n.nodeType!==1) return;
    for(const a of n.attributes){
      const re=/url\(#([^)"']+)\)/g; let m; while((m=re.exec(a.value))) add(m[1]);
      if((a.name==='href'||a.name==='xlink:href')&&a.value.startsWith('#')) add(a.value.slice(1));
    }
    for(const c of n.children) walk(c);
  };
  walk(el); return [...acc].map(i=>defsById[i].outerHTML).join('');
}
function rect(el){const r=el.getBoundingClientRect(); return {x:r.left-origin.left,y:r.top-origin.top,w:r.width,h:r.height};}
function image(el,pad){
  const b=rect(el); const x=b.x-pad,y=b.y-pad,w=b.w+2*pad,h=b.h+2*pad;
  const body=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${x} ${y} ${w} ${h}" width="${w}" height="${h}" font-family="${svg.getAttribute('font-family')||''}">${rootStyle}<defs>${refs(el)}</defs>${el.outerHTML}</svg>`;
  return {kind:'image',x,y,w,h,svg:body};
}
function spansOf(textEl){
  const spans=[]; let off=0;
  const walk=(node,parentStyle)=>{
    for(const n of node.childNodes){
      if(n.nodeType===3){
        if(n.textContent.length) spans.push({t:n.textContent,ff:parentStyle.fontFamily,fs:parseFloat(parentStyle.fontSize),
          fw:parentStyle.fontWeight,fst:parentStyle.fontStyle,fill:parentStyle.fill,off});
      } else if(n.nodeType===1){
        off+=parseFloat(n.getAttribute('dy')||0);
        walk(n,getComputedStyle(n));
      }
    }
  };
  walk(textEl,getComputedStyle(textEl));
  return spans;
}
const out=[];
function visit(el){
  const tag=el.tagName.toLowerCase();
  if(['defs','style','symbol','marker','clippath','title','desc'].includes(tag)) return;
  const s=getComputedStyle(el);
  if(tag==='g'){
    if(el.hasAttribute('transform')||el.hasAttribute('clip-path')){out.push(image(el,4)); return;}
    for(const c of el.children) visit(c); return;
  }
  if(tag==='rect'){
    if(s.fill==='none'&&s.stroke==='none') return;
    out.push({kind:'rect',x:+el.getAttribute('x')||0,y:+el.getAttribute('y')||0,w:+el.getAttribute('width'),h:+el.getAttribute('height'),
      rx:+(el.getAttribute('rx')||0),fill:s.fill,stroke:s.stroke,sw:parseFloat(s.strokeWidth),dash:s.strokeDasharray,
      fo:+s.fillOpacity,so:+s.strokeOpacity,op:+s.opacity,box:el.dataset.box||null,bkind:el.dataset.kind||null});
    return;
  }
  if(tag==='circle'){
    out.push({kind:'ellipse',cx:+el.getAttribute('cx'),cy:+el.getAttribute('cy'),r:+el.getAttribute('r'),fill:s.fill,stroke:s.stroke,
      sw:parseFloat(s.strokeWidth),dash:s.strokeDasharray,fo:+s.fillOpacity,so:+s.strokeOpacity,op:+s.opacity});
    return;
  }
  if(tag==='text'){
    const b=el.getBBox(); if(!b.width) return;
    out.push({kind:'text',x:b.x,y:b.y,w:b.width,h:b.height,anchor:s.textAnchor,spans:spansOf(el),din:el.dataset.in||null});
    return;
  }
  if(tag==='path'){
    const d=el.getAttribute('d')||'';
    if(s.fill==='none'&&/^[MLHVZ0-9.\s,eE+-]+$/.test(d)){
      out.push({kind:'path',d,stroke:s.stroke,sw:parseFloat(s.strokeWidth),dash:s.strokeDasharray,
        ms:el.getAttribute('marker-start'),me:el.getAttribute('marker-end'),so:+s.strokeOpacity,op:+s.opacity});
      return;
    }
    out.push(image(el,Math.max(2,parseFloat(s.strokeWidth)||0)+8)); return;
  }
  out.push(image(el,4));
}
for(const c of svg.children) visit(c);
const pre=document.createElement('pre'); pre.id='x';
pre.textContent=JSON.stringify({W,H,items:out}); document.body.appendChild(pre);
"""

MARKER_RE = re.compile(r"#ah([0-9A-Fa-f]{6})(\d+)(o?)")


def extract(svg_path: Path, browser: str) -> dict:
    svg = svg_path.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "extract.html"
        page.write_text(f"<!doctype html><meta charset=utf-8><body style='margin:0'>{svg}<script>{JS}</script></body>",
                        encoding="utf-8")
        result = subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--virtual-time-budget=3000", "--dump-dom", page.as_uri()],
            capture_output=True, text=True, encoding="utf-8", timeout=180, check=True,
        )
    match = re.search(r'<pre id="x">(.*?)</pre>', result.stdout, re.DOTALL)
    if not match:
        raise RuntimeError("extraction produced no data; check that the SVG parses in the browser")
    return json.loads(html.unescape(match.group(1)))


def hex_color(value: str | None) -> str:
    """Convert a computed CSS color to #RRGGBB, or 'none'."""
    if not value or value in ("none", "transparent"):
        return "none"
    m = re.match(r"rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)(?:[,\s/]+([\d.]+))?\s*\)", value)
    if m:
        if m.group(4) is not None and float(m.group(4)) == 0:
            return "none"
        return "#{:02X}{:02X}{:02X}".format(*(int(m.group(i)) for i in (1, 2, 3)))
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        return value.upper()
    return "none"


def path_points(d: str) -> list[list[tuple[float, float]]]:
    """Parse absolute M/L/H/V/Z path data into subpaths of points."""
    tokens = re.findall(r"[MLHVZ]|-?\d*\.?\d+(?:[eE][-+]?\d+)?", d)
    subpaths: list[list[tuple[float, float]]] = []
    x = y = 0.0
    i, cmd = 0, None
    while i < len(tokens):
        tok = tokens[i]
        if tok in "MLHVZ":
            cmd = tok
            i += 1
            if cmd == "Z" and subpaths and subpaths[-1]:
                subpaths[-1].append(subpaths[-1][0])
            continue
        if cmd == "M":
            x, y = float(tokens[i]), float(tokens[i + 1])
            subpaths.append([(x, y)])
            i += 2
            cmd = "L"
        elif cmd == "L":
            x, y = float(tokens[i]), float(tokens[i + 1])
            subpaths[-1].append((x, y))
            i += 2
        elif cmd == "H":
            x = float(tok)
            subpaths[-1].append((x, y))
            i += 1
        elif cmd == "V":
            y = float(tok)
            subpaths[-1].append((x, y))
            i += 1
        else:
            raise ValueError(f"unsupported path data: {d}")
    return [sp for sp in subpaths if len(sp) >= 2]


def stroke_style(item: dict) -> list[str]:
    style = [f"strokeColor={hex_color(item.get('stroke'))}", f"strokeWidth={item.get('sw') or 1:g}"]
    dash = item.get("dash")
    if dash and dash != "none":
        style += ["dashed=1", "dashPattern=" + " ".join(f"{float(v):g}" for v in re.split(r"[,\s]+", dash.replace("px", "").strip()) if v)]
    for key, name in (("so", "strokeOpacity"), ("fo", "fillOpacity"), ("op", "opacity")):
        if item.get(key) is not None and item[key] < 0.999:
            style.append(f"{name}={round(item[key] * 100)}")
    return style


def span_html(span: dict) -> str:
    family = span["ff"].replace('"', "'")
    css = [f"font-family:{family}", f"font-size:{span['fs']:g}px", f"color:{hex_color(span['fill'])}", "white-space:pre"]
    if str(span["fw"]) not in ("400", "normal"):
        css.append(f"font-weight:{span['fw']}")
    if span["fst"] != "normal":
        css.append(f"font-style:{span['fst']}")
    if abs(span["off"]) > 0.01:
        css.append(f"vertical-align:{-span['off']:g}px")
    return f'<span style="{";".join(css)}">{html.escape(span["t"], quote=False)}</span>'


def text_label(item: dict) -> str:
    return "".join(span_html(s) for s in item["spans"])


class Builder:
    def __init__(self, width: float, height: float):
        self.width, self.height = width, height
        self.root = ET.Element("root")
        ET.SubElement(self.root, "mxCell", id="0")
        ET.SubElement(self.root, "mxCell", id="1", parent="0")
        self.n = 1

    def _id(self) -> str:
        self.n += 1
        return f"c{self.n}"

    def vertex(self, x, y, w, h, style: list[str], value: str = "") -> ET.Element:
        cell = ET.SubElement(self.root, "mxCell", id=self._id(), value=value, style=";".join(style) + ";", vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=f"{x:.2f}", y=f"{y:.2f}", width=f"{w:.2f}", height=f"{h:.2f}", **{"as": "geometry"})
        return cell

    def edge(self, points: list[tuple[float, float]], style: list[str]) -> None:
        cell = ET.SubElement(self.root, "mxCell", id=self._id(), value="", style=";".join(style) + ";", edge="1", parent="1")
        geo = ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})
        ET.SubElement(geo, "mxPoint", x=f"{points[0][0]:.2f}", y=f"{points[0][1]:.2f}", **{"as": "sourcePoint"})
        ET.SubElement(geo, "mxPoint", x=f"{points[-1][0]:.2f}", y=f"{points[-1][1]:.2f}", **{"as": "targetPoint"})
        if len(points) > 2:
            arr = ET.SubElement(geo, "Array", **{"as": "points"})
            for px, py in points[1:-1]:
                ET.SubElement(arr, "mxPoint", x=f"{px:.2f}", y=f"{py:.2f}")

    def document(self, name: str) -> ET.ElementTree:
        mxfile = ET.Element("mxfile", host="block-diagram-drawer", type="device")
        diagram = ET.SubElement(mxfile, "diagram", id="figure", name=name)
        model = ET.SubElement(diagram, "mxGraphModel", grid="0", gridSize="10", guides="1", tooltips="1", connect="0",
                              arrows="1", fold="1", page="1", pageScale="1", pageWidth=f"{self.width:g}",
                              pageHeight=f"{self.height:g}", math="0", shadow="0")
        model.append(self.root)
        return ET.ElementTree(mxfile)


def marker_style(ref: str | None, end: str) -> list[str]:
    m = MARKER_RE.search(ref or "")
    if not m:
        return [f"{end}Arrow=none"]
    size = int(m.group(2))
    if m.group(3):
        return [f"{end}Arrow=open", f"{end}Fill=0", f"{end}Size={size * 0.8:g}"]
    # draw.io draws block heads larger than an SVG marker of the same nominal size.
    return [f"{end}Arrow=block", f"{end}Fill=1", f"{end}Size={size * 0.6:g}"]


def convert(data: dict, name: str) -> ET.ElementTree:
    items = data["items"]
    b = Builder(data["W"], data["H"])
    # A chip with exactly one centered label becomes a labeled vertex.
    texts_per_box: dict[str, int] = {}
    for it in items:
        if it["kind"] == "text" and it.get("din"):
            texts_per_box[it["din"]] = texts_per_box.get(it["din"], 0) + 1
    chips = {it["box"]: it for it in items if it["kind"] == "rect" and it.get("bkind") == "chip" and it.get("box")}
    labels = {}
    for it in items:
        rect = chips.get(it.get("din")) if it["kind"] == "text" else None
        # Merge only a chip's single label that is centered in it on both axes; offset labels (beside or under an
        # icon) stay free text, because a vertex label is always drawn at the vertex center.
        if rect and texts_per_box[it["din"]] == 1 and it["anchor"] == "middle" \
                and abs(it["x"] + it["w"] / 2 - (rect["x"] + rect["w"] / 2)) < 2.5 \
                and abs(it["y"] + it["h"] / 2 - (rect["y"] + rect["h"] / 2)) < max(3.0, rect["h"] * 0.12):
            labels[it["din"]] = it

    for index, it in enumerate(items):
        kind = it["kind"]
        if kind == "rect":
            fill = hex_color(it["fill"])
            style = ["whiteSpace=nowrap", "html=1", f"fillColor={fill}", *stroke_style(it)]
            if it["rx"]:
                style += ["rounded=1", "absoluteArcSize=1", f"arcSize={it['rx'] * 2:g}"]
            else:
                style.append("rounded=0")
            value = ""
            if it.get("box") in labels:
                label = labels[it["box"]]
                value = text_label(label)
                style += ["align=center", "verticalAlign=middle", "spacing=0", "overflow=visible"]
            if index == 0 and it["w"] >= data["W"] - 0.5 and it["h"] >= data["H"] - 0.5:
                style.append("locked=1")
            b.vertex(it["x"], it["y"], it["w"], it["h"], style, value)
        elif kind == "ellipse":
            style = ["ellipse", "html=1", f"fillColor={hex_color(it['fill'])}", *stroke_style(it)]
            b.vertex(it["cx"] - it["r"], it["cy"] - it["r"], 2 * it["r"], 2 * it["r"], style)
        elif kind == "text":
            if it.get("din") in labels and labels[it["din"]] is it:
                continue
            align = {"start": "left", "middle": "center", "end": "right"}.get(it["anchor"], "left")
            pad = 6
            x = it["x"] - (pad if align == "right" else pad / 2 if align == "center" else 0)
            style = ["text", "html=1", "whiteSpace=nowrap", "overflow=visible", "spacing=0", "spacingLeft=0", "spacingRight=0",
                     f"align={align}", "verticalAlign=middle", "fillColor=none", "strokeColor=none"]
            b.vertex(x, it["y"], it["w"] + pad, it["h"], style, text_label(it))
        elif kind == "path":
            base = ["html=1", "rounded=0", "edgeStyle=none", *stroke_style(it)]
            for points in path_points(it["d"]):
                b.edge(points, base + marker_style(it.get("me"), "end") + marker_style(it.get("ms"), "start"))
        elif kind == "image":
            payload = base64.b64encode(it["svg"].encode("utf-8")).decode("ascii")
            # Marker-less base64: draw.io splits styles on ';', so 'data:...;base64,' would truncate the value.
            style = ["shape=image", "html=1", "imageAspect=0", "aspect=fixed", "verticalLabelPosition=bottom",
                     f"image=data:image/svg+xml,{payload}"]
            b.vertex(it["x"], it["y"], it["w"], it["h"], style)
    return b.document(name)


def find_drawio() -> str | None:
    env = os.environ.get("DRAWIO_PATH")
    if env:
        return env
    for candidate in ("/Applications/draw.io.app/Contents/MacOS/draw.io", r"C:\Program Files\draw.io\draw.io.exe"):
        if Path(candidate).exists():
            return candidate
    return shutil.which("drawio") or shutil.which("draw.io")


def export_png(drawio_file: Path, scale: int = 2) -> Path:
    exe = find_drawio()
    if not exe:
        raise SystemExit("draw.io desktop was not found; set DRAWIO_PATH to export a PNG preview")
    out = drawio_file.with_suffix(".drawio.png")
    subprocess.run([exe, "-x", "-f", "png", "-s", str(scale), "-o", str(out), str(drawio_file)],
                   capture_output=True, timeout=180, check=True)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("svg", type=Path)
    parser.add_argument("-o", "--out", type=Path)
    parser.add_argument("--png", action="store_true", help="also export a PNG preview with the draw.io desktop CLI")
    args = parser.parse_args(argv)
    out = args.out or args.svg.with_suffix(".drawio")
    data = extract(args.svg, find_browser())
    tree = convert(data, args.svg.stem)
    ET.indent(tree, space="  ")
    tree.write(out, encoding="utf-8", xml_declaration=False)
    counts = {k: sum(1 for it in data["items"] if it["kind"] == k) for k in ("rect", "ellipse", "text", "path", "image")}
    print(f"{out}  " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    if args.png:
        print(export_png(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
