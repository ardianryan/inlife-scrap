// SPA Router & API Client for Internship Scraper Console

const API_BASE = window.location.origin;
let syncInterval = null;
let blastInterval = null;

// --- PAGINATION & SELECTION STATE ---
let allApplicants = [];
let currentPage = 1;
const rowsPerPage = 10;
let selectedCandidateIds = [];

// --- INITIALIZATION & SESSION PERSISTENCE ---
document.addEventListener("DOMContentLoaded", () => {
    // Check if user is already authenticated
    const token = localStorage.getItem("session_token") || getQueryParam("session");
    if (token === "authenticated") {
        // Persist token in localStorage
        localStorage.setItem("session_token", "authenticated");
        // Clear query parameters from browser bar cleanly
        window.history.replaceState({}, document.title, window.location.pathname);
        showConsoleBoard();
    } else {
        showLoginScreen();
    }
});

function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// --- AUTHENTICATION ---
async function handleLogin(event) {
    event.preventDefault();
    const user = document.getElementById("username").value;
    const pass = document.getElementById("password").value;
    const errorBox = document.getElementById("login-error");
    
    try {
        const response = await fetch(`${API_BASE}/api/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: user, password: pass })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem("session_token", data.token);
            errorBox.classList.add("hidden");
            showConsoleBoard();
        } else {
            errorBox.classList.remove("hidden");
        }
    } catch (e) {
        errorBox.textContent = "Server connection lost.";
        errorBox.classList.remove("hidden");
    }
}

function handleLogout() {
    localStorage.removeItem("session_token");
    showLoginScreen();
}

function showLoginScreen() {
    document.getElementById("login-screen").classList.remove("hidden");
    document.getElementById("app-screen").classList.add("hidden");
}

function showConsoleBoard() {
    document.getElementById("login-screen").classList.add("hidden");
    document.getElementById("app-screen").classList.remove("hidden");
    
    // Initialize Dashboard data
    switchPage("Dashboard");
}

// --- CLIENT-SIDE SPA ROUTING ---
function switchPage(pageId) {
    // 1. Toggle Sidebar Active State
    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.remove("active");
    });
    const activeNav = document.getElementById(`nav-${pageId}`);
    if (activeNav) activeNav.classList.add("active");
    
    // 2. Toggle Main Content Views
    document.querySelectorAll(".view-panel").forEach(panel => {
        panel.classList.add("hidden");
    });
    document.getElementById(`view-${pageId}`).classList.remove("hidden");
    
    // 3. Load Dynamic Data depending on view
    if (pageId === "Dashboard") {
        loadDashboard();
    } else if (pageId === "Sync") {
        loadSyncInfo();
    } else if (pageId === "Settings") {
        loadSettings();
    }
}

// --- DASHBOARD LOADER ---
async function loadDashboard() {
    try {
        // Load Database Stats
        const statsRes = await fetch(`${API_BASE}/api/stats`);
        const stats = await statsRes.json();
        
        // Update KPI values
        document.getElementById("kpi-total-candidates").textContent = stats.total || 0;
        document.getElementById("kpi-active-positions").textContent = stats.unique_positions_count || 0;
        document.getElementById("kpi-last-updated").textContent = stats.last_updated || "No records";
        
        // Update Sidebar labels
        document.getElementById("db-size-label").textContent = `${stats.db_size_kb.toFixed(1)} KB`;
        
        // Update Network status dot
        const statusDiv = document.getElementById("connection-status");
        if (stats.db_size_kb >= 0) { // backend is active
            statusDiv.className = "status-indicator online";
            statusDiv.querySelector(".label").textContent = "Online";
        }
        
        // Render Position Breakdown Bars
        renderPositionBreakdown(stats.position_distribution, stats.total);
        
        // Load filter lists once
        await loadFilterOptions();
        
        // Load Applicants records
        await loadApplicants();
        
    } catch (e) {
        console.error("Failed to load dashboard statistics:", e);
    }
}

function renderPositionBreakdown(distribution, total) {
    const container = document.getElementById("position-breakdown-container");
    container.innerHTML = "";
    
    if (!distribution || Object.keys(distribution).length === 0) {
        container.innerHTML = `<div style="grid-column: span 2; text-align: center; color: #64748b; font-size: 0.9rem;">No distributions recorded yet.</div>`;
        return;
    }
    
    // Sort items desc
    const sorted = Object.entries(distribution).sort((a, b) => b[1] - a[1]);
    
    sorted.forEach(([pos, count]) => {
        const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
        
        const cardHTML = `
            <div class="distribution-item">
                <div class="dist-header">
                    <span>${pos}</span>
                    <span class="dist-count">${count} (${pct}%)</span>
                </div>
                <div class="dist-bar-bg">
                    <div class="dist-bar-fill" style="width: ${pct}%;"></div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML("beforeend", cardHTML);
    });
}

// --- FILTER & TABLE LOADER ---
let filtersLoaded = false;
async function loadFilterOptions() {
    if (filtersLoaded) return; // prevent redundant queries
    try {
        const response = await fetch(`${API_BASE}/api/filters`);
        const data = await response.json();
        
        const majorSelect = document.getElementById("filter-major");
        const posSelect = document.getElementById("filter-position");
        
        // Clear additional options
        majorSelect.innerHTML = '<option value="All Majors">All Majors</option>';
        posSelect.innerHTML = '<option value="All Positions">All Positions</option>';
        
        data.majors.forEach(m => {
            majorSelect.insertAdjacentHTML("beforeend", `<option value="${m}">${m}</option>`);
        });
        
        data.positions.forEach(p => {
            // Find if Sistem Informasi exists to make it default
            const isSI = p.toUpperCase() === "SISTEM INFORMASI";
            posSelect.insertAdjacentHTML("beforeend", `<option value="${p}" ${isSI ? "selected" : ""}>${p}</option>`);
        });
        
        filtersLoaded = true;
    } catch (e) {
        console.error("Failed to load select parameters:", e);
    }
}

async function loadApplicants() {
    const search = document.getElementById("filter-search").value;
    const major = document.getElementById("filter-major").value;
    const position = document.getElementById("filter-position").value;
    
    const tableBody = document.getElementById("applicants-table-body");
    tableBody.innerHTML = '<tr><td colspan="8" class="table-placeholder">Filtering candidate logs...</td></tr>';
    
    try {
        const url = new URL(`${API_BASE}/api/applicants`);
        if (search) url.searchParams.append("search", search);
        if (major) url.searchParams.append("major", major);
        if (position) url.searchParams.append("position", position);
        
        const response = await fetch(url);
        
        // Save to global applicants array and reset page index
        allApplicants = await response.json();
        currentPage = 1;
        
        // Reset selections on search/filter refresh to prevent mismatch
        selectedCandidateIds = [];
        updateBlastButtonState();
        document.getElementById("check-all-candidates").checked = false;
        
        displayApplicants();
        
    } catch (e) {
        tableBody.innerHTML = '<tr><td colspan="8" class="table-placeholder" style="color: #dc2626;">Error retrieving data records.</td></tr>';
    }
}

function displayApplicants() {
    const tableBody = document.getElementById("applicants-table-body");
    const countLabel = document.getElementById("candidates-count-label");
    const pagControls = document.getElementById("pagination-controls");
    
    countLabel.innerHTML = `Found <b>${allApplicants.length}</b> candidates matching criteria.`;
    tableBody.innerHTML = "";
    
    if (allApplicants.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="8" class="table-placeholder">No matching candidate profiles found.</td></tr>';
        pagControls.classList.add("hidden");
        return;
    }
    
    // Calculate Slicing
    const totalPages = Math.ceil(allApplicants.length / rowsPerPage);
    const start = (currentPage - 1) * rowsPerPage;
    const end = Math.min(start + rowsPerPage, allApplicants.length);
    const pageItems = allApplicants.slice(start, end);
    
    // Check if all items on this page are selected to update the head checkbox
    let allOnPageChecked = true;
    
    pageItems.forEach(c => {
        const isChecked = selectedCandidateIds.includes(c.id);
        if (!isChecked) allOnPageChecked = false;
        
        const rawStage = c.tahap ? c.tahap.toUpperCase() : "";
        const displayStage = c.tahap ? c.tahap.toUpperCase() : "-";
        
        // Map status style classes semantically
        let badgeClass = "";
        if (rawStage.includes("DITERIMA") || rawStage.includes("LULUS") || rawStage.includes("SUCCESS")) {
            badgeClass = "diterima";
        } else if (rawStage.includes("DITOLAK") || rawStage.includes("GAGAL") || rawStage.includes("FAIL")) {
            badgeClass = "ditolak";
        } else if (rawStage.includes("INTERVIEW") || rawStage.includes("WAWANCARA")) {
            badgeClass = "interview";
        } else if (rawStage.includes("BERKAS") || rawStage.includes("ADMINISTRASI") || rawStage.includes("SELEKSI")) {
            badgeClass = "berkas";
        }
        
        const rowHTML = `
            <tr>
                <td style="text-align: center;">
                    <input type="checkbox" onchange="handleCandidateSelect(this, ${c.id})" ${isChecked ? "checked" : ""}>
                </td>
                <td style="font-weight: 700; color: #0f172a;" title="${c.name}">${c.name}</td>
                <td title="${c.major}">${c.major}</td>
                <td title="${c.university}">${c.university}</td>
                <td title="${c.phone_number || "-"}">${c.phone_number || "-"}</td>
                <td title="${c.email || "-"}">${c.email || "-"}</td>
                <td title="${c.position_title}">${c.position_title}</td>
                <td><span class="stage-badge ${badgeClass}">${displayStage}</span></td>
            </tr>
        `;
        tableBody.insertAdjacentHTML("beforeend", rowHTML);
    });
    
    // Set status of Select All checkbox
    document.getElementById("check-all-candidates").checked = allOnPageChecked && pageItems.length > 0;
    
    // Configure pagination panel visibility
    if (allApplicants.length > rowsPerPage) {
        pagControls.classList.remove("hidden");
        document.getElementById("page-indicator").textContent = `Page ${currentPage} of ${totalPages}`;
        document.getElementById("btn-prev-page").disabled = currentPage === 1;
        document.getElementById("btn-next-page").disabled = currentPage === totalPages;
    } else {
        pagControls.classList.add("hidden");
    }
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        displayApplicants();
    }
}

function nextPage() {
    const totalPages = Math.ceil(allApplicants.length / rowsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        displayApplicants();
    }
}

// --- CHECKBOX SELECTION HANDLING ---
function handleCandidateSelect(checkbox, id) {
    if (checkbox.checked) {
        if (!selectedCandidateIds.includes(id)) {
            selectedCandidateIds.push(id);
        }
    } else {
        selectedCandidateIds = selectedCandidateIds.filter(cid => cid !== id);
    }
    updateBlastButtonState();
}

function toggleSelectAllCandidates() {
    const isChecked = document.getElementById("check-all-candidates").checked;
    
    // Calculate current page slice
    const start = (currentPage - 1) * rowsPerPage;
    const end = Math.min(start + rowsPerPage, allApplicants.length);
    const pageItems = allApplicants.slice(start, end);
    
    pageItems.forEach(c => {
        if (isChecked) {
            if (!selectedCandidateIds.includes(c.id)) {
                selectedCandidateIds.push(c.id);
            }
        } else {
            selectedCandidateIds = selectedCandidateIds.filter(cid => cid !== c.id);
        }
    });
    
    // Re-render display to check/uncheck inputs
    displayApplicants();
    updateBlastButtonState();
}

function updateBlastButtonState() {
    const btn = document.getElementById("btn-open-blast");
    if (selectedCandidateIds.length > 0) {
        btn.disabled = false;
        btn.querySelector("span:last-child").textContent = `Blast WA (${selectedCandidateIds.length})`;
    } else {
        btn.disabled = true;
        btn.querySelector("span:last-child").textContent = "Blast WA";
    }
}

// --- WHATSAPP BLAST MODAL DIALOGS ---
async function openBlastModal() {
    if (selectedCandidateIds.length === 0) return;
    
    // Set recipient counts
    document.getElementById("blast-recipient-count").textContent = selectedCandidateIds.length;
    
    // Show loading state in text box and log terminal
    const txtArea = document.getElementById("blast-template-text");
    txtArea.value = "Loading message template...";
    txtArea.disabled = true;
    
    document.getElementById("blast-progress-section").classList.add("hidden");
    document.getElementById("blast-console-logs").innerHTML = `<div style="color:var(--text-muted);">Console ready. Waiting to send...</div>`;
    
    // Show Modal overlay
    document.getElementById("blast-modal").classList.remove("hidden");
    
    try {
        // Fetch default WA template from server settings API
        const response = await fetch(`${API_BASE}/api/settings`);
        const data = await response.json();
        
        txtArea.value = data.wa_template || "";
        txtArea.disabled = false;
        
    } catch (e) {
        txtArea.value = "Halo {{nama}},\n\nKami dari Inlife Surabaya...";
        txtArea.disabled = false;
    }
}

function closeBlastModal() {
    document.getElementById("blast-modal").classList.add("hidden");
    if (blastInterval) {
        clearInterval(blastInterval);
        blastInterval = null;
    }
}

async function startWaBlast() {
    const templateMsg = document.getElementById("blast-template-text").value;
    if (!templateMsg.trim()) {
        alert("Pesan template tidak boleh kosong.");
        return;
    }
    
    const sendBtn = document.getElementById("btn-send-blast");
    const cancelBtn = document.getElementById("btn-cancel-blast");
    
    sendBtn.disabled = true;
    cancelBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/wa/blast`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                candidate_ids: selectedCandidateIds,
                message_template: templateMsg
            })
        });
        
        if (response.ok) {
            // Show progress UI and poll progress every 500ms
            document.getElementById("blast-progress-section").classList.remove("hidden");
            document.getElementById("blast-console-logs").innerHTML = `<div class="terminal-line">Starting WhatsApp broadcast scheduler...</div>`;
            
            pollBlastStatus();
        } else {
            const data = await response.json();
            alert(`Error: ${data.message || "Failed to trigger broadcast"}`);
            sendBtn.disabled = false;
            cancelBtn.disabled = false;
        }
    } catch (e) {
        alert("Connection failed.");
        sendBtn.disabled = false;
        cancelBtn.disabled = false;
    }
}

function pollBlastStatus() {
    if (blastInterval) clearInterval(blastInterval);
    
    blastInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/wa/blast/status`);
            const state = await res.json();
            
            // Calculate progress percent
            const percent = state.total > 0 ? Math.round((state.current / state.total) * 100) : 0;
            document.getElementById("blast-progress-text").textContent = `Sending broadcast: ${state.current}/${state.total}`;
            document.getElementById("blast-progress-percent").textContent = `${percent}%`;
            document.getElementById("blast-progress-bar").style.width = `${percent}%`;
            
            // Success & failed labels
            document.getElementById("blast-success-label").textContent = state.success_count;
            document.getElementById("blast-failed-label").textContent = state.failed_count;
            
            // Render terminal logs
            const consoleBox = document.getElementById("blast-console-logs");
            consoleBox.innerHTML = "";
            state.logs.forEach(log => {
                consoleBox.insertAdjacentHTML("afterbegin", `<div class="terminal-line">${log}</div>`);
            });
            
            if (state.status !== "sending") {
                // Completed or error exited
                clearInterval(blastInterval);
                blastInterval = null;
                
                document.getElementById("btn-send-blast").disabled = false;
                document.getElementById("btn-cancel-blast").disabled = false;
                
                if (state.status === "complete") {
                    alert("WhatsApp Broadcast completed!");
                    // Reset selected checkboxes and counts
                    selectedCandidateIds = [];
                    updateBlastButtonState();
                    document.getElementById("check-all-candidates").checked = false;
                    closeBlastModal();
                    // Reload data
                    loadApplicants();
                } else if (state.status === "error") {
                    alert("WhatsApp Broadcast ended with errors. Please check GOWA connection.");
                }
            }
        } catch (e) {
            clearInterval(blastInterval);
            blastInterval = null;
            document.getElementById("btn-send-blast").disabled = false;
            document.getElementById("btn-cancel-blast").disabled = false;
        }
    }, 500);
}

// --- EXCEL DOWNLOADS ---
function exportExcel() {
    const search = document.getElementById("filter-search").value;
    const major = document.getElementById("filter-major").value;
    const position = document.getElementById("filter-position").value;
    
    const url = new URL(`${API_BASE}/api/export`);
    if (search) url.searchParams.append("search", search);
    if (major) url.searchParams.append("major", major);
    if (position) url.searchParams.append("position", position);
    
    // Check if running inside the native Desktop PyWebview wrapper
    if (window.pywebview && window.pywebview.api && window.pywebview.api.download_excel) {
        window.pywebview.api.download_excel(search, position, major).then(response => {
            if (response.status === "success") {
                alert(`Excel file successfully saved to:\n${response.path}`);
            } else if (response.status === "error") {
                alert(`Error saving file: ${response.message}`);
            }
        });
    } else {
        window.location.href = url.toString();
    }
}

// --- SYNC SECTION ---
async function loadSyncInfo() {
    try {
        const settingsRes = await fetch(`${API_BASE}/api/settings`);
        const settings = await settingsRes.json();
        document.getElementById("sync-active-email").textContent = settings.mentor_email;
        
        const banner = document.getElementById("sync-connection-banner");
        const syncBtn = document.getElementById("btn-start-sync");
        const sidebarStatus = document.getElementById("connection-status");
        
        const isOnline = await checkConnectivity();
        
        if (isOnline) {
            banner.className = "connection-banner online";
            banner.textContent = "Ready. Connection established to the mentor portal.";
            syncBtn.disabled = false;
            sidebarStatus.className = "status-indicator online";
            sidebarStatus.querySelector(".label").textContent = "Online";
        } else {
            banner.className = "connection-banner offline";
            banner.textContent = "Offline. Please connect to the internet to synchronize data.";
            syncBtn.disabled = true;
            sidebarStatus.className = "status-indicator offline";
            sidebarStatus.querySelector(".label").textContent = "Offline";
        }
        
        checkSyncRunningState();
        
    } catch (e) {
        console.error("Failed to load sync configurations:", e);
    }
}

async function checkConnectivity() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        if (res.ok) {
            await fetch("https://apply.inlifesurabaya.com/assets/logo_inlife.png", { method: "HEAD", mode: "no-cors", cache: "no-cache" });
            return true;
        }
        return false;
    } catch (e) {
        return false;
    }
}

async function checkSyncRunningState() {
    try {
        const res = await fetch(`${API_BASE}/api/sync/status`);
        const state = await res.json();
        if (state.status === "running") {
            showProgressUI();
            startPollingStatus();
        }
    } catch (e) {}
}

async function startSync() {
    const btn = document.getElementById("btn-start-sync");
    btn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/sync`, { method: "POST" });
        if (response.ok) {
            showProgressUI();
            startPollingStatus();
        } else {
            alert("Failed to start synchronization.");
            btn.disabled = false;
        }
    } catch (e) {
        alert("Server connection failed.");
        btn.disabled = false;
    }
}

function showProgressUI() {
    document.getElementById("sync-progress-area").classList.remove("hidden");
    document.getElementById("sync-console-logs").innerHTML = "<div class='terminal-line'>Connecting to mentor portal...</div>";
}

function startPollingStatus() {
    if (syncInterval) clearInterval(syncInterval);
    
    syncInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/sync/status`);
            const state = await res.json();
            
            const percent = state.total > 0 ? Math.round((state.current / state.total) * 100) : 0;
            document.getElementById("sync-progress-text").textContent = `Downloading profile: ${state.current}/${state.total}`;
            document.getElementById("sync-progress-percent").textContent = `${percent}%`;
            document.getElementById("sync-progress-bar").style.width = `${percent}%`;
            
            const consoleBox = document.getElementById("sync-console-logs");
            consoleBox.innerHTML = "";
            state.logs.forEach(log => {
                consoleBox.insertAdjacentHTML("afterbegin", `<div class="terminal-line">${log}</div>`);
            });
            
            if (state.status !== "running") {
                clearInterval(syncInterval);
                document.getElementById("btn-start-sync").disabled = false;
                if (state.status === "complete") {
                    alert("Synchronization completed successfully.");
                    filtersLoaded = false;
                } else if (state.status === "error") {
                    alert("Synchronization halted with errors. Check logs.");
                }
            }
        } catch (e) {
            clearInterval(syncInterval);
            document.getElementById("btn-start-sync").disabled = false;
        }
    }, 500);
}

// --- SETTINGS CONFIGURATIONS ---
async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/api/settings`);
        const data = await response.json();
        
        // Fill Mentor Credentials
        document.getElementById("settings-email").value = data.mentor_email || "";
        document.getElementById("settings-password").value = data.mentor_password || "";
        
        // Fill WhatsApp Settings
        document.getElementById("settings-wa-url").value = data.wa_api_url || "";
        document.getElementById("settings-wa-device").value = data.wa_device_id || "";
        document.getElementById("settings-wa-template").value = data.wa_template || "";
        document.getElementById("settings-wa-test-phone").value = data.wa_test_phone || "";
        document.getElementById("settings-wa-delay").value = data.wa_delay || "5";
        
        // Reset check box and clear button
        document.getElementById("confirm-cache-clear").checked = false;
        document.getElementById("btn-clear-cache").disabled = true;
        
    } catch (e) {
        console.error("Failed to load configuration values:", e);
    }
}

async function saveSettings(event) {
    event.preventDefault();
    const email = document.getElementById("settings-email").value;
    const password = document.getElementById("settings-password").value;
    
    try {
        const response = await fetch(`${API_BASE}/api/settings`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mentor_email: email, mentor_password: password })
        });
        
        if (response.ok) {
            alert("Mentor configurations successfully updated.");
            loadSettings();
        } else {
            alert("Failed to save configuration settings.");
        }
    } catch (e) {
        alert("Connection error.");
    }
}

async function saveWaSettings(event) {
    event.preventDefault();
    const url = document.getElementById("settings-wa-url").value;
    const device = document.getElementById("settings-wa-device").value;
    const template = document.getElementById("settings-wa-template").value;
    const testPhone = document.getElementById("settings-wa-test-phone").value;
    const delay = document.getElementById("settings-wa-delay").value;
    
    try {
        const response = await fetch(`${API_BASE}/api/settings`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                wa_api_url: url,
                wa_device_id: device,
                wa_template: template,
                wa_test_phone: testPhone,
                wa_delay: delay
            })
        });
        
        if (response.ok) {
            alert("WhatsApp GOWA configurations successfully updated.");
            loadSettings();
        } else {
            alert("Failed to save WhatsApp settings.");
        }
    } catch (e) {
        alert("Connection error.");
    }
}

async function sendTestWaMessage() {
    const url = document.getElementById("settings-wa-url").value;
    const device = document.getElementById("settings-wa-device").value;
    const template = document.getElementById("settings-wa-template").value;
    const testPhone = document.getElementById("settings-wa-test-phone").value;
    
    if (!testPhone.trim()) {
        alert("Masukkan nomor telepon tujuan uji coba terlebih dahulu.");
        return;
    }
    if (!url.trim()) {
        alert("Masukkan URL API GOWA terlebih dahulu.");
        return;
    }
    
    const btn = document.getElementById("btn-send-test-wa");
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="material-icons" style="font-size: 1.1rem; margin-right: 6px; vertical-align: middle;">sync</span><span style="vertical-align: middle;">Sending test...</span>`;
    
    try {
        const response = await fetch(`${API_BASE}/api/wa/test`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                phone: testPhone,
                wa_api_url: url,
                wa_device_id: device,
                message_template: template
            })
        });
        
        const result = await response.json();
        if (response.ok) {
            alert(`Uji coba sukses!\n${result.message}`);
        } else {
            alert(`Gagal mengirim pesan uji coba:\n${result.message}`);
        }
    } catch (e) {
        alert(`Terjadi error koneksi ke Flask server: ${e.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = origText;
    }
}

function toggleClearButton() {
    const isChecked = document.getElementById("confirm-cache-clear").checked;
    document.getElementById("btn-clear-cache").disabled = !isChecked;
}

async function clearCache() {
    if (!confirm("Are you sure you want to completely clear the SQLite cached candidates?")) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/clear`, { method: "POST" });
        if (response.ok) {
            alert("Local candidates database has been cleared.");
            loadSettings();
            filtersLoaded = false;
        } else {
            alert("Failed to clear database cache.");
        }
    } catch (e) {
        alert("Server error occurred.");
    }
}
