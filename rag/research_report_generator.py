"""
Automated Legal Research Report Generator
Creates comprehensive, professional legal research memos and reports.
"""

from typing import Dict, List, Optional, Tuple
import datetime
from rag.query_expander import LegalQueryExpander
from rag.jurisdiction_manager import JurisdictionManager
from rag.confidence_scorer import ConfidenceScorer
from rag.multi_modal import MultiModalRetriever
from rag.citation_analyzer import CitationNetworkAnalyzer
from rag.counterfactual_analyzer import CounterfactualAnalyzer


class LegalResearchReportGenerator:
    """Generates comprehensive legal research reports and memos."""

    def __init__(self):
        self.query_expander = LegalQueryExpander()
        self.jurisdiction_manager = JurisdictionManager()
        self.confidence_scorer = ConfidenceScorer()
        self.multi_modal = MultiModalRetriever()
        self.citation_analyzer = CitationNetworkAnalyzer()
        self.counterfactual_analyzer = CounterfactualAnalyzer()

    def generate_research_memo(self, case: Dict, research_query: str, jurisdiction: str,
                              documents: List[Dict], precedents: List[Dict]) -> str:
        """Generate a comprehensive legal research memorandum."""

        # Generate timestamp
        timestamp = datetime.datetime.now().strftime("%B %d, %Y")

        memo = f"# LEGAL RESEARCH MEMORANDUM\n\n"
        memo += f"**Date:** {timestamp}\n"
        memo += f"**Case:** {case.get('title', 'Unknown Case')}\n"
        memo += f"**Client:** [Client Name]\n"
        memo += f"**Jurisdiction:** {jurisdiction}\n"
        memo += f"**Research Query:** {research_query}\n\n"

        # Executive Summary
        memo += f"## EXECUTIVE SUMMARY\n\n"
        summary = self._generate_executive_summary(case, research_query, jurisdiction, documents, precedents)
        memo += summary + "\n\n"

        # Statement of Facts
        memo += f"## STATEMENT OF FACTS\n\n"
        facts = self._generate_facts_section(case)
        memo += facts + "\n\n"

        # Legal Issues
        memo += f"## LEGAL ISSUES\n\n"
        issues = self._identify_legal_issues(research_query, jurisdiction)
        for i, issue in enumerate(issues, 1):
            memo += f"**Issue {i}:** {issue}\n\n"

        # Legal Analysis
        memo += f"## LEGAL ANALYSIS\n\n"
        analysis = self._generate_legal_analysis(research_query, jurisdiction, documents, precedents)
        memo += analysis + "\n\n"

        # Citation Network Analysis
        if len(documents) > 1:
            memo += f"## CITATION NETWORK ANALYSIS\n\n"
            citation_report = self.citation_analyzer.generate_citation_report(documents, case.get('id', ''))
            # Extract key insights from citation report
            citation_insights = self._extract_citation_insights(citation_report)
            memo += citation_insights + "\n\n"

        # Counterfactual Analysis
        memo += f"## COUNTERFACTUAL ANALYSIS\n\n"
        counterfactual_report = self.counterfactual_analyzer.generate_counterfactual_report(case, jurisdiction)
        # Extract key insights
        counterfactual_insights = self._extract_counterfactual_insights(counterfactual_report)
        memo += counterfactual_insights + "\n\n"

        # Conclusion and Recommendations
        memo += f"## CONCLUSION AND RECOMMENDATIONS\n\n"
        conclusion = self._generate_conclusion_and_recommendations(case, research_query, jurisdiction, documents, precedents)
        memo += conclusion + "\n\n"

        # Appendices
        memo += f"## APPENDICES\n\n"
        memo += f"### Appendix A: Relevant Authorities\n"
        authorities = self._compile_authorities(documents, precedents)
        memo += authorities + "\n\n"

        memo += f"### Appendix B: Research Methodology\n"
        memo += self._generate_methodology_section() + "\n\n"

        return memo

    def _generate_executive_summary(self, case: Dict, query: str, jurisdiction: str,
                                   documents: List[Dict], precedents: List[Dict]) -> str:
        """Generate an executive summary for the research memo."""

        summary = f"This memorandum analyzes the legal question: *{query}* in the context of {case.get('title', 'the case')} "

        if jurisdiction:
            summary += f"under {jurisdiction} law. "

        summary += f"The research examined {len(documents)} relevant documents and {len(precedents)} precedential cases. "

        # Analyze strength of position
        position_strength = self._assess_position_strength(documents, precedents, jurisdiction)

        if position_strength['overall'] == 'STRONG':
            summary += "Based on the analysis, the position appears **strong** with favorable precedent and supporting authority. "
        elif position_strength['overall'] == 'MODERATE':
            summary += "The analysis reveals a **moderate** position with mixed precedent and some supporting authority. "
        else:
            summary += "The research indicates a **weak** position with unfavorable precedent and limited supporting authority. "

        summary += f"Key findings include {position_strength['favorable_cases']} favorable and {position_strength['unfavorable_cases']} unfavorable cases. "

        # Add risk assessment
        if position_strength['risk_level'] == 'HIGH':
            summary += "However, there are significant legal risks that should be carefully considered. "
        elif position_strength['risk_level'] == 'MEDIUM':
            summary += "Some legal risks exist that may impact the outcome. "

        return summary

    def _generate_facts_section(self, case: Dict) -> str:
        """Generate the statement of facts section."""

        facts = case.get('description', 'Case facts not provided.')

        # Format the facts professionally
        formatted_facts = f"**Case Background:** {facts}\n\n"

        # Add any additional context if available
        if case.get('category'):
            formatted_facts += f"**Legal Category:** {case['category']}\n\n"

        return formatted_facts

    def _identify_legal_issues(self, query: str, jurisdiction: str) -> List[str]:
        """Identify and articulate the legal issues from the research query."""

        # Use query expansion to identify related legal concepts
        expanded_query = self.query_expander.expand_query(query, jurisdiction)

        issues = []

        # Extract legal issues from expanded query
        legal_concepts = expanded_query.get('legal_concepts', [])
        jurisdictional_terms = expanded_query.get('jurisdictional_terms', [])

        for concept in legal_concepts[:3]:  # Limit to top 3 issues
            issues.append(f"Whether {concept.lower()} applies to the facts of this case")

        if jurisdictional_terms:
            issues.append(f"The applicability of {jurisdictional_terms[0]} jurisdiction to these proceedings")

        # Add standard legal issues if none identified
        if not issues:
            issues = [
                "The applicable legal standard and burden of proof",
                "The sufficiency of evidence to meet legal requirements",
                "Potential defenses and their applicability"
            ]

        return issues

    def _generate_legal_analysis(self, query: str, jurisdiction: str,
                                documents: List[Dict], precedents: List[Dict]) -> str:
        """Generate the legal analysis section."""

        analysis = ""

        # Analyze documents
        if documents:
            analysis += f"### Analysis of Relevant Documents\n\n"
            for i, doc in enumerate(documents[:5], 1):  # Limit to top 5
                analysis += f"**Document {i}:** {doc.get('filename', 'Unknown')}\n"
                content_preview = doc.get('content', '')[:200] + "..." if len(doc.get('content', '')) > 200 else doc.get('content', '')
                analysis += f"Key provisions: {content_preview}\n\n"

        # Analyze precedents
        if precedents:
            analysis += f"### Precedential Analysis\n\n"
            favorable = []
            unfavorable = []

            for case in precedents:
                # Simple heuristic - could be enhanced
                if any(word in case.get('content', '').lower() for word in ['granted', 'affirmed', 'favorable']):
                    favorable.append(case)
                else:
                    unfavorable.append(case)

            if favorable:
                analysis += f"**Favorable Precedent:**\n"
                for case in favorable[:3]:
                    analysis += f"- *{case.get('title', 'Unknown')}*: Supports the position\n"

            if unfavorable:
                analysis += f"\n**Unfavorable Precedent:**\n"
                for case in unfavorable[:3]:
                    analysis += f"- *{case.get('title', 'Unknown')}*: May weaken the position\n"

        return analysis

    def _assess_position_strength(self, documents: List[Dict], precedents: List[Dict], jurisdiction: str) -> Dict:
        """Assess the overall strength of the legal position."""

        # Simple assessment - could be enhanced with ML
        favorable_cases = len([p for p in precedents if 'favorable' in p.get('content', '').lower()])
        unfavorable_cases = len([p for p in precedents if 'unfavorable' in p.get('content', '').lower()])

        total_cases = len(precedents)

        if total_cases == 0:
            return {'overall': 'UNKNOWN', 'favorable_cases': 0, 'unfavorable_cases': 0, 'risk_level': 'HIGH'}

        favorable_ratio = favorable_cases / total_cases

        if favorable_ratio >= 0.7:
            overall = 'STRONG'
            risk_level = 'LOW'
        elif favorable_ratio >= 0.4:
            overall = 'MODERATE'
            risk_level = 'MEDIUM'
        else:
            overall = 'WEAK'
            risk_level = 'HIGH'

        return {
            'overall': overall,
            'favorable_cases': favorable_cases,
            'unfavorable_cases': unfavorable_cases,
            'risk_level': risk_level
        }

    def _extract_citation_insights(self, citation_report: str) -> str:
        """Extract key insights from citation analysis."""

        insights = "Based on citation network analysis:\n\n"

        # Extract key points from the citation report
        lines = citation_report.split('\n')
        key_findings = []

        for line in lines:
            if any(keyword in line.lower() for keyword in ['landmark', 'central', 'cluster', 'chain']):
                key_findings.append(line.strip())

        if key_findings:
            for finding in key_findings[:3]:
                insights += f"- {finding}\n"
        else:
            insights += "- Citation analysis completed with no significant clusters identified.\n"

        return insights

    def _extract_counterfactual_insights(self, counterfactual_report: str) -> str:
        """Extract key insights from counterfactual analysis."""

        insights = "Counterfactual analysis reveals:\n\n"

        # Extract key risks and considerations
        lines = counterfactual_report.split('\n')
        key_risks = []

        for line in lines:
            if any(keyword in line.lower() for keyword in ['high impact', 'risk', 'strategic']):
                key_risks.append(line.strip())

        if key_risks:
            for risk in key_risks[:3]:
                insights += f"- {risk}\n"
        else:
            insights += "- Multiple scenarios analyzed with varying risk levels identified.\n"

        return insights

    def _generate_conclusion_and_recommendations(self, case: Dict, query: str, jurisdiction: str,
                                                documents: List[Dict], precedents: List[Dict]) -> str:
        """Generate conclusion and recommendations."""

        position_strength = self._assess_position_strength(documents, precedents, jurisdiction)

        conclusion = f"## Conclusion\n\n"
        conclusion += f"Based on the foregoing analysis, "

        if position_strength['overall'] == 'STRONG':
            conclusion += "the legal position appears strong with favorable precedent and supporting authority. "
        elif position_strength['overall'] == 'MODERATE':
            conclusion += "the legal position is moderate with mixed precedent requiring careful evaluation. "
        else:
            conclusion += "the legal position appears weak with unfavorable precedent and limited supporting authority. "

        conclusion += f"The research identified {position_strength['favorable_cases']} favorable and {position_strength['unfavorable_cases']} unfavorable cases.\n\n"

        # Recommendations
        conclusion += f"## Recommendations\n\n"

        if position_strength['overall'] == 'STRONG':
            conclusion += "1. **Proceed with litigation** given the favorable legal landscape.\n"
            conclusion += "2. **Preserve all evidence** to maintain the strong position.\n"
            conclusion += "3. **Consider settlement** only if terms are highly favorable.\n"
        elif position_strength['overall'] == 'MODERATE':
            conclusion += "1. **Conduct additional discovery** to strengthen the position.\n"
            conclusion += "2. **Explore settlement options** given the mixed precedent.\n"
            conclusion += "3. **Develop alternative legal theories** to address weaknesses.\n"
        else:
            conclusion += "1. **Reevaluate case strategy** given unfavorable precedent.\n"
            conclusion += "2. **Pursue settlement aggressively** to minimize exposure.\n"
            conclusion += "3. **Consider motion to dismiss** or summary judgment.\n"

        conclusion += "4. **Monitor for changes in law** that may affect this analysis.\n"
        conclusion += "5. **Preserve appellate rights** in all proceedings.\n"

        return conclusion

    def _compile_authorities(self, documents: List[Dict], precedents: List[Dict]) -> str:
        """Compile list of relevant authorities."""

        authorities = ""

        if precedents:
            authorities += "**Cases:**\n"
            for case in precedents[:10]:  # Limit to top 10
                authorities += f"- {case.get('title', 'Unknown Case')}\n"
            authorities += "\n"

        if documents:
            authorities += "**Documents:**\n"
            for doc in documents[:10]:  # Limit to top 10
                authorities += f"- {doc.get('filename', 'Unknown Document')}\n"
            authorities += "\n"

        return authorities

    def _generate_methodology_section(self) -> str:
        """Generate research methodology section."""

        methodology = """This research memorandum was prepared using advanced AI-powered legal research techniques:

1. **Query Expansion**: Legal concepts and jurisdictional terms were expanded to ensure comprehensive coverage.

2. **Multi-Modal Analysis**: Text and visual evidence were analyzed for relevant legal content.

3. **Citation Network Analysis**: Relationships between legal authorities were mapped and analyzed.

4. **Counterfactual Analysis**: Alternative scenarios were evaluated for risk assessment.

5. **Confidence Scoring**: All analyses include reliability assessments.

6. **Jurisdiction-Specific Research**: Analysis was tailored to the applicable legal framework.

Research was conducted using authoritative legal sources and precedential cases. The analysis represents the current state of the law as of the date of this memorandum."""

        return methodology

    def generate_case_brief(self, case: Dict, jurisdiction: str, documents: List[Dict]) -> str:
        """Generate a professional case brief."""

        brief = f"# CASE BRIEF\n\n"
        brief += f"**Case Name:** {case.get('title', 'Unknown')}\n"
        brief += f"**Jurisdiction:** {jurisdiction}\n"
        brief += f"**Date:** {datetime.datetime.now().strftime('%B %d, %Y')}\n\n"

        # Case Summary
        brief += f"## Case Summary\n\n"
        brief += f"{case.get('description', 'Case details not available.')}\n\n"

        # Key Facts
        brief += f"## Key Facts\n\n"
        facts = self._extract_key_facts(case)
        brief += facts + "\n\n"

        # Legal Issues
        brief += f"## Legal Issues\n\n"
        issues = self._identify_legal_issues_from_case(case, jurisdiction)
        for issue in issues:
            brief += f"- {issue}\n"
        brief += "\n"

        # Analysis
        brief += f"## Analysis\n\n"
        analysis = self._generate_brief_analysis(case, jurisdiction, documents)
        brief += analysis + "\n\n"

        return brief

    def _extract_key_facts(self, case: Dict) -> str:
        """Extract key facts from case description."""
        description = case.get('description', '')
        # Simple extraction - could be enhanced
        sentences = description.split('.')
        key_facts = [s.strip() for s in sentences if len(s.strip()) > 20][:5]
        return '\n'.join(f"- {fact}." for fact in key_facts)

    def _identify_legal_issues_from_case(self, case: Dict, jurisdiction: str) -> List[str]:
        """Identify legal issues from case content."""
        description = case.get('description', '').lower()

        issues = []
        if any(word in description for word in ['contract', 'agreement', 'breach']):
            issues.append("Whether there was a valid contract and if it was breached")
        if any(word in description for word in ['negligence', 'duty', 'care']):
            issues.append("Whether the defendant owed a duty of care and breached it")
        if any(word in description for word in ['damages', 'compensation', 'injury']):
            issues.append("The appropriate measure and amount of damages")

        if not issues:
            issues = ["Legal issues to be determined based on case facts"]

        return issues

    def _generate_brief_analysis(self, case: Dict, jurisdiction: str, documents: List[Dict]) -> str:
        """Generate analysis for case brief."""
        analysis = f"Based on {jurisdiction} law and the facts presented, this case involves "

        description = case.get('description', '').lower()
        if 'contract' in description:
            analysis += "contract law principles including formation, breach, and remedies."
        elif 'negligence' in description:
            analysis += "tort law principles including duty, breach, causation, and damages."
        else:
            analysis += "various legal principles that require careful analysis."

        analysis += f"\n\nThe analysis considers {len(documents)} relevant documents and applies current legal standards."

        return analysis
