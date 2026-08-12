# Mini Legal Data Pipeline

An end-to-end data processing pipeline that crawls web and PDF sources, normalizes unstructured content into Markdown, performs semantic token chunking, and runs a hybrid Named-Entity Recognition (NER) system on legal documents.

---

## Pipeline Architecture

```mermaid
graph TD
    %% Ingestion Layer
    subgraph Ingestion Layer [1. Crawler]
        A[Seed URLs] --> B{Check robots.txt & Dedupe}
        B -->|Static| C[HTTPX w/ Backoff]
        B -->|JS-Rendered| D[Playwright Headless]
        C --> E[(raw/ .html & .pdf)]
        D --> E
        E --> F[crawl_index.jsonl]
    end

    %% Transformation Layer I
    subgraph Parsing Layer [2. Parser & Normalizer]
        F --> G{File Type}
        G -->|HTML| H[BeautifulSoup Boilerplate Removal]
        G -->|PDF| I[PyMuPDF Text & Page Extraction]
        H --> J[(normalized/ .md)]
        I --> J
        J --> K[normalized_index.jsonl]
    end

    %% Transformation Layer II
    subgraph Chunking Layer [3. Semantic Chunker]
        K --> L[Split on Headings/Paragraphs]
        L --> M[tiktoken Tokenization]
        M --> N[Enforce 400-800 Tokens & Overlap]
        N --> O[(chunks/chunks.jsonl)]
    end

    %% Inference & Evaluation Layer
    subgraph AI/NER Layer [4. Hybrid NER & Evaluation]
        O --> P[Regex: SECTION_REF, DATE, MONEY]
        O --> Q[spaCy ML: ORG, ACT_NAME]
        P --> R[(ner/annotations.jsonl)]
        Q --> R
        R --> S[Evaluate vs gold_ner.jsonl]
        S --> T((metrics_report.html & CLI Summary))
    end
Setup & Environment InstructionsPrerequisitesPython: 3.10 or higherPackage Manager: pipDocker (Optional, for containerized execution)  Option 1: Automated Local SetupRun the single-command shell script to automatically set up a virtual environment, install dependencies, download required NLP models, and install browser drivers:  Bashchmod +x run.sh
./run.sh
Option 2: Manual Local SetupBash# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Download spaCy model and Playwright browsers
python -m spacy download en_core_web_sm
playwright install chromium
Option 3: Docker SetupBuild and run the containerized pipeline without modifying your local environment:  Bashdocker build -t legal-pipeline .
docker run --rm legal-pipeline
How to Run Each StageThe pipeline can be executed end-to-end or component-by-component.End-to-End OrchestrationRun the complete pipeline, execute evaluations, generate reports, and print summary statistics to the console:  Bashpython main.py
Running Individual StagesCrawler: Crawls static and dynamic web pages, respects robots.txt, handles exponential backoffs, and saves raw content to /raw.  Bashpython crawler/crawler.py
Parsing & Normalization: Strips HTML boilerplate, extracts PDF pages/text, and converts raw files into clean Markdown in /normalized.  Bashpython parsers/parser.py
Semantic Chunking: Splits normalized documents into 400–800 token semantic chunks with overlap and saves them to chunks/chunks.jsonl.  Bashpython chunker/chunker.py
Hybrid NER Extraction: Runs rule-based regex patterns and spaCy ML models to extract legal entities into ner/annotations.jsonl.  Bashpython ner/ner_system.py
NER Evaluation: Computes Precision, Recall, and F1-score against data/gold_ner.jsonl.  Bashpython ner/evaluate.py
HTML Metrics Report: Renders an interactive Chart.js report at metrics_report.html.  Bashpython scripts/generate_report.py
Unit Testing: Runs tests for hashing, tokenization, chunking, and NER extraction.  Bashpytest tests/ -v
Design Choices & Trade-offsResilient Ingestion Strategy: Used lightweight HTTP requests (httpx) by default for static pages to maximize throughput, reserving headless Playwright browser rendering only for dynamic pages. Added a fallback mechanism to offline mock data when seed URLs return severe network blocks or timeouts.  Semantic Boundary Chunking: Selected paragraph and heading breaks as split boundaries via tiktoken rather than arbitrary character counts. This prevents breaking sentences mid-entity at the cost of slight chunk size variability.  Hybrid NER Architecture: Combined deterministic Regex patterns with statistical NLP models. Regex delivers fast precision for structured items (SECTION_REF, DATE, MONEY), while spaCy handles unstructured context (ORG, ACT_NAME).  Format Normalization: Standardized all HTML and PDF content into Markdown (.md). Markdown preserves document hierarchy (headings, lists) cleanly without the overhead of heavy XML/HTML tag trees.  Limitations & Future ImprovementsCurrent LimitationsRule-Based Heuristics: Regex patterns for SECTION_REF and ACT_NAME are tailored to common legal structures and may misfire on non-standard citation formats.  Single-Node Execution: Pipeline stages run sequentially on a single thread/machine, creating potential bottlenecks when scaling to tens of thousands of documents.Model Precision: Standard spaCy en_core_web_sm is general-purpose and lacks specialized legal-domain fine-tuning[cite: 1].What I’d Improve with More TimeDomain-Specific Transformer Models: Replace generic spaCy models with fine-tuned transformers like Legal-BERT for higher NER precision on complex legal entities.Distributed Processing Framework: Migrate parsing and chunking workloads to Apache Spark or Ray to enable parallel processing across a multi-node cluster.Workflow Orchestration: Replace main.py with an Apache Airflow DAG to manage task dependencies, automated retries, and monitoring at scale.Database Ingestion: Add a dedicated persistence layer to load final annotations and chunks directly into a PostgreSQL or SQLite relational schema for downstream querying.