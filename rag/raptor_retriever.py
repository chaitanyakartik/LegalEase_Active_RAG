from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from typing import List, Any
from rag.embeddings import LocalEmbeddings
from sklearn.cluster import KMeans
import numpy as np


class CustomRaptorRetriever(BaseRetriever):
    """A custom implementation of Raptor (Retrieval-Augmented Prompt Tuning) for hierarchical retrieval."""

    def __init__(self, documents: List[Document], embedding: LocalEmbeddings, k: int = 4):
        super().__init__()
        self.documents = documents
        self.embedding = embedding
        self.k = k
        self.tree = self._build_tree()

    def _build_tree(self) -> dict:
        """Build a simple hierarchical tree by clustering documents."""
        if not self.documents:
            return {"root": []}

        # Embed documents
        embeddings = self.embedding.embed_documents([doc.page_content for doc in self.documents])
        
        # Cluster into groups
        n_clusters = min(self.k, len(self.documents))
        if n_clusters < 2:
            return {"root": self.documents}
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        
        # Group documents by cluster
        clusters = {}
        for i, doc in enumerate(self.documents):
            cluster_id = labels[i]
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(doc)
        
        # Create summaries for each cluster (simple concatenation for now)
        tree = {}
        for cluster_id, docs in clusters.items():
            summary = " ".join([doc.page_content[:200] for doc in docs])[:500]  # Simple summary
            tree[cluster_id] = {
                "summary": summary,
                "documents": docs
            }
        
        return {"clusters": tree, "root_summaries": [tree[cid]["summary"] for cid in tree]}

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[Document]:
        """Retrieve documents hierarchically."""
        if not self.tree or "clusters" not in self.tree:
            return self.documents[:self.k]
        
        # Embed query
        query_emb = self.embedding.embed_query(query)
        
        # Find most relevant cluster summaries
        summaries = self.tree["root_summaries"]
        summary_embs = self.embedding.embed_documents(summaries)
        
        # Compute similarities
        similarities = np.dot(summary_embs, query_emb) / (np.linalg.norm(summary_embs, axis=1) * np.linalg.norm(query_emb))
        
        # Get top clusters
        top_indices = np.argsort(similarities)[-self.k:][::-1]
        
        # Collect documents from top clusters
        relevant_docs = []
        for idx in top_indices:
            cluster_id = list(self.tree["clusters"].keys())[idx]
            relevant_docs.extend(self.tree["clusters"][cluster_id]["documents"][:2])  # Limit per cluster
        
        return relevant_docs[:self.k]