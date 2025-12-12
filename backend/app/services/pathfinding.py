"""
Pathfinding Service
Implements A* algorithm with In-Memory Graph capability for high performance
"""
import ast
import heapq
import math
import uuid
from typing import List, Tuple, Dict, Optional
from app.database import get_db_connection
from app.config import get_settings

settings = get_settings()

class PathfindingService:
    """Service for pathfinding operations using A* algorithm"""
    
    def __init__(self):
        # Cấu trúc dữ liệu mới: Lưu trữ 2 đồ thị riêng biệt
        self.graphs = {
            'car': {'nodes': {}, 'adj_list': {}, 'original_weights': {}, 'current_weights': {}},
            'foot': {'nodes': {}, 'adj_list': {}, 'original_weights': {}, 'current_weights': {}}
        }
        # Mapping để truy cập nhanh
        self.vehicle_types = ['car', 'foot']
        
        # Tải dữ liệu 1 lần duy nhất khi khởi động
        self.load_graph_from_db()
    
    def load_graph_from_db(self):
        """Load graph from database into RAM (Run once on startup)"""
        print("⚡ [RAM] Loading graph from Disk to Memory...")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for v_type in self.vehicle_types:
                # Load nodes
                table_nodes = f"nodes_{v_type}"
                cursor.execute(f"SELECT id, x, y FROM {table_nodes}")
                nodes = cursor.fetchall()
                
                graph = self.graphs[v_type]
                
                for node in nodes:
                    nid = node['id']
                    # Giữ nguyên logic lật trục Y của bạn
                    graph['nodes'][nid] = (node['x'], settings.MAP_HEIGHT - node['y'])
                    graph['adj_list'][nid] = [] # Khởi tạo danh sách kề
                
                # Load edges
                table_edges = f"edges_{v_type}"
                cursor.execute(f"SELECT node_from, node_to, weight FROM {table_edges}")
                edges = cursor.fetchall()
                
                for edge in edges:
                    u = edge['node_from']
                    v = edge['node_to']
                    w = edge['weight']
                    
                    # Chỉ thêm vào nếu cả 2 node đều tồn tại
                    if u in graph['nodes'] and v in graph['nodes']:
                        graph['adj_list'][u].append(v)
                        graph['original_weights'][(u, v)] = w
            
                # Khởi tạo trọng số hiện tại bằng trọng số gốc
                graph['current_weights'] = graph['original_weights'].copy()
                print(f"✓ [RAM] Loaded {v_type} graph: {len(graph['nodes'])} nodes, {len(graph['original_weights'])} edges")

    # --- CÁC HÀM HÌNH HỌC & BIẾN ĐỔI GRAPH (CHO YÊU CẦU 1 & 2) ---

    def find_nearest_edge_projection(self, x: float, y: float, vehicle_type: str) -> Optional[Tuple]:
        """
        Tìm cạnh gần nhất mà hình chiếu của điểm (x,y) nằm trong đoạn thẳng (tam giác nhọn).
        Trả về: (u, v, projection_point, distance)
        """
        if vehicle_type not in self.graphs:
            return None
        
        graph = self.graphs[vehicle_type]
        best_dist = float('inf')
        best_result = None
        
        # Duyệt qua tất cả các cạnh
        for (u, v), _ in graph['original_weights'].items():
            if u not in graph['nodes'] or v not in graph['nodes']:
                continue
                
            p1 = graph['nodes'][u]
            p2 = graph['nodes'][v]
            
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            
            if dx == 0 and dy == 0: continue
            
            # Vector AP
            ap_x = x - p1[0]
            ap_y = y - p1[1]
            
            # Tính t (projection scalar)
            len_sq = dx*dx + dy*dy
            t = (ap_x * dx + ap_y * dy) / len_sq
            
            # Kiểm tra hình chiếu nằm trong đoạn (0 <= t <= 1)
            if 0 <= t <= 1:
                proj_x = p1[0] + t * dx
                proj_y = p1[1] + t * dy
                
                dist = math.sqrt((x - proj_x)**2 + (y - proj_y)**2)
                
                if dist < best_dist:
                    best_dist = dist
                    best_result = (u, v, (proj_x, proj_y), dist)
                    
        return best_result

    def split_edge(self, u, v, split_point: Tuple[float, float], vehicle_type: str) -> Dict:
        """
        Chia cạnh (u,v) tại điểm split_point thành (u, X) và (X, v).
        Trả về thông tin để undo.
        """
        graph = self.graphs[vehicle_type]
        temp_id = f"temp_{uuid.uuid4().hex[:8]}"
        
        # 1. Thêm node mới
        graph['nodes'][temp_id] = split_point
        graph['adj_list'][temp_id] = []
        
        # 2. Tính toán khoảng cách mới
        p_u = graph['nodes'][u]
        p_v = graph['nodes'][v]
        dist_u_x = math.sqrt((p_u[0]-split_point[0])**2 + (p_u[1]-split_point[1])**2)
        dist_x_v = math.sqrt((p_v[0]-split_point[0])**2 + (p_v[1]-split_point[1])**2)

        # --- FIX: TÍNH TỶ LỆ PHẠT HIỆN TẠI ---
        # Nếu cạnh cũ đang bị phạt (mưa/tắc), cạnh mới cũng phải chịu phạt tương ứng
        old_w_orig = graph['original_weights'].get((u, v), 1)
        old_w_curr = graph['current_weights'].get((u, v), 1)
        # Tỷ lệ penalty (ví dụ: 1.0 là bth, 2.0 là mưa to)
        penalty_ratio = old_w_curr / old_w_orig if old_w_orig > 0 else 1.0
        
        # 3. Lưu trạng thái cũ để Undo
        undo_info = {
            'action': 'split', 'temp_id': temp_id, 'u': u, 'v': v,
            'old_w_uv': graph['original_weights'].get((u, v)),
            'old_curr_uv': graph['current_weights'].get((u, v)),
            'has_reverse': False
        }

        # 4. Cập nhật cạnh thuận (u, v) -> (u, X), (X, v)
        if v in graph['adj_list'][u]: graph['adj_list'][u].remove(v)
        graph['adj_list'][u].append(temp_id)
        graph['adj_list'][temp_id].append(v)
        
        if (u, v) in graph['original_weights']: del graph['original_weights'][(u, v)]
        if (u, v) in graph['current_weights']: del graph['current_weights'][(u, v)]
        
        graph['original_weights'][(u, temp_id)] = dist_u_x
        graph['current_weights'][(u, temp_id)] = dist_u_x * penalty_ratio
        graph['original_weights'][(temp_id, v)] = dist_x_v
        graph['current_weights'][(temp_id, v)] = dist_x_v * penalty_ratio
        
        # 5. Cập nhật cạnh nghịch (v, u) nếu có
        if u in graph['adj_list'].get(v, []):
            undo_info['has_reverse'] = True
            undo_info['old_w_vu'] = graph['original_weights'].get((v, u))
            undo_info['old_curr_vu'] = graph['current_weights'].get((v, u))
            
            graph['adj_list'][v].remove(u)
            graph['adj_list'][v].append(temp_id)
            graph['adj_list'][temp_id].append(u)
            
            if (v, u) in graph['original_weights']: del graph['original_weights'][(v, u)]
            if (v, u) in graph['current_weights']: del graph['current_weights'][(v, u)]
            
            graph['original_weights'][(v, temp_id)] = dist_x_v
            graph['current_weights'][(v, temp_id)] = dist_x_v * penalty_ratio
            graph['original_weights'][(temp_id, u)] = dist_u_x
            graph['current_weights'][(temp_id, u)] = dist_u_x * penalty_ratio
            
        return undo_info

    def restore_graph_changes(self, changes: List[Dict], vehicle_type: str):
        """Khôi phục graph dựa trên danh sách thay đổi (Undo)"""
        graph = self.graphs[vehicle_type]
        for change in reversed(changes):
            if change['action'] == 'split':
                temp_id = change['temp_id']
                u, v = change['u'], change['v']
                
                # Xóa node tạm
                if temp_id in graph['nodes']: del graph['nodes'][temp_id]
                if temp_id in graph['adj_list']: del graph['adj_list'][temp_id]
                
                # Khôi phục cạnh thuận
                if temp_id in graph['adj_list'][u]: graph['adj_list'][u].remove(temp_id)
                graph['adj_list'][u].append(v)
                
                # Xóa weights mới
                for k in [(u, temp_id), (temp_id, v)]:
                    if k in graph['original_weights']: del graph['original_weights'][k]
                    if k in graph['current_weights']: del graph['current_weights'][k]
                
                # Khôi phục weights cũ
                if change['old_w_uv'] is not None:
                    graph['original_weights'][(u, v)] = change['old_w_uv']
                    graph['current_weights'][(u, v)] = change['old_curr_uv']
                
                # Khôi phục cạnh nghịch
                if change['has_reverse']:
                    if temp_id in graph['adj_list'][v]: graph['adj_list'][v].remove(temp_id)
                    graph['adj_list'][v].append(u)
                    
                    for k in [(v, temp_id), (temp_id, u)]:
                        if k in graph['original_weights']: del graph['original_weights'][k]
                        if k in graph['current_weights']: del graph['current_weights'][k]
                        
                    if change['old_w_vu'] is not None:
                        graph['original_weights'][(v, u)] = change['old_w_vu']
                        graph['current_weights'][(v, u)] = change['old_curr_vu']

    # --- CÁC HÀM MỚI ĐỂ SCENARIO SERVICE GỌI ---
    
    def update_weight_in_ram(self, u: int, v: int, penalty: float, vehicle_type: str):
        """
        Cập nhật trọng số trực tiếp trong RAM.
        Được gọi bởi ScenarioService. KHÔNG CHẠM VÀO DB.
        """
        if vehicle_type in self.graphs:
            current_weights = self.graphs[vehicle_type]['current_weights']
            if (u, v) in current_weights:
                current_weights[(u, v)] *= penalty

    def reset_weights_in_ram(self):
        """
        Khôi phục trọng số về trạng thái gốc.
        Chỉ mất O(1) hoặc O(N) rất nhanh, không cần đọc lại DB.
        """
        for v_type in self.vehicle_types:
            self.graphs[v_type]['current_weights'] = self.graphs[v_type]['original_weights'].copy()
        print("🔄 [RAM] Graph weights reset to original.")

    # --- CÁC HÀM LOGIC A* (Đã sửa để dùng self.current_weights) ---

    def heuristic(self, node_id: int, goal_id: int, nodes_map: Dict) -> float:
        if node_id not in nodes_map or goal_id not in nodes_map:
            return float('inf')
        
        x1, y1 = nodes_map[node_id]
        x2, y2 = nodes_map[goal_id]
        
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return distance 
    
    def find_nearest_node(self, x: float, y: float, vehicle_type: str) -> Optional[int]:
        if vehicle_type not in self.graphs:
            return None
            
        nodes_map = self.graphs[vehicle_type]['nodes']
        if not nodes_map:
            return None
        
        min_distance = float('inf')
        nearest_node = None
        
        # Duyệt qua dict nodes trong RAM
        for node_id, pos in nodes_map.items():
            node_x, node_y = pos
            distance = math.sqrt((node_x - x) ** 2 + (node_y - y) ** 2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_node = node_id
        
        return nearest_node
    
    def a_star(self, start_id: int, goal_id: int, vehicle_type: str, speed: float) -> Optional[Dict]:
        if vehicle_type not in self.graphs:
            return None
            
        graph = self.graphs[vehicle_type]
        nodes = graph['nodes']
        
        if start_id not in nodes or goal_id not in nodes:
            return None
        
        open_set = [(0, start_id)]
        came_from = {}
        
        g_score = {node_id: float('inf') for node_id in nodes}
        g_score[start_id] = 0
        
        f_score = {node_id: float('inf') for node_id in nodes}
        f_score[start_id] = self.heuristic(start_id, goal_id, nodes)
        
        closed_set = set()
        
        while open_set:
            current_f, current = heapq.heappop(open_set)
            
            if current == goal_id:
                return self._reconstruct_path(came_from, current, vehicle_type, speed)
            
            if current in closed_set:
                continue
            
            closed_set.add(current)
            
            # Lấy danh sách hàng xóm từ adj_list
            for neighbor in graph['adj_list'].get(current, []):
                if neighbor in closed_set:
                    continue
                
                # QUAN TRỌNG: Lấy trọng số từ current_weights (RAM)
                edge_weight = graph['current_weights'].get((current, neighbor), float('inf'))
                
                tentative_g = g_score[current] + edge_weight
                
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal_id, nodes)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return None
    
    def _reconstruct_path(self, came_from: Dict, current: int, vehicle_type: str, speed: float) -> Dict:
        graph = self.graphs[vehicle_type]
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        
        path_coords = []
        total_distance_physical = 0
        total_cost_weighted = 0
        
        for i, node_id in enumerate(path):
            x, y = graph['nodes'][node_id]
            path_coords.append({'node_id': node_id, 'x': x, 'y': y})
            
            if i < len(path) - 1:
                next_node = path[i+1]
                
                # Tính khoảng cách vật lý (Dựa trên trọng số gốc - không bị ảnh hưởng bởi mưa)
                w_orig = graph['original_weights'].get((node_id, next_node), 0)
                total_distance_physical += w_orig
                
                # Tính chi phí thực tế (Dựa trên trọng số hiện tại - có mưa/tắc)
                w_curr = graph['current_weights'].get((node_id, next_node), 0)
                total_cost_weighted += w_curr
        
        # Tính thời gian dựa trên tốc độ (Distance / Speed)
        # Giả sử weight là mét, speed là m/s (hoặc đơn vị tương ứng từ frontend)
        # Nếu speed = 0 hoặc None, tránh chia cho 0

        if speed <= 0: speed = 1
        total_distance_physical*=0.25
        total_cost_weighted*=0.25
        time_cost = round(total_cost_weighted / speed, 2)
        
        if (total_cost_weighted>100000):
            time_cost="Blocked"
            
        return {
            'path': path_coords,
            'node_ids': path,
            'distance': round(total_distance_physical, 2), # Khoảng cách địa lý
            'cost': time_cost,   # Chi phí (thời gian)
            'nodes': len(path)
        }
    
    def find_path(self, start_x: float, start_y: float, end_x: float, end_y: float, vehicle_type: str, speed: float) -> Optional[Dict]:
        if vehicle_type not in self.graphs:
            return None
        
        changes = [] # Lưu các thay đổi tạm thời để restore sau
        
        try:
            # 1. Tìm và thêm điểm Start (Hình chiếu lên cạnh)
            start_info = self.find_nearest_edge_projection(start_x, start_y, vehicle_type)
            if start_info:
                u, v, proj, _ = start_info
                # Split cạnh để thêm điểm Start vào đồ thị
                change = self.split_edge(u, v, proj, vehicle_type)
                changes.append(change)
                start_node = change['temp_id']
            else:
                # Fallback nếu không tìm được hình chiếu (quá xa hoặc lỗi)
                start_node = self.find_nearest_node(start_x, start_y, vehicle_type)

            # 2. Tìm và thêm điểm End
            end_info = self.find_nearest_edge_projection(end_x, end_y, vehicle_type)
            if end_info:
                u, v, proj, _ = end_info
                change = self.split_edge(u, v, proj, vehicle_type)
                changes.append(change)
                end_node = change['temp_id']
            else:
                end_node = self.find_nearest_node(end_x, end_y, vehicle_type)
            
            if start_node is None or end_node is None:
                return None
            
            # 3. Tìm đường
            result = self.a_star(start_node, end_node, vehicle_type, speed)
            return result
            
        finally:
            # 4. Khôi phục đồ thị (Xóa các điểm tạm)
            if changes:
                self.restore_graph_changes(changes, vehicle_type)
    
    # Hàm này không còn dùng nữa vì ta update trực tiếp, nhưng để lại cho tương thích ngược nếu cần
    def reload_graph(self):
        self.graphs = {
            'car': {'nodes': {}, 'adj_list': {}, 'original_weights': {}, 'current_weights': {}},
            'foot': {'nodes': {}, 'adj_list': {}, 'original_weights': {}, 'current_weights': {}}
        }
        self.load_graph_from_db()


# Singleton Instance
_pathfinding_service = None

def get_pathfinding_service() -> PathfindingService:
    global _pathfinding_service
    if _pathfinding_service is None:
        _pathfinding_service = PathfindingService()
    return _pathfinding_service