import numpy as np

from app.services.semantic import JOB_TEMPLATE, SemanticExtractor


class FakeModel:
    def __init__(self):
        # Encode template once
        self._templates = {
            "low": np.array([0.0, 1.0]),  # cosine with template -> 0
            "high": np.array([1.0, 0.0]),  # cosine with template -> 1
        }

    def encode(self, sentences, **kwargs):
        vectors = []
        for s in sentences:
            if "match" in s:
                vectors.append(self._templates["high"])
            elif s == JOB_TEMPLATE:
                vectors.append(self._templates["high"])
            elif "hit" in s:
                vectors.append(self._templates["high"])
            else:
                vectors.append(self._templates["low"])
        return vectors


def test_extract_picks_contiguous_block():
    body = "intro line。match line 1。match line 2。other line"
    extractor = SemanticExtractor(model=FakeModel(), threshold=0.5, template=JOB_TEMPLATE)
    result = extractor.extract(body)

    assert result is not None
    assert result.matched is True
    assert result.text == "match line 1\nmatch line 2"
    assert result.start_line == 1
    assert result.end_line == 2
    assert len(result.line_scores) == 4
    assert result.line_scores[1] >= 0.5
    assert result.line_scores[2] >= 0.5


def test_extract_returns_none_when_no_match():
    body = "foo\nbar\nbaz"
    extractor = SemanticExtractor(model=FakeModel(), threshold=0.9, template=JOB_TEMPLATE)
    result = extractor.extract(body)

    assert result is not None
    assert result.matched is False
    assert result.text == ""
    assert result.start_line is None
    assert result.end_line is None
    assert len(result.line_scores) == 3


def test_extract_start_to_last_hit_includes_gap():
    body = "hit one。mid gap。hit two"
    extractor = SemanticExtractor(model=FakeModel(), threshold=0.5, template=JOB_TEMPLATE)
    result = extractor.extract(body)

    assert result is not None
    assert result.matched is True
    assert result.text == "hit one\nmid gap\nhit two"
    assert result.start_line == 0
    assert result.end_line == 2
