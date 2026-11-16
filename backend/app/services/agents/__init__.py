"""
Text Detective Multi-Agent System (MAS) Framework.
Autonomous specialized AI agents for forensic knowledge graph traversal,
timeline summarization, cross-examination, and adversarial hypothesis debate.
"""

from app.services.agents.timeline_agent import ForensicTimelineAgent, forensic_timeline_agent
from app.services.agents.graph_rag_agent import KnowledgeGraphRAGAgent, graph_rag_agent
from app.services.agents.crossexam_agent import CrossExaminationAgent, cross_exam_agent
from app.services.agents.hypothesis_agent import AdversarialHypothesisAgent, hypothesis_agent
from app.services.agents.orchestrator import MultiAgentSwarmOrchestrator, agent_swarm_orchestrator

__all__ = [
    "ForensicTimelineAgent",
    "forensic_timeline_agent",
    "KnowledgeGraphRAGAgent",
    "graph_rag_agent",
    "CrossExaminationAgent",
    "cross_exam_agent",
    "AdversarialHypothesisAgent",
    "hypothesis_agent",
    "MultiAgentSwarmOrchestrator",
    "agent_swarm_orchestrator",
]
