from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

from app.services.aggregator import Aggregator
from app.services.classifier import Classifier
from app.services.extractor import KeywordExtractor
from app.services.preprocess import LineFilter
from app.services.semantic import SemanticResult, get_semantic_extractor, prepare_semantic_input
from app.services.splitter import SplitBlock, Splitter
from app.services.cleaner import clean_body
from app.utils.config import Config
from app.utils.logging import logger


@dataclass
class PipelineResult:
    source_path: str
    subject: str
    semantic: Optional[SemanticResult]
    aggregation: Dict[str, object]
    blocks: List[SplitBlock]


class Pipeline:
    """Configurable orchestrator allowing per-step enablement."""

    def __init__(self, config: type[Config] = Config):
        self.config = config
        self.steps = [step.strip() for step in config.PIPELINE_STEPS if step.strip()]

        self.line_filter = LineFilter(config) if "line_filter" in self.steps else None
        self.splitter = Splitter(config) if "splitter" in self.steps else None
        self.keyword_extractor = KeywordExtractor(config) if "extractor" in self.steps else None
        self.classifier = (
            Classifier(config.CLASSIFIER_FOREIGNER_PATH, config) if "classifier" in self.steps else None
        )
        self.semantic_extractor = get_semantic_extractor() if "semantic" in self.steps else None
        self.aggregator = Aggregator(
            keyword_extractor=self.keyword_extractor if "extractor" in self.steps else None,
            classifier=self.classifier if "classifier" in self.steps else None,
        )

    def _apply_line_filter(self, body: str) -> str:
        if not self.line_filter:
            return body
        return prepare_semantic_input(body, line_filter=self.line_filter)

    def _split(self, body: str) -> List[SplitBlock]:
        if not self.splitter:
            cleaned = body.strip()
            return [SplitBlock(text=cleaned, start_line=0, end_line=len(cleaned.splitlines()) - 1)] if cleaned else []
        return self.splitter.split(body)

    def _semantic(self, body: str) -> Optional[SemanticResult]:
        if not self.semantic_extractor:
            return None
        try:
            return self.semantic_extractor.extract(body)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Semantic extractor failed: %s", exc)
            return None

    def process_message(self, message) -> PipelineResult:
        logger.info("Pipeline running for %s with steps=%s", getattr(message, "source_path", ""), self.steps)

        body_clean = clean_body(message) if "cleaner" in self.steps else getattr(message, "body", "")
        body_filtered = self._apply_line_filter(body_clean)
        semantic_result = self._semantic(body_filtered)
        blocks = self._split(body_filtered)

        aggregation = (
            self.aggregator.aggregate_blocks(blocks) if "aggregator" in self.steps else {"blocks": [], "summary": {}}
        )

        return PipelineResult(
            source_path=getattr(message, "source_path", ""),
            subject=getattr(message, "subject", ""),
            semantic=semantic_result,
            blocks=blocks,
            aggregation=aggregation,
        )

    def process_messages(self, messages: Sequence) -> List[PipelineResult]:
        # Preprocess all messages to batch semantic extraction
        prepared: List[dict] = []
        for msg in messages:
            body_clean = clean_body(msg) if "cleaner" in self.steps else getattr(msg, "body", "")
            body_filtered = self._apply_line_filter(body_clean)
            prepared.append(
                {
                    "message": msg,
                    "body_filtered": body_filtered,
                }
            )

        semantic_results: List[SemanticResult | None] = []
        if self.semantic_extractor:
            semantic_results = self.semantic_extractor.extract_batch([p["body_filtered"] for p in prepared])
        else:
            semantic_results = [None for _ in prepared]

        results: List[PipelineResult] = []
        for item, semantic_result in zip(prepared, semantic_results):
            msg = item["message"]
            body_filtered = item["body_filtered"]
            blocks = self._split(body_filtered)
            aggregation = (
                self.aggregator.aggregate_blocks(blocks) if "aggregator" in self.steps else {"blocks": [], "summary": {}}
            )
            results.append(
                PipelineResult(
                    source_path=getattr(msg, "source_path", ""),
                    subject=getattr(msg, "subject", ""),
                    semantic=semantic_result,
                    blocks=blocks,
                    aggregation=aggregation,
                )
            )
        return results
