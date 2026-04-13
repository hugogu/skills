#!/usr/bin/env python3
"""
Post review comments to GitLab MR.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Any


def make_request(
    url: str, token: str, method: str = "GET", data: Optional[bytes] = None
) -> Dict:
    """Make authenticated request to GitLab API."""
    headers = {
        "Private-Token": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    req = urllib.request.Request(url, headers=headers, method=method, data=data)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {error_body}", file=sys.stderr)
        raise RuntimeError(f"HTTP {e.code}: {error_body}") from e
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        raise


def post_inline_comment(
    gitlab_url: str, project_path: str, mr_iid: int, token: str, comment: Dict
) -> bool:
    """Post an inline comment to MR."""
    encoded_path = urllib.parse.quote(project_path, safe="")
    url = f"{gitlab_url}/api/v4/projects/{encoded_path}/merge_requests/{mr_iid}/discussions"

    # Build position data
    position = {
        "base_sha": comment.get("base_sha"),
        "head_sha": comment.get("head_sha"),
        "start_sha": comment.get("start_sha"),
        "position_type": "text",
        "new_path": comment["file_path"],
        "old_path": comment["file_path"],
        "new_line": comment.get("line"),
    }

    # Handle multi-line comments
    if comment.get("start_line"):
        position["old_line"] = comment.get("start_line")

    data = {"body": format_comment_body(comment), "position": position}

    try:
        make_request(url, token, method="POST", data=json.dumps(data).encode("utf-8"))
        return True
    except RuntimeError as e:
        err_msg = str(e)
        if "HTTP 400:" in err_msg:
            error_body = err_msg.split("HTTP 400:", 1)[1].strip()
            if "line_code" in error_body:
                print(
                    f"  ✗ Skipped (line {comment.get('line')} is not a valid diff line - ensure it points to an added/modified line)",
                    file=sys.stderr,
                )
            else:
                print(
                    f"  ✗ Skipped (HTTP 400: {error_body or 'invalid request'})",
                    file=sys.stderr,
                )
        else:
            print(f"Failed to post comment: {err_msg}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Failed to post comment: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Failed to post comment: {e}", file=sys.stderr)
        return False


def post_general_comment(
    gitlab_url: str, project_path: str, mr_iid: int, token: str, body: str
) -> bool:
    """Post a general comment to MR (not inline)."""
    encoded_path = urllib.parse.quote(project_path, safe="")
    url = f"{gitlab_url}/api/v4/projects/{encoded_path}/merge_requests/{mr_iid}/notes"

    data = {"body": body}

    try:
        make_request(url, token, method="POST", data=json.dumps(data).encode("utf-8"))
        return True
    except Exception as e:
        print(f"Failed to post general comment: {e}", file=sys.stderr)
        return False


def format_comment_body(comment: Dict) -> str:
    """Format comment body with markdown and optional suggestion block."""
    severity = comment.get("severity", "info")
    issue_type = comment.get("type", "issue")
    message = comment.get("message", "")
    suggestion = comment.get("suggestion", "")
    reference = comment.get("reference", "")

    # Severity emoji mapping
    severity_emojis = {"critical": "🔴", "warning": "🟡", "info": "🔵"}

    emoji = severity_emojis.get(severity, "🔵")

    lines = [
        f"{emoji} **{severity.upper()}**: {issue_type.replace('_', ' ').title()}",
        "",
        message,
    ]

    # Add suggestion using GitLab's suggestion block syntax
    if suggestion:
        lines.extend(
            [
                "",
                "**建议**:",
                "```suggestion",
                suggestion,
                "```",
            ]
        )

    if reference:
        lines.extend(["", f"**参考**: {reference}"])

    return "\n".join(lines)


def calculate_quality_grade(severity_counts: Dict[str, int]) -> str:
    """Calculate overall quality grade based on issue counts."""
    score = (
        100
        - severity_counts.get("critical", 0) * 20
        - severity_counts.get("warning", 0) * 8
        - severity_counts.get("info", 0) * 2
    )
    if score >= 90:
        return "🟢 A (Excellent)"
    if score >= 80:
        return "🟢 B (Good)"
    if score >= 60:
        return "🟡 C (Fair)"
    if score >= 40:
        return "🟠 D (Poor)"
    return "🔴 F (Fail)"


def generate_summary_comment(review_data: Dict) -> str:
    """Generate summary comment markdown."""
    comments = review_data.get("comments", [])
    metadata = review_data.get("metadata", {})

    # Group by severity
    severity_counts = {"critical": 0, "warning": 0, "info": 0}
    type_counts = {}

    for comment in comments:
        severity = comment.get("severity", "info")
        issue_type = comment.get("type", "other")

        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        type_counts[issue_type] = type_counts.get(issue_type, 0) + 1

    grade = calculate_quality_grade(severity_counts)
    total_issues = len(comments)

    # Build summary
    lines = [
        "## 📝 MR Review Summary",
        "",
        f"**Reviewed**: {metadata.get('mr_title', 'MR')} ({metadata.get('detected_language', 'unknown')})",
        f"**Files Changed**: {metadata.get('total_files', 0)} | "
        f"**Additions**: {metadata.get('total_additions', 0)} | "
        f"**Deletions**: {metadata.get('total_deletions', 0)}",
        "",
        f"### 整体质量评级: {grade}",
        "",
        "### 发现的问题",
        "",
        "| Severity | Count |",
        "|----------|-------|",
        f"| 🔴 Critical | {severity_counts['critical']} |",
        f"| 🟡 Warning | {severity_counts['warning']} |",
        f"| 🔵 Info | {severity_counts['info']} |",
        f"| **Total** | **{total_issues}** |",
        "",
    ]

    # Highlight merge conflicts if present
    if metadata.get("has_conflicts"):
        lines.extend(
            [
                "⚠️ **注意**: 该 MR 当前存在合并冲突，请先解决冲突后再合并。",
                "",
            ]
        )

    # Add breakdown by type if there are issues
    if type_counts:
        lines.extend(["### 问题类别", ""])
        for issue_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- **{issue_type.replace('_', ' ').title()}**: {count}")
        lines.append("")

    # Add critical/warning details
    if severity_counts["critical"] > 0 or severity_counts["warning"] > 0:
        lines.extend(["### 需要关注的问题", ""])

        for comment in comments:
            if comment.get("severity") in ["critical", "warning"]:
                file_path = comment.get("file_path", "")
                line = comment.get("line", "")
                msg = comment.get("message", "")[:100]
                if len(comment.get("message", "")) > 100:
                    msg += "..."

                emoji = "🔴" if comment.get("severity") == "critical" else "🟡"
                lines.append(f"{emoji} `{file_path}:{line}` - {msg}")

        lines.append("")

    # Add grade-specific suggestion
    lines.extend(["### 评审意见", ""])
    if severity_counts["critical"] > 0:
        lines.append(
            f"当前代码存在 **{severity_counts['critical']}** 个 critical 问题，强烈建议修复后再合并。"
        )
    elif severity_counts["warning"] > 3:
        lines.append("代码整体可用，但 warning 问题较多，建议抽时间逐步优化。")
    elif total_issues == 0:
        lines.append("本次变更未发现问题，代码质量良好。")
    else:
        lines.append("代码质量整体良好，部分建议供参考。")

    lines.append("")

    # Add suggestions
    lines.extend(["### 建议行动", ""])

    if severity_counts["critical"] > 0:
        lines.append("- [ ] **优先修复** critical 级别的问题")
    if severity_counts["warning"] > 0:
        lines.append("- [ ] 考虑修复 warning 级别的问题")
    if severity_counts["info"] > 0:
        lines.append("- [ ] 酌情参考 info 级别的建议")

    lines.extend(
        [
            "",
            "---",
            "*This review was generated automatically. Please feel free to discuss any suggestions.*",
        ]
    )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Post review comments to GitLab MR")
    parser.add_argument("--gitlab-url", required=True, help="GitLab URL")
    parser.add_argument(
        "--project", required=True, help="Project path (e.g., group/project)"
    )
    parser.add_argument("--mr-iid", type=int, required=True, help="MR IID")
    parser.add_argument("--token", required=True, help="GitLab Personal Access Token")
    parser.add_argument(
        "--comments-file", required=True, help="JSON file with comments to post"
    )
    parser.add_argument("--metadata-file", help="Metadata JSON file for summary")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print comments without posting"
    )

    args = parser.parse_args()

    # Load comments
    comments_file = Path(args.comments_file)
    if not comments_file.exists():
        print(f"Comments file not found: {comments_file}", file=sys.stderr)
        sys.exit(1)

    with open(comments_file, "r", encoding="utf-8") as f:
        review_data = json.load(f)

    comments = review_data.get("comments", [])

    if not comments:
        print("No comments to post")
        sys.exit(0)

    print(f"Posting {len(comments)} comments...")

    # Load metadata if available
    metadata = {}
    if args.metadata_file:
        metadata_path = Path(args.metadata_file)
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

    review_data["metadata"] = metadata

    if args.dry_run:
        print("\n=== DRY RUN MODE ===\n")

        for i, comment in enumerate(comments, 1):
            print(f"\n--- Comment {i} ---")
            print(f"File: {comment.get('file_path')}:{comment.get('line')}")
            print(f"Body:\n{format_comment_body(comment)}")

        print("\n=== Summary Comment ===\n")
        print(generate_summary_comment(review_data))

        sys.exit(0)

    # Post inline comments
    success_count = 0
    for comment in comments:
        print(f"Posting comment on {comment.get('file_path')}:{comment.get('line')}...")

        if post_inline_comment(
            args.gitlab_url, args.project, args.mr_iid, args.token, comment
        ):
            success_count += 1
            print("  ✓ Posted")
        else:
            print("  ✗ Failed")

    # Post summary comment
    print("\nPosting summary comment...")
    summary_body = generate_summary_comment(review_data)

    if post_general_comment(
        args.gitlab_url, args.project, args.mr_iid, args.token, summary_body
    ):
        print("  ✓ Summary posted")
    else:
        print("  ✗ Failed to post summary")

    print(f"\n✓ Posted {success_count}/{len(comments)} comments")


if __name__ == "__main__":
    import urllib.parse

    main()
