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
    get_issue_assignees,
    list_org_repos,
)
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


def check_task_timeout(token, repo, issue, config):
    """
    Check if a task issue has timed out and send reminder if needed.

    Args:
        token: GitHub API token
        repo: Repository in "owner/name" format
        issue: Issue object from GitHub API
        config: Configuration dictionary

    Returns:
        True if reminder was sent, False otherwise
    """
    # Get priority from labels
    priority = get_label_value(issue, config.get("priority_pattern", r"^P([012])$"))
    if not priority:
        return False

    # Get timeout hours for this priority
    timeout_key = f"P{priority}"
    timeout_hours = config.get("timeout_hours", {}).get(timeout_key)
    if timeout_hours is None:
        return False

    # Check if issue has timed out
    hours_since_update = get_hours_since_update(issue)
    if hours_since_update < timeout_hours:
        return False

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
    comment(token, repo, issue_number, reminder_msg)

    # Optional: Add a label to mark as reminded
    if config.get("add_reminded_label", False):
        # This would require adding a label function in github_client
        pass

    return True


def scan_repo_tasks(token, repo, config):
    """
    Scan a single repository for task issues that need reminders.

    Args:
        token: GitHub API token
        repo: Repository in "owner/name" format
        config: Configuration dictionary

    Returns:
        Number of reminders sent
    """
    # Build search query for open issues with Task label
    task_label = config.get("task_label", "Task")

    query_parts = [
        f"repo:{repo}",
        "is:issue",
        "is:open",
        f"label:{task_label}"
    ]

    query = " ".join(query_parts)

    # Search issues
    try:
        issues = search_issues(token, query)
    except RuntimeError as e:
        print(f"Error searching {repo}: {e}")
        return 0

    # Filter issues by priority and check for timeouts
    priority_filter = config.get("priorities_to_check", ["P0", "P1", "P2"])
    priority_pattern = config.get("priority_pattern", r"^P([012])$")

    reminders_sent = 0
    for issue in issues:
        # Check if issue has one of the target priorities
        priority = get_label_value(issue, priority_pattern)
        if not priority or f"P{priority}" not in priority_filter:
            continue

        # Check if timeout and send reminder
        if check_task_timeout(token, repo, issue, config):
            reminders_sent += 1
            print(f"Sent reminder for {repo}#{issue['number']}: {issue['title']}")

    return reminders_sent


def scan_org_tasks(token, org, config):
    """
    Scan all repositories in an organization for task issues.

    Args:
        token: GitHub API token
        org: Organization name
        config: Configuration dictionary

    Returns:
        Number of reminders sent
    """
    # Get all repositories in the org
    try:
        repos = list_org_repos(token, org)
    except RuntimeError as e:
        print(f"Error listing repos for {org}: {e}")
        return 0

    # Scan each repository
    total_reminders = 0
    for repo_obj in repos:
        repo_full_name = repo_obj["full_name"]

        # Check if repo should be excluded
        exclude_repos = config.get("exclude_repos", [])
        if repo_full_name in exclude_repos or repo_obj["name"] in exclude_repos:
            print(f"Skipping excluded repo: {repo_full_name}")
            continue

        print(f"Scanning {repo_full_name}...")
        reminders = scan_repo_tasks(token, repo_full_name, config)
        total_reminders += reminders

    return total_reminders


def check():
    """
    Main function to check tasks and send reminders based on configuration.
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

    if scan_mode == "org":
        # Scan entire organization
        org = cfg.get("org", "").strip()
        if not org:
            raise ValueError("Organization (org) must be set in config when scan_mode is 'org'")

        print(f"Scanning organization: {org}")
        reminders_sent = scan_org_tasks(token, org, cfg)
        print(f"\nTotal reminders sent: {reminders_sent}")

    elif scan_mode == "repo":
        # Scan single repository
        repo = cfg.get("repo", "").strip()
        if not repo:
            raise ValueError("Repository (repo) must be set in config when scan_mode is 'repo'")

        print(f"Scanning repository: {repo}")
        reminders_sent = scan_repo_tasks(token, repo, cfg)
        print(f"\nTotal reminders sent: {reminders_sent}")

    else:
        raise ValueError(f"Invalid scan_mode: {scan_mode}. Must be 'repo' or 'org'")


if __name__ == "__main__":
    check()
