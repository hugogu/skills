---
name: wiki-publisher
description: Publish markdown content to Wiki.js with proper formatting and metadata. Use when user wants to create or update wiki pages, convert notes/articles to wiki format, or publish content to a Wiki.js instance. Handles API authentication, content formatting (removing YAML frontmatter), automatic tagging, and path suggestions.
metadata: {"env": [{"name": "WIKI_KEY", "description": "Wiki.js API token (generate in Admin > API Access)", "required": true, "credential": true}, {"name": "WIKI_URL", "description": "Wiki.js GraphQL endpoint, e.g. https://your-wiki.example.com/graphql", "required": true}], "primaryCredential": "WIKI_KEY", "runtime": {"python": {"deps": ["requests"]}}}
---

# Wiki Publisher

Publish markdown content to Wiki.js with proper formatting and metadata handling.

## When to Use

Use this skill when:
- User wants to publish content to their Wiki.js instance
- Converting articles, notes, or analysis to wiki format
- Creating new wiki pages with proper structure
- Updating existing wiki pages
- Need to handle Wiki.js GraphQL API operations

## Prerequisites

- `WIKI_KEY` environment variable must be set (Wiki.js API key)
- Wiki.js instance URL must be accessible
- User must have write permissions to the target wiki

## Content Formatting Rules

### LaTeX Math Formulas

Wiki.js only supports `$$...$$` (block) and `$...$` (inline) for LaTeX math. All other syntax will render as plain text.

**Inline formulas** (inside sentences, list items, table cells):
- Use `$...$`
- Examples: `$x(t) \in \mathbb{R}^n$`, `$\dot{x} = Ax + Bu$`, `$K_p \cdot e(t)$`
- **NEVER** use `$$...$$` inside a list item or sentence

**Block formulas** (standalone, on their own lines):
- Use `$$...$$` with blank lines before and after
- Example:
  ```markdown
  $$\dot{x}(t) = Ax(t) + Bu(t)$$

  $$y(t) = Cx(t) + Du(t)$$
  ```

**Prohibited patterns:**
- `\[...\]` and `\(...\)` — not supported by Wiki.js
- `` `...` `` (backticks) for math — renders as plain text code
- `$...$$...$` (nesting block inside inline) — breaks rendering
- Unicode math characters (`α`, `β`, `σ`, `∞`, `∂`, `∫`, `→`, `≈`, `≤`, `≥`, `≠`, `·`) — use LaTeX commands instead

**LaTeX command reference:**
| Symbol | LaTeX | Unicode (DON'T USE) |
|--------|-------|---------------------|
| Greek α | `\alpha` | `α` |
| Greek β | `\beta` | `β` |
| Greek γ | `\gamma` | `γ` |
| Greek δ | `\delta` | `δ` |
| Greek σ | `\sigma` | `σ` |
| Greek μ | `\mu` | `μ` |
| Greek φ | `\phi` | `φ` |
| Greek λ | `\lambda` | `λ` |
| Infinity | `\infty` | `∞` |
| Partial | `\partial` | `∂` |
| Integral | `\int` | `∫` |
| Sum | `\sum` | `∑` |
| Arrow | `\to` | `→` |
| Approx | `\approx` | `≈` |
| ≤ | `\leq` | `≤` |
| ≥ | `\geq` | `≥` |
| ≠ | `\neq` | `≠` |
| Dot product | `\cdot` | `·` |
| Real numbers | `\mathbb{R}` | `ℝ` |

**Spacing rules:**
- Always put a space after a LaTeX command before a variable: `\partial x` not `\partialx`
- Correct: `\frac{\partial f}{\partial x}`, `\sigma(y - x)`, `\dot{x}(t)`
- Wrong: `\partialx`, `\partialf`, `\sigmay`, `\deltad`

**Subscripts and superscripts:**
- Simple: `x_0`, `A^T`, `y_n`
- Multi-char: `x^{n+1}`, `A_{ij}`, `\sum_{i=1}^{n}`

**Derivatives:**
- First order: `\dot{x}` (not `ẋ` or `dx/dt` in plain text)
- Second order: `\ddot{x}` (not `d²x/dt²`)
- Partial: `\frac{\partial f}{\partial x}` (not `∂f/∂x`)

**Fractions:**
- Always use `\frac{a}{b}` for displayed math
- Inline simple fractions can use `/`: `$a/b$`

---

### Remove YAML Frontmatter

**CRITICAL:** Wiki.js stores title/description in API parameters, NOT in content.

❌ **Don't include in content:**
```markdown
---
title: Page Title
description: Page description
---

# Page Title
```

✅ **Correct format:**
```markdown
# Page Title

Content starts here...
```

### Heading Structure

- Always start with H1 (`# Title`)
- Use proper hierarchy (H1 → H2 → H3)
- Don't skip levels

### Links

- Use markdown format: `[text](url)`
- Prefer relative links for internal wiki pages
- External links should use full URL

## API Usage

### ⚠️ CRITICAL: GraphQL String Handling

**The #1 cause of failures is incorrect string escaping.**

#### ❌ WRONG - Direct String Interpolation

```python
# DON'T DO THIS - will fail with complex content
query = f'''
mutation {{
  pages {{
    create(content: "{content}") {{  # Content with quotes/newlines will break
      page {{ id }}
    }}
  }}
}}
'''
```

**Why it fails:**
- Markdown contains `"` (quotes) that terminate the GraphQL string
- Newlines in content break the query syntax
- Backslashes in code blocks escape incorrectly
- JSON serialization double-escapes

#### ✅ CORRECT - Use GraphQL Variables (RECOMMENDED)

```python
import json
import requests

query = '''
mutation CreatePage($content: String!, $title: String!, $path: String!) {
  pages {
    create(
      content: $content
      title: $title
      path: $path
      editor: "markdown"
      isPublished: true
      isPrivate: false
      locale: "zh"
    ) {
      page {
        id
        path
        title
      }
      responseResult {
        succeeded
        errorCode
        message
      }
    }
  }
}
'''

variables = {
    "content": raw_content,  # Pass raw content, no preprocessing
    "title": "Page Title",
    "path": "category/page-name",
    "tags": []  # Required - can be empty list
}

# Let json.dumps handle all escaping automatically
payload = json.dumps({
    "query": query,
    "variables": variables
})

response = requests.post(
    WIKI_URL,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WIKI_KEY}"
    },
    data=payload
)
```

**Why this works:**
- `json.dumps()` properly escapes all special characters
- GraphQL Variables separate data from query structure
- Handles quotes, newlines, backslashes, Unicode automatically

#### ✅ ALTERNATIVE - Use Block String (Triple Quotes)

For simple updates when Variables cause issues:

```python
# Replace any """ in content first
safe_content = content.replace('"""', '\x00TRIPLE\x00')

mutation = f'''
mutation {{
  pages {{
    update(
      id: {page_id}
      content: """{safe_content}"""
      description: "Updated description"
      editor: "markdown"
      tags: []
    ) {{
      page {{ id path title }}
      responseResult {{ succeeded errorCode message }}
    }}
  }}
}}
'''
```

### Create Page

```graphql
mutation CreatePage($content: String!, $title: String!, $path: String!, $description: String!, $tags: [String]!) {
  pages {
    create(
      content: $content
      description: $description
      editor: "markdown"
      isPublished: true
      isPrivate: false
      locale: "zh"
      path: $path
      tags: $tags
      title: $title
    ) {
      page {
        id
        path
        title
      }
      responseResult {
        succeeded
        errorCode
        message
      }
    }
  }
}
```

**Variables:**
```json
{
  "content": "# Title\n\nContent...",
  "title": "Page Title",
  "path": "topic/category/page-name",
  "description": "Page description",
  "tags": ["tag1", "tag2"]
}
```

**Important:** `tags` must be provided even if empty (`[]`). Some Wiki.js versions require this field.

**Type Requirements:**
- `$content`: `String!` - Required, raw markdown
- `$title`: `String!` - Required
- `$path`: `String!` - Required, URL path
- `$description`: `String!` - **Required** (can be empty string)
- `$tags`: `[String]!` - **Required** array of strings (can be empty `[]`)

### Update Page

**Two-step process:**
1. Query page ID by path
2. Update page using ID

#### Step 1: Query Page ID

**⚠️ IMPORTANT:** `pages.single` requires `id` parameter, NOT `path`. 

You must first list all pages to find the ID by path:

```graphql
query {
  pages {
    list {
      id
      path
      title
      description
    }
  }
}
```

Then match the path to find the page ID:

```python
def get_page_id_by_path(path: str) -> int:
    """Find page ID by path from pages.list."""
    query = json.dumps({
        "query": "{ pages { list { id path title } } }"
    }).encode()
    
    req = urllib.request.Request(
        WIKI_URL,
        data=query,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WIKI_KEY}"
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        pages = data.get('data', {}).get('pages', {}).get('list', [])

    for page in pages:
        if page['path'] == path:
            return page['id']
    return None
```

**Alternative:** If you need the full page content (including `content` field) and don't want to make two API calls, query `pages.list` with the `content` field directly:

```graphql
query {
  pages {
    list {
      id
      path
      title
      content
      description
      tags {
        id
        tag
      }
    }
  }
}
```

This returns all pages with their full content — filter client-side by path. This avoids the `pages.single(id: Int!)` limitation when you only know the path.
        for p in pages:
            if p.get('path') == path:
                return p.get('id')
    return None
```
```

#### Step 2: Update Page

```graphql
mutation UpdatePage($id: Int!, $content: String!, $description: String!) {
  pages {
    update(
      id: $id
      content: $content
      description: $description
      editor: "markdown"
      tags: []
    ) {
      page {
        id
        path
        title
      }
      responseResult {
        succeeded
        errorCode
        message
      }
    }
  }
}
```

**⚠️ CRITICAL for Update:**
- `tags` is **REQUIRED** even if empty `[]`
- `description` is **REQUIRED** even if empty string `""`
- Missing either will cause: `Cannot read properties of undefined (reading 'map')`

**Variables:**
```json
{
  "id": 25,
  "content": "# Updated Content\n\n...",
  "description": "Updated description"
}
```

## GraphQL String Type Reference

### String Representation

GraphQL supports two string formats:

#### 1. Single-line Strings (Double Quote)
```graphql
description: "Single line text"
```

**Escape sequences required:**
| Character | Escape | Example |
|-----------|--------|---------|
| `"` | `\"` | `"Say \"hello\""` |
| `\` | `\\` | `"C:\\path"` |
| Newline | `\n` | `"Line1\nLine2"` |
| Tab | `\t` | `"Col1\tCol2"` |

#### 2. Block Strings (Triple Quote)
```graphql
content: """
Multi-line
content here
"""
```

**Notes:**
- Preserves newlines
- Must escape `"""` within content
- Leading whitespace is normalized based on first line

### Common Escape Pitfalls

#### Pitfall 1: Markdown Code Blocks

Markdown contains triple backticks that conflict:
```markdown
```python
def hello():
    pass
```
```

When inserted into GraphQL block string:
```graphql
content: """
```python  # ❌ Conflicts with GraphQL """
def hello()
```
"""
```

**Solution:** Use GraphQL Variables (recommended) or escape each `` ` `` as `\`.

#### Pitfall 2: JSON Double-Escaping

```python
# ❌ WRONG - manual escape then JSON serialize
content_escaped = content.replace('"', '\\"')
payload = json.dumps({"query": f'..."{content_escaped}"...'})
# Results in: \" (double escaped)

# ✅ CORRECT - pass raw content to variables
payload = json.dumps({
    "query": "mutation($c: String!) { create(content: $c) }",
    "variables": {"c": raw_content}
})
```

#### Pitfall 3: Unicode Characters

GraphQL Strings are UTF-8 encoded. Ensure:
- Source file is UTF-8
- HTTP request specifies `Content-Type: application/json; charset=utf-8`
- No BOM (Byte Order Mark) at file start

## Path Conventions

Suggest paths based on content type:

| Content Type | Suggested Path |
|--------------|----------------|
| Technical docs | `tech/{category}/{topic}` |
| Thinking models | `topic/thinking-models/{name}` |
| Financial concepts | `financial/{category}/{name}` |
| Personal notes | `notes/{category}/{name}` |
| Project docs | `projects/{name}/{doc}` |

### ⚠️ Reserved Path Words

Wiki.js treats certain words as system-reserved. **Avoid using these as path segments** (especially with underscores):

| Reserved Word | Example (BAD) | Safe Alternative |
|---------------|---------------|------------------|
| `fine` | `ai/tech/fine_tuning` | `ai/tech/fine-tuning` |
| `home` | `docs/home_page` | `docs/home-page` |
| `login` | `auth/login_form` | `auth/login-form` |
| `register` | `user/register_page` | `user/register-page` |

**Rule of thumb:** Always use **hyphens (`-`)** instead of **underscores (`_`)** in wiki paths. Not only does this avoid reserved word conflicts, it also produces cleaner URLs.

## Workflow

### For New Pages:
1. **Extract content** - Get markdown from user or generate it
2. **Clean formatting** - Remove YAML frontmatter if present
3. **Suggest metadata** - Propose path, tags, description
4. **Confirm with user** - Show proposed wiki location
5. **Create** - Execute `pages.create` mutation with **all required fields**
6. **Return link** - Provide wiki page URL

### For Existing Pages:
1. **Query page ID** - Use `pages.single(path: "...")` or `pages.list`
2. **Get current content** (optional) - For comparison
3. **Update** - Execute `pages.update` mutation with **id + all required fields**
4. **Verify** - Check response for success
5. **Return link** - Provide wiki page URL

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ValidationError: Variable $content... invalid value` | String escaping issue | Use Variables + json.dumps |
| `Field "create" argument "tags" of type "[String]!" is required` | Missing required tags parameter | Always provide `tags: []` even if empty |
| `GraphQLError: Variable $tags of type [String]` | Tags type mismatch | Use `[String]!` in mutation signature |
| `Cannot read properties of undefined (reading 'map')` | Missing `tags` or `description` in update | Add `tags: []` and `description: "..."` |
| `Unauthorized` | Invalid API key | Check WIKI_KEY env var |
| `Page already exists` | Path conflict | Use update mutation or different path |

### Debugging Failed Requests

Always check both `errors` array and `responseResult`:

```python
result = response.json()

# Check GraphQL-level errors
if 'errors' in result:
    for err in result['errors']:
        print(f"GraphQL Error: {err.get('message')}")

# Check Wiki.js response result
resp_result = result.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {})
if not resp_result.get('succeeded'):
    print(f"Wiki.js Error {resp_result.get('errorCode')}: {resp_result.get('message')}")
```

## Example: Create Page (Complete)

```python
import os
import json
import urllib.request

WIKI_URL = os.environ.get("WIKI_URL")  # e.g. https://your-wiki.example.com/graphql
WIKI_KEY = os.environ.get("WIKI_KEY")

def create_wiki_page(content: str, title: str, path: str, 
                     description: str = "", tags: list = None) -> dict:
    """
    Create a Wiki.js page using GraphQL API.
    """
    query = '''
    mutation CreatePage($content: String!, $title: String!, 
                       $path: String!, $description: String!, 
                       $tags: [String]!) {
      pages {
        create(
          content: $content
          title: $title
          path: $path
          description: $description
          tags: $tags
          editor: "markdown"
          isPublished: true
          isPrivate: false
          locale: "zh"
        ) {
          page {
            id
            path
            title
          }
          responseResult {
            succeeded
            errorCode
            message
          }
        }
      }
    }
    '''
    
    variables = {
        "content": content,
        "title": title,
        "path": path,
        "description": description or title,
        "tags": tags if tags is not None else []
    }
    
    payload = json.dumps({
        "query": query,
        "variables": variables
    }).encode('utf-8')
    
    req = urllib.request.Request(
        WIKI_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WIKI_KEY}"
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

# Usage
with open('article.md', 'r', encoding='utf-8') as f:
    content = f.read()

result = create_wiki_page(
    content=content,
    title="软件反模式（Anti-Patterns）",
    path="tech/patterns/anti_patterns",
    description="软件工程中常见反模式的识别与规避指南",
    tags=["软件设计", "反模式", "最佳实践"]
)
```

## Example: Update Page (Complete)

```python
import os
import json
import urllib.request

WIKI_URL = os.environ.get("WIKI_URL")  # e.g. https://your-wiki.example.com/graphql
WIKI_KEY = os.environ.get("WIKI_KEY")

def update_wiki_page(page_id: int, content: str, description: str = "") -> dict:
    """
    Update a Wiki.js page using GraphQL API.
    
    ⚠️ IMPORTANT: tags and description are REQUIRED even if empty!
    """
    query = '''
    mutation UpdatePage($id: Int!, $content: String!, $description: String!) {
      pages {
        update(
          id: $id
          content: $content
          description: $description
          editor: "markdown"
          isPublished: true
          isPrivate: false
          tags: []
        ) {
          page {
            id
            path
            title
          }
          responseResult {
            succeeded
            errorCode
            message
          }
        }
      }
    }
    '''
    
    variables = {
        "id": page_id,
        "content": content,
        "description": description
    }
    
    payload = json.dumps({
        "query": query,
        "variables": variables
    }).encode('utf-8')
    
    req = urllib.request.Request(
        WIKI_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WIKI_KEY}"
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get_page_id_by_path(path: str) -> int:
    """Find page ID by path."""
    query = json.dumps({
        "query": "{ pages { list { id path title } } }"
    }).encode()
    
    req = urllib.request.Request(
        WIKI_URL,
        data=query,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WIKI_KEY}"
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        pages = data.get('data', {}).get('pages', {}).get('list', [])
        for p in pages:
            if p.get('path') == path:
                return p.get('id')
    return None

# Usage: Update existing page
with open('wiki_rpc_article.md', 'r', encoding='utf-8') as f:
    content = f.read()

page_id = get_page_id_by_path("tech/api/rpc")
if page_id:
    result = update_wiki_page(
        page_id=page_id,
        content=content,
        description="RPC协议全面指南，涵盖架构、框架对比、协议设计、性能优化等"
    )
    print(f"Updated: https://<wiki-url>/tech/api/rpc")
```

## Internal Link Management

### Find and Update References

When a new wiki page is created, find existing references to it in other pages and update them to internal links.

**Process:**
1. Search all pages for plain text references to the new page title
2. Update matching references to use internal wiki links
3. Use absolute paths (`/path/to/page`) to ensure correct resolution

**Example:**
- Before: `| 《关键对话》 | 科里·帕特森 | 高风险对话的沟通技巧 |`
- After: `| [关键对话](/books/crucial-conversations) | 科里·帕特森 | 高风险对话的沟通技巧 |`

**Implementation:**
```python
import json
import urllib.request

def find_and_update_references(wiki_url: str, wiki_key: str, 
                                page_title: str, page_path: str) -> list:
    """
    Find all pages referencing page_title and update to internal links.
    
    Args:
        wiki_url: Wiki.js GraphQL endpoint
        wiki_key: API key
        page_title: Title of the new page (e.g., "关键对话")
        page_path: Path of the new page (e.g., "books/crucial-conversations")
    
    Returns:
        List of updated page paths
    """
    updated_pages = []
    
    # Step 1: List all pages
    list_query = json.dumps({
        "query": "{ pages { list { id path title } } }"
    }).encode()
    
    req = urllib.request.Request(
        wiki_url,
        data=list_query,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {wiki_key}"
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
        pages = data.get('data', {}).get('pages', {}).get('list', [])
    
    # Step 2: Check each page for references
    for page in pages:
        page_id = page.get('id')
        page_path_current = page.get('path')
        
        # Skip the page itself
        if page_path_current == page_path:
            continue
        
        # Get page content
        content_query = json.dumps({
            "query": f"query GetPage {{ pages {{ single(id: {page_id}) {{ id content }} }} }}"
        }).encode()
        
        req = urllib.request.Request(
            wiki_url,
            data=content_query,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {wiki_key}"
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                page_data = data.get('data', {}).get('pages', {}).get('single')
                if not page_data:
                    continue
                
                content = page_data.get('content', '')
                
                # Check for plain text references
                # Match patterns like: 《关键对话》 or 关键对话 (not already linked)
                import re
                
                # Pattern: 《Title》 not already a link
                patterns = [
                    (f'《{page_title}》', f'[{page_title}](/{page_path})'),
                    (f'[{page_title}]()', f'[{page_title}](/{page_path})'),
                    (f'[[{page_title}]]', f'[{page_title}](/{page_path})'),
                ]
                
                modified = False
                for old_text, new_text in patterns:
                    if old_text in content and f'[{page_title}](/{page_path})' not in content:
                        content = content.replace(old_text, new_text)
                        modified = True
                
                if not modified:
                    continue
                
                # Update page
                update_query = '''
                mutation UpdatePage($id: Int!, $content: String!, $description: String!) {
                  pages {
                    update(
                      id: $id
                      content: $content
                      description: $description
                      editor: "markdown"
                      isPublished: true
                      isPrivate: false
                      tags: []
                    ) {
                      page { id path title }
                      responseResult { succeeded errorCode message }
                    }
                  }
                }
                '''
                
                variables = {
                    "id": page_id,
                    "content": content,
                    "description": f"Updated: added internal link to {page_title}"
                }
                
                req = urllib.request.Request(
                    wiki_url,
                    data=json.dumps({"query": update_query, "variables": variables}).encode(),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {wiki_key}"
                    },
                    method='POST'
                )
                
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read().decode())
                    update_data = result.get('data', {}).get('pages', {}).get('update', {})
                    if update_data.get('responseResult', {}).get('succeeded'):
                        updated_pages.append(page_path_current)
                        
        except Exception as e:
            print(f"Error processing page {page_path_current}: {e}")
            continue
    
    return updated_pages
```

**Usage in workflow:**
```python
# After creating a new page
create_result = create_wiki_page(...)

# Update references in other pages
updated = find_and_update_references(
    wiki_url=WIKI_URL,
    wiki_key=WIKI_KEY,
    page_title="关键对话",
    page_path="books/crucial-conversations"
)

print(f"Updated references in {len(updated)} pages: {updated}")
```

**Important Notes:**
- Always use absolute paths (`/path/to/page`) for internal links
- Check that the link doesn't already exist before updating
- Skip the page itself (don't self-reference)
- Handle errors gracefully - some pages may fail to update
- Report which pages were updated
