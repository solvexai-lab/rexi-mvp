"""Lightweight PageIndex-compatible document tree builder.

Builds hierarchical tree indices from markdown without requiring litellm.
Uses Gemini for optional node summarization.

Tree structure format is compatible with PageIndex for future migration.
"""
import os
import re
import json
import tempfile
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


@dataclass
class TreeNode:
    """A node in the document tree."""
    title: str
    node_id: str = ""
    text: str = ""
    line_num: int = 0
    level: int = 0
    summary: str = ""
    nodes: List["TreeNode"] = field(default_factory=list)

    def to_dict(self) -> Dict:
        d = {
            "title": self.title,
            "node_id": self.node_id,
            "line_num": self.line_num,
            "text": self.text,
        }
        if self.summary:
            d["summary"] = self.summary
        if self.nodes:
            d["nodes"] = [n.to_dict() for n in self.nodes]
        return d


class PageIndexService:
    """Build hierarchical document trees from markdown text.
    
    Disabled when GEMINI_API_KEY is absent (summarization requires LLM).
    Pure tree building works without API key.
    """

    def __init__(self):
        self._gemini_key = GEMINI_API_KEY
        self._enabled = True
        self._model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def status(self) -> Dict:
        return {
            "enabled": self._enabled,
            "gemini_available": bool(self._gemini_key),
            "model": self._model,
        }

    def build_tree_from_markdown(
        self,
        markdown: str,
        doc_name: str = "document",
        add_summaries: bool = True,
    ) -> Dict:
        """Build a hierarchical tree from markdown text.
        
        Returns a dict compatible with PageIndex structure:
        {
            "doc_name": str,
            "structure": [TreeNode dicts],
            "line_count": int,
        }
        """
        if not markdown or not markdown.strip():
            return {"doc_name": doc_name, "structure": [], "line_count": 0}

        lines = markdown.split("\n")
        line_count = len(lines)

        # Extract headers
        node_list = self._extract_nodes(markdown)
        # Attach text content to each node
        nodes_with_text = self._attach_text(node_list, lines)
        # Build hierarchical tree
        tree = self._build_tree(nodes_with_text)
        # Assign node IDs
        self._assign_node_ids(tree)

        # Optionally generate summaries with Gemini
        if add_summaries and self._gemini_key:
            self._generate_summaries(tree)

        return {
            "doc_name": doc_name,
            "structure": [n.to_dict() for n in tree],
            "line_count": line_count,
        }

    def _extract_nodes(self, markdown: str) -> List[Dict]:
        """Extract markdown headers into a flat list."""
        header_pattern = r"^(#{1,6})\s+(.+)$"
        code_block_pattern = r"^```"
        nodes = []
        in_code_block = False

        for line_num, line in enumerate(markdown.split("\n"), 1):
            stripped = line.strip()
            if re.match(code_block_pattern, stripped):
                in_code_block = not in_code_block
                continue
            if in_code_block or not stripped:
                continue
            match = re.match(header_pattern, stripped)
            if match:
                nodes.append({
                    "title": match.group(2).strip(),
                    "level": len(match.group(1)),
                    "line_num": line_num,
                })
        return nodes

    def _attach_text(self, nodes: List[Dict], lines: List[str]) -> List[Dict]:
        """Attach text content between headers to each node."""
        result = []
        for i, node in enumerate(nodes):
            start = node["line_num"] - 1
            end = nodes[i + 1]["line_num"] - 1 if i + 1 < len(nodes) else len(lines)
            text = "\n".join(lines[start:end]).strip()
            result.append({**node, "text": text})
        return result

    def _build_tree(self, nodes: List[Dict]) -> List[TreeNode]:
        """Build hierarchical tree from flat node list."""
        root_nodes: List[TreeNode] = []
        stack: List[tuple] = []  # (TreeNode, level)

        for node in nodes:
            level = node["level"]
            tree_node = TreeNode(
                title=node["title"],
                text=node["text"],
                line_num=node["line_num"],
                level=level,
            )
            while stack and stack[-1][1] >= level:
                stack.pop()
            if stack:
                parent, _ = stack[-1]
                parent.nodes.append(tree_node)
            else:
                root_nodes.append(tree_node)
            stack.append((tree_node, level))
        return root_nodes

    def _assign_node_ids(self, nodes: List[TreeNode], prefix: str = ""):
        """Assign sequential node IDs to all nodes."""
        counter = [0]

        def _assign(node_list: List[TreeNode], parent_prefix: str = ""):
            for i, node in enumerate(node_list):
                if parent_prefix:
                    node.node_id = f"{parent_prefix}.{i + 1}"
                else:
                    node.node_id = f"{i + 1}"
                counter[0] += 1
                if node.nodes:
                    _assign(node.nodes, node.node_id)

        _assign(nodes)

    def _generate_summaries(self, nodes: List[TreeNode]):
        """Generate summaries for each node using Gemini (async-safe wrapper)."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, run summaries in executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(asyncio.run, self._summarize_all(nodes)).result(timeout=60)
        except RuntimeError:
            asyncio.run(self._summarize_all(nodes))

    async def _summarize_all(self, nodes: List[TreeNode]):
        """Recursively generate summaries for all nodes."""
        tasks = []
        for node in nodes:
            if node.text and len(node.text) > 200:
                tasks.append(self._summarize_node(node))
            if node.nodes:
                tasks.append(self._summarize_all(node.nodes))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _summarize_node(self, node: TreeNode):
        """Call Gemini to summarize a single node."""
        try:
            from app.services.gemini_service import _gemini_generate
            prompt = (
                f"Summarize the following contract section in 1-2 sentences. "
                f"Be concise and capture the key legal points.\n\n"
                f"Section: {node.title}\n"
                f"Content:\n{node.text[:3000]}"
            )
            summary = await _gemini_generate(prompt, temperature=0.1)
            node.summary = summary.strip()[:500]
        except Exception:
            pass

    def query_tree(self, tree: Dict, query: str) -> List[Dict]:
        """Simple keyword-based tree search (fallback when LLM unavailable).
        
        Returns matching nodes with relevance scores.
        """
        results = []
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        if not query_terms:
            return results

        def _search(nodes: List[Dict], path: str = ""):
            for node in nodes:
                current_path = f"{path} > {node['title']}" if path else node["title"]
                text = (node.get("text", "") + " " + node.get("summary", "")).lower()
                score = sum(1 for t in query_terms if t in text or t in node["title"].lower())
                if score > 0:
                    results.append({
                        "node_id": node.get("node_id", ""),
                        "title": node["title"],
                        "path": current_path,
                        "score": score / len(query_terms),
                        "text_preview": node.get("text", "")[:300],
                    })
                if "nodes" in node:
                    _search(node["nodes"], current_path)

        _search(tree.get("structure", []))
        results.sort(key=lambda x: (-x["score"], x["title"]))
        return results

    def flatten_tree(self, tree: Dict) -> List[Dict]:
        """Flatten tree into a list of all nodes with paths."""
        results = []

        def _flatten(nodes: List[Dict], path: str = ""):
            for node in nodes:
                current_path = f"{path} > {node['title']}" if path else node["title"]
                results.append({
                    "node_id": node.get("node_id", ""),
                    "title": node["title"],
                    "path": current_path,
                    "line_num": node.get("line_num", 0),
                    "text_preview": node.get("text", "")[:200],
                    "has_children": bool(node.get("nodes")),
                })
                if "nodes" in node:
                    _flatten(node["nodes"], current_path)

        _flatten(tree.get("structure", []))
        return results


pageindex_service = PageIndexService()
