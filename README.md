# MCPP Bot

A collection of GitHub automation tools for managing repositories and organizations.

## Project Structure

```
src/
├── components/         # Bot components and modules
│   ├── scan_join_issues.py    # Process join requests
│   ├── task_checker.py         # Check and remind on overdue tasks
│   └── README.md               # Component documentation
├── config/            # Configuration files
│   ├── join-config.yml        # Join request configuration
│   └── task-checker.yml       # Task checker configuration
├── libs/              # Shared libraries
│   ├── github_client.py       # GitHub API client
│   ├── utils.py               # Utility functions
│   └── __init__.py
└── main.py            # Main entry point
```

## Components

### 1. Task Checker

Monitors task issues with priority labels (P0/P1/P2) and sends reminders when they haven't been updated within configured timeouts.

**Quick Start:**
```bash
export GH_TOKEN="your_github_token"
python src/components/task_checker.py
```

**Features:**
- Scan single repository or entire organization
- Customizable timeout thresholds per priority (P0/P1/P2)
- Flexible reminder templates
- Repository exclusion support
- Configurable priority patterns

See [components/README.md](src/components/README.md) for detailed configuration options.

### 2. Join Request Scanner

Processes join request issues for organization membership management.

**Quick Start:**
```bash
export GH_TOKEN="your_github_token"
python src/components/scan_join_issues.py
```

## Quick Start

1. Clone the repository
2. Set up your GitHub token:
   ```bash
   export GH_TOKEN="your_github_personal_access_token"
   ```
3. Configure the components in `src/config/`
4. Run the bot:
   ```bash
   # Run all components
   python src/main.py all

   # Run specific component
   python src/main.py join-issues
   python src/main.py task-checker

   # Run multiple components
   python src/main.py join-issues task-checker

   # Enable verbose error output
   python src/main.py all --verbose
   ```

## Running Individual Components

You can also run components directly:

```bash
# Task checker
python src/components/task_checker.py

# Join issues scanner
python src/components/scan_join_issues.py
```

## Configuration

All components use YAML configuration files in `src/config/`:

- `join-config.yml` - Join request processing settings
- `task-checker.yml` - Task monitoring and reminder settings

## Requirements

- Python 3.7+
- GitHub Personal Access Token with appropriate permissions
  - For task checker: `repo` scope (read issues, write comments)
  - For join scanner: `admin:org` scope (manage organization members)

## GitHub Actions Workflows

This project includes automated workflows for scheduled execution:

- **Daily Bot Tasks** (`daily-scan.yml`): Runs all components daily at 02:20 UTC
- **Task Checker Hourly** (`task-checker-hourly.yml`): Checks task timeouts every 6 hours

See [.github/workflows/README.md](.github/workflows/README.md) for workflow documentation.

## License

See [LICENSE](LICENSE) for details.