#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request
from html import escape
from pathlib import Path


LOGIN = os.environ.get("GITHUB_LOGIN", "3EC-DEVELOPER")
OUTPUT = Path(os.environ.get("LANGS_OUTPUT", "assets/top-languages.svg"))
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
REST_URL = "https://api.github.com"
LANGUAGE_LIMIT = 6

LANGUAGE_META = {
    "Dart": {
        "color": "#00B4AB",
        "icon_color": "#0175C2",
        "path": "M4.105 4.105S9.158 1.58 11.684.316a3.079 3.079 0 0 1 1.481-.315c.766.047 1.677.788 1.677.788L24 9.948v9.789h-4.263V24H9.789l-9-9C.303 14.5 0 13.795 0 13.105c0-.319.18-.818.316-1.105l3.789-7.895zm.679.679v11.787c.002.543.021 1.024.498 1.508L10.204 23h8.533v-4.263L4.784 4.784zm12.055-.678c-.899-.896-1.809-1.78-2.74-2.643-.302-.267-.567-.468-1.07-.462-.37.014-.87.195-.87.195L6.341 4.105l10.498.001z",
    },
    "Java": {
        "color": "#C17D11",
        "icon_color": "#ED8B00",
        "path": "M11.915 0 11.7.215C9.515 2.4 7.47 6.39 6.046 10.483c-1.064 1.024-3.633 2.81-3.711 3.551-.093.87 1.746 2.611 1.55 3.235-.198.625-1.304 1.408-1.014 1.939.1.188.823.011 1.277-.491a13.389 13.389 0 0 0-.017 2.14c.076.906.27 1.668.643 2.232.372.563.956.911 1.667.911.397 0 .727-.114 1.024-.264.298-.149.571-.33.91-.5.68-.34 1.634-.666 3.53-.604 1.903.062 2.872.39 3.559.704.687.314 1.15.664 1.925.664.767 0 1.395-.336 1.807-.9.412-.563.631-1.33.72-2.24.06-.623.055-1.32 0-2.066.454.45 1.117.604 1.213.424.29-.53-.816-1.314-1.013-1.937-.198-.624 1.642-2.366 1.549-3.236-.08-.748-2.707-2.568-3.748-3.586C16.428 6.374 14.308 2.394 12.13.215zm.175 6.038a2.95 2.95 0 0 1 2.943 2.942 2.95 2.95 0 0 1-2.943 2.943A2.95 2.95 0 0 1 9.148 8.98a2.95 2.95 0 0 1 2.942-2.942zM8.685 7.983a3.515 3.515 0 0 0-.145.997c0 1.951 1.6 3.55 3.55 3.55 1.95 0 3.55-1.598 3.55-3.55 0-.329-.046-.648-.132-.951.334.095.64.208.915.336a42.699 42.699 0 0 1 2.042 5.829c.678 2.545 1.01 4.92.846 6.607-.082.844-.29 1.51-.606 1.94-.315.431-.713.651-1.315.651-.593 0-.932-.27-1.673-.61-.741-.338-1.825-.694-3.792-.758-1.974-.064-3.073.293-3.821.669-.375.188-.659.373-.911.5s-.466.2-.752.2c-.53 0-.876-.209-1.16-.64-.285-.43-.474-1.101-.545-1.948-.141-1.693.176-4.069.823-6.614a43.155 43.155 0 0 1 1.934-5.783c.348-.167.749-.31 1.192-.425zm-3.382 4.362a.216.216 0 0 1 .13.031c-.166.56-.323 1.116-.463 1.665a33.849 33.849 0 0 0-.547 2.555 3.9 3.9 0 0 0-.2-.39c-.58-1.012-.914-1.642-1.16-2.08.315-.24 1.679-1.755 2.24-1.781zm13.394.01c.562.027 1.926 1.543 2.24 1.783-.246.438-.58 1.068-1.16 2.08a4.428 4.428 0 0 0-.163.309 32.354 32.354 0 0 0-.562-2.49 40.579 40.579 0 0 0-.482-1.652.216.216 0 0 1 .127-.03z",
    },
    "JavaScript": {
        "color": "#F1E05A",
        "icon_color": "#F7DF1E",
        "path": "M0 0h24v24H0V0zm22.034 18.276c-.175-1.095-.888-2.015-3.003-2.873-.736-.345-1.554-.585-1.797-1.14-.091-.33-.105-.51-.046-.705.15-.646.915-.84 1.515-.66.39.12.75.42.976.9 1.034-.676 1.034-.676 1.755-1.125-.27-.42-.404-.601-.586-.78-.63-.705-1.469-1.065-2.834-1.034l-.705.089c-.676.165-1.32.525-1.71 1.005-1.14 1.291-.811 3.541.569 4.471 1.365 1.02 3.361 1.244 3.616 2.205.24 1.17-.87 1.545-1.966 1.41-.811-.18-1.26-.586-1.755-1.336l-1.83 1.051c.21.48.45.689.81 1.109 1.74 1.756 6.09 1.666 6.871-1.004.029-.09.24-.705.074-1.65l.046.067zm-8.983-7.245h-2.248c0 1.938-.009 3.864-.009 5.805 0 1.232.063 2.363-.138 2.711-.33.689-1.18.601-1.566.48-.396-.196-.597-.466-.83-.855-.063-.105-.11-.196-.127-.196l-1.825 1.125c.305.63.75 1.172 1.324 1.517.855.51 2.004.675 3.207.405.783-.226 1.458-.691 1.811-1.411.51-.93.402-2.07.397-3.346.012-2.054 0-4.109 0-6.179l.004-.056z",
    },
    "HTML": {
        "color": "#E34C26",
        "icon_color": "#E34F26",
        "path": "M1.5 0h21l-1.91 21.563L11.977 24l-8.564-2.438L1.5 0zm7.031 9.75l-.232-2.718 10.059.003.23-2.622L5.412 4.41l.698 8.01h9.126l-.326 3.426-2.91.804-2.955-.81-.188-2.11H6.248l.33 4.171L12 19.351l5.379-1.443.744-8.157H8.531z",
    },
    "C++": {
        "color": "#F34B7D",
        "icon_color": "#00599C",
        "path": "M22.394 6c-.167-.29-.398-.543-.652-.69L12.926.22c-.509-.294-1.34-.294-1.848 0L2.26 5.31c-.508.293-.923 1.013-.923 1.6v10.18c0 .294.104.62.271.91.167.29.398.543.652.69l8.816 5.09c.508.293 1.34.293 1.848 0l8.816-5.09c.254-.147.485-.4.652-.69.167-.29.27-.616.27-.91V6.91c.003-.294-.1-.62-.268-.91zM12 19.11c-3.92 0-7.109-3.19-7.109-7.11 0-3.92 3.19-7.11 7.11-7.11a7.133 7.133 0 016.156 3.553l-3.076 1.78a3.567 3.567 0 00-3.08-1.78A3.56 3.56 0 008.444 12 3.56 3.56 0 0012 15.555a3.57 3.57 0 003.08-1.778l3.078 1.78A7.135 7.135 0 0112 19.11zm7.11-6.715h-.79v.79h-.79v-.79h-.79v-.79h.79v-.79h.79v.79h.79zm2.962 0h-.79v.79h-.79v-.79h-.79v-.79h.79v-.79h.79v.79h.79z",
    },
    "CMake": {
        "color": "#DA3434",
        "icon_color": "#064F8C",
        "path": "M11.769.066L.067 23.206l12.76-10.843zM23.207 23.934L7.471 17.587 0 23.934zM24 23.736L12.298.463l1.719 19.24zM12.893 12.959l-5.025 4.298 5.62 2.248z",
    },
}

FALLBACK_COLOR = "#8B949E"


def api_get(url):
    if not TOKEN:
        raise RuntimeError("GH_TOKEN or GITHUB_TOKEN is required to fetch languages")

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_repos():
    repos = []
    page = 1
    while True:
        batch = api_get(
            f"{REST_URL}/users/{LOGIN}/repos?per_page=100&page={page}&type=owner&sort=updated"
        )
        if not batch:
            break
        repos.extend(repo for repo in batch if not repo.get("fork"))
        page += 1
    return repos


def fetch_language_totals():
    totals = {}
    for repo in fetch_repos():
        languages_url = repo.get("languages_url")
        if not languages_url:
            continue
        for language, bytes_count in api_get(languages_url).items():
            totals[language] = totals.get(language, 0) + int(bytes_count)
    return totals


def top_languages(totals):
    total_bytes = sum(totals.values())
    if total_bytes <= 0:
        return []
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:LANGUAGE_LIMIT]
    return [
        {
            "name": name,
            "bytes": bytes_count,
            "percent": bytes_count * 100 / total_bytes,
            "color": LANGUAGE_META.get(name, {}).get("color", FALLBACK_COLOR),
            "icon_color": LANGUAGE_META.get(name, {}).get("icon_color", FALLBACK_COLOR),
            "path": LANGUAGE_META.get(name, {}).get("path"),
        }
        for name, bytes_count in ranked
    ]


def icon_svg(language, x, y):
    path = language.get("path")
    if not path:
        letter = escape(language["name"][:1])
        return (
            f'<circle cx="{x + 9}" cy="{y + 9}" r="9" fill="{language["color"]}" opacity="0.22"/>'
            f'<text x="{x + 9}" y="{y + 14}" text-anchor="middle" '
            'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" '
            f'font-size="13" font-weight="700" fill="{language["color"]}">{letter}</text>'
        )
    return (
        f'<g transform="translate({x},{y}) scale(0.75)" fill="{language["icon_color"]}">'
        f'<path d="{path}"/></g>'
    )


def render_svg(languages):
    if not languages:
        languages = [
            {"name": "Dart", "percent": 65.32, **LANGUAGE_META["Dart"]},
            {"name": "Java", "percent": 23.73, **LANGUAGE_META["Java"]},
            {"name": "JavaScript", "percent": 6.19, **LANGUAGE_META["JavaScript"]},
            {"name": "HTML", "percent": 1.98, **LANGUAGE_META["HTML"]},
            {"name": "C++", "percent": 1.55, **LANGUAGE_META["C++"]},
            {"name": "CMake", "percent": 1.23, **LANGUAGE_META["CMake"]},
        ]

    bar_x = 32
    bar_y = 86
    bar_width = 766
    bar_height = 12
    current_x = bar_x
    bar_segments = []
    for index, language in enumerate(languages):
        width = round(bar_width * language["percent"] / 100, 2)
        if index == len(languages) - 1:
            width = round(bar_x + bar_width - current_x, 2)
        rx = 6 if index in (0, len(languages) - 1) else 0
        bar_segments.append(
            f'<rect x="{current_x:.2f}" y="{bar_y}" width="{width:.2f}" height="{bar_height}" '
            f'rx="{rx}" fill="{language["color"]}"/>'
        )
        current_x += width

    legend = []
    positions = [(32, 128), (32, 160), (32, 192), (432, 128), (432, 160), (432, 192)]
    for language, (x, y) in zip(languages, positions):
        label = f'{language["name"]} {language["percent"]:.2f}%'
        legend.append(
            f'<circle cx="{x + 8}" cy="{y - 5}" r="6" fill="{language["color"]}"/>'
            f'{icon_svg(language, x + 24, y - 15)}'
            f'<text x="{x + 52}" y="{y}" '
            'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" '
            f'font-size="17" font-weight="500" fill="#c9d1d9">{escape(label)}</text>'
        )

    return f"""<svg width="830" height="230" viewBox="0 0 830 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Most used languages">
  <rect width="830" height="230" rx="6" fill="#151515"/>
  <text x="32" y="48" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="27" font-weight="700" fill="#f0f6fc">Most Used Languages</text>
  <g>
    {''.join(bar_segments)}
  </g>
  <g>
    {''.join(legend)}
  </g>
</svg>
"""


def write_svg(svg):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")


def main():
    try:
        languages = top_languages(fetch_language_totals())
        if not languages:
            raise RuntimeError("No language data returned")
    except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
        if OUTPUT.exists():
            print(f"Keeping existing {OUTPUT}: {exc}", file=sys.stderr)
            return 0
        print(f"Could not fetch language data: {exc}", file=sys.stderr)
        languages = []

    write_svg(render_svg(languages))
    print("Generated language card: " + ", ".join(f"{l['name']} {l['percent']:.2f}%" for l in languages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
