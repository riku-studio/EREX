from app.services.splitter import SplitBlock, Splitter


def test_splitter_respects_marker_and_skips_edges():
    body = "\n".join(
        [
            "header line 1",
            "header line 2",
            "header line 3",
            "header line 4",
            "header line 5",
            "案件",  # ignored because within skip range
            "noise",
            "案件名",  # used as marker
            "block1 line",
            "案件",  # marker for next block
            "block2 line",
            "footer1",
            "footer2",
            "footer3",
            "footer4",
            "footer5",
        ]
    )
    splitter = Splitter()
    blocks = splitter.split(body)

    assert len(blocks) == 2
    assert isinstance(blocks[0], SplitBlock)
    assert blocks[0].text.startswith("案件名")
    assert blocks[1].text.startswith("案件")


def test_splitter_returns_whole_body_when_no_marker():
    body = "line1\nline2"
    splitter = Splitter()
    blocks = splitter.split(body)

    assert len(blocks) == 1
    assert blocks[0].text == body
    assert blocks[0].start_line == 0
    assert blocks[0].end_line == 1


def test_splitter_requires_marker_alone():
    body = "前置き\nこの案件については\n案件情報まとめ"
    splitter = Splitter()
    blocks = splitter.split(body)

    assert len(blocks) == 1  # no standalone marker
