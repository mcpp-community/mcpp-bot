#!/usr/bin/env python3
"""
分析实际 issues 的 type 字段值

这个脚本会：
1. 搜索你组织的所有 issues
2. 统计不同 type 值的分布
3. 显示每个 type 的示例 issues
"""

import os
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libs.github_client import search_issues, get_issue_type


def main():
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("错误: 请设置环境变量 GH_TOKEN")
        return

    org = "mcpp-community"
    print(f"分析组织: {org}")
    print("=" * 60)

    # 搜索所有打开的 issues
    query = f"org:{org} is:issue is:open"
    print(f"搜索: {query}\n")

    try:
        issues = search_issues(token, query, per_page=100)
        print(f"找到 {len(issues)} 个打开的 issues\n")

        if not issues:
            print("没有找到 issues")
            return

        # 统计 type 字段的原始值
        type_raw_values = Counter()
        type_detected_values = Counter()
        type_examples = {}

        for issue in issues:
            # 原始 type 字段值
            raw_type = issue.get("type")
            type_raw_values[str(raw_type)] += 1

            # 使用 get_issue_type 检测的值
            detected_type = get_issue_type(issue)
            if not detected_type:
                detected_type = "(empty)"
            type_detected_values[detected_type] += 1

            # 保存示例
            if detected_type not in type_examples:
                type_examples[detected_type] = []
            if len(type_examples[detected_type]) < 3:
                type_examples[detected_type].append({
                    "number": issue['number'],
                    "title": issue['title'],
                    "repo": issue.get('repository_url', '').split('/')[-1],
                    "raw_type": raw_type,
                    "labels": [l['name'] for l in issue.get('labels', [])]
                })

        # 显示统计结果
        print("=" * 60)
        print("1. 原始 type 字段值分布:")
        print("=" * 60)
        for type_val, count in type_raw_values.most_common():
            print(f"  {type_val}: {count} 个")

        print("\n" + "=" * 60)
        print("2. get_issue_type() 检测结果分布:")
        print("=" * 60)
        for type_val, count in type_detected_values.most_common():
            print(f"  {type_val}: {count} 个")

        print("\n" + "=" * 60)
        print("3. 每种 Type 的示例 issues:")
        print("=" * 60)
        for type_val in sorted(type_examples.keys()):
            examples = type_examples[type_val]
            print(f"\nType: {type_val} ({type_detected_values[type_val]} 个)")
            print("-" * 60)
            for ex in examples:
                print(f"  [{ex['repo']}] #{ex['number']}: {ex['title']}")
                print(f"    原始 type: {ex['raw_type']}")
                if ex['labels']:
                    print(f"    标签: {', '.join(ex['labels'])}")
                else:
                    print(f"    标签: (无)")

        # 诊断建议
        print("\n" + "=" * 60)
        print("诊断和建议:")
        print("=" * 60)

        task_count = type_detected_values.get("Task", 0)
        if task_count == 0:
            print("\n❌ 没有找到任何 Type=Task 的 issues")
            print("\n可能的原因:")
            print("  1. Issues 的 type 字段都是 null（未设置）")
            print("  2. Issues 没有 'Task' 标签")
            print("\n解决方案:")
            print("  方案 A: 在 GitHub 组织设置中启用 Issue Types 功能，并为 issues 设置 Type")
            print("  方案 B: 为 issues 添加 'Task' 标签")
            print("  方案 C: 使用其他标签格式（如 'Type: Task'）")
        else:
            print(f"\n✓ 找到 {task_count} 个 Type=Task 的 issues")

        null_count = type_detected_values.get("(empty)", 0)
        if null_count > 0:
            print(f"\n⚠️  有 {null_count} 个 issues 没有 Type 信息")
            print("  建议为这些 issues 添加 Type 或标签")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
