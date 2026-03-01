# RSS Digest - Multi-Config Edition

A simple, stateless system to fetch RSS articles, generate AI-powered digests, and deliver them via email. Now with **multi-config support** — run multiple digests (daily, weekly, topic-specific) from the same installation.

No database, no complexity—just RSS feeds, an LLM, and your inbox.

## Features

- **Multi-Config Support**: Define multiple TOML configs for different digests (AI weekly, daily tech, etc.)
- **Stateless & Simple**: No database, no state tracking, no complex setup
- **AI-Powered Digests**: Uses any OpenAI-compatible LLM API (OpenAI, DeepSeek, OpenRouter, etc.)
- **Email Delivery**: Clean HTML digests sent via any SMTP server
- **Flexible Scheduling**: Run locally, via cron, or GitHub Actions
- **Cost-Effective**: ~$0.007/month with Gemini Flash or DeepSeek (~1 cent!)
- **Hype-Free**: Prompts designed to cut through marketing noise and focus on substance

## Workflow

```
RSS Feeds → Fetch Articles → LLM Analysis → Email Digest
```

## Quick Start

```bash
# 1. Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and setup
git clone <your-repo>
cd rss-digest
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys and SMTP settings

# 4. Run your first digest (uses ai-weekly config by default)
uv run python src/main.py --config ai-weekly --dry-run
```

## Multi-Config Setup

Configs live in the `configs/` directory as TOML files:

```
configs/
├── ai-weekly.toml    # AI news weekly digest
├── daily.toml        # Daily tech news
└── custom.toml       # Your own custom digest
```

### Available Configs

```bash
# List all available configs
uv run python src/main.py --list

# Run a specific config
uv run python src/main.py --config ai-weekly
uv run python src/main.py --config daily
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

### CLI Options

```bash
# List available configs
uv run python src/main.py --list

# Run specific config
uv run python src/main.py --config ai-weekly

# Override lookback period
uv run python src/main.py --config ai-weekly --days 3

# Dry run (generate but don't send)
uv run python src/main.py --config ai-weekly --dry-run

# Test mode (only 5 articles)
uv run python src/main.py --config ai-weekly --test

# Verbose logging
uv run python src/main.py --config ai-weekly --verbose
```

### Cron Scheduling

**Weekly (Mondays at 9 AM):**
```cron
0 9 * * 1 cd /path/to/rss-digest && uv run python src/main.py --config ai-weekly
```

**Daily (at 8 AM):**
```cron
0 8 * * * cd /path/to/rss-digest && uv run python src/main.py --config daily
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
      - run: uv run python src/main.py --config ai-weekly
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
│   └── daily.toml
├── src/
│   ├── main.py          # Entry point with --config support
│   ├── rss_fetcher.py   # RSS feed fetching
│   ├── llm_processor.py # LLM digest generation
│   ├── email_sender.py  # Email sending
│   └── config/          # Config loading utilities
│       ├── __init__.py
│       └── loader.py
├── templates/
│   └── email_template.html
├── .env.example
└── pyproject.toml
```

## Cost Estimates

- **DeepSeek**: ~$0.007/month (less than 1 cent!)
- **OpenRouter (Gemini)**: ~$0.007/month
- **OpenAI (GPT-4o-mini)**: ~$0.05/month
- **SMTP Email**: Free (included with most email services)

## Troubleshooting

**No articles fetched:**
```bash
uv run python src/main.py --config ai-weekly --days 14 --verbose
```

**Email fails:**
- Verify SMTP credentials
- Check server/port settings
- Review `digest.log`

**Config errors:**
```bash
# Validate your config
uv run python -c "from config.loader import load_config; print(load_config('your-config'))"
```

## License

MIT
