#!/usr/bin/env python3
"""
Analyze code changes and generate review comments based on checklist.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from difflib import SequenceMatcher


class CodeAnalyzer:
    """Analyze code and generate review comments."""

    def __init__(self, checklist: Dict, language: str):
        self.checklist = checklist
        self.language = language
        self.comments = []

    def analyze_file(
        self,
        file_path: str,
        diff_content: str,
        base_sha: str,
        head_sha: str,
        start_sha: str,
    ) -> List[Dict]:
        """Analyze a single file's diff and generate comments."""
        file_comments = []

        # Parse diff to get added lines
        added_lines = self._parse_diff_lines(diff_content)

        # Detect file extension
        ext = Path(file_path).suffix.lower()

        # Analyze based on language
        if self.language == "javascript" or ext in [
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".mjs",
        ]:
            file_comments.extend(
                self._analyze_javascript(
                    file_path, added_lines, base_sha, head_sha, start_sha
                )
            )
        elif self.language == "java" or ext == ".java":
            file_comments.extend(
                self._analyze_java(
                    file_path, added_lines, base_sha, head_sha, start_sha
                )
            )
        elif self.language == "python" or ext == ".py":
            file_comments.extend(
                self._analyze_python(
                    file_path, added_lines, base_sha, head_sha, start_sha
                )
            )

        return file_comments

    def _parse_diff_lines(self, diff_content: str) -> List[Tuple[int, str]]:
        """Parse diff to extract added lines with their line numbers."""
        lines = []
        current_line = 0

        for line in diff_content.split("\n"):
            if line.startswith("@@"):
                # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if match:
                    current_line = int(match.group(1))
            elif line.startswith("+") and not line.startswith("+++"):
                # Added line
                lines.append((current_line, line[1:]))
                current_line += 1
            elif not line.startswith("-") and not line.startswith("\\"):
                # Context line
                current_line += 1

        return lines

    def _analyze_javascript(
        self,
        file_path: str,
        added_lines: List[Tuple[int, str]],
        base_sha: str,
        head_sha: str,
        start_sha: str,
    ) -> List[Dict]:
        """Analyze JavaScript/TypeScript code."""
        comments = []

        for line_num, line_content in added_lines:
            # Check for var usage
            if re.search(r"\bvar\s+", line_content) and self._check_rule("avoid_var"):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "warning",
                        "type": "code_consistency",
                        "message": "使用 `var` 声明变量，建议使用 `const` 或 `let`",
                        "suggestion": line_content.replace("var ", "const ", 1),
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for eval
            if re.search(r"\beval\s*\(", line_content) and self._check_rule("no_eval"):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "critical",
                        "type": "security",
                        "message": "使用 `eval()` 存在安全风险，可能导致代码注入",
                        "suggestion": "避免使用eval，考虑使用JSON.parse或其他安全替代方案",
                        "reference": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/eval",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for innerHTML
            if re.search(r"\.innerHTML\s*[=:]", line_content) and self._check_rule(
                "no_innerhtml"
            ):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "critical",
                        "type": "security",
                        "message": "使用 `innerHTML` 可能导致XSS攻击",
                        "suggestion": "使用 `textContent` 或框架提供的安全API",
                        "reference": "https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for console.log
            if re.search(
                r"console\.(log|debug|warn|error)\s*\(", line_content
            ) and self._check_rule("no_console_in_prod"):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "info",
                        "type": "code_consistency",
                        "message": "生产代码中包含 console.log",
                        "suggestion": "考虑在生产环境中移除调试日志或使用日志库",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for loose equality
            if re.search(r"(?<![=!])=(?!=)", line_content) and self._check_rule(
                "use_strict_equality"
            ):
                # Skip if it's in a string or comment
                if not self._is_in_string_or_comment(
                    line_content, line_content.find("=")
                ):
                    comments.append(
                        {
                            "file_path": file_path,
                            "line": line_num,
                            "severity": "warning",
                            "type": "code_consistency",
                            "message": "使用 `==` 而非 `===`，可能导致意外类型转换",
                            "suggestion": line_content.replace("==", "===", 1).replace(
                                "!=", "!==", 1
                            ),
                            "base_sha": base_sha,
                            "head_sha": head_sha,
                            "start_sha": start_sha,
                        }
                    )

            # Check for magic numbers
            if self._check_rule("no_magic_numbers"):
                magic_num_match = re.search(r"(?<![\w])\d{2,}(?![\w])", line_content)
                if magic_num_match:
                    num = magic_num_match.group()
                    if num not in ["0", "1", "2", "10", "100", "1000"]:
                        comments.append(
                            {
                                "file_path": file_path,
                                "line": line_num,
                                "severity": "info",
                                "type": "code_consistency",
                                "message": f"使用魔法数字 `{num}`",
                                "suggestion": f"将 `{num}` 定义为具名常量",
                                "base_sha": base_sha,
                                "head_sha": head_sha,
                                "start_sha": start_sha,
                            }
                        )

        return comments

    def _analyze_java(
        self,
        file_path: str,
        added_lines: List[Tuple[int, str]],
        base_sha: str,
        head_sha: str,
        start_sha: str,
    ) -> List[Dict]:
        """Analyze Java code."""
        comments = []

        for line_num, line_content in added_lines:
            # Check for System.out.print
            if re.search(
                r"System\.(out|err)\.(print|println)", line_content
            ) and self._check_rule("no_system_out"):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "warning",
                        "type": "code_consistency",
                        "message": "使用 System.out.println 输出日志",
                        "suggestion": "使用日志框架如 SLF4J 或 Log4j",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for String concatenation in loop
            if self._check_rule("use_stringbuilder_in_loop"):
                # This is a simple heuristic - actual detection would need more context
                pass

            # Check for SQL injection risk
            if re.search(
                r"(executeQuery|executeUpdate|execute)\s*\(\s*[^?)]*\+", line_content
            ) and self._check_rule("no_sql_injection"):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "critical",
                        "type": "security",
                        "message": "可能存在SQL注入风险，SQL语句使用字符串拼接",
                        "suggestion": "使用 PreparedStatement 和参数化查询",
                        "reference": "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for raw exception catching
            if re.search(
                r"catch\s*\(\s*Exception\s+", line_content
            ) and self._check_rule("catch_specific_exceptions"):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "warning",
                        "type": "logic",
                        "message": "捕获通用的 Exception 类型",
                        "suggestion": "捕获具体的异常类型，如 IOException、SQLException 等",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for == on strings
            if re.search(r"==\s*\"|\"\s*==", line_content) and self._check_rule(
                "use_equals_for_strings"
            ):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "warning",
                        "type": "logic",
                        "message": "使用 `==` 比较字符串",
                        "suggestion": "使用 `.equals()` 方法比较字符串内容",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

        return comments

    def _analyze_python(
        self,
        file_path: str,
        added_lines: List[Tuple[int, str]],
        base_sha: str,
        head_sha: str,
        start_sha: str,
    ) -> List[Dict]:
        """Analyze Python code."""
        comments = []

        for line_num, line_content in added_lines:
            # Check for print statements
            if re.search(r"\bprint\s*\(", line_content) and self._check_rule(
                "no_print_in_prod"
            ):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "info",
                        "type": "code_consistency",
                        "message": "使用 print() 输出",
                        "suggestion": "考虑使用 logging 模块",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for eval/exec
            if re.search(r"\b(eval|exec)\s*\(", line_content) and self._check_rule(
                "no_eval_exec"
            ):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "critical",
                        "type": "security",
                        "message": f"使用 `{line_content.strip()[:10]}...` 存在安全风险",
                        "suggestion": "避免使用 eval/exec，使用 ast.literal_eval 或安全的替代方案",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for bare except
            if re.search(r"except\s*:", line_content) and self._check_rule(
                "no_bare_except"
            ):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "warning",
                        "type": "logic",
                        "message": "使用裸 except: 捕获所有异常",
                        "suggestion": "捕获具体的异常类型，如 `except ValueError:`",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for mutable default arguments
            if re.search(
                r"def\s+\w+\s*\([^)]*=\s*(\[|\{)", line_content
            ) and self._check_rule("no_mutable_defaults"):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "critical",
                        "type": "logic",
                        "message": "使用可变对象（list/dict）作为默认参数值",
                        "suggestion": "使用 None 作为默认值，在函数内部初始化",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for SQL string formatting
            if re.search(
                r'(".*?%s.*?"|".*?\{.*?\.*?"|\bformat\s*\().*?(execute|cursor)',
                line_content,
                re.IGNORECASE,
            ) and self._check_rule("no_sql_formatting"):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "critical",
                        "type": "security",
                        "message": "SQL查询使用字符串格式化，存在注入风险",
                        "suggestion": "使用参数化查询: cursor.execute('SELECT * FROM t WHERE id = %s', (id,))",
                        "reference": "https://bobby-tables.com/python",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

            # Check for == None (should be is None)
            if re.search(r"==\s*None|!=\s*None", line_content) and self._check_rule(
                "use_is_none"
            ):
                comments.append(
                    {
                        "file_path": file_path,
                        "line": line_num,
                        "severity": "info",
                        "type": "code_consistency",
                        "message": "使用 `== None` 或 `!= None`",
                        "suggestion": "使用 `is None` 或 `is not None`",
                        "base_sha": base_sha,
                        "head_sha": head_sha,
                        "start_sha": start_sha,
                    }
                )

        return comments

    def _check_rule(self, rule_name: str) -> bool:
        """Check if a rule is enabled in the checklist."""
        rules = self.checklist.get("rules", {})
        return rules.get(rule_name, True)  # Default to enabled

    def _is_in_string_or_comment(self, line: str, pos: int) -> bool:
        """Check if position is inside a string or comment."""
        # Simple check - not comprehensive
        in_string = False
        string_char = None

        for i, char in enumerate(line[:pos]):
            if char in ['"', "'"] and (i == 0 or line[i - 1] != "\\"):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None

        return in_string


def load_checklist(checklist_path: Path, language: str) -> Dict:
    """Load checklist from file."""
    if checklist_path.exists():
        with open(checklist_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse markdown checklist
        checklist = {"rules": {}}

        for line in content.split("\n"):
            # Look for disabled rules
            match = re.search(r"[\-\*]\s*禁用:\s*\"(.+?)\"", line)
            if match:
                rule_name = match.group(1)
                checklist["rules"][rule_name] = False

        return checklist

    return {"rules": {}}  # Default: all rules enabled


def filter_duplicates(
    comments: List[Dict],
    existing_comments: List[Dict],
    similarity_threshold: float = 0.8,
) -> List[Dict]:
    """Filter out comments that already exist."""
    filtered = []

    for new_comment in comments:
        is_duplicate = False

        for existing in existing_comments:
            # Check same file and line
            if new_comment.get("file_path") == existing.get(
                "file_path"
            ) and new_comment.get("line") == existing.get("new_line"):
                # Check message similarity
                new_msg = new_comment.get("message", "")
                existing_body = existing.get("body", "")

                similarity = SequenceMatcher(None, new_msg, existing_body).ratio()

                if similarity > similarity_threshold:
                    is_duplicate = True
                    break

        if not is_duplicate:
            filtered.append(new_comment)

    return filtered


def main():
    parser = argparse.ArgumentParser(
        description="Analyze code and generate review comments"
    )
    parser.add_argument("--changes-file", required=True, help="Path to changes.json")
    parser.add_argument("--metadata-file", required=True, help="Path to metadata.json")
    parser.add_argument(
        "--existing-comments", required=True, help="Path to existing_comments.json"
    )
    parser.add_argument("--checklist", help="Path to custom checklist file")
    parser.add_argument(
        "--default-checklist-dir", help="Directory containing default checklists"
    )
    parser.add_argument("--output", required=True, help="Output file for comments")

    args = parser.parse_args()

    # Load data
    with open(args.changes_file, "r", encoding="utf-8") as f:
        changes = json.load(f)

    with open(args.metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    with open(args.existing_comments, "r", encoding="utf-8") as f:
        existing_comments = json.load(f)

    language = metadata.get("detected_language", "unknown")

    # Load checklist
    checklist = {"rules": {}}

    # Try custom checklist first
    if args.checklist and Path(args.checklist).exists():
        checklist = load_checklist(Path(args.checklist), language)

    # Fall back to default checklist
    elif args.default_checklist_dir:
        default_path = Path(args.default_checklist_dir) / f"checklist-{language}.md"
        if default_path.exists():
            checklist = load_checklist(default_path, language)

    # Analyze code
    analyzer = CodeAnalyzer(checklist, language)
    all_comments = []

    base_sha = metadata.get("base_sha", "")
    head_sha = metadata.get("head_sha", "")
    start_sha = metadata.get("start_sha", "")

    for file_info in changes.get("files", []):
        file_path = file_info.get("new_path") or file_info.get("old_path")
        diff_content = file_info.get("diff", "")

        # Skip deleted files
        if file_info.get("is_deleted"):
            continue

        # Skip binary files
        if file_info.get("diff", "") == "Binary files differ":
            continue

        file_comments = analyzer.analyze_file(
            file_path, diff_content, base_sha, head_sha, start_sha
        )
        all_comments.extend(file_comments)

    # Filter duplicates
    filtered_comments = filter_duplicates(all_comments, existing_comments)

    # Prepare output
    output = {
        "metadata": metadata,
        "comments": filtered_comments,
        "stats": {
            "total_issues": len(filtered_comments),
            "by_severity": {
                "critical": len(
                    [c for c in filtered_comments if c.get("severity") == "critical"]
                ),
                "warning": len(
                    [c for c in filtered_comments if c.get("severity") == "warning"]
                ),
                "info": len(
                    [c for c in filtered_comments if c.get("severity") == "info"]
                ),
            },
            "by_type": {},
        },
    }

    # Group by type
    for comment in filtered_comments:
        issue_type = comment.get("type", "other")
        output["stats"]["by_type"][issue_type] = (
            output["stats"]["by_type"].get(issue_type, 0) + 1
        )

    # Save output
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ Analysis complete")
    print(f"  - Total issues: {len(filtered_comments)}")
    print(f"  - Critical: {output['stats']['by_severity']['critical']}")
    print(f"  - Warning: {output['stats']['by_severity']['warning']}")
    print(f"  - Info: {output['stats']['by_severity']['info']}")
    print(f"  - Duplicates skipped: {len(all_comments) - len(filtered_comments)}")


if __name__ == "__main__":
    main()
