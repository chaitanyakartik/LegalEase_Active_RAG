from rag.nodes import fallback_generate


class LegalQueryExpander:
    """Expands legal queries with related concepts and terminology."""

    def __init__(self):
        self.expansion_prompt = """
You are a legal expert. Given a legal question, expand it by adding related legal concepts, terms, and considerations that would help find more comprehensive information.

Original Question: {query}
Law Category: {law_category}

Generate 3-5 expanded query variations that include:
- Related legal doctrines and principles
- Key terminology and phrases
- Broader legal concepts
- Specific legal remedies or procedures
- Relevant case law types

Format as a numbered list of expanded queries.
"""

    def expand_query(self, query: str, law_category: str) -> list[str]:
        """Expand the query with legal concepts."""
        prompt = self.expansion_prompt.format(query=query, law_category=law_category)
        result = fallback_generate(prompt)

        # Parse the numbered list
        expansions = []
        for line in result.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering and clean
                clean_line = line.lstrip('0123456789.- ').strip()
                if clean_line and len(clean_line) > 10:  # Filter out too short
                    expansions.append(clean_line)

        return expansions[:5]  # Limit to 5 expansions