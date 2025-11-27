from pathlib import Path

from app.services.classifier import Classifier


def test_classifier_counts_ok_and_ng():
    path = Path(__file__).resolve().parents[1] / "config" / "classifiers" / "foreigner.json"
    classifier = Classifier(str(path))
    blocks = [
        "外国籍可（N1以上）",
        "日本人のみ対象 外国籍不可です",
        "記載なし",
    ]

    summary = classifier.summarize(blocks)
    assert summary["ok"]["count"] == 1
    assert summary["ng"]["count"] == 1
    # ratio based on total blocks
    assert summary["ok"]["ratio"] == 1 / len(blocks)
    assert summary["ng"]["ratio"] == 1 / len(blocks)
