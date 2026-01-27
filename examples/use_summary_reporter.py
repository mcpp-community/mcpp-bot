#!/usr/bin/env python3
"""
SummaryReporter 使用示例

这个文件展示了如何在其他组件或项目中使用通用的 SummaryReporter 库。
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libs.summary_reporter import SummaryReporter


def example_component_1(verbose=False):
    """
    示例组件1：数据处理器
    """
    if verbose:
        print("运行示例组件1：数据处理器")

    # 模拟数据处理
    summary = {
        "total_items": 100,
        "processed": 95,
        "failed": 5,
        "skipped": 0,
    }

    if verbose:
        print(f"  处理了 {summary['processed']} / {summary['total_items']} 项")

    return summary


def example_component_2(verbose=False):
    """
    示例组件2：任务调度器
    """
    if verbose:
        print("运行示例组件2：任务调度器")

    # 模拟任务调度
    summary = {
        "total_tasks": 50,
        "scheduled": 45,
        "cancelled": 3,
        "pending": 2,
    }

    if verbose:
        print(f"  调度了 {summary['scheduled']} / {summary['total_tasks']} 个任务")

    return summary


def main():
    """
    主函数：展示如何使用 SummaryReporter
    """
    print("=" * 60)
    print("SummaryReporter 使用示例")
    print("=" * 60)

    # 1. 创建 SummaryReporter 实例
    reporter = SummaryReporter()

    # 2. 运行组件并收集摘要
    print("\n运行组件...")

    # 组件1
    try:
        summary1 = example_component_1(verbose=True)
        reporter.add_component_summary("data-processor", summary1)
        print("✓ 数据处理器完成")
    except Exception as e:
        error_msg = f"数据处理器失败: {e}"
        print(f"✗ {error_msg}")
        reporter.add_error(error_msg)

    # 组件2
    try:
        summary2 = example_component_2(verbose=True)
        reporter.add_component_summary("task-scheduler", summary2)
        print("✓ 任务调度器完成")
    except Exception as e:
        error_msg = f"任务调度器失败: {e}"
        print(f"✗ {error_msg}")
        reporter.add_error(error_msg)

    # 3. 生成并打印摘要报告
    print("\n" + "=" * 60)
    print("生成摘要报告")
    print("=" * 60)

    summary_text = reporter.generate_report(verbose=True)
    print("\n" + summary_text)

    # 4. （可选）发布到 GitHub Issue
    # 注意：需要在配置文件中设置 enabled: true 和 target_issue_url
    print("\n" + "=" * 60)
    print("发布摘要到 GitHub Issue")
    print("=" * 60)

    if reporter.is_enabled():
        print("摘要报告功能已启用，尝试发布...")
        # reporter.post_to_issue(verbose=True)
        print("（示例代码：实际发布已注释）")
    else:
        print("摘要报告功能未启用（在配置文件中设置 enabled: true 以启用）")

    # 5. 在控制台打印简要摘要
    reporter.print_console_summary()

    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
