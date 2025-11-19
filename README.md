# PathFinding App - Hoàn Kiếm District Navigator

A web-based pathfinding application for finding optimal routes in Hoàn Kiếm district, Hanoi using A* algorithm with dynamic edge weights based on weather conditions and road restrictions.

## Team Members (Group 1)
- Hoàng Trung Anh (20235002)
- Lưu Phúc Bảo (202416131)
- Đặng Trung Hiếu (202416201)
- Hoàng Phúc Hưng (202416216)
- Lê Trường Giang (202416187)

## Features
- **Pathfinding**: Find optimal routes between two points using A* algorithm
- **Dynamic Edge Weights**: Adjust path costs based on weather (rain) and road restrictions
- **Admin Dashboard**: Manage scenarios (rain zones, road blocks) with authentication
- **Interactive Map**: Leaflet.js-based visualization of routes and conditions

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS, JavaScript with Leaflet.js
- **Database**: SQLite
- **Authentication**: JWT (Access + Refresh tokens)

## Project Structure
```
pathfinding-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── config.py               # Configuration settings
│   │   ├── database.py             # Database connection
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── node.py            # Node model
│   │   │   ├── edge.py            # Edge model
│   │   │   └── admin.py           # Admin user model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # Auth request/response schemas
│   │   │   ├── path.py            # Path request/response schemas
│   │   │   └── scenario.py        # Scenario schemas
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # Authentication endpoints
│   │   │   ├── path.py            # Pathfinding endpoints
│   │   │   └── scenarios.py       # Scenario management endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── pathfinding.py     # A* algorithm & graph operations
│   │   │   ├── scenario.py        # Scenario management logic
│   │   │   └── auth.py            # JWT & password handling
│   │   └── dependencies/
│   │       ├── __init__.py
│   │       └── access_control.py  # JWT verification dependencies
│   ├── data/
│   │   └── pathfinding.db         # SQLite database (generated)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html                 # User view
│   ├── admin.html                 # Admin dashboard
│   ├── css/
│   │   ├── style.css             # User view styles
│   │   └── admin.css             # Admin view styles
│   └── js/
│       ├── map.js                # Leaflet map for user view
│       ├── pathfinding.js        # Pathfinding UI logic
│       ├── admin.js              # Admin dashboard logic
│       └── auth.js               # Authentication handling
├── scripts/
│   ├── init_db.py                # Database initialization script
│   └── load_data.py              # Load nodes/edges from JSON
├── README.md
└── .gitignore
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Backend Setup

1. **Clone the repository** (or navigate to project directory)

2. **Create virtual environment**:
   ```bash
   cd backend
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

5. **Initialize database**:
   ```bash
   python -m scripts.init_db
   ```

6. **Load node and edge data** (after providing JSON data):
   ```bash
   python -m scripts.load_data --nodes data/nodes.json --edges data/edges.json
   ```

### Running the Application

1. **Start the backend server**:
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Backend will be available at: `http://localhost:8000`
   API documentation: `http://localhost:8000/docs`

2. **Serve the frontend**:
   ```bash
   # Simple Python HTTP server
   cd frontend
   python -m http.server 8080
   ```
   Frontend will be available at: `http://localhost:8080`

   **Or use any static file server like:**
   - VS Code Live Server extension
   - `npx serve`

## API Endpoints

### Authentication
- `POST /api/login` - User login (returns access & refresh tokens)
- `POST /api/logout` - User logout
- `POST /api/refresh` - Refresh access token
- `GET /api/verify` - Verify current token

### Pathfinding
- `GET /api/path` - Find optimal path between two points
  - Query params: `start_node_id`, `end_node_id`
  - Response: List of edges/nodes forming the path

### Scenarios (Admin only)
- `POST /api/scenarios` - Create/update weather or road restriction scenario
  - Body: scenario type, affected area coordinates, penalty weight

## Default Admin Account
```
Username: admin
Password: admin123
```
**⚠️ Change this in production!**

## Database Schema

### Nodes Table
```sql
CREATE TABLE nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    x REAL NOT NULL,
    y REAL NOT NULL
);
```

### Edges Table
```sql
CREATE TABLE edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_from INTEGER NOT NULL,
    node_to INTEGER NOT NULL,
    weight REAL NOT NULL,
    FOREIGN KEY (node_from) REFERENCES nodes(id),
    FOREIGN KEY (node_to) REFERENCES nodes(id)
);
```

### Admin Table
```sql
CREATE TABLE admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin'
);
```

## Development Workflow (Agile)

### Sprint 1: Basic Pathfinding (Giang + Hưng)
- [ ] Implement A* algorithm
- [ ] Create pathfinding API endpoint
- [ ] Build user interface with map
- [ ] Test basic route finding

### Sprint 2: Admin Authentication (Trung Anh)
- [x] Implement JWT authentication
- [x] Create login/logout endpoints
- [x] Build admin login page
- [x] Add access control middleware

### Sprint 3: Scenario Management (Bảo + Hiếu)
- [ ] Implement scenario logic (rain, road blocks)
- [ ] Create scenario API endpoints
- [ ] Build admin scenario UI
- [ ] Test dynamic edge weight updates

## Contributing
1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit for review

## License
Educational project for IT3160 - Introduction to AI course, HUST

---
**Instructor**: Assoc. Prof. Dr. Trần Đình Khang  
**Institution**: Hanoi University of Science and Technology