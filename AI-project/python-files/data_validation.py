"""Validation for the library knowledge base.

The application refuses to start with malformed data instead of silently
repairing it or failing later inside a search.
"""

import math


class LibraryDataError(ValueError):
    """Raised when library_data.json violates the expected schema."""


VALID_PRIORITIES = {"High", "Medium", "Low"}
VALID_CROWD_LEVELS = {"Low", "Medium", "High"}


def _require(condition, message):
    if not condition:
        raise LibraryDataError(message)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def build_adjacency(nodes, edges):
    """Build an undirected adjacency map from the raw edge list."""
    adjacency = {node_id: set() for node_id in nodes}
    for edge in edges:
        adjacency[edge["from"]].add(edge["to"])
        adjacency[edge["to"]].add(edge["from"])
    return adjacency


def validate_library_data(data):
    """Validate the full knowledge base and return a small summary.

    Raises LibraryDataError with a readable message on the first problem.
    """
    _require(isinstance(data, dict), "Library data must be a JSON object.")
    nodes = data.get("nodes")
    edges = data.get("edges")
    books = data.get("books")

    _require(isinstance(nodes, dict) and nodes, "Field 'nodes' must be a non-empty object.")
    _require(isinstance(edges, list), "Field 'edges' must be a list.")
    _require(isinstance(books, list), "Field 'books' must be a list.")

    for node_id, node in nodes.items():
        _require(isinstance(node_id, str) and node_id.strip(), "Every node key must be a non-empty string.")
        _require(isinstance(node, dict), f"Node '{node_id}' must be an object.")
        _require(node.get("id") == node_id, f"Node '{node_id}' must contain a matching 'id' field.")
        _require(isinstance(node.get("label"), str) and node["label"].strip(),
                 f"Node '{node_id}' must contain a non-empty 'label' field.")
        _require(_is_number(node.get("x")), f"Node '{node_id}' has an invalid 'x' coordinate.")
        _require(_is_number(node.get("y")), f"Node '{node_id}' has an invalid 'y' coordinate.")
        _require(isinstance(node.get("restricted"), bool), f"Node '{node_id}' must have a boolean 'restricted' field.")
        _require(node.get("crowd") in VALID_CROWD_LEVELS,
                 f"Node '{node_id}' has invalid crowd level {node.get('crowd')!r}; use Low, Medium or High.")

    seen_edges = set()
    for index, edge in enumerate(edges, start=1):
        _require(isinstance(edge, dict), f"Edge #{index} must be an object.")
        start = edge.get("from")
        goal = edge.get("to")
        _require(start in nodes, f"Edge #{index} references unknown source node {start!r}.")
        _require(goal in nodes, f"Edge #{index} references unknown target node {goal!r}.")
        _require(start != goal, f"Edge #{index} is a self-loop on node '{start}'.")
        pair = frozenset((start, goal))
        _require(pair not in seen_edges,
                 f"Edge #{index} duplicates an existing undirected edge between '{start}' and '{goal}'.")
        seen_edges.add(pair)

        distance = edge.get("distance")
        travel_time = edge.get("time")
        _require(_is_number(distance) and distance > 0,
                 f"Edge #{index} ({start} -> {goal}) has an invalid positive 'distance'.")
        _require(_is_number(travel_time) and travel_time > 0,
                 f"Edge #{index} ({start} -> {goal}) has an invalid positive 'time'.")

        node_a = nodes[start]
        node_b = nodes[goal]
        straight_line = math.hypot(node_b["x"] - node_a["x"], node_b["y"] - node_a["y"])
        _require(distance + 1e-9 >= straight_line,
                 f"Edge #{index} ({start} -> {goal}) has distance {distance}, which is shorter than "
                 f"its Euclidean length {straight_line:.3f}; the A* heuristic would not be admissible.")

    seen_book_ids = set()
    for index, book in enumerate(books, start=1):
        _require(isinstance(book, dict), f"Book #{index} must be an object.")
        book_id = book.get("id")
        _require(isinstance(book_id, str) and book_id.strip(), f"Book #{index} must have a non-empty string 'id'.")
        _require(book_id not in seen_book_ids, f"Duplicate book id '{book_id}'.")
        seen_book_ids.add(book_id)
        for field in ("title", "author", "category"):
            _require(isinstance(book.get(field), str) and book[field].strip(),
                     f"Book '{book_id}' must have a non-empty '{field}' field.")
        _require(book.get("shelf") in nodes,
                 f"Book '{book_id}' references unknown shelf {book.get('shelf')!r}.")
        _require(isinstance(book.get("available"), bool),
                 f"Book '{book_id}' must have a boolean 'available' field.")
        _require(book.get("priority") in VALID_PRIORITIES,
                 f"Book '{book_id}' has invalid priority {book.get('priority')!r}; use High, Medium or Low.")

    adjacency = build_adjacency(nodes, edges)
    start = next(iter(nodes))
    visited = {start}
    stack = [start]
    while stack:
        current = stack.pop()
        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)
    missing = sorted(set(nodes) - visited)
    _require(not missing,
             f"Graph is disconnected when restrictions and closures are ignored; unreachable nodes: {', '.join(missing)}.")

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "book_count": len(books),
        "restricted_nodes": sorted(node_id for node_id, node in nodes.items() if node["restricted"]),
        "crowd_levels": {level: sum(1 for n in nodes.values() if n["crowd"] == level) for level in VALID_CROWD_LEVELS},
        "priorities": {level: sum(1 for b in books if b["priority"] == level) for level in VALID_PRIORITIES},
        "unavailable_books": sum(1 for b in books if not b["available"]),
    }
