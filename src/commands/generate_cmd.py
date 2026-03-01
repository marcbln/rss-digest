"""
Generate command - Fetches content, processes via LLM, outputs Markdown.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from dotenv import load_dotenv

from src.fetchers.rss import RSSFetcher
from src.publishers.file_system import FileSystemPublisher
from src.llm_processor import LLMProcessor
from config.loader import load_config

app = typer.Typer(help="Generate digests and save as Markdown")
console = Console()
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


@app.command()
def run(
    config_name: str = typer.Option(..., "--config", "-c", help="Config name to run"),
    output_dir: str = typer.Option("content/digests", "--output", "-o", help="Output directory for digests"),
    days: Optional[int] = typer.Option(None, "--days", "-d", help="Days to look back (overrides config)"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of articles (for testing)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Generate a digest from RSS feeds and save as Markdown."""
    setup_logging(verbose)
    
    console.print(f"Generating digest for [bold cyan]{config_name}[/bold cyan]...")

    # Load environment variables
    load_dotenv(override=True)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        console.print("[bold red]Error: OPENAI_API_KEY environment variable is required[/bold red]")
        raise typer.Exit(1)

    openai_base_url = os.getenv("OPENAI_BASE_URL") or None
    llm_model = os.getenv("LLM_MODEL") or None

    # Load config
    try:
        config = load_config(config_name)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[bold red]Error: Invalid config - {e}[/bold red]")
        raise typer.Exit(1)

    # Step 1: Fetch articles
    console.print(f"\n[dim]Fetching articles from {len(config['feeds'])} feeds...[/dim]")
    rss_fetcher = RSSFetcher(config['feeds'])
    days_lookback = days if days is not None else config.get('days_lookback', 7)
    items = rss_fetcher.fetch(days_lookback=days_lookback)

    if not items:
        console.print("[bold yellow]No articles found.[/bold yellow]")
        raise typer.Exit(0)

    if limit:
        items = items[:limit]
        console.print(f"[dim]Limited to {limit} articles[/dim]")

    console.print(f"[green]✓[/green] Fetched {len(items)} articles")

    # Step 2: Process with LLM
    console.print("[dim]Processing with LLM...[/dim]")
    llm_processor = LLMProcessor(
        api_key=openai_api_key,
        model=llm_model,
        base_url=openai_base_url
    )

    prompt_template = config.get('prompt', {}).get('template', '')
    if not prompt_template:
        console.print("[bold red]Error: No prompt template found in config[/bold red]")
        raise typer.Exit(1)

    digest = llm_processor.process(
        items=items,
        prompt_template=prompt_template,
        config_name=config['name']
    )

    if not digest:
        console.print("[bold red]Error: Failed to generate digest[/bold red]")
        raise typer.Exit(1)

    console.print("[green]✓[/green] Digest generated")

    # Step 3: Save to filesystem
    fs_publisher = FileSystemPublisher(output_dir=output_dir)
    success = fs_publisher.publish(digest)

    if success:
        filename = f"{digest.date.strftime('%Y-%m-%d')}-{digest.config_name.lower().replace(' ', '-')}.md"
        console.print(f"[bold green]✓[/bold green] Digest saved to [cyan]{output_dir}/{filename}[/cyan]")
        
        # Show token usage
        usage = llm_processor.get_token_usage_summary()
        console.print(f"[dim]Token usage: {usage['total_tokens']} tokens[/dim]")
    else:
        console.print("[bold red]Error: Failed to save digest[/bold red]")
        raise typer.Exit(1)
