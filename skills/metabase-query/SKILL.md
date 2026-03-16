---
name: metabase-query
description: 通过 Metabase MCP 安全地创建 Query、Dashboard 并执行 SQL 查询。当用户提到 Metabase、创建查询、创建 Dashboard、数据分析、SQL 查询、数据可视化、图表、报表、指标监控等场景时使用此 skill。该 skill 会自动检查表结构和索引以避免生成低效的全表扫描 SQL，并在调研阶段强制限制输出行数保护数据库性能。
---

# Metabase Query 与 Dashboard 创建

通过 Metabase MCP 安全地创建查询、Dashboard 并执行 SQL，内置数据库性能保护机制。

## 核心安全原则

在使用 Metabase 进行数据查询时，必须遵守以下安全原则以保护数据库性能：

1. **表结构检查优先**：执行任何 SQL 前必须先检查目标表的列信息和索引情况
2. **索引感知查询**：根据索引设计编写 WHERE 子句，避免全表扫描
3. **行数限制**：调研阶段（exploration）的查询必须限制返回行数（默认 LIMIT 100）
4. **渐进式查询**：从少量数据开始验证逻辑，确认无误后再扩大范围

## 前置条件

- Metabase 实例已部署并可访问
- 已配置 Metabase MCP Server
- 数据库连接已配置
- 了解目标数据库的基本结构

## 工作流程

### 阶段一：调研与表结构分析

#### 1. 获取数据库和表信息

首先使用 Metabase MCP 获取可用的数据库和表：

```json
{
  "tool": "metabase_list_databases"
}
```

获取特定数据库的表列表：

```json
{
  "tool": "metabase_list_tables",
  "params": {
    "database_id": 1
  }
}
```

#### 2. 检查表结构（必须）

**这是强制步骤**，在编写任何 SQL 之前必须执行：

```json
{
  "tool": "metabase_get_table_metadata",
  "params": {
    "database_id": 1,
    "table_id": 123
  }
}
```

返回的元数据包含：
- 列信息（名称、类型、是否可空）
- 索引信息（哪些列有索引）
- 主键和外键关系
- 表行数估算

#### 3. 分析索引设计

根据元数据分析：
- **高选择性列**：适合作为 WHERE 条件的索引列（如用户ID、订单号）
- **低选择性列**：避免单独作为查询条件（如状态、布尔值）
- **复合索引**：了解索引列的顺序，确保查询条件与索引前缀匹配
- **缺失索引警告**：如果查询大表且缺少合适索引，提示用户

### 阶段二：安全的 SQL 查询

#### 1. 编写高性能 SQL 的原则

**必须遵守的规则：**

✅ **使用索引列作为过滤条件**
```sql
-- 好：使用索引列 user_id
SELECT * FROM orders WHERE user_id = 12345 LIMIT 100;

-- 差：在无索引列上过滤大表
SELECT * FROM orders WHERE created_at > '2024-01-01' LIMIT 100;
```

✅ **限制返回行数**
```sql
-- 调研阶段始终使用 LIMIT
SELECT * FROM users WHERE status = 'active' LIMIT 100;

-- 需要统计时使用 COUNT
SELECT COUNT(*) FROM users WHERE status = 'active';
```

✅ **避免 SELECT ***
```sql
-- 好：只选择需要的列
SELECT user_id, username, email FROM users LIMIT 100;

-- 差：选择所有列
SELECT * FROM users LIMIT 100;
```

✅ **使用 EXPLAIN 分析执行计划**（如果 MCP 支持）

#### 2. 调研阶段查询（Exploration）

用于了解数据特征，**必须**遵守以下限制：

- **最大返回行数**：100 行（硬限制）
- **避免聚合大表**：除非有过滤条件
- **时间范围限制**：查询大表时必须添加时间范围过滤

**示例调研查询：**

```sql
-- 查看表结构样例数据
SELECT * FROM orders LIMIT 10;

-- 检查特定用户的订单（使用索引列）
SELECT order_id, amount, status, created_at 
FROM orders 
WHERE user_id = 12345 
ORDER BY created_at DESC 
LIMIT 100;

-- 统计数据分布（使用 COUNT 而非返回所有行）
SELECT status, COUNT(*) as count 
FROM orders 
WHERE created_at > '2024-01-01' 
GROUP BY status;
```

#### 3. 使用 Metabase MCP 执行 SQL

```json
{
  "tool": "metabase_execute_sql",
  "params": {
    "database_id": 1,
    "sql": "SELECT user_id, username FROM users WHERE status = 'active' LIMIT 100"
  }
}
```

### 阶段三：创建 Metabase Query

#### 1. 使用查询构建器

对于简单查询，优先使用 Metabase 的图形化查询构建器：

```json
{
  "tool": "metabase_create_question",
  "params": {
    "database_id": 1,
    "name": "活跃用户列表",
    "query": {
      "source-table": 123,
      "filter": ["=", ["field", 456, null], "active"],
      "limit": 100
    }
  }
}
```

#### 2. 创建原生 SQL 查询

对于复杂查询，创建原生 SQL Question：

```json
{
  "tool": "metabase_create_native_question",
  "params": {
    "database_id": 1,
    "name": "最近30天高价值订单",
    "query": "SELECT order_id, user_id, amount, created_at FROM orders WHERE amount > 1000 AND created_at > NOW() - INTERVAL '30 days' ORDER BY amount DESC LIMIT 100",
    "description": "查询最近30天金额超过1000的订单"
  }
}
```

**创建 SQL Query 时的检查清单：**

- [ ] 已检查表结构和索引
- [ ] WHERE 条件使用了索引列或高选择性条件
- [ ] 已添加适当的 LIMIT 限制
- [ ] 避免了对大表的无条件聚合
- [ ] 查询逻辑已用少量数据验证

### 阶段四：创建 Dashboard

#### 1. 规划 Dashboard 结构

在创建 Dashboard 之前，先规划：
- Dashboard 目标（监控、分析、报表）
- 需要的指标和维度
- 时间范围和数据粒度
- 目标受众

#### 2. 创建 Dashboard

```json
{
  "tool": "metabase_create_dashboard",
  "params": {
    "name": "销售数据监控",
    "description": "实时监控销售关键指标",
    "collection_id": 1
  }
}
```

#### 3. 添加 Question 到 Dashboard

```json
{
  "tool": "metabase_add_card_to_dashboard",
  "params": {
    "dashboard_id": 100,
    "card_id": 200,
    "position": {
      "row": 0,
      "col": 0,
      "size_x": 6,
      "size_y": 4
    }
  }
}
```

#### 4. 配置 Dashboard 过滤器（可选）

```json
{
  "tool": "metabase_add_filter_to_dashboard",
  "params": {
    "dashboard_id": 100,
    "name": "日期范围",
    "type": "date/all-options",
    "default": "past30days"
  }
}
```

### 阶段五：性能优化建议

#### 1. 查询优化建议

向用户提供以下优化建议：

**索引优化：**
- 如果查询经常按某些列过滤，建议添加索引
- 复合索引的列顺序应与查询条件匹配

**查询重写：**
- 使用 JOIN 替代子查询
- 避免在 WHERE 中对列进行函数操作（会导致索引失效）
- 使用 EXISTS 替代 IN（对于大表）

**数据建模：**
- 对于复杂分析，建议使用物化视图
- 考虑使用汇总表存储预计算的指标

#### 2. 监控查询性能

建议用户定期监控：
- 查询执行时间
- 全表扫描的查询
- 返回行数过多的查询

## 常见场景示例

### 场景一：用户行为分析

```sql
-- 检查表结构后，使用索引列 user_id 和时间索引
SELECT 
  user_id,
  COUNT(*) as session_count,
  MAX(created_at) as last_active
FROM user_sessions
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY user_id
HAVING COUNT(*) > 5
LIMIT 100;
```

### 场景二：销售报表

```sql
-- 利用时间索引和状态索引
SELECT 
  DATE(created_at) as date,
  COUNT(*) as order_count,
  SUM(amount) as total_amount
FROM orders
WHERE created_at > NOW() - INTERVAL '30 days'
  AND status IN ('completed', 'paid')
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 100;
```

### 场景三：实时监控指标

```sql
-- 使用合适的时间窗口和 LIMIT
SELECT 
  status,
  COUNT(*) as count
FROM orders
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY status
LIMIT 100;
```

## 错误处理

### 数据库连接错误
- 检查 Metabase 数据库连接配置
- 验证数据库服务是否可用
- 检查网络连接

### 查询超时
- 减少查询时间范围
- 添加更严格的过滤条件
- 减少返回列数
- 增加 LIMIT 限制

### 权限错误
- 检查 Metabase 用户的数据库权限
- 确认表和列的访问权限

### 无效列或表
- 重新获取表元数据确认列名
- 检查表名拼写和大小写（某些数据库区分大小写）

## 最佳实践总结

1. **始终先检查表结构** - 在执行任何查询之前
2. **从小数据量开始** - 使用 LIMIT 限制返回行数
3. **优先使用索引列** - 避免全表扫描
4. **渐进式开发** - 先验证逻辑，再扩展范围
5. **记录查询性能** - 关注执行时间和资源消耗
6. **使用参数化查询** - 避免 SQL 注入风险
7. **定期审查 Dashboard** - 移除不再使用的查询

## 实施检查清单

创建 Query 或 Dashboard 时，确保：

- [ ] 已获取并分析表元数据
- [ ] 理解索引设计并能指出合适的过滤条件
- [ ] 调研阶段查询使用 LIMIT 100
- [ ] WHERE 条件使用了高选择性索引列
- [ ] 避免对大表进行无条件聚合
- [ ] 已验证查询逻辑（使用小数据集）
- [ ] 提供了性能优化建议
- [ ] Dashboard 布局合理，关键指标突出

