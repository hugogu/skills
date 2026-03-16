#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL 安全检查器
用于在创建 Metabase Query 前检查 SQL 的安全性
"""

import re
import sys
import json
from typing import List, Dict, Tuple


class SQLSecurityChecker:
    """SQL 安全检查器"""

    def __init__(self):
        self.issues = []
        self.warnings = []

    def check_limit_clause(self, sql: str) -> bool:
        """检查是否包含 LIMIT 子句"""
        # 移除注释和字符串，避免误判
        cleaned = re.sub(r"'[^']*'", "''", sql, flags=re.IGNORECASE)
        cleaned = re.sub(r"--.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)

        # 检查 LIMIT
        has_limit = bool(re.search(r"\bLIMIT\s+\d+\b", cleaned, re.IGNORECASE))
        return has_limit

    def check_select_star(self, sql: str) -> bool:
        """检查是否使用了 SELECT *"""
        cleaned = re.sub(r"'[^']*'", "''", sql, flags=re.IGNORECASE)
        cleaned = re.sub(r"--.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)

        # 检查 SELECT *
        has_star = bool(re.search(r"\bSELECT\s+\*\b", cleaned, re.IGNORECASE))
        return has_star

    def check_where_clause(self, sql: str) -> bool:
        """检查是否包含 WHERE 子句"""
        cleaned = re.sub(r"'[^']*'", "''", sql, flags=re.IGNORECASE)
        cleaned = re.sub(r"--.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)

        # 检查 WHERE（不包括 JOIN 条件）
        has_where = bool(re.search(r"\bWHERE\b", cleaned, re.IGNORECASE))
        return has_where

    def check_full_table_scan_patterns(self, sql: str) -> List[str]:
        """检查可能导致全表扫描的模式"""
        issues = []
        cleaned = re.sub(r"'[^']*'", "''", sql, flags=re.IGNORECASE)

        # 函数作用于列（导致索引失效）
        function_patterns = [
            (
                r"\bWHERE\s+\w+\s*[=<>!]+\s*\w+\s*\(",
                "WHERE 条件中对列使用函数可能导致索引失效",
            ),
            (
                r"\bLOWER\s*\(\s*\w+\s*\)",
                "LOWER() 函数作用于列可能导致索引失效，考虑使用不区分大小写的比较或函数索引",
            ),
            (r"\bUPPER\s*\(\s*\w+\s*\)", "UPPER() 函数作用于列可能导致索引失效"),
            (
                r"\bDATE\s*\(\s*\w+\s*\)",
                "DATE() 函数作用于列可能导致索引失效，考虑使用范围查询",
            ),
        ]

        for pattern, message in function_patterns:
            if re.search(pattern, cleaned, re.IGNORECASE):
                issues.append(message)

        # LIKE 以 % 开头
        if re.search(r"\bLIKE\s+'%", cleaned, re.IGNORECASE):
            issues.append("LIKE 以 % 开头无法使用索引，考虑使用全文搜索或其他方案")

        return issues

    def check_query_complexity(self, sql: str) -> Tuple[int, List[str]]:
        """检查查询复杂度"""
        complexity_score = 0
        warnings = []

        cleaned = re.sub(r"'[^']*'", "''", sql, flags=re.IGNORECASE)

        # 统计 JOIN 数量
        join_count = len(re.findall(r"\bJOIN\b", cleaned, re.IGNORECASE))
        if join_count > 3:
            complexity_score += 2
            warnings.append(f"查询包含 {join_count} 个 JOIN，可能影响性能")

        # 统计子查询数量
        subquery_count = len(re.findall(r"\bSELECT\b", cleaned, re.IGNORECASE)) - 1
        if subquery_count > 2:
            complexity_score += 2
            warnings.append(f"查询包含 {subquery_count} 个子查询，建议简化")

        # 检查 GROUP BY
        if re.search(r"\bGROUP\s+BY\b", cleaned, re.IGNORECASE):
            complexity_score += 1

        # 检查 ORDER BY 与 GROUP BY 同时存在
        if re.search(r"\bGROUP\s+BY\b", cleaned, re.IGNORECASE) and re.search(
            r"\bORDER\s+BY\b", cleaned, re.IGNORECASE
        ):
            warnings.append("同时使用 GROUP BY 和 ORDER BY 可能导致排序临时表")

        return complexity_score, warnings

    def analyze(self, sql: str, is_exploration: bool = True) -> Dict:
        """分析 SQL 语句"""
        self.issues = []
        self.warnings = []

        # 检查 LIMIT（调研阶段必须）
        if is_exploration and not self.check_limit_clause(sql):
            self.issues.append(
                "调研阶段查询必须使用 LIMIT 限制返回行数（建议 LIMIT 100）"
            )

        # 检查 SELECT *
        if self.check_select_star(sql):
            self.warnings.append("建议使用具体列名替代 SELECT *，减少数据传输")

        # 检查 WHERE 子句
        if not self.check_where_clause(sql):
            self.warnings.append("查询缺少 WHERE 子句，可能对大表进行全表扫描")

        # 检查全表扫描模式
        scan_issues = self.check_full_table_scan_patterns(sql)
        self.warnings.extend(scan_issues)

        # 检查复杂度
        complexity, complexity_warnings = self.check_query_complexity(sql)
        self.warnings.extend(complexity_warnings)

        if complexity >= 3:
            self.issues.append(f"查询复杂度过高（得分: {complexity}），建议拆分或优化")

        return {
            "safe": len(self.issues) == 0,
            "issues": self.issues,
            "warnings": self.warnings,
            "complexity_score": complexity,
            "recommendations": self._generate_recommendations(sql),
        }

    def _generate_recommendations(self, sql: str) -> List[str]:
        """生成优化建议"""
        recommendations = []

        if not self.check_limit_clause(sql):
            recommendations.append("添加 LIMIT 子句限制返回行数")

        if self.check_select_star(sql):
            recommendations.append("列出需要的具体列名，避免 SELECT *")

        if not self.check_where_clause(sql):
            recommendations.append("添加 WHERE 子句过滤数据")

        recommendations.append("确认查询使用了索引列作为过滤条件")
        recommendations.append("在大表上执行前，先用 EXPLAIN 分析执行计划")

        return recommendations


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python check_sql.py '<SQL 语句>' [--exploration]", file=sys.stderr)
        print("  --exploration: 表示这是调研阶段查询（默认开启）", file=sys.stderr)
        sys.exit(1)

    sql = sys.argv[1]
    is_exploration = "--exploration" in sys.argv or "--exploration" not in sys.argv[2:]

    checker = SQLSecurityChecker()
    result = checker.analyze(sql, is_exploration)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 如果有严重问题，返回非零退出码
    if not result["safe"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
