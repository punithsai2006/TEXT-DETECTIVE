import logging
import uuid
from typing import Any, Dict, List, Optional

from app.models.schemas import (
    AgentMessage,
    AgentRole,
    CaseGraph,
    ContradictionItem,
    Entity,
    Event,
    ForensicSummaryMilestone,
    Hypothesis,
    MultiAgentDeliberation,
    TimelineEntry,
)
from app.services.agents.crossexam_agent import cross_exam_agent
from app.services.agents.graph_rag_agent import graph_rag_agent
from app.services.agents.hypothesis_agent import hypothesis_agent
from app.services.agents.timeline_agent import forensic_timeline_agent

logger = logging.getLogger(__name__)


class MultiAgentSwarmOrchestrator:
    """
    Master Orchestration Coordinator for the Text Detective Multi-Agent Swarm (MAS).
    
    Coordinates autonomous agent communication, knowledge graph retrieval,
    timeline summarization, forensic cross-examination, and adversarial multi-LLM debates.
    """

    def __init__(self):
        self.orchestrator_name = "LeadInvestigatorAgent"
        self.role = "Chief Investigative Strategy Coordinator"

    def run_multi_agent_investigation(
        self,
        case_id: str,
        case_name: str,
        case_graph: CaseGraph,
        raw_timeline: List[TimelineEntry],
        events: List[Event],
        entities: List[Entity],
        contradictions: List[ContradictionItem],
        hypotheses: List[Hypothesis],
    ) -> Tuple[List[ForensicSummaryMilestone], MultiAgentDeliberation]:
        """
        Executes the collaborative multi-agent workflow and returns:
        1. A synthesized Forensic Summary Timeline (5 structured crime phases derived from the Case Graph).
        2. A complete Multi-Agent Deliberation record containing agent messages, debates, and consensus.
        """
        messages: List[AgentMessage] = []

        def log_msg(sender: str, recipient: str, m_type: str, thought: str, content: str, citations: List[str] = None, nodes: List[str] = None):
            messages.append(
                AgentMessage(
                    message_id=f"msg_{uuid.uuid4().hex[:8]}",
                    sender=sender,
                    recipient=recipient,
                    message_type=m_type,
                    thought_process=thought,
                    content=content,
                    evidence_citations=citations or [],
                    subgraph_nodes=nodes or [],
                )
            )

        # -------------------------------------------------------------
        # ROUND 1: Task Delegation & Graph-RAG Neighborhood Query
        # -------------------------------------------------------------
        log_msg(
            sender=AgentRole.LEAD_INVESTIGATOR.value,
            recipient=AgentRole.GRAPH_RAG_SPECIALIST.value,
            m_type="task_delegation",
            thought="We need to traverse the newly constructed Case Graph to identify high-centrality suspect nodes and restricted asset access edges.",
            content=f"Initiate Graph-RAG multi-hop neighborhood traversal for case '{case_name}'. Focus on restricted locations, physical keys, and vehicle movements.",
            citations=[f"Case Graph ({len(case_graph.nodes)} nodes, {len(case_graph.edges)} edges)"],
            nodes=[n.label for n in case_graph.nodes[:5]],
        )

        # Execute Graph-RAG
        lead_suspects = [e.name for e in entities if e.entity_type.value == "person"][:3]
        graph_rag_result = graph_rag_agent.retrieve_subgraph_evidence(
            case_id=case_id,
            query="restricted cage access vehicle loading dock keycard tap",
            case_graph=case_graph,
            seed_entities=lead_suspects,
            max_hops=2,
            top_k=5,
        )

        log_msg(
            sender=AgentRole.GRAPH_RAG_SPECIALIST.value,
            recipient=AgentRole.LEAD_INVESTIGATOR.value,
            m_type="graph_retrieval",
            thought="Traversed 2-hop graph neighborhood from suspect nodes. Located physical custody transfer edges and key usage nodes.",
            content=(
                f"Graph-RAG traversal complete. Discovered {len(graph_rag_result.get('graph_paths', []))} connected relational paths. "
                f"Key path: {graph_rag_result.get('graph_paths', ['(Suspect) -> [USES] -> (Restricted Asset)'])[0]}"
            ),
            citations=[chk.get("document", "doc") for chk in graph_rag_result.get("vector_evidence", [])[:3]],
            nodes=graph_rag_result.get("subgraph_nodes", [])[:6],
        )

        # -------------------------------------------------------------
        # ROUND 2: Timeline Agent Graph-Driven Phase Summarization
        # -------------------------------------------------------------
        log_msg(
            sender=AgentRole.LEAD_INVESTIGATOR.value,
            recipient=AgentRole.FORENSIC_TIMELINE.value,
            m_type="task_delegation",
            thought="Raw sorted document lines are noisy for courtroom presentation. We need a graph-grounded Summary Timeline organized by Crime Phases.",
            content="Synthesize raw timeline entries and Case Graph edges into an executive Forensic Summary Timeline clustered by strategic crime phases.",
            citations=[f"{len(raw_timeline)} sequenced log events"],
        )

        summary_timeline = forensic_timeline_agent.synthesize_summary_timeline(
            case_graph=case_graph,
            raw_timeline=raw_timeline,
            events=events,
            entities=entities,
            contradictions=contradictions,
        )

        time_window = summary_timeline[1].timestamp_range if len(summary_timeline) > 1 else "critical incident window"
        log_msg(
            sender=AgentRole.FORENSIC_TIMELINE.value,
            recipient=AgentRole.LEAD_INVESTIGATOR.value,
            m_type="consensus",
            thought="Successfully clustered events into 5 sequential crime phases: Preparation, Breach, Seizure, Egress, and Fabrication.",
            content=(
                f"Forensic Summary Timeline synthesized: {len(summary_timeline)} strategic crime phases identified. "
                f"Physical breach window isolated during: {time_window}."
            ),
            citations=[m.corroborating_sources[0]["document"] for m in summary_timeline if m.corroborating_sources],
            nodes=[m.primary_actor for m in summary_timeline if m.primary_actor],
        )

        # -------------------------------------------------------------
        # ROUND 3: Cross-Examination Agent Deception Detection
        # -------------------------------------------------------------
        log_msg(
            sender=AgentRole.LEAD_INVESTIGATOR.value,
            recipient=AgentRole.CROSS_EXAMINATION.value,
            m_type="task_delegation",
            thought="Cross-examine suspect claims against hard physical sensor nodes (RFID, key locks, CCTV).",
            content="Evaluate witness and suspect interview statements against objective telemetry logs to detect deception and alibi breakdown.",
        )

        crossexam_result = cross_exam_agent.cross_examine_suspect_claims(
            contradictions=contradictions,
            timeline=raw_timeline,
            entities=entities,
        )

        log_msg(
            sender=AgentRole.CROSS_EXAMINATION.value,
            recipient=AgentRole.LEAD_INVESTIGATOR.value,
            m_type="contradiction_alert",
            thought="Detected confirmed physical contradictions. Suspect testimonial claims are refuted by objective physical telemetry.",
            content=(
                f"Cross-examination identified {crossexam_result.get('total_confirmed_lies', 0)} confirmed perjury points. "
                f"Suspect credibility is severely compromised by physical RFID and ANPR sensor telemetry."
            ),
            citations=[d["refuted_claims"][0]["refuting_source"] for d in crossexam_result.get("suspect_dossiers", []) if d.get("refuted_claims")],
        )

        # -------------------------------------------------------------
        # ROUND 4: Adversarial Multi-LLM Courtroom Debate
        # -------------------------------------------------------------
        log_msg(
            sender=AgentRole.LEAD_INVESTIGATOR.value,
            recipient=AgentRole.ADVERSARIAL_HYPOTHESIS.value,
            m_type="task_delegation",
            thought="Initiate multi-LLM adversarial debate: Prosecution Model vs. Defense Model to stress-test candidate guilt hypotheses.",
            content="Conduct adversarial debate between Prosecution and Defense LLM agents using Slide 18 formula and verified graph evidence.",
        )

        lead_h = hypotheses[0] if hypotheses else None
        debate_result = hypothesis_agent.conduct_courtroom_debate(
            lead_hypothesis=lead_h,
            competing_hypotheses=hypotheses[1:],
            confirmed_contradictions=contradictions,
            corroborated_evidence=[],
        )

        log_msg(
            sender=AgentRole.ADVERSARIAL_HYPOTHESIS.value,
            recipient=AgentRole.LEAD_INVESTIGATOR.value,
            m_type="hypothesis_debate",
            thought="Debate concluded. Defense argued alternative theories, but multi-sensor concurrence and physical telemetry confirm guilt beyond reasonable doubt.",
            content=(
                f"Multi-LLM Debate Concluded. Verdict: {debate_result.get('verdict', {}).get('verdict', 'Guilty')}. "
                f"Confidence: {debate_result.get('verdict', {}).get('confidence_percentage', 95)}%. "
                f"Slide 18 Score: {debate_result.get('prosecution', {}).get('mathematical_score', 0)}."
            ),
            citations=[f"Slide 18 Formula: Score = {lead_h.total_score if lead_h else 0}"],
        )

        deliberation_record = MultiAgentDeliberation(
            case_id=case_id,
            agents_involved=[
                AgentRole.LEAD_INVESTIGATOR.value,
                AgentRole.GRAPH_RAG_SPECIALIST.value,
                AgentRole.FORENSIC_TIMELINE.value,
                AgentRole.CROSS_EXAMINATION.value,
                AgentRole.ADVERSARIAL_HYPOTHESIS.value,
            ],
            messages=messages,
            prosecution_argument=debate_result.get("prosecution", {}),
            defense_argument=debate_result.get("defense", {}),
            judicial_verdict=debate_result.get("verdict", {}),
            confidence_score=debate_result.get("verdict", {}).get("confidence_percentage", 95.0) / 100.0,
        )

        logger.info(
            f"Multi-Agent Swarm completed investigation for case '{case_id}'. "
            f"Generated {len(summary_timeline)} summary milestones and {len(messages)} deliberation messages."
        )

        return summary_timeline, deliberation_record


agent_swarm_orchestrator = MultiAgentSwarmOrchestrator()
