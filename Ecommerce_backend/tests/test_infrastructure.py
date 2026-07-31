from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(filename: str) -> dict:
    return yaml.safe_load((ROOT / filename).read_text(encoding="utf-8"))


def test_production_compose_waits_for_dependencies_and_limits_services():
    compose = load_yaml("docker-compose.yml")
    services = compose["services"]

    assert "version" not in compose
    assert "ports" not in services["db"]
    assert "ports" not in services["redis"]
    assert services["db"]["healthcheck"]
    assert services["redis"]["healthcheck"]
    assert "volumes" not in services["redis"]
    assert services["redis"]["command"] == [
        "redis-server",
        "--save",
        "",
        "--appendonly",
        "no",
    ]
    assert services["app"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert services["app"]["depends_on"]["redis"]["condition"] == "service_healthy"
    assert (
        services["app"]["depends_on"]["migrate"]["condition"]
        == "service_completed_successfully"
    )
    assert services["app"]["read_only"] is True
    assert services["app"]["pids_limit"]
    assert all("container_name" not in service for service in services.values())


def test_development_override_is_the_only_reload_and_bind_mount_source():
    production = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    development = load_yaml("docker-compose.override.yml")

    assert "--reload" not in production
    assert "volumes" in development["services"]["app"]
    assert "--reload" in development["services"]["app"]["command"]
    assert development["services"]["app"]["image"].startswith("ecommerce-backend-dev:")
    assert "ports" in development["services"]["db"]
    assert "ports" in development["services"]["redis"]


def test_runtime_image_is_multi_stage_pinned_and_non_root():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert dockerfile.count("FROM python:3.11-slim@sha256:") == 2
    assert " AS builder" in dockerfile
    assert " AS runtime" in dockerfile
    assert "USER app" in dockerfile
    assert "COPY --chown=app:app" in dockerfile
    assert "HEALTHCHECK" in dockerfile


def test_production_requirements_exclude_development_tools():
    production = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    development = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")

    assert "pytest" not in production
    assert "watchfiles" not in production
    assert "pytest" in development
    assert "watchfiles" in development


def test_timestamp_migration_backfills_before_not_null():
    migration = (
        ROOT / "alembic" / "versions" / "c79532bfd238_init_models.py"
    ).read_text(encoding="utf-8")

    assert "UPDATE orders SET created_at = now() WHERE created_at IS NULL" in migration
    assert "UPDATE users SET created_at = now() WHERE created_at IS NULL" in migration
    assert "server_default=sa.text('now()'), nullable=False" in migration