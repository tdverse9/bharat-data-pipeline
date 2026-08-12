import os
import json
import fitz  # PyMuPDF
from bs4 import BeautifulSoup

RAW_INDEX = "raw/crawl_index.jsonl"
NORM_DIR = "normalized"
NORM_INDEX = "normalized/normalized_index.jsonl"

os.makedirs(NORM_DIR, exist_ok=True)

def parse_html(raw_path: str) -> tuple[str, str]:
    with open(raw_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled Legal Document"
    
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()
        
    lines = []
    for elem in soup.find_all(['h1', 'h2', 'h3', 'p', 'li']):
        text = elem.get_text(strip=True)
        if not text:
            continue
        if elem.name == 'h1':
            lines.append(f"# {text}\n")
        elif elem.name in ['h2', 'h3']:
            lines.append(f"## {text}\n")
        elif elem.name == 'li':
            lines.append(f"- {text}")
        else:
            lines.append(f"{text}\n")
            
    return title, "\n".join(lines)

def parse_pdf(raw_path: str) -> tuple[str, str]:
    doc = fitz.open(raw_path)
    title = doc.metadata.get("title") or os.path.basename(raw_path)
    lines = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        lines.append(f"\n<!-- Page {page_num + 1} -->\n")
        lines.append(text)
        
    doc.close()
    return title, "\n".join(lines)

def run_parser():
    if not os.path.exists(RAW_INDEX):
        return

    with open(RAW_INDEX, "r", encoding="utf-8") as f_in, \
         open(NORM_INDEX, "w", encoding="utf-8") as f_out:
        
        for line in f_in:
            entry = json.loads(line)
            raw_path = entry["path_to_raw"]
            url_hash = os.path.basename(raw_path).split('.')[0]
            
            if not os.path.exists(raw_path):
                continue

            if entry["content_type"] == "pdf" or raw_path.endswith(".pdf"):
                title, text_content = parse_pdf(raw_path)
                source_type = "pdf"
            else:
                title, text_content = parse_html(raw_path)
                source_type = "html"

            norm_path = os.path.join(NORM_DIR, f"{url_hash}.md")
            with open(norm_path, "w", encoding="utf-8") as f_md:
                f_md.write(text_content)

            norm_entry = {
                "url": entry["url"],
                "url_hash": url_hash,
                "source_type": source_type,
                "title": title,
                "detected_language": "en",
                "char_count": len(text_content),
                "path_to_text": norm_path
            }
            f_out.write(json.dumps(norm_entry) + "\n")

if __name__ == "__main__":
    run_parser()