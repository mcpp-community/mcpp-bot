"""
GitHub GraphQL API 客户端

用于获取 REST API 不提供的数据，特别是 GitHub Projects V2 的字段数据。
"""

import json
import urllib.request
import urllib.error


def graphql_query(token, query, variables=None):
    """
    执行 GraphQL 查询

    Args:
        token: GitHub API token
        query: GraphQL 查询字符串
        variables: 查询变量字典（可选）

    Returns:
        查询结果字典

    Raises:
        RuntimeError: 如果查询失败
    """
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, headers=headers, data=data, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            result = json.loads(raw)

            # 检查是否有错误
            if "errors" in result:
                errors = result["errors"]
                error_msgs = [e.get("message", str(e)) for e in errors]
                raise RuntimeError(f"GraphQL errors: {'; '.join(error_msgs)}")

            return result.get("data", {})

    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {raw}")


def get_issue_with_projects(token, owner, repo, issue_number):
    """
    获取包含 Projects V2 字段的 issue 信息

    Args:
        token: GitHub API token
        owner: 仓库所有者
        repo: 仓库名称
        issue_number: Issue 编号

    Returns:
        包含 Projects 字段的 issue 数据

    Example result:
        {
            "number": 1,
            "title": "Issue title",
            "projectItems": {
                "nodes": [{
                    "project": {"title": "Project Name"},
                    "fieldValues": {
                        "nodes": [{
                            "field": {"name": "Priority"},
                            "name": "P1"  # 或 "P0", "P2"
                        }]
                    }
                }]
            }
        }
    """
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $number) {
          number
          title
          projectItems(first: 10) {
            nodes {
              project {
                title
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    field {
                      ... on ProjectV2FieldCommon {
                        name
                      }
                    }
                    name
                  }
                  ... on ProjectV2ItemFieldTextValue {
                    field {
                      ... on ProjectV2FieldCommon {
                        name
                      }
                    }
                    text
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "owner": owner,
        "repo": repo,
        "number": issue_number
    }

    try:
        data = graphql_query(token, query, variables)
        repository = data.get("repository", {})
        issue = repository.get("issue", {})
        return issue
    except Exception as e:
        # GraphQL 失败时返回空数据
        return {}


def get_priority_from_projects_graphql(issue_data):
    """
    从 GraphQL 返回的 issue 数据中提取优先级

    支持多种 Priority 字段格式：
    - P0, P1, P2 (标准格式)
    - 🔴 P0, 🟡 P1, 🟢 P2 (带图标)
    - High, Medium, Low (映射到 P0, P1, P2)
    - 高, 中, 低 (中文)
    - Critical, Important, Normal (英文描述)

    注意：
    - Priority 是自定义字段，不是核心字段
    - 不同项目的 Priority 字段 ID 不同
    - 通过 field.name 识别，而不是 field.id

    Args:
        issue_data: GraphQL 返回的 issue 对象

    Returns:
        优先级值 (e.g., "0", "1", "2") 或空字符串
    """
    # 优先级映射表：将各种格式映射到 P0/P1/P2
    PRIORITY_MAPPING = {
        # 标准格式
        "P0": "0", "p0": "0",
        "P1": "1", "p1": "1",
        "P2": "2", "p2": "2",
        # 带图标
        "🔴 P0": "0", "🟡 P1": "1", "🟢 P2": "2",
        # 英文描述
        "High": "0", "high": "0", "HIGH": "0",
        "Medium": "1", "medium": "1", "MEDIUM": "1",
        "Low": "2", "low": "2", "LOW": "2",
        "Critical": "0", "critical": "0", "CRITICAL": "0",
        "Important": "1", "important": "1", "IMPORTANT": "1",
        "Normal": "2", "normal": "2", "NORMAL": "2",
        # 中文
        "高": "0", "中": "1", "低": "2",
        "紧急": "0", "重要": "1", "一般": "2",
    }

    project_items = issue_data.get("projectItems", {})
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

            # 检查是否是优先级字段（不区分大小写）
            if field_name.lower() in ["priority", "优先级", "p-level"]:
                # 获取字段值
                value_name = field_value.get("name", "").strip()

                # 直接查找映射表
                if value_name in PRIORITY_MAPPING:
                    return PRIORITY_MAPPING[value_name]

                # 如果不在映射表中，尝试提取 P0/P1/P2 格式
                if value_name.upper().startswith("P"):
                    # 提取数字部分
                    import re
                    match = re.search(r'P([012])', value_name.upper())
                    if match:
                        return match.group(1)

    return ""


def enrich_issues_with_projects(token, issues, verbose=False):
    """
    为 issues 列表补充 Projects 数据

    这个函数会为每个 issue 调用 GraphQL API 获取 Projects 字段，
    然后将优先级信息合并到 issue 对象中。

    重要说明：
    - 每个 issue 会产生 1 次 GraphQL API 调用
    - GitHub API 限制：5000 次/小时（认证用户）
    - 如果有 100 个 issues，会产生 100 次额外调用

    为什么需要这样做：
    - Priority 是 ProjectV2 的自定义字段，不是核心字段
    - REST API Search 不返回 projectItems 数据
    - 只有 GraphQL API 可以获取自定义字段

    Args:
        token: GitHub API token
        issues: issue 对象列表（来自 REST API search_issues）
        verbose: 是否显示详细日志

    Returns:
        enriched issues 列表，每个 issue 新增 "project_priority" 字段
    """
    enriched = []
    total = len(issues)
    enriched_count = 0

    for i, issue in enumerate(issues, 1):
        # 解析仓库信息
        repo_url = issue.get("repository_url", "")
        if repo_url:
            parts = repo_url.split("/")
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1]
                issue_number = issue.get("number")

                if verbose and i <= 5:  # 只显示前5个的详细日志
                    print(f"  [{i}/{total}] 获取 {owner}/{repo}#{issue_number} 的 Projects 数据...")

                try:
                    # 获取 GraphQL 数据
                    graphql_data = get_issue_with_projects(token, owner, repo, issue_number)
                    if graphql_data:
                        # 提取优先级
                        priority = get_priority_from_projects_graphql(graphql_data)
                        if priority:
                            issue["project_priority"] = priority
                            enriched_count += 1
                            if verbose and i <= 5:
                                print(f"    ✓ 优先级: P{priority}")
                        elif verbose and i <= 5:
                            print(f"    - 未设置优先级")
                except Exception as e:
                    if verbose:
                        print(f"    ✗ GraphQL 失败: {e}")

        enriched.append(issue)

    if verbose:
        if total > 5:
            print(f"  ... 还有 {total - 5} 个 issues")
        print(f"  ✓ 完成：{enriched_count}/{total} 个 issues 有 Projects 优先级")

    return enriched
