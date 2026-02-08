import numpy as np

from app.services.semantic import SemanticExtractor


class FakeModel:
    def encode(self, sentences, **kwargs):
        vectors = []
        for s in sentences:
            if "job" in s or "GLOBAL" in s:
                vectors.append(np.array([1.0, 0.0]))
            elif "greet" in s or "NEG" in s:
                vectors.append(np.array([0.0, 1.0]))
            else:
                vectors.append(np.array([0.0, 0.0]))
        return vectors


def test_extract_marks_relevant_multi_line_window():
    body = "greet hello\njob line one\njob line two\ngreet footer"
    extractor = SemanticExtractor(
        model=FakeModel(),
        global_templates=["GLOBAL"],
        global_threshold=0.2,
        field_templates={},
    )

    result = extractor.extract(body)

    assert result is not None
    assert result.matched is True
    assert result.text == "job line one\njob line two"
    assert result.start_line == 1
    assert result.end_line == 2


def test_extract_returns_no_match_when_below_threshold():
    body = "greet foo\ngreet bar\ngreet baz"
    extractor = SemanticExtractor(
        model=FakeModel(),
        global_templates=["GLOBAL"],
        global_threshold=0.8,
        field_templates={},
    )

    result = extractor.extract(body)

    assert result is not None
    assert result.matched is False
    assert result.text == ""
    assert result.start_line is None
    assert result.end_line is None
    assert len(result.line_scores) == 3


def test_negative_templates_reduce_greeting_bias():
    body = "greet line\njob core line\ngreet sign-off"
    extractor = SemanticExtractor(
        model=FakeModel(),
        global_templates=["GLOBAL"],
        global_threshold=0.1,
        field_templates={},
    )
    extractor.min_lines = 1
    extractor.negative_templates = ["NEG"]
    extractor.negative_embeddings = extractor._embed(extractor.negative_templates)

    result = extractor.extract(body)

    assert result is not None
    assert result.matched is True
    assert result.text == "job core line"
    assert result.start_line == 1
    assert result.end_line == 1


def test_extract_batch_returns_results_per_body():
    bodies = ["greet\njob line", "greet only"]
    extractor = SemanticExtractor(
        model=FakeModel(),
        global_templates=["GLOBAL"],
        global_threshold=0.2,
        field_templates={},
    )

    results = extractor.extract_batch(bodies)

    assert len(results) == 2
    assert results[0] is not None and results[0].matched is True
    assert results[1] is not None and results[1].matched is False


def test_best_window_is_chosen_for_multi_line_content():
    class WeightedModel:
        def encode(self, sentences, **kwargs):
            vectors = []
            for s in sentences:
                if "jobA" in s:
                    vectors.append(np.array([1.0, 0.0]))
                elif "jobB" in s:
                    vectors.append(np.array([0.6, 0.0]))
                elif "GLOBAL" in s:
                    vectors.append(np.array([1.0, 0.0]))
                elif "NEG" in s:
                    vectors.append(np.array([0.0, 1.0]))
                else:
                    vectors.append(np.array([0.0, 0.0]))
            return vectors

    body = "NEG one\njobA one\njobB two\nNEG two"
    extractor = SemanticExtractor(
        model=WeightedModel(),
        global_templates=["GLOBAL"],
        global_threshold=0.2,
        field_templates={},
    )
    extractor.negative_templates = ["NEG"]
    extractor.negative_embeddings = extractor._embed(extractor.negative_templates)

    result = extractor.extract(body)

    assert result is not None
    assert result.matched is True
    assert result.text == "jobA one\njobB two"
    assert result.start_line == 1
    assert result.end_line == 2
