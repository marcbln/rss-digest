"""
Main Orchestration Script
Simplified workflow: Fetch RSS articles → Generate AI digest → Send email
No database dependencies - completely stateless.
Supports multiple TOML/YAML config files for different digests.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from dotenv import load_dotenv

from rss_fetcher import RSSFetcher
from llm_processor import LLMProcessor
from email_sender import EmailSender
from config.loader import load_config, list_available_configs


# Configure logging
def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('digest.log')
        ]
    )


logger = logging.getLogger(__name__)


class DigestOrchestrator:
    """Main orchestrator for the digest system."""

    def __init__(
        self,
        config: Dict[str, Any],
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        recipient_email: str,
        openai_api_key: str,
        smtp_starttls: bool = True,
        from_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        openai_base_url: Optional[str] = None,
        llm_model: Optional[str] = None
    ):
        """
        Initialize the orchestrator with config and credentials.

        Args:
            config: Loaded TOML config dictionary
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP username (usually email address)
            smtp_password: SMTP password
            recipient_email: Email address to send digest to
            openai_api_key: OpenAI-compatible API key
            smtp_starttls: Whether to use STARTTLS encryption
            from_email: Sender email address (defaults to smtp_username)
            sender_name: Display name for sender (defaults to config value)
            openai_base_url: Base URL for OpenAI-compatible API (optional)
            llm_model: LLM model to use (optional)
        """
        self.config = config
        self.rss_fetcher = RSSFetcher(config['feeds'])
        self.llm_processor = LLMProcessor(
            openai_api_key,
            model=llm_model,
            base_url=openai_base_url
        )
        
        # Use config sender_name if not provided
        effective_sender_name = sender_name or config.get('sender_name', 'RSS Digest')
        
        self.email_sender = EmailSender(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            smtp_starttls=smtp_starttls,
            from_email=from_email,
            sender_name=effective_sender_name
        )
        self.recipient_email = recipient_email

        logger.info(f"Digest orchestrator initialized for: {config['name']}")

    def generate_and_send_digest(
        self,
        days: Optional[int] = None,
        dry_run: bool = False,
        save_html: bool = True,
        limit: Optional[int] = None
    ) -> bool:
        """
        Complete workflow: Fetch articles, generate digest, and send email.

        Args:
            days: Number of days to look back (defaults to config value)
            dry_run: If True, generate but don't send email
            save_html: If True, save digest as HTML file
            limit: Limit number of articles (for testing)

        Returns:
            True if successful, False otherwise
        """
        # Use config days_lookback if not specified
        if days is None:
            days = self.config.get('days_lookback', 7)
        
        # Get prompt template from config
        prompt_config = self.config.get('prompt', {})
        prompt_template = prompt_config.get('template', self._default_prompt())
        
        # Get email subject from config
        email_subject = self.config.get('email_subject', f"{self.config['name']} Digest")

        logger.info("=" * 60)
        logger.info(f"STARTING {self.config['name'].upper()} DIGEST WORKFLOW")
        logger.info("=" * 60)

        try:
            # Step 1: Fetch articles from RSS feeds
            logger.info(f"\n[STEP 1] Fetching articles from past {days} days")
            articles = self.rss_fetcher.fetch_recent_articles(days)

            if not articles:
                logger.warning("No articles fetched from RSS feeds")
                return False

            logger.info(f"✓ Fetched {len(articles)} articles")

            # Limit articles if specified (for testing)
            if limit:
                articles = articles[:limit]
                logger.info(f"Limited to {limit} articles for testing")

            # Step 2: Generate digest with LLM
            logger.info(f"\n[STEP 2] Generating digest from {len(articles)} articles")

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            date_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

            # Generate digest HTML in a single LLM call
            digest_html = self.llm_processor.generate_digest_from_articles(
                articles,
                prompt_template,
                date_range
            )

            if not digest_html:
                logger.error("Failed to generate digest")
                return False

            logger.info("✓ Digest generated successfully")

            # Log token usage
            usage = self.llm_processor.get_token_usage_summary()
            logger.info(f"Token usage: {usage['total_tokens']} tokens")

            # Step 3: Save HTML if requested
            if save_html:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_name = self.config['name'].lower().replace(' ', '-')
                filepath = f"digest_{safe_name}_{timestamp}.html"
                self.email_sender.save_digest_html(digest_html, date_range, filepath)
                logger.info(f"✓ Digest saved to {filepath}")

            # Step 4: Send email (unless dry run)
            if not dry_run:
                logger.info("\n[STEP 3] Sending digest email")
                success = self.email_sender.send_digest(
                    recipient_email=self.recipient_email,
                    digest_html=digest_html,
                    date_range=date_range,
                    article_count=len(articles),
                    template_path="templates/email_template.html",
                    subject_override=email_subject
                )

                if success:
                    logger.info("✓ Digest sent successfully")
                    logger.info("\n" + "=" * 60)
                    logger.info("WORKFLOW COMPLETE")
                    logger.info("=" * 60)
                    logger.info(f"\nSummary:")
                    logger.info(f"  Digest: {self.config['name']}")
                    logger.info(f"  Articles processed: {len(articles)}")
                    logger.info(f"  Date range: {date_range}")
                    logger.info(f"  Total tokens: {usage['total_tokens']}")
                    return True
                else:
                    logger.error("Failed to send digest email")
                    return False
            else:
                logger.info("\nDry run mode - email not sent")
                logger.info("✓ Digest saved to HTML file")
                logger.info("\n" + "=" * 60)
                logger.info("WORKFLOW COMPLETE (DRY RUN)")
                logger.info("=" * 60)
                logger.info(f"\nSummary:")
                logger.info(f"  Digest: {self.config['name']}")
                logger.info(f"  Articles processed: {len(articles)}")
                logger.info(f"  Date range: {date_range}")
                logger.info(f"  Total tokens: {usage['total_tokens']}")
                return True

        except Exception as e:
            logger.error(f"Error in workflow: {str(e)}", exc_info=True)
            return False

    def _default_prompt(self) -> str:
        """Return a default prompt template."""
        return """You are creating a news digest from the following articles.

ARTICLES FROM {date_range} ({article_count} articles):
{article_list}

TASK: Create a digest with the following sections:

1. BIG PICTURE
   - One paragraph summary of main themes

2. TOP 3 ARTICLES
   - For each: Title (as clickable link) + 2-3 sentence summary

3. OTHER NOTABLE ITEMS
   - 3-4 other articles worth mentioning

FORMATTING:
- Use clean, semantic HTML
- <h2> for main sections
- <p> for paragraphs
- <a href="url"> for links
- Return ONLY the HTML content

Begin:
"""


def load_environment():
    """Load and validate environment variables."""
    load_dotenv(override=True)
    
    # Required LLM configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Required SMTP configuration
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    
    missing_vars = []
    for var, value in [
        ("SMTP_HOST", smtp_host),
        ("SMTP_PORT", smtp_port),
        ("SMTP_USERNAME", smtp_username),
        ("SMTP_PASSWORD", smtp_password),
        ("RECIPIENT_EMAIL", recipient_email)
    ]:
        if not value:
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Optional configuration with defaults
    openai_base_url = os.getenv("OPENAI_BASE_URL", "")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    smtp_starttls = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
    from_email = os.getenv("FROM_EMAIL", smtp_username)
    sender_name = os.getenv("EMAIL_SENDER_NAME")
    
    try:
        smtp_port = int(smtp_port)
    except ValueError:
        raise ValueError("SMTP_PORT must be a valid integer")
    
    return {
        "openai_api_key": openai_api_key,
        "openai_base_url": openai_base_url,
        "llm_model": llm_model,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_username": smtp_username,
        "smtp_password": smtp_password,
        "smtp_starttls": smtp_starttls,
        "from_email": from_email,
        "sender_name": sender_name,
        "recipient_email": recipient_email
    }


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="RSS Digest - Multi-config RSS monitoring and digest generation"
    )

    parser.add_argument(
        '--config',
        type=str,
        default='ai-weekly',
        help='Config file to use (default: ai-weekly). Use --list to see available configs.'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List available configs and exit'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: process only 5 articles'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode: generate digest but do not send email'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=None,
        help='Number of days to look back for articles (overrides config)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save digest as HTML file'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # List configs if requested
    if args.list:
        configs = list_available_configs()
        if configs:
            print("\nAvailable configs:")
            for config in configs:
                print(f"  - {config}")
            print("\nUse with: --config <name>")
        else:
            print("\nNo configs found in configs/ directory")
        sys.exit(0)

    # Load and validate environment variables
    try:
        env_config = load_environment()
    except ValueError as e:
        logger.error(str(e))
        logger.error("Please check your .env file")
        sys.exit(1)

    # Load the digest config
    try:
        digest_config = load_config(args.config)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid config: {e}")
        sys.exit(1)

    # Initialize orchestrator
    orchestrator = DigestOrchestrator(
        config=digest_config,
        smtp_host=env_config["smtp_host"],
        smtp_port=env_config["smtp_port"],
        smtp_username=env_config["smtp_username"],
        smtp_password=env_config["smtp_password"],
        recipient_email=env_config["recipient_email"],
        openai_api_key=env_config["openai_api_key"],
        smtp_starttls=env_config["smtp_starttls"],
        from_email=env_config["from_email"],
        sender_name=env_config["sender_name"],
        openai_base_url=env_config["openai_base_url"],
        llm_model=env_config["llm_model"]
    )

    # Run workflow
    limit = 5 if args.test else None
    success = orchestrator.generate_and_send_digest(
        days=args.days,
        dry_run=args.dry_run,
        save_html=not args.no_save,
        limit=limit
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
