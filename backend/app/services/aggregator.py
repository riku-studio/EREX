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
        agg_blocks: List[AggregatedBlock] = []
        texts = [b.text for b in blocks]

        keyword_hits_per_block: List[List[KeywordMatch]] = []
        if self.keyword_extractor:
            keyword_hits_per_block = [self.keyword_extractor.extract_keywords(text) for text in texts]

        class_hits_per_block: List[List[str]] = []
        if self.classifier:
            class_hits_per_block = [self.classifier.classify_block(text) for text in texts]

        for idx, block in enumerate(blocks):
            keywords = keyword_hits_per_block[idx] if keyword_hits_per_block else []
            classes = class_hits_per_block[idx] if class_hits_per_block else []
            agg_blocks.append(
                AggregatedBlock(
                    text=block.text,
                    start_line=block.start_line,
                    end_line=block.end_line,
                    keywords=keywords,
                    classes=classes,
                )
            )

        keyword_summary = self.keyword_extractor.summarize(texts) if self.keyword_extractor else {}
        class_summary = self.classifier.summarize(texts) if self.classifier else {}

        return {
            "blocks": [asdict(b) for b in agg_blocks],
            "keyword_summary": keyword_summary,
            "class_summary": class_summary,
        }
