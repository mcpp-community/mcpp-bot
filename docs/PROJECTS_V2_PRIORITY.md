# GitHub Projects V2 优先级字段详解

## 概述

在 GitHub ProjectV2（新版项目看板）中，"Priority"（优先级）**不是核心字段**，而是一个**自定义字段（Custom Field）**。

## 核心字段 vs 自定义字段

### GitHub Issues 的核心字段（系统级）
以下字段是 GitHub Issues 的核心字段，可以直接通过 REST API 获取：

- Title (标题)
- Assignees (负责人)
- Labels (标签)
- Milestone (里程碑)
- Repository (所属仓库)
- State (状态: open/closed)
- Type (类型: null, Task, Bug, Feature) - 新功能

### Projects V2 的核心字段

- **Status（状态）**: 每个 ProjectV2 必须包含且无法删除，用于驱动看板的列

### 自定义字段（Custom Fields）

- **Priority（优先级）**: 虽然常见，但仍然是自定义字段
- 其他任意自定义字段（如 "Effort", "Team", "Quarter" 等）

## Priority 字段的特点

### 1. 为什么你的项目里有 "Priority"？

Priority 字段通常出现在你的项目中是因为：

#### 方式 A: 使用了官方模板
如果你在创建 Project 时选择了以下模板，GitHub 会自动创建 Priority 字段：
- "Feature tracking"（功能跟踪）
- "Team planning"（团队规划）
- "Backlog"（待办事项）

#### 方式 B: 手动创建
项目管理员手动添加了名为 "Priority" 的 Single Select 字段。

### 2. 关键特性

- **非标准化**: 不同项目的 Priority 字段可能有不同的：
  - 字段 ID
  - 选项值（P0/P1/P2 vs High/Medium/Low）
  - 选项数量（有些是 3 级，有些是 5 级）

- **可修改**: 你可以：
  - 重命名字段（Priority → P-Level）
  - 修改选项值（P0 → Critical）
  - 更改字段类型（Single Select → Number）
  - 完全删除该字段

- **跨项目独立**: 同一个 issue 在不同 Projects 中可以有不同的 Priority 值

## API 访问方式

### REST API - ❌ 无法获取

```bash
# REST API 不返回 projectItems 字段
GET /repos/{owner}/{repo}/issues/{number}
```

返回的数据**不包含** Projects 字段信息。

### GraphQL API - ✅ 可以获取

```graphql
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      number
      title
      projectItems(first: 10) {
        nodes {
          project {
            title
          }
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                field {
                  ... on ProjectV2FieldCommon {
                    name      # "Priority"
                  }
                }
                name          # "P0", "P1", "P2" 等
              }
            }
          }
        }
      }
    }
  }
}
```

## MCPP Bot 的实现

### 优先级检测顺序

Bot 按以下顺序检测优先级：

1. **Labels** (最快，无额外 API 调用)
   - 检查 issue 是否有 `P0`, `P1`, `P2` 标签
   - 或 `Type: P0` 格式
   - 或 `type/p0` 格式

2. **Projects GraphQL** (需要额外 API 调用)
   - 为每个 issue 调用 GraphQL API
   - 从 Projects 字段中提取 Priority

### 支持的 Priority 格式

Bot 自动识别以下所有格式：

| 格式 | 示例 | 映射结果 |
|------|------|----------|
| 标准 | P0, P1, P2 | P0, P1, P2 |
| 带图标 | 🔴 P0, 🟡 P1, 🟢 P2 | P0, P1, P2 |
| 英文描述 | High, Medium, Low | P0, P1, P2 |
| 英文详细 | Critical, Important, Normal | P0, P1, P2 |
| 中文 | 高, 中, 低 | P0, P1, P2 |
| 中文描述 | 紧急, 重要, 一般 | P0, P1, P2 |

### 配置选项

在 `config/task-checker.yml` 中：

```yaml
# 是否使用 GraphQL API 获取 Projects 字段数据
use_graphql_for_projects: true

# 优先级标签匹配模式（用于 Labels 方式）
priority_pattern: "^P([012])$"

# 需要检查的优先级
priorities_to_check: ["P0", "P1", "P2"]
```

## 性能考虑

### API 调用次数

**不启用 GraphQL**:
- 1 次 REST API Search 调用

**启用 GraphQL**:
- 1 次 REST API Search
- N 次 GraphQL 调用（N = issue 数量）

### GitHub API 限制

- **认证用户**: 5000 次/小时
- **未认证**: 60 次/小时

### 示例计算

假设组织有 100 个打开的 Task issues：

- **仅 REST API**: 1 次调用
- **REST + GraphQL**: 1 + 100 = 101 次调用

如果每小时运行一次：
- 每天消耗: 101 × 24 = 2,424 次
- 距离限制还有: 5000 - 2424 = 2,576 次余量 ✅

## 最佳实践

### 推荐方案 A: 混合使用（默认）

```yaml
use_graphql_for_projects: true
```

- 优先使用 Labels（快速）
- 如果没有 Label，使用 GraphQL 获取 Projects（准确）
- 适合大多数场景

### 推荐方案 B: 仅使用 Labels

```yaml
use_graphql_for_projects: false
```

- 只检查 Labels，不调用 GraphQL
- 性能最优，API 调用最少
- 需要为所有 Task issues 添加 P0/P1/P2 标签
- 适合 issues 非常多的场景

### 推荐方案 C: 自动化标签同步

使用 GitHub Actions 自动将 Projects Priority 同步为 Labels：

```yaml
# .github/workflows/sync-priority-labels.yml
name: Sync Priority Labels
on:
  issues:
    types: [opened, edited]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Sync priority from project to label
        # 自定义脚本：读取 Projects Priority → 添加对应 Label
```

## 故障排除

### 问题：GraphQL 返回优先级为空

**可能原因：**
1. Issue 没有添加到任何 Project
2. Project 中没有设置 Priority 字段
3. Priority 字段的值为空
4. Priority 字段名称不是 "Priority"（比如改名为 "P-Level"）

**解决方案：**
```bash
# 运行调试脚本
python debug/test_graphql_priority.py
```

### 问题：API 调用次数过多

**解决方案：**
1. 设置 `use_graphql_for_projects: false`
2. 使用 Labels 方式
3. 减少扫描频率
4. 添加 `exclude_repos` 排除不需要扫描的仓库

### 问题：Priority 格式不被识别

**解决方案：**
在 `src/libs/github_graphql.py` 的 `PRIORITY_MAPPING` 中添加你的格式：

```python
PRIORITY_MAPPING = {
    # 添加你的自定义格式
    "⭐⭐⭐": "0",  # 三星 = P0
    "⭐⭐": "1",    # 两星 = P1
    "⭐": "2",      # 一星 = P2
}
```

## 参考资料

- [GitHub Projects V2 Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [GitHub GraphQL API - Projects V2](https://docs.github.com/en/graphql/reference/objects#projectv2)
- [Custom Fields in Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields)
