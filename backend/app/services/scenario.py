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
    ) -> Tuple[Dict[str, List[Tuple[int, int]]], List[Dict]]:
        """
        Tính toán các cạnh bị ảnh hưởng và thực hiện biến đổi đồ thị (nếu cần).
        Trả về: (affected_edges_map, structural_changes)
        """
        affected_edges_by_type = {'car': [], 'foot': []}
        structural_changes = [] # Lưu các thay đổi cấu trúc (split edge) để undo
        
        # 2. Chuẩn bị Vector đường vẽ (Nét vẽ của Admin)
        line_vec_x = line_p2[0] - line_p1[0]
        line_vec_y = line_p2[1] - line_p1[1]
        len_sq = line_vec_x ** 2 + line_vec_y ** 2
        
        # 3. Duyệt qua cả 2 loại phương tiện
        for v_type in ['car', 'foot']:
            graph = pathfinding_service.graphs[v_type]
            nodes = graph['nodes']
            edges_dict = graph['original_weights']
            
            # Copy keys để tránh lỗi runtime nếu dictionary thay đổi kích thước khi split
            edges_list = list(edges_dict.keys())
            for (u, v) in edges_list:
                # Lấy toạ độ Node từ RAM
                if u not in nodes or v not in nodes:
                    continue
                    
                p1 = nodes[u] # (x1, y1)
                p2 = nodes[v] # (x2, y2)
                
                if len_sq == 0:
                    # --- TRƯỜNG HỢP MƯA (HÌNH TRÒN) ---
                    # line_p1 là tâm, threshold là bán kính
                    cx, cy = line_p1
                    radius = threshold
                    
                    # Kiểm tra khoảng cách từ tâm đến đoạn thẳng p1-p2
                    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                    if dx == 0 and dy == 0: continue
                    
                    # Tích vô hướng để tìm hình chiếu
                    t = ((cx - p1[0]) * dx + (cy - p1[1]) * dy) / (dx*dx + dy*dy)
                    
                    # Tìm điểm gần nhất trên đoạn thẳng
                    closest_t = max(0, min(1, t))
                    closest_x = p1[0] + closest_t * dx
                    closest_y = p1[1] + closest_t * dy
                    
                    dist_sq = (cx - closest_x)**2 + (cy - closest_y)**2
                    
                    if dist_sq > radius**2:
                        continue # Nằm ngoài hoàn toàn
                        
                    # Kiểm tra xem nằm trong hoàn toàn hay cắt
                    d1_sq = (cx - p1[0])**2 + (cy - p1[1])**2
                    d2_sq = (cx - p2[0])**2 + (cy - p2[1])**2
                    
                    inside1 = d1_sq <= radius**2
                    inside2 = d2_sq <= radius**2
                    
                    if inside1 and inside2:
                        # Nằm trong hoàn toàn
                        affected_edges_by_type[v_type].append((u, v))
                    else:
                        # Cắt đường tròn (Partial overlap) -> Cần split edge
                        # Giải phương trình bậc 2 tìm giao điểm: |P1 + t*V - C|^2 = R^2
                        fx, fy = p1[0] - cx, p1[1] - cy
                        a = dx*dx + dy*dy
                        b = 2 * (fx*dx + fy*dy)
                        c = (fx*fx + fy*fy) - radius*radius
                        delta = b*b - 4*a*c
                        
                        if delta >= 0:
                            ts = []
                            t1 = (-b - math.sqrt(delta)) / (2*a)
                            t2 = (-b + math.sqrt(delta)) / (2*a)
                            if 0 < t1 < 1: ts.append(t1)
                            if 0 < t2 < 1: ts.append(t2)
                            
                            # Sắp xếp t để xử lý từ gần u đến v
                            ts.sort()
                            
                            # Thực hiện split. Lưu ý: Khi split (u,v) thành (u,X), (X,v),
                            # cạnh (u,v) biến mất. Ta cần thêm cạnh mới vào affected list nếu nó nằm trong.
                            # Logic đơn giản: Split xong, kiểm tra trung điểm các cạnh mới.
                            
                            current_u = u
                            current_v = v
                            
                            for t_val in ts:
                                # Tính toạ độ giao điểm
                                ix = p1[0] + t_val * dx
                                iy = p1[1] + t_val * dy
                                
                                # Gọi PathfindingService để split
                                change = pathfinding_service.split_edge(current_u, current_v, (ix, iy), v_type)
                                structural_changes.append(change)
                                
                                # Sau khi split, ta có (current_u, temp) và (temp, current_v)
                                temp_id = change['temp_id']
                                
                                # Kiểm tra đoạn (current_u, temp) có nằm trong không?
                                # Lấy trung điểm
                                m1 = pathfinding_service.graphs[v_type]['nodes'][current_u]
                                m2 = pathfinding_service.graphs[v_type]['nodes'][temp_id]
                                mid_x, mid_y = (m1[0]+m2[0])/2, (m1[1]+m2[1])/2
                                if (mid_x-cx)**2 + (mid_y-cy)**2 <= radius**2:
                                    affected_edges_by_type[v_type].append((current_u, temp_id))
                                    
                                current_u = temp_id # Tiếp tục xử lý đoạn sau
                            
                            # Kiểm tra đoạn cuối cùng (current_u, current_v ban đầu là v)
                            m1 = pathfinding_service.graphs[v_type]['nodes'][current_u]
                            m2 = pathfinding_service.graphs[v_type]['nodes'][v] # v gốc
                            mid_x, mid_y = (m1[0]+m2[0])/2, (m1[1]+m2[1])/2
                            if (mid_x-cx)**2 + (mid_y-cy)**2 <= radius**2:
                                affected_edges_by_type[v_type].append((current_u, v))

                else:
                    # --- TRƯỜNG HỢP CHẶN ĐƯỜNG (ĐOẠN THẲNG) ---
                    # Kiểm tra giao nhau giữa 2 đoạn thẳng: (p1, p2) và (line_p1, line_p2)
                    if self._segments_intersect(p1, p2, line_p1, line_p2):
                        affected_edges_by_type[v_type].append((u, v))
                
        return affected_edges_by_type, structural_changes
    
    def add_scenario(self, scenario_data: Dict, affected_edges_map: Dict, structural_changes: List[Dict]):
        """Lưu kịch bản vào danh sách tạm"""
        total_edges = sum(len(edges) for edges in affected_edges_map.values())
        new_scenario = {
            "id": self.counter_id,
            "active": True,
            **scenario_data,
            "affected_edges_map": affected_edges_map, # Lưu map {type: [edges]}
            "structural_changes": structural_changes, # Lưu lịch sử thay đổi cấu trúc
            "affected_edges": total_edges
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

    def _segments_intersect(self, p1, p2, p3, p4):
        """Kiểm tra 2 đoạn thẳng p1-p2 và p3-p4 có cắt nhau không"""
        def ccw(A, B, C):
            return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
            
        # Kiểm tra bounding box trước cho nhanh
        if max(p1[0], p2[0]) < min(p3[0], p4[0]) or \
           max(p3[0], p4[0]) < min(p1[0], p2[0]) or \
           max(p1[1], p2[1]) < min(p3[1], p4[1]) or \
           max(p3[1], p4[1]) < min(p1[1], p2[1]):
            return False
            
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

# Singleton Instance
_scenario_service = None

def get_scenario_service() -> ScenarioService:
    global _scenario_service
    if _scenario_service is None:
        _scenario_service = ScenarioService()
    return _scenario_service