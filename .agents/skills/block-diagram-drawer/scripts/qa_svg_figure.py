"""Render-truth QA gate for paper-style SVG figures built with figkit.

The SVG is rendered in headless Chrome/Chromium/Edge and measured with the
browser's own text layout, so width estimates in the build script never decide
acceptance. Thresholds come from a study of 359 method figures in papers
published at robotics, ML and CV venues (references/paper-figure-study.md).

Failing checks:
- overflow:     text escaping its container (text[data-in] -> [data-box]) or the canvas
- collide:      text/text bounding-box collisions
- boxOverlap:   sibling cards/chips/thumbnails that partially overlap
- lineText:     connector or curve strokes crossing a label that no opaque,
                later-drawn container covers
- smallText:    labels printing below --min-pt (6 pt), or below --note-min-pt (5 pt)
                for labels marked as the note tier; math scripts are exempt
- longText:     labels longer than --max-words words outside example content
                (`example` cards and speech bubbles hold prompts, code and traces)
- lowContrast:  label text on its container with a contrast ratio below 3:1
- medianPt:     the figure's median label prints below 5 pt (warning below 6 pt)
- words:        label words outside example content above the fail budget
                (90 words for a 516 by 215 pt figure, scaled by printed area;
                warning above 65)
- exampleWords: words inside example content above 60 (warning above 30)
- coverage:     share of the canvas covered by content below --min-coverage (0.40)

Warnings (reported, never failing): median label below 6 pt, words or example words
above their warning budgets, six or more fill hues, containers nested three deep,
more than 35% of labels bold, and label contrast below 4.5:1.

Usage:
    python qa_svg_figure.py figure.svg [--png] [--json] [--min-pt 6] [--note-min-pt 5]
                            [--max-words 6] [--word-warn 65] [--word-fail 90] [--min-coverage 0.4]
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
from dataclasses import asdict, dataclass
from pathlib import Path

CHECKS = ("overflow", "collide", "boxOverlap", "lineText", "smallText", "longText", "lowContrast")
REFERENCE_AREA_PT2 = 516.0 * 215.0  # a text-width figure at the study's median aspect ratio (2.4)

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


@dataclass(frozen=True)
class Limits:
    """Gate thresholds; defaults follow the published-figure study."""

    min_pt: float = 6.0
    note_min_pt: float = 5.0
    median_warn_pt: float = 6.0
    median_fail_pt: float = 5.0
    max_words: int = 6
    word_warn: int = 65
    word_fail: int = 90
    example_warn: int = 30
    example_fail: int = 60
    hue_warn: int = 6
    nesting_warn: int = 3
    bold_warn: float = 0.35
    contrast_fail: float = 3.0
    contrast_warn: float = 4.5
    min_coverage: float = 0.40
    print_width_pt: float | None = None
    min_px: float | None = None  # legacy pixel minimum at 1400 px width; replaces min_pt when given


JS = r"""
const svg=document.querySelector('svg');
const W=svg.viewBox.baseVal.width,H=svg.viewBox.baseVal.height;
const R=b=>({x:b.x,y:b.y,w:b.width,h:b.height});
const L_=__LIMITS__;
const boxes={};
svg.querySelectorAll('[data-box]').forEach(e=>{boxes[e.dataset.box]=Object.assign(R(e.getBBox()),{kind:e.dataset.kind,id:e.dataset.box});});
const PRINT=parseFloat(svg.dataset.printWidthPt)||L_.print_width_pt||(W>=1000?516:252);
const MIN_FONT=L_.min_px?L_.min_px*W/1400:L_.min_pt*W/PRINT, NOTE_FONT=L_.note_min_pt*W/PRINT;
const rgb=s=>{const m=/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/.exec(s||''); if(!m||(m[4]!==undefined&&+m[4]===0)) return null; return [+m[1],+m[2],+m[3]];};
const lum=c=>{const f=v=>{v/=255; return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);}; return 0.2126*f(c[0])+0.7152*f(c[1])+0.0722*f(c[2]);};
const contrast=(a,b)=>{const x=lum(a),y=lum(b); return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05);};
const hsl=c=>{const r=c[0]/255,g=c[1]/255,b=c[2]/255,mx=Math.max(r,g,b),mn=Math.min(r,g,b),l=(mx+mn)/2,d=mx-mn;
  if(!d) return [0,0,l]; const s=l>0.5?d/(2-mx-mn):d/(mx+mn); let h=mx===r?(g-b)/d+(g<b?6:0):mx===g?(b-r)/d+2:(r-g)/d+4; return [h*60,s,l];};
// Split on ordinary spaces only: typeset math uses thin and four-per-em spaces inside one expression.
const wordCount=s=>s.split(/[ \t\n]+/).reduce((n,tok)=>{const cjk=(tok.match(/[\u3040-\u30ff\u3400-\u9fff]/g)||[]).length;
  return n+(cjk?Math.ceil(cjk/2):0)+(/[A-Za-z0-9]/.test(tok.replace(/[\u3040-\u30ff\u3400-\u9fff]/g,''))?1:0);},0);
const overflow=[],texts=[],textEls=[],smallText=[],longText=[],lowContrast=[],contrastWarn=[],sizes=[];
let words=0,exampleWords=0,bold=0,labels=0;
svg.querySelectorAll('text').forEach(t=>{
  const b=R(t.getBBox()); if(!b.w) return; b.s=t.textContent.slice(0,40); texts.push(b); textEls.push(t);
  if(t.closest('symbol,defs')) return;
  const cs=getComputedStyle(t), fs=parseFloat(cs.fontSize), note=t.dataset.tier==='note';
  if(fs<(note?NOTE_FONT:MIN_FONT)-0.01) smallText.push({s:b.s,size:fs,pt:+(fs*PRINT/W).toFixed(2),note});
  const home=t.dataset.in?svg.querySelector('[data-box="'+t.dataset.in+'"]'):null;
  const n=wordCount(t.textContent);
  if(home&&home.dataset.kind==='example'){exampleWords+=n;}
  else{words+=n; labels++; sizes.push(fs); if(parseInt(cs.fontWeight,10)>=600) bold++;
    if(n>L_.max_words) longText.push({s:t.textContent.slice(0,60),words:n});}
  if(home){const bg=rgb(getComputedStyle(home).fill), fg=rgb(cs.fill);
    if(bg&&fg){const c=contrast(fg,bg); if(c<L_.contrast_fail) lowContrast.push({s:b.s,ratio:+c.toFixed(2)}); else if(c<L_.contrast_warn) contrastWarn.push({s:b.s,ratio:+c.toFixed(2)});}}
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
const bins=new Set();
svg.querySelectorAll('[data-box]').forEach(e=>{
  if(!['card','chip','panel','example'].includes(e.dataset.kind)) return;
  const c=rgb(getComputedStyle(e).fill); if(!c) return; const [h,s,l]=hsl(c);
  if(s>=0.25&&l>0.08&&l<0.97) bins.add(Math.round(h/15)%24);
});
const holders=Object.values(boxes).filter(b=>['panel','card','example'].includes(b.kind));
let maxNesting=0;
Object.values(boxes).forEach(b=>{
  const d=holders.filter(c=>c!==b&&c.w*c.h>b.w*b.h+1&&inside(b,c)).length; if(d>maxNesting) maxNesting=d;
});
sizes.sort((a,b)=>a-b);
const medianPx=sizes.length?sizes[Math.floor((sizes.length-1)/2)]:null;
const out={size:[W,H],texts:texts.length,printWidthPt:PRINT,minFontPx:+MIN_FONT.toFixed(1),
  overflow,collide,boxOverlap,lineText,smallText,longText,lowContrast,contrastWarn,
  medianPt:medianPx?+(medianPx*PRINT/W).toFixed(2):null,words,exampleWords,fillHues:bins.size,maxNesting,
  boldShare:labels?+(bold/labels).toFixed(2):0,coverage:+(cov/n).toFixed(3),framed:+(pcov/n).toFixed(3)};
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


def word_budget(report: dict, limits: Limits) -> tuple[int, int]:
    """Warn and fail word budgets scaled by the figure's printed area, clamped to 0.5x..1.6x the reference."""
    w, h = report["size"]
    printed = report["printWidthPt"]
    ratio = min(1.6, max(0.5, printed * printed * h / w / REFERENCE_AREA_PT2))
    return round(limits.word_warn * ratio), round(limits.word_fail * ratio)


def measure(svg_path: Path, browser: str, limits: Limits | None = None) -> dict:
    """Render the SVG in headless Chrome and return the QA report."""
    limits = limits or Limits()
    svg = svg_path.read_text(encoding="utf-8")
    script = JS.replace("__LIMITS__", json.dumps(asdict(limits)))
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
    report = json.loads(html.unescape(match.group(1)))
    report["wordWarn"], report["wordFail"] = word_budget(report, limits)
    return report


def render_png(svg_path: Path, size: list[float], browser: str, scale: int = 2) -> Path:
    out = svg_path.with_suffix(".png")
    subprocess.run(
        [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--force-device-scale-factor={scale}",
         f"--window-size={int(size[0])},{int(size[1])}", f"--screenshot={out}", svg_path.resolve().as_uri()],
        capture_output=True, timeout=180, check=True,
    )
    return out


def failures(report: dict, limits: Limits | None = None) -> list[str]:
    limits = limits or Limits()
    failed = [f"{key}={len(report[key])}" for key in CHECKS if report.get(key)]
    if report.get("medianPt") is not None and report["medianPt"] < limits.median_fail_pt:
        failed.append(f"medianPt={report['medianPt']} < {limits.median_fail_pt}")
    if "wordFail" in report and report["words"] > report["wordFail"]:
        failed.append(f"words={report['words']} > {report['wordFail']}")
    if report.get("exampleWords", 0) > limits.example_fail:
        failed.append(f"exampleWords={report['exampleWords']} > {limits.example_fail}")
    if report["coverage"] < limits.min_coverage:
        failed.append(f"coverage={report['coverage']} < {limits.min_coverage}")
    return failed


def warnings(report: dict, limits: Limits | None = None) -> list[str]:
    limits = limits or Limits()
    warned = []
    median = report.get("medianPt")
    if median is not None and limits.median_fail_pt <= median < limits.median_warn_pt:
        warned.append(f"medianPt={median} < {limits.median_warn_pt}")
    if "wordWarn" in report and report["wordWarn"] < report["words"] <= report["wordFail"]:
        warned.append(f"words={report['words']} > {report['wordWarn']} (exemplar figures use about 40)")
    if limits.example_warn < report.get("exampleWords", 0) <= limits.example_fail:
        warned.append(f"exampleWords={report['exampleWords']} > {limits.example_warn}")
    if report.get("fillHues", 0) >= limits.hue_warn:
        warned.append(f"fillHues={report['fillHues']} >= {limits.hue_warn}")
    if report.get("maxNesting", 0) >= limits.nesting_warn:
        warned.append(f"maxNesting={report['maxNesting']} >= {limits.nesting_warn}")
    if report.get("boldShare", 0) > limits.bold_warn:
        warned.append(f"boldShare={report['boldShare']} > {limits.bold_warn}")
    if report.get("contrastWarn"):
        warned.append(f"contrast below {limits.contrast_warn}:1 on {len(report['contrastWarn'])} label(s)")
    return warned


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("svg", type=Path)
    parser.add_argument("--png", action="store_true", help="also write a 2x PNG next to the SVG")
    parser.add_argument("--json", action="store_true", help="print the full JSON report")
    defaults = Limits()
    parser.add_argument("--min-pt", type=float, default=defaults.min_pt, help="smallest printed label size in points")
    parser.add_argument("--note-min-pt", type=float, default=defaults.note_min_pt, help="smallest size for note-tier labels")
    parser.add_argument("--print-width-pt", type=float, default=None,
                        help="printed width of the canvas; default from the SVG, else 516 (>= 1000 px) or 252")
    parser.add_argument("--max-words", type=int, default=defaults.max_words, help="longest label outside example content")
    parser.add_argument("--word-warn", type=int, default=defaults.word_warn, help="label words for a 516 x 215 pt figure, warning")
    parser.add_argument("--word-fail", type=int, default=defaults.word_fail, help="label words for a 516 x 215 pt figure, failure")
    parser.add_argument("--example-fail", type=int, default=defaults.example_fail, help="words inside example content, failure")
    parser.add_argument("--min-coverage", type=float, default=defaults.min_coverage)
    parser.add_argument("--min-font", type=float, default=None,
                        help="legacy: smallest label size in px at 1400 px width; replaces --min-pt when given")
    args = parser.parse_args(argv)

    limits = Limits(min_pt=args.min_pt, note_min_pt=args.note_min_pt, print_width_pt=args.print_width_pt,
                    max_words=args.max_words, word_warn=args.word_warn, word_fail=args.word_fail,
                    example_fail=args.example_fail, min_coverage=args.min_coverage, min_px=args.min_font)
    browser = find_browser()
    report = measure(args.svg, browser, limits)
    if args.png:
        report["png"] = str(render_png(args.svg, report["size"], browser))
    failed, warned = failures(report, limits), warnings(report, limits)
    report["pass"], report["warnings"] = not failed, warned

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{args.svg.name}: size={report['size']} print={report['printWidthPt']:g}pt min={report['minFontPx']}px "
              f"median={report['medianPt']}pt words={report['words']}/{report['wordWarn']}/{report['wordFail']} "
              f"example={report['exampleWords']} hues={report['fillHues']} nesting={report['maxNesting']} "
              f"bold={report['boldShare']} coverage={report['coverage']}")
        for key in CHECKS:
            print(f"  {key}: {len(report[key])}")
            for item in report[key][:40]:
                print("    " + json.dumps(item, ensure_ascii=False))
        for line in warned:
            print("  warning: " + line)
        print("PASS" if not failed else "FAIL: " + ", ".join(failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
