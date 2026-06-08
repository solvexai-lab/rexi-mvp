"""Docling-based document processing pipeline.
Pattern from: github.com/docling-project/docling
Replaces naive PyMuPDF extraction for 400-page legal contracts.
"""
import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class DocChunk:
    """A hierarchical chunk of a legal document."""
    chunk_id: str
    text: str
    heading: str = ""
    level: int = 0  # 0=document, 1=article, 2=section, 3=subsection, 4=clause
    page_number: int = 1
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    chunk_type: str = "text"  # text, table, list, formula
    metadata: Dict = field(default_factory=dict)

@dataclass
class DocTable:
    """Extracted table with structured data."""
    table_id: str
    caption: str = ""
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    page_number: int = 1
    markdown: str = ""

class DoclingProcessor:
    """Production-grade document processor using Docling patterns.
    Falls back to PyMuPDF if Docling is not installed.
    """

    def __init__(self):
        self._docling_available = False
        self._converter = None
        self._init_docling()

    def _init_docling(self):
        """Lazy-load Docling. Falls back gracefully."""
        try:
            from docling.document_converter import DocumentConverter
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.datamodel.document import ConversionResult
            self._converter = DocumentConverter()
            self._docling_available = True
            print("[Docling] DocumentConverter initialized")
        except Exception:
            print("[Docling] Not installed. Falling back to PyMuPDF + heuristic chunking.")
            self._docling_available = False

    def process(self, pdf_path: str) -> Dict:
        """Full pipeline: PDF → structured chunks + tables + metadata."""
        if self._docling_available:
            return self._process_with_docling(pdf_path)
        return self._process_fallback(pdf_path)

    def _process_with_docling(self, pdf_path: str) -> Dict:
        """Use Docling for layout-aware extraction."""
        result = self._converter.convert(pdf_path)
        doc = result.document

        # Export to markdown for human readability
        markdown = doc.export_to_markdown()

        # Build hierarchical chunks from Docling's structured output
        chunks = self._build_hierarchical_chunks(doc)

        # Extract tables
        tables = self._extract_tables(doc)

        # Extract cross-references
        cross_refs = self._extract_cross_references(markdown)

        return {
            "full_text": markdown,
            "chunks": [self._chunk_to_dict(c) for c in chunks],
            "tables": [self._table_to_dict(t) for t in tables],
            "cross_references": cross_refs,
            "page_count": len(doc.pages) if hasattr(doc, 'pages') else 1,
            "extracted_by": "docling"
        }

    def _build_hierarchical_chunks(self, doc) -> List[DocChunk]:
        """Build legal-hierarchy chunks from Docling document."""
        chunks = []
        chunk_counter = [0]

        def make_id():
            chunk_counter[0] += 1
            return f"chunk_{chunk_counter[0]:04d}"

        # Docling provides text with provenance (page numbers, bounding boxes)
        # We iterate through the document's text units and group by headings
        current_heading = ""
        current_level = 0
        current_text = []
        current_page = 1

        # Simple heuristic: split by markdown headings and legal numbering patterns
        text = doc.export_to_markdown()
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect heading levels
            level = self._detect_level(line)

            if level > 0 and current_text:
                # Save previous chunk
                chunks.append(DocChunk(
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

        # Save final chunk
        if current_text:
            chunks.append(DocChunk(
                chunk_id=make_id(),
                text='\n'.join(current_text).strip(),
                heading=current_heading,
                level=current_level,
                page_number=current_page,
                chunk_type="text"
            ))

        # Link parent-child relationships
        chunks = self._link_hierarchy(chunks)
        return chunks

    def _detect_level(self, line: str) -> int:
        """Detect hierarchy level from markdown/legal numbering."""
        # Markdown headings
        if line.startswith('####'):
            return 4
        if line.startswith('###'):
            return 3
        if line.startswith('##'):
            return 2
        if line.startswith('#'):
            return 1

        # Legal numbering patterns
        import re
        if re.match(r'^\d+\.\d+\.\d+\.\d+\s', line):
            return 4  # 1.2.3.4
        if re.match(r'^\d+\.\d+\.\d+\s', line):
            return 3  # 1.2.3
        if re.match(r'^\d+\.\d+\s', line):
            return 2  # 1.2
        if re.match(r'^Article\s+\d+|^SECTION\s+\d+|^Schedule\s+\d+', line, re.I):
            return 1
        if re.match(r'^\d+\.\s+\w', line) and len(line) < 100:
            return 2  # Numbered section

        return 0

    def _link_hierarchy(self, chunks: List[DocChunk]) -> List[DocChunk]:
        """Link chunks into parent-child hierarchy."""
        stack = []
        for chunk in chunks:
            # Pop stack until we find parent with lower level
            while stack and stack[-1].level >= chunk.level:
                stack.pop()
            if stack:
                chunk.parent_id = stack[-1].chunk_id
                stack[-1].children_ids.append(chunk.chunk_id)
            stack.append(chunk)
        return chunks

    def _extract_tables(self, doc) -> List[DocTable]:
        """Extract tables from Docling document."""
        tables = []
        if hasattr(doc, 'tables'):
            for i, table in enumerate(doc.tables):
                try:
                    df = table.export_to_dataframe(doc=doc)
                    tables.append(DocTable(
                        table_id=f"table_{i:03d}",
                        headers=list(df.columns),
                        rows=[list(row) for _, row in df.head(50).iterrows()],  # Limit rows
                        markdown=df.to_markdown(index=False) if hasattr(df, 'to_markdown') else str(df),
                        page_number=table.prov[0].page_no if hasattr(table, 'prov') and table.prov else 1
                    ))
                except Exception:
                    pass
        return tables

    def _extract_cross_references(self, text: str) -> List[Dict]:
        """Find legal cross-references like 'Section 4.2(a)' or 'Clause 5.3'."""
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

    def _chunk_to_dict(self, chunk: DocChunk) -> Dict:
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

    def _table_to_dict(self, table: DocTable) -> Dict:
        return {
            "table_id": table.table_id,
            "caption": table.caption,
            "headers": table.headers,
            "rows": table.rows,
            "page_number": table.page_number,
            "markdown": table.markdown,
        }

    def _process_fallback(self, pdf_path: str) -> Dict:
        """Fallback: PyMuPDF + heuristic chunking."""
        import fitz
        doc = fitz.open(pdf_path)
        full_text = ""
        chunks = []
        chunk_counter = [0]

        def make_id():
            chunk_counter[0] += 1
            return f"chunk_{chunk_counter[0]:04d}"

        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            full_text += text + "\n\n"

            # Heuristic: split page by legal numbering
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 20]
            current_heading = f"Page {page_num}"
            current_level = 1
            current_text = []

            for para in paragraphs:
                level = self._detect_level(para)
                if level > 0 and current_text:
                    chunks.append(DocChunk(
                        chunk_id=make_id(),
                        text='\n'.join(current_text),
                        heading=current_heading,
                        level=current_level,
                        page_number=page_num,
                        chunk_type="text"
                    ))
                    current_text = []
                    current_heading = para
                    current_level = level
                else:
                    current_text.append(para)

            if current_text:
                chunks.append(DocChunk(
                    chunk_id=make_id(),
                    text='\n'.join(current_text),
                    heading=current_heading,
                    level=current_level,
                    page_number=page_num,
                    chunk_type="text"
                ))

        chunks = self._link_hierarchy(chunks)
        cross_refs = self._extract_cross_references(full_text)

        return {
            "full_text": full_text,
            "chunks": [self._chunk_to_dict(c) for c in chunks],
            "tables": [],
            "cross_references": cross_refs,
            "page_count": len(doc),
            "extracted_by": "pymupdf_fallback"
        }

docling_processor = DoclingProcessor()
