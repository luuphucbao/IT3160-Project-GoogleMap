/**
 * Pathfinding UI Logic
 * Handles user interactions and API calls
 */

(function() {
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
const btnFoot = document.getElementById('btnFoot');
const btnCar = document.getElementById('btnCar');

// State
let selectingMode = null; // 'start' or 'end'
let currentPath = null;
let selectedVehicle = 'foot'; // Default vehicle

const SPEED_CAR = 11.1; // ~40 km/h in m/s
const SPEED_FOOT = 1.4; // ~5 km/h in m/s

/**
 * Initialize the application
 */
function init() {
    // Initialize map only if not already initialized (e.g. by admin.js)
    if (!MapModule.getMap()) {
        MapModule.init(AppConfig.MAP_IMAGE_URL_USER);
    }
    
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
    
    // Vehicle buttons
    btnCar.addEventListener('click', () => toggleVehicle('car', btnCar, btnFoot));
    btnFoot.addEventListener('click', () => toggleVehicle('foot', btnFoot, btnCar));

    // Map click handler
    MapModule.onMapClick((x, y) => {
        // ADMIN MODE CHECK: If we are in admin dashboard, only process click if Pathfinding tab is active
        const pathfindingTab = document.getElementById('tab-pathfinding');
        if (pathfindingTab && !pathfindingTab.classList.contains('active')) {
            return;
        }

        History.save(); // Save state before changing it
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

    // Listen for storage changes to auto-refresh path on scenario updates
    window.addEventListener('storage', (e) => {
        if (e.key === 'scenarios_updated') {
            // Kiểm tra xem có tọa độ hợp lệ không để tính lại, kể cả khi currentPath đang null (do bị Blocked)
            const sX = parseFloat(startXInput.value);
            const sY = parseFloat(startYInput.value);
            const eX = parseFloat(endXInput.value);
            const eY = parseFloat(endYInput.value);
            const hasCoords = !isNaN(sX) && !isNaN(sY) && !isNaN(eX) && !isNaN(eY);

            if (currentPath || hasCoords) {
                updateStatus('🔄 Scenarios updated by admin. Recalculating path...');
                findPath();
            }
        }
    });
}

/**
 * Handle Vehicle Toggle Logic
 */
function toggleVehicle(type, btnClicked, btnOther) {
    if (selectedVehicle === type) {
        // Nếu nhấn chọn thêm 1 lần nữa vào nút đang được chọn thì nút sẽ tắt
        selectedVehicle = null;
        btnClicked.classList.remove('active');
        updateStatus('⚠️ Chưa chọn phương tiện. Vui lòng chọn Car hoặc Foot.');
    } else {
        // Chọn phương tiện mới
        selectedVehicle = type;
        btnClicked.classList.add('active');
        btnOther.classList.remove('active');
        updateStatus(`Đang chọn ${type === 'car' ? 'Car' : 'Foot'}`);
        
        // Nếu đã có đường đi, tự động tìm lại đường mới với phương tiện mới
        if (currentPath) {
            findPath();
        }
    }
}

/**
 * Find optimal path between start and end points
 */

window.findPath = findPath; // Export for external use
async function findPath() {
    History.save(); // Save state before finding a new path
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

    if (!selectedVehicle) {
        updateStatus('⚠️ Vui lòng chọn phương tiện (Car hoặc Foot) để tìm đường.');
        return;
    }
    
    // Show loading
    showLoading(true);
    updateStatus('🔍 Finding optimal path...');
    
    const speed = selectedVehicle === 'car' ? SPEED_CAR : SPEED_FOOT;

    try {
        // ACTUAL API CALL: Fetch path from the backend service
        const response = await fetch(
            `${API_BASE_URL}/api/path?start_x=${startX}&start_y=${startY}&end_x=${endX}&end_y=${endY}&vehicle=${selectedVehicle}&speed=${speed}`
        );
        
        if (!response.ok) {
            // Attempt to read error detail from JSON response
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || 'Failed to find path');
        }
        
        const data = await response.json();
        
        if (data.cost === 'Blocked') {
            MapModule.clearPath();
            MapModule.addMarker(startX, startY, 'start');
            MapModule.addMarker(endX, endY, 'end');
            pathInfo.innerHTML = '<div style="text-align: center; color: #ef4444; font-weight: bold; font-size: 1.2em; padding: 10px;">Blocked</div>';
            updateStatus('⚠️ Path is blocked.');
            currentPath = null;
            return;
        }
        
        // Draw path on map
        MapModule.drawPath(data.path);
        
        // Update path information
        displayPathInfo(data);
        
        currentPath = data;
        updateStatus('✅ Path found successfully!');
        
    } catch (error) {
        console.error('Error finding path:', error);
        MapModule.clearPath();
        MapModule.addMarker(startX, startY, 'start');
        MapModule.addMarker(endX, endY, 'end');
        pathInfo.innerHTML = '<div style="text-align: center; color: #ef4444; font-weight: bold; font-size: 1.2em; padding: 10px;">No path found</div>';
        updateStatus(`❌ Error finding path: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

/**
 * Generate mock path data for demonstration
 */
/*
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
*/
/**
 * Display path information
 */
function displayPathInfo(data) {
    // Convert seconds to minutes and seconds
    const totalSeconds = parseFloat(data.cost);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = Math.round(totalSeconds % 60);
    const timeDisplay = minutes > 0 
        ? `${minutes} phút ${seconds} giây` 
        : `${seconds} giây`;

    pathInfo.innerHTML = `
        <div class="info-item">
            <span class="info-label">Distance (mét):</span>
            <span class="info-value">${data.distance}</span>
        </div>
        <div class="info-item">
            <span class="info-label">Nodes:</span>
            <span class="info-value">${data.nodes}</span>
        </div>
        <div class="info-item">
            <span class="info-label">Time:</span>
            <span class="info-value">${timeDisplay}</span>
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
    History.save(); // Save state before clearing
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
    
    // Note: "Khi nút đã được chọn thì sẽ không tắt cho đến khi bị chọn sang phương tiện khác"
    // So we do NOT reset selectedVehicle here.
    // But if we wanted to reset to default:
    // selectedVehicle = 'foot';
    // document.getElementById('btnFoot').classList.add('active');
    // document.getElementById('btnCar').classList.remove('active');
    
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
})();