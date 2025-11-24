from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Protocol, Sequence, Tuple

import numpy as np

from app.utils.config import Config
from app.utils.logging import logger

JOB_TEMPLATE = (
    "求人情報, 採用情報, スキル要件, 必須条件, 歓迎条件, 募集要項, 業務内容, "
    "開発経験, 使用技術, プロジェクト内容, 参画期間, 単価, 勤務地, 日本語レベル, "
    "技術スキル, エンジニア募集, 仕事内容, 役割, チーム体制, 国籍"
)


class EmbeddingModel(Protocol):
    def encode(self, sentences: Sequence[str]) -> List[List[float]]:  # pragma: no cover - interface
        ...


def default_model() -> EmbeddingModel:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "semantic extraction requires sentence-transformers; install dependencies."
        ) from exc

    return SentenceTransformer(Config.SEMANTIC_MODEL, device=Config.SEMANTIC_DEVICE)


@dataclass
class SemanticResult:
    text: str
    score: float
    start_line: Optional[int]
    end_line: Optional[int]
    matched: bool
    line_scores: List[float]


class SemanticExtractor:
    def __init__(self, model: EmbeddingModel | None = None, threshold: float | None = None):
        self.model = model or default_model()
        self.threshold = threshold if threshold is not None else Config.SEMANTIC_THRESHOLD
        self.template_embedding = self._embed([JOB_TEMPLATE])[0]

    def _embed(self, lines: Sequence[str]) -> List[np.ndarray]:
        vectors = self.model.encode(lines)
        return [np.array(v, dtype=float) for v in vectors]

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-12
        return float(np.dot(a, b) / denom)

    def extract(self, body: str) -> SemanticResult | None:
        lines = [line for line in body.splitlines()]
        if not lines:
            return None

        line_embeddings = self._embed(lines)
        sims = [self._cosine(vec, self.template_embedding) for vec in line_embeddings]
        logger.info(
            "Semantic scoring: lines=%d, threshold=%.3f, scores=%s",
            len(lines),
            self.threshold,
            ", ".join(f"{i}:{s:.3f}" for i, s in enumerate(sims)),
        )

        hit_indices = [idx for idx, sim in enumerate(sims) if sim >= self.threshold]
        if not hit_indices:
            return SemanticResult(
                text="",
                score=0.0,
                start_line=None,
                end_line=None,
                matched=False,
                line_scores=[float(v) for v in sims],
            )

        start_idx = min(hit_indices)
        end_idx = max(hit_indices)
        hit_scores = [sims[i] for i in hit_indices]
        score = float(np.mean(hit_scores))

        segment_text = "\n".join(lines[start_idx : end_idx + 1]).strip()
        return SemanticResult(
            text=segment_text,
            score=score,
            start_line=start_idx,
            end_line=end_idx,
            matched=True,
            line_scores=[float(v) for v in sims],
        )


def get_semantic_extractor(model: EmbeddingModel | None = None) -> SemanticExtractor:
    return SemanticExtractor(model=model)
