# Intelligent Library Search and Book Collection Agent

## Project Overview
This is a small Flask + HTML/CSS/JavaScript project for the AI subject. It searches for a book and finds a walking route from the library entrance to that book using BFS, DFS, or A*.

The library is a small weighted graph:

- Section and shelf locations are nodes.
- Each individual book is also a node connected to its section.
- Walking connections are edges with a positive distance and time.
- The entrance is the start state and the selected book node is the goal state.

No JavaScript framework (like React or Angular), database, login, or build step is used. Graph visualization is handled cleanly using Vis.js.

## Features
- Search books by title.
- Show the matching book, its section, and whether it is available.
- Add available books to a simple collection list; duplicates are prevented.
- Clear the collection.
- Use BFS, DFS, or A* to navigate from the entrance to the selected book node.
- **Advanced Multi-Book Planning:** Use a nearest-neighbor A* approach that respects book priorities (High, Medium, Low) and a user-defined **Time/Cost Limit**.
- Display the collection order, complete route, total distance, estimated time, and which books were missed if the time limit runs out.
- Display A* open and closed lists, explored nodes, and path costs.
- Support the four required conditions:
  - A closed section blocks paths through it.
  - Unavailable books cannot be collected.
  - A crowded section adds distance and time to connected paths.
  - Restricted shelves require authorization.
- Handle missing, unavailable, and unreachable books clearly.

## Search Algorithms
- **BFS:** FIFO queue. Finds the path with the fewest edges in an unweighted graph, but not necessarily the shortest weighted distance.
- **DFS:** LIFO stack. Explores deeply first and does not guarantee the shortest path.
- **A*:** Uses `f(n) = g(n) + h(n)`. The heuristic is Euclidean distance from the node coordinates. Edge costs are at least that distance, so the heuristic is admissible.
- **Multi-book planning:** Sorts the collection list by Priority (High > Medium > Low). Uses A* to find the cost to the next highest-priority book. If the cost fits within the user's Time Limit, it adds it to the route; otherwise, it marks the book as uncollected.

## Project Structure
```text
AI-project/
  requirements.txt               Python dependency (Flask)
  README.md                      Project documentation
  JSON/
    library_data.json            Graph nodes, edges, books, and coordinates
  python-files/
    app.py                       Flask server and JSON API
    algorithms.py                BFS, DFS, A* implementations
    multi_book_agent.py          Multi-book priority & time-limit route planner
    test_algorithm.py            Algorithm, data, and edge-case unit tests
    templates/
      index.html                 Page layout
    static/
      style.css                  UI styling
      script.js                  API calls and Vis.js graph visualization
```

## Book Data
Each book contains only the fields needed by the application:

```json
{"id": "101", "title": "Introduction to Algorithms", "author": "Cormen", "category": "CS", "shelf": "CS_Section", "available": true, "priority": "High"}
```

The `shelf` value connects the book to its parent graph node, ensuring routes finish exactly at the selected book's location.

## Setup and Run
1. Install Python 3.
2. Open your terminal in the `AI-project` folder and install Flask:
   ```bash
   pip install -r requirements.txt
   ```
3. Navigate to the Python files directory:
   ```bash
   cd python-files
   ```
4. Start the Flask application:
   ```bash
   python app.py
   ```
5. Open your web browser to [http://127.0.0.1:5000](http://127.0.0.1:5000).
6. Stop the server with `Ctrl+C`.

## How to Use
1. Type a book title and click **Find Book**.
2. Click **Add to Collection** for an available book.
3. Choose an algorithm (BFS, DFS, or A*) and an optimization metric (Distance or Time).
4. Enter a maximum **Time/Cost Limit** for multi-book routes.
5. Click **Navigate Single Book** to calculate the path to the most recently added book.
6. Click **Plan Multi-Book Route** to attempt to collect all books within the time limit based on their priority.
7. Observe the Vis.js graph dynamically highlight the calculated path in green.

## Running the Tests
```bash
cd python-files
python -m unittest test_algorithm.py -v
```
The tests cover BFS, DFS, A* optimality, closed sections, restricted access boundaries, and algorithm failure states.

## Viva Notes
- **States:** Library locations, including individual book nodes.
- **Actions:** Walk along a valid edge to a connected location.
- **Goal test:** The current node equals the selected book's shelf node.
- **Path cost:** Distance for A*; number of edges for BFS/DFS.
- **Conditions:** Closed and unauthorized restricted nodes are skipped during neighbor expansion in the search loops. Unavailable books are filtered out of collections.
- **Multi-Book Complexity:** Finding the absolute best multi-stop route is the Traveling Salesperson Problem ($O(n!)$). We use a highly efficient Greedy Nearest-Neighbor heuristic combined with Priority sorting to simulate real-world logical planning.