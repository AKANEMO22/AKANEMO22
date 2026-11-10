"""
Generate the SVG assets used by the profile README.

  assets/header.svg     - animated self-attention header (static content)
  assets/attention.svg  - contribution calendar rendered as an attention map

Only the Python standard library is used. Requires the environment variable
GITHUB_TOKEN (any token able to read public profile data) for attention.svg.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import urllib.request
from collections import Counter
from xml.sax.saxutils import escape

LOGIN = os.environ.get("PROFILE_LOGIN", "AKANEMO22")
ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

BG = "#0d1117"
BORDER = "#30363d"
FG = "#e6edf3"
MUTED = "#8b949e"
FAINT = "#484f58"
ACCENT = "#58a6ff"


# --------------------------------------------------------------------------- #
# Header                                                                      #
# --------------------------------------------------------------------------- #
def build_header() -> str:
    w, h = 900, 240
    tokens = ["learn", "model", "agent", "retrieve", "speak", "ship"]
    xs = [548 + i * 62 for i in range(len(tokens))]
    top_y, bot_y = 66, 192

    # (query index, key index, weight) - a hand-tuned attention pattern
    edges = [
        (0, 1, 0.9), (0, 0, 0.5), (1, 2, 0.8), (1, 3, 0.45), (2, 3, 0.95),
        (2, 4, 0.55), (3, 1, 0.6), (3, 5, 0.4), (4, 2, 0.7), (4, 4, 0.5),
        (5, 2, 0.65), (5, 0, 0.35), (1, 5, 0.3), (3, 3, 0.5), (0, 4, 0.25),
    ]

    paths = []
    for n, (q, k, wgt) in enumerate(edges):
        x1, x2 = xs[q], xs[k]
        d = f"M{x1} {top_y + 12} C{x1} {top_y + 64},{x2} {bot_y - 68},{x2} {bot_y - 16}"
        lo = round(wgt * 0.15, 2)
        paths.append(
            f'<path d="{d}" stroke="{ACCENT}" stroke-width="{0.6 + wgt * 1.8:.2f}" '
            f'fill="none" stroke-linecap="round" opacity="{wgt}">'
            f'<animate attributeName="opacity" values="{wgt};{lo};{wgt}" '
            f'dur="{3.2 + (n % 5) * 0.6:.1f}s" begin="{n * 0.27:.2f}s" repeatCount="indefinite"/>'
            f"</path>"
        )

    tok_svg = []
    for x, t in zip(xs, tokens):
        for y in (top_y, bot_y):
            tok_svg.append(
                f'<text x="{x}" y="{y}" text-anchor="middle" font-family="{MONO}" '
                f'font-size="12" fill="{MUTED}">{t}</text>'
            )
        tok_svg.append(f'<circle cx="{x}" cy="{top_y + 10}" r="2.2" fill="{FG}"/>')
        tok_svg.append(f'<circle cx="{x}" cy="{bot_y - 14}" r="2.2" fill="{FG}"/>')

    subtitle = "applied ai engineer in training"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M24 0H0V24" fill="none" stroke="#161b22" stroke-width="1"/>
    </pattern>
    <clipPath id="type"><rect x="40" y="128" width="330" height="26">
      <animate attributeName="width" from="0" to="330" dur="2.2s" begin="0s" fill="freeze"
               calcMode="discrete" values="{';'.join(str(int(330 * i / len(subtitle))) for i in range(len(subtitle) + 1))}"/>
    </rect></clipPath>
  </defs>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="url(#grid)" opacity="0.6"/>

  <text x="40" y="44" font-family="{MONO}" font-size="12" fill="{FAINT}">AKANEMO22 / README.md</text>
  <text x="40" y="112" font-family="{SANS}" font-size="54" font-weight="700" fill="{FG}" letter-spacing="-1">Do Chimi</text>
  <text x="40" y="148" font-family="{MONO}" font-size="17" fill="{ACCENT}" clip-path="url(#type)">{subtitle}</text>
  <rect x="370" y="134" width="9" height="18" fill="{ACCENT}">
    <animate attributeName="x" from="40" to="370" dur="2.2s" begin="0s" fill="freeze"
             calcMode="discrete" values="{';'.join(str(40 + int(330 * i / len(subtitle))) for i in range(len(subtitle) + 1))}"/>
    <animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>
  </rect>
  <text x="40" y="186" font-family="{SANS}" font-size="14" fill="{MUTED}">FPT University  ·  LLM Agents  ·  Retrieval  ·  Speech  ·  Explainability</text>

  <line x1="508" y1="40" x2="508" y2="200" stroke="{BORDER}"/>
  {''.join(paths)}
  {''.join(tok_svg)}
  <text x="{xs[0] - 20}" y="222" font-family="{MONO}" font-size="10.5" fill="{FAINT}">fig. 1 - self-attention over the things I work on</text>
</svg>
"""


# --------------------------------------------------------------------------- #
# Contribution attention map                                                  #
# --------------------------------------------------------------------------- #
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}
"""


def fetch_calendar(token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{LOGIN}-profile-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def streaks(days: list[dict]) -> tuple[int, int]:
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    current = 0
    seq = list(days)
    if seq and seq[-1]["contributionCount"] == 0:  # today not counted yet
        seq = seq[:-1]
    for d in reversed(seq):
        if d["contributionCount"] == 0:
            break
        current += 1
    return current, longest


def build_attention(cal: dict) -> str:
    weeks = cal["weeks"]
    days = [d for wk in weeks for d in wk["contributionDays"]]
    counts = sorted(c for c in (d["contributionCount"] for d in days) if c > 0)

    def level(c: int) -> int:
        if c == 0 or not counts:
            return 0
        q = [counts[int(len(counts) * p)] for p in (0.25, 0.5, 0.75)]
        return 1 + sum(c > t for t in q)

    palette = ["#161b22", "#0c2d6b", "#1158c7", "#388bfd", "#a5d6ff"]

    cell, gap = 13, 3
    step = cell + gap
    left, top = 56, 92
    w = left + len(weeks) * step + 24
    h = 316

    cols, months = [], []
    last_month = None
    for i, wk in enumerate(weeks):
        x = left + i * step
        first = dt.date.fromisoformat(wk["contributionDays"][0]["date"])
        if first.month != last_month and first.day <= 7:
            months.append(
                f'<text x="{x}" y="{top - 10}" font-family="{MONO}" font-size="10" '
                f'fill="{MUTED}">{first.strftime("%b")}</text>'
            )
            last_month = first.month
        rects = []
        for d in wk["contributionDays"]:
            y = top + d["weekday"] * step
            c = d["contributionCount"]
            rects.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" '
                f'fill="{palette[level(c)]}"><title>{d["date"]}: {c}</title></rect>'
            )
        cols.append(f'<g class="c" style="animation-delay:{i * 22}ms">{"".join(rects)}</g>')

    wd = "".join(
        f'<text x="24" y="{top + r * step + 10}" font-family="{MONO}" font-size="10" fill="{FAINT}">{n}</text>'
        for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    grid_w = len(weeks) * step
    grid_h = 7 * step
    scan = (
        f'<rect x="{left}" y="{top - 3}" width="{step * 2}" height="{grid_h + 3}" rx="3" fill="{ACCENT}" opacity="0.07">'
        f'<animate attributeName="x" from="{left}" to="{left + grid_w - step * 2}" dur="7s" repeatCount="indefinite"/>'
        f"</rect>"
    )

    current, longest = streaks(days)
    active = sum(1 for d in days if d["contributionCount"] > 0)
    peak = max(days, key=lambda d: d["contributionCount"])
    by_wd = Counter()
    for d in days:
        by_wd[d["weekday"]] += d["contributionCount"]
    wd_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    busiest = wd_names[by_wd.most_common(1)[0][0]] if by_wd else "-"
    peak_date = dt.date.fromisoformat(peak["date"]).strftime("%b %d")

    metrics = [
        ("total_contributions", f'{cal["totalContributions"]:,}'),
        ("active_days", f"{active}"),
        ("current_streak", f"{current}d"),
        ("longest_streak", f"{longest}d"),
        ("peak_day", f'{peak["contributionCount"]} · {peak_date}'),
        ("busiest_weekday", busiest),
    ]
    mw = grid_w / len(metrics)
    my = top + grid_h + 44
    met = []
    for i, (k, v) in enumerate(metrics):
        x = left + i * mw
        met.append(
            f'<text x="{x:.1f}" y="{my}" font-family="{MONO}" font-size="10.5" fill="{MUTED}">{k}</text>'
            f'<text x="{x:.1f}" y="{my + 26}" font-family="{SANS}" font-size="20" font-weight="600" fill="{FG}">{escape(v)}</text>'
        )

    legend_x = left + grid_w - 5 * (cell + 4) - 30
    legend = "".join(
        f'<rect x="{legend_x + i * (cell + 4)}" y="22" width="{cell}" height="{cell}" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(palette)
    )
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <style>
    .c {{ animation: f .6s ease-out both; }}
    @keyframes f {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  </style>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
  <text x="24" y="36" font-family="{SANS}" font-size="15" fill="{FG}"><tspan font-weight="700">Figure 2.</tspan><tspan fill="{MUTED}"> Contribution attention map over the last 52 weeks.</tspan></text>
  <text x="24" y="56" font-family="{MONO}" font-size="11" fill="{FAINT}">A[week, day] = softmax(activity / sqrt(d))  ·  intensity binned by quartile of non-zero days</text>
  <text x="{legend_x - 34}" y="33" font-family="{MONO}" font-size="10" fill="{FAINT}">low</text>
  {legend}
  <text x="{legend_x + 5 * (cell + 4) + 2}" y="33" font-family="{MONO}" font-size="10" fill="{FAINT}">high</text>
  {''.join(months)}
  {wd}
  {''.join(cols)}
  {scan}
  <line x1="{left}" y1="{my - 22}" x2="{left + grid_w}" y2="{my - 22}" stroke="{BORDER}"/>
  {''.join(met)}
  <text x="{w - 24}" y="{h - 14}" text-anchor="end" font-family="{MONO}" font-size="9.5" fill="{FAINT}">regenerated {today} GMT+7 by github actions</text>
</svg>
"""


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "header.svg").write_text(build_header(), encoding="utf-8")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not set; skipping attention.svg")
        return
    cal = fetch_calendar(token)
    (ASSETS / "attention.svg").write_text(build_attention(cal), encoding="utf-8")
    print(f"ok: {cal['totalContributions']} contributions")


if __name__ == "__main__":
    main()
