from rag.nodes import fallback_generate


class ConfidenceScorer:
    """Scores confidence in generated legal responses."""

    def __init__(self):
        self.confidence_prompt = """
You are a legal expert evaluating the quality and reliability of a legal analysis.

Question: {question}
Generated Answer: {answer}
Retrieved Context: {context}

Rate the confidence in this answer on a scale of 1-10, where:
- 1-3: Low confidence (limited relevant information, speculative)
- 4-6: Medium confidence (some relevant information, reasonable analysis)
- 7-8: High confidence (strong supporting evidence, well-grounded)
- 9-10: Very high confidence (comprehensive evidence, authoritative)

Consider:
- Amount and relevance of supporting context
- Legal accuracy and completeness
- Presence of specific citations or precedents
- Clarity of legal reasoning
- Coverage of key legal issues

Provide only a single number (1-10) as your confidence score.
"""

    def score_confidence(self, question: str, answer: str, context: str) -> int:
        """Score confidence in the answer."""
        # Truncate context if too long
        context = context[:2000] + "..." if len(context) > 2000 else context

        prompt = self.confidence_prompt.format(
            question=question,
            answer=answer,
            context=context
        )

        try:
            result = fallback_generate(prompt).strip()
            # Extract the first number found
            import re
            numbers = re.findall(r'\d+', result)
            if numbers:
                score = int(numbers[0])
                return max(1, min(10, score))  # Clamp to 1-10
            return 5  # Default medium confidence
        except:
            return 5  # Default on error