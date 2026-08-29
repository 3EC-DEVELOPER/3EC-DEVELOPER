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
CARD_START = dt.date(2024, 4, 13)

FIRE_PATH = (
    "M 1.5 0.67 C 1.5 0.67 2.24 3.32 2.24 5.47 C 2.24 7.53 0.89 9.2 "
    "-1.17 9.2 C -3.23 9.2 -4.79 7.53 -4.79 5.47 L -4.76 5.11 C -6.78 "
    "7.51 -8 10.62 -8 13.99 C -8 18.41 -4.42 22 0 22 C 4.42 22 8 "
    "18.41 8 13.99 C 8 8.6 5.41 3.79 1.5 0.67 Z M -0.29 19 C -2.07 19 "
    "-3.51 17.6 -3.51 15.86 C -3.51 14.24 -2.46 13.1 -0.7 12.74 C 1.07 "
    "12.38 2.9 11.53 3.92 10.16 C 4.31 11.45 4.51 12.81 4.51 14.2 C "
    "4.51 16.85 2.36 19 -0.29 19 Z"
)


def iso_start(value):
    return f"{value.isoformat()}T00:00:00Z"


def iso_end(value):
    return f"{value.isoformat()}T23:59:59Z"


def github_graphql(query, variables):
    if not TOKEN:
        raise RuntimeError("GH_TOKEN or GITHUB_TOKEN is required to fetch contributions")

    payload = {"query": query, "variables": variables}
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

    return result["data"]


def fetch_contribution_days():
    today = dt.date.today()
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
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

    days_by_date = {}
    cursor = CARD_START
    while cursor <= today:
        chunk_end = min(cursor + dt.timedelta(days=364), today)
        data = github_graphql(
            query,
            {
                "login": LOGIN,
                "from": iso_start(cursor),
                "to": iso_end(chunk_end),
            },
        )
        user = data.get("user")
        if not user:
            raise RuntimeError(f"GitHub user not found: {LOGIN}")

        calendar = user["contributionsCollection"]["contributionCalendar"]
        for week in calendar["weeks"]:
            for day in week["contributionDays"]:
                day_date = dt.date.fromisoformat(day["date"])
                if CARD_START <= day_date <= today:
                    days_by_date[day_date] = int(day["contributionCount"])

        cursor = chunk_end + dt.timedelta(days=1)

    return [{"date": date, "count": days_by_date.get(date, 0)} for date in sorted(days_by_date)]


def calculate_stats(days):
    if not days:
        return {
            "total": 0,
            "first_active": None,
            "current": 0,
            "current_start": None,
            "current_end": None,
            "longest": 0,
            "longest_start": None,
            "longest_end": None,
        }

    counts = {item["date"]: item["count"] for item in days}
    all_dates = sorted(counts)
    active_dates = [date for date in all_dates if counts[date] > 0]

    longest = 0
    longest_start = None
    longest_end = None
    running = 0
    running_start = None
    for date in all_dates:
        if counts[date] > 0:
            if running == 0:
                running_start = date
            running += 1
            if running > longest:
                longest = running
                longest_start = running_start
                longest_end = date
        else:
            running = 0
            running_start = None

    today = all_dates[-1]
    current = 0
    current_start = None
    current_end = None
    if counts[today] > 0:
        current_end = today
        cursor = today
        while cursor in counts and counts[cursor] > 0:
            current += 1
            current_start = cursor
            cursor -= dt.timedelta(days=1)

    return {
        "total": sum(counts.values()),
        "first_active": active_dates[0] if active_dates else None,
        "current": current,
        "current_start": current_start,
        "current_end": current_end,
        "longest": longest,
        "longest_start": longest_start,
        "longest_end": longest_end,
    }


def format_date(value, current_year):
    if not value:
        return ""
    if value.year == current_year:
        return value.strftime("%-d %b")
    return value.strftime("%-d %b %Y")


def format_range(start, end, current_year, present=False):
    if present and start:
        return f"{format_date(start, current_year)} - Present"
    if not start or not end:
        return ""
    if start == end:
        return format_date(start, current_year)
    return f"{format_date(start, current_year)} - {format_date(end, current_year)}"


def render_svg(stats, generated_on):
    current_year = generated_on.year
    total = str(stats["total"])
    current = str(stats["current"])
    longest = str(stats["longest"])
    total_range = format_range(stats["first_active"], generated_on, current_year, present=True)
    current_range = format_range(stats["current_start"], stats["current_end"], current_year)
    if not current_range:
        current_range = format_date(generated_on, current_year)
    longest_range = format_range(stats["longest_start"], stats["longest_end"], current_year)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" style="isolation: isolate" viewBox="0 0 495 195" width="495px" height="195px" direction="ltr" role="img" aria-label="GitHub streak stats for {escape(LOGIN)}">
  <style>
    @keyframes currstreak {{
      0% {{ font-size: 3px; opacity: 0.2; }}
      80% {{ font-size: 34px; opacity: 1; }}
      100% {{ font-size: 28px; opacity: 1; }}
    }}
    @keyframes fadein {{
      0% {{ opacity: 0; }}
      100% {{ opacity: 1; }}
    }}
  </style>
  <defs>
    <clipPath id="outer_rectangle">
      <rect width="495" height="195" rx="4.5"/>
    </clipPath>
    <mask id="mask_out_ring_behind_fire">
      <rect width="495" height="195" fill="white"/>
      <ellipse id="mask-ellipse" cx="247.5" cy="32" rx="13" ry="18" fill="black"/>
    </mask>
  </defs>
  <g clip-path="url(#outer_rectangle)">
    <rect stroke="#000000" stroke-opacity="0" fill="#151515" rx="4.5" x="0.5" y="0.5" width="494" height="194"/>
    <line x1="165" y1="28" x2="165" y2="170" vector-effect="non-scaling-stroke" stroke-width="1" stroke="#E4E2E2" stroke-linecap="square"/>
    <line x1="330" y1="28" x2="330" y2="170" vector-effect="non-scaling-stroke" stroke-width="1" stroke="#E4E2E2" stroke-linecap="square"/>

    <g transform="translate(82.5, 48)">
      <text x="0" y="32" text-anchor="middle" fill="#FEFEFE" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="700" font-size="28px" style="opacity: 0; animation: fadein 0.5s linear forwards 0.6s">{escape(total)}</text>
    </g>
    <g transform="translate(82.5, 84)">
      <text x="0" y="32" text-anchor="middle" fill="#FEFEFE" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="400" font-size="14px" style="opacity: 0; animation: fadein 0.5s linear forwards 0.7s">Total Contributions</text>
    </g>
    <g transform="translate(82.5, 114)">
      <text x="0" y="32" text-anchor="middle" fill="#9E9E9E" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="400" font-size="12px" style="opacity: 0; animation: fadein 0.5s linear forwards 0.8s">{escape(total_range)}</text>
    </g>

    <g transform="translate(247.5, 108)">
      <text x="0" y="32" text-anchor="middle" fill="#FB8C00" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="700" font-size="14px" style="opacity: 0; animation: fadein 0.5s linear forwards 0.9s">Current Streak</text>
    </g>
    <g transform="translate(247.5, 145)">
      <text x="0" y="21" text-anchor="middle" fill="#9E9E9E" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="400" font-size="12px" style="opacity: 0; animation: fadein 0.5s linear forwards 0.9s">{escape(current_range)}</text>
    </g>
    <g mask="url(#mask_out_ring_behind_fire)">
      <circle cx="247.5" cy="71" r="40" fill="none" stroke="#FB8C00" stroke-width="5" style="opacity: 0; animation: fadein 0.5s linear forwards 0.4s"/>
    </g>
    <g transform="translate(247.5, 19.5)" stroke-opacity="0" style="opacity: 0; animation: fadein 0.5s linear forwards 0.6s">
      <path d="M -12 -0.5 L 15 -0.5 L 15 23.5 L -12 23.5 L -12 -0.5 Z" fill="none"/>
      <path d="{FIRE_PATH}" fill="#FB8C00" stroke-opacity="0"/>
    </g>
    <g transform="translate(247.5, 48)">
      <text x="0" y="32" text-anchor="middle" fill="#FEFEFE" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="700" font-size="28px" style="animation: currstreak 0.6s linear forwards">{escape(current)}</text>
    </g>

    <g transform="translate(412.5, 48)">
      <text x="0" y="32" text-anchor="middle" fill="#FEFEFE" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="700" font-size="28px" style="opacity: 0; animation: fadein 0.5s linear forwards 1.2s">{escape(longest)}</text>
    </g>
    <g transform="translate(412.5, 84)">
      <text x="0" y="32" text-anchor="middle" fill="#FEFEFE" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="400" font-size="14px" style="opacity: 0; animation: fadein 0.5s linear forwards 1.3s">Longest Streak</text>
    </g>
    <g transform="translate(412.5, 114)">
      <text x="0" y="32" text-anchor="middle" fill="#9E9E9E" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="400" font-size="12px" style="opacity: 0; animation: fadein 0.5s linear forwards 1.4s">{escape(longest_range)}</text>
    </g>
  </g>
</svg>
"""


def write_svg(svg):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")


def main():
    try:
        days = fetch_contribution_days()
        stats = calculate_stats(days)
    except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
        if OUTPUT.exists():
            print(f"Keeping existing {OUTPUT}: {exc}", file=sys.stderr)
            return 0
        print(f"Could not fetch GitHub contributions: {exc}", file=sys.stderr)
        stats = calculate_stats([])

    svg = render_svg(stats, dt.date.today())
    write_svg(svg)
    print(
        f"Generated {OUTPUT}: total={stats['total']}, "
        f"current={stats['current']}, longest={stats['longest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
