# Issue Type 识别指南

## 问题说明

GitHub Issues 本身没有原生的 "Type" 字段。Type 信息通常通过以下方式存储：

1. **Labels（标签）** - 最常见的方式
2. **GitHub Projects V2 字段** - 需要将 issue 添加到 Project
3. **Issue Templates** - 通过模板设置，但不会存储在 issue 对象中

## 当前实现

Bot 的 `get_issue_type()` 函数会尝试从以下位置读取 Type：

### 1. 直接字段（优先级最高）
```python
issue.get("type")  # 检查是否有直接的 type 字段
```

### 2. Labels 标签（主要方式）
支持以下标签格式：
- 直接标签：`Task`, `Bug`, `Feature`
- 前缀格式：`Type: Task`, `Type: Bug`, `Type: Feature`
- 斜杠格式：`type/task`, `type/bug`, `type/feature`

### 3. Projects V2 字段（未来支持）
需要 GraphQL API 支持。

## 调试方法

### 运行调试脚本

```bash
export GH_TOKEN=your_github_token
python debug/inspect_issue_structure.py
```

这个脚本会：
1. 搜索你的组织的 issues
2. 显示 issue 对象的完整结构
3. 列出所有使用的标签
4. 识别可能的 Type 标签

### 分析输出

检查输出中的 "Labels" 部分，看看你的仓库使用的是哪种标签格式：

```
Labels:
  - Task
  - P1
  - good first issue
```

或

```
Labels:
  - Type: Task
  - Priority: P1
  - good first issue
```

## 配置建议

### 方案 A: 使用直接标签（推荐）

创建以下标签：
- `Task`
- `Bug`
- `Feature`

配置文件：
```yaml
task_type: Task
```

### 方案 B: 使用前缀标签

创建以下标签：
- `Type: Task`
- `Type: Bug`
- `Type: Feature`

`get_issue_type()` 会自动识别并提取 "Task" 部分。

### 方案 C: 使用 label 过滤（临时方案）

如果你的仓库已经有一个用于标识任务的标签（比如 "task"、"需求" 等），可以临时使用 label 过滤：

```yaml
task_type: ""  # 不使用 Type 过滤
task_label: "task"  # 使用此 label 过滤
```

## 当前问题排查

如果你看到：
```
- 问题总数 (所有打开的): 50
- Task 类型问题: 0
- 检查的问题 (有优先级): 0
```

这表示：
1. 找到了 50 个打开的 issues
2. 但没有一个 issue 的 Type 是 "Task"

**可能的原因：**
- Issues 没有 `Task` 标签
- 使用了其他标签格式（如 `type/task`, `Type: Task`）
- Type 信息存储在 Projects 字段中（当前不支持）

**解决方案：**
1. 运行调试脚本查看实际的标签格式
2. 根据实际情况调整 `get_issue_type()` 函数
3. 或者为 issues 添加正确的标签

## 扩展 get_issue_type() 函数

如果你的仓库使用其他标签格式，可以修改 `src/libs/github_client.py` 中的 `get_issue_type()` 函数：

```python
def get_issue_type(issue):
    # ... 现有代码 ...

    # 添加自定义标签格式
    for label in issue.get("labels", []):
        label_name = label.get("name", "")

        # 示例：识别中文标签
        if label_name == "任务":
            return "Task"
        if label_name == "缺陷":
            return "Bug"
        if label_name == "功能":
            return "Feature"

        # 示例：识别表情符号标签
        if label_name == "✨ feature":
            return "Feature"
        if label_name == "🐛 bug":
            return "Bug"
        if label_name == "📋 task":
            return "Task"

    return ""
```

## 最佳实践

1. **统一标签格式**: 在组织内统一使用同一种标签格式
2. **使用标签模板**: 在 `.github/labels.yml` 中定义标准标签
3. **Issue 模板**: 在 issue 模板中自动添加 Type 标签
4. **文档化**: 在仓库的 CONTRIBUTING.md 中说明标签规范

## 示例：创建标准标签

在仓库中创建 `.github/labels.yml`:

```yaml
- name: "Task"
  color: "0E8A16"
  description: "工作任务"

- name: "Bug"
  color: "D73A4A"
  description: "错误或缺陷"

- name: "Feature"
  color: "A2EEEF"
  description: "新功能请求"
```

然后使用 GitHub CLI 应用：

```bash
gh label sync --force
```
