from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional, Protocol, Sequence

import numpy as np

from app.utils.config import Config
from app.utils.logging import logger

JOB_TEMPLATE = (
    "求人情報, 採用情報, スキル要件, 必須条件, 歓迎条件, 募集要項, 業務内容, "
    "開発経験, 使用技術, プロジェクト内容, 参画期間, 単価, 勤務地, 日本語レベル, "
    "技術スキル, エンジニア募集, 仕事内容, 役割, チーム体制, 国籍"
)


class EmbeddingModel(Protocol):
    def encode(self, sentences: Sequence[str], *args, **kwargs) -> List[List[float]]:  # pragma: no cover - interface
        ...


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


def split_to_sentences(text: str) -> List[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    # Split on JP/CN punctuation or newlines; remove empty pieces
    parts = re.split(r"(?<=[。！？\?])\s*|\n+", normalized)
    return [p for p in parts if p]


@dataclass
class SemanticResult:
    text: str
    score: float
    start_line: Optional[int]
    end_line: Optional[int]
    matched: bool
    line_scores: List[float]


class SemanticExtractor:
    def __init__(self, model: EmbeddingModel, template: str, threshold: float):
        self.model = model
        self.threshold = threshold
        self.template_embedding = self._embed([template])[0]

    def _embed(self, sentences: Sequence[str]) -> np.ndarray:
        embeddings = self.model.encode(
            sentences,
            batch_size=Config.SEMANTIC_BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.asarray(embeddings, dtype=float)

    def extract(self, body: str) -> Optional[SemanticResult]:
        sentences = split_to_sentences(body)
        if not sentences:
            return None

        sentence_embeddings = self._embed(sentences)
        sims = sentence_embeddings @ self.template_embedding  # cosine since normalized

        logger.info(
            "Semantic scoring: sentences=%d, threshold=%.3f, scores=%s",
            len(sentences),
            self.threshold,
            ", ".join(f"{i}:{s:.3f}" for i, s in enumerate(sims)),
        )

        hits = np.where(sims >= self.threshold)[0]
        if hits.size == 0:
            return SemanticResult(
                text="",
                score=0.0,
                start_line=None,
                end_line=None,
                matched=False,
                line_scores=[float(v) for v in sims],
            )

        start_idx = int(hits.min())
        end_idx = int(hits.max())
        score = float(np.mean(sims[hits]))
        segment_text = "\n".join(s.rstrip("。！？?") for s in sentences[start_idx : end_idx + 1]).strip()

        return SemanticResult(
            text=segment_text,
            score=score,
            start_line=start_idx,
            end_line=end_idx,
            matched=True,
            line_scores=[float(v) for v in sims],
        )


def get_semantic_extractor(model: EmbeddingModel | None = None) -> SemanticExtractor:
    active_model = model or _load_model()
    return SemanticExtractor(
        model=active_model,
        template=JOB_TEMPLATE,
        threshold=Config.SEMANTIC_THRESHOLD,
    )
