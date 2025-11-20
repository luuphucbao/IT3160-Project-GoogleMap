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

// State
let selectingMode = null; // 'start' or 'end'
let currentPath = null;

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
        // TODO: Replace with actual API call when pathfinding endpoint is ready
        // For now, simulate API call with mock data
        
        // const response = await fetch(
        //     `${API_BASE_URL}/api/path?start_x=${startX}&start_y=${startY}&end_x=${endX}&end_y=${endY}`
        // );
        // 
        // if (!response.ok) {
        //     throw new Error('Failed to find path');
        // }
        // 
        // const data = await response.json();
        
        // Mock data for demonstration
        await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate API delay
        
        const data = generateMockPath(startX, startY, endX, endY);
        
        // Draw path on map
        MapModule.drawPath(data.path);
        
        // Update path information
        displayPathInfo(data);
        
        currentPath = data;
        updateStatus('✅ Path found successfully!');
        
    } catch (error) {
        console.error('Error finding path:', error);
        updateStatus('❌ Error finding path. Please try again.');
        showErrorInfo('Could not calculate path. Please ensure start and end points are valid.');
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