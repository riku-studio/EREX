from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Protocol, Sequence, Tuple

import numpy as np

from app.utils.config import Config

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

    return SentenceTransformer(Config.SEMANTIC_MODEL)


@dataclass
class SemanticResult:
    text: str
    score: float
    start_line: int
    end_line: int


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

        best_segment: Tuple[int, int, float] | None = None  # start, end inclusive, score
        start = None
        for idx, sim in enumerate(sims):
            if sim >= self.threshold:
                start = idx if start is None else start
            else:
                if start is not None:
                    end = idx - 1
                    segment_score = float(np.mean(sims[start : end + 1]))
                    best_segment = self._pick_better(best_segment, (start, end, segment_score))
                    start = None
        if start is not None:
            end = len(sims) - 1
            segment_score = float(np.mean(sims[start : end + 1]))
            best_segment = self._pick_better(best_segment, (start, end, segment_score))

        if not best_segment:
            return None

        start_idx, end_idx, score = best_segment
        segment_text = "\n".join(lines[start_idx : end_idx + 1]).strip()
        return SemanticResult(text=segment_text, score=score, start_line=start_idx, end_line=end_idx)

    @staticmethod
    def _pick_better(
        current: Tuple[int, int, float] | None, candidate: Tuple[int, int, float]
    ) -> Tuple[int, int, float]:
        if current is None:
            return candidate
        curr_len = current[1] - current[0]
        cand_len = candidate[1] - candidate[0]
        if cand_len > curr_len:
            return candidate
        if cand_len == curr_len and candidate[2] > current[2]:
            return candidate
        return current


def get_semantic_extractor(model: EmbeddingModel | None = None) -> SemanticExtractor:
    return SemanticExtractor(model=model)
