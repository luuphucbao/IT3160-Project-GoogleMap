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
    const mapWidth = 8900;
    const mapHeight = 7601;
    
    // Create map with CRS.Simple for pixel coordinates
    map = L.map('map', {
        crs: L.CRS.Simple,
        minZoom: -2,
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
        // Get scenario parameters
        const scenarioData = getScenarioData(currentScenario);
        
        // Prepare request data
        const requestData = {
            scenario_type: scenarioData.type,
            line_start: {
                lat: clickPoints[0][0],
                lng: clickPoints[0][1]
            },
            line_end: {
                lat: clickPoints[1][0],
                lng: clickPoints[1][1]
            },
            penalty_weight: scenarioData.penalty,
            threshold: scenarioData.threshold || 50
        };
        
        // TODO: Send to API when scenarios endpoint is ready
        // const response = await authManager.request('/api/scenarios', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify(requestData)
        // });
        
        // For now, just visualize the affected area
        const affectedZone = L.circle(
            [(clickPoints[0][0] + clickPoints[1][0]) / 2, 
             (clickPoints[0][1] + clickPoints[1][1]) / 2],
            {
                radius: scenarioData.threshold || 50,
                color: scenarioData.color,
                fillColor: scenarioData.color,
                fillOpacity: 0.3,
                weight: 2
            }
        ).addTo(map);
        
        scenarioLayers.push(affectedZone);
        
        updateStatus(`${scenarioData.name} applied successfully!`);
        
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
            penalty: 999,
            threshold: 20,
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
        // TODO: Call API to clear scenarios when endpoint is ready
        // await authManager.request('/api/scenarios/clear', { method: 'POST' });
        
        clearScenarioLayers();
        clearTempMarkers();
        clickPoints = [];
        currentScenario = null;
        
        scenarioButtons.forEach(b => b.classList.remove('active'));
        
        updateStatus('All scenarios cleared.');
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