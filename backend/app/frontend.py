from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def mount_frontend(app: FastAPI, directory: Path) -> bool:
    """Serve a built frontend at "/" if one exists. Returns whether it was mounted.

    Call this after the API routers are included, so API routes keep priority.
    """
    if not (directory / "index.html").is_file():
        return False

    app.mount("/", StaticFiles(directory=directory, html=True), name="frontend")
    return True