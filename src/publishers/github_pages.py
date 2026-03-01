"""GitHub Pages publisher - Publishes digests to a GitHub Pages blog repository."""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

import yaml
from git import Repo

from src.core.interfaces import BasePublisher
from src.core.models import DigestResult


class GitHubPagesPublisher(BasePublisher):
    """Publishes a DigestResult to a separate GitHub Pages repository."""
    
    def __init__(
        self,
        repo_url: str,
        local_clone_path: str = "/tmp/rss-digest-blog",
        content_dir: str = "_posts"
    ):
        self.repo_url = repo_url
        self.local_clone_path = Path(local_clone_path)
        self.content_dir = content_dir
        
    def _ensure_repo(self) -> Repo:
        """Clones the repo if it doesn't exist, or pulls latest if it does."""
        if self.local_clone_path.exists():
            repo = Repo(self.local_clone_path)
            origin = repo.remotes.origin
            origin.pull()
            return repo
        else:
            self.local_clone_path.parent.mkdir(parents=True, exist_ok=True)
            return Repo.clone_from(self.repo_url, self.local_clone_path)

    def publish(self, digest: DigestResult, **kwargs) -> bool:
        """
        Publish the digest to the GitHub Pages repository.
        
        Args:
            digest: The DigestResult to publish
            **kwargs: Additional options (commit_message, layout)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            repo = self._ensure_repo()
            
            # GitHub Pages (Jekyll) expects posts in _posts folder
            # with format YYYY-MM-DD-title.md
            posts_dir = self.local_clone_path / self.content_dir
            posts_dir.mkdir(exist_ok=True)
            
            # Format filename
            date_str = digest.date.strftime('%Y-%m-%d')
            safe_title = "".join([c if c.isalnum() else "-" for c in digest.title]).lower()
            # Remove consecutive dashes and trim
            safe_title = "-".join(filter(None, safe_title.split("-")))
            filename = f"{date_str}-{safe_title}.md"
            file_path = posts_dir / filename
            
            # Build frontmatter for Jekyll
            layout = kwargs.get("layout", "post")
            frontmatter = {
                "layout": layout,
                "title": digest.title,
                "date": digest.date.isoformat(),
                "config": digest.config_name,
                **digest.metadata
            }
            
            # Generate content with YAML frontmatter
            content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{digest.markdown_body}"
            
            # Write file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            # Git commit and push
            repo.index.add([str(file_path.relative_to(self.local_clone_path))])
            
            commit_message = kwargs.get("commit_message", f"Add digest: {digest.title}")
            repo.index.commit(commit_message)
            
            origin = repo.remotes.origin
            origin.push()
            
            return True
            
        except Exception as e:
            # Log error but don't crash - caller should handle
            print(f"Error publishing to GitHub Pages: {e}")
            return False
