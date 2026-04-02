---
name: wiki-publisher
description: Publish markdown content to Wiki.js with proper formatting and metadata. Use when user wants to create or update wiki pages, convert notes/articles to wiki format, or publish content to a Wiki.js instance. Handles API authentication, content formatting (removing YAML frontmatter), automatic tagging, and path suggestions.
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

#### ✅ CORRECT - Use GraphQL Variables

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
    }
  }
}
'''

variables = {
    "content": raw_content,  # Pass raw content, no preprocessing
    "title": "Page Title",
    "path": "category/page-name"
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

**Type Requirements:**
- `$content`: `String!` - Required, raw markdown
- `$title`: `String!` - Required
- `$path`: `String!` - Required, URL path
- `$description`: `String!` - Required
- `$tags`: `[String]!` - Required non-null array (elements may be null)

### Update Page

```graphql
mutation UpdatePage($id: Int!, $content: String!) {
  pages {
    update(
      id: $id
      content: $content
      description: "Updated description"
      editor: "markdown"
    ) {
      page {
        id
        path
        title
      }
    }
  }
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

**Solution:** Use GraphQL Variables (recommended) or escape each `` ` `` as `\``.

#### Pitfall 2: JSON Double-Escaping

```python
# ❌ WRONG - manual escape then JSON serialize
content_escaped = content.replace('"', '\\"')
payload = json.dumps({"query": f'..."{content_escaped}"...'})
# Results in: \\\" (double escaped)

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

## Workflow

1. **Extract content** - Get markdown from user or generate it
2. **Clean formatting** - Remove YAML frontmatter if present
3. **Suggest metadata** - Propose path, tags, description
4. **Confirm with user** - Show proposed wiki location
5. **Publish** - Run `{baseDir}/scripts/publish_to_wiki.py publish <file.md> --path <wiki/path>` or execute GraphQL mutation directly using **Variables**
6. **Return link** - Provide wiki page URL

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ValidationError: Variable $content... invalid value` | String escaping issue | Use Variables + json.dumps |
| `GraphQLError: Variable $tags of type [String!]` | Tags type mismatch | Use `[String]!` not `[String!]` (Wiki.js expects non-null array, elements can be null) |
| `Unauthorized` | Invalid API key | Check WIKI_KEY env var |
| `Page already exists` | Path conflict | Use update mutation or different path |

## Example: Complete Python Implementation

```python
import json
import os
import requests

WIKI_URL = os.environ["WIKI_URL"]   # e.g. https://your-wiki.example.com/graphql
WIKI_KEY = os.environ["WIKI_KEY"]

def create_wiki_page(content: str, title: str, path: str, 
                     description: str = "", tags: list = None) -> dict:
    """
    Create a Wiki.js page using GraphQL API.
    
    Args:
        content: Raw markdown content (will be auto-escaped)
        title: Page title
        path: URL path (e.g., "tech/security/topic")
        description: Page description
        tags: List of tag strings
    
    Returns:
        API response JSON
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
        }
      }
    }
    '''
    
    variables = {
        "content": content,  # Raw content - json.dumps handles escaping
        "title": title,
        "path": path,
        "description": description or title,
        "tags": tags or []
    }
    
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
    
    return response.json()

# Usage
with open('article.md', 'r') as f:
    content = f.read()

result = create_wiki_page(
    content=content,
    title="反爬虫技术详解",
    path="tech/security/anti-crawler",
    description="反爬虫与反反爬虫技术详解",
    tags=["网络安全", "爬虫"]
)

base_url = WIKI_URL.replace('/graphql', '')
print(f"Created: {base_url}/{result['data']['pages']['create']['page']['path']}")
```

## Reference

- [GraphQL Spec - String Type](https://spec.graphql.org/October2021/#sec-String)
- See `references/wiki-js-api.md` for complete GraphQL schema
- Wiki.js API Documentation: https://docs.requarks.io/dev/api

---

**Remember:** Always use GraphQL Variables for content. Never interpolate strings directly into GraphQL queries.
