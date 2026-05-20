"""
Legal Citation Network Analysis
Analyzes citation relationships between legal documents and cases.
"""

import re
from typing import List, Dict, Set
from collections import defaultdict
import networkx as nx
from rag.multi_modal import MultiModalRetriever
from rag.jurisdiction_manager import JurisdictionManager
from rag.confidence_scorer import ConfidenceScorer


class CitationNetworkAnalyzer:
    """Analyzes citation networks in legal documents."""

    def __init__(self):
        self.multi_modal = MultiModalRetriever()
        self.jurisdiction_manager = JurisdictionManager()
        self.confidence_scorer = ConfidenceScorer()

    def extract_citations(self, text: str) -> List[str]:
        """Extract legal citations from text using regex patterns."""
        # Common citation patterns
        patterns = [
            r'\d{4}\s+(?:SC|HC|CC|CriLJ|AIR|All|Bom|Cal|Del|Guj|HP|JK|Ker|Mad|MP|Ori|P&H|Pat|Raj|SC|TN|Uttar|WB)\s+\d+',  # Indian citations
            r'\d+\s+U\.S\.\s+\d+',  # US Supreme Court
            r'\d+\s+F\.\s*(?:2d|3d|4th|5th|6th|7th|8th|9th|10th|11th|12th)\s+\d+',  # US Circuit Courts
            r'\d+\s+S\.\s*Ct\.\s+\d+',  # US Supreme Court alternative
            r'\[\d{4}\]\s+(?:EWCA|EWHC|UKSC|UKHL)\s+\d+',  # UK citations
            r'\(\d{4}\)\s+\d+\s+(?:AC|QB|Ch|Fam|RPC|WLR|AllER)\s+\d+',  # UK alternative
        ]

        citations = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.extend(matches)

        return list(set(citations))  # Remove duplicates

    def build_citation_network(self, documents: List[Dict]) -> nx.DiGraph:
        """Build a directed graph of citation relationships."""
        G = nx.DiGraph()

        # Extract citations from each document
        doc_citations = {}
        for doc in documents:
            text = doc.get('content', '')
            citations = self.extract_citations(text)
            doc_citations[doc['id']] = citations

            # Add document as node
            G.add_node(doc['id'],
                      title=doc.get('filename', 'Unknown'),
                      type='document',
                      citations=citations)

        # Create citation edges
        for doc_id, citations in doc_citations.items():
            for citation in citations:
                # Find if any other document contains this citation as a case name
                for other_doc_id, other_citations in doc_citations.items():
                    if doc_id != other_doc_id:
                        # Check if this citation appears in other document's content
                        other_doc = next((d for d in documents if d['id'] == other_doc_id), None)
                        if other_doc and citation in other_doc.get('content', ''):
                            G.add_edge(doc_id, other_doc_id,
                                     citation=citation,
                                     relationship='cites')

        return G

    def analyze_citation_network(self, documents: List[Dict]) -> Dict:
        """Analyze the citation network for insights."""
        G = self.build_citation_network(documents)

        analysis = {
            'network_stats': {
                'total_documents': len(G.nodes()),
                'total_citations': len(G.edges()),
                'density': nx.density(G) if len(G.nodes()) > 1 else 0,
            },
            'central_documents': [],
            'citation_clusters': [],
            'landmark_cases': [],
            'citation_chains': []
        }

        if len(G.nodes()) > 0:
            # Find most cited documents (in-degree centrality)
            in_degree = dict(G.in_degree())
            sorted_by_citations = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)

            analysis['central_documents'] = [
                {
                    'doc_id': doc_id,
                    'citations_received': citations,
                    'title': G.nodes[doc_id].get('title', 'Unknown')
                }
                for doc_id, citations in sorted_by_citations[:5] if citations > 0
            ]

            # Find strongly connected components (citation clusters)
            scc = list(nx.strongly_connected_components(G))
            analysis['citation_clusters'] = [
                {
                    'size': len(component),
                    'documents': [G.nodes[node].get('title', 'Unknown') for node in component]
                }
                for component in scc if len(component) > 1
            ]

            # Find citation chains (longest paths)
            try:
                longest_path = nx.dag_longest_path(G)
                if len(longest_path) > 2:
                    analysis['citation_chains'] = [
                        {
                            'length': len(longest_path),
                            'chain': [G.nodes[node].get('title', 'Unknown') for node in longest_path]
                        }
                    ]
            except:
                pass  # Graph might not be a DAG

        return analysis

    def generate_citation_report(self, documents: List[Dict], case_id: str) -> str:
        """Generate a comprehensive citation network analysis report."""
        analysis = self.analyze_citation_network(documents)

        report = f"# Legal Citation Network Analysis Report\n\n"

        # Network Statistics
        stats = analysis['network_stats']
        report += f"## Network Overview\n"
        report += f"- **Total Documents Analyzed**: {stats['total_documents']}\n"
        report += f"- **Total Citations Found**: {stats['total_citations']}\n"
        report += f"- **Network Density**: {stats['density']:.3f}\n\n"

        # Most Cited Documents
        if analysis['central_documents']:
            report += f"## Most Cited Documents\n"
            for i, doc in enumerate(analysis['central_documents'], 1):
                report += f"{i}. **{doc['title']}** - Cited {doc['citations_received']} times\n"
            report += "\n"

        # Citation Clusters
        if analysis['citation_clusters']:
            report += f"## Citation Clusters\n"
            report += "Documents that frequently cite each other:\n\n"
            for i, cluster in enumerate(analysis['citation_clusters'], 1):
                report += f"**Cluster {i}** ({cluster['size']} documents):\n"
                for doc in cluster['documents']:
                    report += f"- {doc}\n"
                report += "\n"

        # Citation Chains
        if analysis['citation_chains']:
            report += f"## Citation Chains\n"
            for chain in analysis['citation_chains']:
                report += f"**Longest Citation Chain** ({chain['length']} documents):\n"
                for i, doc in enumerate(chain['chain'], 1):
                    report += f"{i}. {doc}\n"
                report += "\n"

        # Insights
        report += f"## Key Insights\n"
        if stats['total_citations'] == 0:
            report += "- No citations detected in the analyzed documents.\n"
        elif stats['density'] > 0.1:
            report += "- High citation density indicates well-connected legal arguments.\n"
        elif analysis['central_documents']:
            central = analysis['central_documents'][0]
            report += f"- **{central['title']}** appears to be a landmark case with {central['citations_received']} citations.\n"

        if analysis['citation_clusters']:
            report += f"- Found {len(analysis['citation_clusters'])} citation clusters, indicating related legal topics.\n"

        return report