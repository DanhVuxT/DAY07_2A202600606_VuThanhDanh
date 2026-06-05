"""
Day 07 demo for Vu Thanh Danh.

Run from repo root:
    python scripts/vector_store_demo.py

This script is intentionally offline. It demonstrates the full RAG data pipeline
without API keys: load documents, attach metadata, sentence chunking, keyword
embeddings, vector search, metadata filtering, benchmark queries and failure case.
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import (  # noqa: E402
    ChunkingStrategyComparator,
    Document,
    EmbeddingStore,
    SentenceChunker,
    compute_similarity,
)

DATA_FILES = [
    ROOT / "data" / "python_intro.txt",
    ROOT / "data" / "vector_store_notes.md",
    ROOT / "data" / "rag_system_design.md",
    ROOT / "data" / "customer_support_playbook.txt",
    ROOT / "data" / "chunking_experiment_report.md",
    ROOT / "data" / "vi_retrieval_notes.md",
]

METADATA_BY_FILE = {
    "python_intro.txt": {
        "source": "data/python_intro.txt",
        "category": "programming",
        "language": "en",
        "owner": "Python / AI study notes",
        "doc_type": "technical_note",
        "pii": "no",
    },
    "vector_store_notes.md": {
        "source": "data/vector_store_notes.md",
        "category": "vector_store",
        "language": "en",
        "owner": "Group RAG notes",
        "doc_type": "technical_note",
        "pii": "no",
    },
    "rag_system_design.md": {
        "source": "data/rag_system_design.md",
        "category": "rag_design",
        "language": "en",
        "owner": "Internal knowledge assistant scenario",
        "doc_type": "design_note",
        "pii": "no",
    },
    "customer_support_playbook.txt": {
        "source": "data/customer_support_playbook.txt",
        "category": "support",
        "language": "en",
        "owner": "Support operations scenario",
        "doc_type": "playbook",
        "pii": "no",
    },
    "chunking_experiment_report.md": {
        "source": "data/chunking_experiment_report.md",
        "category": "chunking",
        "language": "en",
        "owner": "Group experiment summary",
        "doc_type": "experiment_report",
        "pii": "no",
    },
    "vi_retrieval_notes.md": {
        "source": "data/vi_retrieval_notes.md",
        "category": "retrieval",
        "language": "vi",
        "owner": "Vietnamese retrieval notes",
        "doc_type": "technical_note",
        "pii": "no",
    },
}

QUERY_DEMOS = [
    {
        "query": "What is a vector store used for in RAG?",
        "filter": {"category": "vector_store"},
        "gold_answer": "A vector store keeps embeddings and retrieves the most similar chunks for semantic search or retrieval-augmented generation.",
        "expected_source": "data/vector_store_notes.md",
    },
    {
        "query": "How can metadata filters improve retrieval precision?",
        "filter": {"category": "vector_store"},
        "gold_answer": "Metadata filters narrow the search space by fields such as source, language, department or access level, reducing noisy or unsafe results.",
        "expected_source": "data/vector_store_notes.md",
    },
    {
        "query": "When should the support assistant escalate instead of answering?",
        "filter": {"category": "support"},
        "gold_answer": "If retrieval is insufficient or no document explains the issue, the assistant should recommend escalation instead of improvising.",
        "expected_source": "data/customer_support_playbook.txt",
    },
    {
        "query": "Trong hệ thống trợ lý tri thức nội bộ, retrieval đóng vai trò gì?",
        "filter": {"language": "vi"},
        "gold_answer": "Retrieval tìm những đoạn tài liệu phù hợp nhất trước khi mô hình ngôn ngữ tạo câu trả lời.",
        "expected_source": "data/vi_retrieval_notes.md",
    },
    {
        "query": "Why is Python useful for AI applications?",
        "filter": {"category": "programming"},
        "gold_answer": "Python is useful for AI because it supports data cleaning, model training, evaluation scripts and integration with AI libraries and application logic.",
        "expected_source": "data/python_intro.txt",
    },
]

SIMILARITY_PAIRS = [
    ("Vector stores keep embeddings for semantic search.", "A vector database retrieves similar chunks for RAG.", "high"),
    ("Metadata filters reduce noisy retrieval results.", "Access control and language fields narrow search candidates.", "medium"),
    ("Sentence chunking keeps natural language boundaries.", "Recursive chunking first tries paragraph separators.", "medium"),
    ("Python is useful for AI model workflows.", "FastAPI can expose Python logic over HTTP.", "medium"),
    ("Retrieval should escalate when evidence is missing.", "Bananas are yellow fruits.", "low"),
]

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in", "is", "it",
    "of", "on", "or", "that", "the", "this", "to", "used", "use", "what", "why", "with", "about",
    "into", "before", "after", "can", "should", "does", "do", "when", "then", "if", "no", "not",
    "một", "và", "là", "có", "của", "trong", "hệ", "thống", "cho", "về", "gì", "vai", "trò",
    "trợ", "lý", "tri", "thức", "nội", "bộ",
}

SYNONYMS = {
    "retrieval": "retrieval", "retrieve": "retrieval", "retrieves": "retrieval", "retriever": "retrieval",
    "tìm": "retrieval", "truy": "retrieval", "xuất": "retrieval",
    "rag": "rag", "generation": "rag",
    "vector": "vector", "vectors": "vector", "database": "store", "store": "store", "stores": "store",
    "embedding": "embedding", "embeddings": "embedding", "embed": "embedding",
    "metadata": "metadata", "filter": "filter", "filters": "filter", "filtering": "filter",
    "chunk": "chunking", "chunks": "chunking", "chunking": "chunking", "sentence": "sentence",
    "support": "support", "assistant": "assistant", "escalate": "escalation", "escalation": "escalation",
    "python": "python", "ai": "ai", "model": "model", "models": "model", "workflow": "workflow", "workflows": "workflow",
    "semantic": "semantic", "search": "search", "similar": "similarity", "similarity": "similarity",
}


def normalize_token(token: str) -> str:
    token = token.lower().strip()
    return SYNONYMS.get(token, token)


def tokenize(text: str) -> list[str]:
    raw_tokens = re.findall(r"[\wÀ-ỹ]+", text.lower(), flags=re.UNICODE)
    tokens = [normalize_token(t) for t in raw_tokens]
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def build_keyword_embedder(corpus_texts: list[str], extra_texts: list[str]) -> Callable[[str], list[float]]:
    vocab_counter = Counter()
    for text in corpus_texts + extra_texts:
        vocab_counter.update(tokenize(text))
    vocab = [token for token, _ in vocab_counter.most_common(256)]
    index = {token: i for i, token in enumerate(vocab)}

    def embed(text: str) -> list[float]:
        vector = [0.0] * len(vocab)
        counts = Counter(tokenize(text))
        for token, count in counts.items():
            if token in index:
                vector[index[token]] = float(count)
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    return embed


def load_raw_documents() -> list[Document]:
    docs: list[Document] = []
    for path in DATA_FILES:
        content = path.read_text(encoding="utf-8")
        docs.append(Document(id=path.stem, content=content, metadata=dict(METADATA_BY_FILE[path.name])))
    return docs


def chunk_documents(raw_docs: list[Document]) -> list[Document]:
    chunker = SentenceChunker(max_sentences_per_chunk=3)
    chunk_docs: list[Document] = []
    for doc in raw_docs:
        parts = chunker.chunk(doc.content)
        for i, part in enumerate(parts):
            metadata = dict(doc.metadata)
            metadata.update({"doc_id": doc.id, "chunk_index": i, "strategy": "sentence_3"})
            chunk_docs.append(Document(id=f"{doc.id}_chunk_{i}", content=part, metadata=metadata))
    return chunk_docs


def print_chunking_comparator() -> None:
    comparator = ChunkingStrategyComparator()
    print("\n=== CHUNKING STRATEGY COMPARATOR BASELINE ===")
    for path in [ROOT / "data" / "vector_store_notes.md", ROOT / "data" / "rag_system_design.md", ROOT / "data" / "customer_support_playbook.txt"]:
        comparison = comparator.compare(path.read_text(encoding="utf-8"), chunk_size=512)
        print(f"\nFile: {path.name}")
        for strategy, stats in comparison.items():
            print(f"  {strategy}: count={stats['count']} | avg_length={stats['avg_length']:.1f}")


def clean_sentence(text: str) -> str:
    text = " ".join(line.strip() for line in text.splitlines() if line.strip())
    text = re.sub(r"#+\s*", "", text)
    sentences = re.split(r"(?<=[.!?。])\s+", text)
    return " ".join(sentences[:2]).strip()


def offline_answer(query: str, results: list[dict]) -> str:
    if not results:
        return "No retrieved evidence was available."
    best = results[0]
    source = best["metadata"].get("source", "unknown")
    evidence = clean_sentence(best["content"])
    return f"[OFFLINE FALLBACK] Based on {source}: {evidence}"


def main() -> int:
    raw_docs = load_raw_documents()
    corpus_texts = [doc.content for doc in raw_docs]
    query_texts = [item["query"] for item in QUERY_DEMOS]
    similarity_texts = [sentence for pair in SIMILARITY_PAIRS for sentence in pair[:2]]
    embedder = build_keyword_embedder(corpus_texts, query_texts + similarity_texts)

    print("=== DATA INVENTORY ===")
    for doc in raw_docs:
        print(
            f"- {doc.metadata['source']} | category={doc.metadata['category']} | "
            f"language={doc.metadata['language']} | owner={doc.metadata['owner']} | "
            f"chars={len(doc.content)} | pii={doc.metadata['pii']}"
        )

    print_chunking_comparator()

    print("\n=== SIMILARITY PREDICTIONS ===")
    for idx, (left, right, prediction) in enumerate(SIMILARITY_PAIRS, 1):
        score = compute_similarity(embedder(left), embedder(right))
        print(f"{idx}. predicted={prediction:<6} | actual={score:.4f}")
        print(f"   A: {left}")
        print(f"   B: {right}")

    print("\n=== CHUNK + EMBED + INDEX ===")
    chunk_docs = chunk_documents(raw_docs)
    store = EmbeddingStore(embedding_fn=embedder)
    store.add_documents(chunk_docs)
    print(f"Raw docs: {len(raw_docs)}")
    print(f"Chunks indexed: {len(chunk_docs)}")
    print("Chunking strategy: SentenceChunker(max_sentences_per_chunk=3)")

    print("\n=== QUERY DEMO ===")
    print("Answer backend: offline fallback only. No OpenRouter/OpenAI key is required for this submission.")
    top1_hits = 0
    top3_hits = 0
    for item in QUERY_DEMOS:
        results = store.search_with_filter(item["query"], top_k=3, metadata_filter=item["filter"])
        print(f"\nQuery: {item['query']}")
        print(f"Gold answer: {item['gold_answer']}")
        print(f"Expected source: {item['expected_source']}")
        print(f"Filter: {item['filter']}")
        is_top1 = bool(results and results[0]["metadata"].get("source") == item["expected_source"])
        is_top3 = any(r["metadata"].get("source") == item["expected_source"] for r in results)
        top1_hits += int(is_top1)
        top3_hits += int(is_top3)
        for rank, result in enumerate(results, 1):
            meta = result["metadata"]
            snippet = result["content"].replace("\n", " ").strip()[:220]
            print(
                f"  {rank}. score={result['score']:.3f} | source={meta.get('source')} | "
                f"category={meta.get('category')} | chunk={meta.get('chunk_index')} | snippet={snippet}..."
            )
        print("Mini answer:", offline_answer(item["query"], results))
    print(f"\nTop-1 relevant: {top1_hits}/5")
    print(f"Top-3 relevant: {top3_hits}/5")

    print("\n=== FAILURE CASE ===")
    bad_query = "How to improve the system?"
    bad_results = store.search(bad_query, top_k=3)
    print(f"Query: {bad_query}")
    print("This query is too broad, so results may mix RAG design, vector store notes, Python notes and support playbook.")
    for rank, result in enumerate(bad_results, 1):
        print(f"  {rank}. score={result['score']:.3f} | source={result['metadata'].get('source')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
