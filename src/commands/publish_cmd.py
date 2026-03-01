"""
Publish command - Reads Markdown digest and publishes to destinations.
"""

import os
import sys
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from dotenv import load_dotenv

from src.core.models import DigestResult
from src.publishers.email import EmailPublisher
from src.publishers.github_pages import GitHubPagesPublisher

app = typer.Typer(help="Publish generated digests (e.g., via Email)")
console = Console()


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and markdown body from file content."""
    # Match frontmatter between --- markers
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    
    if match:
        frontmatter_text = match.group(1)
        markdown_body = match.group(2).strip()
        frontmatter = yaml.safe_load(frontmatter_text) or {}
        return frontmatter, markdown_body
    
    # No frontmatter found, treat all as body
    return {}, content.strip()


@app.command()
def email(
    file_path: Path = typer.Argument(..., help="Path to markdown digest file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Publish a digest via email."""
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    console.print(f"Publishing [cyan]{file_path}[/cyan] via Email...")

    # Validate file exists
    if not file_path.exists():
        console.print(f"[bold red]Error: File not found: {file_path}[/bold red]")
        raise typer.Exit(1)

    # Load environment variables
    load_dotenv(override=True)
    
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
        console.print(f"[bold red]Error: Missing environment variables: {', '.join(missing_vars)}[/bold red]")
        raise typer.Exit(1)

    try:
        smtp_port = int(smtp_port)
    except ValueError:
        console.print("[bold red]Error: SMTP_PORT must be a valid integer[/bold red]")
        raise typer.Exit(1)

    # Read and parse markdown file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter, markdown_body = parse_frontmatter(content)

    if not frontmatter:
        console.print("[bold yellow]Warning: No frontmatter found in file[/bold yellow]")
        frontmatter = {}

    # Reconstruct DigestResult
    digest = DigestResult(
        title=frontmatter.get("title", "Digest"),
        date=datetime.fromisoformat(frontmatter["date"]) if "date" in frontmatter else datetime.now(),
        config_name=frontmatter.get("config", "unknown"),
        sources_analyzed=frontmatter.get("sources_analyzed", 0),
        markdown_body=markdown_body,
        metadata={k: v for k, v in frontmatter.items() if k not in ["title", "date", "config", "sources_analyzed"]}
    )

    # Send email
    smtp_starttls = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
    from_email = os.getenv("FROM_EMAIL", smtp_username)
    sender_name = os.getenv("EMAIL_SENDER_NAME", digest.config_name)

    publisher = EmailPublisher(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        recipient_email=recipient_email,
        smtp_starttls=smtp_starttls,
        from_email=from_email,
        sender_name=sender_name
    )

    subject_override = frontmatter.get("subject") or f"{digest.config_name} Digest"
    success = publisher.publish(digest, subject_override=subject_override)

    if success:
        console.print("[bold green]✓[/bold green] Digest emailed successfully!")
    else:
        console.print("[bold red]Error: Failed to send email[/bold red]")
        raise typer.Exit(1)


@app.command()
def github_pages(
    file_path: Path = typer.Argument(..., help="Path to markdown digest file"),
    repo_url: str = typer.Option(
        ...,
        "--repo",
        envvar="BLOG_REPO_URL",
        help="GitHub Repository URL (e.g., git@github.com:user/blog.git)"
    ),
    layout: str = typer.Option("post", "--layout", help="Jekyll layout to use"),
    commit_message: Optional[str] = typer.Option(None, "--message", "-m", help="Custom commit message"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Publish a digest to a GitHub Pages blog repository."""
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    console.print(f"Publishing [cyan]{file_path}[/cyan] to GitHub Pages repo...")

    # Validate file exists
    if not file_path.exists():
        console.print(f"[bold red]Error: File not found: {file_path}[/bold red]")
        raise typer.Exit(1)

    # Load environment variables
    load_dotenv(override=True)
    
    # Use env var if option not provided
    if not repo_url:
        repo_url = os.getenv("BLOG_REPO_URL")
    
    if not repo_url:
        console.print("[bold red]Error: BLOG_REPO_URL not set. Provide --repo or set env var.[/bold red]")
        raise typer.Exit(1)

    # Read and parse markdown file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter, markdown_body = parse_frontmatter(content)

    if not frontmatter:
        console.print("[bold yellow]Warning: No frontmatter found in file[/bold yellow]")
        frontmatter = {}

    # Reconstruct DigestResult
    digest = DigestResult(
        title=frontmatter.get("title", "Digest"),
        date=datetime.fromisoformat(frontmatter["date"]) if "date" in frontmatter else datetime.now(),
        config_name=frontmatter.get("config", "unknown"),
        sources_analyzed=frontmatter.get("sources_analyzed", 0),
        markdown_body=markdown_body,
        metadata={k: v for k, v in frontmatter.items() if k not in ["title", "date", "config", "sources_analyzed"]}
    )

    # Publish to GitHub Pages
    publisher = GitHubPagesPublisher(repo_url=repo_url)
    
    success = publisher.publish(
        digest,
        layout=layout,
        commit_message=commit_message or f"Add digest: {digest.title}"
    )

    if success:
        console.print("[bold green]✓[/bold green] Digest pushed to GitHub Pages successfully!")
    else:
        console.print("[bold red]Error: Failed to publish to GitHub Pages[/bold red]")
        raise typer.Exit(1)
