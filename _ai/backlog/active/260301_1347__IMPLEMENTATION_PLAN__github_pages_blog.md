---
filename: "_ai/backlog/active/260301_1347__IMPLEMENTATION_PLAN__github_pages_blog.md"
title: "Publish Digests to GitHub Pages Blog"
createdAt: 2026-03-01 13:47
updatedAt: 2026-03-01 13:47
status: draft
priority: medium
tags: [publishing, github-pages, git, blog]
estimatedComplexity: medium
documentType: IMPLEMENTATION_PLAN
---

## 1. Problem Statement
With the refactoring to a modular Content Curation Engine complete, we now want to publish the generated Markdown digests as an auto-updating blog on GitHub Pages. Over time, the generated content will grow significantly, which could bloat the main `rss-digest` codebase if kept in the same repository.

We need a strategy and implementation to publish these digests seamlessly to a GitHub Pages-enabled repository.

## 2. Architecture & Strategy

**Recommendation: Separate Repository for Content**
Instead of storing the `content/` folder in the main `rss-digest` repository, we will use a dedicated repository (e.g., `rss-digest-blog`) for the blog content. 
- **Why?** It keeps the codebase clean, separates code from data, and leverages GitHub Pages' native Jekyll support.
- **How?** We will create a `GitPublisher` that writes the generated Markdown file into a local clone of the blog repository, commits the new file, and pushes it to GitHub. GitHub Pages will then automatically build and publish the site.

---

## Phase 1: Git Publisher Implementation
Create a new publisher that handles Git operations to commit and push the generated digests.

### Code Changes

```toml
[MODIFY] pyproject.toml
# Add GitPython dependency for programmatic git operations
dependencies = [
    # ... existing ...
    "GitPython>=3.1.40",
]
```

```python
[NEW FILE] src/publishers/github_pages.py
import os
import shutil
from pathlib import Path
from datetime import datetime
from git import Repo
from src.core.interfaces import BasePublisher
from src.core.models import DigestResult

class GitHubPagesPublisher(BasePublisher):
    """Publishes a DigestResult to a separate GitHub Pages repository."""
    
    def __init__(self, repo_url: str, local_clone_path: str = "/tmp/rss-digest-blog"):
        self.repo_url = repo_url
        self.local_clone_path = Path(local_clone_path)
        
    def _ensure_repo(self) -> Repo:
        """Clones the repo if it doesn't exist, or pulls latest if it does."""
        if self.local_clone_path.exists():
            repo = Repo(self.local_clone_path)
            origin = repo.remotes.origin
            origin.pull()
            return repo
        else:
            return Repo.clone_from(self.repo_url, self.local_clone_path)

    def publish(self, digest: DigestResult, **kwargs) -> bool:
        repo = self._ensure_repo()
        
        # GitHub Pages (Jekyll) usually expects posts in a _posts folder
        # with format YYYY-MM-DD-title.md
        posts_dir = self.local_clone_path / "_posts"
        posts_dir.mkdir(exist_ok=True)
        
        # Formatting filename
        date_str = digest.date.strftime('%Y-%m-%d')
        safe_title = "".join([c if c.isalnum() else "-" for c in digest.title]).lower()
        filename = f"{date_str}-{safe_title}.md"
        file_path = posts_dir / filename
        
        # Ensure Frontmatter has layout for Jekyll
        frontmatter = {
            "layout": "post",
            "title": digest.title,
            "date": digest.date.isoformat(),
            "config": digest.config_name,
            **digest.metadata
        }
        
        import yaml
        content = f"---\n{yaml.dump(frontmatter)}---\n\n{digest.markdown_body}"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        # Git Commit and Push
        repo.index.add([str(file_path)])
        repo.index.commit(f"Add digest: {digest.title}")
        origin = repo.remotes.origin
        origin.push()
        
        return True
```

---

## Phase 2: CLI Integration
Integrate the new publisher into the CLI commands.

### Code Changes

```python
[MODIFY] src/commands/publish_cmd.py
# Add a new command for GitHub Pages

from src.publishers.github_pages import GitHubPagesPublisher
import os

@app.command()
def github_pages(
    file_path: Path = typer.Argument(..., help="Path to markdown digest file"),
    repo_url: str = typer.Option(..., "--repo", envvar="BLOG_REPO_URL", help="GitHub Repository URL (e.g., git@github.com:user/blog.git)")
):
    console.print(f"Publishing {file_path} to GitHub Pages repo {repo_url}...")
    
    # 1. Read and parse Markdown file (same as email command)
    # ... existing reading logic ...
    
    # 2. Publish
    publisher = GitHubPagesPublisher(repo_url=repo_url)
    publisher.publish(digest)
    
    console.print("[bold green]Digest pushed to GitHub Pages successfully![/bold green]")
```

```shell
[MODIFY] .env.example
# Add new environment variable
BLOG_REPO_URL=git@github.com:yourusername/rss-digest-blog.git
```

---

## Phase 3: Setup Instructions (User Action Required)
Before this runs successfully, the user needs to set up the blog repository:

1. **Create Repository**: Create a new public repository on GitHub called `rss-digest-blog`.
2. **Enable GitHub Pages**: Go to Settings -> Pages -> Build and deployment -> Source: Deploy from a branch (e.g., `main`).
3. **Choose a Theme**: In the repository settings, select a Jekyll theme (e.g., Minima) so GitHub Pages knows how to render the `_posts/` directory.
4. **Authentication**: Ensure the machine running `rss-digest` has SSH keys configured and added to GitHub to allow `git push` without password prompts.

---

## Phase 4: Report Generation
Once implemented, generate an implementation report.

```yaml
---
filename: "_ai/backlog/reports/260301_1347__IMPLEMENTATION_REPORT__github_pages_blog.md"
title: "Report: Publish Digests to GitHub Pages Blog"
createdAt: YYYY-MM-DD HH:mm
updatedAt: YYYY-MM-DD HH:mm
planFile: "_ai/backlog/active/260301_1347__IMPLEMENTATION_PLAN__github_pages_blog.md"
project: "rss-digest"
status: completed
documentType: IMPLEMENTATION_REPORT
---

# Details...
```
