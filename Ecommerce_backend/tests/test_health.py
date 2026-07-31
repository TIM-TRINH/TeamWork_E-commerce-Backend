from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app import main


class ConnectionContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, statement):
        return 1


class HealthyEngine:
    def connect(self):
        return ConnectionContext()


class UnhealthyEngine:
    def connect(self):
        raise SQLAlchemyError("database unavailable")


class HealthyRedis:
    def ping(self):
        return True


def test_liveness_does_not_require_external_dependencies():
    response = TestClient(main.app).get("/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_reports_ready_when_dependencies_respond(monkeypatch):
    monkeypatch.setattr(main, "engine", HealthyEngine())
    monkeypatch.setattr(main, "redis_client", HealthyRedis())

    response = TestClient(main.app).get("/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_returns_503_without_internal_details(monkeypatch):
    monkeypatch.setattr(main, "engine", UnhealthyEngine())
    monkeypatch.setattr(main, "redis_client", HealthyRedis())

    response = TestClient(main.app).get("/v1/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}