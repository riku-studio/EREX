from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Sequence

from app.services.classifier import Classifier
from app.services.extractor import KeywordExtractor, KeywordMatch
from app.services.splitter import SplitBlock


@dataclass
class AggregatedBlock:
    text: str
    start_line: int
    end_line: int
    keywords: List[KeywordMatch]
    classes: List[str]


class Aggregator:
    """Aggregate splitter blocks with keyword extraction and classifiers."""

    def __init__(
        self,
        keyword_extractor: Optional[KeywordExtractor] = None,
        classifier: Optional[Classifier] = None,
    ):
        self.keyword_extractor = keyword_extractor
        self.classifier = classifier

    def aggregate_blocks(self, blocks: Sequence[SplitBlock]) -> Dict[str, object]:
        texts = [b.text for b in blocks]
        keyword_summary = self.keyword_extractor.summarize(texts) if self.keyword_extractor else {}
        class_summary = self.classifier.summarize(texts) if self.classifier else {}
        return {
            "block_count": len(blocks),
            "keyword_summary": keyword_summary,
            "class_summary": class_summary,
        }
