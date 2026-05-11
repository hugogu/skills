---
name: wiki-js
description: |
  Wiki.js GraphQL API 操作与内容管理规范。处理 Wiki 页面创建、更新、查询，以及读书笔记和技术知识库的路径规范。
---

# Wiki.js Skill

## GraphQL API 备忘

### 常用查询

```graphql
# 列出所有页面
{ pages { list { id path title } } }

# 获取页面内容（需要 id）
query GetPage($id: Int!) {
  pages {
    single(id: $id) {
      id
      title
      content
      description
      tags { id tag }
    }
  }
}
```

### 常用变更

```graphql
# 创建页面
mutation CreatePage($content: String!, $title: String!, $path: String!, $description: String!, $tags: [String]!) {
  pages {
    create(content: $content, title: $title, path: $path, description: $description, tags: $tags, editor: "markdown", isPublished: true, isPrivate: false, locale: "zh") {
      page { id path title }
      responseResult { succeeded errorCode message }
    }
  }
}

# 更新页面（需要 id）
mutation UpdatePage($id: Int!, $content: String!, $title: String!, $description: String!, $tags: [String]!) {
  pages {
    update(id: $id, content: $content, title: $title, description: $description, tags: $tags, editor: "markdown", isPublished: true, isPrivate: false) {
      page { id path title }
      responseResult { succeeded errorCode message }
    }
  }
}

# 删除页面
mutation DeletePage($id: Int!) {
  pages {
    delete(id: $id) {
      responseResult { succeeded errorCode message }
    }
  }
}
```

### 关键注意事项

1. **pages.single 需要 id 参数**，不能用 path
2. **tags 字段需要子字段选择**：`tags { id tag }`
3. **创建/更新时必须提供**：`tags`（可为空数组）和 `description`（可为空字符串）
4. **使用 GraphQL Variables** 传递内容，避免字符串转义问题
5. **API Key** 从 `/root/.openclaw/workspace/.env` 读取 `WIKI_KEY`
6. **LaTeX 公式**：Wiki.js 只支持 `$$...$$`（块级）和 `$...$`（行内）语法，不支持 `\[...\]`、`\(...\)` 或 `\begin{equation}...\end{equation}`。生成内容时必须统一使用 `$$...$$` 和 `$...$`。**禁止**用反引号 `` `...` `` 包裹数学公式——这会导致公式显示为纯文本而非渲染后的数学符号。

   **LaTeX 格式详细规范**：
   - **行内公式**（出现在句子中、列表项中）：用 `$...$`
     - 例：`$x(t) \in \mathbb{R}^n$`、 `$\dot{x} = Ax + Bu$`
   - **块级公式**（独立显示，前后空行）：用 `$$...$$`
     - 例：
       ```
       $$\dot{x}(t) = Ax(t) + Bu(t)$$
       $$y(t) = Cx(t) + Du(t)$$
       ```
   - **禁止混用**：不要在 `$...$` 内嵌套 `$$...$$`，也不要在列表项中用 `$$...$$
   - **LaTeX 命令后必须有空格**：写 `\partial x` 而非 `\partialx`，写 `\sigma(y - x)` 而非 `\sigma(y-x)`（括号前可加空格）
   - **希腊字母必须用 LaTeX 命令**：`\alpha`, `\beta`, `\gamma`, `\delta`, `\sigma`, `\mu`, `\phi`, `\lambda` 等，不要用 Unicode 字符（如 α, β, σ）
   - **上下标**：`x_0`, `A^T`, `x^{n+1}`, `A_{ij}`
   - **分数**：`\frac{a}{b}`，不要用 `a/b` 在复杂公式中
   - **积分/求和**：`\int_{a}^{b}`, `\sum_{i=1}^{n}`
   - **特殊集合**：`\mathbb{R}`, `\mathbb{N}`, `\mathbb{Z}`（需要 amsmath 支持）
   - **范数/绝对值**：`\|x\|`, `|x|`
   - **导数**：`\dot{x}` (一阶), `\ddot{x}` (二阶), 不要用 `ẋ` 或 `d²x/dt²` 的纯文本形式
   - **偏导数**：`\frac{\partial f}{\partial x}`，不要用 `∂f/∂x`
   - **无穷**：`\infty`，不要用 `∞`
   - **箭头**：`\to`, `\Rightarrow`, `\iff`，不要用 `→` 或 `⇒`
   - **近似/不等**：`\approx`, `\leq`, `\geq`, `\neq`，不要用 `≈`, `≤`, `≥`, `≠`
   - **点乘/乘号**：`\cdot`，不要用 `·` 或 `×`
   - **转置**：`A^T` 或 `A^{\mathsf{T}}`，不要用 `Aᵀ`

---

## 路径规范

### 读书笔记

统一放在 `books/` 路径下，使用 kebab-case：

```
books/
├── {book-slug}/index              # 单本书笔记
├── index                          # 总目录
└── ...
```

示例：`books/mind-history`、`books/crucial-conversations`

### 技术知识库

- `tech/` — 技术文章
- `blockchain/` — 区块链专题

---

## 已整理内容索引

### 读书笔记

| 路径 | 书名 |
|------|------|
| books/awakened-mind | 认知觉醒 |
| books/built-to-last | 基业长青 |
| books/burnout-society | 倦怠社会 |
| books/crucial-conversations | 关键对话 |
| books/dopamine-nation | 消失的多巴胺 |
| books/drucker-management | 认识管理 |
| books/great-recession | 大衰退 |
| books/guiguzi | 鬼谷子 |
| books/insight | 洞察 |
| books/life-choices | 人生的选择 |
| books/mckinsey-communication | 麦肯锡高效沟通 |
| books/mind-history | 心智简史 |
| books/money-changes-everything | 千年金融史 |
| books/naval-almanack | 那瓦尔宝典 |
| books/nonviolent-communication | 非暴力沟通 |
| books/organizational-behavior | 组织行为学精要 |
| books/out-of-our-minds | 观念的跃升 |
| books/poor-charlies-almanack | 穷查理宝典 |
| books/practice-of-management | 管理的实践 |
| books/quitting | 适时退出 |
| books/scarcity | 稀缺 |
| books/strategy-and-path | 战略与路径 |
| books/zero-to-one | 从0到1 |
| books/witcher-world | 巫师世界观 |
| books/i-am-you | 我就是你啊：走进他人内心的7项修炼 |
| books/why-we-defend | 为什么我们总是在防御 |
| books/road-less-traveled | 少有人走的路 |

### 区块链知识库

| 路径 | 主题 |
|------|------|
| blockchain/index | 知识库索引 |
| blockchain/basics | 基础原理 |
| blockchain/consensus | 共识机制 |
| blockchain/bitcoin | 比特币 |
| blockchain/ethereum | 以太坊 |
| blockchain/defi | 去中心化金融 |
| blockchain/history | 历史 |
| blockchain/nft | NFT |
| blockchain/smart-contracts | 智能合约 |
| blockchain/future-trends | 未来趋势 |

### 哲学知识库

| 路径 | 主题 | 状态 |
|------|------|------|
| philosophy/index | 哲学知识库索引 | ✅ 已创建 |
| philosophy/schools/ancient-greek | 古希腊哲学 | ⏳ 待优化 |
| philosophy/schools/rationalism | 理性主义 | ⏳ 待优化 |
| philosophy/schools/empiricism | 经验主义 | ⏳ 待优化 |
| philosophy/schools/kantian | 康德哲学 | ⏳ 待优化 |
| philosophy/schools/existentialism | 存在主义 | ⏳ 待优化 |
| philosophy/schools/stoicism | 斯多葛主义 | ⏳ 待优化 |
| philosophy/schools/utilitarianism | 功利主义 | ⏳ 待优化 |
| philosophy/schools/continental | 欧陆哲学 | ⏳ 待优化 |
| philosophy/schools/analytic | 分析哲学 | ⏳ 待优化 |
| philosophy/figures/socrates | 苏格拉底 | ⏳ 待优化 |
| philosophy/figures/plato | 柏拉图 | ⏳ 待优化 |
| philosophy/figures/aristotle | 亚里士多德 | ⏳ 待优化 |
| philosophy/figures/descartes | 笛卡尔 | ⏳ 待优化 |
| philosophy/figures/kant | 康德 | ⏳ 待优化 |
| philosophy/figures/nietzsche | 尼采 | ⏳ 待优化 |
| philosophy/figures/wittgenstein | 维特根斯坦 | ⏳ 待优化 |
| philosophy/figures/sartre | 萨特 | ⏳ 待优化 |
| philosophy/figures/marcus-aurelius | 马可·奥勒留 | ⏳ 待优化 |
| philosophy/figures/confucius | 孔子 | ⏳ 待优化 |
| philosophy/figures/laozi | 老子 | ⏳ 待优化 |
| philosophy/figures/zhuangzi | 庄子 | ⏳ 待优化 |
| philosophy/figures/wang-yangming | 王阳明 | ⏳ 待优化 |
| philosophy/concepts/epistemology | 认识论 | ⏳ 待优化 |
| philosophy/concepts/metaphysics | 形而上学 | ⏳ 待优化 |
| philosophy/concepts/ethics | 伦理学 | ⏳ 待优化 |
| philosophy/concepts/logic | 逻辑学 | ⏳ 待优化 |
| philosophy/concepts/aesthetics | 美学 | ⏳ 待优化 |
| philosophy/concepts/free-will | 自由意志 | ⏳ 待优化 |
| philosophy/concepts/consciousness | 意识 | ⏳ 待优化 |
| philosophy/concepts/meaning-of-life | 生命的意义 | ⏳ 待优化 |

---

## 优化队列

以下页面为占位页面，内容待完善，按优先级排序：

### 高优先级
1. `philosophy/schools/ancient-greek` — 古希腊哲学
2. `philosophy/figures/socrates` — 苏格拉底
3. `philosophy/figures/plato` — 柏拉图
4. `philosophy/figures/aristotle` — 亚里士多德
5. `philosophy/concepts/epistemology` — 认识论
6. `philosophy/concepts/ethics` — 伦理学

### 中优先级
7. `philosophy/schools/existentialism` — 存在主义
8. `philosophy/schools/stoicism` — 斯多葛主义
9. `philosophy/figures/kant` — 康德
10. `philosophy/figures/nietzsche` — 尼采
11. `philosophy/figures/confucius` — 孔子
12. `philosophy/figures/laozi` — 老子

### 低优先级
13-30. 其余哲学流派、人物与概念页面

---

## AI 知识库优化队列

以下 AI 骨架页面待完善，按优先级排序：

### 高优先级（核心模型与技术）
1. `ai/models/gpt` — GPT 系列
2. `ai/models/claude` — Claude 系列
3. `ai/models/deepseek` — DeepSeek 系列
4. `ai/tech/transformer` — Transformer 架构详解
5. `ai/tech/attention` — Attention 机制演进
6. `ai/tech/rag` — RAG 检索增强生成
7. `ai/tech/agent` — AI Agent 架构

### 中优先级（框架与工具）
8. `ai/frameworks/langchain` — LangChain
9. `ai/frameworks/llamaindex` — LlamaIndex
10. `ai/frameworks/ollama` — Ollama
11. `ai/tech/fine-tuning` — 模型微调技术
12. `ai/tech/quantization` — 模型量化
13. `ai/tech/rlhf` — RLHF 与人类反馈强化学习

### 低优先级（论文与应用）
14-25. 其余模型、框架、论文、应用页面

---

### AI 知识库

| 路径 | 主题 | 状态 |
|------|------|------|
| ai/index | AI 知识体系索引 | ✅ 已创建 |
| ai/llm | LLM 大语言模型 | ✅ 已创建 |
| ai/models/index | 知名 AI 模型索引 | ✅ 骨架 |
| ai/models/gpt | GPT 系列 | ✅ 骨架 |
| ai/models/claude | Claude 系列 | ✅ 骨架 |
| ai/models/gemini | Gemini 系列 | ✅ 骨架 |
| ai/models/llama | LLaMA 系列 | ✅ 骨架 |
| ai/models/deepseek | DeepSeek 系列 | ✅ 骨架 |
| ai/models/glm | GLM 系列 | ✅ 骨架 |
| ai/models/kimi | Kimi 系列 | ✅ 骨架 |
| ai/models/qwen | Qwen 系列 | ✅ 骨架 |
| ai/models/mistral | Mistral 系列 | ✅ 骨架 |
| ai/tech/index | AI 核心技术索引 | ✅ 骨架 |
| ai/tech/transformer | Transformer 架构详解 | ✅ 骨架 |
| ai/tech/attention | Attention 机制演进 | ✅ 骨架 |
| ai/tech/rlhf | RLHF 与人类反馈强化学习 | ✅ 骨架 |
| ai/tech/rag | RAG 检索增强生成 | ✅ 骨架 |
| ai/tech/agent | AI Agent 架构 | ✅ 骨架 |
| ai/tech/fine-tuning | 模型微调技术 | ✅ 骨架 |
| ai/tech/quantization | 模型量化 | ✅ 骨架 |
| ai/tech/multimodal | 多模态技术 | ✅ 骨架 |
| ai/tech/embedding | Embedding 与向量表示 | ✅ 骨架 |
| ai/tech/prompt-engineering | Prompt Engineering | ✅ 骨架 |
| ai/tech/evaluation | 模型评估方法 | ✅ 骨架 |
| ai/frameworks/index | AI 开发框架索引 | ✅ 骨架 |
| ai/frameworks/pytorch | PyTorch | ✅ 骨架 |
| ai/frameworks/huggingface | Hugging Face | ✅ 骨架 |
| ai/frameworks/langchain | LangChain | ✅ 骨架 |
| ai/frameworks/llamaindex | LlamaIndex | ✅ 骨架 |
| ai/frameworks/crewai | CrewAI | ✅ 骨架 |
| ai/frameworks/ollama | Ollama | ✅ 骨架 |
| ai/frameworks/vllm | vLLM | ✅ 骨架 |
| ai/frameworks/tensorrt | TensorRT | ✅ 骨架 |
| ai/papers/index | 重要论文索引 | ✅ 骨架 |
| ai/papers/attention-is-all-you-need | Attention Is All You Need | ✅ 骨架 |
| ai/papers/gpt-papers | GPT 系列论文 | ✅ 骨架 |
| ai/papers/bert | BERT | ✅ 骨架 |
| ai/papers/instruction-tuning | Instruction Tuning | ✅ 骨架 |
| ai/papers/chain-of-thought | Chain-of-Thought | ✅ 骨架 |
| ai/papers/rlhf-paper | RLHF 论文 | ✅ 骨架 |
| ai/papers/moe | Mixture of Experts | ✅ 骨架 |
| ai/papers/diffusion | Diffusion Models | ✅ 骨架 |
| ai/papers/vision-transformer | Vision Transformer | ✅ 骨架 |
| ai/applications/index | AI 应用索引 | ✅ 骨架 |
| ai/applications/coding | AI 辅助编程 | ✅ 骨架 |
| ai/applications/writing | AI 辅助写作 | ✅ 骨架 |
| ai/applications/design | AI 辅助设计 | ✅ 骨架 |
| ai/applications/search | AI 搜索 | ✅ 骨架 |
| ai/applications/education | AI 教育 | ✅ 骨架 |
| ai/applications/healthcare | AI 医疗 | ✅ 骨架 |
| ai/applications/finance | AI 金融 | ✅ 骨架 |
| ai/mcp | MCP 模型上下文协议 | ✅ 已创建 |
| ai/skill | Skill 技能系统 | ✅ 已创建 |
| ai/vibe-coding-concepts | Vibe Coding 工具概念对比 | ✅ 已创建 |
| ai/payments | AI 支付领域技术全景 | ✅ 已创建 |
| ai/protocols/acp | ACP 智能体商务协议 | ✅ 已创建 |
| ai/protocols/mpp | MPP 机器支付协议 | ✅ 已创建 |
| ai/protocols/lsp | LSP 语言服务器协议 | ✅ 已创建 |
| ai/protocols/ucp | UCP 通用商务协议 | ✅ 已创建 |
| ai/protocols/acs | ACS 智能体商务套件 | ✅ 已创建 |
| ai/tools | OpenClaw 工具与插件生态全景 | ✅ 已创建 |
| ai/tools/maton-ai | Maton.ai 分析 | ✅ 已创建 |
| ai/coding-tools-ecosystem | AI 辅助编程工具体系 | ✅ 已创建 |
| ai/llm-wiki-pattern | LLM Wiki 模式 | ✅ 已创建 |

---

### 数学知识库

| 路径 | 主题 | 状态 |
|------|------|------|
| math/index | 数学知识库索引 | ✅ 已创建 |
| math/foundations/logic | 数理逻辑 | ⏳ 待优化 |
| math/foundations/set-theory | 集合论 | ⏳ 待优化 |
| math/foundations/proof-techniques | 证明方法 | ⏳ 待优化 |
| math/algebra/elementary | 初等代数 | ⏳ 待优化 |
| math/algebra/linear | 线性代数 | ⏳ 待优化 |
| math/algebra/abstract | 抽象代数 | ⏳ 待优化 |
| math/algebra/number-theory | 数论 | ⏳ 待优化 |
| math/algebra/combinatorics | 组合数学 | ⏳ 待优化 |
| math/algebra/category-theory | 范畴论 | ⏳ 待优化 |
| math/analysis/calculus | 微积分 | ⏳ 待优化 |
| math/analysis/real | 实分析 | ⏳ 待优化 |
| math/analysis/complex | 复分析 | ⏳ 待优化 |
| math/analysis/functional | 泛函分析 | ⏳ 待优化 |
| math/analysis/ode | 常微分方程 | ⏳ 待优化 |
| math/analysis/pde | 偏微分方程 | ⏳ 待优化 |
| math/analysis/harmonic | 调和分析 | ⏳ 待优化 |
| math/geometry/euclidean | 欧几里得几何 | ⏳ 待优化 |
| math/geometry/analytic | 解析几何 | ⏳ 待优化 |
| math/geometry/differential | 微分几何 | ⏳ 待优化 |
| math/geometry/topology | 拓扑学 | ⏳ 待优化 |
| math/geometry/algebraic | 代数几何 | ⏳ 待优化 |
| math/geometry/discrete | 离散几何 | ⏳ 待优化 |
| math/probability/probability-theory | 概率论 | ⏳ 待优化 |
| math/probability/stochastic-processes | 随机过程 | ⏳ 待优化 |
| math/probability/statistics | 统计学 | ⏳ 待优化 |
| math/probability/information-theory | 信息论 | ⏳ 待优化 |
| math/applied/numerical | 数值分析 | ⏳ 待优化 |
| math/applied/optimization | 最优化 | ⏳ 待优化 |
| math/applied/dynamical-systems | 动力系统 | ⏳ 待优化 |
| math/applied/control-theory | 控制论 | ⏳ 待优化 |
| math/applied/game-theory | 博弈论 | ⏳ 待优化 |
| math/applied/cryptography | 密码学 | ⏳ 待优化 |
| math/computational/algorithms | 算法与复杂性 | ⏳ 待优化 |
| math/computational/machine-learning | 机器学习数学 | ⏳ 待优化 |
| math/computational/quantum | 量子计算数学 | ⏳ 待优化 |

---
