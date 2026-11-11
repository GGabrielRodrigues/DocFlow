import pytest

from docflow.domain.identity import (
    Cnpj,
    DomainValidationError,
    InstitutionRegistration,
)


def test_cnpj_accepts_formatted_valid_number_and_normalizes_it() -> None:
    assert Cnpj("11.222.333/0001-81").value == "11222333000181"


@pytest.mark.parametrize(
    "value",
    ["11.222.333/0001-82", "11.222.333/0001-81x", "00000000000000"],
)
def test_cnpj_rejects_invalid_numbers(value: str) -> None:
    with pytest.raises(DomainValidationError, match="CNPJ inválido"):
        Cnpj(value)


def test_registration_always_creates_an_active_administrator() -> None:
    registration = InstitutionRegistration.create(
        institution_name="Escola Exemplo",
        institution_type="SCHOOL",
        cnpj="11.222.333/0001-81",
        institution_email="contato@exemplo.org",
        phone=None,
        address=None,
        administrator_name="Ana Exemplo",
        administrator_email="ana@exemplo.org",
        password="segredo123",
    )

    assert registration.institution.cnpj == "11222333000181"
    assert registration.administrator.role == "ADMIN"
    assert registration.administrator.status == "ACTIVE"
    assert registration.administrator.institution_id == registration.institution.id
    assert registration.administrator.password_hash != "segredo123"


def test_registration_rejects_short_administrator_password() -> None:
    with pytest.raises(DomainValidationError, match="senha"):
        InstitutionRegistration.create(
            institution_name="Escola Exemplo",
            institution_type="SCHOOL",
            cnpj="11.222.333/0001-81",
            institution_email="contato@exemplo.org",
            phone=None,
            address=None,
            administrator_name="Ana Exemplo",
            administrator_email="ana@exemplo.org",
            password="curta",
        )
