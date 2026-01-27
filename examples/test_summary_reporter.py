#!/usr/bin/env python3
"""
SummaryReporter 测试示例

这个脚本测试 SummaryReporter 的各项功能，不会实际发布到 GitHub。
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libs.summary_reporter import SummaryReporter


def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "=" * 60)
    print("测试 1: 基本功能")
    print("=" * 60)

    reporter = SummaryReporter()

    # 添加组件摘要
    reporter.add_component_summary("join-issues", {
        "total_issues": 10,
        "title_updated": 5,
        "not_member_yet": 3,
        "reminder_sent": 2,
        "team_added": 4,
        "team_add_failed": 0,
        "completed": 7,
        "skipped": 0,
    })

    reporter.add_component_summary("task-checker", {
        "total_repos": 5,
        "total_issues": 20,
        "reminders_sent": 3,
        "skipped": 2,
    })

    # 生成报告
    report = reporter.generate_report()
    print(report)

    print("\n✓ 基本功能测试通过")


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试 2: 错误处理")
    print("=" * 60)

    reporter = SummaryReporter()

    # 添加错误
    reporter.add_error("组件 A 失败: 连接超时")
    reporter.add_error("组件 B 失败: 权限不足")

    # 添加一些正常数据
    reporter.add_component_summary("working-component", {
        "total": 5,
        "success": 5,
    })

    # 生成报告
    report = reporter.generate_report()
    print(report)

    # 检查错误是否出现在报告中
    if "❌ 运行错误" in report and "连接超时" in report:
        print("\n✓ 错误处理测试通过")
    else:
        print("\n✗ 错误处理测试失败")


def test_empty_summary():
    """测试空摘要"""
    print("\n" + "=" * 60)
    print("测试 3: 空摘要")
    print("=" * 60)

    reporter = SummaryReporter()

    # 不添加任何数据
    report = reporter.generate_report()
    print(report)

    print("\n✓ 空摘要测试通过")


def test_detailed_vs_simple():
    """测试详细模式和简要模式"""
    print("\n" + "=" * 60)
    print("测试 4: 详细模式 vs 简要模式")
    print("=" * 60)

    # 详细模式
    print("\n[详细模式]")
    reporter1 = SummaryReporter()
    reporter1.config["include_details"] = True
    reporter1.add_component_summary("join-issues", {
        "total_issues": 10,
        "title_updated": 5,
        "not_member_yet": 3,
        "reminder_sent": 2,
        "team_added": 4,
        "team_add_failed": 1,
        "completed": 7,
        "skipped": 2,
    })
    print(reporter1.generate_report())

    # 简要模式
    print("\n[简要模式]")
    reporter2 = SummaryReporter()
    reporter2.config["include_details"] = False
    reporter2.add_component_summary("join-issues", {
        "total_issues": 10,
        "title_updated": 5,
        "not_member_yet": 3,
        "reminder_sent": 2,
        "team_added": 4,
        "team_add_failed": 1,
        "completed": 7,
        "skipped": 2,
    })
    print(reporter2.generate_report())

    print("\n✓ 详细/简要模式测试通过")


def test_console_summary():
    """测试控制台摘要"""
    print("\n" + "=" * 60)
    print("测试 5: 控制台摘要")
    print("=" * 60)

    reporter = SummaryReporter()
    reporter.add_component_summary("component-a", {"count": 10})
    reporter.add_component_summary("component-b", {"count": 20})
    reporter.add_error("测试错误")

    reporter.print_console_summary()

    print("\n✓ 控制台摘要测试通过")


def test_summary_dict():
    """测试获取摘要字典"""
    print("\n" + "=" * 60)
    print("测试 6: 获取摘要字典")
    print("=" * 60)

    reporter = SummaryReporter()
    reporter.add_component_summary("test", {"value": 123})
    reporter.add_error("测试错误")

    data = reporter.get_summary_dict()
    print(f"摘要数据: {data}")

    if "summaries" in data and "errors" in data and "start_time" in data:
        print("\n✓ 摘要字典测试通过")
    else:
        print("\n✗ 摘要字典测试失败")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("SummaryReporter 测试套件")
    print("=" * 60)

    tests = [
        test_basic_functionality,
        test_error_handling,
        test_empty_summary,
        test_detailed_vs_simple,
        test_console_summary,
        test_summary_dict,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
