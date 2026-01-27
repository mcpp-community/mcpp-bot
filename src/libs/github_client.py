import json
import urllib.parse
import urllib.request
import urllib.error
import re

API = "https://api.github.com"

def gh(method: str, path: str, token: str, body=None):
    """
    Generic GitHub API request handler.

    Args:
        method: HTTP method (GET, POST, PATCH, PUT, DELETE, etc.)
        path: API endpoint path (e.g., "repos/owner/repo/issues")
        token: GitHub API token
        body: Optional request body (will be JSON-encoded)

    Returns:
        Tuple of (status_code, response_payload)
    """
    url = f"{API}/{path.lstrip('/')}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "mcpp-bot",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else None
        except Exception:
            payload = raw
        return e.code, payload

def comment(token, repo, issue_number, body):
    """
    Add a comment to a GitHub issue.

    Args:
        token: GitHub API token
        repo: Repository in "owner/name" format
        issue_number: Issue number
        body: Comment text
    """
    gh("POST", f"repos/{repo}/issues/{issue_number}/comments", token, {"body": body})

def close_issue(token, repo, issue_number):
    """
    Close a GitHub issue.

    Args:
        token: GitHub API token
        repo: Repository in "owner/name" format
        issue_number: Issue number
    """
    gh("PATCH", f"repos/{repo}/issues/{issue_number}", token, {"state": "closed"})

def update_issue_title(token, repo, issue_number, new_title):
    """
    Update the title of a GitHub issue.

    Args:
        token: GitHub API token
        repo: Repository in "owner/name" format
        issue_number: Issue number
        new_title: New title for the issue

    Returns:
        Tuple of (status_code, response_payload)
    """
    return gh("PATCH", f"repos/{repo}/issues/{issue_number}", token, {"title": new_title})

def has_label(issue, name):
    """
    Check if an issue has a specific label.

    Args:
        issue: Issue object from GitHub API
        name: Label name to check

    Returns:
        True if the issue has the label, False otherwise
    """
    return any(l["name"] == name for l in issue.get("labels", []))

def get_target_from_labels(issue):
    """
    Extract target from labels matching pattern "target:<value>".

    Args:
        issue: Issue object from GitHub API

    Returns:
        Target value or empty string if not found
    """
    for l in issue.get("labels", []):
        m = re.match(r"^target:(.+)$", l["name"])
        if m:
            return m.group(1)
    return ""

def is_org_member(token, org, username):
    """
    Check if a user is a member of an organization.

    Args:
        token: GitHub API token
        org: Organization name
        username: GitHub username

    Returns:
        True if user is a member, False otherwise
    """
    code, _ = gh("GET", f"orgs/{org}/members/{username}", token)
    return code == 204

def add_user_to_team(token, org, team_slug, username):
    """
    Add a user to a team in an organization.

    Args:
        token: GitHub API token
        org: Organization name
        team_slug: Team slug
        username: GitHub username

    Returns:
        Tuple of (status_code, response_payload)
    """
    return gh("PUT", f"orgs/{org}/teams/{team_slug}/memberships/{username}", token, {"role": "member"})

def is_user_in_team(token, org, team_slug, username):
    """
    Check if a user is in a team.

    Args:
        token: GitHub API token
        org: Organization name
        team_slug: Team slug
        username: GitHub username

    Returns:
        True if user is in team (active or pending), False otherwise
    """
    code, payload = gh("GET", f"orgs/{org}/teams/{team_slug}/memberships/{username}", token)
    return code == 200 and payload and payload.get("state") in ("active", "pending")

def search_issues(token, query, per_page=100):
    """
    Search issues using GitHub search API.

    Args:
        token: GitHub API token
        query: Search query string (e.g., "repo:owner/name is:issue is:open label:bug")
        per_page: Number of results per page (max 100)

    Returns:
        List of issue objects

    Raises:
        RuntimeError: If the search fails
    """
    code, payload = gh("GET", f"search/issues?q={urllib.parse.quote(query)}&per_page={per_page}", token)
    if code != 200:
        raise RuntimeError(f"Search failed: {code} {payload}")
    return payload.get("items", [])

def list_open_join_issues(token, repo):
    """
    List open issues with the "join-request" label.

    Args:
        token: GitHub API token
        repo: Repository in "owner/name" format

    Returns:
        List of issue objects

    Raises:
        RuntimeError: If the search fails
    """
    q = f"repo:{repo} is:issue is:open label:join-request"
    return search_issues(token, q)

def get_label_value(issue, pattern):
    """
    Extract value from labels matching a regex pattern.

    Args:
        issue: Issue object from GitHub API
        pattern: Regex pattern with one capture group (e.g., r"^priority:(.+)$")

    Returns:
        Matched value or empty string if not found
    """
    for l in issue.get("labels", []):
        m = re.match(pattern, l["name"])
        if m:
            return m.group(1)
    return ""

def get_priority_from_project(issue):
    """
    Extract priority from GitHub Projects V2 field data.

    GitHub Projects V2 stores custom field data in the issue object under
    'projectItems' -> 'nodes' -> 'fieldValues' -> 'nodes'

    Args:
        issue: Issue object from GitHub API (with projectItems included)

    Returns:
        Priority value (e.g., "0", "1", "2") or empty string if not found

    Example project field structure:
        {
            "projectItems": {
                "nodes": [{
                    "fieldValues": {
                        "nodes": [{
                            "field": {"name": "Priority"},
                            "name": "P0"  # or "P1", "P2"
                        }]
                    }
                }]
            }
        }
    """
    # Try to get priority from project items
    project_items = issue.get("projectItems", {})
    if isinstance(project_items, dict):
        nodes = project_items.get("nodes", [])
    else:
        nodes = project_items or []

    for project_item in nodes:
        field_values = project_item.get("fieldValues", {})
        if isinstance(field_values, dict):
            field_nodes = field_values.get("nodes", [])
        else:
            field_nodes = field_values or []

        for field_value in field_nodes:
            field = field_value.get("field", {})
            field_name = field.get("name", "")

            # Check if this is a priority field
            if field_name.lower() in ["priority", "优先级"]:
                # Get the value
                value_name = field_value.get("name", "")
                # Extract priority number from "P0", "P1", "P2"
                if value_name and value_name.startswith("P"):
                    priority_num = value_name[1:]  # Get "0", "1", "2"
                    if priority_num in ["0", "1", "2"]:
                        return priority_num

    return ""

def get_issue_assignees(issue):
    """
    Get assignees from an issue.

    Args:
        issue: Issue object from GitHub API

    Returns:
        List of assignee usernames
    """
    return [a["login"] for a in issue.get("assignees", [])]

def list_org_repos(token, org):
    """
    List all repositories in an organization.

    Args:
        token: GitHub API token
        org: Organization name

    Returns:
        List of repository objects

    Raises:
        RuntimeError: If the request fails
    """
    code, payload = gh("GET", f"orgs/{org}/repos?per_page=100&type=all", token)
    if code != 200:
        raise RuntimeError(f"Failed to list repos: {code} {payload}")
    return payload or []

def parse_issue_url(url):
    """
    Parse a GitHub issue URL to extract repo and issue number.

    Args:
        url: GitHub issue URL (e.g., https://github.com/owner/repo/issues/123)

    Returns:
        Tuple of (repo, issue_number) or (None, None) if invalid

    Example:
        >>> parse_issue_url("https://github.com/mcpp-community/OpenOrg/issues/64")
        ("mcpp-community/OpenOrg", 64)
    """
    import re
    match = re.match(r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)", url)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

def post_summary_comment(token, issue_url, summary_text):
    """
    Post a summary comment to a GitHub issue.

    Args:
        token: GitHub API token
        issue_url: Full GitHub issue URL
        summary_text: Markdown-formatted summary text to post

    Returns:
        True if successful, False otherwise
    """
    repo, issue_number = parse_issue_url(issue_url)
    if not repo or not issue_number:
        print(f"✗ 无效的 issue URL: {issue_url}")
        return False

    comment(token, repo, issue_number, summary_text)
    return True
