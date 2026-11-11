from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from uuid import UUID, uuid4


class DomainValidationError(ValueError):
    """Raised when an identity invariant is violated."""


class RegistrationConflictError(ValueError):
    """Raised when a registration would duplicate an identity."""


def _digits(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def _is_valid_cnpj(value: str) -> bool:
    if not re.fullmatch(r"[0-9./\-\s]+", value):
        return False
    digits = _digits(value)
    if len(digits) != 14 or len(set(digits)) == 1:
        return False

    first_weights = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    first_sum = sum(
        int(digit) * weight for digit, weight in zip(digits[:12], first_weights, strict=True)
    )
    first_check = (first_sum * 10) % 11
    if first_check == 10:
        first_check = 0
    if first_check != int(digits[12]):
        return False

    second_weights = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    second_sum = sum(
        int(digit) * weight for digit, weight in zip(digits[:13], second_weights, strict=True)
    )
    second_check = (second_sum * 10) % 11
    if second_check == 10:
        second_check = 0
    return second_check == int(digits[13])


class Cnpj:
    def __init__(self, value: str) -> None:
        normalized = _digits(value)
        if not _is_valid_cnpj(value):
            raise DomainValidationError("CNPJ inválido")
        self.value = normalized


def _normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        raise DomainValidationError("E-mail inválido")
    return normalized


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


@dataclass(frozen=True, slots=True)
class Institution:
    id: UUID
    name: str
    institution_type: str
    cnpj: str
    email: str
    phone: str | None
    address: str | None


@dataclass(frozen=True, slots=True)
class Administrator:
    id: UUID
    institution_id: UUID
    name: str
    email: str
    password_hash: str
    role: str = "ADMIN"
    status: str = "ACTIVE"


@dataclass(frozen=True, slots=True)
class InstitutionRegistration:
    institution: Institution
    administrator: Administrator

    @classmethod
    def create(
        cls,
        *,
        institution_name: str,
        institution_type: str,
        cnpj: str,
        institution_email: str,
        phone: str | None,
        address: str | None,
        administrator_name: str,
        administrator_email: str,
        password: str,
    ) -> InstitutionRegistration:
        if not institution_name.strip():
            raise DomainValidationError("Nome da instituição é obrigatório")
        if not institution_type.strip():
            raise DomainValidationError("Tipo da instituição é obrigatório")
        if not administrator_name.strip():
            raise DomainValidationError("Nome do administrador é obrigatório")
        if len(password) < 8:
            raise DomainValidationError("A senha deve ter pelo menos 8 caracteres")

        institution_id = uuid4()
        institution = Institution(
            id=institution_id,
            name=institution_name.strip(),
            institution_type=institution_type.strip().upper(),
            cnpj=Cnpj(cnpj).value,
            email=_normalize_email(institution_email),
            phone=phone,
            address=address,
        )
        administrator = Administrator(
            id=uuid4(),
            institution_id=institution_id,
            name=administrator_name.strip(),
            email=_normalize_email(administrator_email),
            password_hash=_hash_password(password),
        )
        return cls(institution=institution, administrator=administrator)
