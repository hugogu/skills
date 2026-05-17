---
name: wiki-writer
description: |
  Write Wiki.js-compatible markdown content. Handles formatting rules, heading hierarchy, LaTeX conventions, YAML frontmatter handling, path conventions, and cross-reference management. This skill ONLY produces content — it does not publish to the Wiki.js API. Use the wiki-publisher skill for API publishing.
triggers:
  - "write a wiki page"
  - "create wiki content"
  - "format markdown for wiki"
  - "convert to wiki format"
  - "draft a wiki article"
metadata:
  runtime: none
  output: "Structured markdown content ready for wiki-publisher skill"
---

# Wiki Writer

Write properly formatted Wiki.js markdown content. This skill handles **content creation only** — publishing is delegated to the **wiki-publisher** skill.

---

## 1. Content Structure Rules

### 1.1 Remove YAML Frontmatter

**CRITICAL:** Wiki.js stores title/description/metadata as API parameters, NOT in the content body.

| Requirement | ✅ Correct | ❌ Wrong |
|-------------|-----------|---------|
| Content starts with H1 | `# Title` | `---\ntitle: Title\n---\n\n# Title` |
| Metadata in content | Never | Never put `title:`, `description:`, `tags:` in content |

The very first line of content must be `# Title` or equivalent H1.

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

### 1.3 Paragraphs and Spacing

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
# Internal wiki pages — use relative paths
[Link text](/zh/category/page-name)

# External links — use full URLs
[Link text](https://example.com)
```

- Prefer relative paths for internal pages.
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
- Avoid wrapping LaTeX math in code blocks (see Section 3).

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

## 3. LaTeX Math Formatting (Critical)

Wiki.js uses KaTeX for math rendering. Only these syntaxes are supported:

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

| ❌ Wrong | ✅ Correct | Reason |
|----------|-----------|--------|
| `\[ E = mc^2 \]` | `$$E = mc^2$$` | LaTeX `\[...\]` not supported |
| `\( \alpha + \beta \)` | `$\alpha + \beta$` | LaTeX `\(...\)` not supported |
| `\begin{equation}...\end{equation}` | `$$...$$` | equation env not supported |
| `` `$E=mc^2$` `` | `$E=mc^2$` | Backticks disable rendering |
| `α + β` | `$\alpha + \beta$` | Unicode Greek not rendered |
| `≈` `≤` `→` | `\approx` `\leq` `\to` | Unicode math symbols not rendered |

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

## 4. Path Conventions

### 4.1 General Rules

- **kebab-case only.** Hyphens (`-`) join words. **No underscores**.
  - ✅ `chain-of-thought`, `fine-tuning`, `design-patterns`
  - ❌ `chain_of_thought`, `fine_tuning`
- **English or pinyin** for paths. Avoid Chinese characters in paths.
- All paths are relative, no leading slash.
- Locale is always `zh`.

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

The following words should NOT be used as standalone path segments (they conflict with CMS routing):

- `admin`, `api`, `graphql`, `login`, `logout`, `register`, `assets`, `static`, `uploads`, `files`, `images`, `fonts`, `locale`, `locales`, `i18n`, `sitemap`, `robots`, `health`, `healthcheck`, `metrics`

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

Link to related wiki pages naturally:

```markdown
参见：[Transformer 架构详解](/zh/ai/tech/transformer)
```

```markdown
更多内容：[哲学知识库索引](/zh/philosophy/index)
```

- When mentioning a topic that has its own wiki page, link to it.
- Use `参见：` or `更多内容：` for explicit references.

---

## 6. Output Format

This skill produces a **local markdown file** saved to `wiki_articles/{path}.md`. The file contains exactly what would be sent as the `content` parameter to the Wiki.js API.

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

> **When done, use the wiki-publisher skill to publish this content to Wiki.js.**

---

## Reference

- Wiki.js Markdown Guide: https://docs.requarks.io/editors/markdown
- KaTeX Supported Functions: https://katex.org/docs/supported.html
- See `wiki-publisher` skill for API publishing instructions
