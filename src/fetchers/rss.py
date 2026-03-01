"""
RSS Feed Fetcher - Refactored for Content Curation Engine
Retrieves articles from RSS feeds and returns ContentItems.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import feedparser
from dateutil import parser as date_parser

from src.core.interfaces import BaseFetcher
from src.core.models import ContentItem

logger = logging.getLogger(__name__)


class RSSFetcher(BaseFetcher):
    """Fetches and parses RSS feeds, returning ContentItems."""

    def __init__(self, feeds: Dict[str, str]):
        """
        Initialize RSS fetcher with feed configuration.

        Args:
            feeds: Dictionary mapping feed names to URLs
        """
        self.feeds = feeds

    def fetch(self, days_lookback: int = 7, **kwargs) -> List[ContentItem]:
        """
        Fetch articles from all configured feeds from the past N days.

        Args:
            days_lookback: Number of days to look back (default 7)

        Returns:
            List of ContentItem objects
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_lookback)
        all_items = []

        for feed_name, feed_url in self.feeds.items():
            logger.info(f"Fetching feed: {feed_name}")
            try:
                items = self._fetch_single_feed(feed_url, feed_name, cutoff_date)
                all_items.extend(items)
                logger.info(f"Retrieved {len(items)} articles from {feed_name}")
            except Exception as e:
                logger.error(f"Failed to fetch {feed_name}: {str(e)}")
                continue

        logger.info(f"Total articles retrieved: {len(all_items)}")
        return all_items

    def _fetch_single_feed(
        self,
        feed_url: str,
        feed_name: str,
        cutoff_date: datetime
    ) -> List[ContentItem]:
        """
        Fetch and parse a single RSS feed.

        Args:
            feed_url: URL of the RSS feed
            feed_name: Name/category of the feed
            cutoff_date: Only return articles after this date

        Returns:
            List of ContentItem objects
        """
        feed = feedparser.parse(feed_url)
        items = []

        for entry in feed.entries:
            try:
                pub_date = self._parse_date(entry)

                if pub_date and pub_date < cutoff_date:
                    continue

                # Build content from available fields
                content_parts = []
                if entry.get('summary'):
                    content_parts.append(entry.get('summary'))
                if entry.get('description') and entry.get('description') != entry.get('summary'):
                    content_parts.append(entry.get('description'))
                
                content = '\n\n'.join(content_parts) if content_parts else entry.get('title', '')

                item = ContentItem(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    content=content,
                    source=feed_name,
                    published_date=pub_date
                )

                if item.url and item.title:
                    items.append(item)

            except Exception as e:
                logger.warning(f"Failed to parse entry: {str(e)}")
                continue

        return items

    def _parse_date(self, entry) -> Optional[datetime]:
        """
        Parse publication date from feed entry.

        Args:
            entry: Feed entry object

        Returns:
            Parsed datetime or None if parsing fails
        """
        date_fields = ['published', 'updated', 'created']

        for field in date_fields:
            date_str = entry.get(field)
            if date_str:
                try:
                    return date_parser.parse(date_str)
                except Exception:
                    continue

        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass

        logger.warning(f"Could not parse date for entry: {entry.get('title', 'Unknown')}")
        return None
