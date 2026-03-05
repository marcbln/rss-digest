"""Tests for the core.models module."""

from datetime import datetime
from typing import Dict, Any

import pytest

from src.core.models import ContentItem, DigestResult


@pytest.fixture
def sample_content_item() -> ContentItem:
    """Provide a sample ContentItem for testing."""
    return ContentItem(
        title="Test Article",
        url="https://example.com/article",
        content="This is test content",
        source="Test Feed",
        published_date=datetime(2024, 1, 15, 12, 0, 0),
    )


@pytest.fixture
def sample_digest_result() -> DigestResult:
    """Provide a sample DigestResult for testing."""
    return DigestResult(
        title="Weekly Digest",
        date=datetime(2024, 1, 15, 12, 0, 0),
        config_name="test_config",
        sources_analyzed=5,
        markdown_body="# Test Digest\n\nThis is a test digest.",
        metadata={"version": "1.0", "articles_processed": 10},
    )


def test_content_item_creation(sample_content_item: ContentItem) -> None:
    """Test that ContentItem can be created with valid data."""
    assert sample_content_item.title == "Test Article"
    assert sample_content_item.url == "https://example.com/article"
    assert sample_content_item.content == "This is test content"
    assert sample_content_item.source == "Test Feed"
    assert sample_content_item.published_date == datetime(2024, 1, 15, 12, 0, 0)


def test_content_item_creation_without_optional_fields() -> None:
    """Test that ContentItem can be created without optional published_date."""
    item = ContentItem(
        title="Test Article",
        url="https://example.com/article",
        content="This is test content",
        source="Test Feed",
    )
    assert item.title == "Test Article"
    assert item.published_date is None


def test_digest_result_creation(sample_digest_result: DigestResult) -> None:
    """Test that DigestResult can be created with valid data."""
    assert sample_digest_result.title == "Weekly Digest"
    assert sample_digest_result.config_name == "test_config"
    assert sample_digest_result.sources_analyzed == 5
    assert (
        sample_digest_result.markdown_body == "# Test Digest\n\nThis is a test digest."
    )
    assert sample_digest_result.metadata == {"version": "1.0", "articles_processed": 10}


def test_digest_result_default_metadata() -> None:
    """Test that DigestResult creates empty dict as default metadata."""
    result = DigestResult(
        title="Test Digest",
        date=datetime(2024, 1, 15, 12, 0, 0),
        config_name="test_config",
        sources_analyzed=3,
        markdown_body="# Test",
    )
    assert result.metadata == {}


@pytest.mark.parametrize(
    "title, url, content, source",
    [
        ("", "https://example.com", "content", "source"),  # Empty title
        ("Title", "", "content", "source"),  # Empty url
        ("Title", "https://example.com", "", "source"),  # Empty content
        ("Title", "https://example.com", "content", ""),  # Empty source
    ],
)
def test_content_item_with_empty_fields(
    title: str, url: str, content: str, source: str
) -> None:
    """Test ContentItem creation with various empty field combinations."""
    item = ContentItem(title=title, url=url, content=content, source=source)
    assert item.title == title
    assert item.url == url
    assert item.content == content
    assert item.source == source


def test_content_item_model_validation() -> None:
    """Test that ContentItem validates required fields properly."""
    # All required fields present should work
    item = ContentItem(
        title="Valid Title",
        url="https://example.com",
        content="Valid content",
        source="Valid source",
    )
    assert item is not None

    # Test with special characters
    item_special = ContentItem(
        title='Title with special chars: &<>"',
        url="https://example.com/path?param=value&other=123",
        content="Content with\nnewlines and\ttabs",
        source="Source with émojis 🚀",
    )
    assert item_special.title == 'Title with special chars: &<>"'
    assert item_special.url == "https://example.com/path?param=value&other=123"
    assert item_special.content == "Content with\nnewlines and\ttabs"
    assert item_special.source == "Source with émojis 🚀"


def test_digest_result_with_complex_metadata() -> None:
    """Test DigestResult with complex metadata structure."""
    complex_metadata: Dict[str, Any] = {
        "fetch_stats": {
            "total_articles": 25,
            "successful_fetches": 23,
            "failed_fetches": 2,
        },
        "processing_time": 45.6,
        "llm_tokens_used": 1500,
        "sources": ["feed1", "feed2", "feed3"],
        "tags": ["economics", "policy", "technology"],
    }

    result = DigestResult(
        title="Complex Digest",
        date=datetime(2024, 1, 15, 12, 0, 0),
        config_name="complex_config",
        sources_analyzed=3,
        markdown_body="# Complex Digest",
        metadata=complex_metadata,
    )

    assert result.metadata["fetch_stats"]["total_articles"] == 25
    assert result.metadata["processing_time"] == 45.6
    assert result.metadata["sources"] == ["feed1", "feed2", "feed3"]
    assert result.metadata["tags"] == ["economics", "policy", "technology"]
