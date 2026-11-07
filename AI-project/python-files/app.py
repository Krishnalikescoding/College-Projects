import json
import math
import os

from flask import Flask, jsonify, make_response, render_template, request

from algorithms import astar, bfs, dfs
from data_validation import LibraryDataError, validate_library_data
from multi_book_agent import plan_collection_route

app = Flask(__name__)
app.json.sort_keys = False
app.json.ensure_ascii = False

BASE_DIR = os.path.dirname(__file__)
JSON_PATH = os.path.join(BASE_DIR, "..", "JSON", "library_data.json")

with open(JSON_PATH, "r", encoding="utf-8") as handle:
    library_data = json.load(handle)

try:
    library_stats = validate_library_data(library_data)
except LibraryDataError as exc:
    raise RuntimeError(f"Invalid library data: {exc}") from exc

NODES = library_data["nodes"]
BOOKS = library_data["books"]
BOOKS_BY_ID = {book["id"]: book for book in BOOKS}
VALID_ALGORITHMS = {"BFS", "DFS", "A*"}
VALID_OPTIMIZATIONS = {"distance", "time"}


def build_graph(data):
    graph = {node_id: {} for node_id in data["nodes"]}
    for edge in data["edges"]:
        source, target = edge["from"], edge["to"]
        costs = {"distance": edge["distance"], "time": edge["time"]}
        graph[source][target] = costs
        graph[target][source] = costs
    return graph


GRAPH = build_graph(library_data)


class ApiValidationError(ValueError):
    pass


@app.errorhandler(ApiValidationError)
def handle_validation_error(exc):
    return jsonify({"error": str(exc), "message": str(exc)}), 400


@app.errorhandler(400)
def handle_bad_request(exc):
    return jsonify({
        "error": "Bad request",
        "message": getattr(exc, "description", "The request could not be understood."),
    }), 400


@app.errorhandler(404)
def handle_not_found(exc):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found", "message": f"No API route matches {request.path}."}), 404
    return exc


@app.errorhandler(405)
def handle_method_not_allowed(exc):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Method not allowed", "message": "Use the documented HTTP method for this route."}), 405
    return exc


@app.errorhandler(415)
def handle_unsupported_media_type(exc):
    return jsonify({
        "error": "Unsupported media type",
        "message": "Send an application/json request body.",
    }), 415


def get_json_object():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiValidationError("Request body must be a JSON object.")
    return payload


def validate_node_id(value, field_name):
    if not isinstance(value, str) or value not in NODES:
        raise ApiValidationError(f"{field_name} must be a known node id; received {value!r}.")
    return value


def validate_start(payload):
    return validate_node_id(payload.get("start", "Entrance"), "start")


def validate_target(payload):
    if "target" not in payload:
        raise ApiValidationError("target is required.")
    return validate_node_id(payload.get("target"), "target")


def validate_algorithm(payload):
    algorithm = payload.get("algorithm", "A*")
    if algorithm not in VALID_ALGORITHMS:
        raise ApiValidationError(
            f"algorithm must be one of {', '.join(sorted(VALID_ALGORITHMS))}; received {algorithm!r}."
        )
    return algorithm


def validate_optimize(payload):
    optimize = payload.get("optimize", "distance")
    if optimize not in VALID_OPTIMIZATIONS:
        raise ApiValidationError(
            f"optimize must be 'distance' or 'time'; received {optimize!r}."
        )
    return optimize


def validate_authorized(payload):
    authorized = payload.get("authorized", False)
    if not isinstance(authorized, bool):
        raise ApiValidationError("authorized must be a boolean value (true or false).")
    return authorized


def validate_closed_sections(payload):
    closed_sections = payload.get("closed_sections", [])
    if not isinstance(closed_sections, list):
        raise ApiValidationError("closed_sections must be a list of node ids.")
    validated = []
    for item in closed_sections:
        if not isinstance(item, str) or item not in NODES:
            raise ApiValidationError(f"closed_sections contains unknown node id {item!r}.")
        if item not in validated:
            validated.append(item)
    return validated


def validate_time_limit(payload):
    if "time_limit" not in payload:
        raise ApiValidationError("time_limit is required and must be a non-negative number.")
    limit = payload.get("time_limit")
    if isinstance(limit, bool) or not isinstance(limit, (int, float)) or not math.isfinite(limit):
        raise ApiValidationError("time_limit must be a finite non-negative number.")
    if limit < 0:
        raise ApiValidationError("time_limit cannot be negative.")
    return float(limit)


def validate_books(payload):
    books = payload.get("books")
    if not isinstance(books, list):
        raise ApiValidationError("books must be a list of book objects or book ids.")
    canonical = []
    seen = set()
    for index, item in enumerate(books, start=1):
        if isinstance(item, dict):
            book_id = item.get("id")
        else:
            book_id = item
        if not isinstance(book_id, str) or book_id not in BOOKS_BY_ID:
            raise ApiValidationError(f"books entry #{index} has unknown book id {book_id!r}.")
        if book_id in seen:
            raise ApiValidationError(f"Duplicate book id '{book_id}' in books.")
        seen.add(book_id)
        canonical.append(BOOKS_BY_ID[book_id])
    return canonical


def run_search(algorithm, start, target, optimize, closed_sections, authorized):
    if algorithm == "BFS":
        return bfs(GRAPH, NODES, start, target, optimize, closed_sections, authorized)
    if algorithm == "DFS":
        return dfs(GRAPH, NODES, start, target, optimize, closed_sections, authorized)
    return astar(GRAPH, NODES, start, target, optimize, closed_sections, authorized)


def search_context(payload):
    return {
        "start": validate_start(payload),
        "target": validate_target(payload),
        "optimize": validate_optimize(payload),
        "closed_sections": validate_closed_sections(payload),
        "authorized": validate_authorized(payload),
    }


@app.route("/")
def index():
    response = make_response(render_template("index.html"))
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/api/data", methods=["GET"])
def get_data():
    payload = {
        "nodes": NODES,
        "edges": library_data["edges"],
        "books": BOOKS,
        "stats": library_stats,
    }
    return jsonify(payload)


@app.route("/api/navigate", methods=["POST"])
def navigate():
    payload = get_json_object()
    algorithm = validate_algorithm(payload)
    context = search_context(payload)
    result = run_search(
        algorithm,
        context["start"],
        context["target"],
        context["optimize"],
        context["closed_sections"],
        context["authorized"],
    )
    result.update({
        "algorithm": algorithm,
        "optimize": context["optimize"],
        "start": context["start"],
        "target": context["target"],
        "closed_sections": context["closed_sections"],
        "authorized": context["authorized"],
    })
    return jsonify(result)


@app.route("/api/compare", methods=["POST"])
def compare():
    payload = get_json_object()
    context = search_context(payload)
    results = []
    for algorithm in ("BFS", "DFS", "A*"):
        result = run_search(
            algorithm,
            context["start"],
            context["target"],
            context["optimize"],
            context["closed_sections"],
            context["authorized"],
        )
        result["algorithm"] = algorithm
        results.append(result)
    return jsonify({
        "results": results,
        "optimize": context["optimize"],
        "start": context["start"],
        "target": context["target"],
        "closed_sections": context["closed_sections"],
        "authorized": context["authorized"],
    })


@app.route("/api/multi_route", methods=["POST"])
def multi_route():
    payload = get_json_object()
    start = validate_start(payload)
    optimize = validate_optimize(payload)
    authorized = validate_authorized(payload)
    closed_sections = validate_closed_sections(payload)
    time_limit = validate_time_limit(payload)
    books = validate_books(payload)

    result = plan_collection_route(
        GRAPH,
        NODES,
        start,
        books,
        optimize_for=optimize,
        time_limit=time_limit,
        authorized=authorized,
        closed_sections=closed_sections,
    )
    result.update({
        "start": start,
        "optimize": optimize,
        "authorized": authorized,
        "closed_sections": closed_sections,
        "requested_books": [book["id"] for book in books],
    })
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
