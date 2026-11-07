# Changelog

## Upgraded project - 2026-11-04

### Added

- Data validation module that rejects malformed nodes, edges, books, priorities, crowd levels and disconnected graphs at startup.
- Real crowd-aware time costs using destination-node multipliers (`Low 1.0`, `Medium 1.25`, `High 1.6`).
- Authorization and closed-section support for BFS, DFS and A*.
- `/api/compare` endpoint for BFS / DFS / A* comparison.
- Consistent API validation errors with HTTP 400 and JSON `error` / `message` bodies.
- Multi-book planner response with collected books, missed books, reasons, per-leg paths, cumulative cost and remaining limit.
- Target selector so single-book navigation is no longer tied to the last-added book.
- Live multi-result search across title, author, category, shelf id and shelf label.
- Collection reordering inside priority groups, removal and clear-list action.
- Restricted-access toggle, closed-section checkboxes and closed-section count in the UI.
- Route summary, step-by-step route, visited order, comparison table, plan legs, limit meter and replay control.
- Pinned local Vis.js 9.1.9 file so the UI no longer needs a CDN.
- Test coverage for validation, all three algorithms, no-route responses, crowd-aware time, restrictions, closures, planner priority and limits, API validation and JSON errors.
- Screenshot capture tool and 12 deliverable screenshots.
- Documentation for the upgraded code and for outdated report claims.

### Changed

- Expanded data from 9 nodes / 12 edges / 30 books to 18 nodes / 52 edges / 105 books.
- Priorities now include 36 High, 32 Medium and 37 Low books.
- Data now includes 6 unavailable books and 2 restricted nodes.
- Search now returns all matches instead of only the first match.
- Navigation target is selected from the collection instead of using the last-added book.
- BFS, DFS and A* now return the same dictionary shape with `path`, `cost`, `edge_count`, `explored_count`, `visited`, `found` and `message`.
- Unreachable routes now return `found: false`, `cost: null`, `path: []` and a message instead of `Infinity`.
- Time-mode A* uses a zero heuristic as uniform-cost search; distance-mode A* uses the Euclidean heuristic.
- The planner now returns structured per-leg data and stable ordering inside priority groups.
- The UI keeps the original light theme while improving layout, responsiveness and controls.
- The README now documents the upgraded application, API and test procedure.

### Fixed

- BFS and DFS HTTP 500 errors from incompatible return values.
- `Infinity` / invalid JSON for no-route responses.
- HTTP 500 for unknown targets and invalid bodies; these now return JSON 400 responses.
- Restricted access was enforced only by A* and was unreachable from the UI.
- Closed sections existed only as an unused parameter.
- Crowded sections had no data or cost effect.
- Search returned only the first match.
- Single-book mode always used the last-added book.
- Unavailable and restricted books were not clearly explained in planner results.
- The UI did not expose authorization, closures or comparison.
- Vis.js depended on an external CDN.

### Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v` from `python-files`: **73 tests, OK**.
- `python3 -m py_compile` for all Python files: passed.
- `node --check python-files/static/script.js`: passed.
- `/` returns HTTP 200 and `/api/data` returns 18 nodes / 105 books.
- Headless Chromium screenshots cover main page, multi-result search, priority collection, BFS, DFS, A*, comparison, a partially planned multi-book route, restricted access off/on, closed-section reroute and a real API error.

### Report Status

- `Intelligent_Library_Search_Project_Report.docx` and `.pdf` were **not modified**.
- The report describes the baseline submission, so many of its defect statements are now outdated.
- See `OUTDATED_REPORT_CLAIMS.md` for the itemized old-versus-current list.

### Known limitations

- The planner is greedy and priority-ordered; it does not solve the Travelling Salesperson Problem globally.
- Books are visual nodes attached to shelves; back-end routes target shelf nodes.
- The UI displays visited/explored order, not a complete A* open-list trace.
- The application is a local Flask development app with no authentication, database or deployment setup.
