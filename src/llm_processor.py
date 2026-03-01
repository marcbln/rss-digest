"""
LLM Processor Module - Refactored for Content Curation Engine
Processes ContentItems using LLM and returns DigestResult.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from openai import OpenAI
from openai import RateLimitError, APIError, APIConnectionError

from src.core.models import ContentItem, DigestResult

logger = logging.getLogger(__name__)


class LLMProcessor:
    """Processes ContentItems using LLM via OpenAI-compatible APIs."""

    def __init__(self, api_key: str, model: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize LLM processor.

        Args:
            api_key: OpenAI-compatible API key
            model: Model to use (optional, will use LLM_MODEL env var or default)
            base_url: Base URL for OpenAI-compatible API (optional)
        """
        import os
        if model is None:
            model = os.getenv("LLM_MODEL", "gpt-4o-mini")

        if base_url:
            self.client = OpenAI(base_url=base_url, api_key=api_key)
            logger.info(f"LLM Processor initialized with model: {model}, base_url: {base_url}")
        else:
            self.client = OpenAI(api_key=api_key)
            logger.info(f"LLM Processor initialized with model: {model}")

        self.model = model
        self.total_tokens_used = 0

    def process(self, items: List[ContentItem], prompt_template: str, config_name: str) -> Optional[DigestResult]:
        """
        Process ContentItems and generate a DigestResult.

        Args:
            items: List of ContentItem objects
            prompt_template: Prompt template for digest generation
            config_name: Name of the config (for metadata)

        Returns:
            DigestResult object or None if failed
        """
        try:
            if not items:
                logger.warning("No items provided for digest generation")
                return None

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # Default to 7 days
            date_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

            # Format items for prompt
            item_list = self._format_items_for_prompt(items)

            # Format prompt
            prompt = prompt_template.format(
                article_count=len(items),
                article_list=item_list,
                date_range=date_range
            )

            logger.info(f"Generating digest for {len(items)} items")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skilled editor creating weekly news digests. Analyze the provided articles and create a comprehensive digest in clean, semantic HTML."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=4000
            )

            # Track token usage
            if hasattr(response, 'usage'):
                tokens = response.usage.total_tokens
                self.total_tokens_used += tokens
                logger.info(f"Digest generation tokens used: {tokens}")

            digest_html = response.choices[0].message.content.strip()

            # Convert HTML to Markdown-like content (the LLM returns HTML which is fine)
            markdown_body = digest_html

            logger.info("Successfully generated digest")

            return DigestResult(
                title=f"{config_name} Digest",
                date=datetime.now(),
                config_name=config_name,
                sources_analyzed=len(items),
                markdown_body=markdown_body,
                metadata={
                    "model": self.model,
                    "total_tokens": self.total_tokens_used
                }
            )

        except RateLimitError as e:
            logger.warning(f"Rate limit hit during digest generation: {e}")
            return None
        except APIConnectionError as e:
            logger.error(f"API connection error during digest generation: {e}")
            return None
        except APIError as e:
            logger.error(f"API error during digest generation: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating digest: {e}", exc_info=True)
            return None

    def _format_items_for_prompt(self, items: List[ContentItem]) -> str:
        """
        Format ContentItems into a readable list for the LLM prompt.

        Args:
            items: List of ContentItem objects

        Returns:
            Formatted string with item details
        """
        formatted = []

        for i, item in enumerate(items, 1):
            pub_date_str = item.published_date.strftime('%Y-%m-%d') if item.published_date else 'Unknown'

            item_text = f"""
Article {i}:
Title: {item.title}
URL: {item.url}
Source: {item.source}
Published: {pub_date_str}
Content: {item.content[:500] if item.content else 'No content available'}
"""
            formatted.append(item_text.strip())

        return "\n\n---\n\n".join(formatted)

    def get_token_usage_summary(self) -> Dict:
        """Get summary of token usage."""
        return {
            'total_tokens': self.total_tokens_used
        }
