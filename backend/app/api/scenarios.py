from fastapi import APIRouter, Depends, HTTPException
from typing import List

# Import schemas
from app.schemas.scenario import ScenarioRequest, ScenarioResponse, ScenarioItem
# Import services
from app.services.scenario import get_scenario_service
from app.services.pathfinding import get_pathfinding_service
from app.dependencies.access_control import require_admin

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

@router.get("/", response_model=List[ScenarioItem])
async def get_scenarios():
    """Lấy danh sách kịch bản đang chạy (từ RAM)"""
    return get_scenario_service().active_scenarios

@router.post("/", response_model=ScenarioResponse)
async def create_scenario(
    request: ScenarioRequest,
    _=Depends(require_admin)
):
    """
    Tạo kịch bản mới:
    1. Tính toán hình học (ScenarioService)
    2. Cập nhật RAM (PathfindingService)
    """
    pf_service = get_pathfinding_service()
    sc_service = get_scenario_service()
    
    # Bước 1: Tính toán xem cạnh nào bị dính (Dùng data RAM để tính)
    # Lưu ý: Truyền pf_service vào để ScenarioService truy cập nodes/weights
    affected_edges = sc_service.calculate_affected_edges(
        pathfinding_service=pf_service,
        line_p1=(request.line_start.lat, request.line_start.lng),
        line_p2=(request.line_end.lat, request.line_end.lng),
        threshold=request.threshold
    )
    
    # Bước 2: Cập nhật trọng số ngay lập tức vào RAM
    for u, v in affected_edges:
        pf_service.update_weight_in_ram(u, v, request.penalty_weight)
        
    # Bước 3: Lưu lại kịch bản để quản lý
    saved_scenario = sc_service.add_scenario(request.dict(), affected_edges)
    
    print(f"✅ Applied scenario {request.scenario_type} to {len(affected_edges)} edges.")
    
    return ScenarioResponse(
        message="Scenario applied successfully (In-Memory)",
        affected_edges=len(affected_edges),
        scenario_type=request.scenario_type
    )

@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: int, 
    _=Depends(require_admin)
):
    """
    Xóa kịch bản:
    Chiến thuật: Reset RAM về gốc -> Apply lại các kịch bản còn lại.
    (Đây là cách an toàn nhất để tránh sai lệch trọng số)
    """
    pf_service = get_pathfinding_service()
    sc_service = get_scenario_service()
    
    # 1. Xóa khỏi danh sách quản lý
    success = sc_service.remove_scenario(scenario_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # 2. Reset trọng số RAM về trạng thái ban đầu (như lúc mới khởi động)
    pf_service.reset_weights_in_ram()
    
    # 3. Apply lại TẤT CẢ các kịch bản còn lại trong danh sách
    # (Để đảm bảo nếu còn mưa chỗ khác thì vẫn phải mưa)
    for scenario in sc_service.active_scenarios:
        penalty = scenario['penalty_weight']
        for u, v in scenario['affected_edges_list']:
            pf_service.update_weight_in_ram(u, v, penalty)

    print(f"🔄 Scenario {scenario_id} removed. Graph refreshed.")
    return {"message": "Scenario deleted and graph updated"}

@router.delete("/")
async def clear_all_scenarios(_=Depends(require_admin)):
    """Xóa tất cả kịch bản (Nút Clear All)"""
    pf_service = get_pathfinding_service()
    sc_service = get_scenario_service()
    
    # 1. Xóa danh sách
    sc_service.clear_all()
    
    # 2. Reset RAM về zin
    pf_service.reset_weights_in_ram()
    
    print("🧹 All scenarios cleared. Graph reset to original.")
    return {"message": "All scenarios cleared"}