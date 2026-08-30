#!/usr/bin/env python3
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from html import escape
from pathlib import Path


LOGIN = os.environ.get("GITHUB_LOGIN", "3EC-DEVELOPER")
OUTPUT = Path(os.environ.get("STATS_OUTPUT", "assets/github-stats.svg"))
PROFILE_TOKEN = os.environ.get("PROFILE_STATS_TOKEN")
TOKEN = PROFILE_TOKEN or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
REST_URL = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"
PROFILE_START = dt.date(2024, 4, 13)

GITHUB_PATH = (
    "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 "
    "11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61"
    "-.546-1.387-1.333-1.756-1.333-1.756-1.09-.745.084-.729.084-.729 1.205.084 1.838 "
    "1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.418-1.305.762-1.605"
    "-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 "
    "0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 "
    ".405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 "
    "1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 "
    "0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 "
    "17.592 24 12.297c0-6.627-5.373-12-12-12"
)

ROW_ICONS = {
    "star": "M12 2.25l2.96 6 6.62.96-4.79 4.67 1.13 6.59L12 17.36l-5.92 3.11 1.13-6.59-4.79-4.67 6.62-.96L12 2.25z",
    "commit": "M12 5a7 7 0 1 1-6.32 4H2V7h7v7H7V9.74A5 5 0 1 0 12 7z",
    "pull": "M7 4a2 2 0 1 1-3 1.73V18.3a2 2 0 1 1-2 0V5.73A2 2 0 0 1 7 4zm14 14a2 2 0 1 1-3.45-1.38L14 13.08V7.7a2 2 0 1 1 2 0v4.55l2.96 2.96A2 2 0 0 1 21 18z",
    "issue": "M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20zm0 5a1.25 1.25 0 0 0-1.25 1.25v4.5a1.25 1.25 0 0 0 2.5 0v-4.5A1.25 1.25 0 0 0 12 7zm0 10.4a1.4 1.4 0 1 0 0-2.8 1.4 1.4 0 0 0 0 2.8z",
    "repo": "M5 3h12a2 2 0 0 1 2 2v16l-4-2-4 2-4-2-4 2V5a2 2 0 0 1 2-2zm0 3v11.76l2-1 4 2 4-2 2 1V6H5z",
}


def iso(value):
    return value.isoformat() + "T00:00:00Z"


def api_get(url):
    if not TOKEN:
        raise RuntimeError("PROFILE_STATS_TOKEN, GH_TOKEN, or GITHUB_TOKEN is required")

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


def github_graphql(query, variables):
    if not TOKEN:
        raise RuntimeError("PROFILE_STATS_TOKEN, GH_TOKEN, or GITHUB_TOKEN is required")

    request = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
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


def fetch_owned_repos():
    repos = []
    page = 1
    while True:
        if PROFILE_TOKEN:
            params = "per_page=100&page={page}&visibility=all&affiliation=owner&sort=updated"
            url = f"{REST_URL}/user/repos?" + params.format(page=page)
        else:
            params = "per_page=100&page={page}&type=owner&sort=updated"
            url = f"{REST_URL}/users/{urllib.parse.quote(LOGIN)}/repos?" + params.format(page=page)
        batch = api_get(url)
        if not batch:
            break
        repos.extend(
            repo
            for repo in batch
            if not repo.get("fork") and repo.get("owner", {}).get("login", "").lower() == LOGIN.lower()
        )
        page += 1
    return repos


def search_count(query):
    encoded = urllib.parse.urlencode({"q": query, "per_page": 1})
    data = api_get(f"{REST_URL}/search/issues?{encoded}")
    return int(data.get("total_count", 0))


def search_commit_count(since):
    query = f"author:{LOGIN} author-date:>={since.isoformat()}"
    encoded = urllib.parse.urlencode({"q": query, "per_page": 1})
    data = api_get(f"{REST_URL}/search/commits?{encoded}")
    return int(data.get("total_count", 0))


def contributed_repo_count_last_year(start, end):
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          commitContributionsByRepository(maxRepositories: 100) {
            repository { nameWithOwner owner { login } }
          }
          pullRequestContributionsByRepository(maxRepositories: 100) {
            repository { nameWithOwner owner { login } }
          }
          issueContributionsByRepository(maxRepositories: 100) {
            repository { nameWithOwner owner { login } }
          }
        }
      }
    }
    """
    data = github_graphql(query, {"login": LOGIN, "from": iso(start), "to": iso(end)})
    collection = data["user"]["contributionsCollection"]
    repo_names = set()
    for key in (
        "commitContributionsByRepository",
        "pullRequestContributionsByRepository",
        "issueContributionsByRepository",
    ):
        for item in collection[key]:
            repository = item["repository"]
            if repository["owner"]["login"].lower() != LOGIN.lower():
                repo_names.add(repository["nameWithOwner"])
    return len(repo_names)


def fetch_stats():
    today = dt.date.today()
    last_year_start = today - dt.timedelta(days=365)
    repos = fetch_owned_repos()
    return {
        "stars": sum(int(repo.get("stargazers_count", 0)) for repo in repos),
        "commits_last_year": search_commit_count(last_year_start),
        "prs": search_count(f"author:{LOGIN} type:pr"),
        "issues": search_count(f"author:{LOGIN} type:issue"),
        "contributed_last_year": contributed_repo_count_last_year(last_year_start, today),
    }


def icon(path, x, y):
    return (
        f'<g transform="translate({x},{y}) scale(0.92)" fill="none" stroke="#63ff8f" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="{path}"/></g>'
    )


def row(icon_name, label, value, y):
    return f"""
    {icon(ROW_ICONS[icon_name], 32, y - 18)}
    <text x="74" y="{y}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="24" font-weight="700" fill="#9E9E9E">{escape(label)}</text>
    <text x="595" y="{y}" text-anchor="end" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="24" font-weight="700" fill="#9E9E9E">{escape(str(value))}</text>"""


def render_svg(stats):
    return f"""<svg width="830" height="325" viewBox="0 0 830 325" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Douglas Forbes-Scott's GitHub stats">
  <rect width="830" height="325" rx="6" fill="#151515"/>
  <text x="32" y="58" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="34" font-weight="700" fill="#f0f6fc">Douglas Forbes-Scott's GitHub Stats</text>
  <g>
    {row("star", "Total Stars Earned:", stats["stars"], 106)}
    {row("commit", "Total Commits (last year):", stats["commits_last_year"], 148)}
    {row("pull", "Total PRs:", stats["prs"], 190)}
    {row("issue", "Total Issues:", stats["issues"], 232)}
    {row("repo", "Contributed to (last year):", stats["contributed_last_year"], 274)}
  </g>
  <g transform="translate(607, 75)">
    <circle cx="100" cy="100" r="92" fill="none" stroke="#3e3e3e" stroke-width="12"/>
    <path d="M100 8a92 92 0 0 1 63 25" fill="none" stroke="#d9d9d9" stroke-width="12" stroke-linecap="round"/>
    <circle cx="100" cy="100" r="66" fill="#bdbdbd"/>
    <g transform="translate(34, 32) scale(5.52)" fill="#151515">
      <path d="{GITHUB_PATH}"/>
    </g>
  </g>
</svg>
"""


def write_svg(svg):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")


def main():
    try:
        if not PROFILE_TOKEN:
            print("PROFILE_STATS_TOKEN not set; using public-access stats only", file=sys.stderr)
        stats = fetch_stats()
    except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
        if OUTPUT.exists():
            print(f"Keeping existing {OUTPUT}: {exc}", file=sys.stderr)
            return 0
        print(f"Could not fetch GitHub stats: {exc}", file=sys.stderr)
        stats = {
            "stars": 0,
            "commits_last_year": 0,
            "prs": 0,
            "issues": 0,
            "contributed_last_year": 0,
        }

    write_svg(render_svg(stats))
    print(
        "Generated stats card: "
        f"stars={stats['stars']}, commits_last_year={stats['commits_last_year']}, "
        f"prs={stats['prs']}, issues={stats['issues']}, "
        f"contributed_last_year={stats['contributed_last_year']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
