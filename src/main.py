#!/usr/bin/env python3
"""
MCPP Bot - Main Entry Point

This script provides a unified entry point to run different bot components.
"""

import sys
import argparse
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from components.scan_join_issues import scan as scan_join_issues
from components.task_checker import check as check_tasks


def main():
    """
    Main entry point for the MCPP bot.
    """
    parser = argparse.ArgumentParser(
        description="MCPP Bot - GitHub automation tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all components
  python src/main.py all

  # Run specific component
  python src/main.py join-issues
  python src/main.py task-checker

  # Run multiple components
  python src/main.py join-issues task-checker

Environment Variables:
  GH_TOKEN    GitHub personal access token (required)
        """
    )

    parser.add_argument(
        'components',
        nargs='+',
        choices=['all', 'join-issues', 'task-checker'],
        help='Component(s) to run'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Determine which components to run
    components_to_run = set()
    if 'all' in args.components:
        components_to_run = {'join-issues', 'task-checker'}
    else:
        components_to_run = set(args.components)

    print("=" * 60)
    print("MCPP Bot - GitHub Automation")
    print("=" * 60)

    # Run components
    errors = []

    if 'join-issues' in components_to_run:
        print("\n[1/2] Running Join Issues Scanner...")
        print("-" * 60)
        try:
            scan_join_issues(verbose=args.verbose)
            print("✓ Join Issues Scanner completed successfully")
        except Exception as e:
            error_msg = f"✗ Join Issues Scanner failed: {e}"
            print(error_msg)
            errors.append(error_msg)
            if args.verbose:
                import traceback
                traceback.print_exc()

    if 'task-checker' in components_to_run:
        print("\n[2/2] Running Task Checker...")
        print("-" * 60)
        try:
            check_tasks(verbose=args.verbose)
            print("✓ Task Checker completed successfully")
        except Exception as e:
            error_msg = f"✗ Task Checker failed: {e}"
            print(error_msg)
            errors.append(error_msg)
            if args.verbose:
                import traceback
                traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if errors:
        print(f"✗ {len(errors)} component(s) failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✓ All components completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
