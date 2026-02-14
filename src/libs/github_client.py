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

def list_issue_comments(token, repo, issue_number, per_page=100):
    """
    List comments for a GitHub issue.

    Args:
        token: GitHub API token
        repo: Repository in "owner/name" format
        issue_number: Issue number
        per_page: Number of results per page (max 100)

    Returns:
        List of comment objects

    Raises:
        RuntimeError: If the request fails
    """
    code, payload = gh("GET", f"repos/{repo}/issues/{issue_number}/comments?per_page={per_page}", token)
    if code != 200:
        raise RuntimeError(f"Failed to list issue comments: {code} {payload}")
    return payload or []

def search_issues(token, query, per_page=100):
    """
    Search issues using GitHub search API.

    Note: GitHub REST API Search 可能不会返回 issue_type 字段。
    如果需要获取 issue_type，可能需要：
    1. 为每个 issue 单独调用 GET /repos/:owner/:repo/issues/:number
    2. 或者使用 GraphQL API

    Args:
        token: GitHub API token
        query: Search query string (e.g., "repo:owner/name is:issue is:open label:bug")
        per_page: Number of results per page (max 100)

    Returns:
        List of issue objects

    Raises:
        RuntimeError: If the search fails
    """
    # 添加 Accept header 以获取 Beta 功能
    # GitHub 的 issue_type 功能可能需要特殊的 Accept header
    url = f"search/issues?q={urllib.parse.quote(query)}&per_page={per_page}"
    code, payload = gh("GET", url, token)
    if code != 200:
        raise RuntimeError(f"Search failed: {code} {payload}")

    issues = payload.get("items", [])

    # 如果搜索结果中没有 issue_type 字段，可以尝试为每个 issue 获取完整信息
    # 但这会增加 API 调用次数，所以默认不启用
    # 如果需要，可以取消下面的注释

    # for i, issue in enumerate(issues):
    #     if "issue_type" not in issue:
    #         # 获取完整的 issue 信息
    #         repo_url = issue.get("repository_url", "")
    #         issue_number = issue.get("number")
    #         if repo_url and issue_number:
    #             owner_repo = "/".join(repo_url.split("/")[-2:])
    #             code, full_issue = gh("GET", f"repos/{owner_repo}/issues/{issue_number}", token)
    #             if code == 200 and full_issue:
    #                 issues[i] = full_issue

    return issues

def get_issue_type(issue):
    """
    Get the type of an issue (Bug, Task, Feature, etc.).

    GitHub Issues 的 Type 可以通过以下方式获取（按优先级）：
    1. 原生 type 字段（GitHub REST API 返回的字段）
    2. Labels 标签（如 "Task", "Type: Task", "type/task"）
    3. Project 字段（未来支持）

    Args:
        issue: Issue object from GitHub API

    Returns:
        Issue type string (e.g., "Task", "Bug", "Feature") or empty string

    Examples:
        原生字段: issue["type"] = "Task"  (如果为 null 则没有设置)
        标签方式: issue["labels"] = [{"name": "Task"}, ...]
    """
    # 1. 优先检查原生的 'type' 字段
    # GitHub REST API 返回 "type" 字段，可能的值: "Task", "Bug", "Feature", null
    type_field = issue.get("type")
    if type_field:  # type_field 不是 None 且不是空字符串
        if isinstance(type_field, str):
            return type_field
        elif isinstance(type_field, dict):
            return type_field.get("name", "")

    # 2. 检查 issue_type 字段（备用，某些 API 可能使用这个名称）
    issue_type = issue.get("issue_type")
    if issue_type:
        if isinstance(issue_type, str):
            return issue_type
        elif isinstance(issue_type, dict):
            return issue_type.get("name", "")

    # 3. 从 labels 中查找 Type
    for label in issue.get("labels", []):
        label_name = label.get("name", "")

        # 直接标签：Task, Bug, Feature
        if label_name in ["Task", "Bug", "Feature", "Enhancement"]:
            return label_name

        # "Type: XXX" 格式
        if label_name.startswith("Type:"):
            return label_name.split(":", 1)[1].strip()

        # "type/XXX" 格式
        if label_name.startswith("type/"):
            return label_name.split("/", 1)[1].strip()

        # 中文标签支持
        type_mapping = {
            "任务": "Task",
            "缺陷": "Bug",
            "功能": "Feature",
            "增强": "Enhancement",
        }
        if label_name in type_mapping:
            return type_mapping[label_name]

    return ""

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

    注意: REST API 的 Search Issues 不返回 projectItems 字段！
    如果需要从 Projects 获取优先级，必须：
    1. 使用 GraphQL API
    2. 或者在 issue 对象中查找 "project_priority" 字段（由 GraphQL 补充）

    Args:
        issue: Issue object from GitHub API

    Returns:
        Priority value (e.g., "0", "1", "2") or empty string if not found
    """
    # 首先检查是否有 GraphQL 补充的 project_priority 字段
    project_priority = issue.get("project_priority", "")
    if project_priority:
        return project_priority

    # REST API 返回的 projectItems 字段（通常不存在）
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
