import os
import json
import re
import tiktoken

NORM_INDEX = "normalized/normalized_index.jsonl"
CHUNKS_DIR = "chunks"
CHUNKS_FILE = os.path.join(CHUNKS_DIR, "chunks.jsonl")

os.makedirs(CHUNKS_DIR, exist_ok=True)
encoder = tiktoken.get_encoding("cl100k_base")

def get_token_count(text: str) -> int:
    return len(encoder.encode(text))

def chunk_text(text: str, target_min=400, target_max=800, overlap=75):
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = []
    current_tokens = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        para_tokens = get_token_count(para)
        
        if current_tokens + para_tokens > target_max and current_chunk:
            chunk_str = "\n\n".join(current_chunk)
            chunks.append((chunk_str, current_tokens))
            
            # Retain overlap tokens from the end of the previous chunk
            overlap_p = []
            overlap_tokens = 0
            for p in reversed(current_chunk):
                p_tok = get_token_count(p)
                if overlap_tokens + p_tok <= overlap:
                    overlap_p.insert(0, p)
                    overlap_tokens += p_tok
                else:
                    break
            current_chunk = overlap_p
            current_tokens = overlap_tokens

        current_chunk.append(para)
        current_tokens += para_tokens

    if current_chunk:
        chunk_str = "\n\n".join(current_chunk)
        chunks.append((chunk_str, current_tokens))

    return chunks

def run_chunker():
    if not os.path.exists(NORM_INDEX):
        return

    total_chunks = 0
    with open(NORM_INDEX, "r", encoding="utf-8") as f_in, \
         open(CHUNKS_FILE, "w", encoding="utf-8") as f_out:
        
        for line in f_in:
            doc = json.loads(line)
            with open(doc["path_to_text"], "r", encoding="utf-8") as f_md:
                text = f_md.read()

            raw_chunks = chunk_text(text)
            char_cursor = 0
            
            for idx, (chunk_str, tokens) in enumerate(raw_chunks):
                char_start = text.find(chunk_str[:30], char_cursor) if len(chunk_str) >= 30 else char_cursor
                if char_start == -1:
                    char_start = char_cursor
                char_end = char_start + len(chunk_str)
                char_cursor = max(char_cursor, char_end - 200)

                # Heading detection heuristic for section_path
                
                headings = [line.replace("#", "").strip() for line in chunk_str.split("\n") if line.startswith("#")]

                chunk_entry = {
                    "chunk_id": f"{doc['url_hash']}:{idx+1:04d}",
                    "url": doc["url"],
                    "title": doc["title"],
                    "section_path": headings if headings else ["Main Content"],
                    "page_no": 1,
                    "char_start": char_start,
                    "char_end": char_end,
                    "token_estimate": tokens,
                    "text": chunk_str
                }
                f_out.write(json.dumps(chunk_entry) + "\n")
                total_chunks += 1

if __name__ == "__main__":
    run_chunker()