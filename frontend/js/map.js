/**
 * Map Module for User View
 * Handles map initialization and path visualization
 */

// Map configuration
let map;
let pathLayer;
let startMarker;
let endMarker;
let nodeLayer; // <-- added to hold all nodes layer

/**
 * Initialize the map with local image
 */
function initializeMap(imageUrl) {
    // Create map with CRS.Simple for pixel coordinates
    map = L.map('map', {
        crs: L.CRS.Simple,
        minZoom: -3,
        maxZoom: 2,
        zoomSnap: 0.25,
        zoomDelta: 0.25,
        attributionControl: false
    });
    
    // Calculate bounds for the image
    const bounds = [[0, 0], [AppConfig.MAP_HEIGHT, AppConfig.MAP_WIDTH]];
    
    // Set the map bounds to prevent dragging outside the image
    map.setMaxBounds(bounds);
    map.on('drag', function() {
        map.panInsideBounds(bounds, { animate: false });
    });

    // Add the local map image
    L.imageOverlay(imageUrl, bounds).addTo(map);
    
    // Set the map bounds
    map.fitBounds(bounds);
    
    // Set initial view to center
    map.setView([AppConfig.MAP_HEIGHT / 2, AppConfig.MAP_WIDTH / 2], -1);
    
    // Add attribution
    L.control.attribution({
        position: 'bottomright',
        prefix: 'PathFinding App - Hoàn Kiếm'
    }).addTo(map);
    
    console.log('Map initialized successfully');

}

/**
 * Convert database coordinates (x, y) to Leaflet coordinates [y, x]
 */
/**
 * Convert database coordinates (x, y) to Leaflet coordinates [y, x]
 * KHẮC PHỤC: Đảo ngược tọa độ Y bằng cách trừ đi chiều cao của bản đồ.
 */
function dbToLeaflet(x, y) {
    return [y,x]
}
/**
 * Draw a marker on the map
 */
function addMarker(x, y, type = 'start') {
    const position = dbToLeaflet(x, y);
    if (type === 'start' && startMarker) {
        map.removeLayer(startMarker);
    } else if (type === 'end' && endMarker) {
        map.removeLayer(endMarker);
    }
    const markerOptions = {
        radius: 10,
        fillColor: type === 'start' ? '#22c55e' : '#ef4444',
        color: '#fff',
        weight: 3,
        opacity: 1,
        fillOpacity: 0.9
    };
    
    const marker = L.circleMarker(position, markerOptions).addTo(map);
    if (type === 'start') {
        startMarker = marker; // Gán marker mới vào biến startMarker
    } else if (type === 'end') {
        endMarker = marker; // Gán marker mới vào biến endMarker
    }
    // Add popup
    const label = type === 'start' ? 'Start' : 'End';
    marker.bindPopup(`<b>${label} Point</b><br>Coordinates: (${x.toFixed(0)}, ${y.toFixed(0)})`);
    
    return marker;
}

/**
 * Draw the path on the map
 */
function drawPath(pathData) {
    // Clear existing path
    clearPath();
    
    // pathData should be array of edges: [{from: {x, y}, to: {x, y}}, ...]
    // or array of nodes: [{x, y}, ...]
    
    if (!pathData || pathData.length === 0) {
        console.warn('No path data to draw');
        return;
    }
    
    // Create layer group for the path
    pathLayer = L.layerGroup().addTo(map);
    
    // Check if we have edges or nodes
    if (pathData[0].from && pathData[0].to) {
        // Draw edges
        // ... (Existing logic for edges if needed, but backend returns nodes now)
        // Assuming backend returns nodes format as per python code
    } else if (pathData[0].x !== undefined && pathData[0].y !== undefined) {
        // Draw path from nodes
        const coordinates = pathData.map(node => dbToLeaflet(node.x, node.y));
        
        // Logic vẽ đường: 
        // - Cạnh đầu (Start -> Proj) và Cạnh cuối (Proj -> End) vẽ nét đứt.
        // - Các cạnh giữa vẽ nét liền.
        
        if (coordinates.length >= 2) {
            // 1. Vẽ cạnh đầu tiên (Nét đứt)
            L.polyline([coordinates[0], coordinates[1]], {
                color: '#3b82f6',
                weight: 4,
                opacity: 0.8,
                dashArray: '10, 10'
            }).addTo(pathLayer);
        }

        if (coordinates.length > 3) {
            // 2. Vẽ phần giữa (Nét liền)
            // Từ node 1 đến node N-2
            const middleCoords = coordinates.slice(1, coordinates.length - 1);
            L.polyline(middleCoords, {
                color: '#3b82f6',
                weight: 4,
                opacity: 0.8
            }).addTo(pathLayer);
        }

        if (coordinates.length >= 3) {
            // 3. Vẽ cạnh cuối cùng (Nét đứt)
            // Từ node N-2 đến node N-1
            const len = coordinates.length;
            L.polyline([coordinates[len-2], coordinates[len-1]], {
            color: '#3b82f6',
            weight: 4,
            opacity: 0.8,
            dashArray: '10, 10'
            }).addTo(pathLayer);
        }
        
        // Add markers
        const firstNode = pathData[0];
        const lastNode = pathData[pathData.length - 1];
        
        startMarker = addMarker(firstNode.x, firstNode.y, 'start');
        endMarker = addMarker(lastNode.x, lastNode.y, 'end');
    }
    
    // Fit map to show the entire path
    if (pathLayer && pathLayer.getBounds) {
        map.fitBounds(pathLayer.getBounds(), { padding: [50, 50] });
    }
}

/**
 * Draw all nodes (points) on the map
 * nodes: array of { id, x, y, ... }
 */
function showAllNodes(nodes) {
    // Clear existing node layer if any
    if (nodeLayer) {
        map.removeLayer(nodeLayer);
        nodeLayer = null;
    }

    if (!nodes || nodes.length === 0) {
        console.warn('No nodes to display');
        return;
    }

    nodeLayer = L.layerGroup().addTo(map);

    nodes.forEach(n => {
        const pos = dbToLeaflet(n.x, n.y);
        const marker = L.circleMarker(pos, {
            radius: 4,
            fillColor: '#f97316',
            color: '#fff',
            weight: 1,
            fillOpacity: 0.9
        }).bindPopup(`<b>ID:</b> ${n.id}<br><b>Coords:</b> (${n.x.toFixed(0)}, ${n.y.toFixed(0)})`);
        nodeLayer.addLayer(marker);
    });

    // Optionally fit bounds to nodes if many
    if (nodeLayer && nodeLayer.getBounds && nodeLayer.getLayers().length) {
        try {
            map.fitBounds(nodeLayer.getBounds(), { padding: [40, 40] });
        } catch (e) {
            // ignore if single point or error
        }
    }
}

/**
 * Clear the current path from the map
 */

function clearPath() {
    if (pathLayer) {
        map.removeLayer(pathLayer);
        pathLayer = null;
    }
    
    if (startMarker) { // <-- Logic xóa Start Marker
        map.removeLayer(startMarker);
        startMarker = null;
    }
    
    if (endMarker) { // <-- Logic xóa End Marker
        map.removeLayer(endMarker);
        endMarker = null;
    }
}
/**
 * Clear nodes layer
 */
function clearNodes() {
    if (nodeLayer) {
        map.removeLayer(nodeLayer);
        nodeLayer = null;
    }
}

/**
 * Highlight a specific node on the map
 */
function highlightNode(x, y) {
    const position = dbToLeaflet(x, y);
    
    const marker = L.circleMarker(position, {
        radius: 8,
        fillColor: '#fbbf24',
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map);
    
    // Pulse animation
    marker.bindPopup('Selected Node');
    marker.openPopup();
    
    return marker;
}

/**
 * Get map click coordinates
 */
function onMapClick(callback) {
    map.on('click', (e) => {
        // Convert Leaflet coordinates [y, x] back to database coordinates (x, y)
        const x = e.latlng.lng;
        const y = e.latlng.lat;
        
        callback(x, y);
    });
}

function setStartMarker(marker) {
    startMarker = marker;
}

function setEndMarker(marker) {
    endMarker = marker;
}

// Export functions for use in other modules
window.MapModule = {
    init: initializeMap,
    drawPath: drawPath,
    clearPath: clearPath,
    addMarker: addMarker,
    highlightNode: highlightNode,
    onMapClick: onMapClick,
    dbToLeaflet: dbToLeaflet,
    showAllNodes: showAllNodes, // <-- exported
    clearNodes: clearNodes,      // <-- exported
    getMap: () => map,
    getStartMarker: () => startMarker,
    getEndMarker: () => endMarker,
    getPathLayer: () => pathLayer,
    setPathLayer: (layer) => pathLayer = layer,
    setStartMarker,
    setEndMarker,
};