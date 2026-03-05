"""Tests for the fetchers.rss module."""

from datetime import datetime, timedelta, timezone
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest
from dateutil import parser as date_parser

from src.fetchers.rss import RSSFetcher
from src.core.models import ContentItem


@pytest.fixture
def sample_feeds() -> Dict[str, str]:
    """Provide sample feed configuration for testing."""
    return {
        "Test Feed 1": "https://example.com/feed1.xml",
        "Test Feed 2": "https://example.com/feed2.xml",
    }


@pytest.fixture
def rss_fetcher(sample_feeds: Dict[str, str]) -> RSSFetcher:
    """Provide RSSFetcher instance for testing."""
    return RSSFetcher(sample_feeds)


@pytest.fixture
def mock_feed_entry() -> MagicMock:
    """Provide a mock feed entry with typical RSS data."""
    entry = MagicMock()
    entry.title = "Test Article"
    entry.link = "https://example.com/article"
    entry.summary = "Test summary"
    entry.description = "Test description"
    entry.published = "Mon, 15 Jan 2024 12:00:00 GMT"
    entry.updated = "Mon, 15 Jan 2024 12:30:00 GMT"
    # Prevent infinite recursion by configuring get behavior
    entry.get.side_effect = lambda key, default=None: {
        "title": entry.title,
        "link": entry.link,
        "summary": entry.summary,
        "description": entry.description,
        "published": entry.published,
        "updated": entry.updated,
    }.get(key, default)
    return entry


@pytest.fixture
def mock_feed_with_old_entry() -> MagicMock:
    """Provide a mock feed entry with old date (should be filtered out)."""
    entry = MagicMock()
    entry.title = "Old Article"
    entry.link = "https://example.com/old-article"
    entry.summary = "Old summary"
    entry.published = "Mon, 01 Jan 2024 12:00:00 GMT"
    # Prevent infinite recursion by configuring get behavior
    entry.get.side_effect = lambda key, default=None: {
        "title": entry.title,
        "link": entry.link,
        "summary": entry.summary,
        "published": entry.published,
    }.get(key, default)
    return entry


def test_rss_fetcher_initialization(sample_feeds: Dict[str, str]) -> None:
    """Test RSSFetcher initialization with feeds."""
    fetcher = RSSFetcher(sample_feeds)
    assert fetcher.feeds == sample_feeds
    assert len(fetcher.feeds) == 2


def test_rss_fetcher_initialization_empty_feeds() -> None:
    """Test RSSFetcher initialization with empty feeds."""
    fetcher = RSSFetcher({})
    assert fetcher.feeds == {}


@patch("src.fetchers.rss.feedparser.parse")
def test_fetch_success(
    mock_parse: MagicMock, rss_fetcher: RSSFetcher, mock_feed_entry: MagicMock
) -> None:
    """Test successful fetching of RSS feeds."""
    # Setup mock feed
    mock_feed = MagicMock()
    mock_feed.entries = [mock_feed_entry]
    mock_parse.return_value = mock_feed

    # Test fetch
    with patch.object(rss_fetcher, "_fetch_single_feed") as mock_fetch_single:
        mock_fetch_single.return_value = [
            ContentItem(
                title=mock_feed_entry.title,
                url=mock_feed_entry.link,
                content=mock_feed_entry.summary,
                source="Test Feed 1",
                published_date=date_parser.parse(mock_feed_entry.published),
            )
        ]

        result = rss_fetcher.fetch(days_lookback=7)

        assert isinstance(result, list)
        assert len(result) == 2  # 2 feeds * 1 item each
        assert all(isinstance(item, ContentItem) for item in result)
        assert mock_fetch_single.call_count == 2


@patch("src.fetchers.rss.feedparser.parse")
def test_fetch_with_feed_failure(
    mock_parse: MagicMock, rss_fetcher: RSSFetcher
) -> None:
    """Test fetching when one feed fails."""
    # Setup mock to raise exception for one feed
    mock_parse.side_effect = Exception("Feed fetch failed")

    result = rss_fetcher.fetch(days_lookback=7)

    assert isinstance(result, list)
    assert len(result) == 0  # No items due to fetch failure


@patch("src.fetchers.rss.feedparser.parse")
@patch("src.fetchers.rss.date_parser.parse")
def test_fetch_single_feed_success(
    mock_date_parser: MagicMock,
    mock_parse: MagicMock,
    rss_fetcher: RSSFetcher,
    mock_feed_entry: MagicMock,
) -> None:
    """Test successful fetching of a single RSS feed."""
    # Mock date parsing to return a recent date
    recent_date = datetime.now(timezone.utc) - timedelta(days=1)
    mock_date_parser.return_value = recent_date

    # Setup mock feed
    mock_feed = MagicMock()
    mock_feed.entries = [mock_feed_entry]
    mock_parse.return_value = mock_feed

    # Use a recent cutoff date to ensure the entry is included
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    result = rss_fetcher._fetch_single_feed(
        "https://example.com/feed.xml", "Test Feed", cutoff_date
    )

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], ContentItem)
    assert result[0].title == "Test Article"
    assert result[0].url == "https://example.com/article"
    assert result[0].source == "Test Feed"


@patch("src.fetchers.rss.feedparser.parse")
@patch("src.fetchers.rss.date_parser.parse")
def test_fetch_single_feed_filters_old_entries(
    mock_date_parser: MagicMock,
    mock_parse: MagicMock,
    rss_fetcher: RSSFetcher,
    mock_feed_entry: MagicMock,
    mock_feed_with_old_entry: MagicMock,
) -> None:
    """Test that old entries are filtered out based on cutoff date."""
    # Mock date parsing - recent date for new entry, old date for old entry
    recent_date = datetime.now(timezone.utc) - timedelta(days=1)
    old_date = datetime.now(timezone.utc) - timedelta(days=30)

    def mock_date_parse(date_str):
        if date_str == "Mon, 15 Jan 2024 12:00:00 GMT":
            return recent_date
        elif date_str == "Mon, 01 Jan 2024 12:00:00 GMT":
            return old_date
        return recent_date  # default

    mock_date_parser.side_effect = mock_date_parse

    # Setup mock feed with both new and old entries
    mock_feed = MagicMock()
    mock_feed.entries = [mock_feed_entry, mock_feed_with_old_entry]
    mock_parse.return_value = mock_feed

    # Set cutoff date to filter out old entry
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
    result = rss_fetcher._fetch_single_feed(
        "https://example.com/feed.xml", "Test Feed", cutoff_date
    )

    assert isinstance(result, list)
    assert len(result) == 1  # Only new entry should be included
    assert result[0].title == "Test Article"


@patch("src.fetchers.rss.feedparser.parse")
def test_fetch_single_feed_handles_entry_parsing_errors(
    mock_parse: MagicMock, rss_fetcher: RSSFetcher
) -> None:
    """Test that entry parsing errors are handled gracefully."""
    # Setup mock feed with problematic entry
    problematic_entry = MagicMock()
    problematic_entry.title = None  # This will cause issues
    problematic_entry.link = None
    # Prevent infinite recursion
    problematic_entry.get.side_effect = lambda key, default=None: {
        "title": problematic_entry.title,
        "link": problematic_entry.link,
        "summary": None,
        "description": None,
        "published": None,
        "updated": None,
        "created": None,
    }.get(key, default)

    mock_feed = MagicMock()
    mock_feed.entries = [problematic_entry]
    mock_parse.return_value = mock_feed

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
    result = rss_fetcher._fetch_single_feed(
        "https://example.com/feed.xml", "Test Feed", cutoff_date
    )

    assert isinstance(result, list)
    assert len(result) == 0  # Entry should be filtered out due to missing title/url


def test_parse_date_success() -> None:
    """Test successful date parsing from feed entry."""
    entry = MagicMock()
    entry.published = "Mon, 15 Jan 2024 12:00:00 GMT"
    # Prevent infinite recursion
    entry.get.side_effect = lambda key, default=None: {
        "published": entry.published,
        "updated": None,
        "created": None,
    }.get(key, default)

    fetcher = RSSFetcher({})
    result = fetcher._parse_date(entry)

    assert isinstance(result, datetime)
    assert result.tzinfo is not None


def test_parse_date_with_multiple_fields() -> None:
    """Test date parsing tries multiple date fields."""
    entry = MagicMock()
    entry.published = None
    entry.updated = "Mon, 15 Jan 2024 12:30:00 GMT"
    entry.created = None
    # Prevent infinite recursion
    entry.get.side_effect = lambda key, default=None: {
        "published": entry.published,
        "updated": entry.updated,
        "created": entry.created,
    }.get(key, default)

    fetcher = RSSFetcher({})
    result = fetcher._parse_date(entry)

    assert isinstance(result, datetime)
    assert result.tzinfo is not None


def test_parse_date_failure() -> None:
    """Test date parsing failure returns None."""
    entry = MagicMock()
    entry.published = "invalid-date"
    entry.updated = None
    entry.created = None
    # Prevent infinite recursion
    entry.get.side_effect = lambda key, default=None: {
        "published": entry.published,
        "updated": entry.updated,
        "created": entry.created,
    }.get(key, default)
    del entry.published_parsed  # Ensure no parsed date attribute

    fetcher = RSSFetcher({})
    result = fetcher._parse_date(entry)

    assert result is None


def test_parse_date_with_parsed_struct() -> None:
    """Test date parsing with time.struct_time."""
    entry = MagicMock()
    entry.published = None
    entry.updated = None
    entry.created = None
    entry.published_parsed = (2024, 1, 15, 12, 0, 0, 0, 15, 0)  # time.struct_time
    # Prevent infinite recursion
    entry.get.side_effect = lambda key, default=None: {
        "published": entry.published,
        "updated": entry.updated,
        "created": entry.created,
    }.get(key, default)

    fetcher = RSSFetcher({})
    result = fetcher._parse_date(entry)

    assert isinstance(result, datetime)
    assert result.tzinfo is not None
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15


@patch("src.fetchers.rss.feedparser.parse")
def test_content_building_with_summary_and_description(
    mock_parse: MagicMock, rss_fetcher: RSSFetcher
) -> None:
    """Test content building when both summary and description are present."""
    entry = MagicMock()
    entry.title = "Test Article"
    entry.link = "https://example.com/article"
    entry.summary = "Test summary"
    entry.description = "Test description"
    entry.published = "Mon, 15 Jan 2024 12:00:00 GMT"
    # Prevent infinite recursion
    entry.get.side_effect = lambda key, default=None: {
        "title": entry.title,
        "link": entry.link,
        "summary": entry.summary,
        "description": entry.description,
    }.get(key, default)

    mock_feed = MagicMock()
    mock_feed.entries = [entry]
    mock_parse.return_value = mock_feed

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
    result = rss_fetcher._fetch_single_feed(
        "https://example.com/feed.xml", "Test Feed", cutoff_date
    )

    assert len(result) == 1
    expected_content = "Test summary\n\nTest description"
    assert result[0].content == expected_content


@patch("src.fetchers.rss.feedparser.parse")
def test_content_building_with_only_summary(
    mock_parse: MagicMock, rss_fetcher: RSSFetcher
) -> None:
    """Test content building when only summary is present."""
    entry = MagicMock()
    entry.title = "Test Article"
    entry.link = "https://example.com/article"
    entry.summary = "Test summary"
    entry.description = None
    entry.published = "Mon, 15 Jan 2024 12:00:00 GMT"
    # Prevent infinite recursion
    entry.get.side_effect = lambda key, default=None: {
        "title": entry.title,
        "link": entry.link,
        "summary": entry.summary,
        "description": entry.description,
    }.get(key, default)

    mock_feed = MagicMock()
    mock_feed.entries = [entry]
    mock_parse.return_value = mock_feed

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
    result = rss_fetcher._fetch_single_feed(
        "https://example.com/feed.xml", "Test Feed", cutoff_date
    )

    assert len(result) == 1
    assert result[0].content == "Test summary"


@patch("src.fetchers.rss.feedparser.parse")
def test_content_building_fallback_to_title(
    mock_parse: MagicMock, rss_fetcher: RSSFetcher
) -> None:
    """Test content building falls back to title when no content fields."""
    entry = MagicMock()
    entry.title = "Test Article"
    entry.link = "https://example.com/article"
    entry.summary = None
    entry.description = None
    entry.published = "Mon, 15 Jan 2024 12:00:00 GMT"
    # Prevent infinite recursion
    entry.get.side_effect = lambda key, default=None: {
        "title": entry.title,
        "link": entry.link,
        "summary": entry.summary,
        "description": entry.description,
    }.get(key, default)

    mock_feed = MagicMock()
    mock_feed.entries = [entry]
    mock_parse.return_value = mock_feed

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
    result = rss_fetcher._fetch_single_feed(
        "https://example.com/feed.xml", "Test Feed", cutoff_date
    )

    assert len(result) == 1
    assert result[0].content == "Test Article"


@pytest.mark.parametrize("days_lookback", [1, 3, 7, 14, 30])
@patch("src.fetchers.rss.feedparser.parse")
def test_fetch_with_different_lookback_periods(
    mock_parse: MagicMock,
    rss_fetcher: RSSFetcher,
    mock_feed_entry: MagicMock,
    days_lookback: int,
) -> None:
    """Test fetch with different days_lookback values."""
    mock_feed = MagicMock()
    mock_feed.entries = [mock_feed_entry]
    mock_parse.return_value = mock_feed

    with patch.object(rss_fetcher, "_fetch_single_feed") as mock_fetch_single:
        mock_fetch_single.return_value = [
            ContentItem(
                title=mock_feed_entry.title,
                url=mock_feed_entry.link,
                content=mock_feed_entry.summary,
                source="Test Feed 1",
                published_date=date_parser.parse(mock_feed_entry.published),
            )
        ]

        result = rss_fetcher.fetch(days_lookback=days_lookback)

        assert isinstance(result, list)
        # Verify cutoff_date calculation by checking it was called correctly
        mock_fetch_single.assert_called()
        call_args = mock_fetch_single.call_args
        cutoff_date = call_args[0][2]  # Third argument is cutoff_date
        expected_cutoff = datetime.now(timezone.utc) - timedelta(days=days_lookback)
        assert (
            abs((cutoff_date - expected_cutoff).total_seconds()) < 1
        )  # Within 1 second
