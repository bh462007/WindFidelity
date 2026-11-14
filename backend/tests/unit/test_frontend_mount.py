from app.frontend import mount_frontend
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _app() -> FastAPI:
    app = FastAPI()

    @app.get("/api/ping")
    def ping():
        return {"ok": True}

    return app


def test_serves_the_built_frontend_without_shadowing_the_api(tmp_path):
    (tmp_path / "index.html").write_text("<div id='root'>marker</div>", encoding="utf-8")
    app = _app()

    mounted = mount_frontend(app, tmp_path)
    client = TestClient(app)

    assert mounted is True
    assert "marker" in client.get("/").text
    assert client.get("/api/ping").json() == {"ok": True}


def test_does_nothing_when_there_is_no_build(tmp_path):
    app = _app()

    mounted = mount_frontend(app, tmp_path / "missing")
    client = TestClient(app)

    assert mounted is False
    assert client.get("/").status_code == 404
    assert client.get("/api/ping").status_code == 200