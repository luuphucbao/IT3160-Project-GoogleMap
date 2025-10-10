# map_editor.py
# Single-file PyQt6 app to display map image, draw nodes & edges from SQLite DB,
# allow selecting two nodes and adding an edge between them (writes to DB).
#
# This code references logic and structure from your provided files (map_viewer.py, pathfinding.py)
# but is a standalone implementation (does NOT import those files).

import sys
import os
import math
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsEllipseItem,
    QGraphicsLineItem, QMessageBox
)
from PyQt6.QtGui import QPixmap, QPen, QBrush, QColor,QPainter
from PyQt6.QtCore import Qt, QPointF, QRectF

DB_PATH = "graph.db"        # change path if needed
MAP_IMAGE = "C:/Users/Giang/Desktop/PathFinding/app/assets/map.png"  # change to your map image path

NODE_RADIUS = 4
NODE_Z = 2
EDGE_Z = 1
SELECTED_COLOR = QColor("orange")
START_COLOR = QColor("green")
END_COLOR = QColor("blue")
NODE_COLOR = QColor("red")
EDGE_COLOR = QColor("black")

# ---------- Helper: load nodes & edges from DB (similar idea to Pathfinding.load_graph_from_db) ----------
def load_nodes_and_edges_from_db(db_path):
    """
    Return:
      nodes: dict node_id -> (x, y)  # numeric pixel coords stored in db `nodes.x,y`
      edges: list of (from_id, to_id, weight)
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    nodes = {}
    edges = []

    try:
        # nodes table: (name, x, y) as in pathfinding.py
        cur.execute("SELECT name, x, y FROM nodes")
        for name, x, y in cur.fetchall():
            # skip if coords null
            if x is None or y is None:
                continue
            try:
                nx = float(x)
                ny = float(y)
            except Exception:
                continue
            nodes[str(name)] = (nx, ny)

        # edges table: (node_from, node_to, weight)
        cur.execute("SELECT node_from, node_to, weight FROM edges")
        for a, b, w in cur.fetchall():
            edges.append((str(a), str(b), float(w) if w is not None else None))

    finally:
        conn.close()

    return nodes, edges

# ---------- Helper: insert edge into DB ----------
def insert_edge_to_db(db_path, node_from, node_to, weight):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        # Ensure table exists; adapt to your schema if needed
        # We assume edges table has (node_from TEXT, node_to TEXT, weight REAL)
        cur.execute(
            "INSERT INTO edges (node_from, node_to, weight) VALUES (?, ?, ?)",
            (node_from, node_to, weight)
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        # Could be primary key / unique constraint violation; still return False
        print("DB IntegrityError:", e)
        conn.rollback()
        return False
    except Exception as e:
        print("DB insert error:", e)
        conn.rollback()
        return False
    finally:
        conn.close()
    return True

# ---------- Graphics view that draws map, nodes and edges ----------
class MapCanvas(QGraphicsView):
    def __init__(self, map_image_path, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # load background image
        pixmap = QPixmap(map_image_path)
        if pixmap.isNull():
            print("Warning: cannot load map image:", map_image_path)
        else:
            self.bg_item = QGraphicsPixmapItem(pixmap)
            self.bg_item.setZValue(0)
            self.scene.addItem(self.bg_item)

        self.node_items = {}   # node_id -> QGraphicsEllipseItem
        self.edge_items = {}   # (u,v) -> QGraphicsLineItem
        self.nodes = {}        # node_id -> (x,y)
        self.edges = []        # list of (u,v,weight)

        self.start_node = None
        self.end_node = None
        self.selected_nodes = set()

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
         # Zoom config
        self.scale_factor = 1.0
        self.zoom_step = 1.15       # tốc độ zoom mỗi lần lăn chuột
        self.min_scale = 0.01        # zoom nhỏ nhất
        self.max_scale = 5.0        # zoom lớn nhất
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def clear_all(self):
        # remove all node and edge items
        for it in self.node_items.values():
            if it.scene(): self.scene.removeItem(it)
        for it in self.edge_items.values():
            if it.scene(): self.scene.removeItem(it)
        self.node_items.clear()
        self.edge_items.clear()
        self.nodes.clear()
        self.edges.clear()
        self.start_node = None
        self.end_node = None
        self.selected_nodes.clear()

    def load_graph(self, nodes_dict, edges_list):
        """
        nodes_dict: node_id -> (x,y)
        edges_list: list of (u,v,weight)
        """
        # clear existing visual items
        # but keep background
        for it in list(self.node_items.values()):
            if it.scene(): self.scene.removeItem(it)
        for it in list(self.edge_items.values()):
            if it.scene(): self.scene.removeItem(it)
        self.node_items.clear()
        self.edge_items.clear()

        self.nodes = dict(nodes_dict)
        self.edges = list(edges_list)

        # draw edges first (under nodes)
        pen = QPen(EDGE_COLOR)
        pen.setWidth(1)
        for u, v, w in self.edges:
            if u in self.nodes and v in self.nodes:
                x1, y1 = self.nodes[u]
                x2, y2 = self.nodes[v]
                line = QGraphicsLineItem(x1, y1, x2, y2)
                line.setPen(pen)
                line.setZValue(EDGE_Z)
                self.scene.addItem(line)
                self.edge_items[(u, v)] = line

        # draw nodes
        for nid, (x, y) in self.nodes.items():
            self._add_node_item(nid, x, y)

    def _add_node_item(self, nid, x, y):
        ellipse = QGraphicsEllipseItem(x - NODE_RADIUS, y - NODE_RADIUS, NODE_RADIUS*2, NODE_RADIUS*2)
        ellipse.setBrush(QBrush(NODE_COLOR))
        ellipse.setPen(QPen(Qt.PenStyle.NoPen))
        ellipse.setZValue(NODE_Z)
        ellipse.setToolTip(f"Node {nid}")
        self.scene.addItem(ellipse)
        self.node_items[nid] = ellipse

    def highlight_node(self, nid, role="normal"):
        """role: normal / start / end / selected"""
        if nid not in self.node_items:
            return
        item = self.node_items[nid]
        if role == "start":
            item.setBrush(QBrush(START_COLOR))
        elif role == "end":
            item.setBrush(QBrush(END_COLOR))
        elif role == "selected":
            item.setBrush(QBrush(SELECTED_COLOR))
        else:
            item.setBrush(QBrush(NODE_COLOR))

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.position().toPoint())
        # find nearest node (brute force)
        nearest = None
        min_d2 = float("inf")
        for nid, (x, y) in self.nodes.items():
            dx = x - pos.x()
            dy = y - pos.y()
            d2 = dx*dx + dy*dy
            if d2 < min_d2:
                min_d2 = d2
                nearest = nid
        # threshold: consider click only if within some pixels
        if nearest is not None and min_d2 <= (20.0**2):  # 20 px threshold
            # toggle selection logic:
            if nearest in self.selected_nodes:
                self.selected_nodes.remove(nearest)
                # if was start or end, clear accordingly
                if self.start_node == nearest:
                    self.start_node = None
                if self.end_node == nearest:
                    self.end_node = None
                self.highlight_node(nearest, "normal")
                print(f"Node {nearest} deselected")
            else:
                # if less than 2 selected, add
                if len(self.selected_nodes) < 2:
                    self.selected_nodes.add(nearest)
                    # assign start/end
                    if self.start_node is None:
                        self.start_node = nearest
                        self.highlight_node(nearest, "start")
                    elif self.end_node is None:
                        # avoid setting end same as start
                        if nearest == self.start_node:
                            # shouldn't happen due to set membership check, but guard
                            pass
                        else:
                            self.end_node = nearest
                            self.highlight_node(nearest, "end")
                    else:
                        # if both exist, just mark selected visually
                        self.highlight_node(nearest, "selected")
                    print(f"Node {nearest} selected")
                else:
                    # if already 2 selected, replace last selected (simple policy)
                    # remove one (the earlier inserted)
                    first = next(iter(self.selected_nodes))
                    self.selected_nodes.remove(first)
                    if self.start_node == first:
                        self.start_node = None
                    if self.end_node == first:
                        self.end_node = None
                    self.highlight_node(first, "normal")
                    # add new
                    self.selected_nodes.add(nearest)
                    if self.start_node is None:
                        self.start_node = nearest
                        self.highlight_node(nearest, "start")
                    elif self.end_node is None:
                        self.end_node = nearest
                        self.highlight_node(nearest, "end")
                    print(f"Replaced selection {first} with {nearest}")
            # emit nothing; just keep state
            return  # consume event
        # else default behavior (pan)
        super().mousePressEvent(event)
        # ---------- Zoom with mouse wheel ----------
    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel, centered under cursor"""
        # Lấy hướng lăn chuột
        zoom_in = event.angleDelta().y() > 0

        if zoom_in:
            factor = self.zoom_step
        else:
            factor = 1 / self.zoom_step

        new_scale = self.scale_factor * factor

        # Giới hạn mức zoom
        if new_scale < self.min_scale or new_scale > self.max_scale:
            return

        self.scale_factor = new_scale
        self.scale(factor, factor)

    def add_edge_visual(self, u, v, weight=None):
        # avoid duplicate visual if exists
        if (u, v) in self.edge_items or (v, u) in self.edge_items:
            return
        if u in self.nodes and v in self.nodes:
            x1, y1 = self.nodes[u]
            x2, y2 = self.nodes[v]
            pen = QPen(EDGE_COLOR)
            pen.setWidth(1)
            line = QGraphicsLineItem(x1, y1, x2, y2)
            line.setPen(pen)
            line.setZValue(EDGE_Z)
            self.scene.addItem(line)
            self.edge_items[(u, v)] = line
            # optionally add tooltip with weight
            if weight is not None:
                line.setToolTip(f"{u} - {v} (w={weight:.2f})")
    

# ---------- MainWindow with controls ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Map Editor - Add Edge Tool")
        self.resize(1100, 700)

        # central layouts
        central = QWidget()
        self.setCentralWidget(central)
        hbox = QHBoxLayout(central)

        # left: buttons/labels
        vbox = QVBoxLayout()
        self.info_label = QLabel("Click nodes on map to select (start -> green, end -> blue).\nSelect two nodes then click 'Add Edge'.")
        vbox.addWidget(self.info_label)

        self.load_btn = QPushButton("Load DB")
        self.load_btn.clicked.connect(self.load_db)
        vbox.addWidget(self.load_btn)

        self.add_edge_btn = QPushButton("Add Edge (between selected nodes)")
        self.add_edge_btn.clicked.connect(self.add_edge_between_selection)
        vbox.addWidget(self.add_edge_btn)

        self.refresh_btn = QPushButton("Refresh View")
        self.refresh_btn.clicked.connect(self.reload_graph)
        vbox.addWidget(self.refresh_btn)

        vbox.addStretch()
        hbox.addLayout(vbox, 0)

        # right: map canvas
        self.canvas = MapCanvas(MAP_IMAGE)
        hbox.addWidget(self.canvas, 1)

        # internal state
        self.db_path = DB_PATH
        self.nodes = {}  # node_id -> (x,y)
        self.edges = []  # (u,v,w)

        # load automatically if DB exists
        if os.path.exists(self.db_path):
            self.load_db()
        else:
            QMessageBox.information(self, "DB missing", f"Database {self.db_path} not found. Use 'Load DB' when ready.")

    def load_db(self):
        try:
            nodes, edges = load_nodes_and_edges_from_db(self.db_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load DB: {e}")
            return
        self.nodes = nodes
        self.edges = edges
        self.canvas.load_graph(self.nodes, self.edges)
        self.info_label.setText(f"Loaded {len(self.nodes)} nodes, {len(self.edges)} edges.\nSelect two nodes then click 'Add Edge'.")
        print(f"Loaded nodes: {len(nodes)}, edges: {len(edges)}")

    def reload_graph(self):
        # re-read DB and refresh visuals
        self.load_db()

    def add_edge_between_selection(self):
        # require exactly two selected nodes: start and end in canvas
        start = self.canvas.start_node
        end = self.canvas.end_node
        if start is None or end is None:
            QMessageBox.warning(self, "Selection", "Please select two nodes (start and end) by clicking on the map.")
            return
        if start == end:
            QMessageBox.warning(self, "Selection", "Start and End cannot be the same node.")
            return
        # compute euclidean distance on scene coords
        p1 = self.nodes.get(start)
        p2 = self.nodes.get(end)
        if p1 is None or p2 is None:
            QMessageBox.critical(self, "Error", "Node coordinates not found in memory.")
            return
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        dist = math.hypot(dx, dy)
        weight = dist / 100.0

        # insert into DB
        ok = insert_edge_to_db(self.db_path, start, end, weight)
        if not ok:
            QMessageBox.critical(self, "DB Error", "Failed to insert edge into DB. See console for details.")
            return

        # update in-memory and visuals
        self.edges.append((start, end, weight))
        self.canvas.add_edge_visual(start, end, weight)
        QMessageBox.information(self, "Added", f"Edge {start} -> {end} added (weight={weight:.2f}).")
        print(f"Inserted edge {start}->{end} weight {weight:.2f}")

        # Optionally clear selection or keep it
        # Here we clear selection:
        if start in self.canvas.selected_nodes:
            self.canvas.selected_nodes.remove(start)
        if end in self.canvas.selected_nodes:
            self.canvas.selected_nodes.remove(end)
        # reset highlight
        self.canvas.highlight_node(start, "normal")
        self.canvas.highlight_node(end, "normal")
        self.canvas.start_node = None
        self.canvas.end_node = None

# ---------- Run ----------
def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
