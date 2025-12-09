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
        # 1. Lưu toạ độ Node: {node_id: (x, y)}
        self.nodes: Dict[int, Tuple[float, float]] = {}
        
        # 2. Lưu cấu trúc kề (Ai nối với Ai): {node_id: [neighbor_id_1, neighbor_id_2]}
        self.adj_list: Dict[int, List[int]] = {}
        
        # 3. Lưu trọng số GỐC (Backup): {(u, v): weight}
        self.original_weights: Dict[Tuple[int, int], float] = {}
        
        # 4. Lưu trọng số HIỆN TẠI (Đang dùng để tìm đường): {(u, v): weight}
        self.current_weights: Dict[Tuple[int, int], float] = {}
        
        # Tải dữ liệu 1 lần duy nhất khi khởi động
        self.load_graph_from_db()
    
    def load_graph_from_db(self):
        """Load graph from database into RAM (Run once on startup)"""
        print("⚡ [RAM] Loading graph from Disk to Memory...")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Load nodes
            cursor.execute("SELECT id, x, y FROM nodes")
            nodes = cursor.fetchall()
            for node in nodes:
                nid = node['id']
                # Giữ nguyên logic lật trục Y của bạn
                self.nodes[nid] = (node['x'], settings.MAP_HEIGHT - node['y'])
                self.adj_list[nid] = [] # Khởi tạo danh sách kề
            
            # Load edges
            cursor.execute("SELECT node_from, node_to, weight FROM edges")
            edges = cursor.fetchall()
            
            for edge in edges:
                u = edge['node_from']
                v = edge['node_to']
                w = edge['weight']
                
                # Chỉ thêm vào nếu cả 2 node đều tồn tại (tránh lỗi dữ liệu rác)
                if u in self.nodes and v in self.nodes:
                    # Xây dựng danh sách kề (Vô hướng -> 2 chiều)
                    self.adj_list[u].append(v)
                    #self.adj_list[v].append(u)
                    
                    # Lưu trọng số gốc
                    self.original_weights[(u, v)] = w
                    #self.original_weights[(v, u)] = w
        
        # Khởi tạo trọng số hiện tại bằng trọng số gốc
        self.current_weights = self.original_weights.copy()
        
        print(f"✓ [RAM] Loaded graph: {len(self.nodes)} nodes, {len(self.original_weights)} edges")

    # --- CÁC HÀM MỚI ĐỂ SCENARIO SERVICE GỌI ---
    
    def update_weight_in_ram(self, u: int, v: int, penalty: float):
        """
        Cập nhật trọng số trực tiếp trong RAM.
        Được gọi bởi ScenarioService. KHÔNG CHẠM VÀO DB.
        """
        # Cập nhật trọng số cho cạnh có hướng (u, v)
        if (u, v) in self.current_weights:
            self.current_weights[(u, v)] *= penalty

    def reset_weights_in_ram(self):
        """
        Khôi phục trọng số về trạng thái gốc.
        Chỉ mất O(1) hoặc O(N) rất nhanh, không cần đọc lại DB.
        """
        self.current_weights = self.original_weights.copy()
        print("🔄 [RAM] Graph weights reset to original.")

    # --- CÁC HÀM LOGIC A* (Đã sửa để dùng self.current_weights) ---

    def heuristic(self, node_id: int, goal_id: int) -> float:
        if node_id not in self.nodes or goal_id not in self.nodes:
            return float('inf')
        
        x1, y1 = self.nodes[node_id]
        x2, y2 = self.nodes[goal_id]
        
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return distance 
    
    def find_nearest_node(self, x: float, y: float) -> Optional[int]:
        if not self.nodes:
            return None
        
        min_distance = float('inf')
        nearest_node = None
        
        # Duyệt qua dict nodes trong RAM
        for node_id, pos in self.nodes.items():
            node_x, node_y = pos
            distance = math.sqrt((node_x - x) ** 2 + (node_y - y) ** 2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_node = node_id
        
        return nearest_node
    
    def a_star(self, start_id: int, goal_id: int) -> Optional[Dict]:
        if start_id not in self.nodes or goal_id not in self.nodes:
            return None
        
        open_set = [(0, start_id)]
        came_from = {}
        
        g_score = {node_id: float('inf') for node_id in self.nodes}
        g_score[start_id] = 0
        
        f_score = {node_id: float('inf') for node_id in self.nodes}
        f_score[start_id] = self.heuristic(start_id, goal_id)
        
        closed_set = set()
        
        while open_set:
            current_f, current = heapq.heappop(open_set)
            
            if current == goal_id:
                return self._reconstruct_path(came_from, current)
            
            if current in closed_set:
                continue
            
            closed_set.add(current)
            
            # Lấy danh sách hàng xóm từ adj_list
            for neighbor in self.adj_list.get(current, []):
                if neighbor in closed_set:
                    continue
                
                # QUAN TRỌNG: Lấy trọng số từ current_weights (RAM)
                edge_weight = self.current_weights.get((current, neighbor), float('inf'))
                
                tentative_g = g_score[current] + edge_weight
                
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal_id)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return None
    
    def _reconstruct_path(self, came_from: Dict, current: int) -> Dict:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        
        path_coords = []
        total_distance_physical = 0
        total_cost_weighted = 0
        
        for i, node_id in enumerate(path):
            x, y = self.nodes[node_id]
            path_coords.append({'node_id': node_id, 'x': x, 'y': y})
            
            if i < len(path) - 1:
                next_node = path[i+1]
                
                # Tính khoảng cách vật lý (Dựa trên trọng số gốc - không bị ảnh hưởng bởi mưa)
                w_orig = self.original_weights.get((node_id, next_node), 0)
                total_distance_physical += w_orig
                
                # Tính chi phí thực tế (Dựa trên trọng số hiện tại - có mưa/tắc)
                w_curr = self.current_weights.get((node_id, next_node), 0)
                total_cost_weighted += w_curr
        total_cost_weighted=round(total_cost_weighted*0.25/2, 2)
        if (total_cost_weighted>100000):
            total_cost_weighted="Blocked"
        return {
            'path': path_coords,
            'node_ids': path,
            'distance': round(total_distance_physical*0.25, 2), # Khoảng cách địa lý
            'cost': total_cost_weighted,   # Chi phí (thời gian/xăng)
            'nodes': len(path)
        }
    
    def find_path(self, start_x: float, start_y: float, end_x: float, end_y: float) -> Optional[Dict]:
        start_node = self.find_nearest_node(start_x, start_y)
        end_node = self.find_nearest_node(end_x, end_y)
        
        if start_node is None or end_node is None:
            return None
        
        if start_node == end_node:
            x, y = self.nodes[start_node]
            return {
                'path': [{'node_id': start_node, 'x': x, 'y': y}],
                'node_ids': [start_node],
                'distance': 0, 'cost': 0, 'nodes': 1
            }
        
        return self.a_star(start_node, end_node)
    
    # Hàm này không còn dùng nữa vì ta update trực tiếp, nhưng để lại cho tương thích ngược nếu cần
    def reload_graph(self):
        self.nodes = {}
        self.adj_list = {}
        self.original_weights = {}
        self.current_weights = {}
        self.load_graph_from_db()


# Singleton Instance
_pathfinding_service = None

def get_pathfinding_service() -> PathfindingService:
    global _pathfinding_service
    if _pathfinding_service is None:
        _pathfinding_service = PathfindingService()
    return _pathfinding_service