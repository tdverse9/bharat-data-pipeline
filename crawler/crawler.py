import os
import json
import time
import hashlib
import urllib.robotparser
from urllib.parse import urlparse

import httpx
from playwright.sync_api import sync_playwright


USER_AGENT = "BharatLawPipelineBot/1.0"

# Project root
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

RAW_DIR = os.path.join(BASE_DIR, "raw")
MOCK_DIR = os.path.join(BASE_DIR, "data", "mock")
SEED_FILE = os.path.join(BASE_DIR, "data", "seed_urls.json")
INDEX_FILE = os.path.join(RAW_DIR, "crawl_index.jsonl")


os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(MOCK_DIR, exist_ok=True)


def load_seed_urls():
    """Load seed URLs from data/seed_urls.json."""

    if not os.path.exists(SEED_FILE):
        raise FileNotFoundError(
            f"Seed URL file not found: {SEED_FILE}"
        )

    with open(
        SEED_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            "seed_urls.json must contain a JSON object."
        )

    seed_urls = list(data.values())

    # Validate URLs
    for url in seed_urls:
        if not isinstance(url, str):
            raise ValueError(
                f"Invalid URL value: {url}"
            )

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"Invalid URL: {url}"
            )

    return seed_urls


def get_url_hash(url):
    """Generate a consistent hash for file naming."""

    return hashlib.md5(
        url.encode("utf-8")
    ).hexdigest()


def check_robots_txt(url):
    """Check robots.txt before crawling."""

    parsed_url = urlparse(url)

    robots_url = (
        f"{parsed_url.scheme}://"
        f"{parsed_url.netloc}/robots.txt"
    )

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)

    try:
        rp.read()
        return rp.can_fetch(
            USER_AGENT,
            url
        )

    except Exception:
        # If robots.txt cannot be accessed,
        # allow the crawl.
        return True


def fetch_with_backoff(
    url,
    max_retries=3,
    base_delay=2
):
    """Fetch static content with retries."""

    for attempt in range(max_retries):

        try:

            headers = {
                "User-Agent": USER_AGENT
            }

            response = httpx.get(
                url,
                headers=headers,
                timeout=15.0,
                follow_redirects=True,
            )

            response.raise_for_status()

            return (
                response.content,
                response.headers.get(
                    "Content-Type",
                    "text/html"
                ),
            )

        except httpx.HTTPError as e:

            if attempt == max_retries - 1:

                print(
                    f"Failed to fetch {url}: {e}"
                )

                return None, None

            sleep_time = base_delay * (
                2 ** attempt
            )

            print(
                f"Retry {attempt + 1}/"
                f"{max_retries} for {url} "
                f"in {sleep_time}s..."
            )

            time.sleep(sleep_time)

    return None, None


def fetch_dynamic_content(url):
    """Fetch JavaScript-rendered content using Playwright."""

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page(
                user_agent=USER_AGENT
            )

            page.goto(
                url,
                wait_until="networkidle",
                timeout=30000,
            )

            content = page.content()

            browser.close()

            return (
                content.encode("utf-8"),
                "text/html"
            )

    except Exception as e:

        print(
            f"Playwright failed for {url}: {e}"
        )

        return None, None


def fallback_to_mock(
    url_hash,
    content_type="text/html"
):
    """Load local mock data if online fetch fails."""

    if "pdf" in content_type.lower():
        extension = ".pdf"
    else:
        extension = ".html"

    mock_path = os.path.join(
        MOCK_DIR,
        f"mock_{url_hash}{extension}"
    )

    if os.path.exists(mock_path):

        print(
            f"Using mock file: {mock_path}"
        )

        with open(
            mock_path,
            "rb"
        ) as f:
            return f.read()

    return None


def crawl(seed_urls, max_depth=3):
    """Main crawler."""

    visited = set()

    queue = [
        (url, 1)
        for url in seed_urls
    ]

    with open(
        INDEX_FILE,
        "w",
        encoding="utf-8"
    ) as index_out:

        while queue:

            url, depth = queue.pop(0)

            if url in visited:
                continue

            if depth > max_depth:
                continue

            visited.add(url)

            url_hash = get_url_hash(url)

            # robots.txt
            if not check_robots_txt(url):

                print(
                    f"Blocked by robots.txt: {url}"
                )

                continue

            print(
                f"Crawling: {url} "
                f"(Depth: {depth})"
            )

            # Use Playwright for selected JS-heavy sites.
            used_js = any(
                keyword in url.lower()
                for keyword in [
                    "incometax.gov.in",
                    "cbic.gov.in",
                    "indiacode.nic.in",
                    "sci.gov.in",
                ]
            )

            if used_js:

                content, content_type = (
                    fetch_dynamic_content(url)
                )

            else:

                content, content_type = (
                    fetch_with_backoff(url)
                )

            status = 200

            # Fallback
            if not content:

                print(
                    f"Fetch failed. "
                    f"Trying mock fallback..."
                )

                content = fallback_to_mock(
                    url_hash,
                    content_type or "text/html"
                )

                if content:
                    status = 206

            # Save content
            if content:

                if (
                    content_type
                    and "pdf"
                    in content_type.lower()
                ):
                    extension = ".pdf"
                else:
                    extension = ".html"

                file_path = os.path.join(
                    RAW_DIR,
                    f"{url_hash}{extension}"
                )

                with open(
                    file_path,
                    "wb"
                ) as f:
                    f.write(content)

                index_entry = {
                    "url": url,
                    "status": status,
                    "content_type": (
                        content_type
                        or "text/html"
                    ),
                    "used_js": used_js,
                    "timestamp": time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ",
                        time.gmtime()
                    ),
                    "path_to_raw": file_path
                }

                index_out.write(
                    json.dumps(
                        index_entry,
                        ensure_ascii=False
                    )
                    + "\n"
                )

                print(
                    f"Saved: {file_path}"
                )

            else:

                print(
                    f"Could not retrieve: {url}"
                )

    print()
    print("Crawling completed.")
    print(
        f"Index: {INDEX_FILE}"
    )

    return INDEX_FILE


def run_crawler(max_depth=3):
    """
    Public function used by main.py.

    Loads URLs from data/seed_urls.json
    and starts the crawler.
    """

    seed_urls = load_seed_urls()

    print(
        f"Loaded {len(seed_urls)} seed URLs."
    )

    return crawl(
        seed_urls,
        max_depth=max_depth
    )


if __name__ == "__main__":
    run_crawler()