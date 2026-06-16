import pytest

from shared_core.docparse import (
    ChunkStrategy,
    MarkdownParser,
    ParsedDocument,
    chunk_text,
    compute_hash,
    filter_duplicates,
    get_parser,
    is_duplicate,
)
from shared_core.errors import ValidationError


def test_markdown_parser_extracts_title():
    doc = MarkdownParser().parse(b"# Heading\n\nBody text", filename="a.md")
    assert isinstance(doc, ParsedDocument)
    assert doc.title == "Heading"
    assert "Body text" in doc.text
    assert doc.metadata["source"] == "a.md"


def test_get_parser_by_extension_and_unknown():
    assert isinstance(get_parser("notes.md"), MarkdownParser)
    assert isinstance(get_parser("text/plain"), MarkdownParser)
    with pytest.raises(ValidationError):
        get_parser("archive.zip")


def test_chunk_text_fixed_with_overlap():
    text = "abcdefghij" * 6  # 60 chars
    chunks = chunk_text(text, strategy=ChunkStrategy.FIXED, chunk_size=20, overlap=5)
    assert len(chunks) > 1
    assert all(len(c) <= 20 for c in chunks)
    # Reassembled coverage: first chunk is the prefix
    assert chunks[0] == text[:20]


def test_chunk_text_semantic_and_structural():
    semantic = chunk_text(
        "First sentence. Second sentence. Third one.",
        strategy=ChunkStrategy.SEMANTIC,
        chunk_size=20,
    )
    assert len(semantic) >= 2
    structural = chunk_text(
        "# A\nalpha\n# B\nbeta",
        strategy=ChunkStrategy.STRUCTURAL,
        chunk_size=100,
    )
    assert len(structural) == 2


def test_chunk_text_empty():
    assert chunk_text("") == []


def test_hash_and_dedup():
    h1 = compute_hash("same")
    h2 = compute_hash(b"same")
    assert h1 == h2
    seen = {h1}
    assert is_duplicate(h1, seen)
    assert not is_duplicate(compute_hash("other"), seen)


def test_filter_duplicates_preserves_order():
    items = ["a", "b", "a", "c", "b"]
    assert filter_duplicates(items, key=compute_hash) == ["a", "b", "c"]
