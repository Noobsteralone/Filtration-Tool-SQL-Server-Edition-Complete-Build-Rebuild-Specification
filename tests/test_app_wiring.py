"""
Smoke tests for the FastAPI application wiring itself (routers, dependency
graph). These do NOT require a live SQL Server -- database calls only
happen inside request handlers / the startup lifespan, and the lifespan
failure path is exercised here deliberately (no SQL Server is reachable
in this sandbox), proving the friendly-error behaviour from section 61.
"""
from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_db_unreachable_gracefully():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["database_ready"] is False
        assert "SQL Server connection failed" in body["database_error"]


def test_all_reference_list_routes_are_registered():
    with TestClient(app) as client:
        spec = client.get("/openapi.json").json()
        for segment in [
            "personal-domains", "restricted-domains", "spam-domains",
            "keywords", "titles", "industries", "allowed-tlds",
        ]:
            assert f"/api/reference/{segment}" in spec["paths"]
            assert f"/api/reference/{segment}/bulk" in spec["paths"]


def test_job_and_master_routes_registered():
    with TestClient(app) as client:
        spec = client.get("/openapi.json").json()
        for path in [
            "/api/jobs/upload", "/api/jobs/{job_id}/start", "/api/jobs/{job_id}/cancel",
            "/api/jobs/{job_id}/retry", "/api/jobs/{job_id}/download/{download_type}",
            "/api/master", "/api/master/merge", "/api/other-tld-master",
        ]:
            assert path in spec["paths"]


def test_protected_endpoints_require_authentication():
    with TestClient(app) as client:
        response = client.get("/api/jobs")
        assert response.status_code == 401


def test_db_dependent_endpoint_returns_friendly_error_not_a_stack_trace():
    """
    Regression test: /api/auth/login goes through the SQLAlchemy get_db()
    dependency (not the raw_connection() wrapper that /api/health uses),
    so a SQL Server outage there previously leaked a raw 500 + Python
    traceback to the client. The global DBAPIError handler in main.py
    must turn this into a clean, human-readable 503 instead (section 61).
    """
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/auth/login", json={"username": "admin", "password": "x"})
        assert response.status_code == 503
        body = response.json()
        assert "Traceback" not in body["detail"]
        assert "SQL Server connection failed" in body["detail"]
