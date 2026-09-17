---
name: wiki-writer
description: |
  Write well-structured markdown content for knowledge-base / wiki pages. Handles formatting rules, heading hierarchy, math notation conventions, metadata handling, path/slug conventions, and cross-reference management. This skill ONLY produces content — it is platform-agnostic and does not publish to any specific wiki/CMS API. Use a dedicated publisher skill (e.g. wiki-publisher for Wiki.js) to push the output.
triggers:
  - "write a wiki page"
  - "create wiki content"
  - "format markdown for wiki"
  - "convert to wiki format"
  - "draft a wiki article"
metadata:
  runtime: none
  output: "Structured markdown content ready for a publisher skill"
---

# Wiki Writer

Write properly formatted markdown content for a knowledge base. This skill handles **content creation only** and is **platform-agnostic** — publishing is delegated to a separate publisher skill (see `wiki-publisher` for Wiki.js).

> **Platform note.** This skill defines generic markdown conventions. A few conventions (math syntax, path/slug rules, metadata handling) have platform-specific variants. Where a platform differs, an adapter is expected to override the defaults in **Section 7**; the defaults below target the common case (GFM + KaTeX).

---

## 1. Content Structure Rules

### 1.1 Metadata Handling

**CRITICAL:** Page metadata (title, description, tags, locale) belongs to the **publishing layer**, not the content body. Keep the body clean and let the publisher supply metadata as API/form parameters.

| Requirement | ✅ Correct | ❌ Wrong |
|-------------|-----------|---------|
| Content starts with H1 | `# Title` | `---\ntitle: Title\n---\n\n# Title` |
| Metadata in content | Never | Never put `title:`, `description:`, `tags:` in content |

The very first line of content must be `# Title` or equivalent H1.

> If a target platform **requires** YAML frontmatter (some static-site generators do), that is a platform adapter concern — see Section 7. Default: no frontmatter.

### 1.2 Heading Hierarchy

```markdown
# H1 — Page Title (ONLY ONE per page)
## H2 — Major Section
### H3 — Subsection
#### H4 — Minor subsection
```

- **Exactly one H1.** It must be the first line of content.
- Do not skip levels (H1 → H3 is invalid).
- Keep H3+ for detailed breakdowns; avoid going deeper than H4 for readability.

### 1.3 Section Content Completeness

**Every section must have sufficient textual description.** A section should not consist solely of a table, list, code block, or diagram — each section needs narrative text that:

- **Introduces** the topic: what is being discussed and why it matters
- **Explains** the table/list: what the data or items mean, not just present them
- **Provides commentary**: insights, comparisons, implications, or historical context

> ✅ **Good** — Section with a table and accompanying text:
> ```markdown
> ## 处理器架构演进
>
> 处理器架构在过去五十年的演进反映了半导体工艺和计算需求的协同发展。从单核到多核，从复杂指令集到精简指令集，每一次架构变革都对应着特定时期的技术瓶颈突破。
>
> | 架构 | 时期 | 代表产品 | 关键技术突破 |
> |------|------|---------|-------------|
> | x86 | 1978 | 8086 | CISC架构的普及 |
> | ARM | 1985 | ARM1 | RISC低功耗设计 |
>
> 上表展示了两种主流架构的起点。x86 凭借向后兼容性统治桌面和服务器市场数十年，而 ARM 则凭借能效比优势在移动端无可匹敌。近年来两者正在趋近——苹果 M 系列芯片证明了 ARM 架构同样可以胜任高性能计算。
> ```

> ❌ **Bad** — Section with only a table, no narrative:
> ```markdown
> ## 处理器架构演进
>
> | 架构 | 时期 | 代表产品 |
> |------|------|---------|
> | x86 | 1978 | 8086 |
> | ARM | 1985 | ARM1 |
> ```

**Exception:** Index/summary tables (e.g., a glossary list or reference table) at the end of an article may be standalone, but should still have a brief introductory sentence.

### 1.4 Paragraphs and Spacing

- Separate paragraphs with **one blank line**.
- Separate sections with **one blank line** before H2.
- Lists should have a blank line before the first item and after the last.
- Code blocks should have blank lines before and after.

---

## 2. Markdown Formatting Rules

### 2.1 Bold and Italic

| Style | Syntax | Example |
|-------|--------|---------|
| Bold | `**text**` | **bold text** |
| Italic | `*text*` | *italic text* |
| Bold+Italic | `***text***` | ***bold italic*** |

### 2.2 Links

```markdown
# Internal pages — relative paths by default
[Link text](/category/page-name)

# External links — full URLs
[Link text](https://example.com)
```

- Prefer relative paths for internal pages. Match the target platform's canonical URL scheme (some include a locale prefix like `/zh/...` — see Section 4.1).
- Use full URLs only for external resources.
- Link text should be descriptive, not "click here".

### 2.3 Images

```markdown
![Alt text](https://cdn.example.com/image.png)
```

- Always include descriptive alt text.
- Prefer CDN-hosted images. Avoid data URIs in content.
- Use markdown image syntax, not HTML `<img>` tags.

### 2.4 Lists

**Unordered:**
```markdown
- Item one
- Item two
  - Nested item (2-space indent)
  - Another nested
- Item three
```

**Ordered:**
```markdown
1. First step
2. Second step
   1. Sub-step (3-space indent)
3. Third step
```

- Use consistent indentation (2 spaces for nested items).
- Add blank line before and after lists.

### 2.5 Code Blocks

```markdown
\```language-name
code here
\```
```

- Always specify the language for syntax highlighting (pre-requisite: the code block is preceded by a blank line; the triple backticks each on their own line).
- Use inline `` `code` `` for short references.
- Avoid wrapping math in code blocks (see Section 3).

### 2.6 Tables

```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell     | Cell     | Cell     |
| Cell     | Cell     | Cell     |
```

- Always include the separator line after headers.
- Keep tables concise. For large datasets, consider breaking into multiple tables.
- Left-align text, center or right-align numbers as appropriate.

### 2.7 Blockquotes

```markdown
> Quote text.
>
> > Nested quote (use >> on each line).
>
> — Attribution
```

---

## 3. Math Notation

Most wiki platforms render math with a client-side library. The **default target is KaTeX** (`$...$` inline, `$$...$$` display), which is the common convention for modern markdown wikis.

### 3.1 Inline Math

Use **`$...$`** for math within a sentence.

```
When $E = mc^2$, the energy...
The function $f(x) = ax^2 + bx + c$ is quadratic.
```

### 3.2 Display / Block Math

Use **`$$...$$`** for standalone math, each on its own line:

```
$$
\int_{a}^{b} f(x) \, dx = F(b) - F(a)
$$

$$
\frac{\partial u}{\partial t} = \alpha \nabla^2 u
$$
```

### 3.3 Prohibited Syntax ❌

These render reliably across KaTeX/MathJax-based wikis but poorly or not at all:

| ❌ Wrong | ✅ Correct | Reason |
|----------|-----------|--------|
| `\[ E = mc^2 \]` | `$$E = mc^2$$` | LaTeX `\[...\]` often not supported |
| `\( \alpha + \beta \)` | `$\alpha + \beta$` | LaTeX `\(...\)` often not supported |
| `\begin{equation}...\end{equation}` | `$$...$$` | equation env often not supported |
| `` `$E=mc^2$` `` | `$E=mc^2$` | Backticks disable rendering |
| `α + β` | `$\alpha + \beta$` | Unicode Greek not rendered |
| `≈` `≤` `→` | `\approx` `\leq` `\to` | Unicode math symbols not rendered |

> **Platform variant:** if the target renderer is MathJax-based and accepts `\(...\)` / `\[...\]`, an adapter may relax this. Default stays strict (`$`/`$$`) for maximum portability.

### 3.4 LaTeX Command Reference

| Category | Command | Example |
|----------|---------|---------|
| Greek | `\alpha`, `\beta`, `\gamma`, `\delta`, `\sigma`, `\mu`, `\phi`, `\lambda`, `\theta`, `\omega`, `\pi`, `\tau` | `$\alpha\beta\gamma$` |
| Subscript | `_` | `x_0`, `A_{ij}` |
| Superscript | `^` | `x^2`, `e^{x+y}` |
| Fraction | `\frac{numerator}{denominator}` | `$\frac{1}{2}$` |
| Integral | `\int_{lower}^{upper}` | `$\int_{0}^{\infty}$` |
| Summation | `\sum_{i=1}^{n}` | `$\sum_{i=1}^{n} x_i$` |
| Derivative | `\dot{x}`, `\ddot{x}` | `$\dot{x} = v$` |
| Partial | `\frac{\partial f}{\partial x}` | `$\frac{\partial f}{\partial x}$` |
| Vector/Matrix | `\mathbf{v}`, `\mathbb{R}`, `\mathcal{L}` | `$\mathbf{x} \in \mathbb{R}^n$` |
| Norm | `\|x\|` | `$\|x\|_2$` |
| Arrow | `\to`, `\Rightarrow`, `\Leftrightarrow`, `\iff` | `$x \to y$` |
| Relation | `\approx`, `\leq`, `\geq`, `\neq`, `\sim`, `\subset` | `$x \approx y$` |
| Operator | `\cdot`, `\times`, `\pm`, `\circ` | `$a \cdot b$` |
| Set | `\cup`, `\cap`, `\in`, `\notin`, `\emptyset` | `$x \in A$` |
| Infinity | `\infty` | `$\lim_{x \to \infty}$` |
| Transpose | `A^T`, `A^{\mathsf{T}}` | `$A^T A$` |
| Ellipsis | `\dots`, `\cdots`, `\vdots`, `\ddots` | `$x_1, x_2, \dots, x_n$` |
| Accents | `\hat{x}`, `\bar{x}`, `\tilde{x}`, `\vec{x}` | `$\hat{\beta}$` |
| Brackets | `\left(`, `\right)`, `\left[`, `\right]`, `\lbrace`, `\rbrace` | `$\left( \frac{a}{b} \right)$` |

### 3.5 LaTeX Spacing Rules

- **LaTeX commands must be followed by a space or punctuation** before the next letter:
  - ✅ `\partial x`, `\sigma(y - x)`, `\alpha \beta`
  - ❌ `\partialx`, `\sigmay`, `\alphabeta`
- For commands at end of sentence: `... \alpha.` (dot after space)
- For commands before comma: `\alpha, \beta`

---

## 4. Path & Slug Conventions

### 4.1 General Rules

- **kebab-case only.** Hyphens (`-`) join words. **No underscores**.
  - ✅ `chain-of-thought`, `fine-tuning`, `design-patterns`
  - ❌ `chain_of_thought`, `fine_tuning`
- **English or pinyin** for slugs. Avoid Chinese characters in slugs.
- All paths are relative, no leading slash.
- Locale handling is a **publishing-layer** concern. Some platforms prefix URLs with a locale (`/zh/...`); capture that in the publisher, not by hardcoding it into every link.

### 4.2 Category Paths

| Content Type | Example Path |
|--------------|-------------|
| Book notes | `books/{book-slug}/index` |
| Blog posts | `blog/{year}/{month}/{slug}` |
| Technical docs | `tech/{category}/{topic}` |
| AI knowledge base | `ai/{category}/{topic}` |
| Philosophy | `philosophy/{category}/{name}` |
| Mathematics | `math/{branch}/{topic}` |
| Blockchain | `blockchain/{topic}` |
| World history | `history/{country}/{category}/{page}` |
| Personal notes | `notes/{category}/{name}` |
| Project docs | `projects/{name}/{doc}` |

### 4.3 Book Notes Specific

```
books/
├── {book-slug}/index              # Main notes page
├── index                          # Books index
└── ...
```

### 4.4 Reserved Path Words

The following words should NOT be used as standalone slug segments (they commonly conflict with CMS/web routing):

- `admin`, `api`, `graphql`, `login`, `logout`, `register`, `assets`, `static`, `uploads`, `files`, `images`, `fonts`, `locale`, `locales`, `i18n`, `sitemap`, `robots`, `health`, `healthcheck`, `metrics`

> The exact reserved list is platform-specific; the publisher can extend this set.

---

## 5. Content Quality Guidelines

### 5.1 Structure

- **Start with a summary/overview** paragraph after the H1 (before any H2).
- Organize with clear H2 sections.
- Use H3 and H4 for depth within sections.
- End with references, further reading, or related pages.

### 5.2 Tone and Voice

- **Knowledge base, not blog post.** Be factual, structured, and reference-based.
- Use plain Chinese for instructional content.
- Define technical terms on first use.
- Avoid subjective opinions unless attributed.
- Prefer active voice: "该系统支持..." over "该系统是被支持的..."

### 5.3 Data and References

- Use tables for structured data comparisons.
- Cite sources where applicable.
- For timelines, use ordered lists or tables.
- Keep statistics specific (year, source).

### 5.4 Cross-References

Link to related pages naturally:

```markdown
参见：[Transformer 架构详解](/ai/tech/transformer)
```

```markdown
更多内容：[哲学知识库索引](/philosophy/index)
```

- When mentioning a topic that has its own page, link to it.
- Use `参见：` or `更多内容：` for explicit references.

---

## 6. Output Format

This skill produces a **local markdown file** saved to `wiki_articles/{path}.md`. The file contains exactly what a publisher would send as the content payload.

**File structure:**
```
wiki_articles/
└── {category}/
    └── {page-name}/
        └── index.md
```

**File content example:**
```markdown
# Page Title

Summary/overview paragraph.

## Section One

Content with proper formatting...

## Section Two

More content...

### Subsection

$$
E = mc^2
$$

## References

- Source one
- Source two
```

> **When done, hand the file to a publisher skill** (e.g. `wiki-publisher` for Wiki.js) to push it to the target platform.

---

## 7. Platform Adapters (Optional)

This skill is platform-agnostic by default. When targeting a specific platform, record only the **deltas** here instead of rewriting the whole skill.

| Concern | Default | Adapter overrides |
|---------|---------|-------------------|
| Metadata | Title/description/tags supplied by publisher | Platforms needing frontmatter (static-site generators) re-inject it |
| Math | `$...$` / `$$...$$` (KaTeX) | MathJax platforms may allow `\(...\)` / `\[...\]` |
| Internal links | Relative path, no locale prefix | Locale-prefixed platforms (e.g. Wiki.js `/zh/...`) add the prefix |
| Reserved slugs | Common CMS/web words | Platform extends the list |
| Publisher | External publisher skill | Wiki.js → `wiki-publisher`; others → their own |

**Wiki.js adapter:** see the `wiki-publisher` skill. Its specifics (locale `zh`, GraphQL API params, KaTeX rendering) are handled there, not baked into this writer.

---

## Reference

- CommonMark / GFM spec: https://github.github.com/gfm/
- KaTeX Supported Functions: https://katex.org/docs/supported.html
- MathJax: https://docs.mathjax.org/
