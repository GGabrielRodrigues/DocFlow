"""Adaptador SMTP concreto para envio de e-mails via Mailpit ou servidores corporativos."""

import asyncio
import logging
import smtplib
from email.message import EmailMessage as PyEmailMessage
from typing import Any

from docflow.core.config import Settings, get_settings
from docflow.domain.ports.email import (
    EmailAuthenticationError,
    EmailConnectionError,
    EmailDeliveryError,
    EmailMessage,
    EmailSender,
)

logger = logging.getLogger("docflow.email")


class SMTPEmailSender(EmailSender):
    """Adaptador de envio de e-mails via protocolo SMTP (suporta dev/Mailpit e prod com TLS/SSL)."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        from_email: str | None = None,
        use_tls: bool | None = None,
        use_ssl: bool | None = None,
        timeout: float | None = None,
    ) -> None:
        cfg = settings or get_settings()

        self.host: str = host if host is not None else cfg.smtp_host
        self.port: int = port if port is not None else cfg.smtp_port
        self.user: str = user if user is not None else cfg.smtp_user
        self.password: str = password if password is not None else cfg.smtp_password
        self.from_email: str = from_email if from_email is not None else cfg.smtp_from_email
        self.use_tls: bool = use_tls if use_tls is not None else cfg.smtp_use_tls
        self.use_ssl: bool = use_ssl if use_ssl is not None else cfg.smtp_use_ssl
        self.timeout: float = timeout if timeout is not None else cfg.smtp_timeout

    def build_mime_message(self, message: EmailMessage) -> PyEmailMessage:
        """Constrói uma mensagem MIME padrão Python a partir de EmailMessage."""
        mime = PyEmailMessage()
        from_addr = message.from_email or self.from_email
        if not from_addr:
            raise EmailDeliveryError("Remetente (from_email) não configurado.")

        mime["Subject"] = message.subject
        mime["From"] = from_addr
        mime["To"] = ", ".join(r.format() for r in message.recipients)

        if message.cc:
            mime["Cc"] = ", ".join(r.format() for r in message.cc)

        if message.reply_to:
            mime["Reply-To"] = message.reply_to

        for header_name, header_value in message.headers.items():
            mime[header_name] = header_value

        mime.set_content(message.body_text)

        if message.body_html:
            mime.add_alternative(message.body_html, subtype="html")

        for attachment in message.attachments:
            if "/" in attachment.content_type:
                maintype, subtype = attachment.content_type.split("/", 1)
            else:
                maintype, subtype = "application", "octet-stream"

            mime.add_attachment(
                attachment.content,
                maintype=maintype,
                subtype=subtype,
                filename=attachment.filename,
            )

        return mime

    def send_sync(self, message: EmailMessage) -> None:
        """Envia mensagem síncrona via smtplib da biblioteca padrão."""
        to_addrs = message.all_recipient_emails
        if not to_addrs:
            raise EmailDeliveryError("A lista de destinatários está vazia.")

        mime_message = self.build_mime_message(message)

        try:
            client: smtplib.SMTP
            if self.use_ssl:
                client = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout)
            else:
                client = smtplib.SMTP(self.host, self.port, timeout=self.timeout)

            with client:
                if not self.use_ssl and self.use_tls:
                    client.starttls()
                if self.user and self.password:
                    client.login(self.user, self.password)
                client.send_message(mime_message, to_addrs=to_addrs)
            logger.info("E-mail '%s' enviado com sucesso para %s", message.subject, to_addrs)
        except smtplib.SMTPAuthenticationError as exc:
            logger.error("Falha de autenticação SMTP ao enviar para %s: %s", to_addrs, exc)
            raise EmailAuthenticationError(f"Falha de autenticação SMTP: {exc}") from exc
        except smtplib.SMTPConnectError as exc:
            logger.error(
                "Falha ao conectar no servidor SMTP (%s:%s): %s", self.host, self.port, exc
            )
            raise EmailConnectionError(
                f"Falha de conexão SMTP ({self.host}:{self.port}): {exc}"
            ) from exc
        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused) as exc:
            logger.error("Destinatário ou remetente recusado pelo SMTP: %s", exc)
            raise EmailDeliveryError(f"Destinatário ou remetente recusado: {exc}") from exc
        except (smtplib.SMTPException, OSError, TimeoutError) as exc:
            logger.error("Erro na comunicação SMTP com %s:%s: %s", self.host, self.port, exc)
            raise EmailConnectionError(f"Erro de comunicação SMTP: {exc}") from exc

    async def send(self, message: EmailMessage) -> None:
        """Envia mensagem assíncrona utilizando aiosmtplib (não bloqueia event loop)."""
        to_addrs = message.all_recipient_emails
        if not to_addrs:
            raise EmailDeliveryError("A lista de destinatários está vazia.")

        mime_message = self.build_mime_message(message)

        try:
            import aiosmtplib
        except ImportError:
            await asyncio.to_thread(self.send_sync, message)
            return

        try:
            kwargs: dict[str, Any] = {
                "recipients": to_addrs,
                "hostname": self.host,
                "port": self.port,
                "timeout": self.timeout,
            }
            if self.user and self.password:
                kwargs["username"] = self.user
                kwargs["password"] = self.password

            if self.use_ssl:
                kwargs["use_tls"] = True
            elif self.use_tls:
                kwargs["start_tls"] = True
            else:
                kwargs["use_tls"] = False
                kwargs["start_tls"] = False

            await aiosmtplib.send(mime_message, **kwargs)
            logger.info(
                "E-mail assíncrono '%s' enviado com sucesso para %s", message.subject, to_addrs
            )
        except aiosmtplib.SMTPAuthenticationError as exc:
            logger.error(
                "Falha de autenticação SMTP assíncrona ao enviar para %s: %s", to_addrs, exc
            )
            raise EmailAuthenticationError(f"Falha de autenticação SMTP: {exc}") from exc
        except (aiosmtplib.SMTPConnectError, aiosmtplib.SMTPConnectTimeoutError) as exc:
            logger.error(
                "Falha de conexão SMTP assíncrona com %s:%s: %s", self.host, self.port, exc
            )
            raise EmailConnectionError(
                f"Falha de conexão SMTP ({self.host}:{self.port}): {exc}"
            ) from exc
        except (
            aiosmtplib.SMTPRecipientRefused,
            aiosmtplib.SMTPRecipientsRefused,
            aiosmtplib.SMTPSenderRefused,
        ) as exc:
            logger.error("Destinatário ou remetente recusado no SMTP assíncrono: %s", exc)
            raise EmailDeliveryError(f"Destinatário ou remetente recusado: {exc}") from exc
        except (aiosmtplib.SMTPException, OSError, TimeoutError) as exc:
            logger.error("Erro de comunicação no envio assíncrono de e-mail: %s", exc)
            raise EmailConnectionError(f"Erro de comunicação SMTP assíncrona: {exc}") from exc
