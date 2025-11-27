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
