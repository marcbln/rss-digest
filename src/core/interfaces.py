from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import ContentItem, DigestResult


class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self, **kwargs) -> List[ContentItem]:
        """Fetch data from a source and return a list of ContentItems."""
        pass


class BasePublisher(ABC):
    @abstractmethod
    def publish(self, digest: DigestResult, **kwargs) -> bool:
        """Publish the digest result to a specific destination."""
        pass
