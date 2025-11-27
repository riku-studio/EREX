from app.services.extractor import KeywordExtractor


def test_longer_keywords_match_first():
    extractor = KeywordExtractor()
    text = "経験: C++ と Tailwind CSS を使用"
    hits = extractor.extract_keywords(text)
    keywords = {h.keyword for h in hits}

    assert "C++" in keywords
    assert "C" not in keywords
    assert "Tailwind CSS" in keywords
    assert "CSS" not in keywords


def test_count_by_keyword_counts_once_per_block():
    extractor = KeywordExtractor()
    blocks = ["Python Python", "Java and Python", "no hit"]
    counts = extractor.count_by_keyword(blocks)

    assert counts["Python"] == 2  # first and second block
    assert counts["Java"] == 1


def test_summarize_groups_by_category_with_ratio():
    extractor = KeywordExtractor()
    blocks = ["Python Python", "Java and Python", "React", ""]
    summary = extractor.summarize(blocks)

    total_blocks = len(blocks)
    assert "programming_languages" in summary
    py_entry = next(item for item in summary["programming_languages"] if item["keyword"] == "Python")
    java_entry = next(item for item in summary["programming_languages"] if item["keyword"] == "Java")
    assert py_entry["count"] == 2
    assert java_entry["count"] == 1
    assert py_entry["ratio"] == py_entry["count"] / total_blocks
    assert "frontend_frameworks" in summary
