# Backend/main.py
import sys
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure the Backend directory is in the python path
sys.path.append(str(Path(__file__).parent.parent))

from Backend.config.settings import FRONTEND_DIR
from Backend.api.routes import router
from Backend.services.memory import memory_service
from Backend.services.animation import animation_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- 🚀 AI HUB BACKEND STARTING ---")
    await memory_service.start()
    await animation_service.run_startup_scan()
    yield
    print("--- 🛑 SHUTDOWN ---")

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router)

# Static Files
if FRONTEND_DIR.exists():
    # If the frontend folder exists, mount its static subfolder and serve index.html
    static_path = FRONTEND_DIR / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    @app.get("/")
    async def root():
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"status": "Frontend index.html not found in /Frontend"}
else:
    @app.get("/")
    async def root():
        return {"status": "Frontend folder not found. Please create a /Frontend folder."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Backend.main:app", host="0.0.0.0", port=8000, reload=True)
