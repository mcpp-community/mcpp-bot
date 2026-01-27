#!/usr/bin/env python3
"""
Task Checker 跳过统计功能测试

演示新增的详细跳过原因统计功能。
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libs.summary_reporter import SummaryReporter


def test_detailed_skip_stats():
    """测试详细的跳过统计"""
    print("=" * 60)
    print("测试详细跳过统计")
    print("=" * 60)

    reporter = SummaryReporter()

    # 模拟扫描了多个仓库，有各种跳过情况
    task_summary = {
        "total_repos": 9,
        "total_issues": 50,  # 找到 50 个有 Task 标签的 issue
        "checked_issues": 15,  # 其中 15 个有优先级并被检查
        "reminders_sent": 3,  # 发送了 3 个提醒

        # 跳过原因统计
        "skipped_no_priority": 30,  # 30 个没有设置优先级
        "skipped_not_in_filter": 2,  # 2 个优先级不在检查范围（比如 P3）
        "skipped_no_timeout_config": 0,  # 0 个优先级未配置超时
        "skipped_not_timeout": 12,  # 12 个未超时

        # 发送提醒的 issues
        "reminded_issues": [
            {
                "priority": "P0",
                "issue_number": 101,
                "title": "Critical: Production server down",
                "url": "https://github.com/mcpp-community/repo1/issues/101",
                "hours_since_update": 30.5,
            },
            {
                "priority": "P1",
                "issue_number": 202,
                "title": "Bug: Memory leak in data processor",
                "url": "https://github.com/mcpp-community/repo2/issues/202",
                "hours_since_update": 55.2,
            },
            {
                "priority": "P1",
                "issue_number": 303,
                "title": "Feature: Add export functionality",
                "url": "https://github.com/mcpp-community/repo3/issues/303",
                "hours_since_update": 80.0,
            },
        ],
    }

    reporter.add_component_summary("task-checker", task_summary)

    # 详细模式
    print("\n详细模式摘要:")
    print("=" * 60)
    reporter.config["include_details"] = True
    print(reporter.generate_report())

    # 简要模式
    print("\n简要模式摘要:")
    print("=" * 60)
    reporter.config["include_details"] = False
    print(reporter.generate_report())


def test_no_priority_issues():
    """测试所有 issue 都没有优先级的情况"""
    print("\n" + "=" * 60)
    print("测试所有 issue 都没有优先级")
    print("=" * 60)

    reporter = SummaryReporter()

    # 这就是用户遇到的情况
    task_summary = {
        "total_repos": 9,
        "total_issues": 50,  # 有 50 个 Task issue
        "checked_issues": 0,  # 但没有一个有优先级
        "reminders_sent": 0,

        # 全部跳过，原因是没有设置优先级
        "skipped_no_priority": 50,
        "skipped_not_in_filter": 0,
        "skipped_no_timeout_config": 0,
        "skipped_not_timeout": 0,

        "reminded_issues": [],
    }

    reporter.add_component_summary("task-checker", task_summary)
    reporter.config["include_details"] = True

    print(reporter.generate_report())

    print("\n💡 解决方案:")
    print("  1. 为 issues 添加 P0/P1/P2 标签")
    print("  2. 或者在 GitHub Projects 中设置 Priority 字段")
    print("  3. 参考文档: docs/task_checker_priority_setup.md")


def test_mixed_skip_reasons():
    """测试各种跳过原因混合的情况"""
    print("\n" + "=" * 60)
    print("测试混合跳过原因")
    print("=" * 60)

    reporter = SummaryReporter()

    task_summary = {
        "total_repos": 5,
        "total_issues": 100,
        "checked_issues": 40,  # 40 个有优先级的被检查
        "reminders_sent": 8,

        # 各种跳过原因
        "skipped_no_priority": 55,  # 55 个没设置优先级
        "skipped_not_in_filter": 5,  # 5 个优先级不在范围（比如 P3）
        "skipped_no_timeout_config": 0,  # 0 个未配置超时
        "skipped_not_timeout": 32,  # 32 个未超时（正常）

        "reminded_issues": [
            {
                "priority": "P0",
                "issue_number": 1,
                "title": "P0 issue 1",
                "url": "https://github.com/org/repo/issues/1",
                "hours_since_update": 25.0,
            },
            {
                "priority": "P0",
                "issue_number": 2,
                "title": "P0 issue 2",
                "url": "https://github.com/org/repo/issues/2",
                "hours_since_update": 26.0,
            },
            {
                "priority": "P1",
                "issue_number": 10,
                "title": "P1 issue 1",
                "url": "https://github.com/org/repo/issues/10",
                "hours_since_update": 50.0,
            },
            {
                "priority": "P1",
                "issue_number": 11,
                "title": "P1 issue 2",
                "url": "https://github.com/org/repo/issues/11",
                "hours_since_update": 55.0,
            },
            {
                "priority": "P1",
                "issue_number": 12,
                "title": "P1 issue 3",
                "url": "https://github.com/org/repo/issues/12",
                "hours_since_update": 60.0,
            },
            {
                "priority": "P2",
                "issue_number": 20,
                "title": "P2 issue 1",
                "url": "https://github.com/org/repo/issues/20",
                "hours_since_update": 125.0,
            },
            {
                "priority": "P2",
                "issue_number": 21,
                "title": "P2 issue 2",
                "url": "https://github.com/org/repo/issues/21",
                "hours_since_update": 130.0,
            },
            {
                "priority": "P2",
                "issue_number": 22,
                "title": "P2 issue 3",
                "url": "https://github.com/org/repo/issues/22",
                "hours_since_update": 140.0,
            },
        ],
    }

    reporter.add_component_summary("task-checker", task_summary)
    reporter.config["include_details"] = True

    print(reporter.generate_report())

    print("\n📊 数据分析:")
    print(f"  总共 100 个 Task issues")
    print(f"  - 40 个有优先级，被检查")
    print(f"  - 55 个没有优先级，跳过")
    print(f"  - 5 个优先级不在检查范围（P3或其他），跳过")
    print(f"  在 40 个被检查的 issues 中:")
    print(f"  - 8 个超时，发送了提醒")
    print(f"  - 32 个未超时，等待下次检查")


def main():
    """运行所有测试"""
    test_detailed_skip_stats()
    test_no_priority_issues()
    test_mixed_skip_reasons()

    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
