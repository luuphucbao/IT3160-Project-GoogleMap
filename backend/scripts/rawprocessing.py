import json
import math
import csv
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
# Giới hạn map
lonLeft = 105.840676
lonRight = 105.861112
latTop = 21.041218
latBottom = 21.023721
# Giới hạn khoảng cách pixel để chia nhỏ cạnh
LIMIT = 6
# Kích thước ảnh
WIDTH = 8500
HEIGHT = 7801

# --- Tùy chỉnh trích xuất ---
# Các biến boolean để kiểm soát loại đường nào sẽ được trích xuất.
# Đặt thành True để cho phép, False để bỏ qua.
EXTRACT_MOTORWAY = True      # motorway, motorway_link, trunk, trunk_link
EXTRACT_PRIMARY = True       # primary, primary_link, secondary, secondary_link, tertiary, tertiary_link
EXTRACT_RESIDENTIAL = True   # residential, living_street, unclassified, service
EXTRACT_OTHER_SERVICE = True # Cho phép các loại 'service' khác ngoài 'driveway'. Phụ thuộc EXTRACT_RESIDENTIAL.
EXTRACT_FOOTWAY = False       # footway, pedestrian, path, steps, bridleway, cycleway

# Nếu EXTRACT_RESIDENTIAL là False, thì EXTRACT_OTHER_SERVICE cũng sẽ bị vô hiệu hóa.
if not EXTRACT_RESIDENTIAL:
    EXTRACT_OTHER_SERVICE = False

@dataclass
class Node:
    id: int
    lat: float # Vĩ độ
    lon: float # Kinh độ
    tags: Dict[str, Any]
    x: Optional[float] = None # Tọa độ pixel
    y: Optional[float] = None # Tọa độ pixel

@dataclass
class Edge:
    start: int
    end: int
    tags: Dict[str, Any]
    weight: Optional[float] = None
    # Thêm các thuộc tính khác nếu cần, ví dụ: weight, length_px


def load_osm_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def extract_nodes(data: List[Dict[str, Any]]) -> Dict[int, Node]:
    nodes = {}
    for obj in data:
        if obj.get("type") == "node":
            nid = obj["id"]
            nodes[nid] = Node(
                id=nid,
                lat=obj["lat"],
                lon=obj["lon"],
                tags=obj.get("tags", {})
            )
    return nodes


def should_extract_highway(tags: Dict[str, Any]) -> bool:
    """Kiểm tra xem một 'way' có nên được trích xuất dựa trên các biến toàn cục hay không."""
    highway_tag = tags.get("highway")
    if not highway_tag:
        return False

    if EXTRACT_MOTORWAY and highway_tag in {"motorway", "motorway_link", "trunk", "trunk_link"}:
        return True

    if EXTRACT_PRIMARY and highway_tag in {"primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link"}:
        return True

    if EXTRACT_RESIDENTIAL:
        if highway_tag in {"residential", "living_street", "unclassified"}:
            return True
        if highway_tag == "service":
            # Nếu chỉ cho phép Residential (không OtherService), chỉ lấy service="driveway"
            if not EXTRACT_OTHER_SERVICE:
                return tags.get("service") == "driveway"
            else:
                # Nếu cho phép cả OtherService, lấy tất cả các loại service
                return True

    if EXTRACT_FOOTWAY and highway_tag in {"footway", "pedestrian", "path", "steps", "bridleway", "cycleway"}:
        return True

    return False


def extract_edges(data: List[Dict[str, Any]]) -> List[Edge]:
    edges = []
    for obj in data:
        if obj.get("type") == "way":
            tags = obj.get("tags", {})

            # Kiểm tra xem có nên trích xuất loại đường này không
            if not should_extract_highway(tags):
                continue

            node_list = obj.get("nodes", [])
            for i in range(len(node_list) - 1):
                edges.append(
                    Edge(
                        start=node_list[i],
                        end=node_list[i + 1],
                        tags=tags
                    )
                )
    return edges


def convert_coords(nodes: Dict[int, Node]):
    """Chuyển đổi (lon, lat) sang tọa độ pixel (x, y)."""
    for node in nodes.values():
        node.x = (node.lon - lonLeft) / (lonRight - lonLeft) * WIDTH
        # Gốc tọa độ ở góc trên-trái nên y được tính ngược lại từ latTop
        node.y = (latTop - node.lat) / (latTop - latBottom) * HEIGHT


def add_bidirectional_edges(edges: List[Edge]) -> List[Edge]:
    """Thêm các cạnh ngược chiều cho đường hai chiều."""
    new_edges = []
    for edge in edges:
        # Mặc định đường là 2 chiều trừ khi có tag oneway=yes
        is_oneway = edge.tags.get("oneway") == "yes"
        if not is_oneway:
            # Thêm cạnh ngược chiều
            new_edges.append(Edge(start=edge.end, end=edge.start, tags=edge.tags))
    return new_edges


def subdivide_edges(nodes: Dict[int, Node], edges: List[Edge]) -> (Dict[int, Node], List[Edge]):
    """Chia nhỏ các cạnh dài hơn LIMIT."""
    new_edges = []
    # ID cho các node mới, bắt đầu từ một số lớn để tránh trùng lặp
    new_node_id_counter = max(nodes.keys()) + 1
    subdivided_edge_count = 0
    # Cache để lưu các đỉnh trung gian đã tạo cho một cặp node (u, v)
    # Key là tuple (min(u,v), max(u,v)), value là list các ID của node trung gian
    subdivided_cache: Dict[tuple[int, int], list[int]] = {}

    for edge in edges:
        canonical_edge = tuple(sorted((edge.start, edge.end)))
        start_node = nodes[edge.start]
        end_node = nodes[edge.end]

        dist = math.sqrt((start_node.x - end_node.x)**2 + (start_node.y - end_node.y)**2)

        if dist <= LIMIT:
            new_edges.append(edge)
            continue

        subdivided_edge_count += 1

        # Nếu cạnh ngược chiều đã được chia nhỏ, tái sử dụng các node trung gian
        if canonical_edge in subdivided_cache:
            intermediate_nodes = subdivided_cache[canonical_edge]
            # Nối các node theo thứ tự ngược lại
            all_nodes_in_path = [edge.start] + intermediate_nodes[::-1] + [edge.end]
            for i in range(len(all_nodes_in_path) - 1):
                new_edges.append(Edge(start=all_nodes_in_path[i], end=all_nodes_in_path[i+1], tags=edge.tags))
        else:
            # Nếu chưa, thực hiện chia nhỏ và lưu vào cache
            num_segments = math.ceil(dist / LIMIT)
            intermediate_nodes_ids = []
            last_node_id = edge.start

            for i in range(1, int(num_segments)):
                # Nội suy tuyến tính để tìm vị trí các điểm mới
                ratio = i / num_segments
                new_x = start_node.x + ratio * (end_node.x - start_node.x)
                new_y = start_node.y + ratio * (end_node.y - start_node.y)
                # Chuyển đổi ngược lại từ pixel sang lat/lon cho điểm mới
                new_lon = lonLeft + (new_x / WIDTH) * (lonRight - lonLeft)
                new_lat = latTop - (new_y / HEIGHT) * (latTop - latBottom)

                new_node = Node(id=new_node_id_counter, lat=new_lat, lon=new_lon, tags={}, x=new_x, y=new_y)
                nodes[new_node_id_counter] = new_node
                intermediate_nodes_ids.append(new_node_id_counter)

                # Nối đỉnh trước đó với đỉnh mới
                new_edges.append(Edge(start=last_node_id, end=new_node_id_counter, tags=edge.tags))

                last_node_id = new_node_id_counter
                new_node_id_counter += 1

            # Nối đỉnh mới cuối cùng với đỉnh kết thúc của cạnh ban đầu
            new_edges.append(Edge(start=last_node_id, end=edge.end, tags=edge.tags))
            # Lưu các node trung gian vào cache
            subdivided_cache[canonical_edge] = intermediate_nodes_ids

    print(f"Thao tác 5: Chia nhỏ cạnh. Số cạnh bị chia: {subdivided_edge_count}")
    return nodes, new_edges


def main(input_file: str):
    json_data = load_osm_json(input_file)
    elements = json_data.get("elements", [])

    nodes = extract_nodes(elements)
    edges = extract_edges(elements)

    print(f"Số liệu ban đầu: {len(nodes)} nodes, {len(edges)} edges")
    print("-" * 30)

    # 1. Chuyển tọa độ (kinh độ, vĩ độ) thành (x,y)
    convert_coords(nodes)
    print("Thao tác 3: Đã chuyển đổi tọa độ (lon, lat) sang (x, y) cho các node.")

    # 2. Thêm các cạnh (v,u) tương ứng với mỗi cạnh (u,v) là đường hai chiều
    bidirectional_edges_to_add = add_bidirectional_edges(edges)
    num_added_edges = len(bidirectional_edges_to_add)
    edges.extend(bidirectional_edges_to_add)
    print(f"Thao tác 4: Thêm cạnh hai chiều. Số cạnh được thêm: {num_added_edges}")
    print(f"Tổng số cạnh sau khi thêm: {len(edges)}")
    print(f"--> Số liệu hiện tại: {len(nodes)} nodes, {len(edges)} edges")
    print("-" * 30)

    # 3. Chia nhỏ các cạnh
    nodes_before_subdivide = len(nodes)
    edges_before_subdivide = len(edges)
    nodes, edges = subdivide_edges(nodes, edges)
    print(f"  -> Số node mới được thêm: {len(nodes) - nodes_before_subdivide}")
    print(f"  -> Tổng số cạnh sau khi chia nhỏ: {len(edges)} (thay đổi từ {edges_before_subdivide})")
    print(f"--> Số liệu hiện tại: {len(nodes)} nodes, {len(edges)} edges")
    print("-" * 30)

    # 4. (Đã di chuyển) Loại bỏ các đỉnh không thỏa mãn
    initial_node_count = len(nodes)
    nodes_in_bounds = {nid: node for nid, node in nodes.items() if lonLeft <= node.lon <= lonRight and latBottom <= node.lat <= latTop}
    print(f"Thao tác 1 (sau chia nhỏ): Lọc node. Số node bị loại bỏ: {initial_node_count - len(nodes_in_bounds)}")
    nodes = nodes_in_bounds
    print(f"--> Số liệu hiện tại: {len(nodes)} nodes, {len(edges)} edges (cạnh chưa được lọc)")

    # 5. (Đã di chuyển) Loại bỏ các cạnh mà không có 2 đỉnh đều thỏa mãn
    initial_edge_count = len(edges)
    valid_edges = [edge for edge in edges if edge.start in nodes and edge.end in nodes]
    print(f"Thao tác 2 (sau chia nhỏ): Lọc edge. Số edge bị loại bỏ: {initial_edge_count - len(valid_edges)}")
    edges = valid_edges
    print(f"--> Số liệu hiện tại: {len(nodes)} nodes, {len(edges)} edges")
    print("-" * 30)

    # 6. (Mới) Loại bỏ các đỉnh và cạnh trùng lặp
    print("Thao tác 6: Loại bỏ các đỉnh và cạnh trùng lặp.")
    # Loại bỏ cạnh trùng
    initial_edge_count = len(edges)
    seen_edges = set()
    unique_edges = []
    for edge in edges:
        # Sắp xếp để coi (u,v) và (v,u) là khác nhau
        edge_tuple = (edge.start, edge.end)
        if edge_tuple not in seen_edges:
            unique_edges.append(edge)
            seen_edges.add(edge_tuple)
    edges = unique_edges
    print(f"  -> Đã loại bỏ {initial_edge_count - len(edges)} cạnh trùng lặp.")

    # Loại bỏ các đỉnh không được sử dụng sau khi đã xóa cạnh
    nodes_in_use = {edge.start for edge in edges} | {edge.end for edge in edges}
    nodes = {nid: node for nid, node in nodes.items() if nid in nodes_in_use}
    print(f"--> Số liệu hiện tại: {len(nodes)} nodes, {len(edges)} edges")

    print("Hoàn tất xử lý.")
    print(f"Kết quả cuối cùng: {len(nodes)} nodes, {len(edges)} edges")

    # 7. (Mới) Tính độ dài Euclid của mỗi cạnh
    print("Thực hiện tác vụ 7: Tính độ dài Euclid cho mỗi cạnh.")
    for edge in edges:
        start_node = nodes.get(edge.start)
        end_node = nodes.get(edge.end)
        if start_node and end_node:
            dist = math.sqrt((start_node.x - end_node.x)**2 + (start_node.y - end_node.y)**2)
            edge.weight = dist
    print(f"  -> Đã tính trọng số cho {len(edges)} cạnh.")
    print("-" * 30)
    
    # 8. (Mới) Lưu nodes và edges vào file .csv
    print("Thực hiện tác vụ 8: Bắt đầu lưu vào file CSV...")
    with open("nodes.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "pixel_x", "pixel_y"])
        writer.writerows([[node.id, node.x, node.y] for node in nodes.values()])
    print("  -> Đã lưu nodes.csv")

    with open("edges.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["u", "v", "weight"])
        writer.writerows([[edge.start, edge.end, edge.weight] for edge in edges])
    print("  -> Đã lưu edges.csv")
    print("Lưu file CSV hoàn tất.")


if __name__ == "__main__":
    input_file="export1.json"
    main(input_file)
