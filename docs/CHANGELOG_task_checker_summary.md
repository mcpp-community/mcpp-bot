# Task Checker 摘要功能增强

## 概述

为 Task Checker 组件增加了按优先级分类显示提醒 issues 的功能。现在摘要报告不仅显示统计数字，还会列出所有发送提醒的 issues，并按照 P0/P1/P2 优先级进行分类展示。

## 主要改动

### 1. `task_checker.py` - 数据收集

**改动内容:**
- `check_task_timeout()` 现在返回包含详细信息的字典，而不是简单的 True/False
- 返回数据包括：优先级、issue 编号、标题、URL、距上次更新时间
- `scan_repo_tasks()` 和 `scan_org_tasks()` 的摘要中新增 `reminded_issues` 字段

**返回数据格式:**
```python
{
    "total_issues": 25,
    "reminders_sent": 7,
    "skipped": 5,
    "reminded_issues": [
        {
            "priority": "P0",
            "issue_number": 123,
            "title": "Critical Bug: System crash on startup",
            "url": "https://github.com/mcpp-community/mcpp/issues/123",
            "hours_since_update": 48.5,
        },
        # ... more issues
    ]
}
```

### 2. `summary_reporter.py` - 格式化展示

**改动内容:**
- 增强 `_format_task_checker_summary()` 方法
- 自动按优先级（P0/P1/P2）分组显示
- 为不同优先级添加彩色图标：
  - 🔴 P0 (最高优先级)
  - 🟡 P1 (重要)
  - 🟢 P2 (一般)
- 显示每个 issue 的链接、标题和距上次更新时间
- 自动截断过长的标题（超过 60 字符）

## 功能展示

### 摘要报告示例

```markdown
### ⏰ 任务检查器 (Task Checker)
- **扫描仓库数:** 3
- **检查的任务:** 25
- **发送提醒:** 7 📬
- **跳过:** 5

#### 发送提醒的任务

**🔴 P0 级别任务** (2 个):
- [#123](https://github.com/mcpp-community/mcpp/issues/123) Critical Bug: System crash on startup (已 48.5h 未更新)
- [#125](https://github.com/mcpp-community/mcpp/issues/125) Security vulnerability in authentication module (已 36.2h 未更新)

**🟡 P1 级别任务** (3 个):
- [#130](https://github.com/mcpp-community/mcpp/issues/130) Feature request: Add support for dark mode (已 72.0h 未更新)
- [#135](https://github.com/mcpp-community/mcpp/issues/135) Performance optimization for large datasets processing (已 80.5h 未更新)
- [#140](https://github.com/mcpp-community/mcpp/issues/140) Improve error messages to be more user-friendly and provi... (已 65.3h 未更新)

**🟢 P2 级别任务** (2 个):
- [#150](https://github.com/mcpp-community/mcpp/issues/150) Update documentation for new features (已 120.0h 未更新)
- [#155](https://github.com/mcpp-community/mcpp/issues/155) Refactor legacy code in utils module (已 96.7h 未更新)
```

### 在 GitHub Issue 中的效果

在 GitHub Issue 评论中，上述 Markdown 会被渲染为：

- ✅ 自动生成的 issue 链接可点击
- ✅ 按优先级分类，一目了然
- ✅ 彩色图标直观标识优先级
- ✅ 显示距上次更新时间，便于评估紧急程度
- ✅ 长标题自动截断，保持版面整洁

## 使用方法

### 运行 Task Checker

```bash
# 运行 task checker 并生成摘要
python src/main.py task-checker --verbose

# 运行所有组件（包括自动发布摘要）
python src/main.py all
```

### 测试功能

```bash
# 运行专门的测试脚本
python examples/test_task_checker_summary.py
```

## 技术细节

### 优先级识别

通过配置文件中的 `priority_pattern` 识别优先级标签：
```yaml
priority_pattern: "^P([012])$"  # 匹配 P0, P1, P2
```

### 数据流

```
task_checker.py
    └─> 扫描 issues
    └─> 检查超时
    └─> 发送提醒
    └─> 收集详细信息 (priority, issue_number, title, url, hours)
    └─> 返回 summary with reminded_issues[]

main.py
    └─> 接收 summary
    └─> 传递给 SummaryReporter

summary_reporter.py
    └─> 按优先级分组 reminded_issues
    └─> 格式化为 Markdown
    └─> 发布到 GitHub Issue
```

## 优势

1. **透明度提升**: 用户可以直接看到哪些任务被提醒了
2. **优先级明确**: 通过颜色和分组一眼识别优先级
3. **快速访问**: 直接点击链接跳转到相关 issue
4. **上下文信息**: 显示距上次更新时间，帮助判断紧急程度
5. **可追溯**: 每次运行的详细记录，便于审计和分析

## 向后兼容性

- ✅ 完全向后兼容
- ✅ 如果组件不返回 `reminded_issues`，仍能正常工作
- ✅ 旧的摘要报告格式仍然支持
- ✅ 不影响其他组件的功能

## 测试覆盖

- ✅ 有提醒 issues 的情况
- ✅ 无提醒 issues 的情况
- ✅ 多优先级混合的情况
- ✅ 长标题自动截断
- ✅ 多组件混合摘要
- ✅ 详细模式和简要模式

## 未来扩展

可以考虑的增强：
- [ ] 添加 assignees 信息显示
- [ ] 显示 issue 创建时间
- [ ] 支持自定义优先级图标
- [ ] 支持更多优先级级别（P3, P4...）
- [ ] 添加过滤选项（只显示特定优先级）

## 相关文件

- `src/components/task_checker.py` - Task Checker 核心逻辑
- `src/libs/summary_reporter.py` - 通用摘要报告库
- `src/config/summary-config.yml` - 摘要配置文件
- `examples/test_task_checker_summary.py` - 测试脚本
- `src/libs/README_summary_reporter.md` - 详细文档
