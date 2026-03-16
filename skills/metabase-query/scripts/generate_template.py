#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL 模板生成器
生成符合安全规范的 SQL 查询模板
"""

import sys

EXPLORATION_TEMPLATES = {
    "sample": """-- 查看表样例数据
SELECT {columns}
FROM {table}
LIMIT {limit};""",
    "filter_by_id": """-- 根据 ID 查询数据（使用索引）
SELECT {columns}
FROM {table}
WHERE {id_column} = {value}
LIMIT {limit};""",
    "filter_by_time": """-- 根据时间范围查询（使用时间索引）
SELECT {columns}
FROM {table}
WHERE {time_column} > NOW() - INTERVAL '{days} days'
LIMIT {limit};""",
    "aggregation": """-- 统计数据分布（使用索引列过滤后聚合）
SELECT 
  {group_column},
  COUNT(*) as count
FROM {table}
WHERE {indexed_column} {operator} {value}
GROUP BY {group_column}
ORDER BY count DESC
LIMIT {limit};""",
    "time_series": """-- 时间序列统计
SELECT 
  DATE({time_column}) as date,
  COUNT(*) as count,
  SUM({value_column}) as total
FROM {table}
WHERE {time_column} > NOW() - INTERVAL '{days} days'
GROUP BY DATE({time_column})
ORDER BY date DESC
LIMIT {limit};""",
}

REPORT_TEMPLATES = {
    "daily_metrics": """-- 每日指标报表
SELECT 
  DATE({time_column}) as date,
  COUNT(DISTINCT {id_column}) as unique_count,
  COUNT(*) as total_count,
  SUM({value_column}) as total_value,
  AVG({value_column}) as avg_value
FROM {table}
WHERE {time_column} >= '{start_date}'
  AND {time_column} <= '{end_date}'
  AND {status_column} IN ({status_values})
GROUP BY DATE({time_column})
ORDER BY date DESC;""",
    "top_n": """-- Top N 统计
SELECT 
  {group_column},
  COUNT(*) as count,
  SUM({value_column}) as total
FROM {table}
WHERE {time_column} > NOW() - INTERVAL '{days} days'
GROUP BY {group_column}
ORDER BY total DESC
LIMIT {n};""",
}


def print_usage():
    """打印使用说明"""
    print("""
SQL 模板生成器

用法:
  python generate_template.py <type> [参数...]

调研阶段模板 (exploration):
  sample           - 查看表样例数据
  filter_by_id     - 根据 ID 查询（使用索引）
  filter_by_time   - 根据时间范围查询
  aggregation      - 统计数据分布
  time_series      - 时间序列统计

报表模板 (report):
  daily_metrics    - 每日指标报表
  top_n            - Top N 统计

示例:
  # 生成查看样例数据的模板
  python generate_template.py sample table=users columns="user_id, username, email" limit=10
  
  # 生成根据 ID 查询的模板
  python generate_template.py filter_by_id table=orders columns="*" id_column=user_id value=12345 limit=100
  
  # 生成时间序列统计模板
  python generate_template.py time_series table=orders time_column=created_at value_column=amount days=7 limit=100
""")


def parse_args(args):
    """解析参数"""
    params = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            params[key] = value
    return params


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["--help", "-h"]:
        print_usage()
        sys.exit(0)

    template_type = sys.argv[1]
    params = parse_args(sys.argv[2:])

    # 设置默认值
    defaults = {
        "limit": "100",
        "columns": "*",
        "days": "7",
        "n": "10",
        "operator": "=",
        "value": "?",
        "status_values": "'completed', 'paid'",
    }

    for key, value in defaults.items():
        if key not in params:
            params[key] = value

    # 选择模板
    if template_type in EXPLORATION_TEMPLATES:
        template = EXPLORATION_TEMPLATES[template_type]
    elif template_type in REPORT_TEMPLATES:
        template = REPORT_TEMPLATES[template_type]
    else:
        print(f"错误: 未知模板类型 '{template_type}'", file=sys.stderr)
        print(
            "可用模板:",
            list(EXPLORATION_TEMPLATES.keys()) + list(REPORT_TEMPLATES.keys()),
            file=sys.stderr,
        )
        sys.exit(1)

    # 生成 SQL
    try:
        sql = template.format(**params)
        print(sql)
    except KeyError as e:
        print(f"错误: 缺少必需参数 {e}", file=sys.stderr)
        print(
            f"该模板需要以下参数之一: {extract_required_params(template)}",
            file=sys.stderr,
        )
        sys.exit(1)


def extract_required_params(template):
    """提取模板中的必需参数"""
    import re

    params = re.findall(r"\{([^}]+)\}", template)
    return ", ".join(set(params))


if __name__ == "__main__":
    main()
