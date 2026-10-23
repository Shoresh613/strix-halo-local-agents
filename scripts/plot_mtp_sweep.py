"""Render assets/mtp-draft-sweep.svg from data/mtp-draft-sweep.csv (stdlib only)."""

import csv
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(ROOT / "data/mtp-draft-sweep.csv")))

runs = defaultdict(list)
for r in rows:
    runs[int(r["spec_draft_n_max"])].append(float(r["decode_tok_s"]))
points = sorted((n, statistics.median(v), len(v)) for n, v in runs.items())
best = max(points, key=lambda p: p[1])[0]

W, H = 640, 300
left, right, top, bottom = 48, 16, 56, 52
plot_w, plot_h = W - left - right, H - top - bottom
y_max = 100
bar_w = 24
band = plot_w / len(points)


def y(v):
    return top + plot_h * (1 - v / y_max)


out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
    'font-family="-apple-system, Segoe UI, Helvetica, Arial, sans-serif" role="img" '
    'aria-label="Decode speed by MTP draft length for Qwen3.6-35B-A3B on Strix Halo, ROCm">',
    "<style>",
    ".bg{fill:#fcfcfb}.t1{fill:#0b0b0b}.t2{fill:#52514e}.grid{stroke:#e4e3de}"
    ".base{stroke:#8a8983}.bar{fill:#b4b2a9}.best{fill:#2a78d6}",
    "@media (prefers-color-scheme: dark){.bg{fill:#1a1a19}.t1{fill:#ffffff}.t2{fill:#c3c2b7}"
    ".grid{stroke:#33332f}.base{stroke:#6b6a64}.bar{fill:#5f5e58}.best{fill:#3987e5}}",
    "</style>",
    f'<rect class="bg" width="{W}" height="{H}" rx="8"/>',
    f'<text class="t1" x="{left}" y="24" font-size="15" font-weight="600">'
    "Decode speed vs. MTP draft length (--spec-draft-n-max)</text>",
    f'<text class="t2" x="{left}" y="42" font-size="12">'
    "Qwen3.6-35B-A3B-MTP UD-Q4_K_XL · Ryzen AI Max+ 395 · llama.cpp ROCm via Lemonade · tokens/s</text>",
]

for v in range(0, y_max + 1, 20):
    out.append(f'<line class="grid" x1="{left}" x2="{W - right}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>')
    out.append(f'<text class="t2" x="{left - 8}" y="{y(v) + 4:.1f}" font-size="11" text-anchor="end">{v}</text>')

for i, (n, v, k) in enumerate(points):
    cx = left + band * (i + 0.5)
    x0, x1, yt, yb = cx - bar_w / 2, cx + bar_w / 2, y(v), y(0)
    r = 4  # rounded data end, square at the baseline
    path = (f"M{x0:.1f},{yb:.1f} V{yt + r:.1f} Q{x0:.1f},{yt:.1f} {x0 + r:.1f},{yt:.1f} "
            f"H{x1 - r:.1f} Q{x1:.1f},{yt:.1f} {x1:.1f},{yt + r:.1f} V{yb:.1f} Z")
    cls = "best" if n == best else "bar"
    label = f"{v:.1f}" + (f" (n={k})" if k > 1 else "")
    out.append(f'<path class="{cls}" d="{path}"><title>{n} draft tokens: {label} tok/s</title></path>')
    weight = ' font-weight="600"' if n == best else ""
    out.append(f'<text class="t1" x="{cx:.1f}" y="{yt - 6:.1f}" font-size="12" text-anchor="middle"{weight}>{v:.1f}</text>')
    out.append(f'<text class="t2" x="{cx:.1f}" y="{yb + 18:.1f}" font-size="12" text-anchor="middle">{n}</text>')

out.append(f'<line class="base" x1="{left}" x2="{W - right}" y1="{y(0):.1f}" y2="{y(0):.1f}"/>')
out.append(f'<text class="t2" x="{left}" y="{H - 10}" font-size="11">'
           "Draft tokens. 3 = median of 3 runs (80.6–81.2); others single runs; 7 not tested. "
           "Same prompt, fresh chat each run.</text>")
out.append("</svg>")

(ROOT / "assets/mtp-draft-sweep.svg").write_text("\n".join(out) + "\n")
print("wrote assets/mtp-draft-sweep.svg", points)
