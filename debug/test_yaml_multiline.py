#!/usr/bin/env python3
"""
测试 YAML 多行字符串解析
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libs.utils import load_simple_yaml


def test_multiline():
    """测试多行字符串解析"""
    print("测试 task-checker.yml 的多行字符串解析")
    print("=" * 60)

    config_path = Path(__file__).parent.parent / "src" / "config" / "task-checker.yml"
    config = load_simple_yaml(str(config_path))

    reminder_template = config.get("reminder_template", "")

    print(f"reminder_template 类型: {type(reminder_template)}")
    print(f"reminder_template 长度: {len(reminder_template) if isinstance(reminder_template, str) else 'N/A'}")
    print("\n内容:")
    print("-" * 60)
    print(reminder_template)
    print("-" * 60)

    if isinstance(reminder_template, str) and len(reminder_template) > 0:
        print("\n✓ 多行字符串解析成功")

        # 测试格式化
        try:
            formatted = reminder_template.format(
                assignees="@user1 @user2",
                priority="P0",
                hours=48.5,
                title="测试任务",
                timeout=72
            )
            print("\n格式化后的消息:")
            print("-" * 60)
            print(formatted)
            print("-" * 60)
            print("\n✓ 格式化成功")
        except Exception as e:
            print(f"\n✗ 格式化失败: {e}")
    else:
        print("\n✗ 多行字符串解析失败")
        print(f"  期望: 字符串")
        print(f"  实际: {type(reminder_template)}")


if __name__ == "__main__":
    test_multiline()
