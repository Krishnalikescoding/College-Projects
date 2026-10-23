from algorithms import astar

def plan_collection_route(graph, nodes_data, start_node, target_books, optimize_for='distance', time_limit=float('inf'), authorized=False):
    current_location = start_node
    
    # ADVANCED FEATURE: Sort books by Priority (High first, then Medium, then Low)
    priority_map = {"High": 1, "Medium": 2, "Low": 3}
    pending_books = sorted(target_books, key=lambda b: priority_map.get(b.get('priority', 'Low'), 3))
    
    full_route = [start_node]
    total_cost = 0
    total_explored = 0
    collected_books = []
    uncollected_books = []
    
    while pending_books:
        best_next_book = pending_books[0] # Take highest priority book
        target_shelf = best_next_book['shelf']
        
        path, cost, explored, closed_list = astar(
            graph, nodes_data, current_location, target_shelf, 
            optimize_for=optimize_for, authorized=authorized
        )
            
        # ADVANCED FEATURE: Check Time/Cost Limit
        if path and (total_cost + cost <= time_limit):
            if len(full_route) > 0 and path[0] == full_route[-1]:
                full_route.extend(path[1:])
            else:
                full_route.extend(path)
                
            total_cost += cost
            total_explored += explored
            current_location = target_shelf
            collected_books.append(best_next_book)
        else:
            uncollected_books.append(best_next_book)
            
        pending_books.pop(0)

    return full_route, total_cost, total_explored, collected_books, uncollected_books