"""
Counterfactual Legal Analysis
Analyzes hypothetical scenarios and their legal implications.
"""

from typing import Dict, List, Optional
import json
from rag.query_expander import LegalQueryExpander
from rag.jurisdiction_manager import JurisdictionManager
from rag.confidence_scorer import ConfidenceScorer
from rag.multi_modal import MultiModalRetriever


class CounterfactualAnalyzer:
    """Analyzes counterfactual legal scenarios."""

    def __init__(self):
        self.query_expander = LegalQueryExpander()
        self.jurisdiction_manager = JurisdictionManager()
        self.confidence_scorer = ConfidenceScorer()
        self.multi_modal = MultiModalRetriever()

    def generate_counterfactual_scenarios(self, case_facts: str, jurisdiction: str) -> List[Dict]:
        """Generate plausible counterfactual scenarios for a legal case."""

        # Extract key elements from case facts
        key_elements = self._extract_case_elements(case_facts)

        scenarios = []

        # Scenario 1: Different timing
        if key_elements.get('dates'):
            scenarios.append({
                'type': 'temporal',
                'description': 'What if the incident occurred at a different time?',
                'variables': ['time_of_incident', 'statute_of_limitations', 'jurisdictional_changes'],
                'potential_impacts': [
                    'Different applicable law',
                    'Statute of limitations issues',
                    'Different court jurisdiction',
                    'Changes in evidentiary requirements'
                ]
            })

        # Scenario 2: Different jurisdiction
        scenarios.append({
            'type': 'jurisdictional',
            'description': 'What if the case was filed in a different jurisdiction?',
            'variables': ['court_location', 'applicable_law', 'precedent_availability'],
            'potential_impacts': [
                'Different substantive law application',
                'Different procedural rules',
                'Access to different precedents',
                'Different jury pool characteristics',
                'Changes in damages calculations'
            ]
        })

        # Scenario 3: Different parties involved
        if key_elements.get('parties'):
            scenarios.append({
                'type': 'party_based',
                'description': 'What if different parties were involved?',
                'variables': ['party_characteristics', 'relationships', 'prior_interactions'],
                'potential_impacts': [
                    'Different legal standards of care',
                    'Changes in burden of proof',
                    'Different evidentiary admissibility',
                    'Alterations in damages claims'
                ]
            })

        # Scenario 4: Different evidence available
        scenarios.append({
            'type': 'evidentiary',
            'description': 'What if different evidence was available?',
            'variables': ['witness_availability', 'document_discovery', 'expert_testimony'],
            'potential_impacts': [
                'Changes in proof strength',
                'Different trial strategies',
                'Settlement vs. litigation decisions',
                'Changes in case valuation'
            ]
        })

        # Scenario 5: Legislative changes
        scenarios.append({
            'type': 'legislative',
            'description': 'What if relevant laws were different?',
            'variables': ['statutory_interpretation', 'recent_legislation', 'constitutional_issues'],
            'potential_impacts': [
                'Different legal standards',
                'Changes in liability determinations',
                'Alterations in remedy availability',
                'Impact on class action potential'
            ]
        })

        return scenarios

    def analyze_counterfactual_scenario(self, original_case: Dict, scenario: Dict, jurisdiction: str) -> Dict:
        """Analyze the legal implications of a specific counterfactual scenario."""

        analysis = {
            'scenario': scenario,
            'legal_implications': [],
            'risk_assessment': {},
            'strategic_considerations': [],
            'confidence_score': 0
        }

        scenario_type = scenario.get('type')

        if scenario_type == 'temporal':
            analysis['legal_implications'] = self._analyze_temporal_scenario(original_case, jurisdiction)
        elif scenario_type == 'jurisdictional':
            analysis['legal_implications'] = self._analyze_jurisdictional_scenario(original_case, jurisdiction)
        elif scenario_type == 'party_based':
            analysis['legal_implications'] = self._analyze_party_scenario(original_case, jurisdiction)
        elif scenario_type == 'evidentiary':
            analysis['legal_implications'] = self._analyze_evidentiary_scenario(original_case, jurisdiction)
        elif scenario_type == 'legislative':
            analysis['legal_implications'] = self._analyze_legislative_scenario(original_case, jurisdiction)

        # Assess risks
        analysis['risk_assessment'] = self._assess_scenario_risks(analysis['legal_implications'])

        # Strategic considerations
        analysis['strategic_considerations'] = self._generate_strategic_considerations(scenario, analysis['legal_implications'])

        # Confidence scoring
        analysis['confidence_score'] = self.confidence_scorer.score_response(
            json.dumps(analysis), f"Counterfactual analysis for {scenario_type} scenario"
        )

        return analysis

    def _extract_case_elements(self, case_facts: str) -> Dict:
        """Extract key elements from case facts for counterfactual analysis."""
        elements = {
            'parties': [],
            'dates': [],
            'jurisdiction': None,
            'legal_issues': [],
            'evidence': []
        }

        # Simple extraction - could be enhanced with NLP
        lines = case_facts.split('\n')
        for line in lines:
            line = line.strip().lower()
            if ' vs ' in line or ' versus ' in line or ' plaintiff' in line or ' defendant' in line:
                elements['parties'].append(line)
            if any(word in line for word in ['january', 'february', 'march', 'april', 'may', 'june',
                                          'july', 'august', 'september', 'october', 'november', 'december',
                                          'occurred', 'happened', 'date']):
                elements['dates'].append(line)

        return elements

    def _analyze_temporal_scenario(self, case: Dict, jurisdiction: str) -> List[Dict]:
        """Analyze implications of different timing."""
        implications = []

        implications.append({
            'aspect': 'Statute of Limitations',
            'impact': 'HIGH',
            'description': 'Different timing could affect whether claims are time-barred',
            'specific_changes': ['Filing deadlines', 'Discovery periods', 'Appeal windows']
        })

        implications.append({
            'aspect': 'Applicable Law',
            'impact': 'MEDIUM',
            'description': 'Laws may have changed between different time periods',
            'specific_changes': ['Statutory amendments', 'Judicial interpretations', 'Regulatory changes']
        })

        return implications

    def _analyze_jurisdictional_scenario(self, case: Dict, jurisdiction: str) -> List[Dict]:
        """Analyze implications of different jurisdiction."""
        implications = []

        implications.append({
            'aspect': 'Substantive Law',
            'impact': 'HIGH',
            'description': 'Different jurisdictions apply different substantive legal rules',
            'specific_changes': ['Liability standards', 'Damage calculations', 'Causation requirements']
        })

        implications.append({
            'aspect': 'Procedural Rules',
            'impact': 'HIGH',
            'description': 'Court procedures and rules vary significantly by jurisdiction',
            'specific_changes': ['Pleadings standards', 'Discovery rules', 'Trial procedures']
        })

        return implications

    def _analyze_party_scenario(self, case: Dict, jurisdiction: str) -> List[Dict]:
        """Analyze implications of different parties."""
        implications = []

        implications.append({
            'aspect': 'Standard of Care',
            'impact': 'MEDIUM',
            'description': 'Different parties may be held to different standards of conduct',
            'specific_changes': ['Professional standards', 'Reasonable person standards', 'Industry customs']
        })

        return implications

    def _analyze_evidentiary_scenario(self, case: Dict, jurisdiction: str) -> List[Dict]:
        """Analyze implications of different evidence."""
        implications = []

        implications.append({
            'aspect': 'Burden of Proof',
            'impact': 'HIGH',
            'description': 'Different evidence strength affects proof requirements',
            'specific_changes': ['Sufficiency of evidence', 'Jury instructions', 'Directed verdict potential']
        })

        return implications

    def _analyze_legislative_scenario(self, case: Dict, jurisdiction: str) -> List[Dict]:
        """Analyze implications of different legislation."""
        implications = []

        implications.append({
            'aspect': 'Legal Standards',
            'impact': 'HIGH',
            'description': 'Changes in law fundamentally alter legal analysis',
            'specific_changes': ['Liability frameworks', 'Remedy availability', 'Defenses applicability']
        })

        return implications

    def _assess_scenario_risks(self, implications: List[Dict]) -> Dict:
        """Assess overall risks of the counterfactual scenario."""
        high_impact = len([imp for imp in implications if imp['impact'] == 'HIGH'])
        medium_impact = len([imp for imp in implications if imp['impact'] == 'MEDIUM'])

        risk_level = 'LOW'
        if high_impact >= 2:
            risk_level = 'HIGH'
        elif high_impact >= 1 or medium_impact >= 2:
            risk_level = 'MEDIUM'

        return {
            'overall_risk': risk_level,
            'high_impact_factors': high_impact,
            'medium_impact_factors': medium_impact,
            'key_risks': [imp['aspect'] for imp in implications if imp['impact'] in ['HIGH', 'MEDIUM']]
        }

    def _generate_strategic_considerations(self, scenario: Dict, implications: List[Dict]) -> List[str]:
        """Generate strategic considerations for the scenario."""
        considerations = []

        scenario_type = scenario.get('type')

        if scenario_type == 'temporal':
            considerations.extend([
                'Consider forum shopping for most favorable timing rules',
                'Evaluate preservation of evidence requirements',
                'Assess impact on witness availability and memory'
            ])
        elif scenario_type == 'jurisdictional':
            considerations.extend([
                'Venue selection becomes critical strategic decision',
                'Consider removal or transfer options',
                'Evaluate jury pool characteristics and demographics'
            ])
        elif scenario_type == 'evidentiary':
            considerations.extend([
                'Focus on evidence preservation and spoliation prevention',
                'Develop comprehensive discovery strategies',
                'Consider impact on settlement negotiations'
            ])

        return considerations

    def generate_counterfactual_report(self, case: Dict, jurisdiction: str) -> str:
        """Generate a comprehensive counterfactual analysis report."""

        case_facts = case.get('description', '')
        scenarios = self.generate_counterfactual_scenarios(case_facts, jurisdiction)

        report = f"# Counterfactual Legal Analysis Report\n\n"
        report += f"**Case**: {case.get('title', 'Unknown')}\n"
        report += f"**Jurisdiction**: {jurisdiction}\n\n"

        report += f"## Generated Scenarios\n\n"

        for i, scenario in enumerate(scenarios, 1):
            report += f"### Scenario {i}: {scenario['description']}\n\n"

            # Analyze this scenario
            analysis = self.analyze_counterfactual_scenario(case, scenario, jurisdiction)

            # Legal Implications
            report += f"**Legal Implications:**\n"
            for imp in analysis['legal_implications']:
                report += f"- **{imp['aspect']}** ({imp['impact']} impact): {imp['description']}\n"
            report += "\n"

            # Risk Assessment
            risk = analysis['risk_assessment']
            report += f"**Risk Assessment:** {risk['overall_risk']}\n"
            report += f"- High impact factors: {risk['high_impact_factors']}\n"
            report += f"- Key risks: {', '.join(risk['key_risks'])}\n\n"

            # Strategic Considerations
            if analysis['strategic_considerations']:
                report += f"**Strategic Considerations:**\n"
                for consideration in analysis['strategic_considerations']:
                    report += f"- {consideration}\n"
                report += "\n"

            # Confidence Score
            confidence = analysis['confidence_score']
            confidence_icon = "🟢" if confidence >= 7 else "🟡" if confidence >= 5 else "🔴"
            report += f"**Analysis Confidence:** {confidence_icon} {confidence}/10\n\n"

            report += "---\n\n"

        report += f"## Summary Insights\n\n"
        report += f"- **Total Scenarios Analyzed**: {len(scenarios)}\n"
        report += f"- **High-Risk Scenarios**: {len([s for s in scenarios if any(imp['impact'] == 'HIGH' for imp in self.analyze_counterfactual_scenario(case, s, jurisdiction)['legal_implications'])])} \n"
        report += f"- **Key Vulnerabilities**: Timing, Jurisdiction, Evidence Strength\n\n"

        report += f"## Recommendations\n\n"
        report += f"1. **Conduct thorough due diligence** on all high-impact variables\n"
        report += f"2. **Develop contingency strategies** for identified risks\n"
        report += f"3. **Consider alternative dispute resolution** if risks are significant\n"
        report += f"4. **Preserve all potential evidence** to maximize options\n"

        return report
