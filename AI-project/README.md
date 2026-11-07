# Intelligent Library Search and Book Collection Agent

A Flask + HTML/CSS/JavaScript project for CSN-304 Artificial Intelligence. The application searches a library catalogue, finds walking routes with BFS, DFS or A*, compares the three algorithms, and plans a priority-ordered multi-book trip under a cost limit.

No JavaScript framework, database, login or build step is required. Vis.js is vendored locally, so the browser UI does not depend on a CDN.

## Features

- Live search across title, author, category, shelf id and shelf label.
- Add available books to a collection, reorder books inside a priority group, remove books and clear the list.
- Choose the navigation target from the collection instead of always using the last-added book.
- Navigate with BFS, DFS or A* using either distance or crowd-aware time.
- Compare BFS, DFS and A* against the same target in one request.
- Authorize restricted sections and temporarily close sections from the UI.
- Plan a High -> Medium -> Low collection with a cumulative cost limit.
- Show route steps, weighted cost, edge count, explored nodes, visited order, comparison table, plan legs and missed-book reasons.
- Replay the visited order on the graph.
- Return consistent JSON errors instead of HTTP 500 pages or `Infinity`.

## Library Data

The upgraded knowledge base contains:

- 18 graph nodes (sections and facilities)
- 52 undirected edges
- 105 books
- High 36 / Medium 32 / Low 37 priorities
- 6 unavailable books
- 2 restricted nodes: `Restricted_Archive`, `Research_Archive`
- Crowd levels: Low 11 / Medium 5 / High 2 nodes

Each book remains a visual node attached to its shelf in the browser. Back-end navigation still ends at the book's shelf node.

The application validates the data at startup with `python-files/data_validation.py`. Invalid coordinates, edges shorter than their Euclidean length, duplicate ids, missing fields, bad priorities, bad crowd levels and disconnected graphs stop the application with a readable error.

## Algorithms

- **BFS:** FIFO queue; minimises the number of edges, not weighted cost.
- **DFS:** deterministic alphabetical depth-first search; does not guarantee a shortest route.
- **A*:** `f(n) = g(n) + h(n)`. The heuristic is Euclidean distance in distance mode. Time mode uses a zero heuristic (uniform-cost search).
- **Multi-book planner:** stable priority ordering, greedy A* per leg, cumulative limit and per-leg reasons. It is not a globally optimal Travelling Salesperson solver.

Cost model:

- Distance mode uses the hand-set edge distance.
- Time mode uses the hand-set edge time multiplied by the destination node's crowd multiplier: Low `1.0`, Medium `1.25`, High `1.6`.
- Edge distances are at least their Euclidean length, so the A* distance heuristic is admissible.

All three search functions return the same shape:

```json
{
  "path": ["Entrance", "Math_Section", "Physics_Section"],
  "cost": 12.0,
  "edge_count": 2,
  "explored_count": 5,
  "visited": ["Entrance", "CS_Section", "..."],
  "found": true,
  "message": "A* found a route with 2 edge(s) and weighted distance cost 12."
}
```

No route uses `found: false`, `cost: null`, `path: []` and a readable message. It never emits `Infinity` or `NaN`.

## API

| Route | Method | Main fields | Purpose |
| --- | --- | --- | --- |
| `/` | GET | - | Serve the UI |
| `/api/data` | GET | - | Nodes, edges, books and data statistics |
| `/api/navigate` | POST | `target`, `algorithm`, `optimize`, `start`, `authorized`, `closed_sections` | Run one algorithm |
| `/api/compare` | POST | `target`, `optimize`, `start`, `authorized`, `closed_sections` | Run BFS, DFS and A* |
| `/api/multi_route` | POST | `books`, `time_limit`, `optimize`, `start`, `authorized`, `closed_sections` | Run the planner |

`target` and `start` are node ids such as `Physics_Section` or `Entrance`. The UI converts a selected book to its shelf node before calling the API. `time_limit` is required, finite and non-negative. API validation failures return HTTP 400 with JSON containing `error` and `message`.

## Project Structure

```text
AI-project/
  README.md
  CHANGELOG.md
  OUTDATED_REPORT_CLAIMS.md
  PROGRESS.md
  requirements.txt
  JSON/
    library_data.json
  python-files/
    app.py
    algorithms.py
    data_validation.py
    multi_book_agent.py
    test_algorithm.py
    test_api.py
    test_data.py
    test_planner.py
    templates/
      index.html
    static/
      style.css
      script.js
      vendor/
        vis-network-9.1.9.min.js
  tools/
    capture_screenshots.js
  deliverables/
    README.md
    screenshots/
      01-main.png ... 12-error.png
```

## Setup and Run

```bash
pip install -r requirements.txt
cd python-files
python app.py
```

Open <http://127.0.0.1:5000>. Stop the server with `Ctrl+C`.

Tested with Python 3.14.8 and Flask 3.0.0.

## How to Use

1. Type a title, author, category or shelf in Search. Multiple matches appear live.
2. Add an available book to the Collection. Unavailable or duplicate books cannot be added.
3. Pick the collection book to navigate to, then choose an algorithm and metric.
4. Toggle **Authorized access** when entering a restricted section.
5. Open **Closed sections** to close a section and test rerouting.
6. Click **Navigate** for one book or **Compare BFS / DFS / A*** for all three.
7. For a multi-book trip, set a cost limit and click **Plan multi-book route**.
8. Use the graph controls to fit, replay visited order or inspect the legend.

## Tests

From the `python-files` directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v
```

The suite has 73 tests covering data validation, BFS/DFS/A*, restrictions, closures, crowd-aware time, no-route responses, planner priority/limits/reasons, API validation and JSON errors. Current result: **73 tests, OK**.

## Screenshots

Screenshots are in `deliverables/screenshots/`, with a description table in `deliverables/README.md`. They were captured at 1440x1400 from the running application using `tools/capture_screenshots.js` and headless Chromium over the DevTools protocol.

To recapture them, start Flask first, then start Chromium with a debugging port:

```bash
chromium-browser --headless=new --no-sandbox --disable-gpu \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/library-chrome-profile about:blank

node tools/capture_screenshots.js
```

The script writes the 12 PNG files and prints a DOM summary for each scenario.

## Notes and Limitations

- The planner is priority-ordered and greedy; it does not search all book permutations.
- Books are graph nodes in the visualisation; the back-end search graph contains shelf and facility nodes.
- The visited list is expansion order, not a full A* open-list trace.
- The submitted report describes the baseline defects. It was intentionally not edited; see `OUTDATED_REPORT_CLAIMS.md` for claims that no longer match the upgraded code.
