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
            try:
                self._dense_model = SentenceTransformer(self._dense_model_name, local_files_only=True)
            except Exception:
                if not settings.ALLOW_MODEL_DOWNLOADS:
                    raise
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

    def index_case_chunks(self, case_id: str, documents: List[DocumentMetadata], persist_chroma: bool = True) -> int:
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
                    "page_number": chk.page_number,
                    "char_start": chk.char_start,
                    "char_end": chk.char_end,
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

        # Keep optional Chroma persistence for existing installations. FAISS
        # mode uses the case-local vectors directly and avoids a second index.
        if settings.USE_FAISS or not persist_chroma:
            return len(all_chunks)

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
        Normalizes token separators (underscores, colons, hyphens) into spaces.
        """
        clean_texts = [re.sub(r"[_:\-]+", " ", t) for t in texts]
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            vec = TfidfVectorizer(max_features=512, stop_words="english")
            mat = vec.fit_transform(clean_texts)
            return mat.toarray().tolist()
        except Exception:
            # Simple pure-Python bag-of-words fallback
            vocab: Dict[str, int] = {}
            tokenized = []
            for t in clean_texts:
                words = re.findall(r"\b[A-Za-z0-9]{2,}\b", t.lower())
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

        matrix = np.asarray([embeddings[i] for i in filtered_indices], dtype=np.float32)
        query_vector = np.asarray(query_emb, dtype=np.float32).reshape(1, -1)
        if settings.USE_FAISS and matrix.shape[1]:
            try:
                import faiss
            except ImportError as exc:
                raise RuntimeError(
                    "USE_FAISS requires compatible faiss-cpu and NumPy installations."
                ) from exc

            faiss.normalize_L2(matrix)
            faiss.normalize_L2(query_vector)
            index = faiss.IndexFlatIP(matrix.shape[1])
            index.add(matrix)
            similarities, positions = index.search(query_vector, len(filtered_indices))
            semantic_scores = [
                (filtered_indices[position], max(0.0, float(score)))
                for score, position in zip(similarities[0], positions[0])
            ]
        else:
            dots = (matrix @ query_vector.T).ravel()
            norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query_vector)
            similarities = np.divide(dots, norms, out=np.zeros_like(dots), where=norms > 1e-9)
            semantic_scores = [(i, max(0.0, float(score))) for i, score in zip(filtered_indices, similarities)]

        semantic_scores.sort(key=lambda x: (-x[1], x[0]))
        sem_rank = {idx: rank + 1 for rank, (idx, _) in enumerate(semantic_scores)}

        # 2. Keyword ranking by token overlap and frequency with stopword suppression and alias expansion
        ENGLISH_STOPWORDS = {
            "the", "a", "an", "is", "was", "were", "are", "be", "been", "being",
            "in", "on", "at", "to", "for", "of", "with", "by", "from", "and", "or",
            "that", "this", "these", "those", "it", "its", "as", "into", "did", "do",
            "does", "what", "where", "who", "when", "why", "how", "has", "had", "have",
            "would", "could", "should", "tell", "regarding", "about"
        }
        SYNONYM_EXPANSIONS = {
            "open": ["unlock", "unlocked", "access", "unsealing", "entry"],
            "opened": ["unlock", "unlocked", "access", "unsealed", "entry"],
            "opening": ["unlock", "unlocking", "access"],
            "unlock": ["open", "opened", "unlock", "unlocked"],
            "unlocked": ["open", "opened", "unlock", "unlocked"],
            "lock": ["secure", "close", "closed", "locked"],
            "locked": ["secure", "close", "closed", "locked"],
            "enter": ["access", "entry", "swipe", "swiped", "door", "inside", "arrived"],
            "entered": ["access", "entry", "swiped", "door", "inside", "arrived"],
            "entry": ["enter", "entered", "swiped", "access"],
            "exit": ["leave", "left", "departure", "departed", "out"],
            "exited": ["leave", "left", "departure", "departed", "out"],
            "left": ["exit", "exited", "departure", "departed"],
            "leave": ["exit", "exited", "departure"],
            "carry": ["tube", "bag", "drive", "device", "item", "holding", "held"],
            "carrying": ["tube", "bag", "drive", "device", "item", "holding", "held", "carried"],
            "carried": ["tube", "bag", "drive", "device", "item", "holding", "held", "carrying"],
            "tube": ["cardboard", "cylinder", "carrying", "carried", "package"],
            "case": ["case_lock", "display", "cabinet", "vault", "safe"],
            "display": ["case", "case_lock", "cabinet", "vault"],
            "building": ["facility", "premises", "staff_door", "door", "entrance"],
            "alibi": ["claimed", "stated", "home", "dinner", "left", "denied"],
            "contradict": ["denied", "conflict", "different", "inconsistent", "discrepancy"],
            "contradicts": ["denied", "conflict", "different", "inconsistent", "discrepancy"],
        }

        is_question = bool(
            query.strip().endswith("?")
            or re.match(r"^(?:who|what|when|where|why|how|which|did|was|were|is)\b", query.strip(), re.I)
        )

        query_norm = re.sub(r"[_:\-]+", " ", query.lower())
        all_terms = set(re.findall(r"\b[A-Za-z0-9]{2,}\b", query_norm))
        filtered_q_terms = {t for t in all_terms if t not in ENGLISH_STOPWORDS}
        q_terms = filtered_q_terms if filtered_q_terms else all_terms

        # Person name alias expansion (e.g. "tom", "reyes" -> "treyes", "tom_reyes")
        expanded_terms = set(q_terms)
        name_pairs = re.findall(r"\b([a-z]{2,})\s+([a-z]{2,})\b", query_norm)
        for first, last in name_pairs:
            if first in q_terms and last in q_terms:
                expanded_terms.add(f"{first[0]}{last}")       # e.g. treyes
                expanded_terms.add(f"{first}_{last}")        # e.g. tom_reyes
                expanded_terms.add(f"{first[0]}_{last}")      # e.g. t_reyes

        # Question-specific expansions for natural-language investigative inquiries
        if is_question:
            for term in list(q_terms):
                if term in SYNONYM_EXPANSIONS:
                    expanded_terms.update(SYNONYM_EXPANSIONS[term])

            # Time token expansion (e.g. 6:02 PM -> 18:02, 06:02; 3:30 PM -> 15:30)
            time_12 = re.finditer(r"\b(0?[1-9]|1[0-2]):([0-5]\d)(?::([0-5]\d))?\s*(am|pm)\b", query, re.I)
            for tm in time_12:
                hr = int(tm.group(1))
                mn = tm.group(2)
                ampm = tm.group(4).lower()
                hr_24 = hr + 12 if (ampm == "pm" and hr < 12) else (0 if (ampm == "am" and hr == 12) else hr)
                expanded_terms.add(f"{hr_24:02d}:{mn}")
                expanded_terms.add(f"{hr:02d}:{mn}")
                expanded_terms.add(f"{hr}:{mn}")
                expanded_terms.add(f"{hr_24:02d}{mn}")

            time_24 = re.finditer(r"\b([01]?\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?\b", query)
            for tm in time_24:
                hr_24 = int(tm.group(1))
                mn = tm.group(2)
                expanded_terms.add(f"{hr_24:02d}:{mn}")
                expanded_terms.add(f"{hr_24}:{mn}")
                hr_12 = 12 if hr_24 in [0, 12] else (hr_24 - 12 if hr_24 > 12 else hr_24)
                ampm = "pm" if hr_24 >= 12 else "am"
                expanded_terms.add(f"{hr_12}:{mn}")
                expanded_terms.add(f"{hr_12:02d}:{mn}")

        keyword_scores = []
        for i in filtered_indices:
            txt = chunks[i]["text"]
            txt_lower = txt.lower()
            doc_name = chunks[i].get("document_name", "").lower()
            txt_norm = re.sub(r"[_:\-]+", " ", txt_lower)
            overlap_score = 0.0

            for term in expanded_terms:
                term_clean = term.replace(":", " ")
                count = len(re.findall(rf"\b{re.escape(term)}\b", txt_lower)) or len(re.findall(rf"\b{re.escape(term_clean)}\b", txt_norm))
                if not count and ":" in term:
                    # Check prefix, e.g. "18:02" matching "18:02:19"
                    count = len(re.findall(rf"\b{re.escape(term)}:\d{{2}}\b", txt_lower))
                if count:
                    overlap_score += 1.0 + math.log(1.0 + count)
                if term in doc_name:
                    overlap_score += 1.5

            # Exact multi-word phrase matching
            query_phrases = re.findall(r"\b[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)+\b", query_norm)
            for phrase in query_phrases:
                if phrase not in ENGLISH_STOPWORDS and phrase in txt_norm:
                    overlap_score += 2.0

            # In question mode, demote pure document header chunks and boost timestamped action rows
            if is_question:
                is_pure_header = (
                    bool(re.match(r"^(?:DOCUMENT\s+\d+|Document Type:|System:|Author:|Case ID:)", txt.strip(), re.I))
                    and not re.search(r"\b\d{1,2}:\d{2}(?::\d{2})?\s*-\s*[A-Z_]+", txt)
                    and not re.search(r"\[\d{1,2}:\d{2}\s*(?:AM|PM)\]\s*[A-Z]+:", txt)
                    and not re.search(r"\b(?:unlocked|locked|entered|exited|swiped|carried|saw|stated|photo)\b", txt_lower)
                )
                has_action_event = bool(
                    re.search(r"\b(?:UNLOCKED|LOCKED|ENTRY|EXIT|ARMED|DISARMED|SWIPED|ACCESS_GRANTED|OPENED|CARRIED|FLASHED|INSERTED)\b", txt, re.I)
                    or re.search(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", txt)
                )

                if is_pure_header:
                    overlap_score *= 0.35
                elif has_action_event:
                    overlap_score *= 1.35

            keyword_scores.append((i, overlap_score))

        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        kw_rank = {idx: rank + 1 for rank, (idx, _) in enumerate(keyword_scores)}

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF_Score = 1 / (60 + sem_rank) + 1 / (60 + kw_rank)
        cosine_by_index = dict(semantic_scores)
        keyword_by_index = dict(keyword_scores)
        rrf_results = []
        for i in filtered_indices:
            raw_sim = cosine_by_index[i]
            if raw_sim == 0.0 and keyword_by_index[i] == 0.0:
                continue
            s_rank = sem_rank.get(i, 999)
            k_rank = kw_rank.get(i, 999)
            rrf = (1.0 / (60.0 + s_rank)) + (1.0 / (60.0 + k_rank))
            # Also combine with raw cosine similarity for fine-grained ranking
            combined_score = round(rrf * 10.0 + raw_sim * 0.5, 4)
            if combined_score >= threshold:
                rrf_results.append((i, combined_score))

        rrf_results.sort(key=lambda x: x[1], reverse=True)

        # Multi-hop credential resolution: If top chunks reference a key or credential,
        # ensure chunks defining who holds that credential are also retrieved
        top_indices = [idx for idx, _ in rrf_results[:top_k]]
        top_text = " ".join(chunks[idx]["text"] for idx in top_indices)
        referenced_keys = set(re.findall(r"\b(KEY_\d+|CARD_\d+|BADGE_\d+)\b", top_text, re.I))

        if is_question and referenced_keys:
            for i in filtered_indices:
                if i not in top_indices:
                    chunk_txt = chunks[i]["text"]
                    if any(k.upper() in chunk_txt.upper() and ("assigned to" in chunk_txt.lower() or "held by" in chunk_txt.lower()) for k in referenced_keys):
                        rrf_results.insert(min(top_k - 1, len(rrf_results)), (i, 0.45))
                        break

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
                    page_number=c.get("page_number"),
                    char_start=c.get("char_start"),
                    char_end=c.get("char_end"),
                )
            )

        return results


# Global singleton instance
retriever = HybridRetriever()
