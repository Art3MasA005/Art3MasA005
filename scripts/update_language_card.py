"""Refresh the profile's dated public-repository language card."""

import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
ACCOUNT = "Art3MasA005"
COLORS = {
    "Python": "#3572A5",
    "Dart": "#00B4AB",
    "HTML": "#e34c26",
    "JavaScript": "#f1e05a",
    "C": "#777777",
    "Java": "#b07219",
    "C++": "#f34b7d",
}
FALLBACK_COLORS = ("#a371f7", "#3fb950", "#db6d28", "#d29922", "#8b949e")


def public_repositories():
    repositories = []
    page = 1
    while True:
        result = subprocess.run(
            ["gh", "api", f"users/{ACCOUNT}/repos?per_page=100&type=owner&page={page}"],
            check=True,
            capture_output=True,
            text=True,
        )
        batch = json.loads(result.stdout)
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


counts = Counter(
    repository["language"]
    for repository in public_repositories()
    if repository["language"] and not repository["fork"] and repository["name"] != ACCOUNT
)
preferred = {name: index for index, name in enumerate(("Python", "Dart", "HTML", "JavaScript", "C"))}
leaders = sorted(counts.items(), key=lambda pair: (-pair[1], preferred.get(pair[0], 100), pair[0]))[:5]
total = sum(count for _, count in leaders)
today = datetime.now(timezone(timedelta(hours=6))).strftime("%d %b %Y")

parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="350" height="165" viewBox="0 0 350 165" role="img" aria-label="Top languages by public repository">',
    '<rect x="0.5" y="0.5" width="349" height="164" rx="7" fill="#0d1117" stroke="#30363d"/>',
    '<text x="17" y="28" fill="#58a6ff" font-family="Segoe UI, Arial, sans-serif" font-size="19">Top Languages by Repo</text>',
    '<path d="M17 39 H333" stroke="#30363d"/>',
]

for index, (language, count) in enumerate(leaders):
    y = 58 + index * 20
    color = COLORS.get(language, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])
    parts.extend(
        (
            f'<rect x="19" y="{y - 9}" width="10" height="10" fill="{color}"/>',
            f'<text x="39" y="{y}" fill="#c9d1d9" font-family="Segoe UI, Arial, sans-serif" font-size="12">{escape(language)}</text>',
            f'<text x="151" y="{y}" text-anchor="end" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">{count}</text>',
        )
    )

start = -math.pi / 2
for index, (language, count) in enumerate(leaders):
    end = start + 2 * math.pi * count / total
    outer_start = (260 + 50 * math.cos(start), 96 + 50 * math.sin(start))
    outer_end = (260 + 50 * math.cos(end), 96 + 50 * math.sin(end))
    inner_end = (260 + 30 * math.cos(end), 96 + 30 * math.sin(end))
    inner_start = (260 + 30 * math.cos(start), 96 + 30 * math.sin(start))
    large = int(end - start > math.pi)
    color = COLORS.get(language, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])
    path = (
        f"M{outer_start[0]:.2f},{outer_start[1]:.2f} "
        f"A50,50 0 {large} 1 {outer_end[0]:.2f},{outer_end[1]:.2f} "
        f"L{inner_end[0]:.2f},{inner_end[1]:.2f} "
        f"A30,30 0 {large} 0 {inner_start[0]:.2f},{inner_start[1]:.2f} Z"
    )
    parts.append(f'<path d="{path}" fill="{color}" stroke="#0d1117" stroke-width="1.5"/>')
    start = end

parts.extend(
    (
        f'<text x="260" y="101" text-anchor="middle" fill="#c9d1d9" font-family="Segoe UI, Arial, sans-serif" font-size="11">{total} repos</text>',
        f'<text x="18" y="156" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="10">Updated {today}</text>',
        '</svg>',
    )
)
svg = "\n".join(parts) + "\n"
ElementTree.fromstring(svg)
output = ROOT / "assets" / "top-languages.svg"
output.write_text(svg, encoding="utf-8")
print(f"Wrote {output}: {dict(leaders)}")
