import os
import json
from rich.console import Console
from rich.table import Table

from crawler.crawler import run_crawler
from parsers.parser import run_parser
from chunker.chunker import run_chunker
from ner.ner_system import run_ner
from ner.evaluate import evaluate
from scripts.generate_report import generate


def main():
    console = Console()

    console.print(
        "[bold blue]Starting Mini Legal Data Pipeline...[/bold blue]"
    )

    # Run crawler
    run_crawler(max_depth=2)

    # Run parser
    run_parser()

    # Run chunker
    run_chunker()

    # Run NER
    run_ner()

    # Evaluate NER
    metrics = evaluate()

    # Generate report
    generate()

    # Calculate summary stats
    crawled_count = 0

    if os.path.exists("raw/crawl_index.jsonl"):
        with open("raw/crawl_index.jsonl", encoding="utf-8") as f:
            crawled_count = sum(1 for _ in f)

    chunks_count = 0
    total_tokens = 0

    if os.path.exists("chunks/chunks.jsonl"):
        with open("chunks/chunks.jsonl", encoding="utf-8") as f:
            for line in f:
                chunks_count += 1
                total_tokens += json.loads(line).get(
                    "token_estimate", 0
                )

    avg_tokens = (
        total_tokens // chunks_count
        if chunks_count > 0
        else 0
    )

    table = Table(
        title="Pipeline Execution Summary",
        style="cyan"
    )

    table.add_column("Metric", style="bold white")
    table.add_column("Value", style="green")

    table.add_row("Pages Crawled", str(crawled_count))
    table.add_row("Chunks Created", str(chunks_count))
    table.add_row("Avg Tokens/Chunk", str(avg_tokens))
    table.add_row(
        "NER F1-Score",
        f"{metrics.get('F1-Score', 0.0):.2f}"
    )

    console.print(table)

    console.print(
        "[bold green]"
        "✔ Execution complete. "
        "View metrics report at metrics_report.html"
        "[/bold green]"
    )


if __name__ == "__main__":
    main()