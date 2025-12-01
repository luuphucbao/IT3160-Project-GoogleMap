"""
Pathfinding API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from app.services.pathfinding import get_pathfinding_service
from app.database import get_db_connection
router = APIRouter(prefix="/api", tags=["Pathfinding"])


@router.get("/path")
async def find_path(
    start_x: float = Query(..., description="Starting X coordinate (0-8500)", ge=0, le=8500),
    start_y: float = Query(..., description="Starting Y coordinate (0-7801)", ge=0, le=7801),
    end_x: float = Query(..., description="Ending X coordinate (0-8500)", ge=0, le=8500),
    end_y: float = Query(..., description="Ending Y coordinate (0-7801)", ge=0, le=7801)
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

@router.get("/nodes", tags=["nodes"])
async def get_all_nodes():
    """
    Lấy danh sách tất cả các node (điểm) có trong cơ sở dữ liệu.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Chọn tất cả các cột từ bảng nodes
            cursor.execute("SELECT id, x, y FROM nodes")
            
            # Chuyển kết quả truy vấn thành danh sách các dictionary
            nodes = [dict(row) for row in cursor.fetchall()]
            
            return {"nodes": nodes}
            
    except Exception as e:
        print(f"Error fetching nodes: {e}")
        # Trả về lỗi HTTP 500 nếu có lỗi truy vấn DB
        raise HTTPException(status_code=500, detail="Internal server error while fetching nodes")
