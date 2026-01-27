# Summary Reporter - 通用摘要报告库

## 简介

`summary_reporter.py` 是一个通用的摘要报告生成和发布工具，用于收集各组件的运行统计数据，生成格式化的 Markdown 报告，并将其自动发布到指定的 GitHub Issue。

## 功能特性

- ✅ **通用数据收集**：支持任意组件添加统计数据
- 📊 **自动格式化**：自动生成美观的 Markdown 报告
- 🚀 **自动发布**：可配置自动发布到 GitHub Issue
- 🔧 **高度可配置**：通过配置文件控制行为
- 📝 **错误追踪**：自动记录和展示运行错误
- 🎨 **详细模式**：支持简要和详细两种显示模式

## 快速开始

### 基本使用

```python
from libs.summary_reporter import SummaryReporter

# 1. 创建报告器
reporter = SummaryReporter()

# 2. 添加组件摘要数据
reporter.add_component_summary("my-component", {
    "total_items": 10,
    "processed": 8,
    "failed": 2,
})

# 3. 添加错误（可选）
reporter.add_error("Component X failed: timeout")

# 4. 发布到 GitHub Issue
if reporter.is_enabled():
    reporter.post_to_issue(token="ghp_xxx", verbose=True)
```

### 在组件中使用

```python
def my_component(verbose=False):
    """
    你的组件函数
    """
    # 初始化统计数据
    summary = {
        "total_items": 0,
        "processed": 0,
        "failed": 0,
        "processed_items": [],  # 可选：保存处理过的项目详情
    }

    # 执行业务逻辑
    items = get_items()
    summary["total_items"] = len(items)

    for item in items:
        try:
            process_item(item)
            summary["processed"] += 1
            # 可选：记录详细信息用于摘要展示
            summary["processed_items"].append({
                "id": item.id,
                "name": item.name,
                "url": item.url,
            })
        except Exception as e:
            summary["failed"] += 1
            if verbose:
                print(f"Failed to process {item}: {e}")

    # 返回摘要数据
    return summary
```

**Task Checker 示例（带优先级分类）:**

```python
def check_tasks(verbose=False):
    """
    任务检查器组件，发送超时提醒并按优先级分类
    """
    summary = {
        "total_issues": 0,
        "reminders_sent": 0,
        "reminded_issues": [],  # 发送提醒的 issues 列表
    }

    issues = get_timeout_issues()
    summary["total_issues"] = len(issues)

    for issue in issues:
        if should_send_reminder(issue):
            send_reminder(issue)
            summary["reminders_sent"] += 1
            # 记录详细信息，用于按优先级分类显示
            summary["reminded_issues"].append({
                "priority": issue.priority,  # P0, P1, P2
                "issue_number": issue.number,
                "title": issue.title,
                "url": issue.html_url,
                "hours_since_update": issue.hours_since_update,
            })

    return summary
```

### 在主程序中集成

```python
from libs.summary_reporter import SummaryReporter

def main():
    # 创建报告器
    reporter = SummaryReporter()

    # 运行组件并收集摘要
    try:
        summary = my_component(verbose=True)
        reporter.add_component_summary("my-component", summary)
    except Exception as e:
        reporter.add_error(f"my-component failed: {e}")

    # 发布摘要报告
    reporter.post_to_issue()
```

## 配置文件

配置文件位于 `src/config/summary-config.yml`：

```yaml
# 启用或禁用摘要报告
enabled: true

# 摘要报告将发布到的目标 issue URL
target_issue_url: https://github.com/owner/repo/issues/123

# 报告标题模板
title_template: "🤖 MCPP Bot 运行报告 - {date}"

# 是否在摘要中包含详细信息
include_details: true
```

### 配置项说明

- **enabled**: 全局开关，`false` 时不会发布任何摘要
- **target_issue_url**: GitHub Issue 的完整 URL
- **title_template**: 报告标题，支持 `{date}` 占位符
- **include_details**: `true` 显示详细统计，`false` 只显示关键指标

## API 文档

### SummaryReporter 类

#### 初始化

```python
reporter = SummaryReporter(config_path=None)
```

- `config_path`: 配置文件路径（可选，默认使用 `src/config/summary-config.yml`）

#### 方法

##### is_enabled()

检查摘要报告功能是否启用。

```python
if reporter.is_enabled():
    # 发布摘要
    pass
```

##### add_component_summary(component_name, summary_data)

添加组件的摘要数据。

```python
reporter.add_component_summary("join-issues", {
    "total_issues": 10,
    "completed": 8,
    "skipped": 2,
})
```

##### add_error(error_msg)

添加错误信息到摘要。

```python
reporter.add_error("Component failed: connection timeout")
```

##### generate_report(verbose=False)

生成 Markdown 格式的摘要报告。

```python
markdown_text = reporter.generate_report(verbose=True)
print(markdown_text)
```

##### post_to_issue(token=None, verbose=False)

将摘要发布到配置的 GitHub Issue。

```python
success = reporter.post_to_issue(token="ghp_xxx", verbose=True)
```

- `token`: GitHub API Token（可选，默认从环境变量 `GH_TOKEN` 读取）
- `verbose`: 是否打印详细日志
- 返回: `True` 成功，`False` 失败

##### print_console_summary()

在控制台打印简要摘要。

```python
reporter.print_console_summary()
```

## 自定义组件格式化

如果你想为新组件添加自定义的格式化逻辑，可以在 `SummaryReporter` 类中添加新的格式化方法：

```python
def _format_my_component_summary(self, summary: Dict[str, Any], include_details: bool) -> list:
    """
    格式化我的组件摘要
    """
    lines = []
    lines.append("### 🔥 我的组件 (My Component)")
    lines.append(f"- **处理项目:** {summary.get('total_items', 0)}")
    lines.append(f"- **成功:** {summary.get('processed', 0)}")

    if include_details:
        lines.append(f"- **失败:** {summary.get('failed', 0)}")

    lines.append("")
    return lines
```

然后在 `generate_report()` 方法中调用：

```python
if "my-component" in self.summaries:
    lines.extend(self._format_my_component_summary(
        self.summaries["my-component"],
        include_details
    ))
```

## 示例输出

### 详细模式 (include_details: true)

```markdown
## 🤖 MCPP Bot 运行报告 - 2026-01-27 10:30:00 UTC
**运行时间:** 2026-01-27 10:30:00 UTC

### 📋 加入请求扫描器 (Join Issues Scanner)
- **待处理请求:** 5
- **已完成并关闭:** 3 ✅
- **标题已更新:** 2
- **等待加入组织:** 1
  - 发送提醒: 1
- **已添加到团队:** 2
- **跳过:** 1

### ⏰ 任务检查器 (Task Checker)
- **扫描仓库数:** 3
- **检查的任务:** 15
- **发送提醒:** 3 📬
- **跳过:** 5

#### 发送提醒的任务

**🔴 P0 级别任务** (1 个):
- [#123](https://github.com/mcpp-community/mcpp/issues/123) Critical Bug: System crash on startup (已 48.5h 未更新)

**🟡 P1 级别任务** (2 个):
- [#130](https://github.com/mcpp-community/mcpp/issues/130) Feature request: Add support for dark mode (已 72.0h 未更新)
- [#135](https://github.com/mcpp-community/mcpp/issues/135) Performance optimization for large datasets proc... (已 80.5h 未更新)

---
*Generated by [MCPP Bot](https://github.com/mcpp-community/mcpp-bot)*
```

### 简要模式 (include_details: false)

```markdown
## 🤖 MCPP Bot 运行报告 - 2026-01-27 10:30:00 UTC
**运行时间:** 2026-01-27 10:30:00 UTC

### 📋 加入请求扫描器 (Join Issues Scanner)
- **待处理请求:** 5
- **已完成并关闭:** 3 ✅
- **等待加入组织:** 1 (已发送 1 条提醒)

### ⏰ 任务检查器 (Task Checker)
- **扫描仓库数:** 3
- **检查的任务:** 15
- **发送提醒:** 2 📬

---
*Generated by [MCPP Bot](https://github.com/mcpp-community/mcpp-bot)*
```

## 高级用法

### 自定义配置文件路径

```python
reporter = SummaryReporter(config_path="/path/to/custom-config.yml")
```

### 获取摘要数据字典

```python
data = reporter.get_summary_dict()
# 返回: {"summaries": {...}, "errors": [...], "start_time": "..."}
```

### 仅生成报告而不发布

```python
markdown_text = reporter.generate_report()
# 自己处理这个文本，比如保存到文件
with open("summary.md", "w") as f:
    f.write(markdown_text)
```

## 注意事项

1. **环境变量**: 如果不在代码中传递 token，需要设置环境变量 `GH_TOKEN`
2. **Issue URL 格式**: 必须是完整的 GitHub Issue URL，格式：`https://github.com/owner/repo/issues/123`
3. **权限要求**: GitHub Token 需要有对目标仓库的写权限（可以评论 issue）
4. **配置文件**: 确保配置文件存在且格式正确

## 故障排除

### 摘要没有发布

1. 检查 `enabled: true` 是否设置
2. 检查 `target_issue_url` 是否正确
3. 检查 `GH_TOKEN` 环境变量是否设置
4. 使用 `verbose=True` 查看详细错误信息

### Issue URL 格式错误

确保 URL 格式为：`https://github.com/owner/repo/issues/123`

不要使用：
- 短链接
- PR URL (pulls 而不是 issues)
- 其他格式

## 贡献

欢迎提交 PR 来扩展此库的功能！
