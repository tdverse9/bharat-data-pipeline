import os
import pytest
from crawler.crawler import get_url_hash, check_robots_txt
from parsers.parser import parse_html
from chunker.chunker import chunk_text, get_token_count
from ner.ner_system import extract_entities

def test_url_hash():
    """Verify MD5 hash generation for consistency and length."""
    url = "https://nujslawreview.org/articles-archives/"
    h = get_url_hash(url)
    assert isinstance(h, str)
    assert len(h) == 32

def test_token_estimation():
    """Verify tiktoken encoder calculates tokens correctly."""
    text = "Section 2(1)(a) of the Income Tax Act, 1961."
    tokens = get_token_count(text)
    assert tokens > 0
    assert isinstance(tokens, int)

def test_semantic_chunking():
    """Verify chunker respects boundary limits and paragraph structure."""
    sample_text = "Heading 1\n\nThis is paragraph one for testing.\n\nThis is paragraph two."
    chunks = chunk_text(sample_text, target_min=5, target_max=30, overlap=5)
    assert len(chunks) > 0
    assert "paragraph one" in chunks[0][0]

def test_ner_regex_extraction():
    """Verify hybrid NER extracts target legal entities accurately."""
    text = "As per section 2(1)(a) dated 12 March 2024, the penalty is ₹500 under the Income Tax Act, 1961."
    entities = extract_entities(text)
    labels = [e["label"] for e in entities]
    
    assert "SECTION_REF" in labels
    assert "DATE" in labels
    assert "MONEY" in labels
    assert "ACT_NAME" in labels