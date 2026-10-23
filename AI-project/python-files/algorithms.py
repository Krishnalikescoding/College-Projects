import heapq
import math

def heuristic(node_a, node_b, nodes_data):
    """Calculates the Euclidean (straight-line) distance between two nodes."""
    x1, y1 = nodes_data[node_a]['x'], nodes_data[node_a]['y']
    x2, y2 = nodes_data[node_b]['x'], nodes_data[node_b]['y']
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def bfs(graph, start, goal, closed_sections, authorized):
    """Breadth-First Search (Finds path with fewest edges)."""
    queue = [[start]]
    visited = set()
    explored_count = 0

    while queue:
        path = queue.pop(0)
        node = path[-1]

        if node == goal:
            return path, explored_count

        if node not in visited:
            visited.add(node)
            explored_count += 1
            for neighbor in graph.get(node, {}):
                if neighbor not in closed_sections:
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
    return None, explored_count

def dfs(graph, start, goal, closed_sections, authorized):
    """Depth-First Search (Explores deep before backtracking)."""
    stack = [[start]]
    visited = set()
    explored_count = 0

    while stack:
        path = stack.pop()
        node = path[-1]

        if node == goal:
            return path, explored_count

        if node not in visited:
            visited.add(node)
            explored_count += 1
            for neighbor in graph.get(node, {}):
                if neighbor not in closed_sections:
                    new_path = list(path)
                    new_path.append(neighbor)
                    stack.append(new_path)
    return None, explored_count

def astar(graph, nodes_data, start, goal, optimize_for='distance', closed_sections=[], authorized=False):
    """A* Search using f(n) = g(n) + h(n)."""
    pq = [(0, 0, start, [start])] # This acts as our Open List
    visited = set()               # This acts as our Closed List
    explored_count = 0

    while pq:
        f_cost, g_cost, current, path = heapq.heappop(pq)

        if current == goal:
            # We return the path, cost, explored count, and the closed list
            return path, g_cost, explored_count, list(visited)

        if current in visited:
            continue

        visited.add(current)
        explored_count += 1

        for neighbor, costs in graph.get(current, {}).items():
            if neighbor in closed_sections:
                continue
            if nodes_data[neighbor].get('restricted', False) and not authorized:
                continue
            
            edge_cost = costs[optimize_for]
            new_g = g_cost + edge_cost
            h_cost = heuristic(neighbor, goal, nodes_data) if optimize_for == 'distance' else 0
            new_f = new_g + h_cost
            
            new_path = list(path)
            new_path.append(neighbor)
            heapq.heappush(pq, (new_f, new_g, neighbor, new_path))
            
    return None, float('inf'), explored_count, list(visited)