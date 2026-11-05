"""Refresh the dated profile stats card with the signed-in GitHub account.

Run locally with `gh auth login` completed. No token is written to the repo.
"""

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
ACCOUNT = "Art3MasA005"


def graphql(query):
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


viewer = graphql("query { viewer { login contributionsCollection { contributionYears } } }")["viewer"]
if viewer["login"] != ACCOUNT:
    raise RuntimeError(f"Signed in as {viewer['login']}, expected {ACCOUNT}")

years = viewer["contributionsCollection"]["contributionYears"]
fields = " ".join(
    f'y{year}: contributionsCollection(from:"{year}-01-01T00:00:00Z",'
    f'to:"{year}-12-31T23:59:59Z") '
    "{ totalCommitContributions totalPullRequestContributions totalIssueContributions }"
    for year in years
)
collections = graphql(f"query {{ viewer {{ {fields} }} }}")["viewer"]
commits = sum(item["totalCommitContributions"] for item in collections.values())
prs = sum(item["totalPullRequestContributions"] for item in collections.values())
issues = sum(item["totalIssueContributions"] for item in collections.values())
today = datetime.now(timezone(timedelta(hours=6))).strftime("%d %b %Y")

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="350" height="165" viewBox="0 0 350 165" role="img" aria-label="GitHub stats: {commits:,} counted commits, {prs} pull requests, {issues} issues; updated {today}">
  <rect x="0.5" y="0.5" width="349" height="164" rx="7" fill="#0d1117" stroke="#30363d"/>
  <text x="17" y="28" fill="#58a6ff" font-family="Segoe UI, Arial, sans-serif" font-size="19">GitHub Stats</text>
  <path d="M17 39 H333" stroke="#30363d"/>
  <text x="17" y="89" fill="#e6edf3" font-family="Segoe UI, Arial, sans-serif" font-size="40" font-weight="700">{commits:,}</text>
  <text x="18" y="109" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="12">counted commits, public + private</text>
  <text x="18" y="137" fill="#c9d1d9" font-family="Segoe UI, Arial, sans-serif" font-size="13">Pull requests: {prs}   ·   Issues: {issues}</text>
  <text x="18" y="156" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="10">Updated {today}</text>
</svg>
'''
ElementTree.fromstring(svg)
output = ROOT / "assets" / "github-stats.svg"
output.write_text(svg, encoding="utf-8")
print(f"Wrote {output}: {commits:,} commits, {prs} PRs, {issues} issue(s)")
