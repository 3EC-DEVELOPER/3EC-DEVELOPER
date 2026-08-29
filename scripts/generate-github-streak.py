#!/usr/bin/env python3
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from html import escape
from pathlib import Path


LOGIN = os.environ.get("GITHUB_LOGIN", "3EC-DEVELOPER")
OUTPUT = Path(os.environ.get("STREAK_OUTPUT", "assets/github-streak.svg"))
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
GRAPHQL_URL = "https://api.github.com/graphql"

FLAME_PATH = (
    "M13.5 2.1c.5 3.2-1.1 4.6-2.8 6.2-1.5 1.4-2.9 2.8-2.9 5.3"
    " 0 3.4 2.8 6.2 6.2 6.2s6.2-2.8 6.2-6.2c0-3.6-2.3-6.3-4.7-8.5"
    ".1 1.9-.8 3.3-2.2 4.2.2-2.5-1.1-4.6-3.1-6.4z"
)
TROPHY_PATH = (
    "M8 4h8v3h3v2a5 5 0 0 1-4.2 4.9A5.8 5.8 0 0 1 13 16.7V19h3v2H8v-2h3v-2.3"
    "a5.8 5.8 0 0 1-1.8-2.8A5 5 0 0 1 5 9V7h3V4zm-1 5a3 3 0 0 0 1.7 2.7A8 8 0 0 1 8 9V8H7v1zm9 0"
    "c0 .9-.2 1.8-.7 2.7A3 3 0 0 0 17 9V8h-1v1z"
)
GRAPH_PATHS = (
    '<rect x="5" y="12" width="3" height="7" rx="1" fill="#3fb950"/>'
    '<rect x="11" y="7" width="3" height="12" rx="1" fill="#58a6ff"/>'
    '<rect x="17" y="4" width="3" height="15" rx="1" fill="#f85149"/>'
)


def iso_date(value):
    return value.isoformat() + "T00:00:00Z"


def fetch_contribution_days():
    if not TOKEN:
        raise RuntimeError("GH_TOKEN or GITHUB_TOKEN is required to fetch contributions")

    today = dt.date.today()
    start = today - dt.timedelta(days=365)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    payload = {
        "query": query,
        "variables": {
            "login": LOGIN,
            "from": iso_date(start),
            "to": iso_date(today),
        },
    }
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        },
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))

    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"]))

    user = result.get("data", {}).get("user")
    if not user:
        raise RuntimeError(f"GitHub user not found: {LOGIN}")

    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = [
        {
            "date": day["date"],
            "count": int(day["contributionCount"]),
        }
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]
    days.sort(key=lambda item: item["date"])
    return days, int(calendar["totalContributions"])


def calculate_streaks(days):
    if not days:
        return 0, 0, None, None

    counts = {
        dt.date.fromisoformat(item["date"]): int(item["count"])
        for item in days
    }
    all_dates = sorted(counts)

    longest = 0
    running = 0
    for date in all_dates:
        if counts[date] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    end = all_dates[-1]
    if counts[end] == 0 and len(all_dates) > 1:
        end = all_dates[-2]

    current = 0
    cursor = end
    while cursor in counts and counts[cursor] > 0:
        current += 1
        cursor -= dt.timedelta(days=1)

    active_days = [date for date in all_dates if counts[date] > 0]
    first_active = active_days[0] if active_days else None
    last_active = active_days[-1] if active_days else None
    return current, longest, first_active, last_active


def render_svg(current, longest, total, first_active, last_active, generated_on):
    first_text = first_active.strftime("%d %b %Y") if first_active else "No activity"
    last_text = last_active.strftime("%d %b %Y") if last_active else "No activity"
    generated_text = generated_on.strftime("%d %b %Y")

    cards = [
        ("CURRENT STREAK", f"{current}", "#ff9f1c", "days", "flame"),
        ("LONGEST STREAK", f"{longest}", "#d29922", "days", "trophy"),
        ("YEARLY CONTRIBUTIONS", f"{total}", "#58a6ff", "total", "graph"),
    ]

    card_svg = []
    for index, (label, value, color, suffix, icon) in enumerate(cards):
        x = 12 + index * 272
        cx = x + 129
        font_size = 40 if len(value) <= 4 else 34 if len(value) <= 6 else 28
        if icon == "graph":
            icon_svg = f'<g transform="translate({cx - 12},32)">{GRAPH_PATHS}</g>'
        else:
            path = FLAME_PATH if icon == "flame" else TROPHY_PATH
            icon_svg = (
                f'<g transform="translate({cx - 14},28) scale(1.1667)" '
                f'fill="{color}"><path d="{path}"/></g>'
            )
        card_svg.append(
            f"""
  <rect x="{x}" y="12" width="257" height="151" rx="8" fill="#252c37"/>
  <circle cx="{cx}" cy="44" r="21" fill="{color}" opacity="0.12"/>
  {icon_svg}
  <text x="{cx}" y="78" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="10" fill="#8b949e" letter-spacing="1.5" font-weight="600">{escape(label)}</text>
  <text x="{cx}" y="126" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="{font_size}" font-weight="700" fill="#f0f6fc">{escape(value)}</text>
  <text x="{cx}" y="148" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="11" fill="#8b949e">{escape(suffix)}</text>"""
        )

    return f"""<svg width="830" height="205" viewBox="0 0 830 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub contribution streak for {escape(LOGIN)}">
  <rect width="830" height="205" rx="12" fill="#1b1f24"/>
{''.join(card_svg)}
  <text x="24" y="188" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="12" fill="#8b949e">Active range: {escape(first_text)} to {escape(last_text)}</text>
  <text x="806" y="188" text-anchor="end" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="12" fill="#8b949e">Updated {escape(generated_text)}</text>
</svg>
"""


def write_svg(svg):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")


def main():
    try:
        days, total = fetch_contribution_days()
        current, longest, first_active, last_active = calculate_streaks(days)
    except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
        if OUTPUT.exists():
            print(f"Keeping existing {OUTPUT}: {exc}", file=sys.stderr)
            return 0
        print(f"Could not fetch GitHub contributions: {exc}", file=sys.stderr)
        current, longest, total, first_active, last_active = 0, 0, 0, None, None

    svg = render_svg(
        current=current,
        longest=longest,
        total=total,
        first_active=first_active,
        last_active=last_active,
        generated_on=dt.date.today(),
    )
    write_svg(svg)
    print(f"Generated {OUTPUT}: current={current}, longest={longest}, total={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
