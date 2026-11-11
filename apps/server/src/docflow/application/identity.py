from __future__ import annotations

from typing import Protocol

from docflow.domain.identity import (
    InstitutionRegistration,
    RegistrationConflictError,
)


class RegistrationRepository(Protocol):
    def save(self, registration: InstitutionRegistration) -> None: ...

    def has_cnpj(self, cnpj: str) -> bool: ...

    def has_user_email(self, email: str) -> bool: ...


class RegisterInstitution:
    def __init__(self, repository: RegistrationRepository) -> None:
        self.repository = repository

    def execute(self, **data: str | None) -> InstitutionRegistration:
        registration = InstitutionRegistration.create(
            institution_name=data["institution_name"] or "",
            institution_type=data["institution_type"] or "",
            cnpj=data["cnpj"] or "",
            institution_email=data["institution_email"] or "",
            phone=data["phone"],
            address=data["address"],
            administrator_name=data["administrator_name"] or "",
            administrator_email=data["administrator_email"] or "",
            password=data["password"] or "",
        )
        if self.repository.has_cnpj(registration.institution.cnpj):
            raise RegistrationConflictError("CNPJ já cadastrado")
        if self.repository.has_user_email(registration.administrator.email):
            raise RegistrationConflictError("E-mail do administrador já cadastrado")
        self.repository.save(registration)
        return registration
