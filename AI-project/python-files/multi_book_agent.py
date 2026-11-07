"""Priority-ordered greedy multi-book planner.

This is deliberately a greedy planner, not a globally optimal Travelling
Salesperson solver.  Books are handled in stable priority order and each leg
is computed with A* from the current location to the next book's shelf.
"""

from algorithms import astar

PRIORITY_ORDER = {"High": 1, "Medium": 2, "Low": 3}


def _book_summary(book, reason=None, **extra):
    item = {
        "id": book.get("id"),
        "title": book.get("title"),
        "author": book.get("author"),
        "shelf": book.get("shelf"),
        "priority": book.get("priority", "Low"),
    }
    if reason is not None:
        item["reason"] = reason
    item.update(extra)
    return item


def _miss_reason(graph, nodes_data, book, start, optimize_for, closed_sections, authorized):
    shelf = book["shelf"]
    if not book.get("available", True):
        return "Book unavailable"
    if shelf in closed_sections:
        return "Closed section"
    if nodes_data[shelf].get("restricted", False) and not authorized:
        return "Restricted access"

    if not authorized:
        diagnostic = astar(
            graph, nodes_data, start, shelf, optimize_for,
            closed_sections=closed_sections, authorized=True,
        )
        if diagnostic["found"]:
            return "Restricted access required"

    if closed_sections:
        diagnostic = astar(
            graph, nodes_data, start, shelf, optimize_for,
            closed_sections=[], authorized=authorized,
        )
        if diagnostic["found"]:
            return "Closed section blocks route"

    return "Unreachable shelf"


def plan_collection_route(
    graph,
    nodes_data,
    start_node,
    target_books,
    optimize_for="distance",
    time_limit=9999,
    authorized=False,
    closed_sections=None,
):
    """Plan a priority-ordered route for a collection.

    Returns a structured dictionary with collected books, missed books and
    per-leg costs.  The planner is greedy: it does not search all permutations.
    """
    closed_sections = set(closed_sections or [])
    limit = float(time_limit)
    pending_books = sorted(target_books, key=lambda b: PRIORITY_ORDER.get(b.get("priority", "Low"), 3))

    full_route = [start_node]
    total_cost = 0.0
    total_explored = 0
    current_location = start_node
    collected = []
    missed = []
    legs = []

    for book in pending_books:
        shelf = book["shelf"]

        if not book.get("available", True):
            missed.append(_book_summary(book, "Book unavailable"))
            continue

        if shelf in closed_sections:
            missed.append(_book_summary(book, "Closed section"))
            continue

        if nodes_data[shelf].get("restricted", False) and not authorized:
            missed.append(_book_summary(book, "Restricted access"))
            continue

        if shelf == current_location:
            collected.append(book)
            legs.append({
                "from": current_location,
                "to": shelf,
                "book_id": book.get("id"),
                "title": book.get("title"),
                "shelf": shelf,
                "priority": book.get("priority", "Low"),
                "cost": 0.0,
                "cumulative_cost": round(total_cost, 6),
                "remaining_limit": round(max(0.0, limit - total_cost), 6),
                "path": [current_location],
                "edge_count": 0,
                "explored_count": 0,
            })
            continue

        result = astar(
            graph,
            nodes_data,
            current_location,
            shelf,
            optimize_for=optimize_for,
            closed_sections=closed_sections,
            authorized=authorized,
        )
        total_explored += result["explored_count"]

        if not result["found"]:
            reason = _miss_reason(
                graph, nodes_data, book, current_location,
                optimize_for, closed_sections, authorized,
            )
            missed.append(_book_summary(book, reason))
            continue

        leg_cost = float(result["cost"])
        if total_cost + leg_cost > limit + 1e-9:
            missed.append(_book_summary(
                book,
                "Limit exceeded",
                required_cost=round(leg_cost, 6),
                remaining_limit=round(max(0.0, limit - total_cost), 6),
            ))
            continue

        path = result["path"]
        if path and path[0] == full_route[-1]:
            full_route.extend(path[1:])
        else:
            full_route.extend(path)

        total_cost = round(total_cost + leg_cost, 6)
        current_location = shelf
        collected.append(book)
        legs.append({
            "from": result["path"][0],
            "to": shelf,
            "book_id": book.get("id"),
            "title": book.get("title"),
            "shelf": shelf,
            "priority": book.get("priority", "Low"),
            "cost": round(leg_cost, 6),
            "cumulative_cost": total_cost,
            "remaining_limit": round(max(0.0, limit - total_cost), 6),
            "path": result["path"],
            "edge_count": result["edge_count"],
            "explored_count": result["explored_count"],
        })

    if not pending_books:
        message = "The collection is empty; there are no books to collect."
        found = True
    elif collected:
        message = (
            f"Planned {len(collected)} of {len(pending_books)} book(s) in priority order. "
            f"{len(missed)} book(s) could not be collected."
        )
        found = True
    else:
        message = (
            f"No requested book could be collected. {len(missed)} book(s) were missed "
            "because of availability, access, closure, reachability or the limit."
        )
        found = False

    return {
        "path": full_route,
        "total_cost": round(total_cost, 6),
        "limit": limit,
        "remaining_limit": round(max(0.0, limit - total_cost), 6),
        "explored_count": total_explored,
        "collected": collected,
        "missed": missed,
        "legs": legs,
        "found": found,
        "optimize": optimize_for,
        "message": message,
    }
