![](img/robot_writing.jpg)

# RSS Weekly Digest

A simple, stateless system to fetch RSS articles, generate AI-powered digests, and deliver them via email. No database, no complexity—just RSS feeds, an LLM, and your inbox.

## Features

- **Stateless & Simple**: No database, no state tracking, no complex setup
- **AI-Powered Digests**: Uses any OpenAI-compatible LLM API (OpenAI, DeepSeek, OpenRouter, etc.)
- **Email Delivery**: Clean HTML digests sent via any SMTP server (Gmail, Outlook, custom providers)
- **Flexible Scheduling**: Run locally, via cron, or GitHub Actions
- **Cost-Effective**: ~$0.007/month with Gemini Flash or DeepSeek (~1 cent!)
- **Easy to Customize**: Simple config files for feeds and prompts

## How It Works

```
RSS Feeds → Fetch Articles → LLM Analysis → Email Digest
```

1. **Fetch**: Pull articles from configured RSS feeds (default: last 7 days)
2. **Analyze**: Send all articles to LLM in a single API call to generate digest
3. **Send**: Email the HTML digest via your configured SMTP server

## Quick Start

1. **Clone the repo**
```bash
   git clone git@github.com:DataFrosch/rss-digest.git
   ```
2. **Add your favorite RSS feeds** in `config/feeds.py`.
3. **Set your LLM API key** (DeepSeek, OpenAI, or OpenRouter).
4. **Tweak the prompt** to match your interests.
5. **Set up GitHub Actions** to automate your weekly digest.

## Detailed setup

```bash
# 1. Install uv (Python package manager) if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and setup
git clone git@github.com:DataFrosch/rss-digest.git
cd rss-digest
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys (see Setup section)

# 4. Run
uv run python src/main.py
```

### 1. Get API Keys

**LLM Provider** - Choose one:
- **OpenAI**: [platform.openai.com](https://platform.openai.com) → API Keys → Leave `OPENAI_BASE_URL` empty
- **DeepSeek** (recommended): [platform.deepseek.com](https://platform.deepseek.com) → Set `OPENAI_BASE_URL=https://api.deepseek.com`
- **OpenRouter**: [openrouter.ai/keys](https://openrouter.ai/keys) → Set `OPENAI_BASE_URL=https://openrouter.ai/api/v1`

### Email Configuration

Choose your SMTP provider and configure accordingly:

**Option 1: Gmail (Recommended for simplicity)**
- Enable 2-Factor Authentication: https://myaccount.google.com/security
- Generate App Password: https://myaccount.google.com/apppasswords
- Set SMTP_HOST=smtp.gmail.com, SMTP_PORT=587

**Option 2: Outlook/Hotmail**
- Use your Microsoft account credentials
- Set SMTP_HOST=smtp-mail.outlook.com, SMTP_PORT=587

**Option 3: European Email Providers**
See detailed configurations below for popular European providers.

**Option 4: Custom SMTP Provider**
- Use your provider's SMTP server details
- Common ports: 587 (STARTTLS), 465 (SSL), 25 (unencrypted)

Environment variables:
```bash
# Generic SMTP configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_STARTTLS=true
FROM_EMAIL=your-email@example.com
RECIPIENT_EMAIL=recipient@example.com
EMAIL_SENDER_NAME=RSS Digest
```

## European Email Provider Configurations

Below are SMTP configurations for popular European email providers that prioritize privacy and GDPR compliance:

### German Providers

**Posteo (Germany) - Privacy-focused, €1/month**
```bash
SMTP_HOST=posteo.de
SMTP_PORT=587
SMTP_USERNAME=yourname@posteo.de
SMTP_PASSWORD=your-app-password
SMTP_STARTTLS=true
```
- Requires app password generation
- No ads, privacy-focused
- Carbon-neutral hosting

**Mailbox.org (Germany) - €1/month**
```bash
SMTP_HOST=smtp.mailbox.org
SMTP_PORT=587
SMTP_USERNAME=your-email@mailbox.org
SMTP_PASSWORD=your-password
SMTP_STARTTLS=true
```
- Includes office suite
- Strong privacy features
- Based in Germany

**GMX (Germany) - Free tier available**
```bash
SMTP_HOST=mail.gmx.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmx.com
SMTP_PASSWORD=your-password
SMTP_STARTTLS=true
```
- Free with ads option
- Large user base in Germany
- Part of United Internet Group

### Swiss Providers

**ProtonMail (Switzerland) - Requires paid plan for SMTP**
```bash
SMTP_HOST=smtp.protonmail.ch
SMTP_PORT=587
SMTP_USERNAME=your-email@proton.me
SMTP_PASSWORD=your-mail-password
SMTP_STARTTLS=true
```
- End-to-end encryption
- Paid plan required for SMTP access
- Based in Switzerland (outside EU but strong privacy)

### Other European Providers

**Tutanota (Germany) - Limited SMTP access**
```bash
# Note: Tutanota primarily uses web interface
# SMTP available only with specific business plans
# Check current offerings at tutanota.com
```

**Inbox.eu (Latvia)**
```bash
SMTP_HOST=smtp.inbox.eu
SMTP_PORT=587
SMTP_USERNAME=your-email@inbox.eu
SMTP_PASSWORD=your-password
SMTP_STARTTLS=true
```

**Web.de (Germany)**
```bash
SMTP_HOST=smtp.web.de
SMTP_PORT=587
SMTP_USERNAME=your-email@web.de
SMTP_PASSWORD=your-password
SMTP_STARTTLS=true
```

### Choosing a European Provider

**For Privacy**: Posteo, ProtonMail, Tutanota
**For Free Service**: GMX, Web.de
**For Features**: Mailbox.org (includes office suite)
**For Business**: Mailbox.org, ProtonMail Business

**Note**: Some providers may require:
- App passwords instead of main password
- Paid subscriptions for SMTP access
- Specific account settings to enable external clients

Always verify current settings in your provider's documentation as configurations may change.

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys - see .env.example for provider-specific examples
```

### 3. Customize Feeds (Optional)

Edit `config/feeds.py` to add your RSS feeds:

```python
RSS_FEEDS = {
    "Tech News": "https://example.com/feed.xml",
    "Your Blog": "https://yourblog.com/rss",
}
```

You can also customize the LLM prompt in the same file.

## Usage

```bash
# Full digest
uv run python src/main.py

# Options:
#   --test        Process only 5 articles
#   --dry-run     Generate but don't send email
#   --days N      Look back N days (default: 7)
#   --verbose     Detailed logging
#   --no-save     Don't save HTML file locally
```

## Automation

**GitHub Actions**: Settings → Secrets → Add: `OPENAI_API_KEY`, `OPENAI_BASE_URL` (if needed), `LLM_MODEL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `FROM_EMAIL`, `RECIPIENT_EMAIL`

**Cron**: `0 9 * * 1 cd /path/to/rss-digest && uv run python src/main.py`

## Customization

- **RSS Feeds**: Edit `config/feeds.py`
- **LLM Prompt**: Edit `DIGEST_GENERATION_PROMPT` in `config/feeds.py`
- **LLM Model**: Change `LLM_MODEL` in `.env` (see `.env.example` for options)
- **Email Template**: Edit `templates/email_template.html`

## Project Structure

```
rss-digest/
├── src/
│   ├── main.py           # Main orchestration
│   ├── rss_fetcher.py    # RSS feed fetching
│   ├── llm_processor.py  # LLM digest generation
│   └── email_sender.py   # Email sending
├── config/
│   └── feeds.py          # Feed URLs & prompts
├── templates/
│   └── email_template.html
├── .github/workflows/
│   └── weekly_digest.yml # GitHub Actions
├── .env.example          # Environment template
└── pyproject.toml        # Dependencies
```

## Cost Estimate

- **DeepSeek**: ~$0.007/month (less than 1 cent!)
- **OpenRouter (Gemini)**: ~$0.007/month
- **OpenAI (GPT-4o-mini)**: ~$0.05/month
- **SMTP Email**: Free (included with most email services, some providers may charge)

## Troubleshooting

- **No articles**: Try `--days 14 --verbose`
- **Email fails**: Verify SMTP credentials are correct, check server/port settings, ensure authentication is properly configured, check `digest.log`
- **LLM errors**: Verify API key, check `OPENAI_BASE_URL`, check credits

## Contributing

Issues and PRs welcome!

## License

MIT
