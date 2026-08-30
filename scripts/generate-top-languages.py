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
MAX_DISPLAY_LANGUAGES = 8
EXTRA_LANGUAGE_LIMIT = MAX_DISPLAY_LANGUAGES - LANGUAGE_LIMIT
NEON_FALLBACKS = [
    "#00F5FF",
    "#FF8A00",
    "#B6FF00",
    "#FF2BD6",
    "#8A2BFF",
    "#FF1744",
    "#00FF85",
    "#3B82FF",
    "#FFEA00",
    "#FF4D00",
]

LANGUAGE_META = {
    "Dart": {
        "color": "#00F5FF",
        "icon_color": "#0175C2",
        "path": "M4.105 4.105S9.158 1.58 11.684.316a3.079 3.079 0 0 1 1.481-.315c.766.047 1.677.788 1.677.788L24 9.948v9.789h-4.263V24H9.789l-9-9C.303 14.5 0 13.795 0 13.105c0-.319.18-.818.316-1.105l3.789-7.895zm.679.679v11.787c.002.543.021 1.024.498 1.508L10.204 23h8.533v-4.263L4.784 4.784zm12.055-.678c-.899-.896-1.809-1.78-2.74-2.643-.302-.267-.567-.468-1.07-.462-.37.014-.87.195-.87.195L6.341 4.105l10.498.001z",
    },
    "Java": {
        "color": "#FF8A00",
        "icon_color": "#ED8B00",
        "path": "M11.915 0 11.7.215C9.515 2.4 7.47 6.39 6.046 10.483c-1.064 1.024-3.633 2.81-3.711 3.551-.093.87 1.746 2.611 1.55 3.235-.198.625-1.304 1.408-1.014 1.939.1.188.823.011 1.277-.491a13.389 13.389 0 0 0-.017 2.14c.076.906.27 1.668.643 2.232.372.563.956.911 1.667.911.397 0 .727-.114 1.024-.264.298-.149.571-.33.91-.5.68-.34 1.634-.666 3.53-.604 1.903.062 2.872.39 3.559.704.687.314 1.15.664 1.925.664.767 0 1.395-.336 1.807-.9.412-.563.631-1.33.72-2.24.06-.623.055-1.32 0-2.066.454.45 1.117.604 1.213.424.29-.53-.816-1.314-1.013-1.937-.198-.624 1.642-2.366 1.549-3.236-.08-.748-2.707-2.568-3.748-3.586C16.428 6.374 14.308 2.394 12.13.215zm.175 6.038a2.95 2.95 0 0 1 2.943 2.942 2.95 2.95 0 0 1-2.943 2.943A2.95 2.95 0 0 1 9.148 8.98a2.95 2.95 0 0 1 2.942-2.942zM8.685 7.983a3.515 3.515 0 0 0-.145.997c0 1.951 1.6 3.55 3.55 3.55 1.95 0 3.55-1.598 3.55-3.55 0-.329-.046-.648-.132-.951.334.095.64.208.915.336a42.699 42.699 0 0 1 2.042 5.829c.678 2.545 1.01 4.92.846 6.607-.082.844-.29 1.51-.606 1.94-.315.431-.713.651-1.315.651-.593 0-.932-.27-1.673-.61-.741-.338-1.825-.694-3.792-.758-1.974-.064-3.073.293-3.821.669-.375.188-.659.373-.911.5s-.466.2-.752.2c-.53 0-.876-.209-1.16-.64-.285-.43-.474-1.101-.545-1.948-.141-1.693.176-4.069.823-6.614a43.155 43.155 0 0 1 1.934-5.783c.348-.167.749-.31 1.192-.425zm-3.382 4.362a.216.216 0 0 1 .13.031c-.166.56-.323 1.116-.463 1.665a33.849 33.849 0 0 0-.547 2.555 3.9 3.9 0 0 0-.2-.39c-.58-1.012-.914-1.642-1.16-2.08.315-.24 1.679-1.755 2.24-1.781zm13.394.01c.562.027 1.926 1.543 2.24 1.783-.246.438-.58 1.068-1.16 2.08a4.428 4.428 0 0 0-.163.309 32.354 32.354 0 0 0-.562-2.49 40.579 40.579 0 0 0-.482-1.652.216.216 0 0 1 .127-.03z",
    },
    "JavaScript": {
        "color": "#B6FF00",
        "icon_color": "#F7DF1E",
        "path": "M0 0h24v24H0V0zm22.034 18.276c-.175-1.095-.888-2.015-3.003-2.873-.736-.345-1.554-.585-1.797-1.14-.091-.33-.105-.51-.046-.705.15-.646.915-.84 1.515-.66.39.12.75.42.976.9 1.034-.676 1.034-.676 1.755-1.125-.27-.42-.404-.601-.586-.78-.63-.705-1.469-1.065-2.834-1.034l-.705.089c-.676.165-1.32.525-1.71 1.005-1.14 1.291-.811 3.541.569 4.471 1.365 1.02 3.361 1.244 3.616 2.205.24 1.17-.87 1.545-1.966 1.41-.811-.18-1.26-.586-1.755-1.336l-1.83 1.051c.21.48.45.689.81 1.109 1.74 1.756 6.09 1.666 6.871-1.004.029-.09.24-.705.074-1.65l.046.067zm-8.983-7.245h-2.248c0 1.938-.009 3.864-.009 5.805 0 1.232.063 2.363-.138 2.711-.33.689-1.18.601-1.566.48-.396-.196-.597-.466-.83-.855-.063-.105-.11-.196-.127-.196l-1.825 1.125c.305.63.75 1.172 1.324 1.517.855.51 2.004.675 3.207.405.783-.226 1.458-.691 1.811-1.411.51-.93.402-2.07.397-3.346.012-2.054 0-4.109 0-6.179l.004-.056z",
    },
    "HTML": {
        "color": "#FF2BD6",
        "icon_color": "#E34F26",
        "path": "M1.5 0h21l-1.91 21.563L11.977 24l-8.564-2.438L1.5 0zm7.031 9.75l-.232-2.718 10.059.003.23-2.622L5.412 4.41l.698 8.01h9.126l-.326 3.426-2.91.804-2.955-.81-.188-2.11H6.248l.33 4.171L12 19.351l5.379-1.443.744-8.157H8.531z",
    },
    "C++": {
        "color": "#8A2BFF",
        "icon_color": "#00599C",
        "path": "M22.394 6c-.167-.29-.398-.543-.652-.69L12.926.22c-.509-.294-1.34-.294-1.848 0L2.26 5.31c-.508.293-.923 1.013-.923 1.6v10.18c0 .294.104.62.271.91.167.29.398.543.652.69l8.816 5.09c.508.293 1.34.293 1.848 0l8.816-5.09c.254-.147.485-.4.652-.69.167-.29.27-.616.27-.91V6.91c.003-.294-.1-.62-.268-.91zM12 19.11c-3.92 0-7.109-3.19-7.109-7.11 0-3.92 3.19-7.11 7.11-7.11a7.133 7.133 0 016.156 3.553l-3.076 1.78a3.567 3.567 0 00-3.08-1.78A3.56 3.56 0 008.444 12 3.56 3.56 0 0012 15.555a3.57 3.57 0 003.08-1.778l3.078 1.78A7.135 7.135 0 0112 19.11zm7.11-6.715h-.79v.79h-.79v-.79h-.79v-.79h.79v-.79h.79v.79h.79zm2.962 0h-.79v.79h-.79v-.79h-.79v-.79h.79v-.79h.79v.79h.79z",
    },
    "CMake": {
        "color": "#FF1744",
        "icon_color": "#064F8C",
        "path": "M11.769.066L.067 23.206l12.76-10.843zM23.207 23.934L7.471 17.587 0 23.934zM24 23.736L12.298.463l1.719 19.24zM12.893 12.959l-5.025 4.298 5.62 2.248z",
    },
    "Python": {
        "color": "#00FF85",
        "icon_color": "#3776AB",
        "path": "M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z",
    },
    "TypeScript": {
        "color": "#3B82FF",
        "icon_color": "#3178C6",
        "path": "M1.125 0C.502 0 0 .502 0 1.125v21.75C0 23.498.502 24 1.125 24h21.75c.623 0 1.125-.502 1.125-1.125V1.125C24 .502 23.498 0 22.875 0zm17.363 9.75c.612 0 1.154.037 1.627.111a6.38 6.38 0 0 1 1.306.34v2.458a3.95 3.95 0 0 0-.643-.361 5.093 5.093 0 0 0-.717-.26 5.453 5.453 0 0 0-1.426-.2c-.3 0-.573.028-.819.086a2.1 2.1 0 0 0-.623.242c-.17.104-.3.229-.393.374a.888.888 0 0 0-.14.49c0 .196.053.373.156.529.104.156.252.304.443.444s.423.276.696.41c.273.135.582.274.926.416.47.197.892.407 1.266.628.374.222.695.473.963.753.268.279.472.598.614.957.142.359.214.776.214 1.253 0 .657-.125 1.21-.373 1.656a3.033 3.033 0 0 1-1.012 1.085 4.38 4.38 0 0 1-1.487.596c-.566.12-1.163.18-1.79.18a9.916 9.916 0 0 1-1.84-.164 5.544 5.544 0 0 1-1.512-.493v-2.63a5.033 5.033 0 0 0 3.237 1.2c.333 0 .624-.03.872-.09.249-.06.456-.144.623-.25.166-.108.29-.234.373-.38a1.023 1.023 0 0 0-.074-1.089 2.12 2.12 0 0 0-.537-.5 5.597 5.597 0 0 0-.807-.444 27.72 27.72 0 0 0-1.007-.436c-.918-.383-1.602-.852-2.053-1.405-.45-.553-.676-1.222-.676-2.005 0-.614.123-1.141.369-1.582.246-.441.58-.804 1.004-1.089a4.494 4.494 0 0 1 1.47-.629 7.536 7.536 0 0 1 1.77-.201zm-15.113.188h9.563v2.166H9.506v9.646H6.789v-9.646H3.375z",
    },
}

PINNED_LANGUAGES = [
    ("Dart", 65.32),
    ("Java", 23.73),
    ("JavaScript", 6.19),
    ("HTML", 1.98),
    ("C++", 1.55),
    ("CMake", 1.23),
]


def language_color(name):
    meta = LANGUAGE_META.get(name)
    if meta:
        return meta["color"]
    return NEON_FALLBACKS[sum(ord(char) for char in name) % len(NEON_FALLBACKS)]


def language_card(name, percent, bytes_count=0):
    meta = LANGUAGE_META.get(name, {})
    color = language_color(name)
    return {
        "name": name,
        "bytes": bytes_count,
        "percent": percent,
        "color": color,
        "icon_color": meta.get("icon_color", color),
        "path": meta.get("path"),
    }


def pinned_languages():
    return [
        {
            "name": name,
            "percent": percent,
            "bytes": 0,
            "color": language_color(name),
            "icon_color": LANGUAGE_META.get(name, {}).get("icon_color", language_color(name)),
            "path": LANGUAGE_META.get(name, {}).get("path"),
        }
        for name, percent in PINNED_LANGUAGES
    ]


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
    pinned_names = [name for name, _ in PINNED_LANGUAGES]
    ranked_names = [
        name
        for name, _ in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]
    extra_names = [
        name
        for name in ranked_names
        if name not in pinned_names
    ][:EXTRA_LANGUAGE_LIMIT]
    selected_names = pinned_names + extra_names
    selected_names.sort(key=lambda name: totals.get(name, 0), reverse=True)

    cards = []
    for name in selected_names:
        bytes_count = int(totals.get(name, 0))
        if bytes_count:
            percent = bytes_count * 100 / total_bytes
        else:
            percent = dict(PINNED_LANGUAGES).get(name, 0)
        cards.append(language_card(name, percent, bytes_count))
    return cards


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
        f'<g transform="translate({x},{y}) scale(1)" fill="{language["icon_color"]}">'
        f'<path d="{path}"/></g>'
    )


def render_svg(languages):
    if not languages:
        languages = pinned_languages()

    bar_x = 32
    bar_y = 98
    bar_width = 766
    bar_height = 22
    percent_total = sum(language["percent"] for language in languages) or 1
    current_x = bar_x
    bar_segments = []
    for index, language in enumerate(languages):
        width = round(bar_width * language["percent"] / percent_total, 2)
        if index == len(languages) - 1:
            width = round(bar_x + bar_width - current_x, 2)
        bar_segments.append(
            f'<rect x="{current_x:.2f}" y="{bar_y}" width="{width:.2f}" height="{bar_height}" '
            f'rx="0" fill="{language["color"]}"/>'
        )
        current_x += width

    legend = []
    row_gap = 40
    rows = max(3, (len(languages) + 1) // 2)
    height = 150 + ((rows - 1) * row_gap) + 40
    positions = []
    for index in range(len(languages)):
        col = index // rows
        row = index % rows
        positions.append((32 + col * 400, 150 + row * row_gap))

    for language, (x, y) in zip(languages, positions):
        label = f'{language["name"]} {language["percent"]:.2f}%'
        legend.append(
            f'<circle cx="{x + 9}" cy="{y - 7}" r="8" fill="{language["color"]}"/>'
            f'{icon_svg(language, x + 30, y - 25)}'
            f'<text x="{x + 66}" y="{y}" '
            'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" '
            f'font-size="24" font-weight="600" fill="#c9d1d9">{escape(label)}</text>'
        )

    return f"""<svg width="830" height="{height}" viewBox="0 0 830 {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Most used languages">
  <rect width="830" height="{height}" rx="6" fill="#151515"/>
  <text x="32" y="58" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="34" font-weight="700" fill="#f0f6fc">Most Used Languages</text>
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
        languages = pinned_languages()

    write_svg(render_svg(languages))
    print("Generated language card: " + ", ".join(f"{l['name']} {l['percent']:.2f}%" for l in languages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
