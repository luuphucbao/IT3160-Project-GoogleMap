# Quick Reference Card

## 🚀 Start Development

```bash
# Terminal 1 - Backend
cd backend
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
python -m http.server 8080
```

## 🌐 URLs

| Service | URL |
|---------|-----|
| User Interface | http://localhost:8080/index.html |
| Admin Dashboard | http://localhost:8080/admin.html |
| API Docs | http://localhost:8000/docs |
| Backend API | http://localhost:8000 |

## 🔐 Default Login

```
Username: admin
Password: admin123
```

## 📐 Coordinate System

```
Map Dimensions: 8900 × 7601 pixels
Origin (0,0): Top-left corner
X-axis: 0 → 8900 (horizontal)
Y-axis: 0 → 7601 (vertical)
```

## 📁 Key Files by Team

### Trung Anh (Admin - ✅ Complete)
```
✅ backend/app/api/auth.py
✅ backend/app/services/auth.py
✅ frontend/admin.html
✅ frontend/js/admin.js
✅ frontend/js/auth.js
```

### Giang + Hưng (Pathfinding - 🔨 To Do)
```
🔨 backend/app/services/pathfinding.py
🔨 backend/app/api/path.py
🔨 scripts/load_data.py
✅ frontend/index.html
✅ frontend/js/pathfinding.js
✅ frontend/js/map.js
```

### Bảo + Hiếu (Scenarios - 🔨 To Do)
```
🔨 backend/app/services/scenario.py
🔨 backend/app/api/scenarios.py
🔨 backend/app/schemas/scenario.py
✅ frontend/js/admin.js (UI ready)
```

## 🔧 Common Commands

### Database
```bash
# Initialize database
python -m scripts.init_db

# View database
sqlite3 backend/data/pathfinding.db

# SQL queries
SELECT * FROM nodes LIMIT 10;
SELECT * FROM edges LIMIT 10;
SELECT * FROM admin;
.exit
```

### Python Virtual Environment
```bash
# Create
python -m venv venv

# Activate
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# Deactivate
deactivate

# Install dependencies
pip install -r requirements.txt
```

### Git
```bash
# Check status
git status

# Create feature branch
git checkout -b feature/your-name

# Stage and commit
git add .
git commit -m "feat: your message"

# Push
git push -u origin feature/your-name
```

## 🐛 Quick Debugging

### Backend Not Starting
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000    # Windows
lsof -ti:8000                   # macOS/Linux

# Kill process
taskkill /PID  /F          # Windows
kill -9                    # macOS/Linux
```

### Frontend Not Loading
```bash
# Check if port 8080 is in use
netstat -ano | findstr :8080    # Windows
lsof -ti:8080                   # macOS/Linux
```

### Database Errors
```bash
# Delete and recreate
rm backend/data/pathfinding.db
python -m scripts.init_db
```

### bcrypt Error
```bash
pip uninstall passlib bcrypt -y
pip install passlib==1.7.4 bcrypt==4.0.1
```

## 📊 API Endpoints

### Authentication
```
POST   /api/login       - Login
POST   /api/logout      - Logout
GET    /api/verify      - Verify token
POST   /api/refresh     - Refresh token
```

### Pathfinding (To Implement)
```
GET    /api/path        - Find path
  Params: start_x, start_y, end_x, end_y
```

### Scenarios (To Implement)
```
POST   /api/scenarios   - Create scenario (admin only)
DELETE /api/scenarios   - Clear scenarios (admin only)
```

## 🎨 Map Styling

### Marker Colors
```javascript
Start Point:  #22c55e (green)
End Point:    #ef4444 (red)
Path Line:    #3b82f6 (blue)
Rain Zone:    #3b82f6 (blue, various opacity)
Road Block:   #ef4444 (red)
```

### Coordinate Conversion
```javascript
// Database (x, y) → Leaflet [y, x]
function dbToLeaflet(x, y) {
    return [y, x];
}

// Leaflet [lat, lng] → Database (x, y)
function leafletToDb(latlng) {
    return { x: latlng.lng, y: latlng.lat };
}
```

## 📝 Testing Checklist

### Backend
- [ ] Server starts without errors
- [ ] Can login at `/docs`
- [ ] Database has tables
- [ ] JWT tokens work

### Frontend
- [ ] Map image loads (`fixed.png`)
- [ ] Can select points on map
- [ ] Coordinates display correctly
- [ ] Admin login works

### Integration
- [ ] Frontend connects to backend
- [ ] API calls work
- [ ] Path displays on map
- [ ] Scenarios affect paths

## 💾 Data Format

### Nodes
```json
{
  "id": 1,
  "name": "Node1",
  "x": 1000,
  "y": 2000
}
```

### Edges
```json
{
  "id": 1,
  "node_from": 1,
  "node_to": 2,
  "weight": 1.5
}
```

### Path Response
```json
{
  "path": [
    {"x": 1000, "y": 2000},
    {"x": 1500, "y": 2500},
    {"x": 2000, "y": 3000}
  ],
  "distance": 1414.21,
  "cost": 14.14
}
```

## 🔍 Useful Browser Console Commands

```javascript
// Test coordinate conversion
MapModule.dbToLeaflet(4450, 3800)

// Clear map
MapModule.clearPath()

// Check auth status
authManager.isAuthenticated()

// View current username
authManager.getUsername()
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| README.md | Project overview |
| SETUP_GUIDE.md | Detailed setup |
| LOCAL_MAP_USAGE.md | Map integration |
| CHANGES_SUMMARY.md | What changed |
| QUICK_REFERENCE.md | This file |

## ⚡ Pro Tips

1. **Always activate venv before running Python commands**
2. **Check both terminals for errors**
3. **Use browser DevTools (F12) for frontend debugging**
4. **Test API endpoints in `/docs` before frontend integration**
5. **Commit frequently with clear messages**
6. **Keep your branch up to date with main**

---
📅 Last Updated: November 2024
👥 Team: Nhóm 1 - IT3160