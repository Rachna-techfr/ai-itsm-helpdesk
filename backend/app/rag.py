from __future__ import annotations

import logging
import httpx

from app.config import Settings
from app.embeddings import Embedder, cosine, retrieval_confidence
from app.schemas import CitationOut, SearchOut

logger = logging.getLogger("rag")


class RAGEngine:
    """Enterprise RAG pipeline with dense vector retrieval, LLM generation, and hallucination guardrails."""

    def __init__(self, settings: Settings, embedder: Embedder, store: Any):
        self.settings = settings
        self.embedder = embedder
        self.store = store
        self.hf_token = settings.hf_token
        self.hf_model = settings.hf_model

    def search(self, query: str, top_k: int = 3) -> SearchOut:
        """Search chunks using cosine similarity over embeddings."""
        query_vec = self.embedder.embed(query)
        scored = []
        for chunk in self.store.chunks:
            chunk_vec = chunk.get("embedding", [])
            score = cosine(query_vec, chunk_vec)
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored[:top_k]

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

        # Hallucination Guardrail Check
        # If top match score is below rag_threshold, the approved KB does not have the answer
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
                "I searched our enterprise knowledge repository, but found no verified guidance or runbooks covering this specific question. "
                "In accordance with IT Safety and Governance policies, I will not generate an ungrounded or speculative answer.\n\n"
                "Would you like me to open a ticket for our IT Service Desk to investigate?"
            )
            return text, "Safety Guardrail", "Knowledge Base Refusal"

        # Construct context from top citations
        top_citation = search_result.results[0]
        context_snippets = []
        for res in search_result.results[:2]:
            context_snippets.append(f"[{res.id}: {res.title}]\n{res.excerpt}")
        context_block = "\n\n".join(context_snippets)

        # If Hugging Face token is provided, invoke Hugging Face API
        if self.hf_token:
            try:
                hf_reply = self._call_huggingface(query, context_block)
                if hf_reply:
                    return (
                        hf_reply,
                        f"Hugging Face ({self.hf_model})",
                        f"Grounded on {top_citation.id}",
                    )
            except Exception as exc:
                logger.warning("Hugging Face API call failed (%s). Falling back to grounded synthesizer.", exc)

        # Grounded template synthesis based on matched knowledge
        art = next((a for a in self.store.articles if a["id"] == top_citation.id), None)
        steps_list = ""
        if art and art.get("steps"):
            steps_list = "\n".join(f"{i+1}. {st}" for i, st in enumerate(art["steps"]))
        else:
            steps_list = top_citation.excerpt

        answer_text = (
            f"Here is the verified IT procedure from **[{top_citation.id}: {top_citation.title}]**:\n\n"
            f"{steps_list}\n\n"
            f"📌 *Source: {top_citation.title} ({top_citation.id}) | Category: {top_citation.category} | Confidence: {int(search_result.confidence * 100)}%*"
        )
        return (
            answer_text,
            "Grounded RAG Synthesizer",
            f"Knowledge Base ({top_citation.id})",
        )

    def _call_huggingface(self, query: str, context: str) -> str | None:
        """Query Hugging Face Inference API with grounded context."""
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        prompt = (
            f"<|im_start|>system\n"
            f"You are Northline IT Helpdesk AI Assistant. Answer the employee's IT question using ONLY the approved knowledge base context below. "
            f"Do not hallucinate. Cite the article ID.\n"
            f"Approved Context:\n{context}\n<|im_end|>\n"
            f"<|im_start|>user\n{query}\n<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 250, "temperature": 0.2, "return_full_text": False},
        }
        with httpx.Client(timeout=12.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                out = resp.json()
                if isinstance(out, list) and len(out) > 0:
                    return out[0].get("generated_text", "").strip()
        return None

