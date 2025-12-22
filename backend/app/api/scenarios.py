from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

# Import schemas
from app.schemas.scenario import ScenarioRequest, ScenarioResponse, ScenarioItem
# Import services
from app.services.scenario import get_scenario_service
from app.services.pathfinding import get_pathfinding_service
from app.dependencies.access_control import require_admin

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

# --- Local Models to support 'barrier' type without editing schemas/scenario.py ---
class PointModel(BaseModel):
    lat: float
    lng: float

class ScenarioRequestLocal(BaseModel):
    scenario_type: str
    line_start: PointModel
    line_end: PointModel
    penalty_weight: float
    threshold: float

class ScenarioResponseLocal(BaseModel):
    message: str
    affected_edges: int
    scenario_type: str

class ScenarioItemLocal(BaseModel):
    id: int
    active: bool
    scenario_type: str
    line_start: PointModel
    line_end: PointModel
    penalty_weight: float
    threshold: float
    affected_edges: int
# --------------------------------------------------------------------------------

@router.get("/", response_model=List[ScenarioItemLocal])
async def get_scenarios():
    """Lấy danh sách kịch bản đang chạy (từ RAM)"""
    return get_scenario_service().active_scenarios

@router.post("/", response_model=ScenarioResponseLocal)
async def create_scenario(
    request: ScenarioRequestLocal,
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
    affected_edges_map, structural_changes = sc_service.calculate_affected_edges(
        pathfinding_service=pf_service,
        line_p1=(request.line_start.lng, request.line_start.lat),
        line_p2=(request.line_end.lng, request.line_end.lat),
        threshold=request.threshold,
        scenario_type=request.scenario_type
    )
    
    # Bước 2: Cập nhật trọng số ngay lập tức vào RAM
    total_affected = 0
    for v_type, edges in affected_edges_map.items():
        total_affected += len(edges)
        for u, v in edges:
            pf_service.update_weight_in_ram(u, v, request.penalty_weight, v_type)
        
    # Bước 3: Lưu lại kịch bản để quản lý
    saved_scenario = sc_service.add_scenario(request.dict(), affected_edges_map, structural_changes)
    
    print(f"✅ Applied scenario {request.scenario_type} to {total_affected} edges.")
    
    return ScenarioResponseLocal(
        message="Scenario applied successfully (In-Memory)",
        affected_edges=total_affected,
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
    # Cần lấy scenario ra trước để biết nó đã thay đổi cấu trúc gì
    scenario_to_remove = next((s for s in sc_service.active_scenarios if s["id"] == scenario_id), None)
    
    if not scenario_to_remove:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    sc_service.remove_scenario(scenario_id)

    # 2. Reset trọng số RAM về trạng thái ban đầu
    pf_service.reset_weights_in_ram()
    
    # 3. Undo các thay đổi cấu trúc (Split edges) của scenario này
    # Lưu ý: Nếu có nhiều scenario chồng chéo, việc undo này có thể phức tạp.
    # Ở đây ta giả định reset toàn bộ graph về gốc rồi apply lại các scenario còn lại là an toàn nhất.
    # Tuy nhiên, PathfindingService không hỗ trợ "reset cấu trúc" dễ dàng trừ khi reload DB.
    # Cách tốt nhất: Reload Graph từ DB -> Apply lại các scenario còn lại.
    
    pf_service.reload_graph() # Reset cấu trúc và trọng số về zin
    
    # 4. Apply lại TẤT CẢ các kịch bản còn lại trong danh sách
    # (Để đảm bảo nếu còn mưa chỗ khác thì vẫn phải mưa)
    for scenario in sc_service.active_scenarios:
        # Cần tính toán lại cấu trúc cho các scenario còn lại (vì graph đã reset)
        # Đây là bước tốn kém nhưng đảm bảo tính đúng đắn
        
        # Tính lại affected edges và structural changes trên graph mới
        req = scenario # scenario dict chứa data request
        new_map, new_struct = sc_service.calculate_affected_edges(
            pf_service,
            (req['line_start']['lng'], req['line_start']['lat']),
            (req['line_end']['lng'], req['line_end']['lat']),
            req['threshold'],
            scenario_type=req['scenario_type']
        )
        
        # Cập nhật lại thông tin mới vào scenario trong list
        scenario['affected_edges_map'] = new_map
        scenario['structural_changes'] = new_struct
        
        penalty = scenario['penalty_weight']
        for v_type, edges in new_map.items():
            for u, v in edges:
                pf_service.update_weight_in_ram(u, v, penalty, v_type)

    print(f"🔄 Scenario {scenario_id} removed. Graph refreshed.")
    return {"message": "Scenario deleted and graph updated"}

@router.delete("/")
async def clear_all_scenarios(_=Depends(require_admin)):
    """Xóa tất cả kịch bản (Nút Clear All)"""
    pf_service = get_pathfinding_service()
    sc_service = get_scenario_service()
    
    # 1. Xóa danh sách
    sc_service.clear_all()
    
    # 2. Reset RAM về zin (Bao gồm cả cấu trúc)
    pf_service.reload_graph()
    
    print("🧹 All scenarios cleared. Graph reset to original.")
    return {"message": "All scenarios cleared"}