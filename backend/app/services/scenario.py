import math
import time
from typing import List, Tuple, Dict, Optional
from app.database import get_db_connection
from app.services.pathfinding import get_pathfinding_service
class ScenarioService:
    def __init__(self):
        # Lưu cache trong RAM để quản lý ID và xóa nhanh
        self.active_scenarios: List[Dict] = []
        self.counter_id = 1
        pathfinding=get_pathfinding_service()
    def get_active_scenarios(self):
        return self.active_scenarios

    def find_edges_near_line(self, line_p1: Tuple[float, float], line_p2: Tuple[float, float], threshold: float) -> List[Tuple[int, int]]:
        """Tìm các cạnh nằm trong vùng ảnh hưởng (Logic toán học)"""
        affected_edges = []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Lấy toạ độ các cạnh từ DB (Giả sử node lưu x=lng, y=lat)
            cursor.execute("""
                SELECT e.node_from, e.node_to, n1.x as x1, n1.y as y1, n2.x as x2, n2.y as y2
                FROM edges_session e
                JOIN nodes n1 ON e.node_from = n1.id
                JOIN nodes n2 ON e.node_to = n2.id
            """)
            edges = cursor.fetchall()
            
            line_vec_x, line_vec_y = line_p2[0] - line_p1[0], line_p2[1] - line_p1[1]
            len_sq = line_vec_x ** 2 + line_vec_y ** 2

            for edge in edges:
                mid_x = (edge['x1'] + edge['x2']) / 2
    
                # LẬT NGƯỢC trục Y để khớp với màn hình hiển thị (giống bên pathfinding.py)
                # Lưu ý: Kiểm tra kỹ số 7801 có phải chiều cao map của bạn không
                visual_y1 = 7801 - edge['y1']
                visual_y2 = 7801 - edge['y2']
                mid_y = (visual_y1 + visual_y2) / 2
                
                if len_sq == 0:
                    closest_x, closest_y = line_p1
                else:
                    t = max(0, min(1, ((mid_x - line_p1[0]) * line_vec_x + (mid_y - line_p1[1]) * line_vec_y) / len_sq))
                    closest_x = line_p1[0] + t * line_vec_x
                    closest_y = line_p1[1] + t * line_vec_y
                
                dist = math.sqrt((mid_x - closest_x) ** 2 + (mid_y - closest_y) ** 2)
                if dist < threshold:
                    affected_edges.append((edge['node_from'], edge['node_to']))
        return affected_edges

    def modify_edge_weight(self, node_from: int, node_to: int, add_weight: float):
        """Cập nhật DB"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE edges_session SET weight = weight + ? WHERE node_from = ? AND node_to = ?", (add_weight, node_from, node_to))
            conn.commit()
            #print(f"[DEBUG] Updated edge ({node_from}, {node_to}) weight += {add_weight}")

    def apply_scenario(self, scenario_type: str, line_start: Tuple[float, float], line_end: Tuple[float, float], penalty_weight: float, threshold: float) -> int:
        """Áp dụng kịch bản và lưu lại vào RAM"""
        # Lưu ý: line_start từ API là (lat, lng), cần đổi sang (x, y) nếu DB dùng (lng, lat)
        # Ở đây tôi giả định hệ toạ độ map khớp với DB (thường là x=lng, y=lat)
        p1 = (line_start[1], line_start[0]) 
        p2 = (line_end[1], line_end[0])
        start_time=time.time()
        affected = self.find_edges_near_line(p1, p2, threshold)
        end_time= time.time()
        print(f"Time load db:{end_time-start_time}")
        start_time=time.time()
        # Tối ưu hóa: Mở một kết nối duy nhất cho tất cả các lần cập nhật
        if affected:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for u, v in affected:
                    cursor.execute("UPDATE edges_session SET weight = weight + ? WHERE node_from = ? AND node_to = ?", (penalty_weight, u, v))
                conn.commit()
        end_time=time.time()
        print(f"Time adjust db:{end_time-start_time}")

        # Lưu thông tin để quản lý
        self.active_scenarios.append({
            "id": self.counter_id,
            "scenario_type": scenario_type,
            "active": True,
            "affected_edges_list": affected,
            "penalty_weight": penalty_weight,
            "line_start": {"lat": line_start[0], "lng": line_start[1]},
            "line_end": {"lat": line_end[0], "lng": line_end[1]},
            "threshold": threshold
        })
        self.counter_id += 1
        return len(affected)

    def remove_scenario(self, scenario_id: int) -> bool:
        """Hoàn tác (Xóa) kịch bản"""
        scenario = next((s for s in self.active_scenarios if s["id"] == scenario_id), None)
        if not scenario:
            return False
            
        # Tối ưu hóa: Mở một kết nối duy nhất để hoàn tác tất cả thay đổi
        if scenario["affected_edges_list"]:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for u, v in scenario["affected_edges_list"]:
                    cursor.execute("UPDATE edges_session SET weight = weight + ? WHERE node_from = ? AND node_to = ?", (-scenario["penalty_weight"], u, v))
                conn.commit()
            
        self.active_scenarios.remove(scenario)
        return True

# Singleton
_service = ScenarioService()
def get_scenario_service():
    return _service