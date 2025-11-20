"""
Pathfinding API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from app.services.pathfinding import get_pathfinding_service

router = APIRouter(prefix="/api", tags=["Pathfinding"])


@router.get("/path")
async def find_path(
    start_x: float = Query(..., description="Starting X coordinate (0-8900)", ge=0, le=8900),
    start_y: float = Query(..., description="Starting Y coordinate (0-7601)", ge=0, le=7601),
    end_x: float = Query(..., description="Ending X coordinate (0-8900)", ge=0, le=8900),
    end_y: float = Query(..., description="Ending Y coordinate (0-7601)", ge=0, le=7601)
):
    """
    Find optimal path between two points using A* algorithm
    
    - **start_x, start_y**: Starting coordinates in pixels
    - **end_x, end_y**: Ending coordinates in pixels
    
    Returns path information including:
    - path: List of nodes with coordinates
    - distance: Total distance in pixels
    - cost: Calculated cost (distance/100 + penalties)
    - nodes: Number of nodes in path
    """
    # Get pathfinding service
    service = get_pathfinding_service()
    
    # Find path
    result = service.find_path(start_x, start_y, end_x, end_y)
    
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No path found between the specified points. Make sure both points are near valid nodes."
        )
    
    return result


@router.post("/path/reload")
async def reload_graph():
    """
    Reload graph from database
    Call this after updating edge weights or scenarios
    """
    service = get_pathfinding_service()
    service.reload_graph()
    
    return {
        "message": "Graph reloaded successfully",
        "nodes": len(service.graph)
    }


@router.get("/nodes")
async def get_nodes():
    """
    Get all nodes in the graph
    Useful for debugging and testing
    """
    service = get_pathfinding_service()
    
    nodes = []
    for node_id, data in service.graph.items():
        x, y = data['pos']
        nodes.append({
            'id': node_id,
            'x': x,
            'y': y,
            'neighbors': len(data['neighbors'])
        })
    
    return {
        'nodes': nodes,
        'total': len(nodes)
    }