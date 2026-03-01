"""
FileSystem Publisher - Saves DigestResult as Markdown with YAML frontmatter.
"""

import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.core.interfaces import BasePublisher
from src.core.models import DigestResult


class FileSystemPublisher(BasePublisher):
    """Saves a DigestResult as a Markdown file with YAML frontmatter."""

    def __init__(self, output_dir: str = "content/digests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def publish(self, digest: DigestResult, output_path: Optional[str] = None, **kwargs) -> bool:
        """
        Save digest as Markdown file with YAML frontmatter.

        Args:
            digest: The DigestResult to save
            output_path: Optional custom file path (overrides default naming)
            **kwargs: Additional options

        Returns:
            True if saved successfully
        """
        frontmatter = {
            "title": digest.title,
            "date": digest.date.isoformat(),
            "config": digest.config_name,
            "sources_analyzed": digest.sources_analyzed,
            **digest.metadata
        }

        content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{digest.markdown_body}"

        if output_path:
            file_path = Path(output_path)
        else:
            filename = f"{digest.date.strftime('%Y-%m-%d')}-{digest.config_name.lower().replace(' ', '-')}.md"
            file_path = self.output_dir / filename

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True
