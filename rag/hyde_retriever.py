from rag.nodes import fallback_generate


class HydeRetriever:
    """Hyde (Hypothetical Document Embeddings) for improved retrieval."""

    def __init__(self):
        self.hyde_prompt = """
You are a legal expert. Given the following question, generate a detailed hypothetical answer as if you were explaining it to a client.

Question: {query}

Generate a comprehensive hypothetical answer that would be found in legal documents. Be detailed and use legal terminology. This will be used to find relevant documents, so make it realistic and thorough.

Hypothetical Answer:"""

    def generate_hypothetical_answer(self, query: str) -> str:
        """Generate a hypothetical answer to the query."""
        prompt = self.hyde_prompt.format(query=query)
        return fallback_generate(prompt)

    def get_hypothetical_embedding(self, query: str, embedding_function) -> list[float]:
        """Generate embedding for the hypothetical answer."""
        hypothetical_answer = self.generate_hypothetical_answer(query)
        return embedding_function.embed_query(hypothetical_answer)