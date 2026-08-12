import os
import json
import re
import spacy

CHUNKS_FILE = "chunks/chunks.jsonl"
NER_DIR = "ner"
ANNOTATIONS_FILE = os.path.join(NER_DIR, "annotations.jsonl")

os.makedirs(NER_DIR, exist_ok=True)

try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = spacy.blank("en")

REGEX_PATTERNS = {
    "SECTION_REF": r"(?i)\b(?:section|sec\.|article|order|rule)\s+\d+(?:\(\d+\))*(?:\([a-z]\))*",
    "DATE": r"\b(?:\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{2}[-/]\d{2}[-/]\d{4})\b",
    "MONEY": r"(?:₹|\$|USD\s*|INR\s*)\d+(?:,\d+)*(?:\.\d+)?"
}

ACT_NAME_PATTERN = r"\b[A-Z][a-zA-Z\s]+Act,\s*\d{4}\b"

def extract_entities(text: str):
    entities = []
    
    # Rule/Regex Extraction
    for label, pattern in REGEX_PATTERNS.items():
        for match in re.finditer(pattern, text):
            entities.append({
                "label": label,
                "text": match.group(0),
                "start": match.start(),
                "end": match.end()
            })

    # Act Name Heuristic Regex
    for match in re.finditer(ACT_NAME_PATTERN, text):
        entities.append({
            "label": "ACT_NAME",
            "text": match.group(0),
            "start": match.start(),
            "end": match.end()
        })

    # spaCy ML Extraction for ORG
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "ORG":
            entities.append({
                "label": "ORG",
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char
            })

    return entities

def run_ner():
    if not os.path.exists(CHUNKS_FILE):
        return

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f_in, \
         open(ANNOTATIONS_FILE, "w", encoding="utf-8") as f_out:
        for line in f_in:
            chunk = json.loads(line)
            extracted = extract_entities(chunk["text"])
            output = {
                "chunk_id": chunk["chunk_id"],
                "entities": extracted
            }
            f_out.write(json.dumps(output) + "\n")

if __name__ == "__main__":
    run_ner()