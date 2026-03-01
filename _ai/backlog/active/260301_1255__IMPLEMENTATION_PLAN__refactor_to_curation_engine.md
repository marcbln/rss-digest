---
filename: "_ai/backlog/active/260301_1255__IMPLEMENTATION_PLAN__refactor_to_curation_engine.md"
title: "Refactor RSS Digest into Modular Content Curation Engine"
createdAt: 2026-03-01 12:55
updatedAt: 2026-03-01 12:55
status: draft
priority: high
tags: [refactoring, architecture, cli, solid]
estimatedComplexity: complex
documentType: IMPLEMENTATION_PLAN
---

## 1. Problem Statement
The current `rss-digest` architecture is a monolithic script that tightly couples fetching RSS feeds, processing them with an LLM, and dispatching an email. To support future data sources (YouTube, GitHub, Twitter) and new publishing destinations (GitHub Pages, Static Site Generators), we need to refactor the application into a highly modular **Content Curation Engine**. 

We will split the application into two distinct phases:
1. **Generate**: Fetch content (via plugins), process it via an LLM, and output a standard Markdown file with YAML frontmatter.
2. **Publish**: Read the generated Markdown file and publish it to the designated destinations (e.g., via Email).

## 2. Project Environment
- Project Name: rss-digest
- Frontend root: n/a
- Backend root: src

---

## Phase 1: Foundation & Core Interfaces
Establish the foundation of the refactoring by defining clear domain models and Abstract Base Classes (Interfaces) following SOLID principles.

### Code Changes

```toml
[MODIFY] pyproject.toml
# Ensure the following dependencies are present in[project.dependencies]
dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.7.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "markdown>=3.5.0", # Used to convert the MD body to HTML for emails
    "python-dotenv>=1.0.0",
    # (preserve existing dependencies like feedparser, openai/litellm, etc.)
]

[project.scripts]
rss-digest = "src.cli:main"
```

```python
[NEW FILE] src/core/models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class ContentItem(BaseModel):
    """Standardized format for incoming data (RSS, YouTube, Git)."""
    title: str
    url: str
    content: str
    source: str
    published_date: Optional[datetime] = None

class DigestResult(BaseModel):
    """Standardized format for LLM output ready to be saved/published."""
    title: str
    date: datetime
    config_name: str
    sources_analyzed: int
    markdown_body: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

```python
[NEW FILE] src/core/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import ContentItem, DigestResult

class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self, **kwargs) -> List[ContentItem]:
        """Fetch data from a source and return a list of ContentItems."""
        pass

class BasePublisher(ABC):
    @abstractmethod
    def publish(self, digest: DigestResult, **kwargs) -> bool:
        """Publish the digest result to a specific destination."""
        pass
```

```python[NEW FILE] src/config.py
# Centralized CLI settings
CLI_CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
}
```

---

## Phase 2: Refactoring Data Gathering & Digestion (Generate)
Refactor the existing RSS fetching and LLM processing logic to conform to the new models, and implement a FileSystem publisher to save the output as Markdown.

### Code Changes

```python[NEW FILE] src/fetchers/rss.py
import feedparser
from typing import List, Dict
from datetime import datetime
from src.core.interfaces import BaseFetcher
from src.core.models import ContentItem

class RSSFetcher(BaseFetcher):
    def fetch(self, feeds: Dict[str, str], days_lookback: int) -> List[ContentItem]:
        # TODO: Move the existing feedparser logic from src/rss_fetcher.py here.
        # Ensure it maps the parsed entries into the ContentItem Pydantic model.
        items = []
        # ... logic ...
        return items
```

```python
[NEW FILE] src/publishers/file_system.py
import os
import yaml
from pathlib import Path
from src.core.interfaces import BasePublisher
from src.core.models import DigestResult

class FileSystemPublisher(BasePublisher):
    """Saves a DigestResult as a Markdown file with YAML frontmatter."""
    
    def __init__(self, output_dir: str = "content/digests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def publish(self, digest: DigestResult, **kwargs) -> bool:
        frontmatter = {
            "title": digest.title,
            "date": digest.date.isoformat(),
            "config": digest.config_name,
            "sources_analyzed": digest.sources_analyzed,
            **digest.metadata
        }
        
        content = f"---\n{yaml.dump(frontmatter)}---\n\n{digest.markdown_body}"
        filename = f"{digest.date.strftime('%Y-%m-%d')}-{digest.config_name}.md"
        
        file_path = self.output_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return True
```

```python
[MODIFY] src/llm_processor.py
# TODO: Refactor the existing process() function to accept a `List[ContentItem]` 
# and return a `DigestResult` object instead of a raw string.
```

---

## Phase 3: Refactoring Publishing (Email)
Create a command to read a saved Markdown digest and push it out via email.

### Code Changes

```python
[NEW FILE] src/publishers/email.py
import markdown
from src.core.interfaces import BasePublisher
from src.core.models import DigestResult
# TODO: Import existing SMTP logic from src/email_sender.py

class EmailPublisher(BasePublisher):
    def publish(self, digest: DigestResult, **kwargs) -> bool:
        # 1. Convert Markdown body to HTML
        html_content = markdown.markdown(digest.markdown_body)
        
        # 2. Map data to existing email_template.html
        # 3. Send email using the existing SMTP logic
        
        return True
```

---

## Phase 4: CLI Orchestration
Wire everything together using `Typer`, following project conventions.

### Code Changes

```python
[NEW FILE] src/commands/generate_cmd.py
import typer
from rich.console import Console
from src.fetchers.rss import RSSFetcher
from src.publishers.file_system import FileSystemPublisher
# TODO: Import config loader and LLM processor

app = typer.Typer(help="Generate digests and save as Markdown")
console = Console()

@app.command()
def run(config_name: str = typer.Option(..., "--config", "-c", help="Config name to run")):
    console.print(f"Generating digest for [bold cyan]{config_name}[/bold cyan]...")
    # 1. Load TOML config
    # 2. rss_fetcher = RSSFetcher() -> get ContentItems
    # 3. digest = llm_processor.process(items, ...)
    # 4. fs_publisher = FileSystemPublisher() -> save Markdown
    console.print("[bold green]Digest generated and saved successfully![/bold green]")
```

```python
[NEW FILE] src/commands/publish_cmd.py
import typer
import yaml
from pathlib import Path
from rich.console import Console
from src.core.models import DigestResult
from src.publishers.email import EmailPublisher
from datetime import datetime

app = typer.Typer(help="Publish generated digests (e.g., via Email)")
console = Console()

@app.command()
def email(file_path: Path = typer.Argument(..., help="Path to markdown digest file")):
    console.print(f"Publishing {file_path} via Email...")
    
    # 1. Read Markdown file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 2. Parse YAML Frontmatter & Body
    parts = content.split("---", 2)
    frontmatter = yaml.safe_load(parts[1])
    markdown_body = parts[2].strip()
    
    # 3. Reconstruct DigestResult
    digest = DigestResult(
        title=frontmatter["title"],
        date=datetime.fromisoformat(frontmatter["date"]),
        config_name=frontmatter.get("config", "unknown"),
        sources_analyzed=frontmatter.get("sources_analyzed", 0),
        markdown_body=markdown_body,
        metadata={k: v for k, v in frontmatter.items() if k not in["title", "date", "config", "sources_analyzed"]}
    )
    
    # 4. Publish
    publisher = EmailPublisher()
    publisher.publish(digest)
    
    console.print("[bold green]Digest emailed successfully![/bold green]")
```

```python
[NEW FILE] src/cli.py
import typer
from src.config import CLI_CONTEXT_SETTINGS
from src.commands import generate_cmd, publish_cmd

app = typer.Typer(context_settings=CLI_CONTEXT_SETTINGS)

app.add_typer(generate_cmd.app, name="generate")
app.add_typer(publish_cmd.app, name="publish")

def main():
    app()

if __name__ == "__main__":
    main()
```

```text
[DELETE] src/main.py
[DELETE] src/rss_fetcher.py
[DELETE] src/email_sender.py
```

---

## Phase 5: Documentation Updates
The `README.md` must be updated to reflect the new commands:

```markdown
[MODIFY] README.md
# Update usage section to:

```bash
# Generate a digest and save it to content/digests/
uv run rss-digest generate --config ai-weekly

# Publish a generated digest via email
uv run rss-digest publish email content/digests/2026-03-01-ai-weekly.md
```
```

---

## Phase 6: Report Generation
Once the AI Coding Agent completes the above phases, it must generate a report.

```yaml
---
filename: "_ai/backlog/reports/260301_1255__IMPLEMENTATION_REPORT__refactor_to_curation_engine.md"
title: "Report: Refactor RSS Digest into Modular Content Curation Engine"
createdAt: YYYY-MM-DD HH:mm
updatedAt: YYYY-MM-DD HH:mm
planFile: "_ai/backlog/active/260301_1255__IMPLEMENTATION_PLAN__refactor_to_curation_engine.md"
project: "rss-digest"
status: completed
filesCreated: 0
filesModified: 0
filesDeleted: 0
tags:[refactoring, architecture, cli, solid]
documentType: IMPLEMENTATION_REPORT
---

1. **Summary**: ...
2. **Files Changed**: ...
3. **Key Changes**: ...
4. **Technical Decisions**: ...
5. **Testing Notes**: ...
6. **Usage Examples**: ...
7. **Documentation Updates**: ...
8. **Next Steps**: ...
```
