"""
临时测试脚本：解析目录下的 .eml/.msg/.pst 邮件，清洗正文、行过滤、语义抽取并导出为 CSV。

用法：
    cd backend && uv run python tests/export_to_csv.py --input ../data --output ./tests/out.csv --stage semantic
    # --stage 可选 clean|line_filter|semantic，便于观察各阶段输出
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Optional

# 确保 backend 根目录在 sys.path 中，便于直接运行脚本
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.cleaner import clean_body
from app.services.email_parser import EmailContent, parse_directory, parse_email_file
from app.services.semantic import (
    SemanticExtractor,
    get_semantic_extractor,
    prepare_semantic_input,
)
from app.services.preprocess import LineFilter
from app.utils.config import Config
from app.utils.logging import logger


def _load_messages(target: Path) -> List[EmailContent]:
    if target.is_file():
        return parse_email_file(target)
    return parse_directory(target)


def _rows(
    contents: List[EmailContent],
    stage: str,
    line_filter: Optional[LineFilter],
    extractor: Optional[SemanticExtractor],
):
    prepared: List[tuple[EmailContent, str, str, int | str]] = []
    for item in contents:
        body_clean = clean_body(item)
        lines = body_clean.splitlines()
        if stage == "clean":
            body_filtered = body_clean
            removed: int | str = ""
        else:
            body_filtered = prepare_semantic_input(body_clean, line_filter=line_filter)
            filtered_lines = body_filtered.splitlines()
            removed = len(lines) - len(filtered_lines)
        prepared.append((item, body_clean, body_filtered, removed))

    if stage == "semantic" and extractor:
        semantics = extractor.extract_batch([body_clean for _, body_clean, _, _ in prepared])
    else:
        semantics = [None for _ in prepared]

    for (item, body_clean, body_filtered, removed), semantic in zip(prepared, semantics):
        yield {
            "source_path": item.source_path,
            "subject": item.subject,
            "sender": item.sender,
            "recipients": ";".join(item.recipients),
            "received_at": item.received_at or "",
            "parser": item.parser,
            "error": item.error or "",
            "body_raw": item.body,
            "body_clean": body_clean,
            "body_filtered": body_filtered,
            "line_filter_removed": removed,
            "line_filter_enabled": line_filter.enabled if line_filter else False,
            "pipeline_stage": stage,
            "semantic_text": semantic.text if semantic else "",
            "semantic_score": f"{semantic.score:.4f}" if semantic else "",
            "semantic_start_line": semantic.start_line if semantic else "",
            "semantic_end_line": semantic.end_line if semantic else "",
            "semantic_line_scores": "\n".join(f"{s:.4f}" for s in (semantic.line_scores if semantic else [])),
        }


def export_to_csv(input_path: Path, output_path: Path, stage: str):
    contents = _load_messages(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[info] Batch cleaning {len(contents)} messages (stage={stage})")
    line_filter = LineFilter(Config) if stage != "clean" else None

    try:
        extractor = get_semantic_extractor() if stage == "semantic" else None
    except Exception as exc:
        print(f"[warn] 语义模型加载失败，跳过语义列: {exc}", file=sys.stderr)
        extractor = None

    with output_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=[
                "source_path",
                "subject",
                "sender",
                "recipients",
                "received_at",
                "parser",
                "error",
                "body_raw",
                "body_clean",
                "body_filtered",
                "line_filter_removed",
                "line_filter_enabled",
                "pipeline_stage",
                "semantic_text",
                "semantic_score",
                "semantic_start_line",
                "semantic_end_line",
                "semantic_line_scores",
            ],
        )
        writer.writeheader()
        rows = list(_rows(contents, stage, line_filter, extractor))
        for idx, row in enumerate(rows, start=1):
            if idx % 10 == 0:
                print(f"[progress] 已写入 {idx}/{len(rows)} 条")
            writer.writerow(row)
        print(f"[done] 共导出 {len(rows)} 条记录 -> {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Export parsed emails to CSV (test-only helper)")
    parser.add_argument("--input", required=True, help="文件或目录路径，支持 .eml/.msg/.pst")
    parser.add_argument("--output", required=True, help="CSV 输出路径（将自动创建目录）")
    parser.add_argument(
        "--stage",
        choices=["clean", "line_filter", "semantic"],
        default="semantic",
        help="选择导出到的 pipeline 阶段，便于观察过滤效果",
    )
    args = parser.parse_args()

    export_to_csv(Path(args.input), Path(args.output), stage=args.stage)
    print(f"CSV 已生成：{args.output}")


if __name__ == "__main__":
    main()
