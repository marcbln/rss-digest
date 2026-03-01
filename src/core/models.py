from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class ContentItem(BaseModel):
    """Standardized format for incoming data (RSS, YouTube, Git)."""
    title: str
    url: str
    content: str
    source: str
    published_date: Optional[datetime] = None


class DigestResult(BaseModel):
    """Standardized format for LLM output ready to be saved/published."""
    title: str
    date: datetime
    config_name: str
    sources_analyzed: int
    markdown_body: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
