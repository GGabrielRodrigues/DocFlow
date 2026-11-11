from docflow.application.identity import RegistrationRepository
from docflow.domain.identity import InstitutionRegistration


class InMemoryRegistrationRepository(RegistrationRepository):
    def __init__(self) -> None:
        self._registrations: list[InstitutionRegistration] = []

    def save(self, registration: InstitutionRegistration) -> None:
        self._registrations.append(registration)

    def has_cnpj(self, cnpj: str) -> bool:
        return any(item.institution.cnpj == cnpj for item in self._registrations)

    def has_user_email(self, email: str) -> bool:
        return any(item.administrator.email == email for item in self._registrations)
