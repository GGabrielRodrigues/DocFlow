"""Testes unitários da porta, adaptadores e templates de envio de e-mails."""

import smtplib
from email.message import EmailMessage as PyEmailMessage
from unittest.mock import AsyncMock, MagicMock, patch

import aiosmtplib
import pytest

from docflow.application.email_service import EmailNotificationService
from docflow.core.config import Settings
from docflow.domain.ports.email import (
    EmailAttachment,
    EmailAuthenticationError,
    EmailConnectionError,
    EmailDeliveryError,
    EmailMessage,
    EmailRecipient,
    EmailSender,
)
from docflow.infra.email.memory import FakeEmailSender
from docflow.infra.email.renderer import EmailTemplateRenderer
from docflow.infra.email.smtp import SMTPEmailSender

# =============================================================================
# 1. Testes do Domínio e Value Objects (EmailMessage, EmailRecipient)
# =============================================================================


def test_email_recipient_format() -> None:
    r1 = EmailRecipient(email="usuario@exemplo.com", name="Nome Teste")
    assert r1.format() == "Nome Teste <usuario@exemplo.com>"

    r2 = EmailRecipient(email="usuario@exemplo.com")
    assert r2.format() == "usuario@exemplo.com"

    r3 = EmailRecipient.from_value(" teste@dominio.com ")
    assert r3.email == "teste@dominio.com"
    assert r3.name is None

    r4 = EmailRecipient.from_value(r1)
    assert r4 is r1


def test_email_message_creation_and_normalization() -> None:
    msg = EmailMessage(
        to="dest@exemplo.com",
        subject="Assunto Teste",
        body_text="Texto simples",
        body_html="<p>HTML</p>",
        cc=["cc1@exemplo.com", EmailRecipient("cc2@exemplo.com", "CC 2")],
        bcc="bcc@exemplo.com",
        from_email="remetente@exemplo.com",
        reply_to="resposta@exemplo.com",
        headers={"X-Custom": "123"},
    )

    assert msg.recipient_emails == ["dest@exemplo.com"]
    assert msg.cc_emails == ["cc1@exemplo.com", "cc2@exemplo.com"]
    assert msg.bcc_emails == ["bcc@exemplo.com"]
    assert msg.all_recipient_emails == [
        "dest@exemplo.com",
        "cc1@exemplo.com",
        "cc2@exemplo.com",
        "bcc@exemplo.com",
    ]
    assert msg.subject == "Assunto Teste"
    assert msg.body_text == "Texto simples"
    assert msg.body_html == "<p>HTML</p>"
    assert msg.from_email == "remetente@exemplo.com"
    assert msg.reply_to == "resposta@exemplo.com"
    assert msg.headers["X-Custom"] == "123"


def test_email_message_requires_at_least_one_recipient() -> None:
    with pytest.raises(ValueError, match="Ao menos um destinatário"):
        EmailMessage(recipients=None)

    with pytest.raises(ValueError, match="não pode ser vazia"):
        EmailMessage(recipients=[])


# =============================================================================
# 2. Testes do FakeEmailSender / InMemoryEmailSender
# =============================================================================


def test_fake_email_sender_satisfies_protocol() -> None:
    sender = FakeEmailSender()
    assert isinstance(sender, EmailSender)


@pytest.mark.asyncio
async def test_fake_email_sender_async_and_sync_recording() -> None:
    sender = FakeEmailSender()
    assert sender.count == 0
    assert sender.get_last_message() is None

    msg1 = EmailMessage(to="user1@exemplo.com", subject="Msg 1", body_text="Texto 1")
    await sender.send(msg1)

    assert sender.count == 1
    assert sender.get_last_message() == msg1
    assert sender.has_sent_to("user1@exemplo.com")
    assert not sender.has_sent_to("outro@exemplo.com")

    msg2 = EmailMessage(to="user2@exemplo.com", subject="Msg 2 Alerta", body_text="Texto 2")
    sender.send_sync(msg2)

    assert sender.count == 2
    assert sender.get_last_message() == msg2

    # Filtros
    filtered_recip = sender.filter_by_recipient("user1@exemplo.com")
    assert len(filtered_recip) == 1
    assert filtered_recip[0].subject == "Msg 1"

    filtered_sub = sender.filter_by_subject("alerta")
    assert len(filtered_sub) == 1
    assert filtered_sub[0].subject == "Msg 2 Alerta"

    # Limpeza
    sender.clear()
    assert sender.count == 0
    assert sender.get_last_message() is None


@pytest.mark.asyncio
async def test_fake_email_sender_simulated_failure() -> None:
    sender = FakeEmailSender(should_fail=True)

    msg = EmailMessage(to="erro@exemplo.com", subject="Falha", body_text="Falha")

    with pytest.raises(EmailDeliveryError, match="Falha simulada"):
        await sender.send(msg)

    with pytest.raises(EmailDeliveryError, match="Falha simulada"):
        sender.send_sync(msg)

    custom_error = EmailConnectionError("Conexão recusada no teste")
    sender.failure_error = custom_error

    with pytest.raises(EmailConnectionError, match="Conexão recusada"):
        await sender.send(msg)


# =============================================================================
# 3. Testes do EmailTemplateRenderer e dos 4 Templates
# =============================================================================


def test_template_renderer_user_invitation() -> None:
    renderer = EmailTemplateRenderer()
    subject, text, html = renderer.render_user_invitation(
        user_name="Carlos Eduardo",
        institution_name="Câmara Municipal",
        invite_url="https://docflow.app/invite?token=xyz",
        role="Administrador",
        expires_in_hours=72,
    )

    assert "Convite para acessar o DocFlow — Câmara Municipal" in subject
    assert "Carlos Eduardo" in text and "Carlos Eduardo" in html
    assert "Câmara Municipal" in text and "Câmara Municipal" in html
    assert "Administrador" in text and "Administrador" in html
    assert "https://docflow.app/invite?token=xyz" in text
    assert "https://docflow.app/invite?token=xyz" in html
    assert "72 horas" in text and "72 horas" in html


def test_template_renderer_password_reset() -> None:
    renderer = EmailTemplateRenderer()
    subject, text, html = renderer.render_password_reset(
        user_name="Mariana Souza",
        reset_url="https://docflow.app/reset?token=abc",
        token="123456",
        expires_in_minutes=15,
    )

    assert "Recuperação de Senha" in subject
    assert "Mariana Souza" in text and "Mariana Souza" in html
    assert "https://docflow.app/reset?token=abc" in text
    assert "https://docflow.app/reset?token=abc" in html
    assert "123456" in text and "123456" in html
    assert "15 minutos" in text and "15 minutos" in html


def test_template_renderer_document_validation() -> None:
    renderer = EmailTemplateRenderer()
    subject, text, html = renderer.render_document_validation(
        recipient_name="Dra. Validadora",
        document_title="Ata da 15ª Reunião Ordinária",
        requester_name="Secretário Geral",
        validation_url="https://docflow.app/docs/doc-123/validate",
        document_id="doc-uuid-123",
        document_type="Ata Oficial",
        due_date="15/12/2026",
    )

    assert "Documento para Validação: Ata da 15ª Reunião Ordinária" in subject
    assert "Dra. Validadora" in text and "Dra. Validadora" in html
    assert "Ata da 15ª Reunião Ordinária" in text and "Ata da 15ª Reunião Ordinária" in html
    assert "Secretário Geral" in text and "Secretário Geral" in html
    assert "doc-uuid-123" in text and "doc-uuid-123" in html
    assert "Ata Oficial" in text and "Ata Oficial" in html
    assert "15/12/2026" in text and "15/12/2026" in html
    assert "https://docflow.app/docs/doc-123/validate" in text
    assert "https://docflow.app/docs/doc-123/validate" in html


def test_template_renderer_job_completed_success_and_failure() -> None:
    renderer = EmailTemplateRenderer()

    # Cenário de Sucesso
    subject_ok, text_ok, html_ok = renderer.render_job_completed(
        recipient_name="Roberto",
        job_title="Gravação_Sessao_Plenaria.mp4",
        job_type="Transcrição com IA",
        result_url="https://docflow.app/media/job-777",
        status="Concluído com Sucesso",
        is_success=True,
        duration="4 minutos e 12 segundos",
    )

    assert "[Concluído]" in subject_ok
    assert "Roberto" in text_ok and "Roberto" in html_ok
    assert "Gravação_Sessao_Plenaria.mp4" in text_ok
    assert "Transcrição com IA" in text_ok
    assert "4 minutos e 12 segundos" in text_ok
    assert "https://docflow.app/media/job-777" in text_ok

    # Cenário de Falha
    subject_err, text_err, html_err = renderer.render_job_completed(
        recipient_name="Roberto",
        job_title="Gravação_Corrompida.mp4",
        job_type="Compressão de Vídeo",
        status="Erro",
        is_success=False,
        error_message="Codec de áudio não suportado",
    )

    assert "[Falha no processamento]" in subject_err
    assert "Codec de áudio não suportado" in text_err
    assert "Codec de áudio não suportado" in html_err


# =============================================================================
# 4. Testes do Adaptador SMTP (SMTPEmailSender)
# =============================================================================


def test_smtp_sender_satisfies_protocol() -> None:
    sender = SMTPEmailSender()
    assert isinstance(sender, EmailSender)


def test_smtp_sender_configuration_priority() -> None:
    settings = Settings(
        smtp_host="mail.config.local",
        smtp_port=2525,
        smtp_from_email="config@docflow.local",
    )

    # Usa valores de settings por padrão
    sender1 = SMTPEmailSender(settings)
    assert sender1.host == "mail.config.local"
    assert sender1.port == 2525
    assert sender1.from_email == "config@docflow.local"

    # Sobrescreve com kwargs explícitos
    sender2 = SMTPEmailSender(
        settings,
        host="override.host",
        port=587,
        from_email="custom@docflow.local",
    )
    assert sender2.host == "override.host"
    assert sender2.port == 587
    assert sender2.from_email == "custom@docflow.local"


def test_smtp_build_mime_message() -> None:
    sender = SMTPEmailSender(from_email="padrao@docflow.local")
    msg = EmailMessage(
        to=[EmailRecipient("dest1@exemplo.com", "Destinatário 1")],
        subject="Assunto MIME",
        body_text="Texto Puro",
        body_html="<strong>HTML Negrito</strong>",
        cc=["cc@exemplo.com"],
        reply_to="reply@docflow.local",
        headers={"X-Priority": "1"},
        attachments=[
            EmailAttachment(
                filename="documento.pdf",
                content=b"%PDF-1.4 mock",
                content_type="application/pdf",
            )
        ],
    )

    mime = sender.build_mime_message(msg)

    assert isinstance(mime, PyEmailMessage)
    assert mime["Subject"] == "Assunto MIME"
    assert mime["From"] == "padrao@docflow.local"
    assert "Destinatário 1 <dest1@exemplo.com>" in mime["To"]
    assert "cc@exemplo.com" in mime["Cc"]
    assert mime["Reply-To"] == "reply@docflow.local"
    assert mime["X-Priority"] == "1"

    # Verifica anexo
    attachments = list(mime.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "documento.pdf"


def test_smtp_build_mime_message_missing_from_email() -> None:
    sender = SMTPEmailSender(from_email="")
    msg = EmailMessage(to="dest@exemplo.com", subject="Sem remetente", body_text="Teste")
    with pytest.raises(EmailDeliveryError, match="Remetente .* não configurado"):
        sender.build_mime_message(msg)


def test_smtp_send_sync_success() -> None:
    sender = SMTPEmailSender(
        host="localhost",
        port=1025,
        user="testuser",
        password="secretpassword",
        from_email="sender@docflow.local",
        use_tls=True,
    )
    msg = EmailMessage(
        to="alvo@exemplo.com",
        subject="Envio Síncrono OK",
        body_text="Conteúdo",
    )

    mock_client = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_client) as mock_smtp_class:
        sender.send_sync(msg)

        mock_smtp_class.assert_called_once_with("localhost", 1025, timeout=10.0)
        mock_client.__enter__.assert_called_once()
        mock_client.starttls.assert_called_once()
        mock_client.login.assert_called_once_with("testuser", "secretpassword")
        mock_client.send_message.assert_called_once()


def test_smtp_send_sync_ssl_mode() -> None:
    sender = SMTPEmailSender(
        host="smtp.corp.local",
        port=465,
        from_email="sender@docflow.local",
        use_ssl=True,
    )
    msg = EmailMessage(to="ssl@exemplo.com", subject="SSL", body_text="Texto")

    mock_client = MagicMock()
    with patch("smtplib.SMTP_SSL", return_value=mock_client) as mock_ssl_class:
        sender.send_sync(msg)

        mock_ssl_class.assert_called_once_with("smtp.corp.local", 465, timeout=10.0)
        mock_client.send_message.assert_called_once()


def test_smtp_send_sync_error_handling() -> None:
    sender = SMTPEmailSender(
        host="localhost",
        port=1025,
        user="testuser",
        password="bad",
        from_email="sender@docflow.local",
    )
    msg = EmailMessage(to="alvo@exemplo.com", subject="Teste Erro", body_text="Corpo")

    # 1. Falha de autenticação
    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = MagicMock()
        mock_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        mock_smtp.return_value = mock_instance

        with pytest.raises(EmailAuthenticationError, match="Falha de autenticação SMTP"):
            sender.send_sync(msg)

    # 2. Falha de conexão
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = smtplib.SMTPConnectError(421, b"Cannot connect")

        with pytest.raises(EmailConnectionError, match="Falha de conexão SMTP"):
            sender.send_sync(msg)

    # 3. Recusa de destinatário
    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = MagicMock()
        mock_instance.send_message.side_effect = smtplib.SMTPRecipientsRefused(
            {"alvo@exemplo.com": (550, b"User unknown")}
        )
        mock_smtp.return_value = mock_instance

        with pytest.raises(EmailDeliveryError, match="Destinatário ou remetente recusado"):
            sender.send_sync(msg)

    # 4. Timeout / OSError
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = TimeoutError("Tempo esgotado")

        with pytest.raises(EmailConnectionError, match="Erro de comunicação SMTP"):
            sender.send_sync(msg)


@pytest.mark.asyncio
async def test_smtp_send_async_success() -> None:
    sender = SMTPEmailSender(
        host="localhost",
        port=1025,
        from_email="sender@docflow.local",
    )
    msg = EmailMessage(
        to="async@exemplo.com",
        subject="Envio Assíncrono",
        body_text="Conteúdo assíncrono",
    )

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_aiosmtp:
        await sender.send(msg)

        mock_aiosmtp.assert_awaited_once()
        assert mock_aiosmtp.await_args is not None
        call_kwargs = mock_aiosmtp.await_args.kwargs
        assert call_kwargs["hostname"] == "localhost"
        assert call_kwargs["port"] == 1025
        assert call_kwargs["recipients"] == ["async@exemplo.com"]


@pytest.mark.asyncio
async def test_smtp_send_async_error_handling() -> None:
    sender = SMTPEmailSender(
        host="localhost",
        port=1025,
        user="testuser",
        password="bad",
        from_email="sender@docflow.local",
    )
    msg = EmailMessage(to="alvo@exemplo.com", subject="Teste Erro Async", body_text="Corpo")

    # 1. Falha de autenticação assíncrona
    with patch("aiosmtplib.send", side_effect=aiosmtplib.SMTPAuthenticationError(535, "Auth fail")):
        with pytest.raises(EmailAuthenticationError, match="Falha de autenticação SMTP"):
            await sender.send(msg)

    # 2. Falha de conexão assíncrona
    with patch("aiosmtplib.send", side_effect=aiosmtplib.SMTPConnectError("Connection refused")):
        with pytest.raises(EmailConnectionError, match="Falha de conexão SMTP"):
            await sender.send(msg)

    # 3. Recusa de destinatário
    with patch(
        "aiosmtplib.send",
        side_effect=aiosmtplib.SMTPRecipientRefused(550, "User unknown", "alvo@exemplo.com"),
    ):
        with pytest.raises(EmailDeliveryError, match="Destinatário ou remetente recusado"):
            await sender.send(msg)

    # 4. Timeout assíncrono
    with patch("aiosmtplib.send", side_effect=TimeoutError("Timed out")):
        with pytest.raises(EmailConnectionError, match="Erro de comunicação SMTP"):
            await sender.send(msg)


# =============================================================================
# 5. Testes do EmailNotificationService (Caso de Uso / Aplicação)
# =============================================================================


@pytest.mark.asyncio
async def test_email_notification_service_all_flows() -> None:
    fake_sender = FakeEmailSender()
    service = EmailNotificationService(sender=fake_sender)

    # 1. Convite de usuário
    await service.send_user_invitation(
        recipient_email="novo@exemplo.com",
        user_name="Ana Paula",
        institution_name="Secretaria de Educação",
        invite_url="https://docflow.app/invite?token=111",
        role="Funcionário",
    )
    assert fake_sender.count == 1
    invitation_msg = fake_sender.get_last_message()
    assert invitation_msg is not None
    assert "novo@exemplo.com" in invitation_msg.recipient_emails
    assert "Convite para acessar o DocFlow — Secretaria de Educação" in invitation_msg.subject
    assert "Ana Paula" in invitation_msg.body_text
    assert invitation_msg.body_html is not None

    # 2. Reset de senha
    await service.send_password_reset(
        recipient_email="ana@exemplo.com",
        user_name="Ana Paula",
        reset_url="https://docflow.app/reset?token=222",
        token="778899",
    )
    assert fake_sender.count == 2
    reset_msg = fake_sender.get_last_message()
    assert reset_msg is not None
    assert "ana@exemplo.com" in reset_msg.recipient_emails
    assert "Recuperação de Senha" in reset_msg.subject
    assert "778899" in reset_msg.body_text

    # 3. Validação de documento (síncrono)
    service.send_document_validation_sync(
        recipient_email="validador@exemplo.com",
        recipient_name="Dr. Marcos",
        document_title="Projeto de Lei 05/2026",
        requester_name="Vereador Carlos",
        validation_url="https://docflow.app/validate/99",
        document_id="doc-99",
        document_type="Projeto de Lei",
    )
    assert fake_sender.count == 3
    val_msg = fake_sender.get_last_message()
    assert val_msg is not None
    assert "validador@exemplo.com" in val_msg.recipient_emails
    assert "Projeto de Lei 05/2026" in val_msg.subject

    # 4. Conclusão de processamento de mídia/job (síncrono)
    service.send_job_completed_sync(
        recipient_email="usuario@exemplo.com",
        recipient_name="Dra. Fernanda",
        job_title="Audiencia_12.mp4",
        job_type="Transcrição com IA",
        result_url="https://docflow.app/jobs/12",
        status="Concluído",
        is_success=True,
        duration="3m 15s",
    )
    assert fake_sender.count == 4
    job_msg = fake_sender.get_last_message()
    assert job_msg is not None
    assert "usuario@exemplo.com" in job_msg.recipient_emails
    assert "[Concluído] Audiencia_12.mp4" in job_msg.subject
    assert "3m 15s" in job_msg.body_text
