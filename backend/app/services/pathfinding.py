"""
Pathfinding Service
Implements A* algorithm for finding optimal paths on the graph
"""
import heapq
import math
from typing import List, Tuple, Dict, Optional
from app.database import get_db_connection


class PathfindingService:
    """Service for pathfinding operations using A* algorithm"""
    
    def __init__(self):
        self.graph = {}  # {node_id: {'pos': (x, y), 'neighbors': [(neighbor_id, weight), ...]}}
        self.load_graph()
    
    def load_graph(self):
        """Load graph from database"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Load nodes
            cursor.execute("SELECT id, x, y FROM nodes")
            nodes = cursor.fetchall()
            
            for node in nodes:
                node_id = node['id']
                self.graph[node_id] = {
                    'pos': (node['x'], node['y']),
                    'neighbors': []
                }
            
            # Load edges
            cursor.execute("SELECT node_from, node_to, weight FROM edges")
            edges = cursor.fetchall()
            
            for edge in edges:
                node_from = edge['node_from']
                node_to = edge['node_to']
                weight = edge['weight']
                
                # Add bidirectional edges (assuming undirected graph)
                if node_from in self.graph:
                    self.graph[node_from]['neighbors'].append((node_to, weight))
                if node_to in self.graph:
                    self.graph[node_to]['neighbors'].append((node_from, weight))
        
        print(f"✓ Loaded graph: {len(self.graph)} nodes")
    
    def heuristic(self, node_id: int, goal_id: int) -> float:
        """
        Calculate heuristic (estimated cost) from node to goal
        Uses Euclidean distance divided by 100 (as per your specification)
        """
        if node_id not in self.graph or goal_id not in self.graph:
            return float('inf')
        
        x1, y1 = self.graph[node_id]['pos']
        x2, y2 = self.graph[goal_id]['pos']
        
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return distance / 100
    
    def find_nearest_node(self, x: float, y: float) -> Optional[int]:
        """
        Find the nearest node to the given coordinates
        Returns node_id or None if no nodes exist
        """
        if not self.graph:
            return None
        
        min_distance = float('inf')
        nearest_node = None
        
        for node_id, data in self.graph.items():
            node_x, node_y = data['pos']
            distance = math.sqrt((node_x - x) ** 2 + (node_y - y) ** 2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_node = node_id
        
        return nearest_node
    
    def a_star(self, start_id: int, goal_id: int) -> Optional[Dict]:
        """
        A* pathfinding algorithm
        Returns path information or None if no path exists
        """
        if start_id not in self.graph or goal_id not in self.graph:
            return None
        
        # Priority queue: (f_score, node_id)
        open_set = [(0, start_id)]
        
        # For path reconstruction
        came_from = {}
        
        # Cost from start to each node
        g_score = {node_id: float('inf') for node_id in self.graph}
        g_score[start_id] = 0
        
        # Estimated total cost (f = g + h)
        f_score = {node_id: float('inf') for node_id in self.graph}
        f_score[start_id] = self.heuristic(start_id, goal_id)
        
        # Track visited nodes
        closed_set = set()
        
        while open_set:
            # Get node with lowest f_score
            current_f, current = heapq.heappop(open_set)
            
            # Goal reached!
            if current == goal_id:
                return self._reconstruct_path(came_from, current)
            
            # Skip if already processed
            if current in closed_set:
                continue
            
            closed_set.add(current)
            
            # Check all neighbors
            for neighbor, edge_weight in self.graph[current]['neighbors']:
                if neighbor in closed_set:
                    continue
                
                # Calculate tentative g_score
                tentative_g = g_score[current] + edge_weight
                
                # If this path is better
                if tentative_g < g_score[neighbor]:
                    # Update path
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal_id)
                    
                    # Add to open set
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # No path found
        return None
    
    def _reconstruct_path(self, came_from: Dict, current: int) -> Dict:
        """Reconstruct path from came_from dictionary"""
        path = [current]
        
        while current in came_from:
            current = came_from[current]
            path.append(current)
        
        path.reverse()
        
        # Convert to coordinate format
        path_coords = []
        for node_id in path:
            x, y = self.graph[node_id]['pos']
            path_coords.append({'node_id': node_id, 'x': x, 'y': y})
        
        # Calculate total distance
        total_distance = 0
        for i in range(len(path) - 1):
            x1, y1 = self.graph[path[i]]['pos']
            x2, y2 = self.graph[path[i + 1]]['pos']
            total_distance += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        
        return {
            'path': path_coords,
            'node_ids': path,
            'distance': round(total_distance, 2),
            'cost': round(total_distance / 100, 2),
            'nodes': len(path)
        }
    
    def find_path(self, start_x: float, start_y: float, 
                  end_x: float, end_y: float) -> Optional[Dict]:
        """
        Find optimal path between two coordinate points
        
        Args:
            start_x, start_y: Starting coordinates
            end_x, end_y: Ending coordinates
            
        Returns:
            Dictionary with path information or None if no path exists
        """
        # Find nearest nodes
        start_node = self.find_nearest_node(start_x, start_y)
        end_node = self.find_nearest_node(end_x, end_y)
        
        if start_node is None or end_node is None:
            return None
        
        if start_node == end_node:
            # Same node
            x, y = self.graph[start_node]['pos']
            return {
                'path': [{'node_id': start_node, 'x': x, 'y': y}],
                'node_ids': [start_node],
                'distance': 0,
                'cost': 0,
                'nodes': 1
            }
        
        # Run A* algorithm
        return self.a_star(start_node, end_node)
    
    def reload_graph(self):
        """Reload graph from database (call after edge weight updates)"""
        self.graph = {}
        self.load_graph()


# Create singleton instance
_pathfinding_service = None

def get_pathfinding_service() -> PathfindingService:
    """Get or create pathfinding service instance"""
    global _pathfinding_service
    if _pathfinding_service is None:
        _pathfinding_service = PathfindingService()
    return _pathfinding_service