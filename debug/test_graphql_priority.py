#!/usr/bin/env python3
"""
测试 GraphQL API 获取 Projects 优先级

这个脚本会测试从 GitHub Projects V2 获取优先级的功能。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libs.github_graphql import get_issue_with_projects, get_priority_from_projects_graphql


def main():
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("错误: 请设置环境变量 GH_TOKEN")
        print("\n使用方法:")
        print("  export GH_TOKEN=your_github_token")
        print("  python debug/test_graphql_priority.py")
        return

    # 测试公开的 issue
    owner = "mcpp-community"
    repo = "mcpp-bot"
    issue_number = 1

    print(f"测试获取 Issue #{issue_number} 的 Projects 数据")
    print(f"仓库: {owner}/{repo}")
    print("=" * 60)

    try:
        # 使用 GraphQL 获取 issue 数据
        issue_data = get_issue_with_projects(token, owner, repo, issue_number)

        if not issue_data:
            print("✗ 未能获取 issue 数据")
            return

        print(f"\nIssue #{issue_data.get('number')}: {issue_data.get('title')}")
        print("-" * 60)

        # 检查 projectItems
        project_items = issue_data.get("projectItems", {})
        if isinstance(project_items, dict):
            nodes = project_items.get("nodes", [])
        else:
            nodes = project_items or []

        if not nodes:
            print("\n✗ 该 issue 没有添加到任何 Project")
            print("\n提示:")
            print("  1. 确保 issue 已添加到 GitHub Project")
            print("  2. 确保 Project 中设置了 Priority 字段")
            return

        print(f"\n✓ 该 issue 在 {len(nodes)} 个 Project 中")

        # 显示每个 Project 的信息
        for i, project_item in enumerate(nodes, 1):
            project_title = project_item.get("project", {}).get("title", "Unknown")
            print(f"\nProject {i}: {project_title}")
            print("-" * 40)

            field_values = project_item.get("fieldValues", {})
            if isinstance(field_values, dict):
                field_nodes = field_values.get("nodes", [])
            else:
                field_nodes = field_values or []

            if not field_nodes:
                print("  (无字段值)")
                continue

            print("  字段值:")
            for field_value in field_nodes:
                field = field_value.get("field", {})
                field_name = field.get("name", "Unknown Field")
                value_name = field_value.get("name", field_value.get("text", "N/A"))
                print(f"    - {field_name}: {value_name}")

        # 提取优先级
        priority = get_priority_from_projects_graphql(issue_data)
        print("\n" + "=" * 60)
        if priority:
            print(f"✓ 检测到优先级: P{priority}")
        else:
            print("✗ 未检测到优先级")
            print("\n可能的原因:")
            print("  1. Project 中没有 'Priority' 字段")
            print("  2. Priority 字段的值不是 P0/P1/P2 格式")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
