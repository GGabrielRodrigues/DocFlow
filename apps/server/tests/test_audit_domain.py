from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import pytest

from docflow.domain.audit import (
    AuditAction,
    AuditLog,
    AuditLogFilter,
    AuditLogImmutableError,
)


def test_audit_log_creation_with_defaults() -> None:
    log = AuditLog(
        institution_id="inst-123",
        action=AuditAction.LOGIN,
        resource_type="auth",
    )
    assert log.id is not None
    assert len(log.id) > 0
    assert log.institution_id == "inst-123"
    assert log.action == "login"
    assert log.resource_type == "auth"
    assert log.user_id is None
    assert log.resource_id is None
    assert log.details == {}
    assert log.ip_address is None
    assert isinstance(log.created_at, datetime)
    assert log.created_at.tzinfo is not None


def test_audit_log_with_full_details() -> None:
    now = datetime.now(timezone.utc)
    log = AuditLog(
        id="audit-uuid-1",
        institution_id="inst-123",
        user_id="user-456",
        action="doc_create",
        resource_type="document",
        resource_id="doc-789",
        details={"title": "Ata Reunião", "format": "docx"},
        ip_address="192.168.1.100",
        created_at=now,
    )
    assert log.id == "audit-uuid-1"
    assert log.institution_id == "inst-123"
    assert log.user_id == "user-456"
    assert log.action == "doc_create"
    assert log.resource_type == "document"
    assert log.resource_id == "doc-789"
    assert log.details == {"title": "Ata Reunião", "format": "docx"}
    assert log.ip_address == "192.168.1.100"
    assert log.created_at == now


def test_audit_log_is_immutable() -> None:
    log = AuditLog(
        institution_id="inst-123",
        action=AuditAction.UPLOAD,
        resource_type="media",
    )
    with pytest.raises(FrozenInstanceError):
        # Tentativa de mutação no objeto de domínio
        log.action = "tampered"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        log.details = {"new": "val"}  # type: ignore[misc]


def test_audit_log_validation() -> None:
    with pytest.raises(ValueError, match="institution_id é obrigatório"):
        AuditLog(institution_id="", action="login", resource_type="auth")

    with pytest.raises(ValueError, match="action é obrigatória"):
        AuditLog(institution_id="inst-1", action="  ", resource_type="auth")

    with pytest.raises(ValueError, match="resource_type é obrigatório"):
        AuditLog(institution_id="inst-1", action="login", resource_type="")


def test_audit_actions_cover_required_events() -> None:
    required_actions = {
        "login",
        "upload",
        "doc_create",
        "doc_edit",
        "approve",
        "return",
        "export",
        "delete",
    }
    action_values = {a.value for a in AuditAction}
    assert required_actions.issubset(action_values)


def test_audit_log_filter() -> None:
    filter_vo = AuditLogFilter(
        action="login",
        resource_type="auth",
        user_id="user-1",
    )
    assert filter_vo.action == "login"
    assert filter_vo.resource_type == "auth"
    assert filter_vo.user_id == "user-1"
    assert filter_vo.start_date is None
    assert filter_vo.end_date is None
