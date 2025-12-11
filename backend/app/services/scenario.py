"""
Scenario Management Service
Handles geometric calculations for scenarios using In-Memory Graph data
"""
import math
from typing import List, Tuple, Dict, Any

class ScenarioService:
    """Service for managing scenarios logic without touching DB"""
    
    def __init__(self):
        # Lưu trữ metadata các kịch bản đang chạy
        self.active_scenarios: List[Dict[str, Any]] = []
        self.counter_id = 1

    def calculate_affected_edges(
        self, 
        pathfinding_service, 
        line_p1: Tuple[float, float], 
        line_p2: Tuple[float, float], 
        threshold: float
    ) -> Dict[str, List[Tuple[int, int]]]:
        """
        Tính toán các cạnh bị ảnh hưởng dựa trên dữ liệu RAM của PathfindingService.
        """
        affected_edges_by_type = {'car': [], 'foot': []}
        
        # 2. Chuẩn bị Vector đường vẽ (Nét vẽ của Admin)
        line_vec_x = line_p2[0] - line_p1[0]
        line_vec_y = line_p2[1] - line_p1[1]
        len_sq = line_vec_x ** 2 + line_vec_y ** 2
        
        # 3. Duyệt qua cả 2 loại phương tiện
        for v_type in ['car', 'foot']:
            graph = pathfinding_service.graphs[v_type]
            nodes = graph['nodes']
            edges_dict = graph['original_weights']
            
            for (u, v), _ in edges_dict.items():
                # Lấy toạ độ Node từ RAM
                if u not in nodes or v not in nodes:
                    continue
                    
                p1 = nodes[u] # (x1, y1)
                p2 = nodes[v] # (x2, y2)
                
                # --- TOÁN HỌC HÌNH CHIẾU ---
                mid_x = (p1[0] + p2[0]) / 2
                mid_y = (p1[1] + p2[1]) / 2
                
                if len_sq == 0:
                    # Trường hợp Mưa (Điểm tròn)
                    closest_x, closest_y = line_p1
                else:
                    # Trường hợp Chặn đường (Đoạn thẳng)
                    dot = (mid_x - line_p1[0]) * line_vec_x + (mid_y - line_p1[1]) * line_vec_y
                    t = max(0, min(1, dot / len_sq))
                    closest_x = line_p1[0] + t * line_vec_x
                    closest_y = line_p1[1] + t * line_vec_y
                
                # Tính khoảng cách
                dist = math.sqrt((mid_x - closest_x) ** 2 + (mid_y - closest_y) ** 2)
                
                if dist < threshold:
                    affected_edges_by_type[v_type].append((u, v))
                
        return affected_edges_by_type
    
    def add_scenario(self, scenario_data: Dict, affected_edges_map: Dict[str, List[Tuple[int, int]]]):
        """Lưu kịch bản vào danh sách tạm"""
        total_edges = sum(len(edges) for edges in affected_edges_map.values())
        new_scenario = {
            "id": self.counter_id,
            "active": True,
            **scenario_data,
            "affected_edges_map": affected_edges_map, # Lưu map {type: [edges]}
            "affected_edges": total_edges  # Tổng số lượng cạnh
        }
        self.active_scenarios.append(new_scenario)
        self.counter_id += 1
        return new_scenario

    def remove_scenario(self, scenario_id: int):
        """Xóa kịch bản khỏi danh sách"""
        scenario = next((s for s in self.active_scenarios if s["id"] == scenario_id), None)
        if scenario:
            self.active_scenarios.remove(scenario)
            return True
        return False

    def clear_all(self):
        """Xóa sạch sành sanh"""
        self.active_scenarios = []

# Singleton Instance
_scenario_service = None

def get_scenario_service() -> ScenarioService:
    global _scenario_service
    if _scenario_service is None:
        _scenario_service = ScenarioService()
    return _scenario_service