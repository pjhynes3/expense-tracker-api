def test_health_check_is_public(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_returns_ready(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_check_returns_unavailable_when_database_is_down(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.solution.is_database_ready",
        lambda: False,
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not ready"}
