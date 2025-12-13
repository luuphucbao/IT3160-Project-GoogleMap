/**
 * Admin Dashboard JavaScript
 * Handles login UI, map initialization, and scenario management
 */

// DOM Elements
const loginModal = document.getElementById('loginModal');
const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const adminDashboard = document.getElementById('adminDashboard');
const welcomeMessage = document.getElementById('welcomeMessage');
const logoutBtn = document.getElementById('logoutBtn');
const statusMessage = document.getElementById('statusMessage');
const scenarioButtons = document.querySelectorAll('.btn-scenario');
const clearAllBtn = document.getElementById('clearAllBtn');
const toggleDeleteBtn = document.getElementById('toggleDeleteBtn');

// State
let map;
let currentScenario = null;
let clickPoints = [];
let tempMarkers = [];
let scenarioHistory = [];
let isDeleteMode = false;

/**
 * Initialize the application
 */
async function init() {
    // Check if user is already logged in
    if (authManager.isAuthenticated()) {
        const isValid = await authManager.verifyToken();
        if (isValid) {
            showDashboard();
            return;
        }
    }
    
    // Show login modal
    showLogin();
}

/**
 * Show login modal
 */
function showLogin() {
    loginModal.style.display = 'flex';
    adminDashboard.style.display = 'none';
}

/**
 * Show admin dashboard
 */
function showDashboard() {
    loginModal.style.display = 'none';
    adminDashboard.style.display = 'block';
    
    // Update welcome message
    welcomeMessage.textContent = `Welcome, ${authManager.getUsername()}`;
    
    // Initialize map if not already done
    if (!map) {
        initMap();
    }

    // Load existing scenarios from the backend
    loadAndDrawScenarios();
}

/**
 * Initialize Leaflet map with local image
 */
function initMap() {
    // Create map with CRS.Simple for pixel coordinates
    map = L.map('map', {
        crs: L.CRS.Simple,
        minZoom: -3,
        maxZoom: 2,
        zoomSnap: 0.25,
        zoomDelta: 0.25
    });
    
    // Calculate bounds for the image
    // Leaflet uses [y, x] format, so [height, width]
    const bounds = [[0, 0], [AppConfig.MAP_HEIGHT, AppConfig.MAP_WIDTH]];
    
    // Set the map bounds to prevent dragging outside the image
    map.setMaxBounds(bounds);
    map.on('drag', function() {
        map.panInsideBounds(bounds, { animate: false });
    });

    // Add the local map image
    L.imageOverlay(AppConfig.MAP_IMAGE_URL_ADMIN, bounds).addTo(map);
    
    // Set the map bounds
    map.fitBounds(bounds);
    
    // Set initial view to center of map
    map.setView([AppConfig.MAP_HEIGHT / 2, AppConfig.MAP_WIDTH / 2], -1);
    
    // Add click handler for scenario drawing
    map.on('click', onMapClick);
    
    updateStatus('Map initialized. Select a scenario to begin.');
}

/**
 * Handle login form submission
 */
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    // Clear previous error
    loginError.textContent = '';
    loginError.classList.remove('show');
    
    // Disable submit button
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Logging in...';
    
    // Attempt login
    const result = await authManager.login(username, password);
    
    if (result.success) {
        showDashboard();
    } else {
        loginError.textContent = result.error;
        loginError.classList.add('show');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Login';
    }
});

logoutBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to logout?')) {
        await authManager.logout();
        
        // Reload the page to ensure all state is reset and the user is shown the login screen
        window.location.reload();
    }
});

/**
 * Handle toggle delete mode button
 */
toggleDeleteBtn.addEventListener('click', () => {
    isDeleteMode = !isDeleteMode;

    if (isDeleteMode) {
        // De-select any active scenario when entering delete mode
        currentScenario = null;
        scenarioButtons.forEach(b => b.classList.remove('active'));
        clearTempMarkers();
        clickPoints = [];
    }

    updateDeleteModeUI();
});

/**
 * Handle scenario button clicks
 */
scenarioButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        // PREVENT SCENARIO SELECTION IF IN DELETE MODE
        if (isDeleteMode) {
            updateStatus('Cannot add new scenarios while in Delete Mode. Disable it first.');
            // Ensure no scenario is active
            scenarioButtons.forEach(b => b.classList.remove('active'));
            currentScenario = null;
            return; // Stop further execution
        }

        const isAlreadyActive = btn.classList.contains('active');

        // Luôn xóa các điểm và marker tạm thời khi có tương tác với nút kịch bản
        clickPoints = [];
        clearTempMarkers();

        // Xóa trạng thái active khỏi tất cả các nút
        scenarioButtons.forEach(b => b.classList.remove('active'));

        if (isAlreadyActive) {
            // Nếu nút đã được chọn, hủy chọn nó
            currentScenario = null;
            updateStatus('Đã hủy chọn kịch bản. Chọn một kịch bản để bắt đầu.');
        } else {
            // Nếu nút chưa được chọn, hãy kích hoạt nó
            btn.classList.add('active');
            currentScenario = btn.dataset.scenario;
            updateStatus(`${btn.textContent.trim()} đã được chọn. Nhấp vào hai điểm trên bản đồ để xác định khu vực bị ảnh hưởng.`);
        }
    });
});

/**
 * Handle map clicks for scenario drawing
 */
function onMapClick(e) {
    if (isDeleteMode) return; // Do nothing if in delete mode

    if (!currentScenario) {
        updateStatus('Please select a scenario first.');
        return;
    }
    
    if (clickPoints.length >= 2) {
        // Reset if already have 2 points
        clickPoints = [];
        clearTempMarkers();
        updateStatus('Click two points to define affected area.');
        return;
    }
    
    // Add point
    clickPoints.push([e.latlng.lat, e.latlng.lng]);
    
    // Add marker
    const marker = L.circleMarker(e.latlng, {
        radius: 8,
        fillColor: '#667eea',
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map);
    
    tempMarkers.push(marker);
    
    if (clickPoints.length === 1) {
        updateStatus('Click second point to complete the area.');
    } else if (clickPoints.length === 2) {
        // Draw line between points
        const line = L.polyline(clickPoints, {
            color: '#667eea',
            weight: 3,
            opacity: 0.7,
            dashArray: '10, 10'
        }).addTo(map);
        
        tempMarkers.push(line);
        
        // Apply scenario
        applyScenario();
    }
}

function updateDeleteModeUI() {
    const activeClass = 'active'; // A class to indicate active state
    
    if (isDeleteMode) {
        toggleDeleteBtn.textContent = 'Disable Delete Mode';
        toggleDeleteBtn.classList.add(activeClass);
        map.getContainer().style.cursor = 'crosshair';
        
        // Update style of existing layers to indicate they are deletable
        scenarioHistory.forEach(scenario => {
            if (scenario.layer && scenario.layer.setStyle) {
                scenario.layer.setStyle({ dashArray: '5, 5'}); // A noticeable red
            }
        });
        
        updateStatus('Delete mode enabled. Click a scenario on the map to remove it.');
    } else {
        toggleDeleteBtn.textContent = 'Enable Delete Mode';
        toggleDeleteBtn.classList.remove(activeClass);
        map.getContainer().style.cursor = '';
        
        // Revert style for existing layers
        scenarioHistory.forEach(scenario => {
            if (scenario.layer && scenario.layer.setStyle) {
                // Get original color from the scenario data mapping
                const scenarioData = getScenarioData(scenario.scenarioKey);
                scenario.layer.setStyle({
                    dashArray: null,
                    color: scenarioData.color
                });
            }
        });
        
        updateStatus('Delete mode disabled.');
    }
}

/**
 * Handle click on a scenario layer to delete it
 */
function onScenarioClick(e) {
    // Only allow deletion if delete mode is active
    if (!isDeleteMode) return;

    // Stop the click from propagating to the map, which would trigger onMapClick
    L.DomEvent.stopPropagation(e);

    // `this` refers to the layer that was clicked
    const clickedLayer = this;

    // Use a confirmation dialog
    if (!confirm('Are you sure you want to delete this specific scenario?')) {
        return;
    }

    // Find the index of the scenario in our history array
    const scenarioIndex = scenarioHistory.findIndex(scenario => scenario.layer === clickedLayer);

    if (scenarioIndex > -1) {
        // Remove the layer from the map
        map.removeLayer(clickedLayer);

        // Remove the scenario from our history array
        scenarioHistory.splice(scenarioIndex, 1);

        // Resynchronize the backend state
        updateStatus('Deleting scenario and resyncing...');
        resyncBackendScenarios(); // This function will clear the backend and re-add the remaining scenarios
    } else {
        console.error("Could not find the clicked scenario in the history.");
        updateStatus("Error: Could not delete the scenario.");
    }
}

/**
 * Apply selected scenario
 */
async function applyScenario() {
    updateStatus('Applying scenario...');
    
    try {
        const scenarioData = getScenarioData(currentScenario);
        
        // Lấy toạ độ 2 điểm click
        const p1 = { lat: clickPoints[0][0], lng: clickPoints[0][1] };
        const p2 = { lat: clickPoints[1][0], lng: clickPoints[1][1] };
        
        let apiStart = p1;
        let apiEnd = p2;
        let apiThreshold = scenarioData.threshold || 50;
        
        // --- LOGIC 1: XỬ LÝ TOÁN HỌC CHO MƯA ---
        let visualCenter = clickPoints[0]; // Mặc định tâm là điểm đầu
        let visualRadius = apiThreshold;   // Mặc định bán kính là threshold cố định

        if (scenarioData.type === 'rain') {
            // 1. Tính TRUNG ĐIỂM (Tâm của hình tròn)
            const midLat = (p1.lat + p2.lat) / 2;
            const midLng = (p1.lng + p2.lng) / 2;
            const centerPoint = { lat: midLat, lng: midLng };

            // 2. Tính KHOẢNG CÁCH P1-P2 (Đường kính)
            const dx = p1.lng - p2.lng;
            const dy = p1.lat - p2.lat;
            const diameter = Math.sqrt(dx*dx + dy*dy);
            
            // 3. Bán kính = Đường kính / 2
            const radius = diameter / 2;

            // Cập nhật dữ liệu để gửi API & Vẽ
            // Gửi start = end = tâm để Backend hiểu là "nguồn điểm" (Point Source)
            apiStart = centerPoint;
            apiEnd = centerPoint; 
            apiThreshold = radius; // Threshold bây giờ là bán kính động
            
            // Dữ liệu để vẽ lên bản đồ
            visualCenter = [midLat, midLng];
            visualRadius = radius;
        }

        // Chuẩn bị dữ liệu gửi đi
        const requestData = {
            scenario_type: scenarioData.type,
            line_start: apiStart,
            line_end: apiEnd,
            penalty_weight: scenarioData.penalty,
            threshold: apiThreshold
        };
        
        // Gọi API
        const response = await authManager.request('/api/scenarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) throw new Error('Failed to apply scenario');
        const data = await response.json();
        
        // --- LOGIC 2: VẼ LẠI (VISUALIZATION) ---
        let visualLayer;
        
        if (scenarioData.type === 'rain') {
            // Vẽ Mưa: Hình tròn tại Trung điểm với Bán kính = 1/2 đoạn kéo
            visualLayer = L.circle(visualCenter, {
                radius: visualRadius,
                color: scenarioData.color,
                fillColor: scenarioData.color,
                fillOpacity: 0.3,
                weight: 2
            });
        } else {
            // Vẽ Chặn đường: Chỉ vẽ ĐƯỜNG THẲNG (Đã bỏ hình tròn ở giữa)
            visualLayer = L.polyline(clickPoints, { 
                color: 'red', 
                weight: 5 
            });
        }
        
        visualLayer.on('click', onScenarioClick);
        visualLayer.addTo(map);

        // If in delete mode, apply the deletable style immediately
        if (isDeleteMode) {
            if (visualLayer.setStyle) {
                visualLayer.setStyle({ dashArray: '5, 5', color: '#e53e3e' });
            }
        }
        scenarioHistory.push({
            layer: visualLayer,
            request: requestData,
            response: data,
            scenarioKey: currentScenario
        });
        
        updateStatus(`${scenarioData.name} applied! Affected ${data.affected_edges} edges.`);
        
        // Clear temp markers and reset
        clearTempMarkers();
        clickPoints = [];
        
        // // Deactivate scenario button
        // scenarioButtons.forEach(b => b.classList.remove('active'));
        // currentScenario = null;

        // Signal other tabs that scenarios have changed
        localStorage.setItem('scenarios_updated', new Date().toISOString());
        
    } catch (error) {
        console.error('Error applying scenario:', error);
        updateStatus('Error applying scenario. Please try again.');
    }
}

/**
 * Get scenario configuration
 */
function getScenarioData(scenario) {
    const scenarios = {
        'rain-light': {
            name: 'Light Rain',
            type: 'rain',
            penalty: 1.2,
            threshold: 30,
            // Đổi sang màu xanh da trời sáng (Sky Blue) để tạo cảm giác nhẹ nhàng
            color: '#60a5fa' 
        },
        'rain-medium': {
            name: 'Medium Rain',
            type: 'rain',
            penalty: 1.5,
            threshold: 50,
            // Màu xanh dương tiêu chuẩn, rực rỡ và dễ nhìn
            color: '#2563eb' 
        },
        'rain-heavy': {
            name: 'Heavy Rain',
            type: 'rain',
            penalty: 2.0,
            threshold: 70,
            // Màu xanh đậm hơn hẳn, báo hiệu mức độ nghiêm trọng
            color: '#14358eff' 
        },
        'rain-extreme': {
            name: 'Extreme Rain',
            type: 'rain',
            penalty: 3.0,
            threshold: 100,
            // Màu xanh tím than (gần như đen), tạo cảm giác bão tố/nguy hiểm
            color: '#663adfff' 
        },
        'road-block': {
            name: 'Road Block',
            type: 'block',
            penalty: 10000,
            threshold: 50,
            // Giữ nguyên màu đỏ cảnh báo, hoặc dùng màu đỏ cam sáng hơn (#ef4444 là ok)
            color: '#ef4444' 
        }
    };
    
    if (scenario) {
        return scenarios[scenario] || scenarios['rain-light'];
    }
    return scenarios; // Return all if no specific scenario is requested
}

/**
 * Helper function to find scenario key by penalty and type
 */
function findScenarioKey(penalty, type) {
    const scenarios = getScenarioData(); // Get all scenarios
    for (const key in scenarios) {
        if (scenarios[key].type === type && scenarios[key].penalty === penalty) {
            return key;
        }
    }
    // Fallback for road-block or if not found
    return type === 'block' ? 'road-block' : 'rain-light'; 
}

/**
 * Load existing scenarios from the backend and draw them on the map
 */
async function loadAndDrawScenarios() {
    try {
        updateStatus('Loading existing scenarios...');
        const response = await authManager.request('/api/scenarios/');
        if (!response.ok) {
            throw new Error('Could not fetch scenarios.');
        }

        const scenarios = await response.json();

        // Clear any local scenarios before loading from backend
        clearScenarioHistory();
        
        if (scenarios.length === 0) {
            updateStatus('No active scenarios found. Select a scenario to begin.');
            return;
        }

        for (const scenario of scenarios) {
            const scenarioKey = findScenarioKey(scenario.penalty_weight, scenario.scenario_type);
            const scenarioData = getScenarioData(scenarioKey);
            
            let visualLayer;
            let clickPoints = [[scenario.line_start.lat, scenario.line_start.lng], [scenario.line_end.lat, scenario.line_end.lng]];

            if (scenario.scenario_type === 'rain') {
                // For rain, API returns center point as start/end, and radius as threshold
                const visualCenter = [scenario.line_start.lat, scenario.line_start.lng];
                const visualRadius = scenario.threshold;
                visualLayer = L.circle(visualCenter, {
                    radius: visualRadius,
                    color: scenarioData.color,
                    fillColor: scenarioData.color,
                    fillOpacity: 0.3,
                    weight: 2
                });
            } else { // block
                visualLayer = L.polyline(clickPoints, { 
                    color: 'red', 
                    weight: 5 
                });
            }
            
            visualLayer.on('click', onScenarioClick);
            visualLayer.addTo(map);

            // If in delete mode, apply the deletable style immediately
            if (isDeleteMode) {
                if (visualLayer.setStyle) {
                    visualLayer.setStyle({ dashArray: '5, 5', color: '#e53e3e' });
                }
            }

            // Reconstruct the scenario object to store in history
            const historyItem = {
                layer: visualLayer,
                // The request object from the backend is what we need
                request: {
                    scenario_type: scenario.scenario_type,
                    line_start: scenario.line_start,
                    line_end: scenario.line_end,
                    penalty_weight: scenario.penalty_weight,
                    threshold: scenario.threshold
                },
                response: { /* We don't have this, but it's not critical for deletion */ },
                scenarioKey: scenarioKey
            };
            scenarioHistory.push(historyItem);
        }

        updateStatus(`Loaded ${scenarios.length} active scenarios.`);

    } catch (error) {
        console.error('Error loading scenarios:', error);
        updateStatus('Failed to load existing scenarios.');
    }
}

/**
 * Clear temporary markers
 */
function clearTempMarkers() {
    tempMarkers.forEach(marker => map.removeLayer(marker));
    tempMarkers = [];
}

/**
 * Clear all scenario layers
 */
function clearScenarioHistory() {
    scenarioHistory.forEach(scenario => map.removeLayer(scenario.layer));
    scenarioHistory = [];
}

/**
 * Handle clear all button
 */
clearAllBtn.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear all scenarios?')) {
        return;
    }
    
    try {
        updateStatus('Clearing scenarios...');
        
        // Bước 1: Gọi API xóa toàn bộ (Backend đã hỗ trợ endpoint DELETE /api/scenarios/)
        // Việc này nhanh hơn nhiều so với xóa từng cái vì không phải tính lại trọng số nhiều lần
        const response = await authManager.request('/api/scenarios/', { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to clear scenarios');
        
        // Bước 2: Dọn dẹp giao diện
        clearScenarioHistory();
        clearTempMarkers();
        clickPoints = [];
        currentScenario = null;
        
        scenarioButtons.forEach(b => b.classList.remove('active'));

        // If in delete mode, disable it since there's nothing left to delete
        if (isDeleteMode) {
            isDeleteMode = false;
            updateDeleteModeUI();
        }
        
        updateStatus(`All scenarios cleared successfully.`);

        // Signal other tabs that scenarios have changed
        localStorage.setItem('scenarios_updated', new Date().toISOString());
    } catch (error) {
        console.error('Error clearing scenarios:', error);
        updateStatus('Error clearing scenarios. Please try again.');
    }
});

/**
 * Update status message
 */
function updateStatus(message) {
    statusMessage.textContent = message;
}

/**
 * Resync all scenarios with the backend.
 * This is done by clearing all scenarios on the backend and then re-adding them.
 */
async function resyncBackendScenarios() {
    // 1. Clear all scenarios on the backend
    try {
        await authManager.request('/api/scenarios/', { method: 'DELETE' });
    } catch (error) {
        console.error('Failed to clear scenarios during resync:', error);
        updateStatus('Error during undo operation. Scenarios may be out of sync.');
        return;
    }

    // 2. Re-apply all scenarios from history
    const scenariosToReapply = [...scenarioHistory]; // Create a copy

    for (const scenario of scenariosToReapply) {
        try {
            // We don't need to do anything with the response here
            await authManager.request('/api/scenarios', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scenario.request)
            });
        } catch (error) {
            console.error('Failed to re-apply a scenario during resync:', error);
            // If one fails, we should probably stop and alert the user
            updateStatus('Error re-applying scenarios after undo. State might be inconsistent.');
            return; // Stop processing further
        }
    }

    // Signal other tabs that scenarios have changed
    localStorage.setItem('scenarios_updated', new Date().toISOString());
    updateStatus(`Undo successful. ${scenarioHistory.length} scenarios active.`);
}

/**
 * Undo the last added scenario
 */
async function undoLastScenario() {
    if (scenarioHistory.length === 0) {
        updateStatus('Nothing to undo.');
        return;
    }

    updateStatus('Undoing last scenario...');

    // 1. Remove from history and map
    const lastScenario = scenarioHistory.pop();
    if (lastScenario && lastScenario.layer) {
        map.removeLayer(lastScenario.layer);
    }

    // 2. Resync backend
    await resyncBackendScenarios();
}


// Add keyboard listener for Ctrl+Z
document.addEventListener('keydown', function(event) {
    // Check if the login modal is hidden, so we don't undo while typing username/password
    if (loginModal.style.display === 'none' && event.ctrlKey && event.key === 'z') {
        event.preventDefault();
        undoLastScenario();
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);