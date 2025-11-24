import numpy as np

from app.services.semantic import JOB_TEMPLATE, SemanticExtractor


class FakeModel:
    def __init__(self):
        # Encode template once
        self._templates = {
            "low": np.array([0.0, 1.0]),  # cosine with template -> 0
            "high": np.array([1.0, 0.0]),  # cosine with template -> 1
        }

    def encode(self, sentences):
        vectors = []
        for s in sentences:
            if "match" in s:
                vectors.append(self._templates["high"])
            elif s == JOB_TEMPLATE:
                vectors.append(self._templates["high"])
            else:
                vectors.append(self._templates["low"])
        return vectors


def test_extract_picks_contiguous_block():
    body = "intro line\nmatch line 1\nmatch line 2\nother line"
    extractor = SemanticExtractor(model=FakeModel(), threshold=0.5)
    result = extractor.extract(body)

    assert result is not None
    assert result.text == "match line 1\nmatch line 2"
    assert result.start_line == 1
    assert result.end_line == 2


def test_extract_returns_none_when_no_match():
    body = "foo\nbar\nbaz"
    extractor = SemanticExtractor(model=FakeModel(), threshold=0.9)
    result = extractor.extract(body)

    assert result is None
