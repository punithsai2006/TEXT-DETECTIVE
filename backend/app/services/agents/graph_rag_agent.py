import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from app.models.schemas import CaseGraph, CaseGraphEdge, CaseGraphNode, EvidenceItem
from app.services.retrieval.retriever import retriever

logger = logging.getLogger(__name__)


class KnowledgeGraphRAGAgent:
    """
    Autonomous AI Agent specializing in Knowledge Graph-Augmented Retrieval (Graph-RAG).
    
    Combines multi-hop graph neighborhood traversal across the Case Graph
    with dense vector embeddings (all-MiniLM-L6-v2) and lexical BM25/TF-IDF
    via Reciprocal Rank Fusion (RRF).
    """

    def __init__(self):
        self.agent_name = "KnowledgeGraphRAGAgent"
        self.role = "Forensic Graph-RAG Retrieval Specialist"

    def retrieve_subgraph_evidence(
        self,
        case_id: str,
        query: str,
        case_graph: CaseGraph,
        seed_entities: Optional[List[str]] = None,
        max_hops: int = 2,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Executes a dual-channel Graph-RAG query:
        Channel 1: Traverses the Case Graph around seed entities up to `max_hops` to discover connected subgraphs.
        Channel 2: Queries the hybrid vector/keyword index via Reciprocal Rank Fusion (RRF).
        Merges both channels to return grounded multi-hop evidence paths.
        """
        # Channel 1: Graph Traversal
        matched_nodes: List[CaseGraphNode] = []
        matched_edges: List[CaseGraphEdge] = []
        visited_node_ids: Set[str] = set()

        q_lower = query.lower()
        seeds = [s.lower() for s in (seed_entities or [])]

        # Find starting anchor nodes
        start_nodes = []
        for n in case_graph.nodes:
            lbl = n.label.lower()
            if any(s in lbl for s in seeds) or any(w in lbl for w in q_lower.split() if len(w) > 3):
                start_nodes.append(n)
                visited_node_ids.add(n.id)

        # Multi-hop graph neighborhood expansion
        frontier = [n.id for n in start_nodes]
        matched_nodes.extend(start_nodes)

        for hop in range(max_hops):
            next_frontier = []
            for curr_id in frontier:
                for edge in case_graph.edges:
                    neighbor_id = None
                    if edge.source == curr_id and edge.target not in visited_node_ids:
                        neighbor_id = edge.target
                    elif edge.target == curr_id and edge.source not in visited_node_ids:
                        neighbor_id = edge.source

                    if neighbor_id:
                        visited_node_ids.add(neighbor_id)
                        next_frontier.append(neighbor_id)
                        matched_edges.append(edge)
                        node_obj = next((n for n in case_graph.nodes if n.id == neighbor_id), None)
                        if node_obj:
                            matched_nodes.append(node_obj)
            frontier = next_frontier

        # Format Graph Subgraph Paths
        graph_paths = []
        for e in matched_edges[:12]:
            s_node = next((n for n in case_graph.nodes if n.id == e.source), None)
            t_node = next((n for n in case_graph.nodes if n.id == e.target), None)
            s_name = s_node.label if s_node else e.source
            t_name = t_node.label if t_node else e.target
            path_str = f"({s_name}) -[:{e.relation.upper()}]-> ({t_name})"
            if e.evidence_sentence:
                path_str += f" [Evidence: \"{e.evidence_sentence[:70]}...\"]"
            graph_paths.append(path_str)

        # Channel 2: Hybrid Dense/BM25 Vector Retrieval via RRF
        retrieved_chunks = retriever.search(case_id=case_id, query=query, top_k=top_k)

        logger.info(
            f"Graph-RAG Agent: retrieved {len(matched_nodes)} nodes, {len(matched_edges)} edges, "
            f"and {len(retrieved_chunks)} RRF vector chunks for query '{query[:40]}'."
        )

        return {
            "query": query,
            "graph_paths": graph_paths,
            "subgraph_nodes": [n.label for n in matched_nodes[:15]],
            "subgraph_edge_count": len(matched_edges),
            "vector_evidence": [
                {
                    "document": chk.document_name,
                    "timestamp": chk.timestamp,
                    "speaker": chk.speaker,
                    "excerpt": chk.text,
                    "chunk_id": chk.chunk_id,
                }
                for chk in retrieved_chunks
            ],
            "retrieval_method": "Dual-Channel Graph-RAG (Case Graph Traversal + Dense/BM25 RRF)",
        }


graph_rag_agent = KnowledgeGraphRAGAgent()
