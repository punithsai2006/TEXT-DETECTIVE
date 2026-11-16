"""Original-passage search remains available without report synthesis or an LLM."""
from datetime import datetime
import json
from app.models.schemas import EvidenceItem


def search_case(service, case_id, request):
    if request.mode not in {"hybrid", "exact"}:
        raise ValueError("Search mode must be hybrid or exact")
    if not request.query.strip() or len(request.query) > 2000:
        raise ValueError("Enter a query between 1 and 2000 characters")
    for value in (request.date_from, request.date_to):
        if value:
            datetime.strptime(value, "%Y-%m-%d")
    if request.date_from and request.date_to and request.date_from > request.date_to:
        raise ValueError("Start date must not follow end date")
    documents = service.documents(case_id)
    sources = service.sources(case_id)
    docs = {d.document_id: d for d in documents}
    run = service.load(case_id)
    claims = run["claims"] if run and not run["stale"] else []
    eligible = set(sources)
    if request.document_ids is not None:
        eligible &= {s for s in sources if sources[s]["document_id"] in request.document_ids}
    if request.evidence_type:
        eligible &= {s for s in sources if docs[sources[s]["document_id"]].document_type.value == request.evidence_type}
    if request.entity:
        eligible &= {s for c in claims if request.entity.casefold() in {c["subject"].casefold(), c["object"].casefold(), (c["location"] or "").casefold()} for s in c["source_span_ids"]}
    if request.date_from or request.date_to:
        eligible &= {s for c in claims if c["event_start"] and len(c["event_start"]) >= 10
                     and (not request.date_from or c["event_start"][:10] >= request.date_from)
                     and (not request.date_to or c["event_start"][:10] <= request.date_to) for s in c["source_span_ids"]}
    limit = min(max(request.top_k, 1), 50)
    if request.mode == "exact":
        matches = [EvidenceItem(evidence_id="evid_" + s, case_id=case_id, document_id=sources[s]["document_id"],
                   document_name=sources[s]["filename"], document_type=docs[sources[s]["document_id"]].document_type,
                   chunk_id=s, text=sources[s]["quote"], page_number=sources[s]["page_number"],
                   char_start=sources[s]["char_start"], char_end=sources[s]["char_end"],
                   score=1, retrieval_method="exact_phrase") for s in sources
                   if s in eligible and request.query.casefold() in sources[s]["quote"].casefold()][:limit]
    else:
        service._index(case_id, documents)
        model_used = json.loads(service.retriever._index_path(case_id).read_text(encoding="utf-8"))["model_used"]
        matches = [m for m in service.retriever.search(case_id, request.query, top_k=max(len(sources), limit),
                   threshold=request.threshold or 0) if m.chunk_id in eligible][:limit]
        for match in matches:
            match.retrieval_method = "lexical_tfidf_keyword_rrf" if model_used.startswith("lexical") else "semantic_and_keyword_rrf"
    for match in matches:
        match.page_number = sources[match.chunk_id]["page_number"]
        match.paragraph = sources[match.chunk_id]["paragraph"]
        match.related_event_ids = ["event_" + c["claim_id"] for c in claims if match.chunk_id in c["source_span_ids"]]
        match.related_graph_node_ids = [c["claim_id"] for c in claims if match.chunk_id in c["source_span_ids"]]
        match.related_contradiction_ids = [f["id"] for f in (run["comparisons"] if run and not run["stale"] else []) if match.chunk_id in f["source_a_ids"] + f["source_b_ids"]]
    return matches
