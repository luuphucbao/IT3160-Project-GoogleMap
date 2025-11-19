# PathFinding App - Quick Setup Guide

## 📋 Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- A code editor (VS Code recommended)
- Web browser

## 🚀 Quick Start (5 Steps)

### Step 1: Create Project Structure
```bash
# Create main directory
mkdir pathfinding-app
cd pathfinding-app

# Create subdirectories
mkdir -p backend/app/{api,models,schemas,services,dependencies}
mkdir -p backend/data
mkdir -p frontend/{css,js}
mkdir -p scripts

# Create __init__.py files for Python packages
touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/services/__init__.py
touch backend/app/dependencies/__init__.py
```

### Step 2: Copy All Files
Copy the files from the artifacts into their respective locations:
- `requirements.txt` → `backend/requirements.txt`
- `.env.example` → `backend/.env.example`
- `.gitignore` → root directory
- All Python files → their respective locations in `backend/app/`
- All HTML/CSS/JS files → `frontend/`
- Database script → `scripts/`

### Step 3: Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Generate secure secret key (optional but recommended)
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and replace SECRET_KEY in .env
```

### Step 4: Initialize Database
```bash
# Make sure you're in the backend directory with venv activated
python -m scripts.init_db
```

You should see:
```
=== Initializing PathFinding Database ===

Creating database tables...
✓ Database tables created successfully

Creating default admin user: admin
✓ Admin user created successfully
  Username: admin
  Password: admin123

⚠️  IMPORTANT: Change the default password in production!

=== Database initialization complete ===
```

### Step 5: Start the Application

**Terminal 1 - Start Backend:**
```bash
cd backend
# Make sure venv is activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
python -m http.server 8080
```

You should see:
```
Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...
```

## 🎉 Test the Application

1. **Open browser** and go to: `http://localhost:8080/admin.html`

2. **Login** with default credentials:
   - Username: `admin`
   - Password: `admin123`

3. **Test the API** at: `http://localhost:8000/docs`
   - FastAPI automatic documentation
   - Try out the endpoints interactively

## 📊 Next Steps

After confirming the admin view works, you can:

1. **Add Node & Edge Data**
   - Create JSON files with your graph data
   - Load them using `scripts/load_data.py`

2. **Implement Pathfinding**
   - Add A* algorithm in `backend/app/services/pathfinding.py`
   - Create pathfinding API endpoint
   - Build user interface in `frontend/index.html`

3. **Implement Scenarios**
   - Complete scenario logic in `backend/app/services/scenario.py`
   - Create scenarios API endpoint
   - Connect admin UI to scenarios API

## 🔧 Troubleshooting

### Port Already in Use
If you get "port already in use" errors:

**Backend (port 8000):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID  /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

**Frontend (port 8080):**
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID  /F

# macOS/Linux
lsof -ti:8080 | xargs kill -9
```

### Module Not Found Errors
Make sure you:
1. Activated the virtual environment
2. Installed all requirements: `pip install -r requirements.txt`
3. Are in the correct directory when running scripts

### CORS Errors
If you see CORS errors in browser console:
1. Check that `ALLOWED_ORIGINS` in `.env` includes your frontend URL
2. Restart the backend server after changing `.env`

### Database Errors
If database operations fail:
```bash
# Delete and recreate database
rm backend/data/pathfinding.db
python -m scripts.init_db
```

## 📝 File Structure Checklist

```
pathfinding-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py ✓
│   │   ├── main.py ✓
│   │   ├── config.py ✓
│   │   ├── database.py ✓
│   │   ├── api/
│   │   │   ├── __init__.py ✓
│   │   │   └── auth.py ✓
│   │   ├── schemas/
│   │   │   ├── __init__.py ✓
│   │   │   └── auth.py ✓
│   │   ├── services/
│   │   │   ├── __init__.py ✓
│   │   │   └── auth.py ✓
│   │   └── dependencies/
│   │       ├── __init__.py ✓
│   │       └── access_control.py ✓
│   ├── data/
│   │   └── pathfinding.db (generated)
│   ├── venv/ (generated)
│   ├── requirements.txt ✓
│   ├── .env ✓
│   └── .env.example ✓
├── frontend/
│   ├── admin.html ✓
│   ├── css/
│   │   └── admin.css ✓
│   └── js/
│       ├── auth.js ✓
│       └── admin.js ✓
├── scripts/
│   └── init_db.py ✓
├── README.md ✓
├── SETUP_GUIDE.md ✓
└── .gitignore ✓
```

## 💡 Tips

1. **Keep both terminals open** while developing
2. **Backend auto-reloads** when you change Python files (thanks to `--reload`)
3. **Frontend needs manual refresh** in browser after changes
4. **Check browser console** for JavaScript errors
5. **Check terminal** for Python errors
6. **Use API docs** at `/docs` to test backend independently

## 🆘 Need Help?

Common issues:
- Database file not found → Run `init_db.py` again
- Login fails → Check backend logs for errors
- Map doesn't load → Check browser console for Leaflet errors
- API returns 404 → Verify backend is running on port 8000

Good luck with your project! 🚀