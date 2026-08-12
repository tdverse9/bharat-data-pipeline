import os
import json
import html

EVAL_RESULTS_FILE = "ner/eval_results.json"
REPORT_OUTPUT = "metrics_report.html"


def load_results():
    """Load NER evaluation results safely."""

    default_results = {
        "Precision": 0.0,
        "Recall": 0.0,
        "F1-Score": 0.0,
    }

    if not os.path.exists(EVAL_RESULTS_FILE):
        print(f"Warning: {EVAL_RESULTS_FILE} not found.")
        return default_results

    try:
        with open(EVAL_RESULTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            print("Warning: Evaluation JSON is not a dictionary.")
            return default_results

        return data

    except json.JSONDecodeError as e:
        print(f"Error reading evaluation JSON: {e}")
        return default_results


def get_metric(results, name):
    """Safely retrieve a numeric metric."""

    value = results.get(name, 0.0)

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def get_quality_label(f1):
    """Return a human-readable F1 quality label."""

    if f1 >= 0.90:
        return "Excellent"
    elif f1 >= 0.80:
        return "Very Good"
    elif f1 >= 0.70:
        return "Good"
    elif f1 >= 0.60:
        return "Fair"
    else:
        return "Needs Improvement"


def find_entity_metrics(results):
    """
    Try to find per-entity metrics from several common JSON formats.

    Supported examples:

    {
        "entities": {
            "PERSON": {
                "Precision": 0.8,
                "Recall": 0.7,
                "F1-Score": 0.75
            }
        }
    }

    or:

    {
        "per_entity": {
            ...
        }
    }
    """

    entity_data = results.get("entities")

    if entity_data is None:
        entity_data = results.get("per_entity")

    if entity_data is None:
        entity_data = results.get("entity_metrics")

    if not isinstance(entity_data, dict):
        return {}

    return entity_data


def generate_entity_rows(entity_metrics):
    """Generate HTML table rows for entity-level metrics."""

    if not entity_metrics:
        return """
        <tr>
            <td colspan="5" class="empty">
                No per-entity metrics available.
            </td>
        </tr>
        """

    rows = []

    for entity_name, metrics in entity_metrics.items():

        if not isinstance(metrics, dict):
            continue

        precision = get_metric(metrics, "Precision")
        recall = get_metric(metrics, "Recall")
        f1 = get_metric(metrics, "F1-Score")

        # Support common alternative naming
        if "precision" in metrics:
            precision = get_metric(metrics, "precision")

        if "recall" in metrics:
            recall = get_metric(metrics, "recall")

        if "f1" in metrics:
            f1 = get_metric(metrics, "f1")

        support = metrics.get(
            "Support",
            metrics.get(
                "support",
                metrics.get("Count", "-")
            )
        )

        rows.append(
            f"""
            <tr>
                <td><strong>{html.escape(str(entity_name))}</strong></td>
                <td>{precision:.2f}</td>
                <td>{recall:.2f}</td>
                <td class="f1-cell">{f1:.2f}</td>
                <td>{html.escape(str(support))}</td>
            </tr>
            """
        )

    if not rows:
        return """
        <tr>
            <td colspan="5" class="empty">
                No per-entity metrics available.
            </td>
        </tr>
        """

    return "".join(rows)


def generate_html_report():
    """Generate a professional HTML report from NER evaluation results."""

    results = load_results()

    precision = get_metric(results, "Precision")
    recall = get_metric(results, "Recall")
    f1 = get_metric(results, "F1-Score")

    quality = get_quality_label(f1)

    # Pipeline statistics
    pages_crawled = results.get(
        "Pages Crawled",
        results.get("pages_crawled", 1)
    )

    chunks_created = results.get(
        "Chunks Created",
        results.get("chunks_created", 1)
    )

    avg_tokens = results.get(
        "Avg Tokens/Chunk",
        results.get("avg_tokens_per_chunk", 0)
    )

    entity_metrics = find_entity_metrics(results)

    entity_rows = generate_entity_rows(entity_metrics)

    entity_labels = list(entity_metrics.keys())

    entity_f1_values = []

    for entity in entity_labels:
        metrics = entity_metrics.get(entity, {})

        if isinstance(metrics, dict):
            value = metrics.get(
                "F1-Score",
                metrics.get(
                    "f1",
                    0
                )
            )

            try:
                entity_f1_values.append(float(value))
            except (TypeError, ValueError):
                entity_f1_values.append(0)
        else:
            entity_f1_values.append(0)

    html_template = f"""<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Legal Pipeline NER Evaluation</title>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            padding: 40px;

            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                Arial,
                sans-serif;

            background: #0f172a;
            color: #f8fafc;
        }}

        .container {{
            max-width: 1100px;
            margin: auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 35px;
        }}

        .header h1 {{
            margin: 0;

            font-size: 32px;

            color: #38bdf8;
        }}

        .header p {{
            color: #94a3b8;
            margin-top: 10px;
        }}

        .section {{
            background: #1e293b;

            border-radius: 14px;

            padding: 25px;

            margin-bottom: 25px;

            box-shadow:
                0 8px 25px
                rgba(0, 0, 0, 0.25);
        }}

        .section h2 {{
            margin-top: 0;

            color: #e2e8f0;

            font-size: 21px;
        }}

        .summary-grid {{
            display: grid;

            grid-template-columns:
                repeat(auto-fit, minmax(180px, 1fr));

            gap: 15px;
        }}

        .summary-card {{
            background: #334155;

            border-radius: 10px;

            padding: 20px;

            text-align: center;
        }}

        .summary-value {{
            font-size: 30px;

            font-weight: 700;

            color: #38bdf8;
        }}

        .summary-label {{
            margin-top: 5px;

            color: #94a3b8;

            font-size: 14px;
        }}

        .metrics-grid {{
            display: grid;

            grid-template-columns:
                repeat(auto-fit, minmax(200px, 1fr));

            gap: 18px;
        }}

        .metric-card {{
            background: #334155;

            padding: 25px;

            border-radius: 10px;

            text-align: center;
        }}

        .metric-value {{
            font-size: 38px;

            font-weight: 700;

            color: #34d399;
        }}

        .metric-label {{
            color: #94a3b8;

            margin-top: 5px;
        }}

        .quality {{
            text-align: center;

            margin-top: 25px;

            padding: 15px;

            background: #0f172a;

            border-radius: 10px;

            color: #38bdf8;

            font-size: 18px;
        }}

        .chart-container {{
            position: relative;

            height: 350px;

            margin-top: 15px;
        }}

        table {{
            width: 100%;

            border-collapse: collapse;
        }}

        th {{
            text-align: left;

            background: #334155;

            color: #cbd5e1;

            padding: 14px;
        }}

        td {{
            padding: 14px;

            border-bottom:
                1px solid #334155;

            color: #e2e8f0;
        }}

        tr:hover {{
            background: #263449;
        }}

        .f1-cell {{
            color: #34d399;

            font-weight: 700;
        }}

        .empty {{
            text-align: center;

            color: #94a3b8;

            padding: 25px;
        }}

        .footer {{
            text-align: center;

            color: #64748b;

            font-size: 13px;

            margin-top: 30px;
        }}

        @media (max-width: 600px) {{

            body {{
                padding: 20px;
            }}

            .header h1 {{
                font-size: 25px;
            }}

            .chart-container {{
                height: 280px;
            }}

        }}

    </style>

</head>

<body>

<div class="container">

    <div class="header">

        <h1>Legal Pipeline NER Evaluation</h1>

        <p>
            Named Entity Recognition Pipeline Performance Report
        </p>

    </div>


    <!-- Pipeline Summary -->

    <div class="section">

        <h2>Pipeline Execution Summary</h2>

        <div class="summary-grid">

            <div class="summary-card">

                <div class="summary-value">
                    {pages_crawled}
                </div>

                <div class="summary-label">
                    Pages Crawled
                </div>

            </div>


            <div class="summary-card">

                <div class="summary-value">
                    {chunks_created}
                </div>

                <div class="summary-label">
                    Chunks Created
                </div>

            </div>


            <div class="summary-card">

                <div class="summary-value">
                    {avg_tokens}
                </div>

                <div class="summary-label">
                    Avg Tokens / Chunk
                </div>

            </div>


            <div class="summary-card">

                <div class="summary-value">
                    {f1:.2f}
                </div>

                <div class="summary-label">
                    NER F1-Score
                </div>

            </div>

        </div>

    </div>


    <!-- Overall Metrics -->

    <div class="section">

        <h2>Overall NER Performance</h2>

        <div class="metrics-grid">

            <div class="metric-card">

                <div class="metric-value">
                    {precision:.2f}
                </div>

                <div class="metric-label">
                    Precision
                </div>

            </div>


            <div class="metric-card">

                <div class="metric-value">
                    {recall:.2f}
                </div>

                <div class="metric-label">
                    Recall
                </div>

            </div>


            <div class="metric-card">

                <div class="metric-value">
                    {f1:.2f}
                </div>

                <div class="metric-label">
                    F1-Score
                </div>

            </div>

        </div>


        <div class="quality">

            Model Quality:
            <strong>{quality}</strong>

        </div>

    </div>


    <!-- Overall Chart -->

    <div class="section">

        <h2>Overall Metrics Chart</h2>

        <div class="chart-container">

            <canvas id="metricsChart"></canvas>

        </div>

    </div>


    <!-- Entity Metrics -->

    <div class="section">

        <h2>Entity-Level Performance</h2>

        <table>

            <thead>

                <tr>
                    <th>Entity</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1-Score</th>
                    <th>Support</th>
                </tr>

            </thead>

            <tbody>

                {entity_rows}

            </tbody>

        </table>

    </div>


    <!-- Entity Chart -->

    <div class="section">

        <h2>Entity F1-Score</h2>

        <div class="chart-container">

            <canvas id="entityChart"></canvas>

        </div>

    </div>


    <div class="footer">

        Generated automatically by the Legal NER Pipeline

    </div>

</div>


<script>

    /*
     * Overall metrics chart
     */

    const metricsCtx =
        document
            .getElementById("metricsChart")
            .getContext("2d");


    new Chart(metricsCtx, {{

        type: "bar",

        data: {{

            labels: [
                "Precision",
                "Recall",
                "F1-Score"
            ],

            datasets: [{{

                label: "NER Metrics",

                data: [
                    {precision},
                    {recall},
                    {f1}
                ],

                backgroundColor: [
                    "#38bdf8",
                    "#818cf8",
                    "#34d399"
                ],

                borderRadius: 8

            }}]

        }},

        options: {{

            responsive: true,

            maintainAspectRatio: false,

            plugins: {{

                legend: {{
                    display: false
                }}

            }},

            scales: {{

                y: {{

                    beginAtZero: true,

                    max: 1,

                    ticks: {{
                        stepSize: 0.1
                    }},

                    grid: {{
                        color: "#334155"
                    }}

                }},

                x: {{

                    grid: {{
                        display: false
                    }}

                }}

            }}

        }}

    }});


    /*
     * Entity-level F1 chart
     */

    const entityCtx =
        document
            .getElementById("entityChart")
            .getContext("2d");


    new Chart(entityCtx, {{

        type: "bar",

        data: {{

            labels: {json.dumps(entity_labels)},

            datasets: [{{

                label: "Entity F1",

                data: {json.dumps(entity_f1_values)},

                backgroundColor: "#34d399",

                borderRadius: 8

            }}]

        }},

        options: {{

            responsive: true,

            maintainAspectRatio: false,

            plugins: {{

                legend: {{
                    display: false
                }}

            }},

            scales: {{

                y: {{

                    beginAtZero: true,

                    max: 1,

                    ticks: {{
                        stepSize: 0.1
                    }},

                    grid: {{
                        color: "#334155"
                    }}

                }},

                x: {{

                    grid: {{
                        display: false
                    }}

                }}

            }}

        }}

    }});

</script>

</body>

</html>
"""

    with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"Report generated: {REPORT_OUTPUT}")


def generate():
    """Pipeline-compatible entry point."""
    return generate_html_report()


if __name__ == "__main__":
    generate()