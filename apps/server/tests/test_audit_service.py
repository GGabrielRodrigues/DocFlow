from unittest.mock import MagicMock

from docflow.application.audit import AuditService
from docflow.domain.audit import AuditAction, AuditLog, AuditLogFilter


def test_audit_service_record_event() -> None:
    mock_repo = MagicMock()
    service = AuditService(mock_repo)

    mock_repo.record.side_effect = lambda log: log

    result = service.record_event(
        institution_id="inst-1",
        action=AuditAction.LOGIN,
        resource_type="auth",
        user_id="user-1",
        resource_id="session-1",
        details={"status": "success"},
        ip_address="10.0.0.1",
    )

    mock_repo.record.assert_called_once()
    assert result.institution_id == "inst-1"
    assert result.action == "login"
    assert result.resource_type == "auth"
    assert result.user_id == "user-1"
    assert result.details == {"status": "success"}
    assert result.ip_address == "10.0.0.1"


def test_audit_service_get_by_id() -> None:
    mock_repo = MagicMock()
    service = AuditService(mock_repo)
    expected_log = AuditLog(
        id="log-123",
        institution_id="inst-1",
        action="export",
        resource_type="document",
    )
    mock_repo.get_by_id.return_value = expected_log

    res = service.get_by_id("log-123")
    mock_repo.get_by_id.assert_called_once_with("log-123")
    assert res == expected_log


def test_audit_service_list_logs_pagination_sanitization() -> None:
    mock_repo = MagicMock()
    service = AuditService(mock_repo)
    mock_repo.list.return_value = ([], 0)

    filter_vo = AuditLogFilter(action="upload")
    # Se page < 1 ou page_size < 1, sanitiza para page=1, page_size=20
    items, total = service.list_logs(filter_params=filter_vo, page=-1, page_size=0)

    mock_repo.list.assert_called_once_with(
        filter_params=filter_vo,
        page=1,
        page_size=20,
    )
    assert items == []
    assert total == 0
