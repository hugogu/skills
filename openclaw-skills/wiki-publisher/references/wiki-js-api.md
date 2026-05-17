# Wiki.js API Reference

This is a reference companion to the `wiki-publisher` skill. See `SKILL.md` for detailed usage instructions.

## Quick Reference Table

| Operation | Method | Key | Requires Permission |
|-----------|--------|-----|-------------------|
| List pages | Query | None | `pages.list` |
| Get single | Query | `id: Int!` | `pages.read` |
| Create | Mutation | `content`, `title`, `path`, `description` + `tags` | `pages.create` |
| Update | Mutation | `id`, `content`, `title`, `description` + `tags` | `pages.update` |
| Move | Mutation | `id`, `destinationPath` | `pages.move` |
| Delete | Mutation | `id` | `pages.delete` |

## Endpoint

```
POST {WIKI_URL}/graphql
```

## GraphQL Schema Overview

```graphql
type Mutation {
  pages: PageMutation
}

type PageMutation {
  create(
    content: String!
    description: String!
    editor: String
    isPublished: Boolean
    isPrivate: Boolean
    locale: String
    path: String!
    tags: [String]!
    title: String!
  ): PageResponse

  update(
    id: Int!
    content: String!
    description: String!
    editor: String
    isPublished: Boolean
    isPrivate: Boolean
    tags: [String]!
    title: String!
  ): PageResponse

  move(
    id: Int!
    destinationPath: String!
    destinationLocale: String
  ): PageResponse

  delete(id: Int!): PageDeleteResponse
}

type Query {
  pages: PageQuery
}

type PageQuery {
  list: [Page!]!
  single(id: Int!): Page
}

type Page {
  id: Int!
  path: String!
  title: String!
  content: String!
  description: String
  tags: [PageTag!]!
  locale: String
}

type PageResponse {
  page: Page
  responseResult: ResponseResult
}

type ResponseResult {
  succeeded: Boolean!
  errorCode: Int
  message: String
}

type PageDeleteResponse {
  responseResult: ResponseResult
}

type PageTag {
  id: Int
  tag: String
}
```

## Error Codes

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| 0 | Success | — |
| 403 | Forbidden | API key lacks required permission |
| 404 | Not Found | Page ID doesn't exist |
| 409 | Conflict | Path already exists (on create) |
| 422 | Validation Error | Missing required field or type mismatch |
| 500 | Internal Error | Server-side issue |

## Tags Type Note

Wiki.js defines `tags` as `[String]!` (non-null array, elements may be null).
Use `[]` for no tags. Both `["a", "b"]` and `["a", null, "b"]` work.

## Content Verification

After publishing, always verify by fetching the page content back and checking:
1. Content length matches (or is close to) original
2. No LaTeX backslash corruption: check for `rac{` (should be `\frac`), `partial` (should be `\partial`)
3. No truncation at special characters
