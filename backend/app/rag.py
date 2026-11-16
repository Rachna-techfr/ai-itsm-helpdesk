from __future__ import annotations

import logging
from typing import Any
import numpy as np

from app.config import Settings
from app.embeddings import Embedder, cosine, retrieval_confidence
from app.schemas import CitationOut, SearchOut

logger = logging.getLogger("rag")

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False


class FAISSVectorStore:
    """FAISS FlatIP vector index over 384-dimensional dense normalized embeddings."""

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.chunks: list[dict] = []
        if HAS_FAISS:
            self.index = faiss.IndexFlatIP(dim)
        else:
            self.index = None

    def build(self, chunks: list[dict]) -> None:
        self.chunks = list(chunks)
        if not HAS_FAISS or not chunks:
            return
        vectors = np.array([c["embedding"] for c in chunks], dtype=np.float32)
        faiss.normalize_L2(vectors)
        self.index.reset()
        self.index.add(vectors)
        logger.info("Indexed %d chunks into FAISS vector database (dim=%d)", len(chunks), self.dim)

    def search(self, query_vec: list[float], top_k: int = 3) -> list[tuple[float, dict]]:
        if not HAS_FAISS or self.index is None or self.index.ntotal == 0:
            # Fallback to in-process cosine loop
            scored = []
            for chunk in self.chunks:
                score = cosine(query_vec, chunk.get("embedding", []))
                scored.append((score, chunk))
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[:top_k]

        q = np.array([query_vec], dtype=np.float32)
        faiss.normalize_L2(q)
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(q, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self.chunks):
                results.append((float(score), self.chunks[idx]))
        return results


class RAGEngine:
    """Enterprise RAG pipeline with FAISS vector retrieval, Hugging Face LLM, and hallucination guardrails."""

    def __init__(self, settings: Settings, embedder: Embedder, store: Any):
        self.settings = settings
        self.embedder = embedder
        self.store = store
        self.hf_token = settings.hf_token
        self.hf_model = settings.hf_model
        self.vector_store = FAISSVectorStore(dim=embedder.dim)
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        if self.store and self.store.chunks:
            self.vector_store.build(self.store.chunks)

    def search(self, query: str, top_k: int = 3) -> SearchOut:
        """Search knowledge chunks using FAISS dense vector similarity."""
        query_vec = self.embedder.embed(query)
        top_matches = self.vector_store.search(query_vec, top_k=top_k)

        citations: list[CitationOut] = []
        best_score = 0.0
        if top_matches:
            best_score = top_matches[0][0]

        for score, chunk in top_matches:
            conf = retrieval_confidence(score)
            citations.append(
                CitationOut(
                    id=chunk.get("article_id", "KB0000"),
                    title=chunk.get("title", "Knowledge Document"),
                    category=chunk.get("category", ""),
                    score=round(score, 3),
                    confidence=conf,
                    excerpt=chunk.get("excerpt", ""),
                )
            )

        # AI Safety & Governance: Zero Hallucination Threshold
        knows = best_score >= self.settings.rag_threshold
        top_conf = retrieval_confidence(best_score) if citations else 0.1

        return SearchOut(
            query=query,
            results=citations,
            confidence=top_conf if knows else 0.15,
            knows=knows,
        )

    def answer(self, query: str, search_result: SearchOut) -> tuple[str, str, str]:
        """
        Generate grounded answer from retrieved context.
        Returns (answer_text, provider_label, narrative_source).
        """
        if not search_result.knows or not search_result.results:
            text = (
                "⚠️ **Approved Knowledge Base Content Insufficient**\n\n"
                "I searched our enterprise knowledge repository using our FAISS vector database, but found no verified guidance or runbooks covering this specific question. "
                "In accordance with IT Safety and Governance policies, I will not generate an ungrounded or speculative answer.\n\n"
                "Would you like me to open a ticket for our IT Service Desk to investigate?"
            )
            return text, "Safety Guardrail", "Knowledge Base Refusal"

        top_citation = search_result.results[0]
        context_snippets = [f"[{res.id}: {res.title}]\n{res.excerpt}" for res in search_result.results[:2]]
        context_block = "\n\n".join(context_snippets)

        # 1. If HF_TOKEN is configured, query Hugging Face Inference API / Router
        if self.hf_token:
            try:
                hf_reply = self._call_huggingface(query, context_block)
                if hf_reply:
                    return (
                        hf_reply,
                        f"Hugging Face ({self.hf_model})",
                        f"Grounded on {top_citation.id} via FAISS",
                    )
            except Exception as exc:
                logger.warning("Hugging Face API call failed (%s); using grounded synthesizer.", exc)

        # 2. Grounded deterministic synthesis over matched runbook
        art = next((a for a in self.store.articles if a["id"] == top_citation.id), None)
        if art and art.get("steps"):
            steps_list = "\n".join(f"{i+1}. {st}" for i, st in enumerate(art["steps"]))
        else:
            steps_list = top_citation.excerpt

        answer_text = (
            f"Here is the verified IT procedure from **[{top_citation.id}: {top_citation.title}]**:\n\n"
            f"{steps_list}\n\n"
            f"📌 *Vector Search: FAISS Inner Product (384-dim) | Source: {top_citation.title} ({top_citation.id}) | Cosine Score: {top_citation.score} | Confidence: {int(search_result.confidence * 100)}%*"
        )
        return (
            answer_text,
            "Grounded RAG Synthesizer (FAISS + MiniLM)",
            f"Knowledge Base ({top_citation.id})",
        )

    def _call_huggingface(self, query: str, context: str) -> str | None:
        """Call Hugging Face Inference using chat completions or text generation."""
        try:
            from huggingface_hub import InferenceClient

            client = InferenceClient(model=self.hf_model, token=self.hf_token, timeout=15.0)

            # 1. Try chat completion (for instruct/chat models like Qwen)
            messages = [
                {
                    "role": "system",
                    "content": f"You are the IT Helpdesk AI Assistant. Answer the question using ONLY the approved context below:\n\n{context}",
                },
                {"role": "user", "content": query},
            ]
            try:
                chat_res = client.chat.completions.create(messages=messages, max_tokens=250, temperature=0.2)
                if chat_res and chat_res.choices:
                    return chat_res.choices[0].message.content.strip()
            except Exception as e:
                logger.info("Chat completion attempt failed (%s), trying text_generation", e)

            # 2. Try text generation
            prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
            resp = client.text_generation(prompt, max_new_tokens=220, temperature=0.2)
            if resp:
                return resp.strip()
        except Exception as exc:
            logger.info("InferenceClient fallback to HTTP: %s", exc)

        # 3. Fallback HTTP to modern router endpoint
        import httpx

        url = f"https://router.huggingface.co/hf-inference/models/{self.hf_model}"
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        prompt = f"Context: {context}\n\nQuestion: {query}\nAnswer:"
        try:
            with httpx.Client(timeout=10.0) as http_client:
                resp = http_client.post(
                    url,
                    json={"inputs": prompt, "parameters": {"max_new_tokens": 200, "temperature": 0.2}},
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0].get("generated_text", "").strip()
        except Exception as exc:
            logger.warning("HTTP fallback failed: %s", exc)
        return None
