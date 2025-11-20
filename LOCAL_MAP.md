# Using Local Map Image (fixed.png)

## 🗺️ Overview

The application now uses your local map image (`map/fixed.png`) instead of OpenStreetMap tiles. This provides pixel-perfect coordinate mapping for your 8900×7601 map of Hoàn Kiếm district.

## 📐 Coordinate System

Your map uses a **pixel-based coordinate system**:
- **Origin (0,0)**: Top-left corner of the map
- **X-axis**: Horizontal (0 to 8900)
- **Y-axis**: Vertical (0 to 7601)

## 🔄 Changes Made

### 1. Admin Dashboard (admin.js)
- Changed from geographic coordinates (lat/lng) to pixel coordinates
- Uses `L.CRS.Simple` for pixel-based mapping
- Loads `../map/fixed.png` as image overlay
- Map bounds set to [[0, 0], [7601, 8900]]

### 2. User Interface (NEW)
Created complete user interface with:
- **index.html**: Main pathfinding interface
- **css/style.css**: Beautiful, responsive styling
- **js/map.js**: Map module with local image support
- **js/pathfinding.js**: Pathfinding logic and API integration

## 📁 Required Folder Structure

```
frontend/
├── index.html          ✓ NEW - User interface
├── admin.html          ✓ UPDATED - Uses local map
├── css/
│   ├── style.css       ✓ NEW - User interface styles
│   └── admin.css       ✓ Existing
├── js/
│   ├── map.js          ✓ NEW - Map module
│   ├── pathfinding.js  ✓ NEW - Pathfinding logic
│   ├── admin.js        ✓ UPDATED - Uses local map
│   └── auth.js         ✓ Existing
└── map/
    └── fixed.png       ✓ YOUR MAP IMAGE
```

## 🎯 How It Works

### Coordinate Conversion

The map uses Leaflet's `CRS.Simple` coordinate system where:
- Database stores: `(x, y)` in pixels
- Leaflet expects: `[y, x]` (note the order!)

**Example:**
```javascript
// Database coordinates
const dbX = 4450;  // Middle of map horizontally
const dbY = 3800;  // Middle of map vertically

// Convert to Leaflet format
const leafletCoords = [dbY, dbX];  // [3800, 4450]

// Add marker
L.circleMarker(leafletCoords).addTo(map);
```

### User Interface Features

1. **Click to Select**: Users can click the map to select start/end points
2. **Manual Input**: Users can enter coordinates manually
3. **Path Visualization**: Paths are drawn as lines between nodes
4. **Path Information**: Shows distance, number of nodes, and cost

## 🚀 Testing the Map

### 1. Start the Application
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
python -m http.server 8080
```

### 2. Test User View
1. Open `http://localhost:8080/index.html`
2. You should see your `fixed.png` map
3. Try clicking different areas to test coordinates
4. The map should zoom and pan smoothly

### 3. Test Admin View
1. Open `http://localhost:8080/admin.html`
2. Login with admin credentials
3. You should see your `fixed.png` map
4. Click scenario buttons and test drawing

## 🔧 Map Configuration

If you need to adjust map settings, edit these values in the JavaScript files:

```javascript
// In map.js and admin.js
const MAP_CONFIG = {
    width: 8900,      // Your map width in pixels
    height: 7601,     // Your map height in pixels
    imageUrl: '../map/fixed.png'
};
```

## 📊 Integrating with Your Node/Edge Data

When you load your node and edge data, make sure:

1. **Nodes table** stores pixel coordinates:
   ```sql
   INSERT INTO nodes (name, x, y) VALUES 
   ('Node1', 100, 200),  -- x and y in pixels
   ('Node2', 500, 300);
   ```

2. **Pathfinding API** returns coordinates in the same format:
   ```json
   {
     "path": [
       {"x": 100, "y": 200},
       {"x": 300, "y": 250},
       {"x": 500, "y": 300}
     ]
   }
   ```

3. **Frontend automatically converts** these to Leaflet format

## 🎨 Customizing Map Appearance

### Change Zoom Levels
```javascript
map = L.map('map', {
    crs: L.CRS.Simple,
    minZoom: -3,  // Zoom out more
    maxZoom: 3,   // Zoom in more
});
```

### Change Initial View
```javascript
// Center on specific area
map.setView([3800, 4450], 0);  // [y, x], zoom
```

### Adjust Marker Styles
```javascript
const marker = L.circleMarker([y, x], {
    radius: 12,           // Size
    fillColor: '#22c55e', // Color
    color: '#fff',        // Border color
    weight: 3,            // Border width
    fillOpacity: 0.9
});
```

## 🐛 Troubleshooting

### Map Not Showing
1. Check console for errors: `F12` → Console tab
2. Verify `fixed.png` exists in `frontend/map/` folder
3. Check path: Should be `../map/fixed.png` (relative to HTML files)

### Wrong Coordinates
1. Verify your nodes use pixel coordinates (0-8900, 0-7601)
2. Check that database coordinates match map pixels
3. Use browser console to log coordinates: `console.log(x, y)`

### Map Too Zoomed In/Out
Adjust initial zoom level:
```javascript
map.setView([mapHeight / 2, mapWidth / 2], -1);  // Try different zoom values
```

## 📝 Next Steps

1. **Load your node/edge data** into the database
2. **Implement A* algorithm** in `backend/app/services/pathfinding.py`
3. **Create pathfinding API** endpoint: `GET /api/path`
4. **Connect frontend** to the real API (remove mock data)
5. **Test with real paths** on your map

## 💡 Tips

- Keep the map image optimized (compress PNG if needed)
- Test with different coordinate ranges to verify accuracy
- Use browser dev tools to debug coordinate conversions
- Check that node positions align with actual locations on the map

Good luck! Your map is now ready for pathfinding! 🎉