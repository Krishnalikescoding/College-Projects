let libraryData = null;
let currentFoundBook = null;
let collectionList = [];
let network = null;

// Initialize the application by grabbing JSON data from backend
fetch('/api/data')
    .then(response => response.json())
    .then(data => {
        libraryData = data;
        drawGraph();
    });

function searchBook() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    currentFoundBook = null;
    
    for (let book of libraryData.books) {
        if (book.title.toLowerCase().includes(query) || book.author.toLowerCase().includes(query)) {
            
            // Check if the book is already in the collection list
            const isAlreadyAdded = collectionList.some(b => b.id === book.id);
            
            // Determine the status text to display
            let status = "Available";
            if (!book.available) {
                status = "Unavailable";
            } else if (isAlreadyAdded) {
                status = "Unavailable (Already in Collection)";
            }
            
            document.getElementById('searchResult').innerHTML = `Found: <b>${book.title}</b><br>Shelf: ${book.shelf} (${status})`;
            
            // Store the book temporarily, but force it to be "unavailable" if already added
            currentFoundBook = { 
                ...book, 
                available: book.available && !isAlreadyAdded 
            };
            
            return;
        }
    }
    document.getElementById('searchResult').innerText = "Book not found.";
}

function addToCollection() {
    if (!currentFoundBook) return alert("Search for a book first!");
    if (!currentFoundBook.available) return alert("Book is unavailable.");
    
    const isAlreadyAdded = collectionList.some(book => book.id === currentFoundBook.id);
    if (isAlreadyAdded) {
        return alert("You have already added this book to your collection!");
    }
    
    collectionList.push(currentFoundBook);
    updateCollectionUI();
    currentFoundBook = null;
    document.getElementById('searchResult').innerText = "";
    document.getElementById('searchInput').value = "";
}

function clearCollection() {
    collectionList = [];
    updateCollectionUI();
}

function updateCollectionUI() {
    const list = document.getElementById('collectionList');
    list.innerHTML = "";
    collectionList.forEach(book => {
        const li = document.createElement('li');
        li.innerText = `${book.title} (${book.shelf})`;
        list.appendChild(li);
    });
}

function drawGraph(path = []) {
    const container = document.getElementById('networkMap');
    const nodes = [];
    const edges = [];

    // 1. Create Main Section Nodes (Spread out for better visibility)
    for (const [nodeId, attr] of Object.entries(libraryData.nodes)) {
        let bgColor = 'lightblue'; 
        if (attr.restricted) bgColor = '#ff9999';
        if (path.includes(nodeId)) bgColor = '#99ff99';

        nodes.push({
            id: nodeId,
            label: nodeId,
            x: attr.x * 120, // Increased spacing so nodes are clearly visible
            y: attr.y * 120,
            color: { background: bgColor, border: '#666' },
            font: { size: 14, bold: true },
            shape: 'box', 
            fixed: false // Unfixing them temporarily helps the initial layout render cleaner
        });
    }

    // 2. Create Book Nodes as Children
    libraryData.books.forEach(book => {
        const bookNodeId = 'book_' + book.id; 
        
        nodes.push({
            id: bookNodeId,
            label: book.title,
            color: { background: '#fff9c4', border: '#fbc02d' }, 
            font: { size: 10 },
            shape: 'ellipse'
        });

        // Link the book to its shelf
        edges.push({
            from: book.shelf,
            to: bookNodeId,
            color: { color: '#888', opacity: 0.6 }, // Softer color for book edges
            dashes: true, 
            length: 40 
        });
    });

    // 3. Create Main Walking Edges
    libraryData.edges.forEach(edge => {
        let color = '#ccc';
        let width = 1;
        
        // Highlight edge if part of the calculated path
        for (let i = 0; i < path.length - 1; i++) {
            if ((path[i] === edge.from && path[i+1] === edge.to) || 
                (path[i] === edge.to && path[i+1] === edge.from)) {
                color = 'green';
                width = 3;
                break;
            }
        }

        edges.push({
            from: edge.from,
            to: edge.to,
            label: String(edge.distance),
            color: { color: color },
            width: width,
            font: { align: 'top', size: 12 },
            length: edge.distance * 15
        });
    });

    const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };
    
    // Use Repulsion instead of BarnesHut for a cleaner, stiffer initial layout
    const options = { 
        physics: {
            enabled: true,
            solver: 'repulsion',
            repulsion: {
                nodeDistance: 100,
                springLength: 100,
                springConstant: 0.05
            },
            stabilization: {
                iterations: 200 // Calculates physics instantly before showing the graph
            }
        },
        layout: {
            randomSeed: 42 // Ensures the graph always loads in the exact same clean layout
        }
    };
    
    if (network) network.destroy();
    network = new vis.Network(container, data, options);

    // Once the graph calculates its layout, turn physics completely OFF.
    // This stops all bouncy animations and locks the nodes beautifully in place.
    network.on("stabilizationIterationsDone", function () {
        network.setOptions({ physics: false }); // Turn off animation/movement
        network.fit({ padding: 30 });           // Center the camera
    });
}

async function navigateSingle() {
    if (collectionList.length === 0) return alert("Add a book to collection first.");
    
    const target = collectionList[collectionList.length - 1].shelf;
    const algo = document.getElementById('algoSelect').value;
    
    // Grab the optimization choice from HTML
    const optimizeDropdown = document.getElementById('optimizeSelect');
    const optimizeChoice = optimizeDropdown ? optimizeDropdown.value : 'distance';

    const res = await fetch('/api/navigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            target: target, 
            algorithm: algo,
            optimize: optimizeChoice 
        })
    });
    
    const data = await res.json();
    if (data.path) {
        document.getElementById('resultText').innerHTML = `<b>Cost:</b> ${data.cost}<br><b>Explored Nodes:</b> ${data.explored}<br><b>Closed List:</b> ${data.closed_list.join(', ')}<br><b>Route:</b> ${data.path.join(' ➔ ')}`;
        drawGraph(data.path);
    } else {
        document.getElementById('resultText').innerText = "No path found.";
    }
}

async function navigateMulti() {
    if (collectionList.length === 0) return alert("Collection is empty.");
    
    // Grab the actual book objects so the backend knows their priorities
    const booksData = collectionList.map(b => b); 

    // Grab the advanced feature inputs from HTML
    const optimizeDropdown = document.getElementById('optimizeSelect');
    const optimizeChoice = optimizeDropdown ? optimizeDropdown.value : 'distance';
    
    const timeLimitInput = document.getElementById('timeLimit');
    const timeLimitValue = timeLimitInput ? parseInt(timeLimitInput.value) : 9999;

    const res = await fetch('/api/multi_route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            books: booksData, 
            optimize: optimizeChoice,
            time_limit: timeLimitValue
        })
    });
    
    const data = await res.json();
    if (data.path) {
        let msg = `<b>Distance/Time Used:</b> ${data.distance}<br><b>Explored:</b> ${data.explored}<br>`;
        msg += `<b>Collected:</b> ${data.collected.join(', ')}<br>`;
        
        if (data.uncollected && data.uncollected.length > 0) {
            msg += `<span style="color:red"><b>Out of Time! Missed:</b> ${data.uncollected.join(', ')}</span><br>`;
        }
        
        msg += `<b>Route:</b> ${data.path.join(' ➔ ')}`;
        
        document.getElementById('resultText').innerHTML = msg;
        drawGraph(data.path);
    } else {
        document.getElementById('resultText').innerText = "Failed to generate route.";
    }
}