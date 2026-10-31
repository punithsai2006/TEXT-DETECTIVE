import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import settings
from app.models.schemas import DocumentMetadata, EvidenceItem, TextChunk

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid Evidence Retrieval Engine combining dense semantic similarity
    and lexical/BM25 keyword search with Reciprocal Rank Fusion (RRF) and reranking.
    Strictly isolated per case_id.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or (settings.storage_path / "chroma")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._dense_model = None
        self._dense_model_name = "all-MiniLM-L6-v2"
        self._model_load_attempted = False

    def _get_dense_model(self):
        """
        Lazily loads SentenceTransformers if installed. Falls back gracefully
        to fast offline TF-IDF/lexical vectorizer if unavailable.
        """
        if self._model_load_attempted:
            return self._dense_model

        self._model_load_attempted = True
        try:
            from sentence_transformers import SentenceTransformer
            self._dense_model = SentenceTransformer(self._dense_model_name)
            logger.info(f"Loaded SentenceTransformer model: {self._dense_model_name}")
        except Exception as e:
            logger.info(f"Dense SentenceTransformer unavailable ({e}). Using offline TF-IDF/lexical vectorizer.")
            self._dense_model = None
        return self._dense_model

    def _index_path(self, case_id: str) -> Path:
        p = self.storage_dir / case_id
        p.mkdir(parents=True, exist_ok=True)
        return p / "vector_index.json"

    def index_case_chunks(self, case_id: str, documents: List[DocumentMetadata]) -> int:
        """
        Indexes all text chunks belonging to a case into case-isolated persistent storage.
        """
        all_chunks: List[Dict[str, Any]] = []
        for doc in documents:
            for chk in doc.chunks:
                all_chunks.append({
                    "chunk_id": chk.chunk_id,
                    "case_id": case_id,
                    "document_id": doc.document_id,
                    "document_name": doc.filename,
                    "document_type": doc.document_type.value,
                    "speaker": chk.speaker,
                    "timestamp": chk.timestamp,
                    "text": chk.text,
                    "sentence_indices": chk.sentence_indices,
                })

        if not all_chunks:
            return 0

        # Compute embeddings
        model = self._get_dense_model()
        texts = [c["text"] for c in all_chunks]

        if model is not None:
            try:
                embeddings = model.encode(texts, convert_to_numpy=True).tolist()
                model_used = self._dense_model_name
            except Exception as e:
                logger.warning(f"Dense encoding error: {e}. Falling back to TF-IDF.")
                embeddings = self._compute_lexical_vectors(texts)
                model_used = "lexical-tfidf-fallback"
        else:
            embeddings = self._compute_lexical_vectors(texts)
            model_used = "lexical-tfidf-offline"

        data = {
            "case_id": case_id,
            "model_used": model_used,
            "chunks": all_chunks,
            "embeddings": embeddings,
        }

        with open(self._index_path(case_id), "w", encoding="utf-8") as f:
            json.dump(data, f)

        # Also attempt ChromaDB persistence if available
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(self.storage_dir / "chroma_db"))
            collection_name = f"case_{case_id.replace('-', '_')}"
            try:
                client.delete_collection(name=collection_name)
            except Exception:
                pass
            col = client.create_collection(name=collection_name)
            col.add(
                ids=[c["chunk_id"] for c in all_chunks],
                documents=texts,
                metadatas=[{
                    "doc_name": c["document_name"],
                    "speaker": c["speaker"] or "",
                    "timestamp": c["timestamp"] or "",
                } for c in all_chunks],
            )
        except Exception:
            pass

        return len(all_chunks)

    def _compute_lexical_vectors(self, texts: List[str]) -> List[List[float]]:
        """
        Deterministic TF-IDF vectorizer for offline or fallback search.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            vec = TfidfVectorizer(max_features=512, stop_words="english")
            mat = vec.fit_transform(texts)
            return mat.toarray().tolist()
        except Exception:
            # Simple pure-Python bag-of-words fallback
            vocab: Dict[str, int] = {}
            tokenized = []
            for t in texts:
                words = re.findall(r"\b[A-Za-z0-9_]{2,}\b", t.lower())
                tokenized.append(words)
                for w in words:
                    if w not in vocab and len(vocab) < 512:
                        vocab[w] = len(vocab)

            vectors = []
            for words in tokenized:
                v = [0.0] * max(len(vocab), 1)
                for w in words:
                    if w in vocab:
                        v[vocab[w]] += 1.0
                norm = math.sqrt(sum(x * x for x in v))
                if norm > 0:
                    v = [x / norm for x in v]
                vectors.append(v)
            return vectors

    def search(
        self,
        case_id: str,
        query: str,
        top_k: int = 10,
        filter_doc_ids: Optional[List[str]] = None,
        threshold: float = 0.0,
    ) -> List[EvidenceItem]:
        """
        Executes hybrid semantic + keyword retrieval using Reciprocal Rank Fusion (RRF).
        """
        idx_file = self._index_path(case_id)
        if not idx_file.exists():
            return []

        with open(idx_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        chunks = data.get("chunks", [])
        embeddings = data.get("embeddings", [])
        if not chunks:
            return []

        # Filter by document IDs if specified
        filtered_indices = [
            i for i, c in enumerate(chunks)
            if filter_doc_ids is None or c["document_id"] in filter_doc_ids
        ]
        if not filtered_indices:
            return []

        # 1. Semantic / Vector Ranking
        model = self._get_dense_model()
        if model is not None and data.get("model_used") == self._dense_model_name:
            query_emb = model.encode([query], convert_to_numpy=True)[0]
        else:
            # Query vector using TF-IDF projection
            doc_texts = [chunks[i]["text"] for i in filtered_indices]
            all_texts = [query] + doc_texts
            all_vecs = self._compute_lexical_vectors(all_texts)
            query_emb = np.array(all_vecs[0])
            for idx, f_idx in enumerate(filtered_indices):
                embeddings[f_idx] = all_vecs[idx + 1]

        semantic_scores = []
        for i in filtered_indices:
            doc_emb = np.array(embeddings[i])
            # Cosine similarity
            denom = (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb))
            sim = float(np.dot(query_emb, doc_emb) / denom) if denom > 1e-9 else 0.0
            semantic_scores.append((i, max(0.0, sim)))

        semantic_scores.sort(key=lambda x: x[1], reverse=True)
        sem_rank = {idx: rank + 1 for rank, (idx, _) in enumerate(semantic_scores)}

        # 2. Keyword / Lexical Ranking (BM25 token overlap)
        q_terms = set(re.findall(r"\b[A-Za-z0-9_]{2,}\b", query.lower()))
        keyword_scores = []
        for i in filtered_indices:
            txt = chunks[i]["text"].lower()
            overlap_score = 0.0
            for term in q_terms:
                if term in txt:
                    count = len(re.findall(rf"\b{re.escape(term)}\b", txt))
                    overlap_score += 1.0 + math.log(1.0 + count)
            keyword_scores.append((i, overlap_score))

        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        kw_rank = {idx: rank + 1 for rank, (idx, _) in enumerate(keyword_scores)}

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF_Score = 1 / (60 + sem_rank) + 1 / (60 + kw_rank)
        rrf_results = []
        for i in filtered_indices:
            s_rank = sem_rank.get(i, 999)
            k_rank = kw_rank.get(i, 999)
            rrf = (1.0 / (60.0 + s_rank)) + (1.0 / (60.0 + k_rank))
            # Also combine with raw cosine similarity for fine-grained ranking
            raw_sim = next((score for idx, score in semantic_scores if idx == i), 0.0)
            combined_score = round(rrf * 10.0 + raw_sim * 0.5, 4)
            if combined_score >= threshold:
                rrf_results.append((i, combined_score))

        rrf_results.sort(key=lambda x: x[1], reverse=True)

        results: List[EvidenceItem] = []
        for i, score in rrf_results[:top_k]:
            c = chunks[i]
            results.append(
                EvidenceItem(
                    evidence_id=f"evid_{c['chunk_id']}",
                    case_id=case_id,
                    document_id=c["document_id"],
                    document_name=c["document_name"],
                    document_type=c["document_type"],
                    chunk_id=c["chunk_id"],
                    text=c["text"],
                    speaker=c.get("speaker"),
                    timestamp=c.get("timestamp"),
                    sentence_indices=c.get("sentence_indices", []),
                    score=score,
                    retrieval_method="hybrid",
                )
            )

        return results


# Global singleton instance
retriever = HybridRetriever()
