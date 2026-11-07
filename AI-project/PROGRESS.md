# Progress Log

## Status: Complete

Date: 2026-11-04

## Baseline Findings

- Original data: 9 nodes, 12 edges, 30 books.
- Original test suite: 5 tests, 1 pass, 4 errors.
- BFS and DFS web requests returned HTTP 500 because `app.py` unpacked three values from two-value results.
- A* no-route responses emitted `Infinity`, which is invalid JSON.
- The UI never sent `authorized`, had no closed-section controls, and used only the last-added book as the target.
- Search showed only the first matching book.
- Crowd data and penalties did not exist.
- Vis.js was loaded from a CDN.

## Completed Work

1. Expanded and validated the data set.
   - 18 nodes, 52 edges, 105 books.
   - 36 High, 32 Medium, 37 Low.
   - 6 unavailable books.
   - 2 restricted nodes.
   - Crowd levels on nodes; edge distances at least Euclidean length.

2. Reworked the search layer.
   - Shared result shape for BFS, DFS and A*.
   - Restrictions and closures enforced consistently.
   - Crowd-aware time cost.
   - No-route results use `found: false`, `cost: null`, `path: []`.
   - Visited order returned for replay and display.

3. Reworked the planner.
   - Stable High -> Medium -> Low ordering.
   - Greedy A* per leg.
   - Cumulative limit and per-leg details.
   - Explicit miss reasons: unavailable, restricted, closed, unreachable, closed route, limit exceeded.

4. Reworked the Flask API.
   - `/api/navigate`, `/api/compare`, `/api/multi_route`.
   - Startup validation.
   - JSON 400 errors for malformed bodies, unknown ids and invalid limits.
   - 404/405/415 JSON handling for API routes.

5. Rebuilt the UI.
   - Preserved the original light theme and color language.
   - Live multi-result search.
   - Priority collection with reorder/remove/clear.
   - Target selector, authorization toggle and closed-section controls.
   - Single-route results, comparison table, planner legs and limit meter.
   - Visited-order replay, toasts, legend and responsive layout.
   - Local Vis.js 9.1.9.

6. Added verification.
   - 73 unittest tests, all passing.
   - Python compilation check passed.
   - JavaScript syntax check passed.
   - Live API smoke tests passed.
   - 12 headless Chromium screenshots captured at 1440x1400.

7. Added documentation.
   - Upgraded README.
   - Changelog.
   - Outdated report claims list.
   - Screenshot index.
   - This progress log.

## Verification Commands and Results

```bash
cd python-files
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v
```

Result: `Ran 73 tests ... OK`.

```bash
python3 -m py_compile python-files/*.py
node --check python-files/static/script.js
```

Result: passed.

Live smoke tests:

- `GET /` -> HTTP 200.
- `GET /api/data` -> 18 nodes, 105 books.
- BFS to Physics -> 1 edge, cost 40.
- DFS to Physics -> 10 edges, cost 67.
- A* to Physics -> 2 edges, cost 12.
- Restricted archive without authorization -> no route with reason.
- Restricted archive with authorization -> route found.
- Closed `CS_Section` to AI -> reroute through Periodicals.
- Invalid target -> HTTP 400 JSON error.

## Screenshot Verification

Screenshots were captured with `tools/capture_screenshots.js` against the running Flask server and headless Chromium over the DevTools protocol. For each scenario the script printed the result badge, result text, search count, collection count, closed count and sidebar positions to confirm the expected content was present.

Files are in `deliverables/screenshots/`:

1. `01-main.png`
2. `02-search-multiple.png`
3. `03-collection-priorities.png`
4. `04-single-bfs.png`
5. `05-single-dfs.png`
6. `06-single-astar.png`
7. `07-compare.png`
8. `08-multi-plan-missed.png`
9. `09-restricted-off.png`
10. `10-restricted-on.png`
11. `11-closed-reroute.png`
12. `12-error.png`

## Packaging

- Deliverable archive: `AI-project-upgraded.zip`.
- Excluded from the archive: `.git`, nested `.git`, `__pycache__`, `*.pyc`, the archive itself.
- The original report `.docx`/`.pdf` are left unchanged and included as reference.
- No git commit was created.

## Notes

- The planner is greedy and does not solve the Travelling Salesperson Problem globally.
- Back-end routes target shelf nodes; book nodes are visual only.
- The UI shows visited/explored order, not a complete A* open-list trace.
- The report files describe the baseline and are not updated; use `OUTDATED_REPORT_CLAIMS.md`.
