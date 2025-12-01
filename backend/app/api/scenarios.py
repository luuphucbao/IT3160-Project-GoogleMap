from fastapi import APIRouter, Depends, HTTPException
from typing import List

# Import schemas
from app.schemas.scenario import ScenarioRequest, ScenarioResponse, ScenarioItem
# Import services
from app.services.scenario import get_scenario_service
from app.services.pathfinding import get_pathfinding_service # Quan trọng!
from app.dependencies.access_control import require_admin

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

@router.get("/", response_model=List[ScenarioItem])
async def get_scenarios():
    """Lấy danh sách các kịch bản đang chạy (Cho Admin UI)"""
    service = get_scenario_service()
    return service.get_active_scenarios()

@router.post("/", response_model=ScenarioResponse)
async def create_scenario(
    request: ScenarioRequest,
    _=Depends(require_admin)
):
    """Tạo kịch bản tắc đường mới"""
    service = get_scenario_service()
    
    # 1. Tính toán và cập nhật DB
    affected_count = service.apply_scenario(
        scenario_type=request.scenario_type,
        line_start=(request.line_start.lat, request.line_start.lng),
        line_end=(request.line_end.lat, request.line_end.lng),
        penalty_weight=request.penalty_weight,
        threshold=request.threshold
    )
    
    # 2. QUAN TRỌNG: Báo cho Service tìm đường load lại đồ thị mới
    pathfinding = get_pathfinding_service()
    pathfinding.reload_graph()
    print("[DEBUG] Pathfinding graph reloaded after scenario applied.")
    
    return ScenarioResponse(
        message="Scenario applied successfully",
        affected_edges=affected_count,
        scenario_type=request.scenario_type
    )

@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: int, 
    _=Depends(require_admin)
):
    """Xóa kịch bản (Hoàn tác trọng số)"""
    service = get_scenario_service()
    success = service.remove_scenario(scenario_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Reload lại đồ thị sau khi xóa
    pathfinding = get_pathfinding_service()
    if pathfinding:
        pathfinding.reload_graph()

    return {"message": "Scenario deleted and graph reloaded"}