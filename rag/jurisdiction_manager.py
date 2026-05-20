class JurisdictionManager:
    """Manages legal jurisdiction context for more accurate analysis."""

    JURISDICTIONS = {
        "India": {
            "courts": ["Supreme Court", "High Courts", "District Courts", "Tribunals"],
            "laws": ["Constitution", "IPC", "CrPC", "CPC", "Contract Act", "Companies Act"],
            "common_issues": ["constitutional law", "criminal law", "civil disputes", "corporate law"]
        },
        "USA": {
            "courts": ["Supreme Court", "Circuit Courts", "District Courts", "State Courts"],
            "laws": ["Constitution", "Federal Statutes", "State Laws", "Common Law"],
            "common_issues": ["constitutional law", "tort law", "contract law", "corporate law"]
        },
        "UK": {
            "courts": ["Supreme Court", "Court of Appeal", "High Court", "County Courts"],
            "laws": ["Constitution", "Statute Law", "Common Law", "EU Law (pre-Brexit)"],
            "common_issues": ["constitutional law", "contract law", "tort law", "employment law"]
        },
        "General": {
            "courts": ["International Courts", "Arbitral Tribunals"],
            "laws": ["International Law", "Treaties", "Customary Law"],
            "common_issues": ["international law", "human rights", "trade law"]
        }
    }

    def __init__(self):
        self.current_jurisdiction = "General"

    def detect_jurisdiction(self, text: str) -> str:
        """Detect jurisdiction from text content."""
        text_lower = text.lower()

        # Simple keyword-based detection
        if any(word in text_lower for word in ["india", "indian", "delhi", "mumbai", "constitution of india"]):
            return "India"
        elif any(word in text_lower for word in ["united states", "america", "federal", "supreme court", "us"]):
            return "USA"
        elif any(word in text_lower for word in ["uk", "united kingdom", "british", "england", "london"]):
            return "UK"
        else:
            return "General"

    def get_jurisdiction_context(self, jurisdiction: str) -> dict:
        """Get jurisdiction-specific context."""
        return self.JURISDICTIONS.get(jurisdiction, self.JURISDICTIONS["General"])

    def enhance_query_with_jurisdiction(self, query: str, jurisdiction: str) -> str:
        """Add jurisdiction context to query."""
        context = self.get_jurisdiction_context(jurisdiction)
        courts = ", ".join(context["courts"][:2])  # Top 2 courts
        laws = ", ".join(context["laws"][:3])  # Top 3 laws

        enhanced = f"{query} (considering {jurisdiction} jurisdiction, relevant courts: {courts}, applicable laws: {laws})"
        return enhanced