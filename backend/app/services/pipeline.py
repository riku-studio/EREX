from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence

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


ProgressCallback = Callable[[float, str, str, int, int], None]


class Pipeline:
    """Configurable orchestrator allowing per-step enablement."""

    def __init__(self, config: type[Config] = Config):
        self.config = config
        self.steps = [step.strip() for step in config.PIPELINE_STEPS if step.strip()]
        self.preprocess_workers = max(1, int(getattr(config, "PIPELINE_PREPROCESS_WORKERS", 1)))

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

    def process_messages(
        self, messages: Sequence, progress_callback: Optional[ProgressCallback] = None
    ) -> List[PipelineResult]:
        def _notify(percent: float, stage: str, message: str, current: int, total: int) -> None:
            if progress_callback is None:
                return
            bounded = min(100.0, max(0.0, float(percent)))
            progress_callback(bounded, stage, message, current, total)

        # Preprocess all messages to batch semantic extraction
        prepared: List[dict] = [{} for _ in range(len(messages))]
        total_messages = len(messages)
        _notify(0.0, "preprocess", "Preparing message bodies", 0, total_messages)
        if total_messages > 0:
            if self.preprocess_workers <= 1 or total_messages <= 1:
                for index, msg in enumerate(messages, start=1):
                    body_clean = clean_body(msg) if "cleaner" in self.steps else getattr(msg, "body", "")
                    body_filtered = self._apply_line_filter(body_clean)
                    prepared[index - 1] = {
                        "message": msg,
                        "body_filtered": body_filtered,
                    }
                    preprocess_percent = 30.0 * (index / total_messages)
                    _notify(preprocess_percent, "preprocess", "Cleaning and filtering message body", index, total_messages)
            else:
                logger.info(
                    "Pipeline preprocess parallel enabled: workers=%d, messages=%d",
                    self.preprocess_workers,
                    total_messages,
                )

                def _preprocess_one(idx: int, msg_obj) -> tuple[int, dict]:
                    body_clean_local = clean_body(msg_obj) if "cleaner" in self.steps else getattr(msg_obj, "body", "")
                    body_filtered_local = self._apply_line_filter(body_clean_local)
                    return idx, {"message": msg_obj, "body_filtered": body_filtered_local}

                done = 0
                with ThreadPoolExecutor(max_workers=self.preprocess_workers) as pool:
                    future_map = {pool.submit(_preprocess_one, idx, msg): idx for idx, msg in enumerate(messages)}
                    for fut in as_completed(future_map):
                        idx, item = fut.result()
                        prepared[idx] = item
                        done += 1
                        preprocess_percent = 30.0 * (done / total_messages)
                        _notify(
                            preprocess_percent,
                            "preprocess",
                            "Cleaning and filtering message body",
                            done,
                            total_messages,
                        )

        semantic_results: List[SemanticResult | None] = []
        if self.semantic_extractor:
            _notify(32.0, "semantic", "Computing semantic embeddings", 0, total_messages)
            semantic_results = self.semantic_extractor.extract_batch([p["body_filtered"] for p in prepared])
            _notify(68.0, "semantic", "Semantic matching completed", total_messages, total_messages)
        else:
            semantic_results = [None for _ in prepared]
            _notify(68.0, "semantic", "Semantic step skipped", total_messages, total_messages)

        results: List[PipelineResult] = []
        _notify(70.0, "aggregate", "Splitting and aggregating statistics", 0, total_messages)
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
            done = len(results)
            aggregate_percent = 70.0 + (30.0 * (done / total_messages) if total_messages else 30.0)
            _notify(aggregate_percent, "aggregate", "Message aggregation completed", done, total_messages)
        return results
