# Implementation Guide for Team

## 🎯 Overview

This guide helps you implement the remaining features. Templates are provided to get you started quickly.

## 📝 Sprint 1: Pathfinding (Giang + Hưng)

### Step 1: Load Your Data

Create `scripts/load_data.py`:

```python
"""
Load nodes and edges from JSON files into database
"""
import json
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database import get_db_connection


def load_nodes(json_file):
    """Load nodes from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        nodes = json.load(f)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for node in nodes:
            cursor.execute(
                "INSERT INTO nodes (id, name, x, y) VALUES (?, ?, ?, ?)",
                (node['id'], node.get('name', ''), node['x'], node['y'])
            )
        
        print(f"✓ Loaded {len(nodes)} nodes")


def load_edges(json_file):
    """Load edges from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        edges = json.load(f)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for edge in edges:
            cursor.execute(
                "INSERT INTO edges (node_from, node_to, weight) VALUES (?, ?, ?)",
                (edge['node_from'], edge['node_to'], edge['weight'])
            )
        
        print(f"✓ Loaded {len(edges)} edges")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load graph data')
    parser.add_argument('--nodes', required=True, help='Path to nodes JSON file')
    parser.add_argument('--edges', required=True, help='Path to edges JSON file')
    
    args = parser.parse_args()
    
    print("=== Loading Graph Data ===\n")
    load_nodes(args.nodes)
    load_edges(args.edges)
    print("\n=== Data loaded successfully ===")
```

**Usage:**
```bash
python scripts/load_data.py --nodes data/nodes.json --edges data/edges.json
```

### Step 2: Implement Pathfinding Service

The template is already created at:
- `backend/app/services/pathfinding.py`

**What to do:**
1. Copy the template to your backend
2. Test it loads correctly: `python -c "from app.services.pathfinding import get_pathfinding_service; print('OK')"`
3. Review the A* implementation
4. Adjust if needed for your specific requirements

### Step 3: Create API Endpoint

The template is already created at:
- `backend/app/api/path.py`

**What to do:**
1. Copy the template to your backend
2. Create `__init__.py` in `backend/app/api/` if it doesn't exist
3. Uncomment the import in `backend/app/main.py`:
   ```python
   from app.api import path
   app.include_router(path.router)
   ```
4. Restart the backend server
5. Test at: http://localhost:8000/docs

### Step 4: Connect Frontend

Update `frontend/js/pathfinding.js`:

Replace the mock data section with:

```javascript
async function findPath() {
    // ... validation code ...
    
    try {
        // Real API call
        const response = await fetch(
            `${API_BASE_URL}/api/path?start_x=${startX}&start_y=${startY}&end_x=${endX}&end_y=${endY}`
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to find path');
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
        updateStatus('❌ ' + error.message);
        showErrorInfo(error.message);
    } finally {
        showLoading(false);
    }
}
```

### Step 5: Test Complete Flow

1. **Load test data:**
   ```bash
   python scripts/load_data.py --nodes data/nodes.json --edges data/edges.json
   ```

2. **Verify in database:**
   ```bash
   sqlite3 backend/data/pathfinding.db
   SELECT COUNT(*) FROM nodes;
   SELECT COUNT(*) FROM edges;
   .exit
   ```

3. **Test API directly:**
   - Go to http://localhost:8000/docs
   - Try `GET /api/path` with sample coordinates

4. **Test in UI:**
   - Open http://localhost:8080/index.html
   - Select two points
   - Verify path displays correctly

## 📝 Sprint 3: Scenarios (Bảo + Hiếu)

### Step 1: Create Scenario Schema

Create `backend/app/schemas/scenario.py`:

```python
from pydantic import BaseModel
from typing import Literal


class Point(BaseModel):
    """Geographic point"""
    lat: float
    lng: float


class ScenarioRequest(BaseModel):
    """Request to create/update scenario"""
    scenario_type: Literal["rain", "block"]
    line_start: Point
    line_end: Point
    penalty_weight: float
    threshold: float = 50.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "scenario_type": "rain",
                "line_start": {"lat": 3800.0, "lng": 4000.0},
                "line_end": {"lat": 3900.0, "lng": 4500.0},
                "penalty_weight": 1.5,
                "threshold": 50.0
            }
        }


class ScenarioResponse(BaseModel):
    """Response after applying scenario"""
    message: str
    affected_edges: int
    scenario_type: str
```

### Step 2: Implement Scenario Service

Create `backend/app/services/scenario.py`:

```python
"""
Scenario Management Service
Handles dynamic edge weight modifications
"""
import math
from typing import List, Tuple
from app.database import get_db_connection


class ScenarioService:
    """Service for managing scenarios that affect edge weights"""
    
    def find_edges_near_line(
        self, 
        line_p1: Tuple[float, float], 
        line_p2: Tuple[float, float], 
        threshold: float
    ) -> List[Tuple[int, int]]:
        """
        Find edges whose midpoints are within threshold distance of a line
        
        Args:
            line_p1: (x, y) start point of line
            line_p2: (x, y) end point of line
            threshold: maximum distance in pixels
            
        Returns:
            List of (node_from, node_to) tuples
        """
        affected_edges = []
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all edges with their node positions
            cursor.execute("""
                SELECT e.node_from, e.node_to, 
                       n1.x as x1, n1.y as y1,
                       n2.x as x2, n2.y as y2
                FROM edges e
                JOIN nodes n1 ON e.node_from = n1.id
                JOIN nodes n2 ON e.node_to = n2.id
            """)
            
            edges = cursor.fetchall()
            
            # Line vector
            line_vec_x = line_p2[0] - line_p1[0]
            line_vec_y = line_p2[1] - line_p1[1]
            len_sq = line_vec_x ** 2 + line_vec_y ** 2
            
            for edge in edges:
                # Edge midpoint
                mid_x = (edge['x1'] + edge['x2']) / 2
                mid_y = (edge['y1'] + edge['y2']) / 2
                
                # Find closest point on line to midpoint
                if len_sq == 0:
                    # Line is actually a point
                    closest_x, closest_y = line_p1
                else:
                    # Project midpoint onto line
                    point_vec_x = mid_x - line_p1[0]
                    point_vec_y = mid_y - line_p1[1]
                    
                    dot = point_vec_x * line_vec_x + point_vec_y * line_vec_y
                    t = max(0, min(1, dot / len_sq))
                    
                    closest_x = line_p1[0] + t * line_vec_x
                    closest_y = line_p1[1] + t * line_vec_y
                
                # Distance from midpoint to closest point on line
                dist = math.sqrt(
                    (mid_x - closest_x) ** 2 + 
                    (mid_y - closest_y) ** 2
                )
                
                if dist < threshold:
                    affected_edges.append((edge['node_from'], edge['node_to']))
        
        return affected_edges
    
    def modify_edge_weight(
        self, 
        node_from: int, 
        node_to: int, 
        add_weight: float = None,
        set_weight: float = None
    ):
        """
        Modify edge weight by adding or setting value
        
        Args:
            node_from: Starting node ID
            node_to: Ending node ID
            add_weight: Amount to add to current weight
            set_weight: New weight value (overrides current)
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if add_weight is not None:
                cursor.execute("""
                    UPDATE edges 
                    SET weight = weight + ? 
                    WHERE node_from = ? AND node_to = ?
                """, (add_weight, node_from, node_to))
            elif set_weight is not None:
                cursor.execute("""
                    UPDATE edges 
                    SET weight = ? 
                    WHERE node_from = ? AND node_to = ?
                """, (set_weight, node_from, node_to))
    
    def apply_scenario(
        self,
        scenario_type: str,
        line_start: Tuple[float, float],
        line_end: Tuple[float, float],
        penalty_weight: float,
        threshold: float
    ) -> int:
        """
        Apply scenario to affected edges
        
        Returns:
            Number of affected edges
        """
        # Convert lat/lng to x/y if needed
        # For now assume they're already in pixel coordinates
        affected = self.find_edges_near_line(
            (line_start[1], line_start[0]),  # (lng, lat) -> (x, y)
            (line_end[1], line_end[0]),
            threshold
        )
        
        # Apply penalty to each affected edge
        for node_from, node_to in affected:
            self.modify_edge_weight(node_from, node_to, add_weight=penalty_weight)
        
        return len(affected)


# Singleton instance
_scenario_service = None

def get_scenario_service() -> ScenarioService:
    """Get scenario service instance"""
    global _scenario_service
    if _scenario_service is None:
        _scenario_service = ScenarioService()
    return _scenario_service
```

### Step 3: Create Scenarios API

Create `backend/app/api/scenarios.py`:

```python
from fastapi import APIRouter, Depends
from app.schemas.scenario import ScenarioRequest, ScenarioResponse
from app.services.scenario import get_scenario_service
from app.services.pathfinding import get_pathfinding_service
from app.dependencies.access_control import require_admin

router = APIRouter(prefix="/api", tags=["Scenarios"])


@router.post("/scenarios", response_model=ScenarioResponse)
async def create_scenario(
    request: ScenarioRequest,
    _=Depends(require_admin)
):
    """
    Apply scenario to graph (Admin only)
    
    Updates edge weights based on weather or road conditions
    """
    service = get_scenario_service()
    
    # Apply scenario
    affected = service.apply_scenario(
        scenario_type=request.scenario_type,
        line_start=(request.line_start.lat, request.line_start.lng),
        line_end=(request.line_end.lat, request.line_end.lng),
        penalty_weight=request.penalty_weight,
        threshold=request.threshold
    )
    
    # Reload graph in pathfinding service
    pathfinding = get_pathfinding_service()
    pathfinding.reload_graph()
    
    return ScenarioResponse(
        message=f"Scenario applied successfully",
        affected_edges=affected,
        scenario_type=request.scenario_type
    )


@router.post("/scenarios/clear")
async def clear_scenarios(_=Depends(require_admin)):
    """
    Reset all edge weights to original values (Admin only)
    
    Note: This requires storing original weights.
    For now, you might need to reload from original data.
    """
    # TODO: Implement weight reset logic
    # Option 1: Store original weights in a separate column
    # Option 2: Reload edges from original data file
    
    return {"message": "Scenarios cleared"}
```

### Step 4: Update main.py

Add to `backend/app/main.py`:

```python
from app.api import scenarios

app.include_router(scenarios.router)
```

### Step 5: Connect Admin UI

Update `frontend/js/admin.js`, replace the `applyScenario()` function:

```javascript
async function applyScenario() {
    updateStatus('Applying scenario...');
    
    try {
        const scenarioData = getScenarioData(currentScenario);
        
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
        
        // Make API call
        const response = await authManager.request('/api/scenarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to apply scenario');
        }
        
        const data = await response.json();
        
        // Visualize affected area
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
        
        updateStatus(`${scenarioData.name} applied! Affected ${data.affected_edges} edges.`);
        
        clearTempMarkers();
        clickPoints = [];
        scenarioButtons.forEach(b => b.classList.remove('active'));
        currentScenario = null;
        
    } catch (error) {
        console.error('Error applying scenario:', error);
        updateStatus('Error applying scenario. Please try again.');
    }
}
```

## ✅ Testing Checklist

### Pathfinding
- [ ] Data loaded into database
- [ ] API returns path for valid coordinates
- [ ] Path displays correctly on map
- [ ] Error handling works for invalid coordinates
- [ ] Path information shows correct values

### Scenarios
- [ ] Can draw rain zone in admin panel
- [ ] API applies penalty to affected edges
- [ ] Pathfinding considers updated weights
- [ ] Can clear scenarios
- [ ] Multiple scenarios can coexist

## 🐛 Common Issues

### Issue: "No path found"
**Possible causes:**
- Selected points too far from any nodes
- No connected path in graph
- Edge weights too high (blocked)

**Solution:**
- Check node coverage on map
- Verify graph connectivity
- Adjust `find_nearest_node()` radius

### Issue: Scenario doesn't affect path
**Possible causes:**
- Path doesn't go through affected area
- Threshold too small
- Forgot to reload graph

**Solution:**
- Increase threshold
- Call `reload_graph()` after weight updates
- Verify affected edges are on the path

### Issue: Frontend can't connect to backend
**Possible causes:**
- CORS not configured
- Wrong API URL
- Backend not running

**Solution:**
- Check `.env` has correct ALLOWED_ORIGINS
- Verify API_BASE_URL in JavaScript
- Check backend terminal for errors

## 📚 Resources

- [A* Algorithm Tutorial](https://www.redblobgames.com/pathfinding/a-star/introduction.html)
- [Leaflet.js Documentation](https://leafletjs.com/reference.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🎉 Success Criteria

You're done when:
1. Can load real node/edge data
2. Can find path between any two points
3. Path displays correctly on fixed.png
4. Admin can apply scenarios
5. Scenarios affect pathfinding results

Good luck! 🚀