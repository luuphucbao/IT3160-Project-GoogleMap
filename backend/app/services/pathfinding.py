"""
Pathfinding Service
Implements A* algorithm with In-Memory Graph capability for high performance
"""
import ast
import heapq
import math
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
            
        start_node = self.find_nearest_node(start_x, start_y, vehicle_type)
        end_node = self.find_nearest_node(end_x, end_y, vehicle_type)
        
        if start_node is None or end_node is None:
            return None
        
        if start_node == end_node:
            x, y = self.graphs[vehicle_type]['nodes'][start_node]
            return {
                'path': [{'node_id': start_node, 'x': x, 'y': y}],
                'node_ids': [start_node],
                'distance': 0, 'cost': 0, 'nodes': 1
            }
        
        return self.a_star(start_node, end_node, vehicle_type, speed)
    
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