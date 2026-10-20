# Behavioral acceptance scenarios

Use these for a future smoke run or regression check. They describe observable outcomes, not a claim that a complete diagram has been generated during skill installation. Run artifact-producing cases in a task-owned workspace.

## Overview

Prompt: “用 Excalidraw 画一张人工智能领域知识拆解图，从人工智能逐步分解到算法、数学和数据原理，初学者能沿着图学习。”

Expected: coherent levels and reading order; classification dimensions remain distinct; labeled prerequisite/application links; foundational explanations and verified examples; usable editable source and matching exports. No requirement for exactly ten sections or 54 cards.

## Drill-down with mathematics

Prompt: “把总图里的概率统计展开成类似的大图，只围绕 AI 需要的部分。所有公式包括行内变量都用 LaTeX。”

Expected: relevant scope, parent context, definitions/assumptions/notation, connections to AI methods, rendered equations with retained TeX sources, consistent inline baselines. No literal TeX masquerading as rendered math. It does not merely reproduce the linear-algebra map with renamed headings.

## Global repair

Prompt: “这些卡片下方空了很多，整体都修一下，别缩字号，也别删内容。”

Input: an existing map with short and tall neighboring cards, matrices, captions, cross-section arrows, and formula sources.

Expected: per-card content-sized bounds; appropriate row/section gutters; preserved concept coverage and formula associations; reconnected arrows; regenerated matching outputs. Overview and close-ups include regions outside the screenshot that prompted the repair. If editor testing is unavailable, the delivery states that limit.

## Selection boundaries

- “在 Neo4j 中导入实体和关系并建立知识图谱查询” should route to database/data-engineering work rather than this visual learning-map workflow.
- “只画一个月度销售趋势折线图” should route to plotting rather than an Excalidraw atlas.
- “把现有 Excalidraw 学习地图里的矩阵公式排好并收紧全局布局” should select this skill and preserve unrelated canvas content.
