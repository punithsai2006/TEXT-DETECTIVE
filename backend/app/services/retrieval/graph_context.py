"""Bounded breadth-first traversal of sourced graph edges, never inferred facts."""
from collections import deque
from app.config import settings


def expand_graph(graph, seed_nodes, sources, max_hops=None):
    hops = max(0, min(2, settings.GRAPH_MAX_HOPS if max_hops is None else max_hops))
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    adjacency = {}
    for edge in graph.get("edges", []):
        if not set(edge.get("source_span_ids", [])) <= set(sources):
            continue
        adjacency.setdefault(edge["source"], []).append((edge["target"], edge))
        adjacency.setdefault(edge["target"], []).append((edge["source"], edge))
    visited = set(list(dict.fromkeys(n for n in seed_nodes if n in nodes))[:settings.GRAPH_MAX_NODES])
    queue = deque((n, [], 0) for n in sorted(visited))
    paths, refs = [], []
    while queue:
        current, path, depth = queue.popleft()
        if depth >= hops:
            continue
        for target, edge in adjacency.get(current, []):
            if target in visited or len(visited) >= settings.GRAPH_MAX_NODES:
                continue
            visited.add(target)
            step = {"source": current, "target": target, "relation": edge["relation"],
                    "source_span_ids": edge.get("source_span_ids", [])}
            trail = path + [step]
            paths.append({"node_ids": [trail[0]["source"]] + [s["target"] for s in trail],
                          "edges": trail, "source_span_ids": list(dict.fromkeys(s for x in trail for s in x["source_span_ids"]))})
            refs.extend(step["source_span_ids"])
            queue.append((target, trail, depth + 1))
    return {"paths": paths, "source_span_ids": list(dict.fromkeys(refs))[:settings.EVIDENCE_CONTEXT_LIMIT],
            "visited_nodes": len(visited), "max_hops": hops,
            "truncated": len(visited) >= settings.GRAPH_MAX_NODES}
