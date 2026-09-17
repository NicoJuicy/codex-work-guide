"""Render-truth QA gate for dense SVG figures built with figkit.

The SVG is rendered in headless Chrome/Chromium/Edge and measured with the
browser's own text layout, so width estimates in the build script never decide
acceptance. Reported checks:

- overflow:   text escaping its container (text[data-in] -> [data-box]) or the canvas
- collide:    text/text bounding-box collisions
- boxOverlap: sibling cards/chips/thumbnails that partially overlap
- lineText:   connector or curve strokes crossing a label that no opaque,
              later-drawn container covers
- smallText:  labels set below the minimum size (11 px at 1400 px width, scaled
              with the canvas); math scripts inside a label are exempt
- coverage:   share of the canvas covered by cards, chips, thumbnails and text
- framed:     share covered by stage panels or content

Exit code 1 when any check fails or coverage is below --min-coverage.

Usage:
    python qa_svg_figure.py figure.svg [--png] [--json] [--min-coverage 0.55] [--min-font 11]
Set CHROME_PATH when the browser is not auto-detected.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKS = ("overflow", "collide", "boxOverlap", "lineText", "smallText")

_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
)
_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge")

JS = r"""
const svg=document.querySelector('svg');
const W=svg.viewBox.baseVal.width,H=svg.viewBox.baseVal.height;
const R=b=>({x:b.x,y:b.y,w:b.width,h:b.height});
const boxes={};
svg.querySelectorAll('[data-box]').forEach(e=>{boxes[e.dataset.box]=Object.assign(R(e.getBBox()),{kind:e.dataset.kind,id:e.dataset.box});});
const overflow=[],texts=[],textEls=[],smallText=[];
const MIN_FONT=__MIN_FONT__*W/1400;
svg.querySelectorAll('text').forEach(t=>{
  const b=R(t.getBBox()); if(!b.w) return; b.s=t.textContent.slice(0,40); texts.push(b); textEls.push(t);
  const fs=parseFloat(getComputedStyle(t).fontSize); if(fs<MIN_FONT-0.01) smallText.push({s:b.s,size:fs});
  if(b.x<0||b.y<0||b.x+b.w>W||b.y+b.h>H) overflow.push({s:b.s,box:'canvas'});
  const B=boxes[t.dataset.in]; if(!B) return;
  const l=b.x-B.x,r=B.x+B.w-(b.x+b.w),tp=b.y-B.y,bt=B.y+B.h-(b.y+b.h);
  if(l<1.5||r<1.5||tp<-1||bt<-2) overflow.push({s:b.s,box:B.kind,left:Math.round(l),right:Math.round(r),top:Math.round(tp),bottom:Math.round(bt)});
});
const collide=[];
for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++){
  const a=texts[i],c=texts[j];
  const ix=Math.min(a.x+a.w,c.x+c.w)-Math.max(a.x,c.x), iy=Math.min(a.y+a.h,c.y+c.h)-Math.max(a.y,c.y);
  if(ix>1.5&&iy>4) collide.push([a.s,c.s,Math.round(ix),Math.round(iy)]);
}
const solid=Object.values(boxes).filter(b=>b.kind!=='panel');
const inside=(a,b)=>a.x>=b.x-0.5&&a.y>=b.y-0.5&&a.x+a.w<=b.x+b.w+0.5&&a.y+a.h<=b.y+b.h+0.5;
const boxOverlap=[];
for(let i=0;i<solid.length;i++)for(let j=i+1;j<solid.length;j++){
  const a=solid[i],c=solid[j]; if(inside(a,c)||inside(c,a)) continue;
  const ix=Math.min(a.x+a.w,c.x+c.w)-Math.max(a.x,c.x), iy=Math.min(a.y+a.h,c.y+c.h)-Math.max(a.y,c.y);
  if(ix>0.5&&iy>0.5) boxOverlap.push([a.kind+':'+[a.x,a.y].map(Math.round),c.kind+':'+[c.x,c.y].map(Math.round)]);
}
const lineText=[];
const strokes=[...svg.querySelectorAll('path,line,polyline')].filter(e=>!e.closest('symbol,marker,clipPath,defs,[data-qa=ignore]')&&getComputedStyle(e).stroke!=='none');
strokes.forEach(e=>{
  let L; try{L=e.getTotalLength();}catch(_){return;} if(!L) return;
  const hits=new Set();
  for(let d=0;d<=L;d+=2){const p=e.getPointAtLength(d);
    texts.forEach((b,i)=>{if(p.x>b.x+1&&p.x<b.x+b.w-1&&p.y>b.y+b.h*0.22&&p.y<b.y+b.h*0.86) hits.add(i);});}
  hits.forEach(i=>{
    const t=textEls[i]; const cont=t.dataset.in?svg.querySelector('[data-box="'+t.dataset.in+'"]'):null;
    if(cont&&getComputedStyle(cont).fill!=='none'&&(e.compareDocumentPosition(cont)&Node.DOCUMENT_POSITION_FOLLOWING)) return;
    lineText.push([texts[i].s,(e.getAttribute('d')||e.tagName).slice(0,34)]);
  });
});
let cov=0,pcov=0,n=0; const panels=Object.values(boxes).filter(b=>b.kind==='panel');
const hit=(arr,x,y)=>arr.some(b=>x>=b.x&&x<=b.x+b.w&&y>=b.y&&y<=b.y+b.h);
for(let y=2;y<H;y+=4)for(let x=2;x<W;x+=4){n++; if(hit(solid,x,y)||hit(texts,x,y)) cov++; if(hit(panels,x,y)||hit(solid,x,y)) pcov++;}
const out={size:[W,H],texts:texts.length,overflow,collide,boxOverlap,lineText,smallText,coverage:+(cov/n).toFixed(3),framed:+(pcov/n).toFixed(3)};
const pre=document.createElement('pre'); pre.id='qa'; pre.textContent=JSON.stringify(out); document.body.appendChild(pre);
"""


def find_browser() -> str:
    env = os.environ.get("CHROME_PATH")
    if env:
        return env
    for candidate in _CANDIDATES:
        if Path(candidate).exists():
            return candidate
    for name in _NAMES:
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("Chrome, Chromium or Edge was not found; set CHROME_PATH to the browser executable.")


def measure(svg_path: Path, browser: str, min_font: float = 11.0) -> dict:
    svg = svg_path.read_text(encoding="utf-8")
    script = JS.replace("__MIN_FONT__", f"{float(min_font):g}")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "qa.html"
        page.write_text(f"<!doctype html><meta charset=utf-8><body style='margin:0'>{svg}<script>{script}</script></body>", encoding="utf-8")
        result = subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--virtual-time-budget=3000", "--dump-dom", page.as_uri()],
            capture_output=True, text=True, encoding="utf-8", timeout=180, check=True,
        )
    match = re.search(r'<pre id="qa">(.*?)</pre>', result.stdout, re.DOTALL)
    if not match:
        raise RuntimeError("the QA script produced no report; check that the SVG parses in the browser")
    return json.loads(html.unescape(match.group(1)))


def render_png(svg_path: Path, size: list[float], browser: str, scale: int = 2) -> Path:
    out = svg_path.with_suffix(".png")
    subprocess.run(
        [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--force-device-scale-factor={scale}",
         f"--window-size={int(size[0])},{int(size[1])}", f"--screenshot={out}", svg_path.resolve().as_uri()],
        capture_output=True, timeout=180, check=True,
    )
    return out


def failures(report: dict, min_coverage: float) -> list[str]:
    failed = [f"{key}={len(report[key])}" for key in CHECKS if report[key]]
    if report["coverage"] < min_coverage:
        failed.append(f"coverage={report['coverage']} < {min_coverage}")
    return failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("svg", type=Path)
    parser.add_argument("--png", action="store_true", help="also write a 2x PNG next to the SVG")
    parser.add_argument("--json", action="store_true", help="print the full JSON report")
    parser.add_argument("--min-coverage", type=float, default=0.55)
    parser.add_argument("--min-font", type=float, default=11.0,
                        help="smallest allowed label size in px at 1400 px canvas width")
    args = parser.parse_args(argv)

    browser = find_browser()
    report = measure(args.svg, browser, args.min_font)
    if args.png:
        report["png"] = str(render_png(args.svg, report["size"], browser))
    failed = failures(report, args.min_coverage)
    report["pass"] = not failed

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{args.svg.name}: size={report['size']} texts={report['texts']} coverage={report['coverage']} framed={report['framed']}")
        for key in CHECKS:
            print(f"  {key}: {len(report[key])}")
            for item in report[key][:40]:
                print("    " + json.dumps(item, ensure_ascii=False))
        print("PASS" if not failed else "FAIL: " + ", ".join(failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
