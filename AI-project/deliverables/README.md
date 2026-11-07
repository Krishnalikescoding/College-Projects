# Deliverables

## Screenshots

All screenshots are 1440x1400 PNG files captured from the running Flask application with headless Chromium. The scenario is driven by `../tools/capture_screenshots.js`.

| File | What it demonstrates |
| --- | --- |
| `screenshots/01-main.png` | Main page, original light theme, local Vis.js graph, 18 section nodes and 105 visual book nodes. |
| `screenshots/02-search-multiple.png` | Live search for "physics" returning 9 matches instead of only the first match. |
| `screenshots/03-collection-priorities.png` | Collection with High, Medium and Low books, reorder/remove controls and priority badges. |
| `screenshots/04-single-bfs.png` | BFS to the Physics shelf: 1 edge, weighted distance 40. |
| `screenshots/05-single-dfs.png` | DFS to the Physics shelf: 10 edges, weighted distance 67. |
| `screenshots/06-single-astar.png` | A* to the Physics shelf: 2 edges, weighted distance 12. |
| `screenshots/07-compare.png` | BFS / DFS / A* comparison table showing edge count, weighted cost and explored nodes. |
| `screenshots/08-multi-plan-missed.png` | Partially planned multi-book route with limit meter, collected book, missed books and reasons. |
| `screenshots/09-restricted-off.png` | Restricted archive with authorization disabled: no route, explicit reason. |
| `screenshots/10-restricted-on.png` | Same restricted archive with authorization enabled: route found. |
| `screenshots/11-closed-reroute.png` | `CS_Section` closed; A* reroutes through Periodicals to the AI shelf. |
| `screenshots/12-error.png` | Real API validation error rendered in the Results panel and toast. |

## Reproduction

Start the Flask app:

```bash
cd python-files
python app.py
```

Start headless Chromium with remote debugging:

```bash
chromium-browser --headless=new --no-sandbox --disable-gpu \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/library-chrome-profile about:blank
```

Capture the screenshots from the project root:

```bash
node tools/capture_screenshots.js
```

The script overwrites the PNG files and prints a DOM summary for each scenario.
