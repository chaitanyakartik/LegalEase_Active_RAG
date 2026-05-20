from rag.nodes import fallback_generate
from rag.embeddings import LocalEmbeddings


class MultiModalRetriever:
    """Enhanced multi-modal retrieval for text and images."""

    def __init__(self):
        self.image_analysis_prompt = """
You are a legal document analyst. Analyze this image description and relate it to the legal query.

Image Description: {image_desc}
Legal Query: {query}

Provide:
1. How this image is relevant to the legal question
2. Key visual elements that support legal analysis
3. Any legal significance of the visual content
4. How it should be integrated into the legal response

Be specific and focus on legal relevance.
"""
        self.embeddings = LocalEmbeddings(dim=256)

    def analyze_image_relevance(self, image_desc: str, query: str) -> dict:
        """Analyze how an image relates to a legal query."""
        if not image_desc or image_desc.startswith("Image content"):
            return {"relevant": False, "analysis": "No meaningful image content"}

        prompt = self.image_analysis_prompt.format(
            image_desc=image_desc,
            query=query
        )

        analysis = fallback_generate(prompt)

        # Determine relevance
        relevant_keywords = ["relevant", "supports", "evidence", "legal", "significant"]
        is_relevant = any(keyword in analysis.lower() for keyword in relevant_keywords)

        return {
            "relevant": is_relevant,
            "analysis": analysis,
            "image_desc": image_desc
        }

    def enhance_text_with_images(self, text_docs: list, image_docs: list, query: str) -> list:
        """Enhance text retrieval with relevant images."""
        enhanced_docs = text_docs.copy()

        for img_doc in image_docs:
            img_desc = img_doc.metadata.get("image_desc", "")
            analysis = self.analyze_image_relevance(img_desc, query)

            if analysis["relevant"]:
                # Create enhanced document combining text and image analysis
                enhanced_content = f"""
TEXT CONTENT: {img_doc.page_content}

IMAGE ANALYSIS: {analysis['analysis']}

LEGAL SIGNIFICANCE: This visual evidence supports the legal analysis by providing {analysis.get('key_elements', 'additional context')}.
"""
                from langchain_core.documents import Document
                enhanced_doc = Document(
                    page_content=enhanced_content,
                    metadata={**img_doc.metadata, "enhanced": True, "image_analysis": analysis}
                )
                enhanced_docs.append(enhanced_doc)

        return enhanced_docs