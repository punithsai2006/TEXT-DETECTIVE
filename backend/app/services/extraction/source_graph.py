"""Inspectable graph projections retain each originating claim/span lineage."""
from app.models.schemas import CaseGraph, CaseGraphNode, CaseGraphEdge
from app.services.orchestration.evidence_review import digest


def build_source_graph(run, sources, docs):
    nodes, edges = {}, {}
    claims = {c["claim_id"]: c for c in run["claims"]}
    def node(node_id, label, node_type, subtype=None, refs=None, **properties):
        if node_id not in nodes:
            nodes[node_id] = CaseGraphNode(id=node_id, label=label, node_type=node_type, sub_type=subtype,
                properties={"source_span_ids": list(dict.fromkeys(refs or [])), **properties})
        else:
            existing = nodes[node_id].properties["source_span_ids"]
            nodes[node_id].properties["source_span_ids"] = list(dict.fromkeys(existing + (refs or [])))
        return node_id
    def edge(start, end, relation, refs, claim_id):
        edge_id = "edge_" + digest([start, end, relation, refs, claim_id])[:20]
        conflicts = [f["id"] for f in run["comparisons"] if f["outcome"] == "POTENTIAL_CONTRADICTION"
                     and claim_id in (f["claim_a_id"], f["claim_b_id"])]
        edges[edge_id] = CaseGraphEdge(id=edge_id, source=start, target=end, relation=relation,
            source_span_ids=refs, claim_ids=[claim_id], conflict_ids=conflicts,
            evidence_sentence="\n".join(sources[s]["quote"] for s in refs))
    for doc in docs.values():
        node(doc.document_id, doc.filename, "document", refs=[s for s in sources if sources[s]["document_id"] == doc.document_id],
             document_hash=doc.sha256_hash, extraction_version=doc.extraction_version)
    mentions = []
    for entity in run.get("entities", []):
        for doc_id in {sources[s]["document_id"] for s in entity["source_span_ids"]}:
            refs = [s for s in entity["source_span_ids"] if sources[s]["document_id"] == doc_id]
            kind = {"place": "location", "unknown": "object"}.get(entity["entity_type"], entity["entity_type"])
            eid = "mention_" + digest([doc_id, entity["name"], kind])[:20]
            node(eid, entity["name"], "entity", kind, refs, document_id=doc_id, identity="document-scoped mention; no inferred identity merge")
            mentions.append((eid, set(refs)))
    for c in claims.values():
        refs = c["source_span_ids"]
        doc_id = sources[refs[0]]["document_id"]
        conflict_ids = [f["id"] for f in run["comparisons"] if f["outcome"] == "POTENTIAL_CONTRADICTION"
                        and c["claim_id"] in (f["claim_a_id"], f["claim_b_id"])]
        claim_id = node(c["claim_id"], "Source claim: " + c["predicate"] + " " + c["object"], "claim", refs=refs,
                        attribution=c["attribution"], speaker=c["speaker"], conflict_ids=conflict_ids)
        event_id = node("event_" + claim_id, c["subject"] + " / " + c["predicate"], "event", refs=refs,
                        event_basis=c.get("event_basis", "reported"), time_start=c["event_start"], time_end=c["event_end"],
                        timezone=c["timezone"], precision=c["precision"], conflict_ids=conflict_ids)
        edge(doc_id, claim_id, "states_claim", refs, claim_id)
        edge(claim_id, event_id, "reports_event", refs, claim_id)
        for eid, mention_refs in mentions:
            shared = sorted(set(refs) & mention_refs)
            if shared:
                edge(eid, claim_id, "mentioned_in_claim", shared, claim_id)
        subject = next((eid for eid, mention_refs in mentions if nodes[eid].label == c["subject"] and set(refs) & mention_refs), None)
        if subject is None:
            subject = node("subject_" + digest([doc_id, c["subject"]])[:20], c["subject"], "entity", "object", refs,
                           identity="unresolved source subject; type not established")
        edge(subject, claim_id, "subject_of_claim", refs, claim_id)
        if c["location"]:
            location = node("location_" + digest([doc_id, c["location"]])[:20], c["location"], "entity", "location", refs,
                            identity="reported location")
            edge(event_id, location, "reported_at", refs, claim_id)
    return CaseGraph(nodes=list(nodes.values()), edges=list(edges.values()))
