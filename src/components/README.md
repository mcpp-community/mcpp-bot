# Components

This directory contains various bot components for managing GitHub repositories and organizations.

## Available Components

### 1. scan_join_issues.py

Scans and processes join request issues for organization membership.

**Usage:**
```bash
export GH_TOKEN="your_github_token"
python src/components/scan_join_issues.py
```

**Configuration:** `config/join-config.yml`

**Approval Mode:**
- When a team is configured with `mode: approval`, the user will only be added after approvals are found.
- Approvals are detected from issue comments that contain approval keywords, or an optional approval label.
- `reviewers.users`: All specified users must approve.
- `reviewers.teams`: Each team requires approval from at least one member.

Example:
```yaml
teams:
  vteam:
    mode: approval
    team_slug: vteam
    reviewers:
      users: ["sunrisepeak"]
      teams: ["coreteam"]
    approval_keywords: ["/approve", "approve", "lgtm"]
    approval_label: "approved"
```

### 2. task_checker.py

Scans for task issues with priority labels (P0/P1/P2) and sends reminders if they haven't been updated within configured timeouts.

**Usage:**
```bash
export GH_TOKEN="your_github_token"
python src/components/task_checker.py
```

**Configuration:** `config/task-checker.yml`

**Features:**
- Flexible scan modes: single repository or entire organization
- Customizable timeout thresholds for P0/P1/P2 priorities
- Customizable reminder message template
- Repository exclusion support
- Optional reminders for unassigned tasks

**Configuration Options:**

- `scan_mode`: Set to `"repo"` for single repository or `"org"` for organization-wide scanning
- `timeout_hours`: Configure different timeout thresholds for each priority level
  - `P0`: High priority tasks (default: 24 hours)
  - `P1`: Medium priority tasks (default: 72 hours)
  - `P2`: Low priority tasks (default: 168 hours)
- `priorities_to_check`: Limit which priorities to scan (e.g., only P0 and P1)
- `exclude_repos`: Exclude specific repositories when scanning an organization
- `task_label`: Customize the label that identifies task issues (default: "Task")
- `priority_pattern`: Regex pattern to match priority labels
- `reminder_template`: Customize the reminder message format
- `notify_unassigned`: Whether to send reminders for tasks without assignees
- `default_mention`: Default mentions for unassigned tasks (can be string or list)

**Example Scenarios:**

1. **Scan single repository:**
   ```yaml
   scan_mode: repo
   repo: mcpp-community/mcpp-bot
   ```

2. **Scan entire organization:**
   ```yaml
   scan_mode: org
   org: mcpp-community
   exclude_repos:
     - archived-project
   ```

3. **Only check critical tasks (P0):**
   ```yaml
   priorities_to_check: ["P0"]
   timeout_hours:
     P0: 12  # Alert after 12 hours
   ```

## Common Configuration

All components use configuration files in the `config/` directory and require a GitHub token via the `GH_TOKEN` environment variable.
