const fs = require("fs");
const path = require("path");

const OUT_DIR = path.join(__dirname, "..", "deliverables", "screenshots");
const APP_URL = process.env.APP_URL || "http://127.0.0.1:5000/";
const DEBUG_URL = process.env.DEBUG_URL || "http://127.0.0.1:9222";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
    fs.mkdirSync(OUT_DIR, { recursive: true });

    const targets = await (await fetch(`${DEBUG_URL}/json/list`)).json();
    const page = targets.find((target) => target.type === "page");
    if (!page) {
        throw new Error("No Chrome page target found. Start Chromium with --remote-debugging-port=9222.");
    }

    const socket = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
        socket.onopen = resolve;
        socket.onerror = reject;
    });

    let messageId = 0;
    const pending = new Map();
    socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.id && pending.has(message.id)) {
            const { resolve, reject } = pending.get(message.id);
            pending.delete(message.id);
            if (message.error) {
                reject(new Error(JSON.stringify(message.error)));
            } else {
                resolve(message.result);
            }
        }
    };

    function send(method, params = {}) {
        return new Promise((resolve, reject) => {
            const id = ++messageId;
            pending.set(id, { resolve, reject });
            socket.send(JSON.stringify({ id, method, params }));
        });
    }

    async function evaluate(expression, awaitPromise = true) {
        const result = await send("Runtime.evaluate", {
            expression,
            awaitPromise,
            returnByValue: true,
            userGesture: true,
        });
        if (result.exceptionDetails) {
            throw new Error(
                result.exceptionDetails.exception?.description
                || result.exceptionDetails.text
                || "Browser evaluation failed"
            );
        }
        return result.result.value;
    }

    async function waitFor(expression, timeout = 8000) {
        const deadline = Date.now() + timeout;
        while (Date.now() < deadline) {
            if (await evaluate(`Boolean(${expression})`)) {
                return;
            }
            await sleep(100);
        }
        throw new Error(`Timed out waiting for: ${expression}`);
    }

    async function screenshot(name) {
        const result = await send("Page.captureScreenshot", { format: "png", fromSurface: true });
        fs.writeFileSync(path.join(OUT_DIR, name), Buffer.from(result.data, "base64"));
        console.log(`wrote ${name}`);
    }

    async function loadApp() {
        await send("Page.navigate", { url: APP_URL });
        await sleep(1200);
        await waitFor("document.querySelector('#networkMap canvas') && typeof state !== 'undefined' && state.data");
        await sleep(500);
        await evaluate("document.querySelector('.sidebar').scrollTop = 0");
    }

    async function addBook(title) {
        const titleJson = JSON.stringify(title);
        await evaluate(`(async () => {
            const input = document.getElementById('searchInput');
            input.value = ${titleJson};
            input.dispatchEvent(new Event('input', { bubbles: true }));
            await new Promise((resolve) => setTimeout(resolve, 300));
            const items = [...document.querySelectorAll('.search-item')];
            const item = items.find((entry) => entry.querySelector('.search-title')?.textContent.trim() === ${titleJson});
            if (!item) throw new Error('No search result for ' + ${titleJson});
            const button = item.querySelector('.search-actions button');
            if (!button || button.disabled) throw new Error('Add button unavailable for ' + ${titleJson});
            button.click();
            await new Promise((resolve) => setTimeout(resolve, 180));
        })()`);
    }

    async function selectTarget(bookId) {
        await evaluate(`(() => {
            const select = document.getElementById('targetBookSelect');
            select.value = ${JSON.stringify(bookId)};
            select.dispatchEvent(new Event('change', { bubbles: true }));
        })()`);
    }

    async function setSelect(id, value) {
        await evaluate(`(() => {
            const select = document.getElementById(${JSON.stringify(id)});
            select.value = ${JSON.stringify(value)};
            select.dispatchEvent(new Event('change', { bubbles: true }));
        })()`);
    }

    async function setCheckbox(id, checked) {
        await evaluate(`(() => {
            const box = document.getElementById(${JSON.stringify(id)});
            box.checked = ${Boolean(checked)};
            box.dispatchEvent(new Event('change', { bubbles: true }));
        })()`);
    }

    async function click(id) {
        await evaluate(`document.getElementById(${JSON.stringify(id)}).click()`);
    }

    async function scrollTo(id) {
        await evaluate(`(() => {
            const sidebar = document.querySelector('.sidebar');
            const element = document.getElementById(${JSON.stringify(id)});
            if (element) sidebar.scrollTop = Math.max(0, element.offsetTop - 10);
        })()`);
        await sleep(250);
    }

    async function summarize(label) {
        const summary = await evaluate(`(() => {
            const sidebar = document.querySelector('.sidebar');
            const rect = (id) => {
                const element = document.getElementById(id);
                if (!element) return null;
                const box = element.getBoundingClientRect();
                return { top: Math.round(box.top), bottom: Math.round(box.bottom), height: Math.round(box.height) };
            };
            return {
                status: document.getElementById('resultStatusBadge')?.textContent.trim(),
                resultsText: document.getElementById('results')?.innerText.replace(/\\s+/g, ' ').trim().slice(0, 500),
                searchCount: document.getElementById('searchCount')?.textContent.trim(),
                searchText: document.getElementById('searchResults')?.innerText.replace(/\\s+/g, ' ').trim().slice(0, 350),
                collectionCount: document.getElementById('collectionCount')?.textContent.trim(),
                collectionText: document.getElementById('collectionList')?.innerText.replace(/\\s+/g, ' ').trim().slice(0, 350),
                closedCount: document.getElementById('closedCount')?.textContent.trim(),
                resultsRect: rect('resultsHeading'),
                collectionRect: rect('collectionHeading'),
                sidebarTop: Math.round(sidebar.scrollTop),
            };
        })()`);
        console.log(`\n[${label}] ${JSON.stringify(summary)}`);
    }

    async function waitForIdleButton(id) {
        await sleep(350);
        await waitFor(`document.getElementById(${JSON.stringify(id)}).getAttribute('aria-busy') !== 'true'`);
        await sleep(350);
    }

    await send("Page.enable");
    await send("Runtime.enable");
    await send("Emulation.setDeviceMetricsOverride", {
        width: 1440,
        height: 1400,
        deviceScaleFactor: 1,
        mobile: false,
    });

    await loadApp();
    await screenshot("01-main.png");
    await summarize("01-main");

    await evaluate(`(() => {
        const input = document.getElementById('searchInput');
        input.value = 'physics';
        input.dispatchEvent(new Event('input', { bubbles: true }));
    })()`);
    await sleep(400);
    await evaluate("document.querySelector('.sidebar').scrollTop = 0");
    await screenshot("02-search-multiple.png");
    await summarize("02-search-multiple");

    await loadApp();
    await addBook("Introduction to Algorithms");
    await addBook("Numerical Analysis");
    await addBook("1984");
    await evaluate(`(() => {
        const input = document.getElementById('searchInput');
        input.value = '';
        input.dispatchEvent(new Event('input', { bubbles: true }));
    })()`);
    await scrollTo("collectionCard");
    await screenshot("03-collection-priorities.png");
    await summarize("03-collection-priorities");

    await addBook("Fundamentals of Physics");
    await selectTarget("119");
    await setSelect("algoSelect", "BFS");
    await click("navigateBtn");
    await waitForIdleButton("navigateBtn");
    await scrollTo("resultsCard");
    await screenshot("04-single-bfs.png");
    await summarize("04-single-bfs");

    await setSelect("algoSelect", "DFS");
    await click("navigateBtn");
    await waitForIdleButton("navigateBtn");
    await scrollTo("resultsCard");
    await screenshot("05-single-dfs.png");
    await summarize("05-single-dfs");

    await setSelect("algoSelect", "A*");
    await click("navigateBtn");
    await waitForIdleButton("navigateBtn");
    await scrollTo("resultsCard");
    await screenshot("06-single-astar.png");
    await summarize("06-single-astar");

    await click("compareBtn");
    await waitForIdleButton("compareBtn");
    await scrollTo("resultsCard");
    await screenshot("07-compare.png");
    await summarize("07-compare");

    await addBook("Pattern Recognition and Machine Learning");
    await evaluate("document.getElementById('timeLimit').value = '10'");
    await click("planBtn");
    await waitForIdleButton("planBtn");
    await scrollTo("resultsCard");
    await screenshot("08-multi-plan-missed.png");
    await summarize("08-multi-plan-missed");

    await loadApp();
    await addBook("Confidential Neural Networks");
    await selectTarget("117");
    await setSelect("algoSelect", "A*");
    await setCheckbox("authorizedToggle", false);
    await click("navigateBtn");
    await waitForIdleButton("navigateBtn");
    await scrollTo("resultsCard");
    await screenshot("09-restricted-off.png");
    await summarize("09-restricted-off");

    await setCheckbox("authorizedToggle", true);
    await click("navigateBtn");
    await waitForIdleButton("navigateBtn");
    await scrollTo("resultsCard");
    await screenshot("10-restricted-on.png");
    await summarize("10-restricted-on");

    await loadApp();
    await addBook("Machine Learning");
    await selectTarget("111");
    await setSelect("algoSelect", "A*");
    await evaluate(`(() => {
        const box = [...document.querySelectorAll('#closedSectionsList input')]
            .find((input) => input.value === 'CS_Section');
        box.checked = true;
        box.dispatchEvent(new Event('change', { bubbles: true }));
    })()`);
    await click("navigateBtn");
    await waitForIdleButton("navigateBtn");
    await evaluate("document.querySelector('.closed-details').open = true");
    await scrollTo("resultsCard");
    await screenshot("11-closed-reroute.png");
    await summarize("11-closed-reroute");

    await evaluate(`(async () => {
        try {
            await requestJSON('/api/navigate', {
                method: 'POST',
                body: JSON.stringify({ target: 'No_Such_Node' })
            });
        } catch (error) {
            renderError(error.message);
        }
    })()`);
    await sleep(500);
    await scrollTo("resultsCard");
    await screenshot("12-error.png");
    await summarize("12-error");

    socket.close();
    console.log(`Screenshots written to ${OUT_DIR}`);
}

main().catch((error) => {
    console.error(error.stack || error);
    process.exitCode = 1;
});
