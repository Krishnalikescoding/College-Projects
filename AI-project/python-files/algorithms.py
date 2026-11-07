"""Classical graph-search algorithms used by the library agent.

All three searches return the same dictionary shape so the Flask API and the
tests do not need special cases for individual algorithms.
"""

import heapq
import math
from collections import deque


CROWD_MULTIPLIERS = {"Low": 1.0, "Medium": 1.25, "High": 1.6}


def heuristic(node_a, node_b, nodes_data):
    """Euclidean (straight-line) distance between two nodes."""
    x1, y1 = nodes_data[node_a]["x"], nodes_data[node_a]["y"]
    x2, y2 = nodes_data[node_b]["x"], nodes_data[node_b]["y"]
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def effective_edge_cost(graph, nodes_data, source, target, optimize_for="distance"):
    """Return the cost of walking one edge under the selected objective.

    Distance mode uses the hand-set edge distance.  Time mode uses the
    hand-set base time multiplied by the crowd multiplier of the *destination*
    node, because entering a crowded node slows the walker down.
    """
    edge = graph[source][target]
    if optimize_for == "distance":
        return float(edge["distance"])
    crowd = nodes_data[target].get("crowd", "Low")
    return float(edge["time"]) * CROWD_MULTIPLIERS.get(crowd, 1.0)


def path_cost(graph, nodes_data, path, optimize_for="distance"):
    if not path or len(path) < 2:
        return 0.0
    total = 0.0
    for source, target in zip(path, path[1:]):
        total += effective_edge_cost(graph, nodes_data, source, target, optimize_for)
    return round(total, 6)


def _format_number(value):
    return str(int(value)) if float(value).is_integer() else f"{value:.2f}"


def _result(path, cost, explored_count, visited, found, message):
    return {
        "path": path,
        "cost": None if cost is None else round(float(cost), 6),
        "edge_count": max(0, len(path) - 1) if path else 0,
        "explored_count": explored_count,
        "visited": list(visited),
        "found": bool(found),
        "message": message,
    }


def _blocked(node, nodes_data, closed_sections, authorized):
    if node in closed_sections:
        return True
    if nodes_data[node].get("restricted", False) and not authorized:
        return True
    return False


def _access_failure(nodes_data, start, goal, closed_sections, authorized):
    if start in closed_sections:
        return f"Start node '{start}' is closed."
    if nodes_data[start].get("restricted", False) and not authorized:
        return f"Start node '{start}' is restricted; enable authorization to enter it."
    if goal in closed_sections:
        return f"Target node '{goal}' is closed."
    if nodes_data[goal].get("restricted", False) and not authorized:
        return f"Target node '{goal}' is restricted; enable authorization to enter it."
    return None


def _success(algorithm, path, cost, visited, optimize_for):
    metric = "weighted distance" if optimize_for == "distance" else "weighted time"
    message = (
        f"{algorithm} found a route with {max(0, len(path) - 1)} edge(s) "
        f"and {metric} cost {_format_number(cost)}."
    )
    return _result(path, cost, len(visited), visited, True, message)


def _failure(algorithm, start, goal, visited, reason=None):
    message = f"{algorithm}: {reason}" if reason else (
        f"{algorithm} found no route from '{start}' to '{goal}' with the current "
        "restrictions and closed sections."
    )
    return _result([], None, len(visited), visited, False, message)


def bfs(graph, nodes_data, start, goal, optimize_for="distance", closed_sections=None, authorized=False):
    """Breadth-First Search: expands the path with the fewest edges."""
    closed_sections = set(closed_sections or [])
    reason = _access_failure(nodes_data, start, goal, closed_sections, authorized)
    if reason:
        return _failure("BFS", start, goal, [], reason)

    queue = deque([[start]])
    visited = set()
    visited_order = []

    while queue:
        path = queue.popleft()
        node = path[-1]
        if node in visited:
            continue
        visited.add(node)
        visited_order.append(node)

        if node == goal:
            cost = path_cost(graph, nodes_data, path, optimize_for)
            return _success("BFS", path, cost, visited_order, optimize_for)

        for neighbor in sorted(graph.get(node, {})):
            if neighbor in visited:
                continue
            if _blocked(neighbor, nodes_data, closed_sections, authorized):
                continue
            queue.append(path + [neighbor])

    return _failure("BFS", start, goal, visited_order)


def dfs(graph, nodes_data, start, goal, optimize_for="distance", closed_sections=None, authorized=False):
    """Depth-First Search with deterministic alphabetical neighbour order."""
    closed_sections = set(closed_sections or [])
    reason = _access_failure(nodes_data, start, goal, closed_sections, authorized)
    if reason:
        return _failure("DFS", start, goal, [], reason)

    stack = [[start]]
    visited = set()
    visited_order = []

    while stack:
        path = stack.pop()
        node = path[-1]
        if node in visited:
            continue
        visited.add(node)
        visited_order.append(node)

        if node == goal:
            cost = path_cost(graph, nodes_data, path, optimize_for)
            return _success("DFS", path, cost, visited_order, optimize_for)

        for neighbor in sorted(graph.get(node, {}), reverse=True):
            if neighbor in visited:
                continue
            if _blocked(neighbor, nodes_data, closed_sections, authorized):
                continue
            stack.append(path + [neighbor])

    return _failure("DFS", start, goal, visited_order)


def astar(graph, nodes_data, start, goal, optimize_for="distance", closed_sections=None, authorized=False):
    """A* search with f(n) = g(n) + h(n).

    The heuristic is Euclidean distance in distance mode and zero in time mode
    (uniform-cost search).  The closed list is returned in expansion order.
    """
    closed_sections = set(closed_sections or [])
    reason = _access_failure(nodes_data, start, goal, closed_sections, authorized)
    if reason:
        return _failure("A*", start, goal, [], reason)

    counter = 0
    frontier = [(0.0, 0.0, counter, start, [start])]
    best_g = {start: 0.0}
    closed = set()
    visited_order = []

    while frontier:
        _, g_cost, _, current, path = heapq.heappop(frontier)
        if current in closed:
            continue
        closed.add(current)
        visited_order.append(current)

        if current == goal:
            cost = round(g_cost, 6)
            return _success("A*", path, cost, visited_order, optimize_for)

        for neighbor in sorted(graph.get(current, {})):
            if neighbor in closed:
                continue
            if _blocked(neighbor, nodes_data, closed_sections, authorized):
                continue

            edge_cost = effective_edge_cost(graph, nodes_data, current, neighbor, optimize_for)
            new_g = g_cost + edge_cost
            if new_g >= best_g.get(neighbor, float("inf")):
                continue
            best_g[neighbor] = new_g
            h_cost = heuristic(neighbor, goal, nodes_data) if optimize_for == "distance" else 0.0
            counter += 1
            heapq.heappush(
                frontier,
                (new_g + h_cost, new_g, counter, neighbor, path + [neighbor]),
            )

    return _failure("A*", start, goal, visited_order)
