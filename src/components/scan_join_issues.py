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
    list_issue_comments,
    list_open_join_issues,
    update_issue_title,
)
from libs.utils import load_simple_yaml

def _normalize_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value).strip()]

def _is_approval_comment(body, keywords):
    if not body:
        return False
    text = body.lower()
    for kw in keywords:
        if kw and kw.lower() in text:
            return True
    return False

def _is_issue_approved(token, repo, org, issue, team_cfg, team_slug, verbose=False):
    reviewers = team_cfg.get("reviewers") or {}
    required_users = _normalize_list(reviewers.get("users"))
    required_teams = _normalize_list(reviewers.get("teams"))

    approval_label = team_cfg.get("approval_label") or team_cfg.get("approved_label")
    if approval_label and has_label(issue, approval_label):
        return True

    approval_keywords = _normalize_list(team_cfg.get("approval_keywords"))
    if not approval_keywords:
        approval_keywords = ["/approve", "approve", "approved", "lgtm", "同意", "批准", "通过", "已批准"]

    if not required_users and not required_teams:
        if verbose:
            print("  ⊘ 跳过: 未配置审核人/团队")
        return False

    try:
        comments = list_issue_comments(token, repo, issue["number"])
    except RuntimeError as e:
        if verbose:
            print(f"  ✗ 获取评论失败: {e}")
        return False

    approvals = set()
    for c in comments:
        body = c.get("body", "")
        if not _is_approval_comment(body, approval_keywords):
            continue
        author = c.get("user", {}).get("login", "")
        if author:
            approvals.add(author)

    # Check required teams approvals (need at least one member approval per team)
    team_member_cache = {}
    for team in required_teams:
        approved_by_team = False
        for approver in approvals:
            cache_key = (team, approver)
            if cache_key not in team_member_cache:
                team_member_cache[cache_key] = is_user_in_team(token, org, team, approver)
            if team_member_cache[cache_key]:
                approved_by_team = True
                break
        if not approved_by_team:
            if verbose:
                print(f"  ⊘ 跳过: 缺少团队 @{org}/{team} 成员的批准")
            return False

    # Check required users approvals
    for user in required_users:
        if user not in approvals:
            if verbose:
                print(f"  ⊘ 跳过: 缺少审核人 @{user} 的批准")
            return False

    return True

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

    # Initialize summary statistics
    summary = {
        "total_issues": len(issues),
        "title_updated": 0,
        "not_member_yet": 0,
        "reminder_sent": 0,
        "waiting_approval": 0,
        "team_added": 0,
        "team_add_failed": 0,
        "completed": 0,
        "skipped": 0,
    }

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
                summary["title_updated"] += 1
                if verbose:
                    print(f"  ✓ 更新标题: {issue_title} → {new_title}")
            else:
                if verbose:
                    print(f"  ✗ 更新标题失败 (HTTP {code})")

        target = get_target_from_labels(it)
        if not target or target not in teams_cfg:
            summary["skipped"] += 1
            if verbose:
                print(f"  ⊘ 跳过: 未找到有效的目标团队标签 (target={target})\n")
            continue

        team_cfg = teams_cfg[target]
        team_slug = team_cfg.get("team_slug", "") or ""
        team_mode = team_cfg.get("mode", "auto")

        if verbose:
            print(f"  目标团队: {target} (team_slug={team_slug})")

        # If not org member yet, remind and keep open
        if not is_org_member(token, org, author):
            summary["not_member_yet"] += 1
            if verbose:
                print(f"  ⊘ 跳过: @{author} 还不是 @{org} 成员")
            if has_label(it, "invited"):
                summary["reminder_sent"] += 1
                if verbose:
                    print(f"  → 发送提醒评论")
                comment(token, repo, issue_number,
                        f"@{author} 温馨提示：你还未加入 **@{org}**。请在这里接受邀请：\n\nhttps://github.com/orgs/{org}/invitation")
            if verbose:
                print()
            continue

        if verbose:
            print(f"  ✓ @{author} 已是组织成员")

        # If approval required, ensure it is approved before adding to team
        if team_mode == "approval" and team_slug:
            if not _is_issue_approved(token, repo, org, it, team_cfg, team_slug, verbose=verbose):
                summary["waiting_approval"] += 1
                if verbose:
                    print(f"  ⊘ 跳过: @{author} 等待审核\n")
                continue

        # If needs team, ensure team membership
        if team_slug:
            if not is_user_in_team(token, org, team_slug, author):
                if verbose:
                    print(f"  → 添加到团队 @{org}/{team_slug}")
                code, payload = add_user_to_team(token, org, team_slug, author)
                if code not in (200, 201):
                    # Can't add team for some reason; leave a note and continue
                    summary["team_add_failed"] += 1
                    if verbose:
                        print(f"  ✗ 添加团队失败 (HTTP {code})")
                    comment(token, repo, issue_number,
                            f"@{author} 已检测到你已加入 **@{org}**，但加入 **@{org}/{team_slug}** 仍失败，将稍后重试。\n\n"
                            f"HTTP {code}\n\n```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```")
                    if verbose:
                        print()
                    continue
                summary["team_added"] += 1
                if verbose:
                    print(f"  ✓ 成功添加到团队")
            else:
                if verbose:
                    print(f"  ✓ 已在团队 @{org}/{team_slug} 中")

        # Now complete: comment + close
        summary["completed"] += 1
        if verbose:
            print(f"  ✓ 处理完成，关闭 Issue")
        if team_slug:
            comment(token, repo, issue_number, f"@{author} ✅ 已确认你已加入 **@{org}** 并加入 **@{org}/{team_slug}**，本 Issue 将关闭。")
        else:
            comment(token, repo, issue_number, f"@{author} ✅ 已确认你已加入 **@{org}**，本 Issue 将关闭。")

        close_issue(token, repo, issue_number)

        if verbose:
            print()

    return summary

if __name__ == "__main__":
    scan()
