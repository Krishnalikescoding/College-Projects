# Outdated Report Claims

The submitted `Intelligent_Library_Search_Project_Report.docx` and `.pdf` describe the baseline project before the upgrade. They were intentionally **not edited**. This file lists the report statements that no longer describe the current code.

| # | Report claim (location) | Current reality |
| --- | --- | --- |
| 1 | The back-end graph has 9 nodes (Table 10, Section 3.2). | The back-end graph has 18 nodes and 52 edges. |
| 2 | The supplied data has 30 books (Section 2.3.4). | The supplied data has 105 books. |
| 3 | All 30 books are available (Section 2.3.4). | 99 books are available and 6 are unavailable. |
| 4 | Priorities are 14 High and 16 Low, with no Medium books (Section 2.3.4). | Priorities are 36 High, 32 Medium and 37 Low. |
| 5 | Only `Restricted_Archive` is restricted (Section 3.2.2). | `Restricted_Archive` and `Research_Archive` are restricted. |
| 6 | There is no crowd data or crowd penalty (Table 10, Table 23). | Nodes have `crowd` levels and time mode applies Low 1.0, Medium 1.25 and High 1.6 multipliers. |
| 7 | BFS and DFS return HTTP 500 through the API (Table 5, Table 10, Section 4.3, Table 23). | BFS, DFS and A* all work through their single endpoint and in comparison; tests cover them. |
| 8 | Only A* can be demonstrated through the interface (Section 4.3). | BFS, DFS and A* can all be selected and compared in the UI. |
| 9 | An unreachable target returns `cost: Infinity`, producing invalid JSON and a browser parse failure (Table 5, Table 10, Section 4.3, Table 23). | No route returns `found: false`, `cost: null`, `path: []` and a readable message. No `Infinity` is emitted. |
| 10 | An unknown target returns HTTP 500 (Table 5, Table 23). | Unknown targets return HTTP 400 with JSON `error` and `message`. |
| 11 | A null time limit returns HTTP 500 (Table 5, Table 23). | Missing, null, non-numeric, infinite or negative limits return HTTP 400 with JSON `error` and `message`. |
| 12 | The app exposes one page route and three JSON routes (Section 2.3.5). | The app exposes one page route and four JSON routes: `/api/data`, `/api/navigate`, `/api/compare` and `/api/multi_route`. |
| 13 | Restricted access is enforced only by A*, and the UI never sends `authorized` (Table 10, Table 23). | BFS, DFS, A* and the planner enforce restrictions; the UI has an authorization toggle that is sent with every search. |
| 14 | Closed sections are accepted by functions but the API passes an empty list and there is no UI control (Table 10, Table 23). | Closed sections are accepted by the API, selectable in the UI and applied to all three algorithms and the planner. |
| 15 | Search returns only the first match (Table 10, Table 23). | Search returns all matches live across title, author, category, shelf id and shelf label. |
| 16 | Single-book mode uses only the last-added book (Table 23, defect 11). | The collection has a target selector, so any collected book can be navigated to. |
| 17 | BFS and DFS ignore restricted nodes and authorization (Table 23, defect 4). | All algorithms share the same restriction check. |
| 18 | The unit suite has 5 tests, with 1 pass and 4 errors (Table 10, Section 4.7). | The upgraded suite has 73 tests and all pass. It covers algorithms, data validation, planner behavior, API validation and no-route handling. |
| 19 | The README says books are graph nodes, but only the browser draws them (Table 23, defect 7). | This remains partially true and is documented honestly: books are visual nodes attached to shelves; back-end routes target shelf nodes. The stale part is the old 9-node count. |
| 20 | Open and closed lists are only partially displayed (Table 10, Table 23, defects 8). | The UI now shows visited/explored order on the graph and in results, but it still does not show a complete A* open-list trace. |
| 21 | The README documents features the code does not implement (Section 3.2.3). | The README now describes the actual upgraded behavior, API and limitations. |
| 22 | The app depends on a Vis.js CDN and an internet connection (Section 2.3.6). | Vis.js 9.1.9 is vendored locally under `python-files/static/vendor/`. |
| 23 | The project has no crowd-aware metric, no comparison endpoint and no planner details beyond titles (Section 3.2, Table 5). | The API and UI now include crowd-aware time, a comparison endpoint and structured planner legs, reasons and limit details. |

## Report Content That Remains Accurate

- The project is a goal-based agent that searches a weighted graph from the entrance to a book's shelf.
- BFS minimises edge count, DFS does not guarantee a shortest route, and A* uses an admissible Euclidean heuristic in distance mode.
- The planner is greedy and priority-ordered, not a globally optimal tour.
- The application is a local Flask development project without a database, login or deployment setup.
- The report's baseline defect analysis remains useful as a record of the original submission.
