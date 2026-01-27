# Task Checker 优先级设置指南

## 概述

Task Checker 支持两种方式识别 Issue 的优先级：

1. **GitHub Labels（标签）** - 简单直接
2. **GitHub Projects V2 字段** - 功能强大但需要额外配置

## 方法 1: 使用 Labels（推荐用于简单场景）

### 设置步骤

1. **创建优先级标签**

   在仓库中创建以下标签：
   - `P0` - 最高优先级（紧急）
   - `P1` - 重要优先级
   - `P2` - 一般优先级

2. **给 Issue 添加标签**

   为需要检查的 Task Issue 添加对应的优先级标签。

3. **配置文件**

   在 `config/task-checker.yml` 中配置：
   ```yaml
   priority_pattern: "^P([012])$"  # 匹配 P0, P1, P2 标签
   ```

### 优点
- ✅ 简单直接，易于设置
- ✅ 无需额外 API 权限
- ✅ 在 Issue 列表中可见

### 缺点
- ❌ 标签会显示在 Issue 上，可能造成视觉混乱
- ❌ 无法使用 Projects 的高级功能（看板、视图等）

## 方法 2: 使用 GitHub Projects V2 字段

### 设置步骤

1. **创建 GitHub Project**

   - 进入组织或仓库
   - 创建一个新的 Project (Projects V2)

2. **添加优先级字段**

   在 Project 中添加一个 **Single Select** 类型的自定义字段：
   - 字段名称：`Priority` 或 `优先级`
   - 选项值：
     - `P0` - 紧急
     - `P1` - 重要
     - `P2` - 一般

3. **添加 Issues 到 Project**

   - 将需要检查的 Task Issues 添加到 Project
   - 为每个 Issue 设置优先级字段

4. **配置 GitHub Token 权限**

   **重要：** 使用 Projects V2 需要特殊的 API 权限。

   目前 GitHub 的 REST API Search 不返回 Projects V2 数据，需要使用 **GraphQL API**。

### 当前限制

⚠️ **注意：** 当前版本的 `get_priority_from_project()` 函数期望 Issue 对象包含 `projectItems` 字段，但标准的 REST API Search 不会返回这个字段。

要使用 Project 字段功能，需要：

#### 选项 A: 使用 GraphQL API（需要代码修改）

修改 `search_issues()` 函数使用 GraphQL API 查询：

```graphql
query {
  search(query: "repo:owner/name is:issue is:open label:Task", type: ISSUE, first: 100) {
    nodes {
      ... on Issue {
        number
        title
        url
        updatedAt
        projectItems(first: 10) {
          nodes {
            fieldValues(first: 20) {
              nodes {
                ... on ProjectV2ItemFieldSingleSelectValue {
                  field {
                    ... on ProjectV2FieldCommon {
                      name
                    }
                  }
                  name
                }
              }
            }
          }
        }
      }
    }
  }
}
```

#### 选项 B: 暂时使用 Labels

在 Projects V2 完全支持之前，建议使用 **Labels** 方式设置优先级。

## 混合使用

Bot 会自动尝试两种方式：
1. 首先检查 Labels
2. 如果没有找到，尝试检查 Project 字段

这样可以同时支持两种方式，灵活使用。

## 检查优先级设置是否生效

### 运行 verbose 模式

```bash
python src/main.py task-checker --verbose
```

### 查看输出

```
找到 15 个 Task 标签的 Issue

检查 Issue #123: 修复登录问题
  ⊘ 跳过: 未设置优先级（无标签或Project字段)

检查 Issue #124: 性能优化
  优先级: P1, 超时阈值: 48h, 距上次更新: 50.2h
  ✓ 发送超时提醒
```

### 查看摘要报告

摘要会显示详细的统计信息：

```markdown
### ⏰ 任务检查器 (Task Checker)
- **问题总数 (Task标签):** 15
- **检查的问题 (有优先级):** 10
- **发送提醒:** 3 📬
- **跳过的问题:** 5
  - 未设置优先级 (无Project/标签): 5
```

**解读：**
- 找到 15 个有 Task 标签的 Issue
- 其中 10 个设置了优先级（通过 Label 或 Project）
- 5 个没有设置优先级，被跳过

## 故障排除

### 问题：检查的问题为 0

**原因：** 所有 Issue 都没有设置优先级。

**解决方案：**
1. 检查是否创建了 P0/P1/P2 标签
2. 检查 Issue 是否添加了这些标签
3. 如果使用 Projects，确认：
   - Issue 已添加到 Project
   - Priority 字段已设置
   - API 返回了 `projectItems` 数据（当前可能不支持）

### 问题：使用 Project 但优先级识别失败

**原因：** REST API Search 不返回 Projects V2 数据。

**解决方案：**
1. 临时使用 Labels 方式
2. 等待代码更新支持 GraphQL API
3. 或者自行修改代码使用 GraphQL

### 问题：部分 Issue 被跳过

查看 verbose 输出和摘要报告的详细统计：
- **未设置优先级**: 没有 Label 也没有 Project 字段
- **优先级不在检查范围**: 比如设置了 P3，但配置只检查 P0/P1/P2
- **未配置超时**: 比如设置了 P1，但配置文件中没有 P1 的 `timeout_hours`
- **未超时**: 有优先级且距上次更新时间未超过阈值

## 推荐配置

### 简单场景（小团队/少量仓库）

使用 **Labels** 方式：

```yaml
# config/task-checker.yml
task_label: Task
priority_pattern: "^P([012])$"

priorities_to_check:
  - P0
  - P1
  - P2

timeout_hours:
  P0: 24   # 24小时
  P1: 48   # 48小时
  P2: 120  # 5天
```

### 复杂场景（大团队/多仓库）

未来支持 Projects V2 后：

```yaml
# config/task-checker.yml
task_label: Task
use_project_priority: true  # 优先使用 Project 字段
priority_pattern: "^P([012])$"  # 作为备用

priorities_to_check:
  - P0
  - P1
  - P2

timeout_hours:
  P0: 12   # 12小时（紧急）
  P1: 48   # 48小时（重要）
  P2: 168  # 7天（一般）
```

## 相关配置

### task-checker.yml 完整示例

```yaml
# 扫描模式: "repo" 或 "org"
scan_mode: org

# 组织名称（scan_mode=org 时使用）
org: mcpp-community

# 仓库名称（scan_mode=repo 时使用）
# repo: mcpp-community/mcpp-bot

# 任务标签
task_label: Task

# 优先级标签匹配模式
priority_pattern: "^P([012])$"

# 需要检查的优先级
priorities_to_check:
  - P0
  - P1
  - P2

# 超时时间配置（小时）
timeout_hours:
  P0: 24   # 24小时
  P1: 48   # 48小时
  P2: 120  # 5天

# 排除的仓库（可选）
exclude_repos:
  - mcpp-community/archived-repo
  - test-repo

# 提醒消息模板（可选）
reminder_template: |
  ⏰ **任务提醒**

  {assignees} 这个 {priority} 优先级的任务已经 {hours:.1f} 小时没有更新了。

  请及时更新进度或状态。

  **Issue:** {title}
  **超时阈值:** {timeout} 小时

# 是否提醒未分配的任务（可选）
notify_unassigned: false

# 未分配任务的默认提及（可选）
default_mention: "@team"
```

## 总结

- ✅ **现在推荐**：使用 Labels (P0, P1, P2) 方式
- 🚧 **未来支持**：GitHub Projects V2 字段（需要 GraphQL API）
- 📊 **新增功能**：详细的跳过原因统计
- 🔍 **调试工具**：verbose 模式显示每个 issue 的处理过程
