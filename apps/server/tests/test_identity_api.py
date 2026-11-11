from fastapi.testclient import TestClient

from docflow.main import create_app


def _payload() -> dict[str, object]:
    return {
        "institution": {
            "name": "Escola Exemplo",
            "institution_type": "SCHOOL",
            "cnpj": "11.222.333/0001-81",
            "email": "contato@exemplo.org",
            "phone": None,
            "address": None,
        },
        "administrator": {
            "name": "Ana Exemplo",
            "email": "ana@exemplo.org",
            "password": "segredo123",
        },
    }


def test_registers_institution_and_first_administrator() -> None:
    response = TestClient(create_app()).post(
        "/api/v1/institutions/register",
        json=_payload(),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["institution"]["cnpj"] == "11222333000181"
    assert body["administrator"]["role"] == "ADMIN"
    assert body["administrator"]["status"] == "ACTIVE"
    assert "password" not in body["administrator"]


def test_registration_rejects_invalid_cnpj() -> None:
    payload = _payload()
    payload["institution"]["cnpj"] = "11.222.333/0001-82"  # type: ignore[index]

    response = TestClient(create_app()).post(
        "/api/v1/institutions/register",
        json=payload,
    )

    assert response.status_code == 422
    assert "CNPJ inválido" in response.json()["detail"]


def test_registration_rejects_duplicate_cnpj() -> None:
    client = TestClient(create_app())

    assert client.post("/api/v1/institutions/register", json=_payload()).status_code == 201
    response = client.post("/api/v1/institutions/register", json=_payload())

    assert response.status_code == 409
    assert response.json()["detail"] == "CNPJ já cadastrado"
