from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import auth
# Uncomment when pathfinding is implemented:
# from app.api import path

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="PathFinding application for Hoàn Kiếm district with A* algorithm",
    version="1.0.0",
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
# Uncomment when pathfinding is implemented:
# app.include_router(path.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "PathFinding API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)