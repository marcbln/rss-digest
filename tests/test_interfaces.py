"""Tests for the core.interfaces module."""

from abc import ABC
from typing import List

import pytest

from src.core.interfaces import BaseFetcher, BasePublisher
from src.core.models import ContentItem, DigestResult


class TestFetcher(BaseFetcher):
    """Test implementation of BaseFetcher for testing purposes."""

    def fetch(self, **kwargs) -> List[ContentItem]:
        """Test fetch implementation."""
        return []


class TestPublisher(BasePublisher):
    """Test implementation of BasePublisher for testing purposes."""

    def publish(self, digest: DigestResult, **kwargs) -> bool:
        """Test publish implementation."""
        return True


def test_base_fetcher_is_abstract() -> None:
    """Test that BaseFetcher cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseFetcher()  # type: ignore[arg-type, abstract]


def test_base_fetcher_subclass_can_be_instantiated() -> None:
    """Test that BaseFetcher subclass can be instantiated."""
    fetcher = TestFetcher()
    assert isinstance(fetcher, BaseFetcher)
    assert isinstance(fetcher, ABC)


def test_base_fetcher_fetch_method_exists() -> None:
    """Test that BaseFetcher defines fetch method."""
    fetcher = TestFetcher()
    assert hasattr(fetcher, "fetch")
    assert callable(getattr(fetcher, "fetch"))

    # Test that fetch returns expected type
    result = fetcher.fetch()
    assert isinstance(result, list)
    # Note: Empty list since TestFetcher returns []


def test_base_publisher_is_abstract() -> None:
    """Test that BasePublisher cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BasePublisher()  # type: ignore[arg-type, abstract]


def test_base_publisher_subclass_can_be_instantiated() -> None:
    """Test that BasePublisher subclass can be instantiated."""
    publisher = TestPublisher()
    assert isinstance(publisher, BasePublisher)
    assert isinstance(publisher, ABC)


def test_base_publisher_publish_method_exists() -> None:
    """Test that BasePublisher defines publish method."""
    publisher = TestPublisher()
    assert hasattr(publisher, "publish")
    assert callable(getattr(publisher, "publish"))

    # Test that publish returns expected type
    from datetime import datetime

    digest = DigestResult(
        title="Test",
        date=datetime.now(),
        config_name="test",
        sources_analyzed=1,
        markdown_body="# Test",
    )
    result = publisher.publish(digest)
    assert isinstance(result, bool)
    assert result is True


def test_base_fetcher_method_signature() -> None:
    """Test that BaseFetcher.fetch has correct method signature."""
    import inspect

    sig = inspect.signature(BaseFetcher.fetch)
    params = sig.parameters

    # Should have 'self' and '**kwargs'
    assert len(params) == 2
    assert "self" in params
    assert "kwargs" in params
    assert params["kwargs"].kind == inspect.Parameter.VAR_KEYWORD


def test_base_publisher_method_signature() -> None:
    """Test that BasePublisher.publish has correct method signature."""
    import inspect

    sig = inspect.signature(BasePublisher.publish)
    params = sig.parameters

    # Should have 'self', 'digest', and '**kwargs'
    assert len(params) == 3
    assert "self" in params
    assert "digest" in params
    assert "kwargs" in params
    assert params["kwargs"].kind == inspect.Parameter.VAR_KEYWORD
