#!/usr/bin/env python3
"""
Wiki Publisher Script - 发布内容到 Wiki.js
 Usage: python3 publish_to_wiki.py <file.md> <path> [title] [description]
"""

import os
import sys
import json
import requests

WIKI_URL = "https://wiki.hugogu.cn/graphql"
WIKI_KEY = os.environ.get("WIKI_KEY")

def create_wiki_page(content: str, title: str, path: str, 
                     description: str = "", tags: list = None) -> dict:
    """
    Create a Wiki.js page using GraphQL API.
    """
    # FIXED: tags type changed from [String!] to [String]!
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
        "content": content,
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


def update_wiki_page(page_id: int, content: str, description: str = "") -> dict:
    """
    Update an existing Wiki.js page.
    """
    query = '''
    mutation UpdatePage($id: Int!, $content: String!, $description: String!) {
      pages {
        update(
          id: $id
          content: $content
          description: $description
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
    '''
    
    variables = {
        "id": page_id,
        "content": content,
        "description": description
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


def get_page_by_path(path: str) -> dict:
    """
    Check if a page exists by path.
    """
    query = '''
    query GetPage($path: String!) {
      pages {
        singleByPath(path: $path, locale: "zh") {
          id
          path
          title
        }
      }
    }
    '''
    
    variables = {"path": path}
    
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
    
    result = response.json()
    if result.get("data") and result["data"].get("pages") and result["data"]["pages"].get("singleByPath"):
        return result["data"]["pages"]["singleByPath"]
    return None


def main():
    if not WIKI_KEY:
        print("Error: WIKI_KEY environment variable not set")
        sys.exit(1)
    
    if len(sys.argv) < 3:
        print("Usage: python3 publish_to_wiki.py <file.md> <path> [title] [description]")
        print("Example: python3 publish_to_wiki.py article.md tech/security/guide '安全指南'")
        sys.exit(1)
    
    file_path = sys.argv[1]
    wiki_path = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else None
    description = sys.argv[4] if len(sys.argv) > 4 else ""
    
    # Read content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Extract title from content if not provided
    if not title:
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        if not title:
            title = os.path.basename(file_path)
    
    # Check if page exists
    existing_page = get_page_by_path(wiki_path)
    
    if existing_page:
        print(f"Page exists (ID: {existing_page['id']}), updating...")
        result = update_wiki_page(existing_page['id'], content, description)
        if result.get("data") and result["data"].get("pages") and result["data"]["pages"].get("update"):
            page = result["data"]["pages"]["update"]["page"]
            print(f"✅ Updated: https://wiki.hugogu.cn/{page['path']}")
        else:
            print(f"❌ Update failed: {result}")
            sys.exit(1)
    else:
        print(f"Creating new page at path: {wiki_path}")
        result = create_wiki_page(content, title, wiki_path, description)
        if result.get("data") and result["data"].get("pages") and result["data"]["pages"].get("create"):
            page = result["data"]["pages"]["create"]["page"]
            print(f"✅ Created: https://wiki.hugogu.cn/{page['path']}")
        else:
            print(f"❌ Create failed: {result}")
            sys.exit(1)


if __name__ == "__main__":
    main()