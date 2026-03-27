#!/usr/bin/env python3
"""
Wiki Publisher Helper Script

Publish markdown content to Wiki.js via GraphQL API.
"""

import argparse
import json
import os
import sys
import re

import requests


def get_wiki_config():
    """Get wiki configuration from environment."""
    wiki_key = os.environ.get('WIKI_KEY')
    wiki_url = os.environ.get('WIKI_URL', 'https://wiki.hugogu.cn/graphql')
    
    if not wiki_key:
        print("Error: WIKI_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    return wiki_url, wiki_key


def clean_content(content):
    """Remove YAML frontmatter from markdown content."""
    # Remove YAML frontmatter (--- ... ---)
    pattern = r'^---\s*\n.*?\n---\s*\n'
    cleaned = re.sub(pattern, '', content, flags=re.DOTALL)
    return cleaned.strip()


def create_page(wiki_url, wiki_key, title, content, path, description="", tags=None):
    """Create a new wiki page."""
    tags = tags or []
    
    # Clean content - remove YAML frontmatter
    cleaned_content = clean_content(content)
    
    query = """
    mutation {
      pages {
        create(
          content: %s
          description: %s
          editor: "markdown"
          isPublished: true
          isPrivate: false
          locale: "zh"
          path: %s
          tags: %s
          title: %s
        ) {
          page {
            id
            path
            title
          }
        }
      }
    }
    """ % (
        json.dumps(cleaned_content),
        json.dumps(description),
        json.dumps(path),
        json.dumps(tags),
        json.dumps(title)
    )
    
    response = requests.post(
        wiki_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {wiki_key}"
        },
        json={"query": query}
    )
    
    return response.json()


def update_page(wiki_url, wiki_key, page_id, title, content, description=""):
    """Update an existing wiki page."""
    # Clean content - remove YAML frontmatter
    cleaned_content = clean_content(content)
    
    query = """
    mutation {
      pages {
        update(
          id: %d
          content: %s
          description: %s
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
    """ % (
        page_id,
        json.dumps(cleaned_content),
        json.dumps(description)
    )
    
    response = requests.post(
        wiki_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {wiki_key}"
        },
        json={"query": query}
    )
    
    return response.json()


def list_pages(wiki_url, wiki_key):
    """List all wiki pages."""
    query = """
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
    """
    
    response = requests.post(
        wiki_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {wiki_key}"
        },
        json={"query": query}
    )
    
    return response.json()


def main():
    parser = argparse.ArgumentParser(description='Publish content to Wiki.js')
    parser.add_argument('action', choices=['create', 'update', 'list'],
                       help='Action to perform')
    parser.add_argument('--title', '-t', help='Page title')
    parser.add_argument('--path', '-p', help='Page path (e.g., topic/category/name)')
    parser.add_argument('--description', '-d', help='Page description')
    parser.add_argument('--tags', help='Comma-separated tags')
    parser.add_argument('--file', '-f', help='Markdown file to publish')
    parser.add_argument('--content', '-c', help='Content string (alternative to --file)')
    parser.add_argument('--page-id', '-i', type=int, help='Page ID (for update)')
    
    args = parser.parse_args()
    
    wiki_url, wiki_key = get_wiki_config()
    
    if args.action == 'list':
        result = list_pages(wiki_url, wiki_key)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    # Get content
    if args.file:
        with open(args.file, 'r') as f:
            content = f.read()
    elif args.content:
        content = args.content
    else:
        print("Error: Either --file or --content is required", file=sys.stderr)
        sys.exit(1)
    
    # Parse tags
    tags = [t.strip() for t in args.tags.split(',')] if args.tags else []
    
    if args.action == 'create':
        if not args.title or not args.path:
            print("Error: --title and --path are required for create", file=sys.stderr)
            sys.exit(1)
        
        result = create_page(
            wiki_url, wiki_key,
            args.title, content, args.path,
            args.description or "", tags
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.action == 'update':
        if not args.page_id or not args.title:
            print("Error: --page-id and --title are required for update", file=sys.stderr)
            sys.exit(1)
        
        result = update_page(
            wiki_url, wiki_key,
            args.page_id, args.title, content,
            args.description or ""
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
