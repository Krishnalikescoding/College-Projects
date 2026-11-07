const state = {
    data: null,
    nodes: {},
    books: [],
    booksById: {},
    collection: [],
    matches: [],
    closedSections: new Set(),
    currentPath: [],
    currentVisited: [],
    network: null,
    highlightedSection: null,
    bookLabels: true,
    selectedTargetId: "",
    lastSingle: null,
    lastCompare: null,
    lastPlan: null,
    searchTimer: null,
    replayTimer: null,
};

const CROWD_MULTIPLIERS = { Low: 1.0, Medium: 1.25, High: 1.6 };
const PRIORITY_CLASS = { High: "priority-high", Medium: "priority-medium", Low: "priority-low" };

const $ = (id) => document.getElementById(id);

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }[character]));
}

function formatNumber(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return "n/a";
    }
    const number = Number(value);
    return Number.isInteger(number) ? String(number) : number.toFixed(2);
}

function nodeLabel(nodeId) {
    return state.nodes[nodeId]?.label || nodeId;
}

function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    $("toastContainer").appendChild(toast);
    window.setTimeout(() => toast.remove(), 4800);
}

async function requestJSON(url, options = {}) {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 20000);
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        });
        const text = await response.text();
        let data = null;
        if (text) {
            try {
                data = JSON.parse(text);
            } catch (error) {
                throw new Error(`The server returned an invalid JSON response (HTTP ${response.status}).`);
            }
        }
        if (!response.ok) {
            throw new Error(data?.message || data?.error || `Request failed with HTTP ${response.status}.`);
        }
        return data;
    } catch (error) {
        if (error.name === "AbortError") {
            throw new Error("The request timed out. Please try again.");
        }
        throw error;
    } finally {
        window.clearTimeout(timeout);
    }
}

async function withButtonState(button, busyText, task) {
    const original = button.textContent;
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    button.textContent = busyText;
    try {
        return await task();
    } finally {
        button.disabled = false;
        button.removeAttribute("aria-busy");
        button.textContent = original;
        updateControlAvailability();
    }
}

function setResultStatus(kind, label) {
    const badge = $("resultStatusBadge");
    badge.className = `badge ${kind}`;
    badge.textContent = label;
}

function renderIdle() {
    setResultStatus("neutral", "Idle");
    $("results").innerHTML = '<p class="empty-state">Waiting for an action. Search for a book, add it, then navigate or plan.</p>';
    hideLimitMeter();
}

function renderLoading(message) {
    setResultStatus("neutral", "Working");
    $("results").innerHTML = `<p class="empty-state">${escapeHtml(message)}</p>`;
}

function renderError(message) {
    setResultStatus("error", "Error");
    $("results").innerHTML = `
        <div class="result-block">
            <div class="result-banner error">
                <strong>Request failed</strong>
                ${escapeHtml(message)}
            </div>
            <p class="help">Check the input, the server console, or the closed/restricted settings and try again.</p>
        </div>`;
    showToast(message, "error");
}

function edgeCost(from, to, optimize) {
    const edge = state.data.edges.find((item) =>
        (item.from === from && item.to === to) || (item.from === to && item.to === from)
    );
    if (!edge) {
        return 0;
    }
    if (optimize === "time") {
        const multiplier = CROWD_MULTIPLIERS[state.nodes[to]?.crowd] || 1;
        return Number(edge.time) * multiplier;
    }
    return Number(edge.distance);
}

function routeStepHtml(path, optimize) {
    let html = '<ol class="route-list">';
    path.forEach((nodeId, index) => {
        if (index === 0) {
            html += `<li><strong>${escapeHtml(nodeLabel(nodeId))}</strong> <span class="leg-cost">(start)</span></li>`;
            return;
        }
        const previous = path[index - 1];
        const cost = edgeCost(previous, nodeId, optimize);
        html += `<li><strong>${escapeHtml(nodeLabel(previous))} &rarr; ${escapeHtml(nodeLabel(nodeId))}</strong>
            <span class="leg-cost">cost ${formatNumber(cost)} ${escapeHtml(optimize)}</span></li>`;
    });
    html += "</ol>";
    return html;
}

function updateLimitMeter(used, limit, remaining) {
    const meter = $("limitMeter");
    meter.hidden = false;
    const safeLimit = Number(limit) > 0 ? Number(limit) : 0;
    const percent = safeLimit > 0 ? Math.min(100, (Number(used) / safeLimit) * 100) : (Number(used) > 0 ? 100 : 0);
    const fill = $("limitMeterFill");
    fill.style.width = `${percent}%`;
    fill.className = "limit-meter-fill";
    if (Number(used) > safeLimit) {
        fill.classList.add("error");
    } else if (percent >= 80) {
        fill.classList.add("warning");
    } else {
        fill.classList.add("success");
    }
    $("limitMeterText").textContent = `${formatNumber(used)} / ${formatNumber(limit)} used; ${formatNumber(remaining)} remaining`;
}

function hideLimitMeter() {
    $("limitMeter").hidden = true;
}

function renderSingleResult(result) {
    const kind = result.found ? "success" : "warning";
    setResultStatus(kind, result.found ? "Route found" : "No route");
    const closed = (result.closed_sections || []).length
        ? `<p class="help">Closed sections applied: ${(result.closed_sections || []).map(escapeHtml).join(", ")}</p>`
        : "";
    let html = `
        <div class="result-block">
            <div class="result-banner ${kind}">
                <strong>${result.found ? "Route found" : "No route found"}</strong>
                ${escapeHtml(result.message)}
            </div>
            <div class="summary-grid">
                <div class="summary-item"><span>Algorithm</span><strong>${escapeHtml(result.algorithm || "")}</strong></div>
                <div class="summary-item"><span>Cost</span><strong>${formatNumber(result.cost)} ${escapeHtml(result.optimize || "")}</strong></div>
                <div class="summary-item"><span>Edges</span><strong>${formatNumber(result.edge_count)}</strong></div>
                <div class="summary-item"><span>Explored nodes</span><strong>${formatNumber(result.explored_count)}</strong></div>
            </div>`;
    if (result.found && result.path?.length) {
        html += `<div class="result-section"><h3>Step-by-step route</h3>${routeStepHtml(result.path, result.optimize)}</div>`;
    }
    if (result.visited?.length) {
        html += `<details class="result-section">
            <summary>Visited order (${result.visited.length} nodes)</summary>
            <ol class="visited-list">${result.visited.map((node) => `<li>${escapeHtml(nodeLabel(node))}</li>`).join("")}</ol>
        </details>`;
    }
    if (closed) {
        html += closed;
    }
    if (result.found && result.visited?.length) {
        html += '<button class="secondary-btn replay-btn" id="replayVisitedBtn" type="button">Replay visited order</button>';
    }
    html += "</div>";
    $("results").innerHTML = html;
    state.lastSingle = result;
    state.currentPath = result.found ? result.path : [];
    state.currentVisited = result.visited || [];
    const replay = $("replayVisitedBtn");
    if (replay) {
        replay.addEventListener("click", replayVisitedOrder);
    }
    renderGraph(true);
}

function renderCompareResult(result) {
    const foundAny = result.results.some((row) => row.found);
    setResultStatus(foundAny ? "success" : "warning", foundAny ? "Compared" : "No routes");
    const rows = result.results.map((row) => {
        const route = row.found ? row.path.map(nodeLabel).join(" → ") : "No route";
        return `<tr>
            <td><strong>${escapeHtml(row.algorithm)}</strong></td>
            <td class="route-cell">${escapeHtml(route)}</td>
            <td>${row.found ? formatNumber(row.edge_count) : "n/a"}</td>
            <td>${row.found ? formatNumber(row.cost) : "n/a"}</td>
            <td>${formatNumber(row.explored_count)}</td>
        </tr>`;
    }).join("");
    $("results").innerHTML = `
        <div class="result-block">
            <div class="result-banner ${foundAny ? "success" : "warning"}">
                <strong>Algorithm comparison</strong>
                Target: ${escapeHtml(nodeLabel(result.target))}. Metric: ${escapeHtml(result.optimize)}.
            </div>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Algorithm</th><th>Route</th><th>Edges</th><th>Weighted cost</th><th>Explored</th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
            <p class="help">BFS minimises edges, DFS is depth-first, and A* minimises the selected weighted cost when its heuristic is admissible. In time mode A* uses a zero heuristic (uniform-cost search).</p>
        </div>`;
    const best = result.results.find((row) => row.algorithm === "A*" && row.found)
        || result.results.find((row) => row.found);
    state.currentPath = best ? best.path : [];
    state.currentVisited = best ? best.visited : [];
    state.lastCompare = result;
    renderGraph(true);
}

function renderPlanResult(result) {
    const kind = result.missed.length ? "warning" : "success";
    setResultStatus(result.found ? kind : "error", result.found ? (result.missed.length ? "Partially planned" : "Planned") : "Nothing collected");
    const legs = result.legs.map((leg) => `<tr>
        <td>${escapeHtml(nodeLabel(leg.from))} → ${escapeHtml(nodeLabel(leg.to))}</td>
        <td>${escapeHtml(leg.title)}</td>
        <td><span class="badge ${PRIORITY_CLASS[leg.priority] || "neutral"}">${escapeHtml(leg.priority)}</span></td>
        <td>${formatNumber(leg.cost)}</td>
        <td>${formatNumber(leg.cumulative_cost)}</td>
        <td>${formatNumber(leg.remaining_limit)}</td>
    </tr>`).join("");
    const collected = result.collected.length
        ? `<ul class="collected-list">${result.collected.map((book) => `<li>${escapeHtml(book.title)} <span class="help">(${escapeHtml(nodeLabel(book.shelf))}, ${escapeHtml(book.priority)})</span></li>`).join("")}</ul>`
        : '<p class="empty-state">No books were collected.</p>';
    const missed = result.missed.length
        ? `<ul class="missed-list">${result.missed.map((book) => `<li>${escapeHtml(book.title)}<span class="missed-reason">${escapeHtml(book.reason)}${book.required_cost !== undefined ? `; needed ${formatNumber(book.required_cost)}, had ${formatNumber(book.remaining_limit)}` : ""}</span></li>`).join("")}</ul>`
        : '<p class="empty-state">All requested books were collected.</p>';

    $("results").innerHTML = `
        <div class="result-block">
            <div class="result-banner ${kind}">
                <strong>${result.found ? "Multi-book plan" : "Plan could not collect any book"}</strong>
                ${escapeHtml(result.message)}
            </div>
            <div class="summary-grid">
                <div class="summary-item"><span>Total cost</span><strong>${formatNumber(result.total_cost)} ${escapeHtml(result.optimize)}</strong></div>
                <div class="summary-item"><span>Limit</span><strong>${formatNumber(result.limit)}</strong></div>
                <div class="summary-item"><span>Remaining</span><strong>${formatNumber(result.remaining_limit)}</strong></div>
                <div class="summary-item"><span>Explored nodes</span><strong>${formatNumber(result.explored_count)}</strong></div>
            </div>
            <div class="result-section">
                <h4>Collected (${result.collected.length})</h4>
                ${collected}
            </div>
            <div class="result-section">
                <h4>Missed (${result.missed.length})</h4>
                ${missed}
            </div>
            ${result.legs.length ? `<div class="result-section"><h4>Legs between books</h4><div class="table-wrap"><table>
                <thead><tr><th>From → To</th><th>Book</th><th>Priority</th><th>Cost</th><th>Cumulative</th><th>Remaining</th></tr></thead>
                <tbody>${legs}</tbody></table></div></div>` : ""}
            <p class="help">This is a priority-ordered greedy planner using A* for each leg; it is not a globally optimal tour.</p>
        </div>`;
    updateLimitMeter(result.total_cost, result.limit, result.remaining_limit);
    state.lastPlan = result;
    state.currentPath = result.path || [];
    state.currentVisited = [];
    renderGraph(true);
}

function replayVisitedOrder() {
    if (!state.network || !state.currentVisited.length) {
        showToast("No visited order is available for replay.", "warning");
        return;
    }
    window.clearInterval(state.replayTimer);
    let index = 0;
    state.network.selectNodes([]);
    state.replayTimer = window.setInterval(() => {
        if (index >= state.currentVisited.length) {
            window.clearInterval(state.replayTimer);
            state.network.selectNodes([]);
            showToast("Visited-order replay complete.", "success");
            return;
        }
        const nodeId = state.currentVisited[index];
        state.network.selectNodes([nodeId]);
        state.network.focus(nodeId, { scale: 1.1, animation: { duration: 220, easingFunction: "easeInOutQuad" } });
        index += 1;
    }, 380);
}

function normalizeSearchValue(value) {
    return String(value || "").toLowerCase();
}

function searchBooks(query) {
    const needle = normalizeSearchValue(query).trim();
    if (!needle) {
        return [];
    }
    return state.books.filter((book) => {
        const shelfLabel = state.nodes[book.shelf]?.label || "";
        return [book.title, book.author, book.category, book.shelf, shelfLabel]
            .some((value) => normalizeSearchValue(value).includes(needle));
    });
}

function buildBadge(text, className) {
    const span = document.createElement("span");
    span.className = `badge ${className}`;
    span.textContent = text;
    return span;
}

function buildSearchItem(book) {
    const item = document.createElement("li");
    item.className = "search-item";
    const inCollection = state.collection.some((entry) => entry.id === book.id);
    item.innerHTML = `
        <div class="search-item-top">
            <div>
                <p class="search-title">${escapeHtml(book.title)}</p>
                <p class="search-meta">${escapeHtml(book.author)}</p>
            </div>
        </div>
        <p class="search-meta">${escapeHtml(nodeLabel(book.shelf))} (${escapeHtml(book.shelf)})</p>
        <div class="badge-row"></div>
        <div class="search-actions"></div>`;
    const badgeRow = item.querySelector(".badge-row");
    badgeRow.appendChild(buildBadge(book.priority, PRIORITY_CLASS[book.priority] || "neutral"));
    badgeRow.appendChild(buildBadge(book.available ? "Available" : "Unavailable", book.available ? "available" : "unavailable"));
    if (inCollection) {
        badgeRow.appendChild(buildBadge("In collection", "available"));
    }
    const actions = item.querySelector(".search-actions");
    const addButton = document.createElement("button");
    addButton.type = "button";
    addButton.className = "primary-btn";
    addButton.textContent = inCollection ? "In collection" : (book.available ? "Add to collection" : "Unavailable");
    addButton.disabled = inCollection || !book.available;
    addButton.setAttribute("aria-label", `Add ${book.title} to collection`);
    addButton.addEventListener("click", () => addBookToCollection(book.id));
    actions.appendChild(addButton);
    return item;
}

function renderSearchResults() {
    const query = $("searchInput").value;
    const status = $("searchStatus");
    const list = $("searchResults");
    const matches = searchBooks(query);
    state.matches = matches;
    list.innerHTML = "";
    $("searchCount").textContent = `${matches.length} match${matches.length === 1 ? "" : "es"}`;

    if (!query.trim()) {
        status.textContent = "Type to search title, author, category or shelf.";
        return;
    }
    if (!matches.length) {
        status.textContent = "No books match this search.";
        return;
    }
    status.textContent = `Showing all ${matches.length} matching book${matches.length === 1 ? "" : "s"}.`;
    matches.forEach((book) => list.appendChild(buildSearchItem(book)));
}

function addBookToCollection(bookId) {
    const book = state.booksById[bookId];
    if (!book) {
        showToast("That book is not in the catalogue.", "error");
        return;
    }
    if (!book.available) {
        showToast("That book is unavailable and cannot be collected.", "warning");
        return;
    }
    if (state.collection.some((entry) => entry.id === book.id)) {
        showToast("That book is already in the collection.", "warning");
        return;
    }
    state.collection.push(book);
    if (!state.selectedTargetId) {
        state.selectedTargetId = book.id;
    }
    updateCollectionUI();
    renderSearchResults();
    showToast(`Added "${book.title}" to the collection.`, "success");
}

function removeBookFromCollection(bookId) {
    state.collection = state.collection.filter((book) => book.id !== bookId);
    if (state.selectedTargetId === bookId) {
        state.selectedTargetId = state.collection[0]?.id || "";
    }
    updateCollectionUI();
    renderSearchResults();
    showToast("Book removed from the collection.", "info");
}

function moveWithinPriority(index, direction) {
    const book = state.collection[index];
    if (!book) {
        return;
    }
    let target = index + direction;
    while (target >= 0 && target < state.collection.length) {
        if (state.collection[target].priority === book.priority) {
            [state.collection[index], state.collection[target]] = [state.collection[target], state.collection[index]];
            updateCollectionUI();
            return;
        }
        target += direction;
    }
    showToast(`Already at the ${direction < 0 ? "first" : "last"} position in the ${book.priority} group.`, "warning");
}

function buildCollectionItem(book, index) {
    const item = document.createElement("li");
    item.className = "collection-item";
    item.draggable = true;
    item.dataset.index = String(index);
    item.innerHTML = `
        <div class="collection-item-top">
            <div class="collection-title-row">
                <span class="drag-handle" aria-hidden="true">::</span>
                <div>
                    <p class="collection-title">${escapeHtml(book.title)}</p>
                    <p class="collection-meta">${escapeHtml(book.author)}</p>
                    <p class="collection-meta">${escapeHtml(nodeLabel(book.shelf))} (${escapeHtml(book.shelf)})</p>
                </div>
            </div>
        </div>
        <div class="badge-row"></div>
        <div class="collection-actions"></div>`;
    const badgeRow = item.querySelector(".badge-row");
    badgeRow.appendChild(buildBadge(book.priority, PRIORITY_CLASS[book.priority] || "neutral"));
    badgeRow.appendChild(buildBadge(book.available ? "Available" : "Unavailable", book.available ? "available" : "unavailable"));
    const actions = item.querySelector(".collection-actions");

    const up = document.createElement("button");
    up.type = "button";
    up.className = "secondary-btn";
    up.textContent = "Up";
    up.setAttribute("aria-label", `Move ${book.title} up within its priority group`);
    up.addEventListener("click", () => moveWithinPriority(index, -1));
    actions.appendChild(up);

    const down = document.createElement("button");
    down.type = "button";
    down.className = "secondary-btn";
    down.textContent = "Down";
    down.setAttribute("aria-label", `Move ${book.title} down within its priority group`);
    down.addEventListener("click", () => moveWithinPriority(index, 1));
    actions.appendChild(down);

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "secondary-btn";
    remove.textContent = "Remove";
    remove.setAttribute("aria-label", `Remove ${book.title} from the collection`);
    remove.addEventListener("click", () => removeBookFromCollection(book.id));
    actions.appendChild(remove);

    item.addEventListener("dragstart", (event) => {
        event.dataTransfer.setData("text/plain", String(index));
        event.dataTransfer.effectAllowed = "move";
        item.classList.add("dragging");
    });
    item.addEventListener("dragend", () => item.classList.remove("dragging"));
    item.addEventListener("dragover", (event) => {
        event.preventDefault();
        item.classList.add("drag-over");
    });
    item.addEventListener("dragleave", () => item.classList.remove("drag-over"));
    item.addEventListener("drop", (event) => {
        event.preventDefault();
        item.classList.remove("drag-over");
        const sourceIndex = Number(event.dataTransfer.getData("text/plain"));
        const target = state.collection[index];
        const source = state.collection[sourceIndex];
        if (!source || !target || source.id === target.id) {
            return;
        }
        if (source.priority !== target.priority) {
            showToast("Drag books only inside the same priority group.", "warning");
            return;
        }
        state.collection.splice(sourceIndex, 1);
        const insertAt = state.collection.findIndex((entry) => entry.id === target.id);
        state.collection.splice(insertAt, 0, source);
        updateCollectionUI();
    });
    return item;
}

function updateCollectionUI() {
    const list = $("collectionList");
    list.innerHTML = "";
    state.collection.forEach((book, index) => list.appendChild(buildCollectionItem(book, index)));
    $("collectionCount").textContent = String(state.collection.length);
    $("collectionEmpty").hidden = state.collection.length > 0;

    const select = $("targetBookSelect");
    select.innerHTML = "";
    if (!state.collection.length) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "Add a book first";
        select.appendChild(option);
        state.selectedTargetId = "";
    } else {
        if (!state.collection.some((book) => book.id === state.selectedTargetId)) {
            state.selectedTargetId = state.collection[0].id;
        }
        state.collection.forEach((book) => {
            const option = document.createElement("option");
            option.value = book.id;
            option.textContent = `${book.title} — ${nodeLabel(book.shelf)} (${book.priority})`;
            select.appendChild(option);
        });
        select.value = state.selectedTargetId;
    }
    updateControlAvailability();
}

function updateControlAvailability() {
    const empty = state.collection.length === 0;
    $("navigateBtn").disabled = empty;
    $("compareBtn").disabled = empty;
    $("planBtn").disabled = empty;
    $("clearCollectionBtn").disabled = empty;
}

function populateClosedSections() {
    const container = $("closedSectionsList");
    container.innerHTML = "";
    Object.entries(state.nodes)
        .sort((a, b) => (a[1].label || a[0]).localeCompare(b[1].label || b[0]))
        .forEach(([nodeId, node]) => {
            const label = document.createElement("label");
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.value = nodeId;
            checkbox.checked = state.closedSections.has(nodeId);
            checkbox.setAttribute("aria-label", `Close ${node.label || nodeId}`);
            checkbox.addEventListener("change", () => {
                if (checkbox.checked) {
                    state.closedSections.add(nodeId);
                } else {
                    state.closedSections.delete(nodeId);
                }
                updateClosedCount();
                renderGraph(false);
            });
            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(`${node.label || nodeId}${node.restricted ? " (restricted)" : ""}`));
            container.appendChild(label);
        });
    updateClosedCount();
}

function updateClosedCount() {
    $("closedCount").textContent = String(state.closedSections.size);
    $("clearClosedBtn").disabled = state.closedSections.size === 0;
}

function clearClosedSections() {
    state.closedSections.clear();
    document.querySelectorAll("#closedSectionsList input[type=checkbox]").forEach((checkbox) => {
        checkbox.checked = false;
    });
    updateClosedCount();
    renderGraph(false);
    showToast("All sections are open again.", "info");
}

function sectionBookCount(nodeId) {
    return state.books.filter((book) => book.shelf === nodeId).length;
}

function truncateLabel(text, length = 24) {
    const value = String(text || "");
    return value.length > length ? `${value.slice(0, length - 1)}…` : value;
}

function buildSectionTitle(nodeId, node) {
    const crowd = node.crowd || "Low";
    return [
        `${node.label || nodeId}`,
        `Node id: ${nodeId}`,
        `Crowd: ${crowd}`,
        node.restricted ? "Restricted: yes" : "Restricted: no",
        state.closedSections.has(nodeId) ? "Closed: yes" : "Closed: no",
        `Books on this shelf: ${sectionBookCount(nodeId)}`,
    ].join("\n");
}

function buildBookTitle(book) {
    return [
        book.title,
        `Author: ${book.author}`,
        `Category: ${book.category}`,
        `Shelf: ${nodeLabel(book.shelf)} (${book.shelf})`,
        `Priority: ${book.priority}`,
        `Availability: ${book.available ? "Available" : "Unavailable"}`,
    ].join("\n");
}

function buildGraphNodes() {
    const nodes = [];
    const edges = [];
    const pathEdges = new Set();
    for (let index = 0; index < state.currentPath.length - 1; index += 1) {
        const current = state.currentPath[index];
        const next = state.currentPath[index + 1];
        pathEdges.add(`${current}|${next}`);
        pathEdges.add(`${next}|${current}`);
    }
    const pathNodes = new Set(state.currentPath);
    const collectionIds = new Set(state.collection.map((book) => book.id));
    const booksByShelf = new Map();

    Object.entries(state.nodes).forEach(([nodeId, node]) => {
        const isPath = pathNodes.has(nodeId);
        const isClosed = state.closedSections.has(nodeId);
        const isHighlighted = state.highlightedSection === nodeId;
        let background = "lightblue";
        if (node.restricted) {
            background = "#ff9999";
        }
        if (isClosed) {
            background = "#e0e0e0";
        }
        if (isPath) {
            background = "#99ff99";
        }
        const suffix = `${node.restricted ? "\n(restricted)" : ""}${isClosed ? "\n(closed)" : ""}`;
        nodes.push({
            id: nodeId,
            label: `${node.label || nodeId}${suffix}`,
            x: Number(node.x) * 165,
            y: Number(node.y) * 165,
            shape: "box",
            color: {
                background,
                border: isClosed ? "#888888" : (node.restricted ? "#c0392b" : (isPath ? "#27ae60" : "#666666")),
                highlight: { background, border: "#1f6fa8" },
            },
            borderWidth: isHighlighted ? 4 : (isPath ? 3 : 1),
            borderDashes: isClosed ? [6, 4] : false,
            font: { face: "Arial", size: 12, bold: true, color: "#263238" },
            title: buildSectionTitle(nodeId, node),
        });
        const shelfBooks = state.books.filter((book) => book.shelf === nodeId);
        booksByShelf.set(nodeId, shelfBooks);
    });

    booksByShelf.forEach((shelfBooks, shelfId) => {
        const shelf = state.nodes[shelfId];
        const baseX = Number(shelf.x) * 165;
        const baseY = Number(shelf.y) * 165;
        const count = Math.max(1, shelfBooks.length);
        shelfBooks.forEach((book, index) => {
            const angle = (index / count) * Math.PI * 2 + 0.35;
            const radius = 62 + (index % 3) * 17;
            const isHighlightedBook = state.highlightedSection === shelfId;
            const inCollection = collectionIds.has(book.id);
            const onRoute = pathNodes.has(shelfId);
            let background = "#fff9c4";
            let border = "#fbc02d";
            if (inCollection) {
                border = "#2ecc71";
            }
            if (onRoute) {
                background = "#e8ffe8";
            }
            if (isHighlightedBook) {
                background = "#fff3a3";
                border = "#e67e22";
            }
            nodes.push({
                id: `book_${book.id}`,
                label: state.bookLabels ? truncateLabel(book.title) : "",
                x: baseX + Math.cos(angle) * radius,
                y: baseY + Math.sin(angle) * radius,
                shape: "ellipse",
                color: {
                    background,
                    border,
                    highlight: { background: "#fff3a3", border: "#e67e22" },
                },
                borderWidth: isHighlightedBook || inCollection ? 2 : 1,
                font: { face: "Arial", size: 8, color: "#4d3b00" },
                title: buildBookTitle(book),
            });
            edges.push({
                from: shelfId,
                to: `book_${book.id}`,
                dashes: true,
                color: { color: "#888888", opacity: 0.6 },
                width: 1,
                arrows: { to: { enabled: false } },
            });
        });
    });

    state.data.edges.forEach((edge) => {
        const isRoute = pathEdges.has(`${edge.from}|${edge.to}`);
        edges.push({
            from: edge.from,
            to: edge.to,
            label: String(edge.distance),
            color: { color: isRoute ? "#008000" : "#cccccc" },
            width: isRoute ? 4 : 1,
            font: { face: "Arial", size: 10, align: "top", color: "#4d5b63" },
            title: `Walkway: ${edge.from} to ${edge.to}\nDistance: ${edge.distance}\nBase time: ${edge.time}`,
        });
    });
    return { nodes, edges };
}

function renderGraph(shouldFit = true) {
    const container = $("networkMap");
    if (!window.vis) {
        $("graphError").hidden = false;
        return;
    }
    $("graphError").hidden = true;
    const view = state.network
        ? { position: state.network.getViewPosition(), scale: state.network.getScale() }
        : null;
    if (state.network) {
        state.network.destroy();
    }
    const { nodes, edges } = buildGraphNodes();
    const data = {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges),
    };
    const options = {
        physics: false,
        layout: { improvedLayout: false },
        nodes: {
            shape: "box",
            font: { face: "Arial", size: 12 },
            borderWidth: 1,
            shadow: false,
        },
        edges: {
            smooth: false,
            font: { face: "Arial", size: 10 },
            color: { color: "#cccccc" },
        },
        interaction: {
            hover: true,
            tooltipDelay: 150,
            keyboard: true,
            navigationButtons: false,
            multiselect: false,
        },
    };
    state.network = new vis.Network(container, data, options);
    state.network.on("click", handleGraphClick);
    window.setTimeout(() => {
        if (!state.network) {
            return;
        }
        if (view && !shouldFit) {
            state.network.moveTo({ position: view.position, scale: view.scale, animation: false });
        } else {
            state.network.fit({ padding: 45, animation: false });
        }
    }, 30);
}

function handleGraphClick(params) {
    if (!params.nodes.length) {
        if (state.highlightedSection) {
            state.highlightedSection = null;
            renderGraph(false);
        }
        return;
    }
    const nodeId = String(params.nodes[0]);
    if (nodeId.startsWith("book_")) {
        const bookId = nodeId.slice(5);
        const book = state.booksById[bookId];
        if (book) {
            state.highlightedSection = book.shelf;
            renderGraph(false);
            showToast(`${book.title} — ${nodeLabel(book.shelf)}.`, "info");
        }
        return;
    }
    if (state.nodes[nodeId]) {
        state.highlightedSection = nodeId;
        const count = sectionBookCount(nodeId);
        renderGraph(false);
        showToast(`${nodeLabel(nodeId)}: ${count} book${count === 1 ? "" : "s"} on this shelf.`, "info");
    }
}

async function navigateSingle() {
    const book = state.collection.find((entry) => entry.id === state.selectedTargetId);
    if (!book) {
        showToast("Choose a collection book to navigate to.", "warning");
        return;
    }
    const payload = {
        start: "Entrance",
        target: book.shelf,
        algorithm: $("algoSelect").value,
        optimize: $("optimizeSelect").value,
        authorized: $("authorizedToggle").checked,
        closed_sections: Array.from(state.closedSections),
    };
    renderLoading("Searching the graph...");
    try {
        const result = await withButtonState($("navigateBtn"), "Navigating...", () =>
            requestJSON("/api/navigate", { method: "POST", body: JSON.stringify(payload) })
        );
        renderSingleResult(result);
        showToast(result.message, result.found ? "success" : "warning");
    } catch (error) {
        renderError(error.message);
    }
}

async function compareAlgorithms() {
    const book = state.collection.find((entry) => entry.id === state.selectedTargetId);
    if (!book) {
        showToast("Choose a collection book to compare.", "warning");
        return;
    }
    const payload = {
        start: "Entrance",
        target: book.shelf,
        optimize: $("optimizeSelect").value,
        authorized: $("authorizedToggle").checked,
        closed_sections: Array.from(state.closedSections),
    };
    renderLoading("Running BFS, DFS and A*...");
    try {
        const result = await withButtonState($("compareBtn"), "Comparing...", () =>
            requestJSON("/api/compare", { method: "POST", body: JSON.stringify(payload) })
        );
        renderCompareResult(result);
        showToast("Algorithm comparison complete.", "success");
    } catch (error) {
        renderError(error.message);
    }
}

async function planMultiBook() {
    if (!state.collection.length) {
        showToast("Add at least one book to the collection.", "warning");
        return;
    }
    const rawLimit = $("timeLimit").value.trim();
    const limit = Number(rawLimit);
    if (rawLimit === "" || !Number.isFinite(limit) || limit < 0) {
        showToast("Enter a finite, non-negative time/cost limit.", "error");
        $("timeLimit").focus();
        return;
    }
    const payload = {
        start: "Entrance",
        books: state.collection.map((book) => book.id),
        optimize: $("optimizeSelect").value,
        time_limit: limit,
        authorized: $("authorizedToggle").checked,
        closed_sections: Array.from(state.closedSections),
    };
    renderLoading("Planning the collection route...");
    try {
        const result = await withButtonState($("planBtn"), "Planning...", () =>
            requestJSON("/api/multi_route", { method: "POST", body: JSON.stringify(payload) })
        );
        renderPlanResult(result);
        showToast(
            `${result.collected.length} collected, ${result.missed.length} missed.`,
            result.missed.length ? "warning" : "success"
        );
    } catch (error) {
        renderError(error.message);
    }
}

function bindEvents() {
    $("searchInput").addEventListener("input", () => {
        window.clearTimeout(state.searchTimer);
        state.searchTimer = window.setTimeout(renderSearchResults, 120);
    });
    $("clearCollectionBtn").addEventListener("click", () => {
        state.collection = [];
        state.selectedTargetId = "";
        updateCollectionUI();
        renderSearchResults();
        showToast("Collection cleared.", "info");
    });
    $("targetBookSelect").addEventListener("change", (event) => {
        state.selectedTargetId = event.target.value;
    });
    $("clearClosedBtn").addEventListener("click", clearClosedSections);
    $("navigateBtn").addEventListener("click", navigateSingle);
    $("compareBtn").addEventListener("click", compareAlgorithms);
    $("planBtn").addEventListener("click", planMultiBook);
    $("fitViewBtn").addEventListener("click", () => {
        if (state.network) {
            state.network.fit({ padding: 45, animation: true });
        }
    });
    $("bookLabelsToggle").addEventListener("change", (event) => {
        state.bookLabels = event.target.checked;
        renderGraph(false);
    });
}

async function init() {
    try {
        const data = await requestJSON("/api/data");
        state.data = data;
        state.nodes = data.nodes;
        state.books = data.books;
        state.booksById = Object.fromEntries(data.books.map((book) => [book.id, book]));
        bindEvents();
        populateClosedSections();
        updateCollectionUI();
        renderSearchResults();
        renderIdle();
        renderGraph(true);
    } catch (error) {
        renderError(`Could not load library data: ${error.message}`);
        $("graphError").hidden = false;
        updateControlAvailability();
    }
}

init();
