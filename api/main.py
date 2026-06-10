"""
FastAPI entry point.

Dev:        uvicorn api.main:app --reload
Production: uvicorn api.main:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes.replace import router as replace_router
from api.routes.generate import router as generate_router

# ── CORS origins ─────────────────────────────────────────────────────
_DEFAULT_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:4173",  # Vite preview
    "http://localhost:3000",
]
_env_origins = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS: list[str] = (
    [o.strip() for o in _env_origins.split(",") if o.strip()]
    if _env_origins
    else _DEFAULT_ORIGINS
)

# ── App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Minecraft Map Editor API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ────────────────────────────────────────────────────────
app.include_router(replace_router, prefix="/api", tags=["replace"])
app.include_router(generate_router, prefix="/api", tags=["generate"])


@app.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok"}


# ── Frontend static files ─────────────────────────────────────────────
# Serves the pre-built React bundle from frontend/dist/.
# In local dev with `npm run dev`, this folder may not exist — that's fine;
# Vite's dev server handles the frontend independently on port 5173.
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    # Serve hashed asset files (JS/CSS/images) with long cache headers
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST / "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """
        Catch-all for SPA routing — return index.html for any non-asset path
        so that React Router (if added later) can handle client-side navigation.
        """
        requested = FRONTEND_DIST / full_path
        if requested.is_file():
            return FileResponse(str(requested))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
