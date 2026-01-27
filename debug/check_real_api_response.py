#!/usr/bin/env python3
"""
检查真实的 GitHub API 响应

这个脚本会：
1. 使用 Search API 搜索 issues
2. 使用 Issues API 获取单个 issue 的完整信息
3. 对比两者的差异，特别是 issue_type 字段
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libs.github_client import gh, search_issues


def main():
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("错误: 请设置环境变量 GH_TOKEN")
        print("\n使用方法:")
        print("  export GH_TOKEN=your_github_token")
        print("  python debug/check_real_api_response.py")
        return

    repo = "mcpp-community/OpenOrg"
    print(f"检查仓库: {repo}")
    print("=" * 60)

    # 1. 使用 Search API
    print("\n1. Search API 结果:")
    print("-" * 60)
    query = f"repo:{repo} is:issue is:open"
    try:
        issues = search_issues(token, query, per_page=3)
        print(f"找到 {len(issues)} 个 issues")

        if issues:
            issue = issues[0]
            print(f"\nIssue #{issue['number']}: {issue['title']}")
            print(f"\n字段列表:")
            for key in sorted(issue.keys()):
                print(f"  - {key}")

            # 检查 issue_type
            if "issue_type" in issue:
                print(f"\n✓ issue_type 字段存在: {issue['issue_type']}")
            else:
                print(f"\n✗ issue_type 字段不存在")

    except Exception as e:
        print(f"Search API 失败: {e}")
        import traceback
        traceback.print_exc()

    # 2. 使用 Issues API 获取单个 issue
    print("\n" + "=" * 60)
    print("2. Issues API 结果 (单个 issue):")
    print("-" * 60)

    if issues:
        issue_number = issues[0]['number']
        print(f"获取 Issue #{issue_number} 的完整信息...")

        try:
            code, full_issue = gh("GET", f"repos/{repo}/issues/{issue_number}", token)
            if code == 200 and full_issue:
                print(f"\n字段列表:")
                for key in sorted(full_issue.keys()):
                    print(f"  - {key}")

                # 检查 issue_type
                if "issue_type" in full_issue:
                    print(f"\n✓ issue_type 字段存在: {full_issue['issue_type']}")
                else:
                    print(f"\n✗ issue_type 字段不存在")

                # 显示完整的 JSON（前100行）
                print(f"\n完整 JSON (前100行):")
                full_json = json.dumps(full_issue, indent=2, ensure_ascii=False)
                lines = full_json.split('\n')
                for line in lines[:100]:
                    print(line)
                if len(lines) > 100:
                    print(f"\n... (还有 {len(lines) - 100} 行)")

            else:
                print(f"获取失败: HTTP {code}")

        except Exception as e:
            print(f"Issues API 失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("提示:")
    print("  - 如果两个 API 都没有 issue_type 字段，可能需要：")
    print("    1. 在组织设置中启用 Issue Types 功能")
    print("    2. 使用特殊的 Accept header")
    print("    3. 使用 GraphQL API")
    print("=" * 60)


if __name__ == "__main__":
    main()
