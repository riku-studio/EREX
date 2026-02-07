from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Protocol, Sequence, Tuple

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


@lru_cache(maxsize=1)
def _load_model() -> EmbeddingModel:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "semantic extraction requires sentence-transformers; install dependencies."
        ) from exc

    resolved_device = Config.semantic_runtime_device()
    logger.info(
        "Loading semantic model %s on accelerator=%s, device=%s (batch_size=%d)",
        Config.SEMANTIC_MODEL,
        Config.SEMANTIC_ACCELERATOR,
        resolved_device,
        Config.SEMANTIC_BATCH_SIZE,
    )
    return SentenceTransformer(Config.SEMANTIC_MODEL, device=resolved_device)


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
        self.negative_templates = Config.semantic_negative_templates()
        self.negative_embeddings = self._embed(self.negative_templates)
        self.field_embeddings = {name: self._embed(values) for name, values in self.field_templates.items() if values}
        self.negative_weight = Config.SEMANTIC_NEGATIVE_WEIGHT
        self.length_penalty = Config.SEMANTIC_LENGTH_PENALTY
        self.window_max_lines = max(1, Config.SEMANTIC_WINDOW_MAX_LINES)
        self.min_lines = max(1, Config.SEMANTIC_MIN_LINES)
        self.candidate_top_n = max(1, Config.SEMANTIC_CANDIDATE_TOP_N)
        self.candidate_radius = max(1, Config.SEMANTIC_CANDIDATE_RADIUS)
        self.candidate_min_score = Config.SEMANTIC_CANDIDATE_MIN_SCORE

    def _embed(self, sentences: Sequence[str]) -> np.ndarray:
        if not sentences:
            return np.empty((0, 0), dtype=float)
        embeddings = self.model.encode(
            sentences,
            batch_size=Config.SEMANTIC_BATCH_SIZE,
            show_progress_bar=Config.SEMANTIC_SHOW_PROGRESS,
            normalize_embeddings=True,
        )
        return np.asarray(embeddings, dtype=float)

    def _max_sim(self, embedding: np.ndarray, templates: np.ndarray) -> float:
        if embedding.size == 0 or templates.size == 0:
            return 0.0
        sims = embedding @ templates.T
        return float(np.max(sims)) if sims.size else 0.0

    def _log_field_debug(self, line_embeddings: np.ndarray) -> None:
        if not logger.isEnabledFor(logging.DEBUG):
            return
        if line_embeddings.size == 0:
            return

        max_scores: Dict[str, float] = {}
        for name, embeds in self.field_embeddings.items():
            if embeds.size == 0:
                max_scores[name] = 0.0
                continue
            sims = line_embeddings @ embeds.T
            max_scores[name] = float(np.max(sims)) if sims.size else 0.0
        if max_scores:
            logger.debug(
                "Semantic field max scores: %s",
                ", ".join(f"{k}:{v:.3f}" for k, v in max_scores.items()),
            )

    def _line_scores(self, line_embeddings: np.ndarray) -> np.ndarray:
        if line_embeddings.size == 0:
            return np.asarray([], dtype=float)
        pos_scores = np.max(line_embeddings @ self.global_embeddings.T, axis=1) if self.global_embeddings.size else 0.0
        neg_scores = (
            np.max(line_embeddings @ self.negative_embeddings.T, axis=1) if self.negative_embeddings.size else 0.0
        )
        return np.asarray(pos_scores, dtype=float) - (self.negative_weight * np.asarray(neg_scores, dtype=float))

    def _candidate_centers(self, line_scores: np.ndarray) -> List[int]:
        if line_scores.size == 0:
            return []
        ranked = sorted(enumerate(line_scores.tolist()), key=lambda item: item[1], reverse=True)
        centers = [idx for idx, score in ranked if score >= self.candidate_min_score][: self.candidate_top_n]
        if not centers and ranked:
            centers = [ranked[0][0]]
        return centers

    def _window_embedding(self, prefix: np.ndarray, start: int, end: int) -> np.ndarray:
        window_sum = prefix[end + 1] - prefix[start]
        window_len = max(1, end - start + 1)
        window_vec = window_sum / float(window_len)
        norm = float(np.linalg.norm(window_vec))
        if norm > 0:
            window_vec = window_vec / norm
        return window_vec

    def _window_score(self, window_embedding: np.ndarray, window_len: int) -> float:
        pos = self._max_sim(window_embedding, self.global_embeddings)
        neg = self._max_sim(window_embedding, self.negative_embeddings)
        return pos - (self.negative_weight * neg) - (self.length_penalty * float(np.log1p(window_len)))

    def _search_best_window(self, line_embeddings: np.ndarray, line_scores: np.ndarray) -> Tuple[Optional[Tuple[int, int]], float]:
        total_lines = line_embeddings.shape[0]
        if total_lines == 0:
            return None, 0.0

        max_lines = min(self.window_max_lines, total_lines)
        min_lines = min(self.min_lines, max_lines)
        centers = self._candidate_centers(line_scores)

        windows: set[Tuple[int, int]] = set()
        for center in centers:
            left = max(0, center - self.candidate_radius)
            right = min(total_lines - 1, center + self.candidate_radius)
            for length in range(min_lines, max_lines + 1):
                start_lo = max(left, center - length + 1)
                start_hi = min(center, right - length + 1)
                if start_lo > start_hi:
                    continue
                for start in range(start_lo, start_hi + 1):
                    windows.add((start, start + length - 1))

        if not windows:
            for length in range(min_lines, max_lines + 1):
                for start in range(0, total_lines - length + 1):
                    windows.add((start, start + length - 1))

        prefix = np.vstack([np.zeros((1, line_embeddings.shape[1]), dtype=float), np.cumsum(line_embeddings, axis=0)])
        best_window: Optional[Tuple[int, int]] = None
        best_score = -1e9
        best_line_sum = -1e9
        for start, end in windows:
            window_vec = self._window_embedding(prefix, start, end)
            score = self._window_score(window_vec, end - start + 1)
            window_line_sum = float(np.sum(line_scores[start : end + 1]))
            if score > best_score or (abs(score - best_score) <= 1e-9 and window_line_sum > best_line_sum):
                best_score = score
                best_line_sum = window_line_sum
                best_window = (start, end)

        return best_window, float(best_score if best_score > -1e8 else 0.0)

    def extract_batch(self, bodies: Sequence[str]) -> List[Optional[SemanticResult]]:
        lines_per_body: List[List[str]] = []
        for body in bodies:
            prepared_body = prepare_semantic_input(body, line_filter=self.line_filter)
            lines = [line for line in prepared_body.splitlines() if line.strip()]
            lines_per_body.append(lines)

        if not any(lines_per_body):
            return [None for _ in bodies]

        all_lines = [line for lines in lines_per_body for line in lines]
        all_line_embeddings = self._embed(all_lines) if all_lines else np.empty((0, 0))
        self._log_field_debug(all_line_embeddings)

        offsets: List[Tuple[int, int]] = []
        cursor = 0
        for lines in lines_per_body:
            start = cursor
            cursor += len(lines)
            offsets.append((start, cursor))

        results: List[Optional[SemanticResult]] = []
        best_scores: List[float] = []
        for lines, (start, end) in zip(lines_per_body, offsets):
            if not lines:
                results.append(None)
                continue

            line_embeddings = all_line_embeddings[start:end]
            line_scores = self._line_scores(line_embeddings)
            best_window, best_score = self._search_best_window(line_embeddings, line_scores)
            best_scores.append(best_score)

            if best_window is None or best_score < self.global_threshold:
                results.append(
                    SemanticResult(
                        text="",
                        score=max(0.0, float(best_score)),
                        start_line=None,
                        end_line=None,
                        matched=False,
                        line_scores=[float(v) for v in line_scores.tolist()],
                    )
                )
                continue

            start_line, end_line = best_window
            matched_text = "\n".join(lines[start_line : end_line + 1]).strip()
            results.append(
                SemanticResult(
                    text=matched_text,
                    score=float(best_score),
                    start_line=start_line,
                    end_line=end_line,
                    matched=True,
                    line_scores=[float(v) for v in line_scores.tolist()],
                )
            )

        top_samples = sorted(enumerate(best_scores), key=lambda item: item[1], reverse=True)[:5]
        logger.info(
            "Semantic window scoring: bodies=%d, threshold=%.3f, top_scores=%s",
            len(lines_per_body),
            self.global_threshold,
            ", ".join(f"{i}:{s:.3f}" for i, s in top_samples),
        )

        return results

    def extract(self, body: str) -> Optional[SemanticResult]:
        results = self.extract_batch([body])
        return results[0] if results else None


def get_semantic_extractor(model: EmbeddingModel | None = None) -> SemanticExtractor:
    active_model = model or _load_model()
    return SemanticExtractor(model=active_model, line_filter=LineFilter())
