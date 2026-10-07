"""Refresh the auto-updated sections of the profile README.

Fills two blocks delimited by HTML comment markers:
  RECENT_PROJECTS  - your latest non-fork public repos
  CONTRIBUTIONS    - merged PRs you opened on other people's repos
"""
import os
import re
import requests

USER = os.environ.get("GH_USER", "HABIBEEYY")
TOKEN = os.environ.get("GITHUB_TOKEN")
README = "README.md"
MAX_REPOS = 6
MAX_PRS = 5

HEADERS = {"Accept": "application/vnd.github+json"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def get(url, **params):
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def recent_projects():
    repos = get(
        f"https://api.github.com/users/{USER}/repos",
        sort="pushed", direction="desc", per_page=50, type="owner",
    )
    repos = [
        r for r in repos
        if not r["fork"] and not r["archived"] and r["name"].lower() != USER.lower()
    ][:MAX_REPOS]
    if not repos:
        return "_No public projects yet — stay tuned!_"
    rows = ["| Project | Description | Language | ⭐ | Updated |", "|---|---|---|---|---|"]
    for r in repos:
        desc = (r["description"] or "—").replace("|", "\\|")
        lang = r["language"] or "—"
        updated = r["pushed_at"][:10]
        rows.append(f"| [{r['name']}]({r['html_url']}) | {desc} | {lang} | {r['stargazers_count']} | {updated} |")
    return "\n".join(rows)


def contributions():
    data = get(
        "https://api.github.com/search/issues",
        q=f"author:{USER} type:pr is:merged -user:{USER}",
        sort="updated", order="desc", per_page=MAX_PRS,
    )
    items = data.get("items", [])
    if not items:
        return "_No merged contributions to other repositories yet._"
    lines = []
    for it in items:
        repo = it["repository_url"].split("repos/")[-1]
        lines.append(f"- [{it['title']}]({it['html_url']}) in **{repo}**")
    return "\n".join(lines)


def replace_block(text, name, content):
    pattern = re.compile(rf"(<!--{name}:START-->)(.*?)(<!--{name}:END-->)", re.S)
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(3)}", text)


def main():
    with open(README, encoding="utf-8") as f:
        text = f.read()
    text = replace_block(text, "RECENT_PROJECTS", recent_projects())
    text = replace_block(text, "CONTRIBUTIONS", contributions())
    with open(README, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
