#!/usr/bin/env python3
"""
调试脚本：检查 GitHub Issue 对象的结构

用于查看 GitHub API 返回的 Issue 对象包含哪些字段，
特别是查找 Type 字段的位置。

使用方法:
    export GH_TOKEN=your_token
    python debug/inspect_issue_structure.py
"""

import os
import sys
import json
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libs.github_client import search_issues


def inspect_issues():
    """检查 issue 的结构"""
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("错误: 请设置环境变量 GH_TOKEN")
        return

    # 搜索 OpenOrg 仓库的 issues
    repo = "mcpp-community/OpenOrg"
    query = f"repo:{repo} is:issue is:open"

    print(f"搜索: {query}")
    print("=" * 60)

    try:
        issues = search_issues(token, query, per_page=10)  # 取10个样本
        print(f"找到 {len(issues)} 个 issues\n")

        for i, issue in enumerate(issues[:3], 1):  # 只详细查看前3个
            print(f"\n{'=' * 60}")
            print(f"Issue #{i}: #{issue['number']} - {issue['title']}")
            print("=" * 60)

            # 打印所有顶级字段
            print("\n顶级字段:")
            for key in sorted(issue.keys()):
                value = issue[key]
                if isinstance(value, (str, int, bool, type(None))):
                    print(f"  {key}: {value}")
                elif isinstance(value, list):
                    print(f"  {key}: [{len(value)} items]")
                elif isinstance(value, dict):
                    print(f"  {key}: {{dict with {len(value)} keys}}")

            # 详细查看 labels
            print("\nLabels:")
            labels = issue.get("labels", [])
            if labels:
                for label in labels:
                    print(f"  - {label.get('name')}")
            else:
                print("  (无标签)")

            # 查找可能的 Type 字段
            print("\n查找 Type 相关字段:")
            potential_type_fields = [
                "type", "issue_type", "issueType", "state_reason",
                "active_lock_reason", "performed_via_github_app"
            ]
            for field in potential_type_fields:
                if field in issue:
                    value = issue[field]
                    print(f"  ✓ {field}: {value}")
                    if isinstance(value, dict):
                        print(f"    详细: {json.dumps(value, indent=6, ensure_ascii=False)}")
                else:
                    print(f"  ✗ {field}: (不存在)")

            # 测试 get_issue_type 函数
            print("\n测试 get_issue_type() 函数:")
            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            from libs.github_client import get_issue_type
            detected_type = get_issue_type(issue)
            print(f"  检测到的 Type: {detected_type if detected_type else '(未检测到)'}")

            # 完整的 JSON 输出（前50行）
            print("\n完整 JSON:")
            full_json = json.dumps(issue, indent=2, ensure_ascii=False)
            lines = full_json.split('\n')
            for line in lines[:50]:
                print(line)
            if len(lines) > 50:
                print(f"... (还有 {len(lines) - 50} 行)")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    inspect_issues()
