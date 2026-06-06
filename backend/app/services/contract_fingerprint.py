"""Contract fingerprinting via MinHash + Jaccard similarity.

Deterministic, no AI required. Finds near-duplicate contracts and
clusters them by textual similarity.
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from typing import List, Dict, Tuple, Set

# ---------------------------------------------------------------------------
# MinHash parameters (tuned for legal-doc similarity)
# ---------------------------------------------------------------------------
SHINGLE_SIZE = 3          # word-level shingles
NUM_HASHES = 128          # signature length
NUM_BANDS = 16            # LSH bands
ROWS_PER_BAND = 8         # 16 × 8 = 128

# Pre-generate hash seeds for speed
SEEDS = list(range(1, NUM_HASHES + 1))


def _shingle_words(text: str, k: int = SHINGLE_SIZE) -> Set[str]:
    """Create word-level shingles (lowercased, alphanumeric only)."""
    words = [
        "".join(ch for ch in w.lower() if ch.isalnum())
        for w in text.split()
        if w.strip()
    ]
    words = [w for w in words if w]
    if len(words) < k:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + k]) for i in range(len(words) - k + 1)}


def _murmur_hash(key: str, seed: int) -> int:
    """Simple MurmurHash3-like 32-bit hash for stable cross-platform results."""
    data = key.encode("utf-8")
    length = len(data)
    nblocks = length // 4
    h = seed
    c1 = 0xCC9E2D97
    c2 = 0x1B873593
    # Body
    for i in range(nblocks):
        k = struct.unpack("<I", data[i * 4 : i * 4 + 4])[0]
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << 15) | (k >> 17)) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        h ^= k
        h = ((h << 13) | (h >> 19)) & 0xFFFFFFFF
        h = (h * 5 + 0xE6546B64) & 0xFFFFFFFF
    # Tail
    tail = data[nblocks * 4 :]
    k = 0
    if length & 3:
        if length & 3 >= 3:
            k ^= tail[2] << 16
        if length & 3 >= 2:
            k ^= tail[1] << 8
        if length & 3 >= 1:
            k ^= tail[0]
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << 15) | (k >> 17)) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        h ^= k
    # Finalization
    h ^= length
    h ^= (h >> 16)
    h = (h * 0x85EBCA6B) & 0xFFFFFFFF
    h ^= (h >> 13)
    h = (h * 0xC2B2AE35) & 0xFFFFFFFF
    h ^= (h >> 16)
    return h


def minhash_signature(shingles: Set[str]) -> List[int]:
    """Compute MinHash signature for a set of shingles."""
    if not shingles:
        return [0xFFFFFFFF] * NUM_HASHES
    sig = []
    for seed in SEEDS:
        min_val = 0xFFFFFFFF
        for shingle in shingles:
            h = _murmur_hash(shingle, seed)
            if h < min_val:
                min_val = h
        sig.append(min_val)
    return sig


def lsh_bands(signature: List[int]) -> List[int]:
    """Hash each band of the signature for LSH bucketing."""
    bands = []
    for b in range(NUM_BANDS):
        start = b * ROWS_PER_BAND
        end = start + ROWS_PER_BAND
        band_str = ",".join(str(v) for v in signature[start:end])
        bands.append(hash(band_str) & 0xFFFFFFFF)
    return bands


def jaccard_similarity(sig_a: List[int], sig_b: List[int]) -> float:
    """Estimate Jaccard from MinHash signatures."""
    matches = sum(1 for a, b in zip(sig_a, sig_b) if a == b)
    return matches / NUM_HASHES


@dataclass
class ContractFingerprint:
    contract_id: str
    title: str
    contract_type: str
    counterparty_name: str
    shingles: Set[str]
    signature: List[int]
    bands: List[int]


@dataclass
class SimilarPair:
    contract_a_id: str
    contract_a_title: str
    contract_b_id: str
    contract_b_title: str
    similarity: float


@dataclass
class ContractCluster:
    cluster_id: int
    representative_title: str
    contract_ids: List[str]
    avg_similarity: float


class FingerprintService:
    """Generate MinHash fingerprints and find similar contracts."""

    async def fingerprint_contracts(
        self,
        contract_records: List[Dict],
    ) -> List[ContractFingerprint]:
        """Create fingerprints from a list of contract dicts.

        Each dict must have keys: id, title, contract_type, counterparty_name,
        and optionally clauses (list of {clause_type, clause_text}) or parsed_text.
        """
        results = []
        for rec in contract_records:
            text_parts = []
            # Use clauses if available
            clauses = rec.get("clauses", [])
            if clauses:
                for cl in clauses:
                    ct = cl.get("clause_type", "")
                    txt = cl.get("clause_text", "")
                    if txt:
                        text_parts.append(f"[{ct}] {txt}")
            # Fallback to parsed_text
            if not text_parts and rec.get("parsed_text"):
                text_parts.append(rec["parsed_text"])
            # Fallback to title + type
            if not text_parts:
                text_parts.append(f"{rec.get('title', '')} {rec.get('contract_type', '')}")

            full_text = "\n".join(text_parts)
            shingles = _shingle_words(full_text)
            sig = minhash_signature(shingles)
            bands = lsh_bands(sig)
            results.append(
                ContractFingerprint(
                    contract_id=rec["id"],
                    title=rec.get("title", "Untitled"),
                    contract_type=rec.get("contract_type", ""),
                    counterparty_name=rec.get("counterparty_name", ""),
                    shingles=shingles,
                    signature=sig,
                    bands=bands,
                )
            )
        return results

    def find_similar_pairs(
        self,
        fingerprints: List[ContractFingerprint],
        threshold: float = 0.65,
    ) -> List[SimilarPair]:
        """Use LSH + exact MinHash to find similar pairs above threshold."""
        # LSH bucketing
        band_buckets: Dict[Tuple[int, int], List[int]] = {}
        for idx, fp in enumerate(fingerprints):
            for band_idx, band_hash in enumerate(fp.bands):
                key = (band_idx, band_hash)
                band_buckets.setdefault(key, []).append(idx)

        # Candidate pairs from shared buckets
        candidate_pairs: Set[Tuple[int, int]] = set()
        for bucket in band_buckets.values():
            if len(bucket) < 2:
                continue
            bucket.sort()
            for i in range(len(bucket)):
                for j in range(i + 1, len(bucket)):
                    a, b = bucket[i], bucket[j]
                    candidate_pairs.add((a, b) if a < b else (b, a))

        # Exact similarity for candidates
        pairs = []
        for a_idx, b_idx in candidate_pairs:
            fp_a = fingerprints[a_idx]
            fp_b = fingerprints[b_idx]
            sim = jaccard_similarity(fp_a.signature, fp_b.signature)
            if sim >= threshold:
                pairs.append(
                    SimilarPair(
                        contract_a_id=fp_a.contract_id,
                        contract_a_title=fp_a.title,
                        contract_b_id=fp_b.contract_id,
                        contract_b_title=fp_b.title,
                        similarity=round(sim, 3),
                    )
                )

        # Sort by similarity descending
        pairs.sort(key=lambda p: p.similarity, reverse=True)
        return pairs

    def cluster_contracts(
        self,
        fingerprints: List[ContractFingerprint],
        threshold: float = 0.60,
    ) -> List[ContractCluster]:
        """Simple greedy clustering: contracts with similarity >= threshold merge."""
        n = len(fingerprints)
        if n == 0:
            return []

        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry

        # Compare all pairs (n is small for demo)
        for i in range(n):
            for j in range(i + 1, n):
                sim = jaccard_similarity(
                    fingerprints[i].signature,
                    fingerprints[j].signature,
                )
                if sim >= threshold:
                    union(i, j)

        # Build clusters
        groups: Dict[int, List[int]] = {}
        for i in range(n):
            root = find(i)
            groups.setdefault(root, []).append(i)

        clusters = []
        for cid, members in enumerate(sorted(groups.values(), key=lambda m: -len(m))):
            ids = [fingerprints[i].contract_id for i in members]
            titles = [fingerprints[i].title for i in members]
            rep = titles[0]
            # Avg intra-cluster similarity
            if len(members) > 1:
                sims = []
                for i in range(len(members)):
                    for j in range(i + 1, len(members)):
                        sims.append(
                            jaccard_similarity(
                                fingerprints[members[i]].signature,
                                fingerprints[members[j]].signature,
                            )
                        )
                avg_sim = round(sum(sims) / len(sims), 3)
            else:
                avg_sim = 1.0
            clusters.append(
                ContractCluster(
                    cluster_id=cid,
                    representative_title=rep,
                    contract_ids=ids,
                    avg_similarity=avg_sim,
                )
            )
        return clusters


# Singleton
fingerprint_service = FingerprintService()
