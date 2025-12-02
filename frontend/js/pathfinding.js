/**
 * Pathfinding UI Logic
 * Handles user interactions and API calls
 */

const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const startXInput = document.getElementById('startX');
const startYInput = document.getElementById('startY');
const endXInput = document.getElementById('endX');
const endYInput = document.getElementById('endY');
const selectStartBtn = document.getElementById('selectStartBtn');
const selectEndBtn = document.getElementById('selectEndBtn');
const findPathBtn = document.getElementById('findPathBtn');
const clearBtn = document.getElementById('clearBtn');
const pathInfo = document.getElementById('pathInfo');
const statusMessage = document.getElementById('statusMessage');
const loadingOverlay = document.getElementById('loadingOverlay');

// NEW: DOM Element for the Show Nodes button
const showNodesBtn = document.getElementById('showNodesBtn'); 

// State
let selectingMode = null; // 'start' or 'end'
let currentPath = null;
let nodesShown = false; // <-- NEW: State to track node visibility

/**
 * Initialize the application
 */
function init() {
    // Initialize map
    MapModule.init();
    
    // Setup event listeners
    setupEventListeners();
    
    updateStatus('Ready. Click on the map or enter coordinates to begin.');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Select start button
    selectStartBtn.addEventListener('click', () => {
        selectingMode = 'start';
        selectStartBtn.classList.add('active');
        selectEndBtn.classList.remove('active');
        updateStatus('Click on the map to select START point.');
    });
    
    // Select end button
    selectEndBtn.addEventListener('click', () => {
        selectingMode = 'end';
        selectEndBtn.classList.add('active');
        selectStartBtn.classList.remove('active');
        updateStatus('Click on the map to select END point.');
    });
    
    // Find path button
    findPathBtn.addEventListener('click', findPath);
    
    // Clear button
    clearBtn.addEventListener('click', clearAll);
    
    // NEW: Toggle Nodes button
    showNodesBtn.addEventListener('click', toggleShowNodes); 
    
    // Map click handler
    MapModule.onMapClick((x, y) => {
        if (selectingMode === 'start') {
            startXInput.value = Math.round(x);
            startYInput.value = Math.round(y);
            MapModule.addMarker(x, y, 'start');
            selectStartBtn.classList.remove('active');
            selectingMode = null;
            updateStatus('Start point selected. Now select END point.');
        } else if (selectingMode === 'end') {
            endXInput.value = Math.round(x);
            endYInput.value = Math.round(y);
            MapModule.addMarker(x, y, 'end');
            selectEndBtn.classList.remove('active');
            selectingMode = null;
            updateStatus('End point selected. Click "Find Optimal Path" to calculate route.');
        }
    });
}

/**
 * Find optimal path between start and end points
 */
async function findPath() {
    // Validate inputs
    const startX = parseFloat(startXInput.value);
    const startY = parseFloat(startYInput.value);
    const endX = parseFloat(endXInput.value);
    const endY = parseFloat(endYInput.value);
    
    if (isNaN(startX) || isNaN(startY)) {
        updateStatus('❌ Please select or enter a valid START point.');
        return;
    }
    
    if (isNaN(endX) || isNaN(endY)) {
        updateStatus('❌ Please select or enter a valid END point.');
        return;
    }
    
    // Show loading
    showLoading(true);
    updateStatus('🔍 Finding optimal path...');
    
    try {
        // ACTUAL API CALL: Fetch path from the backend service
        const response = await fetch(
            `${API_BASE_URL}/api/path?start_x=${startX}&start_y=${startY}&end_x=${endX}&end_y=${endY}`
        );
        
        if (!response.ok) {
            // Attempt to read error detail from JSON response
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || 'Failed to find path');
        }
        
        const data = await response.json();
        
        // Draw path on map
        MapModule.drawPath(data.path);
        
        // Update path information
        displayPathInfo(data);
        
        currentPath = data;
        updateStatus('✅ Path found successfully!');
        
    } catch (error) {
        console.error('Error finding path:', error);
        
        // Display the specific error detail if available
        const errorMessage = error.message.startsWith('Failed') 
            ? 'Could not calculate path. Make sure start/end points are near valid nodes.' 
            : error.message;
            
        updateStatus(`❌ Error finding path: ${errorMessage}`);
        showErrorInfo(errorMessage);
    } finally {
        showLoading(false);
    }
}

/**
 * NEW: Toggle visibility of all nodes from the database
 */
function toggleShowNodes() {
    if (nodesShown) {
        // Hide nodes
        MapModule.clearNodes();
        showNodesBtn.textContent = '🟠 Toggle All Nodes';
        showNodesBtn.style.backgroundColor = '#f97316';
        updateStatus('Nodes ẩn. Sẵn sàng.');
        nodesShown = false;
    } else {
        // Show nodes
        fetchAndShowNodes();
    }
}


/**
 * NEW: Fetch all nodes from API and display them on the map
 */
async function fetchAndShowNodes() {
    showLoading(true);
    updateStatus('⏳ Đang tải dữ liệu nodes...');

    try {
        // Assuming API endpoint is /nodes as discussed
        const response = await fetch(`${API_BASE_URL}/api/nodes`); 
        
        if (!response.ok) {
            throw new Error(`API call failed with status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.nodes && data.nodes.length > 0) {
            // Use the exported function from MapModule (already in map.js)
            const correctedNodes = data.nodes.map(node => ({ ...node, y: 7801 - node.y }));

            // Use the exported function from MapModule (already in map.js)
            MapModule.showAllNodes(correctedNodes);
            
            nodesShown = true;
            showNodesBtn.textContent = '✅ Hide All Nodes';
            showNodesBtn.style.backgroundColor = '#10b981'; // Green color for active state
            updateStatus(`✅ Đã tải và hiển thị ${data.nodes.length} nodes.`);
        } else {
            updateStatus('⚠️ Không tìm thấy nodes nào trong cơ sở dữ liệu.');
        }

    } catch (error) {
        console.error('Error fetching and showing nodes:', error);
        updateStatus('❌ Lỗi khi tải nodes. Vui lòng kiểm tra API server (endpoint /nodes).');
    } finally {
        showLoading(false);
    }
}


/**
 * Generate mock path data for demonstration
 */
function generateMockPath(startX, startY, endX, endY) {
    // Generate some intermediate points for a curved path
    const numPoints = 5;
    const path = [];
    
    for (let i = 0; i <= numPoints; i++) {
        const t = i / numPoints;
        const x = startX + (endX - startX) * t + Math.sin(t * Math.PI) * 200;
        const y = startY + (endY - startY) * t + Math.cos(t * Math.PI) * 200;
        
        path.push({ x, y });
    }
    
    // Calculate mock distance
    const distance = Math.sqrt(
        Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2)
    );
    
    return {
        path: path,
        distance: distance.toFixed(2),
        nodes: numPoints + 1,
        cost: (distance / 100).toFixed(2)
    };
}

/**
 * Display path information
 */
function displayPathInfo(data) {
    pathInfo.innerHTML = `
        <div class="info-item">
            <span class="info-label">Distance:</span>
            <span class="info-value">${data.distance} pixels</span>
        </div>
        <div class="info-item">
            <span class="info-label">Nodes:</span>
            <span class="info-value">${data.nodes}</span>
        </div>
        <div class="info-item">
            <span class="info-label">Cost:</span>
            <span class="info-value">${data.cost}</span>
        </div>
    `;
}

/**
 * Show error in path info panel
 */
function showErrorInfo(message) {
    pathInfo.innerHTML = `<p style="color: #ef4444; text-align: center;">${message}</p>`;
}

/**
 * Clear all selections and path
 */
function clearAll() {
    // Clear inputs
    startXInput.value = '';
    startYInput.value = '';
    endXInput.value = '';
    endYInput.value = '';
    
    // Clear map
    MapModule.clearPath();
    
    // Clear path info
    pathInfo.innerHTML = '<p class="no-data">No path calculated yet</p>';
    
    // Reset state
    selectingMode = null;
    currentPath = null;
    selectStartBtn.classList.remove('active');
    selectEndBtn.classList.remove('active');
    
    // Clear nodes if shown
    if (nodesShown) {
        MapModule.clearNodes();
        nodesShown = false;
        showNodesBtn.textContent = '🟠 Toggle All Nodes';
        showNodesBtn.style.backgroundColor = '#f97316';
    }
    
    updateStatus('Ready. Click on the map or enter coordinates to begin.');
}

/**
 * Update status message
 */
function updateStatus(message) {
    statusMessage.textContent = message;
}

/**
 * Show/hide loading overlay
 */
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);