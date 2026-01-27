#!/usr/bin/env python3
"""
检查公开 GitHub API 的响应结构（不需要 token）
"""

import json
import urllib.request
import urllib.error


def fetch_public_api(url):
    """获取公开 API"""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "mcpp-bot-debug",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return None


def main():
    # 检查 mcpp-community/OpenOrg 的公开 issues
    repo = "mcpp-community/OpenOrg"

    print("=" * 60)
    print(f"检查公开仓库: {repo}")
    print("=" * 60)

    # 1. Search API
    print("\n1. 使用 Search API:")
    print("-" * 60)
    search_url = f"https://api.github.com/search/issues?q=repo:{repo}+is:issue+is:open&per_page=3"
    search_result = fetch_public_api(search_url)

    if search_result and "items" in search_result:
        issues = search_result["items"]
        print(f"找到 {len(issues)} 个 issues\n")

        if issues:
            issue = issues[0]
            print(f"Issue #{issue['number']}: {issue['title']}")
            print(f"\nSearch API 返回的字段:")
            for key in sorted(issue.keys()):
                value = issue[key]
                if key in ["issue_type", "type", "issueType"]:
                    print(f"  ✓ {key}: {value}")
                else:
                    print(f"  - {key}")

            # 检查 issue_type
            if "issue_type" in issue:
                print(f"\n✓✓✓ issue_type 字段存在: {issue['issue_type']}")
            else:
                print(f"\n✗✗✗ issue_type 字段不存在（Search API）")

            # 保存 issue_number 用于下一步
            issue_number = issue['number']

            # 2. Issues API (单个 issue)
            print("\n" + "=" * 60)
            print("2. 使用 Issues API (单个 issue):")
            print("-" * 60)
            issue_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
            full_issue = fetch_public_api(issue_url)

            if full_issue:
                print(f"Issue #{full_issue['number']}: {full_issue['title']}")
                print(f"\nIssues API 返回的字段:")
                for key in sorted(full_issue.keys()):
                    value = full_issue[key]
                    if key in ["issue_type", "type", "issueType"]:
                        print(f"  ✓ {key}: {value}")
                    else:
                        print(f"  - {key}")

                # 检查 issue_type
                if "issue_type" in full_issue:
                    print(f"\n✓✓✓ issue_type 字段存在: {full_issue['issue_type']}")
                else:
                    print(f"\n✗✗✗ issue_type 字段不存在（Issues API）")

                # 检查 labels 中是否有 Type 信息
                print("\n" + "-" * 60)
                print("Labels 标签:")
                labels = full_issue.get("labels", [])
                if labels:
                    for label in labels:
                        print(f"  - {label['name']}")
                else:
                    print("  (无标签)")

                # 显示部分 JSON
                print("\n" + "-" * 60)
                print("完整 JSON 结构（前 80 行）:")
                full_json = json.dumps(full_issue, indent=2, ensure_ascii=False)
                lines = full_json.split('\n')
                for line in lines[:80]:
                    print(line)
                if len(lines) > 80:
                    print(f"... (还有 {len(lines) - 80} 行)")

    print("\n" + "=" * 60)
    print("总结:")
    print("=" * 60)
    print("如果 issue_type 字段不存在，可能的原因:")
    print("  1. GitHub 的 Issue Types 功能需要在组织设置中启用")
    print("  2. 该功能可能还在 Beta 阶段，需要特殊权限")
    print("  3. REST API 可能不支持，需要使用 GraphQL API")
    print("  4. 需要使用不同的 Accept header")
    print("\n如果使用 Labels 方式，请确保 issues 有以下标签之一:")
    print("  - Task, Bug, Feature")
    print("  - Type: Task, Type: Bug, Type: Feature")
    print("  - type/task, type/bug, type/feature")


if __name__ == "__main__":
    main()
