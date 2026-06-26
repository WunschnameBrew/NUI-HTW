# Backend/services/animation.py
import os
import json
import asyncio
from pathlib import Path
from Backend.config.settings import FRONTEND_DIR

ANIMATION_ROOT = FRONTEND_DIR / "static" / "assets" / "animations"
CONVERTED_DIR = ANIMATION_ROOT / "converted_gltf"

class AnimationService:
    def __init__(self):
        pass

    async def get_animations(self):
        """Returns a list of available animations from the converted folder."""
        if not CONVERTED_DIR.exists():
            return []
        return [f.name for f in CONVERTED_DIR.glob("*.vrma")]

    async def run_startup_scan(self):
        # We assume animations are already converted or the user handles them.
        # This is a stub to keep the frontend happy if it expects a scan.
        print("🎬 Animation Service Ready.")

animation_service = AnimationService()
