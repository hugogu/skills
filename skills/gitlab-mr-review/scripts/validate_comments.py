#!/usr/bin/env python3
"""
Validate review comments against diff before posting.
Removes comments whose line numbers do not point to valid added/modified lines.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_valid_lines(changes: Dict) -> Dict[str, Set[int]]:
    """Extract valid new_line numbers for each file from changes.json."""
    valid_lines: Dict[str, Set[int]] = {}

    for file_info in changes.get("files", []):
        path = file_info.get("new_path") or file_info.get("old_path", "")
        diff = file_info.get("diff", "")
        valid: Set[int] = set()
        current_line = 0

        for line in diff.split("\n"):
            if line.startswith("@@"):
                match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if match:
                    current_line = int(match.group(1))
            elif line.startswith("+") and not line.startswith("+++"):
                valid.add(current_line)
                current_line += 1
            elif not line.startswith("-") and not line.startswith("\\"):
                current_line += 1

        valid_lines[path] = valid
    return valid_lines


def find_nearest_valid(line: int, valid: Set[int]) -> int:
    """Find the nearest valid line number."""
    if not valid:
        return line
    return min(valid, key=lambda v: abs(v - line))


def validate_comments(
    comments: List[Dict], valid_lines: Dict[str, Set[int]]
) -> Tuple[List[Dict], List[Dict]]:
    """Return (valid_comments, invalid_comments)."""
    valid_comments: List[Dict] = []
    invalid_comments: List[Dict] = []

    for comment in comments:
        path = comment.get("file_path", "")
        line = comment.get("line")
        if line is None:
            invalid_comments.append(comment)
            continue

        file_valid = valid_lines.get(path, set())
        if line in file_valid:
            valid_comments.append(comment)
        else:
            nearest = find_nearest_valid(line, file_valid)
            comment["_invalid_reason"] = (
                f"line {line} is not an added/modified line in the diff "
                f"(nearest valid line: {nearest})"
            )
            comment["_suggested_line"] = nearest
            invalid_comments.append(comment)

    return valid_comments, invalid_comments


def main():
    parser = argparse.ArgumentParser(
        description="Validate review comments against diff lines"
    )
    parser.add_argument("--changes-file", required=True, help="Path to changes.json")
    parser.add_argument("--comments-file", required=True, help="Path to comments JSON")
    parser.add_argument(
        "--output", required=True, help="Output path for validated comments JSON"
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically adjust invalid lines to the nearest valid line",
    )

    args = parser.parse_args()

    with open(args.changes_file, "r", encoding="utf-8") as f:
        changes = json.load(f)

    with open(args.comments_file, "r", encoding="utf-8") as f:
        review_data = json.load(f)

    comments = review_data.get("comments", [])
    if not comments:
        print("No comments to validate")
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False)
        sys.exit(0)

    valid_lines = extract_valid_lines(changes)
    valid_comments, invalid_comments = validate_comments(comments, valid_lines)

    if invalid_comments:
        print(f"Found {len(invalid_comments)} invalid comment(s):", file=sys.stderr)
        for c in invalid_comments:
            reason = c.pop("_invalid_reason", "unknown")
            nearest = c.pop("_suggested_line", None)
            print(
                f"  - {c.get('file_path')}:{c.get('line')} -> {reason}",
                file=sys.stderr,
            )
            if args.auto_fix and nearest is not None:
                c["line"] = nearest
                valid_comments.append(c)
                print(f"    (auto-fixed to line {nearest})", file=sys.stderr)

    review_data["comments"] = valid_comments
    review_data["stats"] = {
        "total_issues": len(valid_comments),
        "by_severity": {
            "critical": len(
                [c for c in valid_comments if c.get("severity") == "critical"]
            ),
            "warning": len(
                [c for c in valid_comments if c.get("severity") == "warning"]
            ),
            "info": len([c for c in valid_comments if c.get("severity") == "info"]),
        },
        "by_type": {},
    }
    for c in valid_comments:
        t = c.get("type", "other")
        review_data["stats"]["by_type"][t] = (
            review_data["stats"]["by_type"].get(t, 0) + 1
        )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(review_data, f, indent=2, ensure_ascii=False)

    print(
        f"Validated: {len(valid_comments)}/{len(comments)} comments valid. "
        f"Saved to {args.output}"
    )

    if invalid_comments and not args.auto_fix:
        sys.exit(1)


if __name__ == "__main__":
    main()
