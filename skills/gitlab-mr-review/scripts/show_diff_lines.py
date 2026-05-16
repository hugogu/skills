#!/usr/bin/env python3
"""
Show added/modified lines with their new file line numbers from changes.json.
Useful for finding the exact line number to use in an inline comment.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Show diff added lines with new file line numbers"
    )
    parser.add_argument("--changes-file", required=True, help="Path to changes.json")
    parser.add_argument(
        "--file",
        help="Filter by file path (substring match, e.g. 'FooService.java')",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=0,
        help="Number of context lines to show around each added line",
    )

    args = parser.parse_args()

    with open(args.changes_file, "r", encoding="utf-8") as f:
        changes = json.load(f)

    found = False
    for file_info in changes.get("files", []):
        path = file_info.get("new_path") or file_info.get("old_path", "")
        if args.file and args.file not in path:
            continue

        diff = file_info.get("diff", "")
        if diff == "Binary files differ":
            continue

        current_line = 0
        buffer = []
        lines = diff.split("\n")

        print(f"=== {path} ===")
        found = True

        for idx, line in enumerate(lines):
            if line.startswith("@@"):
                match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if match:
                    current_line = int(match.group(1))
                continue

            is_add = line.startswith("+") and not line.startswith("+++")
            is_rem = line.startswith("-") and not line.startswith("---")
            is_ctx = not is_add and not is_rem and not line.startswith("\\")

            if is_add or is_ctx:
                entry = (current_line, is_add, line)
                buffer.append(entry)
                if is_add:
                    current_line += 1
                elif is_ctx:
                    current_line += 1

                if is_add:
                    # emit with context
                    start = max(0, len(buffer) - 1 - args.context)
                    for bline in buffer[start:]:
                        num, added, text = bline
                        marker = "+" if added else " "
                        if added:
                            print(f"  {marker} {num:4d}: {text}")
                        else:
                            print(f"  {marker} {num:4d}: {text}")
                    print()
                    buffer = []
            elif is_rem:
                # removed lines don't advance new file line numbers
                pass

    if not found:
        print("No matching files found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
