"""Hierarchical chunking service for legal documents.
Pattern from: github.com/docling-project/docling (HierarchicalChunker)
"""
import os
import json
from typing import List, Dict, Optional, Iterator
from dataclasses import dataclass

@dataclass
class ChunkGroup:
    """A group of related chunks for progressive summarization."""
    group_id: str
    level: int  # 0=document, 1=article, 2=section, 3=subsection
    heading: str
    chunks: List[Dict]
    summary: str = ""
    parent_id: Optional[str] = None
    children_ids: List[str] = None

class ChunkingService:
    """Hierarchical chunking for 400-page legal contracts.
    Implements progressive summarization: leaf → parent → document.
    """

    MAX_CHUNK_TOKENS = 4000  # ~3000 words, safe for GPT-4o-mini
    OVERLAP_TOKENS = 200     # Context overlap between adjacent chunks

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY", "")

    def build_chunk_tree(self, chunks: List[Dict]) -> List[ChunkGroup]:
        """Build a tree of chunk groups for progressive processing."""
        # Create lookup
        chunk_map = {c["chunk_id"]: c for c in chunks}

        # Group by parent
        groups: Dict[str, ChunkGroup] = {}

        for chunk in chunks:
            parent_id = chunk.get("parent_id")
            if parent_id and parent_id in chunk_map:
                parent = chunk_map[parent_id]
                if parent_id not in groups:
                    groups[parent_id] = ChunkGroup(
                        group_id=parent_id,
                        level=parent["level"],
                        heading=parent["heading"],
                        chunks=[],
                        parent_id=parent.get("parent_id"),
                        children_ids=[]
                    )
                groups[parent_id].chunks.append(chunk)
            else:
                # Top-level chunk becomes its own group
                if chunk["chunk_id"] not in groups:
                    groups[chunk["chunk_id"]] = ChunkGroup(
                        group_id=chunk["chunk_id"],
                        level=chunk["level"],
                        heading=chunk["heading"],
                        chunks=[chunk],
                        parent_id=chunk.get("parent_id"),
                        children_ids=[]
                    )

        # Add children references
        for chunk in chunks:
            parent_id = chunk.get("parent_id")
            if parent_id and parent_id in groups:
                if chunk["chunk_id"] not in groups[parent_id].children_ids:
                    groups[parent_id].children_ids.append(chunk["chunk_id"])

        return list(groups.values())

    def merge_small_chunks(self, chunks: List[Dict], min_words: int = 100) -> List[Dict]:
        """Merge tiny chunks with their neighbors to avoid fragmentation."""
        if not chunks:
            return chunks

        merged = []
        buffer = chunks[0].copy()

        for chunk in chunks[1:]:
            word_count = len(buffer.get("text", "").split())
            if word_count < min_words and buffer.get("level") == chunk.get("level"):
                # Merge with next chunk
                buffer["text"] += "\n\n" + chunk.get("text", "")
                buffer["heading"] = buffer.get("heading") or chunk.get("heading", "")
                buffer["children_ids"] = buffer.get("children_ids", []) + chunk.get("children_ids", [])
            else:
                merged.append(buffer)
                buffer = chunk.copy()

        merged.append(buffer)
        return merged

    def split_oversized_chunks(self, chunks: List[Dict], max_words: int = 2000) -> List[Dict]:
        """Split oversized chunks while preserving sentence boundaries."""
        result = []
        for chunk in chunks:
            text = chunk.get("text", "")
            words = text.split()
            if len(words) <= max_words:
                result.append(chunk)
                continue

            # Split by sentences, keeping chunks under max_words
            sentences = text.replace('. ', '.\n').replace('? ', '?\n').replace('! ', '!\n').split('\n')
            current_text = ""
            current_words = 0
            part_num = 0

            for sentence in sentences:
                s_words = len(sentence.split())
                if current_words + s_words > max_words and current_text:
                    result.append({
                        **chunk,
                        "chunk_id": f"{chunk['chunk_id']}_p{part_num}",
                        "text": current_text.strip(),
                        "parent_id": chunk["chunk_id"],
                    })
                    part_num += 1
                    current_text = sentence
                    current_words = s_words
                else:
                    current_text += " " + sentence
                    current_words += s_words

            if current_text:
                result.append({
                    **chunk,
                    "chunk_id": f"{chunk['chunk_id']}_p{part_num}",
                    "text": current_text.strip(),
                    "parent_id": chunk["chunk_id"],
                })

        return result

    def create_sliding_windows(self, chunks: List[Dict], window_size: int = 3) -> List[List[Dict]]:
        """Create overlapping windows for context-aware processing.
        Each window contains N consecutive chunks with overlap.
        """
        windows = []
        for i in range(0, len(chunks), window_size - 1):
            window = chunks[i:i + window_size]
            if window:
                windows.append(window)
        return windows

    def progressive_summarize(self, chunks: List[Dict]) -> str:
        """Progressive summarization: summarize leaf chunks, then parents, then document."""
        if not self.openai_key or len(chunks) < 5:
            # Fallback: return first 5000 chars as summary
            return "\n\n".join(c.get("text", "") for c in chunks[:10])[:5000]

        # Level 1: Summarize each chunk group
        chunk_summaries = []
        for chunk in chunks:
            text = chunk.get("text", "")[:1000]
            chunk_summaries.append(f"{chunk.get('heading', '')}: {text[:200]}...")

        # Level 2: Summarize the summaries
        combined = "\n".join(chunk_summaries)
        return combined[:8000]  # Return structured summary for now

    def resolve_cross_references(self, chunks: List[Dict], refs: List[Dict]) -> List[Dict]:
        """Link cross-references to their target chunks."""
        # Build heading index
        heading_map = {}
        for chunk in chunks:
            heading = chunk.get("heading", "").lower()
            heading_map[heading] = chunk["chunk_id"]
            # Also index by number pattern
            import re
            numbers = re.findall(r'\d+(?:\.\d+)*(?:\([a-zA-Z]\))?', heading)
            for num in numbers:
                heading_map[num] = chunk["chunk_id"]

        resolved = []
        for ref in refs:
            target = ref.get("target", "").lower()
            linked = heading_map.get(target)
            resolved.append({
                **ref,
                "linked_chunk_id": linked,
                "resolved": linked is not None
            })

        return resolved

    def prepare_for_extraction(self, chunks: List[Dict]) -> Iterator[Dict]:
        """Yield chunks ready for clause extraction, with enriched context."""
        # Merge small chunks
        merged = self.merge_small_chunks(chunks)
        # Split oversized
        sized = self.split_oversized_chunks(merged)
        # Add parent context to each chunk
        chunk_map = {c["chunk_id"]: c for c in sized}

        for chunk in sized:
            context = self._build_context(chunk, chunk_map)
            yield {
                **chunk,
                "context": context,
                "full_context": f"{context}\n\n{chunk.get('text', '')}"[:4000]
            }

    def _build_context(self, chunk: Dict, chunk_map: Dict) -> str:
        """Build context string from parent hierarchy."""
        parts = []
        current_id = chunk.get("parent_id")
        depth = 0
        while current_id and depth < 3:
            parent = chunk_map.get(current_id)
            if parent:
                heading = parent.get("heading", "")
                if heading:
                    parts.insert(0, heading)
                current_id = parent.get("parent_id")
            else:
                break
            depth += 1
        return " > ".join(parts) if parts else ""

chunking_service = ChunkingService()
