from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Protocol, Sequence

import numpy as np

from app.services.preprocess import LineFilter
from app.utils.config import Config
from app.utils.logging import logger


class EmbeddingModel(Protocol):
    def encode(self, sentences: Sequence[str], *args, **kwargs) -> List[List[float]]:  # pragma: no cover - interface
        ...


@dataclass
class SemanticResult:
    text: str
    score: float
    start_line: Optional[int]
    end_line: Optional[int]
    matched: bool
    line_scores: List[float]


@dataclass
class Segment:
    text: str
    start: int
    end: int


@lru_cache(maxsize=1)
def _load_model() -> EmbeddingModel:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "semantic extraction requires sentence-transformers; install dependencies."
        ) from exc

    logger.info(
        "Loading semantic model %s on device=%s (batch_size=%d)",
        Config.SEMANTIC_MODEL,
        Config.SEMANTIC_DEVICE,
        Config.SEMANTIC_BATCH_SIZE,
    )
    return SentenceTransformer(Config.SEMANTIC_MODEL, device=Config.SEMANTIC_DEVICE)


def prepare_semantic_input(body: str, line_filter: LineFilter | None = None) -> str:
    """Apply lightweight line filtering before semantic extraction."""
    active_filter = line_filter or LineFilter()
    lines = body.splitlines()
    filtered_lines = active_filter.filter_lines(lines)
    return "\n".join(filtered_lines)


class SemanticExtractor:
    def __init__(
        self,
        model: EmbeddingModel,
        global_templates: Optional[Sequence[str]] = None,
        global_threshold: Optional[float] = None,
        context_radius: Optional[int] = None,
        field_templates: Optional[Dict[str, Sequence[str]]] = None,
        field_threshold: Optional[float] = None,
        line_filter: LineFilter | None = None,
    ):
        self.model = model
        self.line_filter = line_filter or LineFilter()
        self.global_templates = list(global_templates) if global_templates is not None else Config.semantic_global_templates()
        self.field_templates = dict(field_templates) if field_templates is not None else Config.semantic_field_templates()
        self.context_radius = context_radius if context_radius is not None else Config.SEMANTIC_CONTEXT_RADIUS
        self.global_threshold = (
            global_threshold if global_threshold is not None else Config.SEMANTIC_JOB_GLOBAL_THRESHOLD
        )
        self.field_threshold = field_threshold if field_threshold is not None else Config.SEMANTIC_JOB_FIELD_THRESHOLD

        self.global_embeddings = self._embed(self.global_templates)
        self.field_embeddings = {name: self._embed(values) for name, values in self.field_templates.items() if values}

    def _embed(self, sentences: Sequence[str]) -> np.ndarray:
        if not sentences:
            return np.empty((0, 0), dtype=float)
        embeddings = self.model.encode(
            sentences,
            batch_size=Config.SEMANTIC_BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.asarray(embeddings, dtype=float)

    def _build_segments(self, lines: List[str]) -> List[Segment]:
        segments: List[Segment] = []
        total = len(lines)
        for idx in range(total):
            start = max(0, idx - self.context_radius)
            end = min(total - 1, idx + self.context_radius)
            segment_text = "\n".join(lines[start : end + 1])
            segments.append(Segment(text=segment_text, start=start, end=end))
        return segments

    def _compute_global_scores(self, segment_embeddings: np.ndarray) -> np.ndarray:
        if segment_embeddings.size == 0:
            return np.asarray([], dtype=float)
        if self.global_embeddings.size == 0:
            return np.zeros(segment_embeddings.shape[0], dtype=float)
        sims = segment_embeddings @ self.global_embeddings.T
        return np.max(sims, axis=1)

    def _score_lines(self, total_lines: int, segments: List[Segment], segment_scores: Sequence[float]) -> List[float]:
        scores = [0.0 for _ in range(total_lines)]
        for segment, score in zip(segments, segment_scores):
            for idx in range(segment.start, segment.end + 1):
                scores[idx] = max(scores[idx], float(score))
        return scores

    def _log_field_debug(self, segment_embeddings: np.ndarray) -> None:
        if not logger.isEnabledFor(logging.DEBUG):
            return
        if segment_embeddings.size == 0:
            return

        max_scores: Dict[str, float] = {}
        for name, embeds in self.field_embeddings.items():
            if embeds.size == 0:
                max_scores[name] = 0.0
                continue
            sims = segment_embeddings @ embeds.T
            max_scores[name] = float(np.max(sims)) if sims.size else 0.0
        if max_scores:
            logger.debug(
                "Semantic field max scores: %s",
                ", ".join(f"{k}:{v:.3f}" for k, v in max_scores.items()),
            )

    def extract(self, body: str) -> Optional[SemanticResult]:
        prepared_body = prepare_semantic_input(body, line_filter=self.line_filter)
        lines = [line for line in prepared_body.splitlines() if line.strip()]
        if not lines:
            return None

        segments = self._build_segments(lines)
        segment_embeddings = self._embed([segment.text for segment in segments])
        global_scores = self._compute_global_scores(segment_embeddings)
        line_scores = self._score_lines(len(lines), segments, global_scores)

        top_samples = sorted(
            [(idx, score) for idx, score in enumerate(global_scores)], key=lambda item: item[1], reverse=True
        )[:5]
        logger.info(
            "Semantic scoring: segments=%d, global_threshold=%.3f, top_scores=%s",
            len(segments),
            self.global_threshold,
            ", ".join(f"{i}:{s:.3f}" for i, s in top_samples),
        )
        self._log_field_debug(segment_embeddings)

        hits = np.where(global_scores >= self.global_threshold)[0]
        if hits.size == 0:
            return SemanticResult(
                text="",
                score=0.0,
                start_line=None,
                end_line=None,
                matched=False,
                line_scores=[float(v) for v in line_scores],
            )

        start_line = min(segments[int(i)].start for i in hits)
        end_line = max(segments[int(i)].end for i in hits)
        matched_scores = [float(global_scores[int(i)]) for i in hits]
        segment_text = "\n".join(lines[start_line : end_line + 1]).strip()

        return SemanticResult(
            text=segment_text,
            score=float(np.mean(matched_scores)) if matched_scores else 0.0,
            start_line=start_line,
            end_line=end_line,
            matched=True,
            line_scores=[float(v) for v in line_scores],
        )


def get_semantic_extractor(model: EmbeddingModel | None = None) -> SemanticExtractor:
    active_model = model or _load_model()
    return SemanticExtractor(model=active_model, line_filter=LineFilter())
