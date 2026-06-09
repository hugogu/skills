---
name: wiki-publisher
description: |
  Publish markdown content to Wiki.js via GraphQL API. Handles all CRUD operations: create, update, list, get, move, and delete. Focuses on API interaction, authentication, error handling, and troubleshooting. Content formatting is the responsibility of the wiki-writer skill — this skill expects pre-formatted markdown.
triggers:
  - "publish to wiki"
  - "create wiki page"
  - "update wiki page"
  - "sync to wiki.js"
  - "upload to wiki"
metadata:
  runtime: script
  env:
    - name: WIKI_KEY
      description: "Wiki.js API token (generate in Admin > API Access)"
      required: true
      credential: true
    - name: WIKI_URL
      description: "Wiki.js GraphQL endpoint, e.g. https://wiki.example.com"
      required: true
      default: "https://wiki.hugogu.cn"
---

# Wiki Publisher

Publish markdown content to Wiki.js via its GraphQL API. This skill handles **API operations only** — it expects pre-formatted content from the **wiki-writer** skill.

---

## 1. Prerequisites

### 1.1 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WIKI_KEY` | ✅ Yes (credential) | Wiki.js API token. Generate in Admin → API Access. |
| `WIKI_URL` | ✅ Yes | Wiki.js base URL (default: `https://wiki.hugogu.cn`) |

### 1.2 API Key Permissions

The API key must have the following permissions in Wiki.js Admin → API Access:

| Permission | Required For |
|------------|-------------|
| `pages.list` | Querying/listing pages |
| `pages.read` | Reading page content |
| `pages.create` | Creating new pages |
| `pages.update` | Updating existing pages (does NOT need create) |
| `pages.move` | Moving/renaming pages |
| `pages.delete` | Deleting pages |
| `pages.export` | Exporting pages |

> ⚠️ **`pages.list` alone is NOT enough for write operations.** If you get `Forbidden` errors, regenerate the API key with proper permissions.

### 1.3 Tool Dependencies

- Node.js with native `fetch` (v18+) — no external packages required
- Or Python 3 with `requests` library

---

## 2. API Endpoint

```
POST {WIKI_URL}/graphql
Headers:
  Content-Type: application/json
  Authorization: Bearer {WIKI_KEY}
Body: JSON with "query" and "variables" fields
```

---

## 3. CRITICAL: GraphQL Variable Binding

### ⚠️ Never Interpolate Content into Query Strings

The **#1 cause of failures** is incorrect string handling.

#### ❌ WRONG — Direct interpolation
```javascript
// WILL FAIL — quotes, newlines, backslashes in markdown break this
const query = `mutation { pages { create(content: "${rawContent}") { id } } }`;
```

The first `"` or newline in the markdown content will break the GraphQL query.

#### ✅ CORRECT — Use GraphQL Variables
```javascript
const query = `
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
      page { id path title }
      responseResult { succeeded errorCode message }
    }
  }
}
`;

const variables = {
  content: rawContent,   // Raw markdown — JSON.stringify handles escaping
  title: "Page Title",
  path: "category/page-name"
};

const body = JSON.stringify({ query, variables });
```

**Why this works:**
- `JSON.stringify()` auto-escapes quotes (`"` → `\"`), newlines (`\n`), backslashes, and Unicode
- GraphQL runtime deserializes variables as native types
- No manual string concatenation

---

## 4. API Operations

### 4.1 List Pages

Query all pages (or search by path pattern):

```graphql
query ListPages {
  pages {
    list {
      id
      path
      title
    }
  }
}
```

**Special note:** Wiki.js does not support filtering by path in the API. To find a page by path, list all and filter client-side.

### 4.2 Get Single Page

Retrieve page content by numeric ID:

```graphql
query GetPage($id: Int!) {
  pages {
    single(id: $id) {
      id
      title
      path
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

> ⚠️ `pages.single` requires numeric `id` — you CANNOT query by path directly. Always list first to get the ID.

**Alternative: Query by path via `pages.list` with client-side filtering**

If you only know the path and want to avoid listing all pages, use `pages.list` with a path filter in the query string (if supported by your Wiki.js version) or filter client-side:

```graphql
query GetPageByPath {
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

Then filter: `pages.find(p => p.path === 'your/path')`

### 4.3 Create Page

```graphql
mutation CreatePage(
  $content: String!
  $title: String!
  $path: String!
  $description: String!
  $tags: [String]!
) {
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
```

**Variables:**
```json
{
  "content": "# Page Title\n\nContent...",
  "title": "Page Title",
  "path": "category/page-name",
  "description": "Brief description of the page",
  "tags": ["tag1", "tag2"]
}
```

**Required fields for `create`:**
- `content` (`String!`) — Raw markdown
- `title` (`String!`) — Page title
- `path` (`String!`) — URL path (kebab-case, no leading slash)
- `description` (`String!`) — Can be empty string `""`
- `tags` (`[String]!`) — Array of strings; pass `[]` for no tags
- `editor` — Always `"markdown"`
- `isPublished` — Always `true`
- `isPrivate` — Always `false`
- `locale` — Always `"zh"`

### 4.4 Update Page

```graphql
mutation UpdatePage(
  $id: Int!
  $content: String!
  $title: String!
  $description: String!
  $tags: [String]!
) {
  pages {
    update(
      id: $id
      content: $content
      title: $title
      description: $description
      tags: $tags
      editor: "markdown"
      isPublished: true
      isPrivate: false
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
  "id": 123,
  "content": "# Updated content...",
  "title": "Updated Title",
  "description": "Updated description",
  "tags": ["new-tag"]
}
```

> ⚠️ `update` requires ALL of: `content`, `title`, `description`, `tags` — even if only changing one field. Omitting any will result in an empty/null value.

### 4.5 Delete Page

```graphql
mutation DeletePage($id: Int!) {
  pages {
    delete(id: $id) {
      responseResult {
        succeeded
        errorCode
        message
      }
    }
  }
}
```

### 4.6 Move Page

Change a page's path (URL):

```graphql
mutation MovePage($id: Int!, $path: String!) {
  pages {
    move(
      id: $id
      destinationPath: $path
      destinationLocale: "zh"
    ) {
      page { id path title }
      responseResult { succeeded errorCode message }
    }
  }
}
```

**Variables:**
```json
{
  "id": 123,
  "path": "new/category/page-name"
}
```

---

## 5. Response Handling

### 5.1 Success Response

```json
{
  "data": {
    "pages": {
      "update": {
        "page": {
          "id": 590,
          "path": "history/usa/index",
          "title": "美国历史"
        },
        "responseResult": {
          "succeeded": true,
          "errorCode": 0,
          "message": "Page has been updated."
        }
      }
    }
  }
}
```

### 5.2 Error Responses

| HTTP Status | GraphQL Error | Cause | Fix |
|-------------|---------------|-------|-----|
| 200 | `{"message":"Forbidden"}` | API key lacks `pages.create` or `pages.update` permission | Regenerate API key in Admin with proper scopes |
| 200 | `Validation error` | Missing required field or type mismatch | Check all required fields are present |
| 200 | `Variable $content of type String!` | Content parameter wrong type | Ensure content is a string, not array/object |
| 401 | `Unauthorized` | Invalid or expired API key | Check `WIKI_KEY` env var, regenerate if needed |
| 400 | `Parse error` | Malformed GraphQL query | Check query syntax, variable definitions |

### 5.3 Verifying Success

Always check both the HTTP status AND the response object:

```javascript
const data = await res.json();

if (data.errors) {
  // GraphQL-level error
  console.error('GraphQL Errors:', data.errors);
  throw new Error(`GraphQL error: ${data.errors[0].message}`);
}

const result = data.data?.pages?.create || data.data?.pages?.update;
if (!result?.responseResult?.succeeded) {
  // Operation-level failure
  console.error('Operation failed:', result?.responseResult);
  throw new Error(`API returned succeeded=false: ${result?.responseResult?.message}`);
}

// Success
console.log('Page:', result.page.path, '(ID:', result.page.id, ')');
```

### 5.4 Content Verification

After create/update, verify content was written correctly:

```javascript
const verify = await fetch(WIKI_URL + '/graphql', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${WIKI_KEY}` },
  body: JSON.stringify({
    query: `query($id: Int!) { pages { single(id: $id) { content } } }`,
    variables: { id: pageId }
  })
});
const verified = await verify.json();
const savedContent = verified.data?.pages?.single?.content;

// Check for LaTeX corruption
if (savedContent.includes('rac{') || savedContent.includes('\\[')) {
  console.warn('⚠️ Possible LaTeX corruption detected in saved content');
}
```

---

## 6. Error Recovery

### 6.1 Permission Denied (Forbidden)

**Symptoms:**
- HTTP 200, but `errors: [{"message": "Forbidden"}]`
- `responseResult.succeeded = false` with `errorCode: 403`

**Actions:**
1. Check API key prefix (first 20 chars) matches the one in Wiki.js Admin
2. In Wiki.js Admin → API Access → Edit key → enable `pages.create`, `pages.update`
3. If the key is expired, generate a new one

### 6.2 Content Not Found After Create/Update

**Symptoms:** API returns success but page content doesn't reflect changes.

**Actions:**
1. Verify the page ID is correct (list all pages to confirm)
2. Check for LaTeX backslash corruption during transmission (see 5.4)
3. Check that the content was sent as a GraphQL variable, not interpolated
4. If the content was truncated (>100KB), split into smaller pages

### 6.3 LaTeX Content Corruption

**Symptoms:** `\frac` displayed as `rac`, `\partial` as `partial`, or formulas fail to render.

**Causes:**
- Backslashes being eaten during transmission (shell escaping, JSON double-escaping, or GraphQL block string normalization)
- Content passed through shell before reaching the HTTP request

**Solution:**
- Always base64-encode content or use proper variable binding via JSON.stringify
- NEVER pipe content through shell arguments
- After publishing, always verify by fetching the page content back and comparing

### 6.4 Unexpected Stale Page ID

If pages were created/deleted/recreated, the numeric IDs shift. Always re-list pages before update operations to get the current ID.

---

## 7. Reference Implementation

### Node.js (no dependencies)

```javascript
const WIKI_URL = 'https://wiki.hugogu.cn';
const WIKI_KEY = process.env.WIKI_KEY;
const fs = require('fs');

async function publishPage(content, title, path, description = '', tags = []) {
  // Step 1: Check if page exists
  const listRes = await fetch(`${WIKI_URL}/graphql`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${WIKI_KEY}` },
    body: JSON.stringify({
      query: `{ pages { list { id path title } } }`
    })
  });
  const listData = await listRes.json();
  const pages = listData.data?.pages?.list || [];
  const existing = pages.find(p => p.path === path);

  // Step 2: Build the mutation
  if (existing) {
    // Update
    const query = `
      mutation UpdatePage($id: Int!, $c: String!, $t: String!, $d: String!, $tags: [String]!) {
        pages { update(id: $id, content: $c, title: $t, description: $d, tags: $tags, editor: "markdown", isPublished: true, isPrivate: false) {
          page { id path title } responseResult { succeeded errorCode message }
        }}
      }
    `;
    const res = await fetch(`${WIKI_URL}/graphql`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${WIKI_KEY}` },
      body: JSON.stringify({
        query,
        variables: { id: existing.id, c: content, t: title, d: description, tags }
      })
    });
    const data = await res.json();
    if (data.errors || !data.data?.pages?.update?.responseResult?.succeeded) {
      throw new Error(data.errors?.[0]?.message || data.data?.pages?.update?.responseResult?.message);
    }
    return { action: 'updated', id: existing.id, path, url: `${WIKI_URL}/zh/${path}` };
  } else {
    // Create
    const query = `
      mutation CreatePage($c: String!, $t: String!, $p: String!, $d: String!, $tags: [String]!) {
        pages { create(content: $c, title: $t, path: $p, description: $d, tags: $tags, editor: "markdown", isPublished: true, isPrivate: false, locale: "zh") {
          page { id path title } responseResult { succeeded errorCode message }
        }}
      }
    `;
    const res = await fetch(`${WIKI_URL}/graphql`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${WIKI_KEY}` },
      body: JSON.stringify({
        query,
        variables: { c: content, t: title, p: path, d: description, tags }
      })
    });
    const data = await res.json();
    if (data.errors || !data.data?.pages?.create?.responseResult?.succeeded) {
      throw new Error(data.errors?.[0]?.message || data.data?.pages?.create?.responseResult?.message);
    }
    return { action: 'created', id: data.data.pages.create.page.id, path, url: `${WIKI_URL}/zh/${path}` };
  }
}

// Usage
// const result = await publishPage(content, 'Page Title', 'category/page-name');
// console.log(`✅ ${result.action}: ${result.url}`);
```

### Python (with requests)

```python
import json
import os
import requests

WIKI_URL = os.environ['WIKI_URL'].rstrip('/') + '/graphql'
WIKI_KEY = os.environ['WIKI_KEY']

def publish_page(content, title, path, description='', tags=None):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {WIKI_KEY}'
    }
    
    # Check if page exists
    list_query = '{ pages { list { id path title } } }'
    resp = requests.post(WIKI_URL, headers=headers, json={'query': list_query})
    pages = resp.json().get('data', {}).get('pages', {}).get('list', [])
    existing = next((p for p in pages if p['path'] == path), None)
    
    if existing:
        mutation = '''
        mutation UpdatePage($id: Int!, $c: String!, $t: String!, $d: String!, $tags: [String]!) {
            pages {
                update(id: $id, content: $c, title: $t, description: $d, tags: $tags,
                       editor: "markdown", isPublished: true, isPrivate: false) {
                    page { id path title }
                    responseResult { succeeded errorCode message }
                }
            }
        }
        '''
        variables = {
            'id': existing['id'],
            'c': content,
            't': title,
            'd': description or title,
            'tags': tags or []
        }
        resp = requests.post(WIKI_URL, headers=headers,
                             json={'query': mutation, 'variables': variables})
        result = resp.json()
        if result.get('errors'):
            raise Exception(result['errors'][0]['message'])
        return {'action': 'updated', 'id': existing['id'], 'path': path}
    else:
        mutation = '''
        mutation CreatePage($c: String!, $t: String!, $p: String!, $d: String!, $tags: [String]!) {
            pages {
                create(content: $c, title: $t, path: $p, description: $d, tags: $tags,
                       editor: "markdown", isPublished: true, isPrivate: false, locale: "zh") {
                    page { id path title }
                    responseResult { succeeded errorCode message }
                }
            }
        }
        '''
        variables = {
            'c': content,
            't': title,
            'p': path,
            'd': description or title,
            'tags': tags or []
        }
        resp = requests.post(WIKI_URL, headers=headers,
                             json={'query': mutation, 'variables': variables})
        result = resp.json()
        if result.get('errors'):
            raise Exception(result['errors'][0]['message'])
        return {'action': 'created', 'id': result['data']['pages']['create']['page']['id'], 'path': path}

# Usage
# result = publish_page(content, 'Page Title', 'category/page-name')
# print(f"✅ {result['action']}: {result['path']}")
```

---

## 8. Quick Reference

| Operation | Query Type | Key Parameters | Error-prone Fields |
|-----------|-----------|----------------|-------------------|
| List all | Query | None | N/A |
| Get single | Query | `id: Int!` | Must use numeric ID, not path |
| Get by path | Query | None | Use `pages.list` + client-side filter |
| Create | Mutation | `content`, `title`, `path`, `description`, `tags` | All required, `tags` must be `[String]!` not `[String!]!` |
| Update | Mutation | `id`, `content`, `title`, `description`, `tags` | Must pass ALL fields, ID must be correct |
| Move | Mutation | `id`, `destinationPath` | Destination must not exist |
| Delete | Mutation | `id` | Destructive, confirm first |

### Tags Type Quirk

Wiki.js expects `[String]!` (non-null array, nullable elements), NOT `[String!]!` (array of non-null strings):

```json
// ✅ Correct
"tags": ["tag1", "tag2", null]   // null elements OK

// ❌ Wrong
"tags": ["tag1", "tag2"]         // Works but technically [String]! not [String!]!
```

When using GraphQL variables, `[]` and `["a", "b"]` both work. The type annotation is `[String]!` in the schema.

---

## 9. Workflow Summary

```
┌─────────────────────────────────────┐
│      wiki-writer skill              │
│                                     │
│  Writes markdown content →          │
│  Saves to wiki_articles/{path}.md   │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│      wiki-publisher skill           │
│                                     │
│  1. Read local .md file             │
│  2. List existing pages to find ID  │
│  3. If exists → Update mutation     │
│     If new    → Create mutation     │
│  4. Verify content after publish    │
│  5. Return URL and page ID          │
└─────────────────────────────────────┘
```

---

## Reference

- Wiki.js API Documentation: https://docs.requarks.io/dev/api
- GraphQL Spec: https://spec.graphql.org/October2021/
- KaTeX Error Handling: https://katex.org/docs/issues.html
