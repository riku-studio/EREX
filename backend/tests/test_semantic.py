import numpy as np

from app.services.semantic import SemanticExtractor


class FakeModel:
    def encode(self, sentences, **kwargs):
        vectors = []
        for s in sentences:
            if "hit" in s or "GLOBAL" in s:
                vectors.append(np.array([1.0, 0.0]))
            elif "field-skill" in s:
                vectors.append(np.array([0.0, 1.0]))
            else:
                vectors.append(np.array([0.0, 0.0]))
        return vectors


def test_extract_marks_relevant_segments():
    body = "intro line\nhit line here\ntrailing"
    extractor = SemanticExtractor(
        model=FakeModel(),
        global_templates=["GLOBAL"],
        global_threshold=0.5,
        context_radius=0,
        field_templates={},
    )

    result = extractor.extract(body)

    assert result is not None
    assert result.matched is True
    assert result.text == "hit line here"
    assert result.start_line == 1
    assert result.end_line == 1
    assert result.line_scores == [0.0, 1.0, 0.0]


def test_extract_returns_no_match_when_below_threshold():
    body = "foo\nbar\nbaz"
    extractor = SemanticExtractor(
        model=FakeModel(),
        global_templates=["GLOBAL"],
        global_threshold=0.9,
        context_radius=0,
        field_templates={},
    )

    result = extractor.extract(body)

    assert result is not None
    assert result.matched is False
    assert result.text == ""
    assert result.start_line is None
    assert result.end_line is None
    assert result.line_scores == [0.0, 0.0, 0.0]


def test_context_radius_expands_scoring_range():
    body = "first\nhit center\nlast"
    extractor = SemanticExtractor(
        model=FakeModel(),
        global_templates=["GLOBAL"],
        global_threshold=0.5,
        context_radius=1,
        field_templates={},
    )

    result = extractor.extract(body)

    assert result is not None
    assert result.matched is True
    assert result.text == body
    assert result.start_line == 0
    assert result.end_line == 2
    assert all(score >= 0.5 for score in result.line_scores)


def test_extract_batch_returns_results_per_body():
    bodies = ["intro\nhit line", "no match here"]
    extractor = SemanticExtractor(
        model=FakeModel(),
        global_templates=["GLOBAL"],
        global_threshold=0.5,
        context_radius=0,
        field_templates={},
    )

    results = extractor.extract_batch(bodies)

    assert len(results) == 2
    assert results[0] is not None and results[0].matched is True
    assert results[1] is not None and results[1].matched is False
