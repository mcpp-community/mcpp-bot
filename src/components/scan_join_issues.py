import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import from libs
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.github_client import (
    comment,
    close_issue,
    has_label,
    get_target_from_labels,
    is_org_member,
    add_user_to_team,
    is_user_in_team,
    list_open_join_issues,
)
from libs.utils import load_simple_yaml

def scan():
    # Load configuration first
    cfg = load_simple_yaml("config/join-config.yml")

    # Get token from environment variable
    token = os.environ.get("GH_TOKEN", "").strip()

    # Get org and repo from config file
    org = cfg.get("org", "").strip()
    repo = cfg.get("repo", "").strip()

    if not token:
        raise ValueError("Environment variable GH_TOKEN is not set or empty")
    if not org:
        raise ValueError("Organization (org) is not set in config file config/join-config.yml")
    if not repo:
        raise ValueError("Repository (repo) is not set in config file config/join-config.yml")

    teams_cfg = cfg.get("teams") or {}

    issues = list_open_join_issues(token, repo)

    for it in issues:
        issue_number = it["number"]
        author = it["user"]["login"]

        target = get_target_from_labels(it)
        if not target or target not in teams_cfg:
            continue

        team_cfg = teams_cfg[target]
        team_slug = team_cfg.get("team_slug", "") or ""

        # If not org member yet, remind and keep open
        if not is_org_member(token, org, author):
            if has_label(it, "invited"):
                comment(token, repo, issue_number,
                        f"@{author} 温馨提示：你还未加入 **@{org}**。请在这里接受邀请：\n\nhttps://github.com/orgs/{org}/invitation")
            continue

        # If needs team, ensure team membership
        if team_slug:
            if not is_user_in_team(token, org, team_slug, author):
                code, payload = add_user_to_team(token, org, team_slug, author)
                if code not in (200, 201):
                    # Can't add team for some reason; leave a note and continue
                    comment(token, repo, issue_number,
                            f"@{author} 已检测到你已加入 **@{org}**，但加入 **@{org}/{team_slug}** 仍失败，将稍后重试。\n\n"
                            f"HTTP {code}\n\n```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```")
                    continue

        # Now complete: comment + close
        if team_slug:
            comment(token, repo, issue_number, f"@{author} ✅ 已确认你已加入 **@{org}** 并加入 **@{org}/{team_slug}**，本 Issue 将关闭。")
        else:
            comment(token, repo, issue_number, f"@{author} ✅ 已确认你已加入 **@{org}**，本 Issue 将关闭。")

        close_issue(token, repo, issue_number)

if __name__ == "__main__":
    scan()
