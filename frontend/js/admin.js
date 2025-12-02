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

// State
let map;
let currentScenario = null;
let clickPoints = [];
let tempMarkers = [];
let scenarioLayers = [];

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
}

/**
 * Initialize Leaflet map with local image
 */
function initMap() {
    // Map image dimensions (8900 x 7601 pixels from your document)
    const mapWidth = 8500;
    const mapHeight = 7801;
    
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
    const bounds = [[0, 0], [mapHeight, mapWidth]];
    
    // Add the local map image
    L.imageOverlay('../map/fixed.png', bounds).addTo(map);
    
    // Set the map bounds
    map.fitBounds(bounds);
    
    // Set initial view to center of map
    map.setView([mapHeight / 2, mapWidth / 2], -1);
    
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

/**
 * Handle logout
 */
logoutBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to logout?')) {
        await authManager.logout();
        
        // Reset state
        currentScenario = null;
        clickPoints = [];
        clearTempMarkers();
        clearScenarioLayers();
        
        showLogin();
    }
});

/**
 * Handle scenario button clicks
 */
scenarioButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all buttons
        scenarioButtons.forEach(b => b.classList.remove('active'));
        
        // Add active class to clicked button
        btn.classList.add('active');
        
        // Set current scenario
        currentScenario = btn.dataset.scenario;
        
        // Reset click points
        clickPoints = [];
        clearTempMarkers();
        
        updateStatus(`${btn.textContent.trim()} selected. Click two points on the map to define affected area.`);
    });
});

/**
 * Handle map clicks for scenario drawing
 */
function onMapClick(e) {
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
        
        visualLayer.addTo(map);
        scenarioLayers.push(visualLayer);
        
        updateStatus(`${scenarioData.name} applied! Affected ${data.affected_edges} edges.`);
        
        // Clear temp markers and reset
        clearTempMarkers();
        clickPoints = [];
        
        // Deactivate scenario button
        scenarioButtons.forEach(b => b.classList.remove('active'));
        currentScenario = null;
        
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
            penalty: 0.5,
            threshold: 30,
            color: '#3b82f6'
        },
        'rain-medium': {
            name: 'Medium Rain',
            type: 'rain',
            penalty: 1.0,
            threshold: 50,
            color: '#2563eb'
        },
        'rain-heavy': {
            name: 'Heavy Rain',
            type: 'rain',
            penalty: 2.0,
            threshold: 70,
            color: '#1e40af'
        },
        'rain-extreme': {
            name: 'Extreme Rain',
            type: 'rain',
            penalty: 5.0,
            threshold: 100,
            color: '#1e3a8a'
        },
        'road-block': {
            name: 'Road Block',
            type: 'block',
            penalty: 9999,
            threshold: 50,
            color: '#ef4444'
        }
    };
    
    return scenarios[scenario] || scenarios['rain-light'];
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
function clearScenarioLayers() {
    scenarioLayers.forEach(layer => map.removeLayer(layer));
    scenarioLayers = [];
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
        
        // Bước 1: Lấy danh sách ID
        const listResponse = await authManager.request('/api/scenarios');
        const scenarios = await listResponse.json();
        
        // Bước 2: Loop xoá từng ID
        // (Cách này hơi chậm nhưng an toàn nếu Backend chưa có hàm delete-all)
        let successCount = 0;
        for (const s of scenarios) {
            await authManager.request(`/api/scenarios/${s.id}`, { method: 'DELETE' });
            successCount++;
        }
        
        // Bước 3: Dọn dẹp giao diện
        clearScenarioLayers();
        clearTempMarkers();
        clickPoints = [];
        currentScenario = null;
        
        scenarioButtons.forEach(b => b.classList.remove('active'));
        
        updateStatus(`Cleared ${successCount} scenarios successfully.`);
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);