#!/usr/bin/env python3
"""
Fetch MR information, diff, and existing comments from GitLab.
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
        raise
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        raise


def fetch_mr_info(gitlab_url: str, project_path: str, mr_iid: int, token: str) -> Dict:
    """Fetch MR basic information."""
    encoded_path = urllib.parse.quote(project_path, safe="")
    url = f"{gitlab_url}/api/v4/projects/{encoded_path}/merge_requests/{mr_iid}"
    return make_request(url, token)


def fetch_mr_diff(
    gitlab_url: str, project_path: str, mr_iid: int, token: str
) -> List[Dict]:
    """Fetch MR diff."""
    encoded_path = urllib.parse.quote(project_path, safe="")
    url = f"{gitlab_url}/api/v4/projects/{encoded_path}/merge_requests/{mr_iid}/diffs"
    return make_request(url, token)


def fetch_discussions(
    gitlab_url: str, project_path: str, mr_iid: int, token: str
) -> List[Dict]:
    """Fetch MR discussions (includes comments)."""
    encoded_path = urllib.parse.quote(project_path, safe="")
    url = f"{gitlab_url}/api/v4/projects/{encoded_path}/merge_requests/{mr_iid}/discussions"

    discussions = []
    page = 1
    per_page = 100

    while True:
        paginated_url = f"{url}?page={page}&per_page={per_page}"
        page_data = make_request(paginated_url, token)

        if not page_data:
            break

        discussions.extend(page_data)

        if len(page_data) < per_page:
            break

        page += 1

    return discussions


def parse_diff_changes(diffs: List[Dict]) -> Dict[str, Any]:
    """Parse diff to extract changed files and content."""
    changes = {"files": [], "additions": 0, "deletions": 0, "changes": 0}

    for diff in diffs:
        file_info = {
            "old_path": diff.get("old_path", ""),
            "new_path": diff.get("new_path", ""),
            "is_new": diff.get("new_file", False),
            "is_deleted": diff.get("deleted_file", False),
            "is_renamed": diff.get("renamed_file", False),
            "diff": diff.get("diff", ""),
            "additions": diff.get("additions", 0),
            "deletions": diff.get("deletions", 0),
        }
        changes["files"].append(file_info)
        changes["additions"] += file_info["additions"]
        changes["deletions"] += file_info["deletions"]
        changes["changes"] += 1

    return changes


def extract_inline_comments(discussions: List[Dict]) -> List[Dict]:
    """Extract inline comments from discussions."""
    comments = []

    for discussion in discussions:
        for note in discussion.get("notes", []):
            if note.get("position"):  # Inline comment
                comment_info = {
                    "id": note.get("id"),
                    "author": note.get("author", {}).get("username"),
                    "body": note.get("body", ""),
                    "file_path": note.get("position", {}).get("new_path"),
                    "old_line": note.get("position", {}).get("old_line"),
                    "new_line": note.get("position", {}).get("new_line"),
                    "base_sha": note.get("position", {}).get("base_sha"),
                    "head_sha": note.get("position", {}).get("head_sha"),
                    "start_sha": note.get("position", {}).get("start_sha"),
                    "created_at": note.get("created_at"),
                    "updated_at": note.get("updated_at"),
                    "resolved": note.get("resolved", False),
                    "resolvable": note.get("resolvable", False),
                    "discussion_id": discussion.get("id"),
                }
                comments.append(comment_info)
            else:  # General comment
                comment_info = {
                    "id": note.get("id"),
                    "author": note.get("author", {}).get("username"),
                    "body": note.get("body", ""),
                    "created_at": note.get("created_at"),
                    "updated_at": note.get("updated_at"),
                    "resolved": note.get("resolved", False),
                    "resolvable": note.get("resolvable", False),
                    "discussion_id": discussion.get("id"),
                }
                comments.append(comment_info)

    return comments


def detect_language(files: List[Dict]) -> str:
    """Detect primary programming language from changed files."""
    extensions = {}

    for file_info in files:
        path = file_info.get("new_path", file_info.get("old_path", ""))
        ext = Path(path).suffix.lower()

        if ext in [".js", ".jsx", ".ts", ".tsx", ".mjs"]:
            extensions["javascript"] = extensions.get("javascript", 0) + 1
        elif ext in [".java"]:
            extensions["java"] = extensions.get("java", 0) + 1
        elif ext in [".py"]:
            extensions["python"] = extensions.get("python", 0) + 1

    if not extensions:
        return "unknown"

    return max(extensions, key=extensions.get)


def main():
    parser = argparse.ArgumentParser(description="Fetch MR data from GitLab")
    parser.add_argument("--gitlab-url", required=True, help="GitLab URL")
    parser.add_argument(
        "--project", required=True, help="Project path (e.g., group/project)"
    )
    parser.add_argument("--mr-iid", type=int, required=True, help="MR IID")
    parser.add_argument("--token", required=True, help="GitLab Personal Access Token")
    parser.add_argument("--output-dir", required=True, help="Output directory")

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Fetch MR info
        print(f"Fetching MR #{args.mr_iid} from {args.project}...")
        mr_info = fetch_mr_info(args.gitlab_url, args.project, args.mr_iid, args.token)

        # Save MR info
        with open(output_dir / "mr_info.json", "w", encoding="utf-8") as f:
            json.dump(mr_info, f, indent=2, ensure_ascii=False)

        # Fetch diff
        print("Fetching diff...")
        diffs = fetch_mr_diff(args.gitlab_url, args.project, args.mr_iid, args.token)
        changes = parse_diff_changes(diffs)

        # Save diff
        with open(output_dir / "changes.json", "w", encoding="utf-8") as f:
            json.dump(changes, f, indent=2, ensure_ascii=False)

        # Save raw diff text
        with open(output_dir / "changes.diff", "w", encoding="utf-8") as f:
            for diff in diffs:
                f.write(diff.get("diff", ""))
                f.write("\n")

        # Fetch discussions
        print("Fetching existing discussions...")
        discussions = fetch_discussions(
            args.gitlab_url, args.project, args.mr_iid, args.token
        )
        comments = extract_inline_comments(discussions)

        # Save comments
        with open(output_dir / "existing_comments.json", "w", encoding="utf-8") as f:
            json.dump(comments, f, indent=2, ensure_ascii=False)

        # Detect language
        detected_lang = detect_language(changes["files"])

        # Get SHA refs from MR info for inline comments
        diff_refs = mr_info.get("diff_refs", {})
        base_sha = diff_refs.get("base_sha", "")
        head_sha = diff_refs.get("head_sha", "")
        start_sha = diff_refs.get("start_sha", "")

        # Create metadata
        metadata = {
            "gitlab_url": args.gitlab_url,
            "project_path": args.project,
            "mr_iid": args.mr_iid,
            "mr_title": mr_info.get("title"),
            "source_branch": mr_info.get("source_branch"),
            "target_branch": mr_info.get("target_branch"),
            "author": mr_info.get("author", {}).get("username"),
            "detected_language": detected_lang,
            "total_files": changes["changes"],
            "total_additions": changes["additions"],
            "total_deletions": changes["deletions"],
            "existing_comments_count": len(comments),
            "base_sha": base_sha,
            "head_sha": head_sha,
            "start_sha": start_sha,
        }

        with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"✓ Successfully fetched MR data")
        print(f"  - Language: {detected_lang}")
        print(f"  - Files: {changes['changes']}")
        print(f"  - Additions: {changes['additions']}")
        print(f"  - Deletions: {changes['deletions']}")
        print(f"  - Existing comments: {len(comments)}")

    except Exception as e:
        print(f"✗ Failed to fetch MR data: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import urllib.parse

    main()
