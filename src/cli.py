"""
RSS Digest CLI - Content Curation Engine
Main entry point using Typer.
"""

import typer
from src.config import CLI_CONTEXT_SETTINGS
from src.commands import generate_cmd, publish_cmd

app = typer.Typer(
    context_settings=CLI_CONTEXT_SETTINGS,
    help="RSS Digest - Content Curation Engine"
)

# Add subcommands
app.add_typer(generate_cmd.app, name="generate")
app.add_typer(publish_cmd.app, name="publish")


def main():
    app()


if __name__ == "__main__":
    main()
