#!/usr/bin/env python3
"""
Task Checker 摘要功能测试

这个脚本演示 task checker 按优先级分类显示提醒 issues 的功能。
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libs.summary_reporter import SummaryReporter


def test_task_checker_with_issues():
    """测试带有具体 issues 的任务检查器摘要"""
    print("=" * 60)
    print("Task Checker 摘要功能测试")
    print("=" * 60)

    reporter = SummaryReporter()

    # 模拟 task checker 返回的摘要数据
    task_summary = {
        "total_repos": 3,
        "total_issues": 25,
        "reminders_sent": 7,
        "skipped": 5,
        "reminded_issues": [
            # P0 级别的紧急任务
            {
                "priority": "P0",
                "issue_number": 123,
                "title": "Critical Bug: System crash on startup",
                "url": "https://github.com/mcpp-community/mcpp/issues/123",
                "hours_since_update": 48.5,
            },
            {
                "priority": "P0",
                "issue_number": 125,
                "title": "Security vulnerability in authentication module",
                "url": "https://github.com/mcpp-community/mcpp/issues/125",
                "hours_since_update": 36.2,
            },
            # P1 级别的重要任务
            {
                "priority": "P1",
                "issue_number": 130,
                "title": "Feature request: Add support for dark mode",
                "url": "https://github.com/mcpp-community/mcpp/issues/130",
                "hours_since_update": 72.0,
            },
            {
                "priority": "P1",
                "issue_number": 135,
                "title": "Performance optimization for large datasets processing",
                "url": "https://github.com/mcpp-community/mcpp/issues/135",
                "hours_since_update": 80.5,
            },
            {
                "priority": "P1",
                "issue_number": 140,
                "title": "Improve error messages to be more user-friendly and provide actionable suggestions",
                "url": "https://github.com/mcpp-community/mcpp/issues/140",
                "hours_since_update": 65.3,
            },
            # P2 级别的一般任务
            {
                "priority": "P2",
                "issue_number": 150,
                "title": "Update documentation for new features",
                "url": "https://github.com/mcpp-community/mcpp/issues/150",
                "hours_since_update": 120.0,
            },
            {
                "priority": "P2",
                "issue_number": 155,
                "title": "Refactor legacy code in utils module",
                "url": "https://github.com/mcpp-community/mcpp/issues/155",
                "hours_since_update": 96.7,
            },
        ],
    }

    # 添加到报告器
    reporter.add_component_summary("task-checker", task_summary)

    # 生成并打印报告
    print("\n详细模式摘要:")
    print("=" * 60)
    reporter.config["include_details"] = True
    detailed_report = reporter.generate_report()
    print(detailed_report)

    print("\n" + "=" * 60)
    print("\n简要模式摘要:")
    print("=" * 60)
    reporter.config["include_details"] = False
    simple_report = reporter.generate_report()
    print(simple_report)


def test_empty_task_checker():
    """测试没有发送提醒的情况"""
    print("\n" + "=" * 60)
    print("测试无提醒情况")
    print("=" * 60)

    reporter = SummaryReporter()

    # 没有发送任何提醒
    task_summary = {
        "total_repos": 2,
        "total_issues": 10,
        "reminders_sent": 0,
        "skipped": 3,
        "reminded_issues": [],
    }

    reporter.add_component_summary("task-checker", task_summary)

    report = reporter.generate_report()
    print(report)


def test_mixed_components():
    """测试同时包含多个组件的摘要"""
    print("\n" + "=" * 60)
    print("测试多组件混合摘要")
    print("=" * 60)

    reporter = SummaryReporter()

    # Join Issues Scanner
    reporter.add_component_summary("join-issues", {
        "total_issues": 5,
        "title_updated": 3,
        "not_member_yet": 2,
        "reminder_sent": 1,
        "team_added": 2,
        "team_add_failed": 0,
        "completed": 3,
        "skipped": 0,
    })

    # Task Checker with P0/P1 issues
    reporter.add_component_summary("task-checker", {
        "total_repos": 1,
        "total_issues": 15,
        "reminders_sent": 3,
        "skipped": 2,
        "reminded_issues": [
            {
                "priority": "P0",
                "issue_number": 100,
                "title": "Critical: Database connection timeout",
                "url": "https://github.com/mcpp-community/openorg/issues/100",
                "hours_since_update": 50.0,
            },
            {
                "priority": "P1",
                "issue_number": 101,
                "title": "Memory leak in long-running process",
                "url": "https://github.com/mcpp-community/openorg/issues/101",
                "hours_since_update": 75.0,
            },
            {
                "priority": "P1",
                "issue_number": 102,
                "title": "API response time degradation",
                "url": "https://github.com/mcpp-community/openorg/issues/102",
                "hours_since_update": 68.5,
            },
        ],
    })

    report = reporter.generate_report()
    print(report)


def main():
    """运行所有测试"""
    test_task_checker_with_issues()
    test_empty_task_checker()
    test_mixed_components()

    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
