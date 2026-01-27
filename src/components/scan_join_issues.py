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
    update_issue_title,
)
from libs.utils import load_simple_yaml

def scan(verbose=False):
    # Load configuration first
    config_path = Path(__file__).parent.parent / "config" / "join-config.yml"
    cfg = load_simple_yaml(str(config_path))

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

    if verbose:
        print(f"扫描仓库: {repo}")
        print(f"组织: {org}")
        print(f"配置的团队: {list(teams_cfg.keys())}")
        print()

    issues = list_open_join_issues(token, repo)

    if verbose:
        print(f"找到 {len(issues)} 个待处理的加入请求\n")

    for it in issues:
        issue_number = it["number"]
        author = it["user"]["login"]
        issue_title = it["title"]

        if verbose:
            print(f"处理 Issue #{issue_number} - 作者: @{author}")

        # Replace @<your-username> with actual username in title
        if "@<your-username>" in issue_title:
            new_title = issue_title.replace("@<your-username>", f"@{author}")
            code, _ = update_issue_title(token, repo, issue_number, new_title)
            if code in (200, 201):
                if verbose:
                    print(f"  ✓ 更新标题: {issue_title} → {new_title}")
            else:
                if verbose:
                    print(f"  ✗ 更新标题失败 (HTTP {code})")

        target = get_target_from_labels(it)
        if not target or target not in teams_cfg:
            if verbose:
                print(f"  ⊘ 跳过: 未找到有效的目标团队标签 (target={target})\n")
            continue

        team_cfg = teams_cfg[target]
        team_slug = team_cfg.get("team_slug", "") or ""

        if verbose:
            print(f"  目标团队: {target} (team_slug={team_slug})")

        # If not org member yet, remind and keep open
        if not is_org_member(token, org, author):
            if verbose:
                print(f"  ⊘ 跳过: @{author} 还不是 @{org} 成员")
            if has_label(it, "invited"):
                if verbose:
                    print(f"  → 发送提醒评论")
                comment(token, repo, issue_number,
                        f"@{author} 温馨提示：你还未加入 **@{org}**。请在这里接受邀请：\n\nhttps://github.com/orgs/{org}/invitation")
            if verbose:
                print()
            continue

        if verbose:
            print(f"  ✓ @{author} 已是组织成员")

        # If needs team, ensure team membership
        if team_slug:
            if not is_user_in_team(token, org, team_slug, author):
                if verbose:
                    print(f"  → 添加到团队 @{org}/{team_slug}")
                code, payload = add_user_to_team(token, org, team_slug, author)
                if code not in (200, 201):
                    # Can't add team for some reason; leave a note and continue
                    if verbose:
                        print(f"  ✗ 添加团队失败 (HTTP {code})")
                    comment(token, repo, issue_number,
                            f"@{author} 已检测到你已加入 **@{org}**，但加入 **@{org}/{team_slug}** 仍失败，将稍后重试。\n\n"
                            f"HTTP {code}\n\n```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```")
                    if verbose:
                        print()
                    continue
                if verbose:
                    print(f"  ✓ 成功添加到团队")
            else:
                if verbose:
                    print(f"  ✓ 已在团队 @{org}/{team_slug} 中")

        # Now complete: comment + close
        if verbose:
            print(f"  ✓ 处理完成，关闭 Issue")
        if team_slug:
            comment(token, repo, issue_number, f"@{author} ✅ 已确认你已加入 **@{org}** 并加入 **@{org}/{team_slug}**，本 Issue 将关闭。")
        else:
            comment(token, repo, issue_number, f"@{author} ✅ 已确认你已加入 **@{org}**，本 Issue 将关闭。")

        close_issue(token, repo, issue_number)

        if verbose:
            print()

if __name__ == "__main__":
    scan()
