import os
import json

EVAL_RESULTS_FILE = "ner/eval_results.json"
REPORT_OUTPUT = "metrics_report.html"

def generate_html_report():
    # Read computed evaluation metrics or fallback to default values
    results = {"Precision": 0.0, "Recall": 0.0, "F1-Score": 0.0}
    if os.path.exists(EVAL_RESULTS_FILE):
        with open(EVAL_RESULTS_FILE, "r", encoding="utf-8") as f:
            results = json.load(f)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>NER Pipeline Metrics Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 40px; margin: 0; }}
        .container {{ max-width: 750px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
        h1 {{ text-align: center; color: #38bdf8; margin-top: 0; }}
        .metrics-grid {{ display: flex; justify-content: space-around; margin: 30px 0; }}
        .metric-card {{ background: #334155; padding: 15px; border-radius: 8px; text-align: center; width: 28%; }}
        .metric-value {{ font-size: 28px; font-weight: bold; color: #34d399; margin-top: 5px; }}
        .metric-label {{ font-size: 14px; color: #94a3b8; uppercase; }}
        canvas {{ max-height: 350px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Legal Pipeline NER Evaluation</h1>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Precision</div>
                <div class="metric-value">{results.get('Precision', 0):.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Recall</div>
                <div class="metric-value">{results.get('Recall', 0):.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">F1-Score</div>
                <div class="metric-value">{results.get('F1-Score', 0):.2f}</div>
            </div>
        </div>
        <canvas id="metricsChart"></canvas>
    </div>
    <script>
        const ctx = document.getElementById('metricsChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: ['Precision', 'Recall', 'F1-Score'],
                datasets: [{{
                    label: 'NER Metrics',
                    data: [{results.get('Precision', 0)}, {results.get('Recall', 0)}, {results.get('F1-Score', 0)}],
                    backgroundColor: ['#38bdf8', '#818cf8', '#34d399'],
                    borderRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ y: {{ beginAtZero: true, max: 1.0, grid: {{ color: '#334155' }} }} }}
            }}
        }});
    </script>
</body>
</html>"""
    
    with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    generate_html_report()