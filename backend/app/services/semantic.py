from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import re
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
    _HEAD_KEEP_RE = re.compile(
        r"(案件名|案件概要|概要|募集|業務内容|ポジション|プロジェクト|担当工程|必須スキル|勤務地|作業場所)"
    )

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
        self.negative_power = max(1.0, Config.SEMANTIC_NEGATIVE_POWER)
        self.pos_top_k = max(1, Config.SEMANTIC_POS_TOP_K)
        self.length_penalty = Config.SEMANTIC_LENGTH_PENALTY
        self.length_reward = Config.SEMANTIC_LENGTH_REWARD
        self.center_weight = Config.SEMANTIC_CENTER_WEIGHT
        self.cluster_delta = max(0.0, Config.SEMANTIC_CLUSTER_DELTA)
        self.cluster_min_windows = max(1, Config.SEMANTIC_CLUSTER_MIN_WINDOWS)
        self.cluster_overlap_only = Config.SEMANTIC_CLUSTER_OVERLAP_ONLY
        self.trim_tail_neg_threshold = Config.SEMANTIC_TRIM_TAIL_NEG_THRESHOLD
        self.trim_tail_pos_threshold = Config.SEMANTIC_TRIM_TAIL_POS_THRESHOLD
        self.trim_tail_margin = Config.SEMANTIC_TRIM_TAIL_MARGIN
        self.trim_head_neg_threshold = Config.SEMANTIC_TRIM_HEAD_NEG_THRESHOLD
        self.trim_head_pos_threshold = Config.SEMANTIC_TRIM_HEAD_POS_THRESHOLD
        self.trim_head_margin = Config.SEMANTIC_TRIM_HEAD_MARGIN
        self.trim_neg_weight_line = Config.SEMANTIC_TRIM_NEG_WEIGHT_LINE
        self.trim_pos_weight_line = Config.SEMANTIC_TRIM_POS_WEIGHT_LINE
        self.max_tail_trim = max(0, Config.SEMANTIC_MAX_TAIL_TRIM)
        self.max_head_trim = max(0, Config.SEMANTIC_MAX_HEAD_TRIM)
        self.boundary_neg_threshold = Config.SEMANTIC_BOUNDARY_NEG_THRESHOLD
        self.boundary_pos_threshold = Config.SEMANTIC_BOUNDARY_POS_THRESHOLD
        self.boundary_margin = Config.SEMANTIC_BOUNDARY_MARGIN
        self.boundary_tail_run = max(0, Config.SEMANTIC_BOUNDARY_TAIL_RUN)
        self.boundary_head_run = max(0, Config.SEMANTIC_BOUNDARY_HEAD_RUN)
        self.window_max_lines = max(1, Config.SEMANTIC_WINDOW_MAX_LINES)
        self.min_lines = max(1, Config.SEMANTIC_MIN_LINES)
        self.window_workers = max(1, Config.SEMANTIC_WINDOW_WORKERS)

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

    def _mean_topk_sim(self, embedding: np.ndarray, templates: np.ndarray, top_k: int) -> float:
        if embedding.size == 0 or templates.size == 0:
            return 0.0
        sims = embedding @ templates.T
        if sims.size == 0:
            return 0.0
        flat = np.ravel(sims)
        k = min(max(1, top_k), flat.shape[0])
        top = np.partition(flat, flat.shape[0] - k)[-k:]
        return float(np.mean(top))

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

    def _window_embedding(self, prefix: np.ndarray, start: int, end: int) -> np.ndarray:
        window_sum = prefix[end + 1] - prefix[start]
        window_len = max(1, end - start + 1)
        window_vec = window_sum / float(window_len)
        norm = float(np.linalg.norm(window_vec))
        if norm > 0:
            window_vec = window_vec / norm
        return window_vec

    def _center_score(self, start: int, end: int, total_lines: int) -> float:
        if total_lines <= 1:
            return 1.0
        doc_mid = (total_lines - 1) / 2.0
        denom = max(doc_mid, 1.0)
        window_mid = (start + end) / 2.0
        return max(0.0, 1.0 - (abs(window_mid - doc_mid) / denom))

    def _window_score(self, window_embedding: np.ndarray, window_len: int, start: int, end: int, total_lines: int) -> float:
        # Tuned base rule: mean_pos_max_neg + length/center terms.
        pos = self._mean_topk_sim(window_embedding, self.global_embeddings, self.pos_top_k)
        neg = self._max_sim(window_embedding, self.negative_embeddings)
        neg_term = float(np.power(max(0.0, neg), self.negative_power))
        center_bonus = self.center_weight * self._center_score(start, end, total_lines)
        length_term = float(np.log1p(window_len))
        return (
            pos
            - (self.negative_weight * neg_term)
            - (self.length_penalty * length_term)
            + (self.length_reward * length_term)
            + center_bonus
        )

    def _window_line_scores(self, line_embeddings: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if line_embeddings.size == 0:
            return np.asarray([], dtype=float), np.asarray([], dtype=float)
        pos_sims = line_embeddings @ self.global_embeddings.T if self.global_embeddings.size else np.zeros((line_embeddings.shape[0], 1))
        neg_sims = line_embeddings @ self.negative_embeddings.T if self.negative_embeddings.size else np.zeros((line_embeddings.shape[0], 1))
        pos_scores: List[float] = []
        for sims in pos_sims:
            flat = np.ravel(sims)
            if flat.size == 0:
                pos_scores.append(0.0)
                continue
            k = min(max(1, self.pos_top_k), flat.shape[0])
            top = np.partition(flat, flat.shape[0] - k)[-k:]
            pos_scores.append(float(np.mean(top)))
        neg_scores = np.max(neg_sims, axis=1) if neg_sims.size else np.zeros((line_embeddings.shape[0],), dtype=float)
        return np.asarray(pos_scores, dtype=float), np.asarray(neg_scores, dtype=float)

    def _trim_window(
        self,
        lines: Sequence[str],
        line_pos_scores: np.ndarray,
        line_neg_scores: np.ndarray,
        start_line: int,
        end_line: int,
    ) -> Tuple[Optional[int], Optional[int]]:
        s = start_line
        e = end_line
        eff_pos = line_pos_scores * self.trim_pos_weight_line
        eff_neg = line_neg_scores * self.trim_neg_weight_line
        margin = eff_neg - eff_pos

        tail_trimmed = 0
        head_trimmed = 0

        while e >= s:
            text = lines[e]
            if self._HEAD_KEEP_RE.search(text):
                break
            if tail_trimmed >= self.max_tail_trim:
                break
            if (
                e < eff_neg.shape[0]
                and eff_neg[e] >= self.trim_tail_neg_threshold
                and e < eff_pos.shape[0]
                and eff_pos[e] <= self.trim_tail_pos_threshold
                and e < margin.shape[0]
                and margin[e] >= self.trim_tail_margin
            ):
                e -= 1
                tail_trimmed += 1
                continue
            break

        while s <= e:
            text = lines[s]
            if self._HEAD_KEEP_RE.search(text):
                break
            if head_trimmed >= self.max_head_trim:
                break
            if (
                s < eff_neg.shape[0]
                and eff_neg[s] >= self.trim_head_neg_threshold
                and s < eff_pos.shape[0]
                and eff_pos[s] <= self.trim_head_pos_threshold
                and s < margin.shape[0]
                and margin[s] >= self.trim_head_margin
            ):
                s += 1
                head_trimmed += 1
                continue
            break

        if e < s:
            return None, None
        return s, e

    def _line_looks_negative_boundary(
        self,
        text: str,
        pos_score: float,
        neg_score: float,
    ) -> bool:
        if self._HEAD_KEEP_RE.search(text):
            return False
        margin = neg_score - pos_score
        return bool(
            neg_score >= self.boundary_neg_threshold
            and pos_score <= self.boundary_pos_threshold
            and margin >= self.boundary_margin
        )

    def _refine_boundary_by_negative_runs(
        self,
        lines: Sequence[str],
        line_pos_scores: np.ndarray,
        line_neg_scores: np.ndarray,
        start_line: int,
        end_line: int,
    ) -> Tuple[Optional[int], Optional[int]]:
        s = start_line
        e = end_line
        if s > e:
            return None, None
        eff_pos = line_pos_scores * self.trim_pos_weight_line
        eff_neg = line_neg_scores * self.trim_neg_weight_line

        # Tail boundary: cut at the first strong negative run.
        run = self.boundary_tail_run
        if run > 0:
            stop_at: Optional[int] = None
            for idx in range(s, e - run + 2):
                ok = True
                for j in range(idx, idx + run):
                    if not self._line_looks_negative_boundary(lines[j], float(eff_pos[j]), float(eff_neg[j])):
                        ok = False
                        break
                if ok:
                    stop_at = idx
                    break
            if stop_at is not None:
                e = stop_at - 1

        # Head boundary: drop a greeting/negative run at the front if present.
        head_run = self.boundary_head_run
        if head_run > 0 and s <= e:
            while s + head_run - 1 <= e:
                ok = True
                for j in range(s, s + head_run):
                    text = lines[j]
                    cond = self._line_looks_negative_boundary(text, float(eff_pos[j]), float(eff_neg[j]))
                    if not cond:
                        ok = False
                        break
                if ok:
                    s += head_run
                else:
                    break

        if e < s:
            return None, None
        return s, e

    def _search_best_window(self, line_embeddings: np.ndarray) -> Tuple[Optional[Tuple[int, int]], float]:
        total_lines = line_embeddings.shape[0]
        if total_lines == 0:
            return None, 0.0

        # Keep minimum window length strict to stay consistent with tuned rules.
        if total_lines < self.min_lines:
            return None, 0.0

        max_lines = min(self.window_max_lines, total_lines)
        min_lines = self.min_lines
        prefix = np.vstack([np.zeros((1, line_embeddings.shape[1]), dtype=float), np.cumsum(line_embeddings, axis=0)])
        starts: List[int] = []
        ends: List[int] = []
        scores: List[float] = []
        best_window: Optional[Tuple[int, int]] = None
        best_score = -1e9
        best_len = 10**9
        for length in range(min_lines, max_lines + 1):
            for start in range(0, total_lines - length + 1):
                end = start + length - 1
                window_vec = self._window_embedding(prefix, start, end)
                score = self._window_score(window_vec, length, start, end, total_lines)
                starts.append(start)
                ends.append(end)
                scores.append(score)
                if score > best_score or (abs(score - best_score) <= 1e-9 and length < best_len):
                    best_score = score
                    best_len = length
                    best_window = (start, end)

        if best_window is None:
            return None, 0.0
        if not scores:
            return best_window, float(best_score if best_score > -1e8 else 0.0)

        window_starts = np.asarray(starts, dtype=int)
        window_ends = np.asarray(ends, dtype=int)
        window_scores = np.asarray(scores, dtype=float)

        best_idx = int(np.argmax(window_scores))
        best_start = int(window_starts[best_idx])
        best_end = int(window_ends[best_idx])
        best_score = float(window_scores[best_idx])

        if best_score < self.global_threshold:
            return (best_start, best_end), best_score

        dyn_threshold = max(self.global_threshold, best_score - self.cluster_delta)
        candidate_idx = np.where(window_scores >= dyn_threshold)[0]
        if self.cluster_overlap_only:
            candidate_idx = np.asarray(
                [
                    i
                    for i in candidate_idx
                    if not (int(window_ends[i]) < best_start or int(window_starts[i]) > best_end)
                ],
                dtype=int,
            )
            if candidate_idx.size == 0:
                candidate_idx = np.asarray([best_idx], dtype=int)

        if candidate_idx.size >= self.cluster_min_windows:
            merged_start = int(np.min(window_starts[candidate_idx]))
            merged_end = int(np.max(window_ends[candidate_idx]))
            return (merged_start, merged_end), best_score

        return best_window, float(best_score if best_score > -1e8 else 0.0)

    def _extract_one_from_embeddings(
        self, lines: Sequence[str], line_embeddings: np.ndarray
    ) -> Tuple[SemanticResult, Optional[float]]:
        if not lines:
            return (
                SemanticResult(
                    text="",
                    score=0.0,
                    start_line=None,
                    end_line=None,
                    matched=False,
                    line_scores=[],
                ),
                None,
            )

        best_window, best_score = self._search_best_window(line_embeddings)
        if best_window is None or best_score < self.global_threshold:
            return (
                SemanticResult(
                    text="",
                    score=max(0.0, float(best_score)),
                    start_line=None,
                    end_line=None,
                    matched=False,
                    line_scores=[0.0 for _ in lines],
                ),
                best_score,
            )

        start_line, end_line = best_window
        line_pos_scores, line_neg_scores = self._window_line_scores(line_embeddings)
        trimmed_start, trimmed_end = self._trim_window(
            lines,
            line_pos_scores,
            line_neg_scores,
            start_line,
            end_line,
        )
        if trimmed_start is None or trimmed_end is None:
            return (
                SemanticResult(
                    text="",
                    score=max(0.0, float(best_score)),
                    start_line=None,
                    end_line=None,
                    matched=False,
                    line_scores=[0.0 for _ in lines],
                ),
                best_score,
            )

        start_line, end_line = trimmed_start, trimmed_end
        refined_start, refined_end = self._refine_boundary_by_negative_runs(
            lines,
            line_pos_scores,
            line_neg_scores,
            start_line,
            end_line,
        )
        if refined_start is None or refined_end is None:
            return (
                SemanticResult(
                    text="",
                    score=max(0.0, float(best_score)),
                    start_line=None,
                    end_line=None,
                    matched=False,
                    line_scores=[0.0 for _ in lines],
                ),
                best_score,
            )

        start_line, end_line = refined_start, refined_end
        matched_text = "\n".join(lines[start_line : end_line + 1]).strip()
        line_scores = [0.0 for _ in lines]
        for idx in range(start_line, end_line + 1):
            line_scores[idx] = float(best_score)
        return (
            SemanticResult(
                text=matched_text,
                score=float(best_score),
                start_line=start_line,
                end_line=end_line,
                matched=True,
                line_scores=line_scores,
            ),
            best_score,
        )

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

        results: List[Optional[SemanticResult]] = [None for _ in lines_per_body]
        best_scores: List[Tuple[int, float]] = []
        tasks = [(idx, lines, start, end) for idx, (lines, (start, end)) in enumerate(zip(lines_per_body, offsets))]

        if self.window_workers <= 1 or len(tasks) <= 1:
            for idx, lines, start, end in tasks:
                if not lines:
                    continue
                result, score = self._extract_one_from_embeddings(lines, all_line_embeddings[start:end])
                results[idx] = result
                if score is not None:
                    best_scores.append((idx, float(score)))
        else:
            logger.info(
                "Semantic window parallel enabled: workers=%d, bodies=%d",
                self.window_workers,
                len(tasks),
            )

            def _run_one(task: Tuple[int, List[str], int, int]) -> Tuple[int, SemanticResult, Optional[float]]:
                idx_local, lines_local, start_local, end_local = task
                result_local, score_local = self._extract_one_from_embeddings(
                    lines_local,
                    all_line_embeddings[start_local:end_local],
                )
                return idx_local, result_local, score_local

            with ThreadPoolExecutor(max_workers=self.window_workers) as pool:
                futures = [pool.submit(_run_one, task) for task in tasks if task[1]]
                for fut in as_completed(futures):
                    idx, result, score = fut.result()
                    results[idx] = result
                    if score is not None:
                        best_scores.append((idx, float(score)))

        for idx, lines in enumerate(lines_per_body):
            if lines and results[idx] is None:
                results[idx] = SemanticResult(
                    text="",
                    score=0.0,
                    start_line=None,
                    end_line=None,
                    matched=False,
                    line_scores=[0.0 for _ in lines],
                )
            elif not lines:
                results[idx] = None

        top_samples = sorted(best_scores, key=lambda item: item[1], reverse=True)[:5]
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
