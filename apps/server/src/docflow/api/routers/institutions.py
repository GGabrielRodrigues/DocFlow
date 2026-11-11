from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from docflow.application.identity import RegisterInstitution
from docflow.domain.identity import DomainValidationError, RegistrationConflictError
from docflow.infra.identity import InMemoryRegistrationRepository


class InstitutionRegistrationData(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    institution_type: str = Field(min_length=1, max_length=50)
    cnpj: str
    email: str
    phone: str | None = None
    address: str | None = None


class AdministratorRegistrationData(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str
    password: str = Field(min_length=8, max_length=128)


class RegistrationRequest(BaseModel):
    institution: InstitutionRegistrationData
    administrator: AdministratorRegistrationData


class InstitutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    institution_type: str
    cnpj: str
    email: str
    phone: str | None
    address: str | None


class AdministratorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution_id: UUID
    name: str
    email: str
    role: str
    status: str


class RegistrationResponse(BaseModel):
    institution: InstitutionResponse
    administrator: AdministratorResponse


def create_institutions_router() -> APIRouter:
    repository = InMemoryRegistrationRepository()
    register = RegisterInstitution(repository)
    router = APIRouter(prefix="/api/v1/institutions", tags=["identity"])

    @router.post(
        "/register",
        response_model=RegistrationResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Cadastra uma instituição e seu primeiro administrador",
    )
    async def register_institution(payload: RegistrationRequest) -> RegistrationResponse:
        try:
            registration = register.execute(
                institution_name=payload.institution.name,
                institution_type=payload.institution.institution_type,
                cnpj=payload.institution.cnpj,
                institution_email=payload.institution.email,
                phone=payload.institution.phone,
                address=payload.institution.address,
                administrator_name=payload.administrator.name,
                administrator_email=payload.administrator.email,
                password=payload.administrator.password,
            )
        except RegistrationConflictError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
        except DomainValidationError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(error),
            ) from error

        return RegistrationResponse(
            institution=InstitutionResponse.model_validate(registration.institution),
            administrator=AdministratorResponse.model_validate(registration.administrator),
        )

    return router
