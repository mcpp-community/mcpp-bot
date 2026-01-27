#!/usr/bin/env python3
"""
手动测试 issue_type 检测

这个脚本用于测试不同格式的 issue_type 字段
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libs.github_client import get_issue_type


def test_cases():
    """测试各种 issue_type 格式"""

    test_issues = [
        # 测试 1: 原生 issue_type 字符串格式
        {
            "name": "原生 issue_type (字符串)",
            "issue": {
                "number": 1,
                "title": "Test issue 1",
                "issue_type": "Task",
                "labels": []
            },
            "expected": "Task"
        },

        # 测试 2: 原生 issue_type 字典格式
        {
            "name": "原生 issue_type (字典)",
            "issue": {
                "number": 2,
                "title": "Test issue 2",
                "issue_type": {"name": "Bug"},
                "labels": []
            },
            "expected": "Bug"
        },

        # 测试 3: Labels 标签 - 直接格式
        {
            "name": "标签 - 直接格式",
            "issue": {
                "number": 3,
                "title": "Test issue 3",
                "labels": [{"name": "Task"}]
            },
            "expected": "Task"
        },

        # 测试 4: Labels 标签 - Type: 前缀
        {
            "name": "标签 - Type: 前缀",
            "issue": {
                "number": 4,
                "title": "Test issue 4",
                "labels": [{"name": "Type: Feature"}]
            },
            "expected": "Feature"
        },

        # 测试 5: Labels 标签 - type/ 前缀
        {
            "name": "标签 - type/ 前缀",
            "issue": {
                "number": 5,
                "title": "Test issue 5",
                "labels": [{"name": "type/bug"}]
            },
            "expected": "bug"
        },

        # 测试 6: 没有 Type 信息
        {
            "name": "无 Type 信息",
            "issue": {
                "number": 6,
                "title": "Test issue 6",
                "labels": [{"name": "good first issue"}]
            },
            "expected": ""
        },

        # 测试 7: 优先级测试 - issue_type 优先于 labels
        {
            "name": "优先级测试",
            "issue": {
                "number": 7,
                "title": "Test issue 7",
                "issue_type": "Task",
                "labels": [{"name": "Bug"}]  # 应该返回 Task 而不是 Bug
            },
            "expected": "Task"
        },
    ]

    print("=" * 60)
    print("Issue Type 检测测试")
    print("=" * 60)

    passed = 0
    failed = 0

    for test in test_issues:
        name = test["name"]
        issue = test["issue"]
        expected = test["expected"]

        result = get_issue_type(issue)

        if result == expected:
            print(f"✓ {name}: {result}")
            passed += 1
        else:
            print(f"✗ {name}: 期望 '{expected}', 得到 '{result}'")
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = test_cases()
    sys.exit(0 if success else 1)
