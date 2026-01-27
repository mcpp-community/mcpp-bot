import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path to import from libs
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.github_client import (
    search_issues,
    comment,
    get_label_value,
    get_priority_from_project,
    get_issue_assignees,
    get_issue_type,
    list_org_repos,
)
from libs.github_graphql import enrich_issues_with_projects
from libs.utils import load_simple_yaml


def parse_iso_datetime(iso_str):
    """
    Parse ISO 8601 datetime string to datetime object.

    Args:
        iso_str: ISO 8601 formatted datetime string

    Returns:
        datetime object with UTC timezone
    """
    # GitHub returns ISO 8601 format like "2024-01-27T10:30:00Z"
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))


def get_hours_since_update(issue):
    """
    Calculate hours since the issue was last updated.

    Args:
        issue: Issue object from GitHub API

    Returns:
        Hours since last update as float
    """
    updated_at = parse_iso_datetime(issue["updated_at"])
    now = datetime.now(timezone.utc)
    delta = now - updated_at
    return delta.total_seconds() / 3600


def check_task_timeout(token, repo, issue, config, verbose=False):
    """
    Check if a task issue has timed out and send reminder if needed.

    Args:
        token: GitHub API token
        repo: Repository in "owner/name" format
        issue: Issue object from GitHub API
        config: Configuration dictionary
        verbose: Enable verbose logging

    Returns:
        Dictionary with reminder info if sent, None otherwise
        Format: {"priority": "P0", "issue_number": 123, "title": "...", "url": "...", "skip_reason": "..."}
    """
    # Get priority from labels or project fields
    priority = get_label_value(issue, config.get("priority_pattern", r"^P([012])$"))

    # If not found in labels, try project fields
    if not priority:
        priority = get_priority_from_project(issue)

    if not priority:
        if verbose:
            print(f"  ⊘ 跳过: 未找到优先级（标签或Project字段）")
        return {"skip_reason": "no_priority"}

    # Get timeout hours for this priority
    timeout_key = f"P{priority}"
    timeout_hours = config.get("timeout_hours", {}).get(timeout_key)
    if timeout_hours is None:
        if verbose:
            print(f"  ⊘ 跳过: {timeout_key} 未配置超时时间")
        return {"skip_reason": "no_timeout_config"}

    # Convert to float (in case it's a string from YAML)
    try:
        timeout_hours = float(timeout_hours)
    except (ValueError, TypeError):
        if verbose:
            print(f"  ⊘ 跳过: {timeout_key} 超时配置无效: {timeout_hours}")
        return {"skip_reason": "no_timeout_config"}

    # Check if issue has timed out
    hours_since_update = get_hours_since_update(issue)
    if verbose:
        print(f"  优先级: {timeout_key}, 超时阈值: {timeout_hours}h, 距上次更新: {hours_since_update:.1f}h")

    if hours_since_update < timeout_hours:
        if verbose:
            print(f"  ⊘ 跳过: 未超时")
        return {"skip_reason": "not_timeout"}

    # Get assignees to mention
    assignees = get_issue_assignees(issue)
    if not assignees:
        # No assignees, optionally notify in config
        if not config.get("notify_unassigned", False):
            return False

        # Handle default_mention as string or list
        default_mention = config.get("default_mention", "@team")
        if isinstance(default_mention, list):
            assignees_mention = " ".join(default_mention)
        else:
            assignees_mention = default_mention
    else:
        assignees_mention = " ".join([f"@{a}" for a in assignees])

    # Build reminder message
    issue_number = issue["number"]
    issue_title = issue["title"]

    reminder_template = config.get("reminder_template",
        "⏰ **任务提醒**\n\n"
        "{assignees} 这个 {priority} 优先级的任务已经 {hours:.1f} 小时没有更新了。\n\n"
        "请及时更新进度或状态。\n\n"
        "**Issue:** {title}\n"
        "**超时阈值:** {timeout} 小时"
    )

    reminder_msg = reminder_template.format(
        assignees=assignees_mention,
        priority=timeout_key,
        hours=hours_since_update,
        title=issue_title,
        timeout=timeout_hours
    )

    # Add comment
    if verbose:
        print(f"  ✓ 发送超时提醒")
    comment(token, repo, issue_number, reminder_msg)

    # Optional: Add a label to mark as reminded
    if config.get("add_reminded_label", False):
        # This would require adding a label function in github_client
        pass

    # Return reminder info
    return {
        "priority": timeout_key,
        "issue_number": issue_number,
        "title": issue_title,
        "url": issue.get("html_url", f"https://github.com/{repo}/issues/{issue_number}"),
        "hours_since_update": hours_since_update,
    }


def scan_repo_tasks(token, repo, config, verbose=False):
    """
    Scan a single repository for task issues that need reminders.

    Args:
        token: GitHub API token
        repo: Repository in "owner/name" format
        config: Configuration dictionary
        verbose: Enable verbose logging

    Returns:
        Dictionary with summary statistics
    """
    # Build search query for open issues
    # Note: We can't filter by Type in search query since it's not a standard field
    # We'll search for all open issues and filter by Type later
    query_parts = [
        f"repo:{repo}",
        "is:issue",
        "is:open",
    ]

    # Optionally add label filter if configured
    task_label = config.get("task_label", "")
    if task_label:
        query_parts.append(f"label:{task_label}")

    query = " ".join(query_parts)

    # Search issues
    try:
        issues = search_issues(token, query)
    except RuntimeError as e:
        print(f"Error searching {repo}: {e}")
        return {
            "total_issues": 0,
            "task_issues": 0,
            "checked_issues": 0,
            "reminders_sent": 0,
            "skipped_no_priority": 0,
            "skipped_not_in_filter": 0,
            "skipped_no_timeout_config": 0,
            "skipped_not_timeout": 0,
            "reminded_issues": []
        }

    if verbose:
        print(f"找到 {len(issues)} 个打开的 Issue")

    # 使用 GraphQL 补充 Projects 数据
    # 注意：这会为每个 issue 产生一次额外的 API 调用
    use_graphql = config.get("use_graphql_for_projects", True)
    if use_graphql and issues:
        if verbose:
            print(f"使用 GraphQL API 获取 Projects 优先级数据（{len(issues)} 个 issues）...")
        try:
            issues = enrich_issues_with_projects(token, issues, verbose=verbose)
            if verbose:
                print()
        except Exception as e:
            if verbose:
                print(f"⚠️ GraphQL API 调用失败: {e}")
                print(f"将继续使用 Labels 方式检测优先级\n")
    elif verbose:
        print()

    # Filter by Type first
    task_type = config.get("task_type", "Task")
    filtered_issues = []

    for issue in issues:
        issue_type = get_issue_type(issue)
        if issue_type == task_type:
            filtered_issues.append(issue)

    if verbose:
        print(f"其中 {len(filtered_issues)} 个 Type={task_type} 的任务\n")

    # Filter issues by priority and check for timeouts
    priority_filter = config.get("priorities_to_check", ["P0", "P1", "P2"])
    priority_pattern = config.get("priority_pattern", r"^P([012])$")

    summary = {
        "total_issues": len(issues),
        "task_issues": len(filtered_issues),
        "checked_issues": 0,
        "reminders_sent": 0,
        "skipped_no_priority": 0,  # 未设置优先级
        "skipped_not_in_filter": 0,  # 优先级不在检查范围
        "skipped_no_timeout_config": 0,  # 优先级未配置超时时间
        "skipped_not_timeout": 0,  # 未超时
        "reminded_issues": [],  # List of issues that got reminders
    }
    for issue in filtered_issues:
        if verbose:
            issue_number = issue["number"]
            print(f"检查 Issue #{issue_number}")
            print(f"  URL: {issue.get('html_url', f'https://github.com/{repo}/issues/{issue_number}')}")

        # Get priority from labels or project fields
        priority = get_label_value(issue, priority_pattern)
        if not priority:
            priority = get_priority_from_project(issue)

        # Check if has priority
        if not priority:
            summary["skipped_no_priority"] += 1
            if verbose:
                print(f"  ⊘ 跳过: 未设置优先级（无标签或Project字段）\n")
            continue

        # Check if priority is in filter
        if f"P{priority}" not in priority_filter:
            summary["skipped_not_in_filter"] += 1
            if verbose:
                print(f"  ⊘ 跳过: 优先级 P{priority} 不在检查范围 {priority_filter}\n")
            continue

        # This issue has a valid priority and will be checked
        summary["checked_issues"] += 1

        # Check if timeout and send reminder
        reminder_info = check_task_timeout(token, repo, issue, config, verbose=verbose)

        if reminder_info:
            # Check skip reason
            skip_reason = reminder_info.get("skip_reason")
            if skip_reason == "no_priority":
                # Already handled above, shouldn't reach here
                pass
            elif skip_reason == "no_timeout_config":
                summary["skipped_no_timeout_config"] += 1
            elif skip_reason == "not_timeout":
                summary["skipped_not_timeout"] += 1
            elif skip_reason is None:
                # Reminder was sent
                summary["reminders_sent"] += 1
                summary["reminded_issues"].append(reminder_info)
                print(f"✓ 发送提醒 {repo}#{issue['number']}: {issue['title']}")

        if verbose:
            print()

    return summary


def scan_org_tasks(token, org, config, verbose=False):
    """
    Scan all repositories in an organization for task issues.

    Args:
        token: GitHub API token
        org: Organization name
        config: Configuration dictionary
        verbose: Enable verbose logging

    Returns:
        Dictionary with summary statistics
    """
    # Get all repositories in the org
    try:
        repos = list_org_repos(token, org)
    except RuntimeError as e:
        print(f"Error listing repos for {org}: {e}")
        return {"total_repos": 0, "total_issues": 0, "reminders_sent": 0, "skipped": 0}

    if verbose:
        print(f"组织 {org} 中找到 {len(repos)} 个仓库\n")

    # Scan each repository
    total_summary = {
        "total_repos": 0,
        "total_issues": 0,
        "task_issues": 0,
        "checked_issues": 0,
        "reminders_sent": 0,
        "skipped_no_priority": 0,
        "skipped_not_in_filter": 0,
        "skipped_no_timeout_config": 0,
        "skipped_not_timeout": 0,
        "reminded_issues": [],  # Aggregate all reminded issues
    }

    for repo_obj in repos:
        repo_full_name = repo_obj["full_name"]

        # Check if repo should be excluded
        exclude_repos = config.get("exclude_repos", [])
        if repo_full_name in exclude_repos or repo_obj["name"] in exclude_repos:
            if verbose:
                print(f"⊘ 跳过排除的仓库: {repo_full_name}\n")
            else:
                print(f"Skipping excluded repo: {repo_full_name}")
            continue

        print(f"扫描仓库: {repo_full_name}")
        repo_summary = scan_repo_tasks(token, repo_full_name, config, verbose=verbose)
        total_summary["total_repos"] += 1
        total_summary["total_issues"] += repo_summary.get("total_issues", 0)
        total_summary["task_issues"] += repo_summary.get("task_issues", 0)
        total_summary["checked_issues"] += repo_summary.get("checked_issues", 0)
        total_summary["reminders_sent"] += repo_summary.get("reminders_sent", 0)
        total_summary["skipped_no_priority"] += repo_summary.get("skipped_no_priority", 0)
        total_summary["skipped_not_in_filter"] += repo_summary.get("skipped_not_in_filter", 0)
        total_summary["skipped_no_timeout_config"] += repo_summary.get("skipped_no_timeout_config", 0)
        total_summary["skipped_not_timeout"] += repo_summary.get("skipped_not_timeout", 0)
        total_summary["reminded_issues"].extend(repo_summary.get("reminded_issues", []))
        if verbose:
            print()

    return total_summary


def check(verbose=False):
    """
    Main function to check tasks and send reminders based on configuration.

    Args:
        verbose: Enable verbose logging
    """
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "task-checker.yml"
    cfg = load_simple_yaml(str(config_path))

    # Get token from environment variable
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        raise ValueError("Environment variable GH_TOKEN is not set or empty")

    # Get scan scope
    scan_mode = cfg.get("scan_mode", "repo")  # "repo" or "org"

    if verbose:
        print(f"扫描模式: {scan_mode}")
        print(f"任务标签: {cfg.get('task_label', 'Task')}")
        print(f"检查优先级: {cfg.get('priorities_to_check', ['P0', 'P1', 'P2'])}")
        print(f"超时配置: {cfg.get('timeout_hours', {})}")
        print()

    if scan_mode == "org":
        # Scan entire organization
        org = cfg.get("org", "").strip()
        if not org:
            raise ValueError("Organization (org) must be set in config when scan_mode is 'org'")

        print(f"扫描组织: {org}")
        summary = scan_org_tasks(token, org, cfg, verbose=verbose)
        print(f"\n总计发送提醒: {summary.get('reminders_sent', 0)}")

    elif scan_mode == "repo":
        # Scan single repository
        repo = cfg.get("repo", "").strip()
        if not repo:
            raise ValueError("Repository (repo) must be set in config when scan_mode is 'repo'")

        print(f"扫描仓库: {repo}")
        summary = scan_repo_tasks(token, repo, cfg, verbose=verbose)
        print(f"\n总计发送提醒: {summary.get('reminders_sent', 0)}")

    else:
        raise ValueError(f"Invalid scan_mode: {scan_mode}. Must be 'repo' or 'org'")

    return summary


if __name__ == "__main__":
    check()
