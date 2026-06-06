"""Marker-based document processing pipeline.
Integrates Datalab's Marker (github.com/datalab-to/marker) as an
alternative/enhanced parser for PDF extraction.

Marker benchmarks better than Docling on legal documents (96.7% vs 87.8%).
Uses surya-ocr under the hood for layout analysis and table recognition.

Architecture: Marker is an enrichment layer. Docling remains primary.
Marker is used when:
  1. Explicitly requested via ?parser=marker
  2. Docling fails or produces low-quality output
  3. Document is a scanned image PDF (marker has superior OCR)

Graceful fallback: If marker is not installed or model loading fails,
fall back to docling_processor automatically.
"""
import os
import json
import tempfile
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class MarkerChunk:
    """A hierarchical chunk extracted by Marker."""
    chunk_id: str
    text: str
    heading: str = ""
    level: int = 0
    page_number: int = 1
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    chunk_type: str = "text"
    metadata: Dict = field(default_factory=dict)


@dataclass
class MarkerTable:
    """Table extracted from Marker markdown output."""
    table_id: str
    caption: str = ""
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    page_number: int = 1
    markdown: str = ""


class MarkerProcessor:
    """Production-grade document processor using Marker patterns.

    Falls back to docling_processor if Marker is unavailable.
    
    NOTE: Marker initialization is LAZY to avoid blocking app startup
    and consuming RAM (~4-6GB) unless explicitly requested.
    """

    def __init__(self):
        self._marker_available = None  # None = not yet attempted
        self._converter = None
        self._model_dict = None
        self._init_error = None

    def _init_marker(self):
        """Lazy-load Marker. Falls back gracefully."""
        if self._marker_available is not None:
            return self._marker_available
        try:
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
            from marker.output import text_from_rendered

            # Load models (heavy — downloads from HF on first run)
            self._model_dict = create_model_dict()
            self._converter = PdfConverter(
                artifact_dict=self._model_dict,
                config={"output_format": "markdown"}
            )
            self._marker_available = True
            print("[Marker] PdfConverter initialized successfully")
        except Exception as e:
            self._init_error = str(e)
            self._marker_available = False
            print(f"[Marker] Not available: {e}")
        return self._marker_available

    @property
    def available(self) -> bool:
        if self._marker_available is None:
            self._init_marker()
        return self._marker_available

    @property
    def init_error(self) -> Optional[str]:
        return self._init_error

    def process(self, pdf_path: str) -> Dict:
        """Full pipeline: PDF → structured chunks + tables + metadata."""
        # Lazy-init Marker only when process() is actually called
        if self._marker_available is None:
            self._init_marker()
        if self._marker_available:
            try:
                return self._process_with_marker(pdf_path)
            except Exception as e:
                print(f"[Marker] Processing failed: {e}, falling back to docling")
                return self._fallback(pdf_path)
        return self._fallback(pdf_path)

    def _process_with_marker(self, pdf_path: str) -> Dict:
        """Use Marker for layout-aware extraction."""
        from marker.output import text_from_rendered

        rendered = self._converter(pdf_path)
        markdown, _, images = text_from_rendered(rendered)

        # Build hierarchical chunks from markdown headings
        chunks = self._build_hierarchical_chunks(markdown)

        # Extract tables from markdown
        tables = self._extract_tables(markdown)

        # Extract cross-references
        cross_refs = self._extract_cross_references(markdown)

        # Extract metadata
        metadata = getattr(rendered, "metadata", {}) or {}
        page_count = metadata.get("page_count", metadata.get("num_pages", 1))

        return {
            "full_text": markdown,
            "chunks": [self._chunk_to_dict(c) for c in chunks],
            "tables": [self._table_to_dict(t) for t in tables],
            "cross_references": cross_refs,
            "page_count": page_count,
            "extracted_by": "marker",
            "images": {k: str(v) for k, v in images.items()},
        }

    def _build_hierarchical_chunks(self, markdown: str) -> List[MarkerChunk]:
        """Build legal-hierarchy chunks from Marker markdown output."""
        chunks = []
        chunk_counter = [0]

        def make_id():
            chunk_counter[0] += 1
            return f"marker_chunk_{chunk_counter[0]:04d}"

        lines = markdown.split('\n')
        current_heading = ""
        current_level = 0
        current_text = []
        current_page = 1

        for line in lines:
            line = line.strip()
            if not line:
                continue

            level = self._detect_level(line)

            if level > 0 and current_text:
                chunks.append(MarkerChunk(
                    chunk_id=make_id(),
                    text='\n'.join(current_text).strip(),
                    heading=current_heading,
                    level=current_level,
                    page_number=current_page,
                    chunk_type="text"
                ))
                current_text = []

            if level > 0:
                current_heading = line.lstrip('#').strip()
                current_level = level
            else:
                current_text.append(line)

        if current_text:
            chunks.append(MarkerChunk(
                chunk_id=make_id(),
                text='\n'.join(current_text).strip(),
                heading=current_heading,
                level=current_level,
                page_number=current_page,
                chunk_type="text"
            ))

        chunks = self._link_hierarchy(chunks)
        return chunks

    def _detect_level(self, line: str) -> int:
        """Detect hierarchy level from markdown/legal numbering."""
        if line.startswith('####'):
            return 4
        if line.startswith('###'):
            return 3
        if line.startswith('##'):
            return 2
        if line.startswith('#'):
            return 1

        import re
        if re.match(r'^\d+\.\d+\.\d+\.\d+\s', line):
            return 4
        if re.match(r'^\d+\.\d+\.\d+\s', line):
            return 3
        if re.match(r'^\d+\.\d+\s', line):
            return 2
        if re.match(r'^Article\s+\d+|^SECTION\s+\d+|^Schedule\s+\d+', line, re.I):
            return 1
        if re.match(r'^\d+\.\s+\w', line) and len(line) < 100:
            return 2

        return 0

    def _link_hierarchy(self, chunks: List[MarkerChunk]) -> List[MarkerChunk]:
        """Link chunks into parent-child hierarchy."""
        stack = []
        for chunk in chunks:
            while stack and stack[-1].level >= chunk.level:
                stack.pop()
            if stack:
                chunk.parent_id = stack[-1].chunk_id
                stack[-1].children_ids.append(chunk.chunk_id)
            stack.append(chunk)
        return chunks

    def _extract_tables(self, markdown: str) -> List[MarkerTable]:
        """Extract markdown tables from Marker output."""
        import re
        tables = []
        # Match markdown tables
        table_pattern = r'(\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n?)+)'
        for i, match in enumerate(re.finditer(table_pattern, markdown)):
            table_md = match.group(0)
            lines = [l.strip() for l in table_md.strip().split('\n') if l.strip()]
            if len(lines) < 2:
                continue
            headers = [c.strip() for c in lines[0].split('|') if c.strip()]
            rows = []
            for line in lines[2:]:
                row = [c.strip() for c in line.split('|') if c.strip()]
                if row:
                    rows.append(row)
            tables.append(MarkerTable(
                table_id=f"marker_table_{i:03d}",
                headers=headers,
                rows=rows,
                markdown=table_md,
                page_number=1
            ))
        return tables

    def _extract_cross_references(self, text: str) -> List[Dict]:
        """Find legal cross-references."""
        import re
        refs = []
        patterns = [
            r'(?:Section|Sec\.?|Clause|Cl\.?|Article|Art\.?|Schedule|Sch\.?)\s*(\d+(?:\.\d+)*(?:\([a-zA-Z]\))?)',
            r'\b(?:section|clause|article|schedule)\s*(\d+(?:\.\d+)*(?:\([a-zA-Z]\))?)',
        ]
        seen = set()
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                ref = match.group(0)
                target = match.group(1)
                if ref not in seen:
                    seen.add(ref)
                    refs.append({"reference": ref, "target": target, "position": match.start()})
        return refs

    def _chunk_to_dict(self, chunk: MarkerChunk) -> Dict:
        return {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            "heading": chunk.heading,
            "level": chunk.level,
            "page_number": chunk.page_number,
            "parent_id": chunk.parent_id,
            "children_ids": chunk.children_ids,
            "chunk_type": chunk.chunk_type,
            "metadata": chunk.metadata,
            "word_count": len(chunk.text.split()),
        }

    def _table_to_dict(self, table: MarkerTable) -> Dict:
        return {
            "table_id": table.table_id,
            "caption": table.caption,
            "headers": table.headers,
            "rows": table.rows,
            "page_number": table.page_number,
            "markdown": table.markdown,
        }

    def _fallback(self, pdf_path: str) -> Dict:
        """Fallback to docling_processor."""
        from app.services.docling_processor import docling_processor
        result = docling_processor.process(pdf_path)
        result["marker_available"] = False
        result["marker_error"] = self._init_error
        return result


_marker_processor_instance = None

def get_marker_processor() -> MarkerProcessor:
    global _marker_processor_instance
    if _marker_processor_instance is None:
        _marker_processor_instance = MarkerProcessor()
    return _marker_processor_instance
