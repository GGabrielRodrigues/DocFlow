from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from docflow.application.identity import RegistrationRepository
from docflow.domain.identity import InstitutionRegistration, RegistrationConflictError
from docflow.infra.database.models import InstitutionModel, UserModel


class SqlAlchemyRegistrationRepository(RegistrationRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, registration: InstitutionRegistration) -> None:
        self.session.add(
            InstitutionModel(
                id=str(registration.institution.id),
                name=registration.institution.name,
                institution_type=registration.institution.institution_type,
                cnpj=registration.institution.cnpj,
                email=registration.institution.email,
                phone=registration.institution.phone,
                address=registration.institution.address,
            )
        )
        self.session.add(
            UserModel(
                id=str(registration.administrator.id),
                institution_id=str(registration.administrator.institution_id),
                name=registration.administrator.name,
                email=registration.administrator.email,
                password_hash=registration.administrator.password_hash,
                role=registration.administrator.role,
                status=registration.administrator.status,
            )
        )
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise RegistrationConflictError("CNPJ ou e-mail já cadastrado") from error

    def has_cnpj(self, cnpj: str) -> bool:
        return self.session.scalar(
            select(InstitutionModel.id).where(InstitutionModel.cnpj == cnpj)
        ) is not None

    def has_user_email(self, email: str) -> bool:
        return self.session.scalar(select(UserModel.id).where(UserModel.email == email)) is not None
