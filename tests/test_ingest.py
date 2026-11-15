"""Testy parsowania Markdowna na bloki (bez sieci)."""

from rag.ingest import load_markdown, source_ids_for


def test_repeated_heading_gets_unique_source_id(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("# Debugging\n\nIntro.\n\n# Exercises\n\n## Debugging\n\nTask.\n")
    ids = [source_ids_for(b.metadata)[0] for b in load_markdown(path)]
    assert [i.split("#", 1)[1] for i in ids] == ["Debugging", "Exercises", "Debugging (2)"]
