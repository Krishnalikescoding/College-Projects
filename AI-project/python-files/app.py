from flask import Flask, render_template, request, jsonify
import json
import os
from algorithms import bfs, dfs, astar
from multi_book_agent import plan_collection_route

app = Flask(__name__)

# Load the library data
base_dir = os.path.dirname(__file__)
json_path = os.path.join(base_dir, '..', 'JSON', 'library_data.json')
with open(json_path, 'r') as f:
    library_data = json.load(f)

# Rebuild graph structure for algorithms
graph = {}
for node in library_data['nodes']:
    graph[node] = {}
for edge in library_data['edges']:
    u, v = edge['from'], edge['to']
    graph[u][v] = {'distance': edge['distance'], 'time': edge['time']}
    graph[v][u] = {'distance': edge['distance'], 'time': edge['time']}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(library_data)

@app.route('/api/navigate', methods=['POST'])
def navigate():
    data = request.json
    target = data.get('target')
    algo = data.get('algorithm', 'A*')
    optimize = data.get('optimize', 'distance')
    start = "Entrance"

    if algo == "BFS":
        path, explored, closed_list = bfs(graph, start, target, [], False)
        cost = len(path) - 1 if path else 0
    elif algo == "DFS":
        path, explored, closed_list = dfs(graph, start, target, [], False)
        cost = len(path) - 1 if path else 0
    else:
        path, cost, explored, closed_list = astar(graph, library_data['nodes'], start, target, optimize, [], False)

    return jsonify({"path": path, "cost": cost, "explored": explored, "closed_list": closed_list})

@app.route('/api/multi_route', methods=['POST'])
def multi_route():
    data = request.json
    books = data.get('books', [])
    time_limit = int(data.get('time_limit', 9999))
    optimize = data.get('optimize', 'distance')
    authorized = data.get('authorized', False)
    
    start = "Entrance"
    
    path, cost, explored, collected, uncollected = plan_collection_route(
        graph, library_data['nodes'], start, books, optimize, time_limit, authorized
    )
    
    return jsonify({
        "path": path, 
        "distance": cost, 
        "explored": explored, 
        "collected": [b['title'] for b in collected], 
        "uncollected": [b['title'] for b in uncollected]
    })

# This is the missing part that starts the server!
if __name__ == '__main__':
    app.run(debug=True)