# RSS Digest - Content Curation Engine

A modular, two-phase content curation system that fetches RSS articles, processes them with AI, and delivers polished digests. **Generate** content in one phase, **publish** it in another—enabling flexible workflows, archival, and multi-channel distribution.

No database, no complexity—just clean architecture, RSS feeds, an LLM, and your inbox.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Fetcher   │────▶│    LLM      │────▶│   Publish   │
│   Plugins   │     │  Processor  │     │  Markdown   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                        ┌─────────────────────┘
                        ▼
                 ┌─────────────┐     ┌─────────────┐
                 │   Publish   │────▶│   Email     │
                 │    Read     │     │   Sender    │
                 │   Command   │     └─────────────┘
                 └─────────────┘
```

**Phase 1: Generate**
- Fetch content from RSS feeds (or future: YouTube, GitHub, Twitter)
- Process with LLM to create curated digest
- Output as Markdown with YAML frontmatter

**Phase 2: Publish**
- Read saved Markdown digest
- Publish to destinations (Email, GitHub Pages, etc.)

## Features

- **Two-Phase Architecture**: Separate content generation from publishing for flexibility
- **Multi-Config Support**: Define multiple TOML configs for different digests
- **Stateless & Simple**: No database, no state tracking, no complex setup
- **AI-Powered Digests**: Uses any OpenAI-compatible LLM API (OpenAI, DeepSeek, OpenRouter, etc.)
- **Email Delivery**: Clean HTML digests sent via any SMTP server
- **Flexible Scheduling**: Run locally, via cron, or GitHub Actions
- **Cost-Effective**: ~$0.007/month with Gemini Flash or DeepSeek (~1 cent!)
- **Hype-Free**: Prompts designed to cut through marketing noise and focus on substance

## Quick Start

```bash
# 1. Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and setup
git clone https://github.com/marcbln/rss-digest.git
cd rss-digest
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys and SMTP settings

# 4. Generate a digest (outputs to content/digests/)
uv run rss-digest generate --config ai-weekly

# 5. Publish the generated digest via email
uv run rss-digest publish email content/digests/2026-03-01-ai-weekly.md
```

## Multi-Config Setup

Configs live in the `configs/` directory as TOML files:

```
configs/
├── ai-weekly.toml              # AI news weekly digest
├── ai-assisted-programming.toml # AI coding tools & workflows
├── tech-daily.toml             # Daily tech news
└── custom.toml                 # Your own custom digest
```

### Available Configs

```bash
# List all available configs
ls configs/

# Generate a specific config
uv run rss-digest generate --config ai-weekly
uv run rss-digest generate --config tech-daily
```

### Creating Your Own Config

Create a new file in `configs/`:

```toml
# configs/my-digest.toml

name = "My Digest"
description = "A custom digest for my interests"
schedule = "weekly"  # daily, weekly, or custom
days_lookback = 7

# Email settings
email_subject = "My Custom Digest"
sender_name = "My Bot"

# RSS Feeds
[feeds]
"Feed Name" = "https://example.com/rss.xml"
"Another Feed" = "https://another.com/feed"

# LLM Prompt
[prompt]
template = """Your custom prompt here...

ARTICLES FROM {date_range} ({article_count} articles):
{article_list}

TASK: Create a digest...
"""
```

## Configuration

### 1. Environment Variables (.env)

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# LLM Provider (OpenAI, DeepSeek, OpenRouter, etc.)
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=           # Optional: for DeepSeek/OpenRouter
LLM_MODEL=gpt-4o-mini      # or deepseek-chat, google/gemini-flash-1.5-8b

# SMTP Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_STARTTLS=true

# Email
RECIPIENT_EMAIL=recipient@example.com
FROM_EMAIL=your-email@gmail.com
EMAIL_SENDER_NAME=RSS Digest
```

### 2. Config Files (configs/*.toml)

Each config defines:
- **RSS feeds** to monitor
- **Schedule** (for documentation)
- **LLM prompt** for digest generation
- **Email subject/sender** names

See `configs/ai-weekly.toml` for a full example.

## Usage

### Generate Command

```bash
# Generate digest for a config
uv run rss-digest generate --config ai-weekly

# Override output directory
uv run rss-digest generate --config ai-weekly --output ./my-digests

# Override lookback period
uv run rss-digest generate --config ai-weekly --days 3

# Limit articles for testing
uv run rss-digest generate --config ai-weekly --limit 5

# Verbose logging
uv run rss-digest generate --config ai-weekly --verbose
```

### Publish Command

```bash
# Publish a generated digest via email
uv run rss-digest publish email content/digests/2026-03-01-ai-weekly.md

# Verbose logging
uv run rss-digest publish email content/digests/2026-03-01-ai-weekly.md --verbose
```

### Cron Scheduling

**Weekly (Mondays at 9 AM):**
```cron
0 9 * * 1 cd /path/to/rss-digest && uv run rss-digest generate --config ai-weekly && uv run rss-digest publish email content/digests/$(date +\%Y-\%m-\%d)-ai-weekly.md
```

**Daily (at 8 AM):**
```cron
0 8 * * * cd /path/to/rss-digest && uv run rss-digest generate --config tech-daily && uv run rss-digest publish email content/digests/$(date +\%Y-\%m-\%d)-tech-daily.md
```

### GitHub Actions

The repo includes a workflow that can be duplicated for each config:

```yaml
# .github/workflows/ai-weekly.yml
name: AI Weekly Digest
on:
  schedule:
    - cron: '0 9 * * 1'  # Mondays at 9 AM
jobs:
  digest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run rss-digest generate --config ai-weekly
      - run: uv run rss-digest publish email content/digests/$(date +%Y-%m-%d)-ai-weekly.md
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LLM_MODEL: ${{ secrets.LLM_MODEL }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_USERNAME: ${{ secrets.SMTP_USERNAME }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
```

## Project Structure

```
rss-digest/
├── configs/              # TOML config files for different digests
│   ├── ai-weekly.toml
│   └── tech-daily.toml
├── content/digests/      # Generated Markdown digests
├── src/
│   ├── cli.py           # Main entry point (Typer CLI)
│   ├── config.py        # CLI settings
│   ├── core/            # Core models and interfaces
│   │   ├── models.py    # ContentItem, DigestResult (Pydantic)
│   │   └── interfaces.py # BaseFetcher, BasePublisher (ABC)
│   ├── fetchers/        # Content fetcher plugins
│   │   └── rss.py       # RSS fetcher implementation
│   ├── publishers/      # Publisher plugins
│   │   ├── file_system.py  # Save as Markdown
│   │   └── email.py     # Email publisher
│   ├── commands/        # CLI subcommands
│   │   ├── generate_cmd.py # Generate command
│   │   └── publish_cmd.py  # Publish command
│   └── llm_processor.py # LLM digest generation
├── config/
│   └── loader.py        # TOML config loading utilities
├── templates/
│   └── email_template.html
├── .env.example
└── pyproject.toml
```

## Extending the Engine

### Adding a New Fetcher

Create a new fetcher by implementing `BaseFetcher`:

```python
from src.core.interfaces import BaseFetcher
from src.core.models import ContentItem

class YouTubeFetcher(BaseFetcher):
    def fetch(self, **kwargs) -> List[ContentItem]:
        # Fetch YouTube data
        items = []
        # ... fetch logic ...
        return items
```

### Adding a New Publisher

Create a new publisher by implementing `BasePublisher`:

```python
from src.core.interfaces import BasePublisher
from src.core.models import DigestResult

class GitHubPagesPublisher(BasePublisher):
    def publish(self, digest: DigestResult, **kwargs) -> bool:
        # Publish to GitHub Pages
        return True
```

## Cost Estimates

- **DeepSeek**: ~$0.007/month (less than 1 cent!)
- **OpenRouter (Gemini)**: ~$0.007/month
- **OpenAI (GPT-4o-mini)**: ~$0.05/month
- **SMTP Email**: Free (included with most email services)

## Troubleshooting

**No articles fetched:**
```bash
uv run rss-digest generate --config ai-weekly --days 14 --verbose
```

**Email fails:**
- Verify SMTP credentials
- Check server/port settings
- Run with `--verbose` for detailed logs

**Config errors:**
```bash
# Validate your config
uv run python -c "from config.loader import load_config; print(load_config('your-config'))"
```

## License

MIT
