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

### Create Page

```graphql
mutation {
  pages {
    create(
      content: "# Title\n\nContent..."
      description: "Page description"
      editor: "markdown"
      isPublished: true
      isPrivate: false
      locale: "zh"
      path: "topic/category/page-name"
      tags: ["tag1", "tag2"]
      title: "Page Title"
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

### Update Page

```graphql
mutation {
  pages {
    update(
      id: PAGE_ID
      content: "# Updated Title\n\nUpdated content..."
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
5. **Publish** - Execute GraphQL mutation
6. **Return link** - Provide wiki page URL

## Example Usage

**User:** "Publish this article to Wiki"

**Process:**
1. Analyze content to determine topic/category
2. Suggest path: `topic/thinking-models/jevons-paradox`
3. Generate tags: `["economics", "thinking-models", "counter-intuitive"]`
4. Confirm with user
5. Publish and return: `https://your-wiki-instance.com/topic/thinking-models/jevons-paradox`

## Error Handling

- API failures: Check WIKI_KEY and network connectivity
- Path conflicts: Suggest alternative paths
- Content too large: Consider splitting into multiple pages

## Reference

See `references/wiki-js-api.md` for complete GraphQL schema and examples.
