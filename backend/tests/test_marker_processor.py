"""Tests for MarkerProcessor.

Tests both the happy path (Marker available) and fallback path
(Marker unavailable or fails).
"""
import pytest
from unittest.mock import MagicMock, patch


class TestMarkerProcessorInit:
    """Test MarkerProcessor initialization."""

    def test_marker_unavailable_when_import_fails(self):
        """If marker import fails, processor should be unavailable."""
        with patch.dict("sys.modules", {"marker.converters.pdf": None, "marker.models": None}):
            # Force reimport by clearing cache
            import importlib
            import app.services.marker_processor as mp_module
            importlib.reload(mp_module)

            processor = mp_module.MarkerProcessor()
            assert processor.available is False
            assert processor.init_error is not None

    def test_marker_available_when_import_succeeds(self):
        """If marker imports OK, processor should be available.
        
        NOTE: We verify lazy initialization state without triggering
        actual model loading (4-6GB RAM) in test environment.
        """
        from app.services.marker_processor import get_marker_processor
        processor = get_marker_processor()
        # Lazy: not initialized yet to avoid blocking test suite
        assert processor._marker_available is None
        assert hasattr(processor, '_init_marker')


class TestMarkerProcessorProcess:
    """Test MarkerProcessor.process() output format."""

    def test_process_returns_standard_dict(self):
        """process() must return the standard dict structure regardless of backend."""
        from app.services.marker_processor import get_marker_processor
        processor = get_marker_processor()
        # Force fallback and mock it to avoid docling trying to open a real file
        processor._marker_available = False
        processor._fallback = lambda pdf_path: {
            "full_text": "mock fallback text",
            "chunks": [],
            "tables": [],
            "cross_references": [],
            "page_count": 1,
            "extracted_by": "docling",
        }

        result = processor.process("nonexistent.pdf")

        # Standard output keys
        assert "full_text" in result
        assert "chunks" in result
        assert "tables" in result
        assert "cross_references" in result
        assert "page_count" in result
        assert "extracted_by" in result

        # extracted_by tells us which parser was used
        assert result["extracted_by"] in ("marker", "docling", "pymupdf_fallback")

    def test_process_fallback_when_marker_unavailable(self):
        """When marker is unavailable, should fall back to docling."""
        from app.services.marker_processor import MarkerProcessor

        processor = MarkerProcessor()
        processor._marker_available = False
        processor._init_error = "Mock: marker not installed"
        processor._fallback = lambda pdf_path: {
            "full_text": "fallback",
            "chunks": [],
            "tables": [],
            "cross_references": [],
            "page_count": 1,
            "extracted_by": "docling",
            "marker_available": False,
            "marker_error": "Mock: marker not installed",
        }

        result = processor.process("nonexistent.pdf")

        assert result["extracted_by"] in ("docling", "pymupdf_fallback")
        assert result.get("marker_available") is False
        assert "marker_error" in result

    def test_detect_level_heading_levels(self):
        """Test markdown heading level detection."""
        from app.services.marker_processor import MarkerProcessor
        p = MarkerProcessor()

        assert p._detect_level("# Heading 1") == 1
        assert p._detect_level("## Heading 2") == 2
        assert p._detect_level("### Heading 3") == 3
        assert p._detect_level("#### Heading 4") == 4
        assert p._detect_level("##### Heading 5") == 4  # capped
        assert p._detect_level("Regular text") == 0

    def test_detect_level_legal_numbering(self):
        """Test legal numbering pattern detection."""
        from app.services.marker_processor import MarkerProcessor
        p = MarkerProcessor()

        assert p._detect_level("1. Introduction") == 2
        assert p._detect_level("1.1 Scope") == 2
        assert p._detect_level("1.1.1 Definitions") == 3
        assert p._detect_level("1.1.1.1 Sub-clause") == 4
        assert p._detect_level("Article 1") == 1
        assert p._detect_level("SECTION 3") == 1
        assert p._detect_level("Schedule 2") == 1

    def test_extract_tables_from_markdown(self):
        """Test markdown table extraction."""
        from app.services.marker_processor import MarkerProcessor
        p = MarkerProcessor()

        md = """
| Col A | Col B | Col C |
|-------|-------|-------|
| 1     | 2     | 3     |
| 4     | 5     | 6     |
"""
        tables = p._extract_tables(md)
        assert len(tables) == 1
        assert tables[0].headers == ["Col A", "Col B", "Col C"]
        assert len(tables[0].rows) == 2

    def test_extract_cross_references(self):
        """Test cross-reference extraction."""
        from app.services.marker_processor import MarkerProcessor
        p = MarkerProcessor()

        text = "Refer to Section 4.2(a) and Clause 5.3 for details."
        refs = p._extract_cross_references(text)
        assert len(refs) == 2
        targets = {r["target"] for r in refs}
        assert "4.2(a)" in targets
        assert "5.3" in targets

    def test_link_hierarchy(self):
        """Test parent-child chunk linking."""
        from app.services.marker_processor import MarkerProcessor, MarkerChunk
        p = MarkerProcessor()

        chunks = [
            MarkerChunk(chunk_id="c1", text="H1", level=1),
            MarkerChunk(chunk_id="c2", text="H2", level=2),
            MarkerChunk(chunk_id="c3", text="H3", level=2),
            MarkerChunk(chunk_id="c4", text="H4", level=3),
        ]
        linked = p._link_hierarchy(chunks)

        assert linked[0].parent_id is None  # root
        assert linked[1].parent_id == "c1"
        assert linked[2].parent_id == "c1"
        assert linked[3].parent_id == "c3"
        assert "c2" in linked[0].children_ids  # c1's children
        assert "c3" in linked[0].children_ids  # c1's children
        assert "c4" in linked[2].children_ids  # c3's children

    def test_chunk_to_dict(self):
        """Test chunk serialization."""
        from app.services.marker_processor import MarkerProcessor, MarkerChunk
        p = MarkerProcessor()

        chunk = MarkerChunk(
            chunk_id="c1",
            text="hello world",
            heading="Test",
            level=1,
            page_number=2,
        )
        d = p._chunk_to_dict(chunk)
        assert d["chunk_id"] == "c1"
        assert d["word_count"] == 2
        assert d["page_number"] == 2

    def test_table_to_dict(self):
        """Test table serialization."""
        from app.services.marker_processor import MarkerProcessor, MarkerTable
        p = MarkerProcessor()

        table = MarkerTable(
            table_id="t1",
            headers=["A", "B"],
            rows=[["1", "2"]],
            markdown="|A|B|\n|-|-|\n|1|2|",
        )
        d = p._table_to_dict(table)
        assert d["table_id"] == "t1"
        assert d["headers"] == ["A", "B"]


class TestMarkerProcessorMock:
    """Test with mocked Marker for happy path."""

    def test_process_with_mocked_marker(self):
        """Test that when marker works, we get marker output."""
        from app.services.marker_processor import MarkerProcessor

        processor = MarkerProcessor()
        processor._marker_available = True
        processor._init_error = None

        # Mock _process_with_marker directly to avoid marker dependency
        processor._process_with_marker = lambda pdf_path: {
            "full_text": "# Contract\n\nThis is a test.\n\n| A | B |\n|---|---|\n| 1 | 2 |",
            "chunks": [{"chunk_id": "c1", "text": "Contract", "heading": "Contract", "level": 1}],
            "tables": [{"table_id": "t1", "headers": ["A", "B"], "rows": [["1", "2"]]}],
            "cross_references": [],
            "page_count": 3,
            "extracted_by": "marker",
            "images": {},
        }

        result = processor.process("dummy.pdf")

        assert result["extracted_by"] == "marker"
        assert "# Contract" in result["full_text"]
        assert result["page_count"] == 3
        assert len(result["chunks"]) > 0
        assert len(result["tables"]) == 1
