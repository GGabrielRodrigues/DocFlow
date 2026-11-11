"""Porta do serviço de envio de e-mails do DocFlow."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


class EmailError(Exception):
    """Exceção base para erros de envio e infraestrutura de e-mail."""


class EmailConnectionError(EmailError):
    """Falha de conexão ou comunicação com o servidor SMTP."""


class EmailAuthenticationError(EmailError):
    """Falha de autenticação (credenciais inválidas)."""


class EmailDeliveryError(EmailError):
    """Falha durante o envio ou rejeição do destinatário/remetente."""


@dataclass(frozen=True)
class EmailRecipient:
    """Destinatário de um e-mail com endereço e nome legível opcional."""

    email: str
    name: str | None = None

    def format(self) -> str:
        """Formata o destinatário para cabeçalhos RFC 5322."""
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email

    @classmethod
    def from_value(cls, value: str | "EmailRecipient") -> "EmailRecipient":
        """Converte string simples ou objeto EmailRecipient em EmailRecipient."""
        if isinstance(value, EmailRecipient):
            return value
        return cls(email=value.strip())


@dataclass(frozen=True)
class EmailAttachment:
    """Anexo de e-mail com conteúdo binário e tipo MIME."""

    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


def _normalize_recipients(
    values: str | EmailRecipient | Sequence[str | EmailRecipient] | None,
) -> list[EmailRecipient]:
    if values is None:
        return []
    if isinstance(values, (str, EmailRecipient)):
        return [EmailRecipient.from_value(values)]
    return [EmailRecipient.from_value(item) for item in values]


@dataclass
class EmailMessage:
    """Representação agnóstica de uma mensagem de e-mail a ser enviada."""

    recipients: list[EmailRecipient] = field(default_factory=list)
    subject: str = ""
    body_text: str = ""
    body_html: str | None = None
    from_email: str | None = None
    reply_to: str | None = None
    cc: list[EmailRecipient] = field(default_factory=list)
    bcc: list[EmailRecipient] = field(default_factory=list)
    attachments: list[EmailAttachment] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)

    def __init__(
        self,
        recipients: str | EmailRecipient | Sequence[str | EmailRecipient] | None = None,
        subject: str = "",
        body_text: str = "",
        body_html: str | None = None,
        from_email: str | None = None,
        reply_to: str | None = None,
        cc: str | EmailRecipient | Sequence[str | EmailRecipient] | None = None,
        bcc: str | EmailRecipient | Sequence[str | EmailRecipient] | None = None,
        attachments: list[EmailAttachment] | None = None,
        headers: dict[str, str] | None = None,
        to: str | EmailRecipient | Sequence[str | EmailRecipient] | None = None,
    ) -> None:
        target_recipients = recipients if recipients is not None else to
        if target_recipients is None:
            raise ValueError("Ao menos um destinatário deve ser informado.")

        self.recipients = _normalize_recipients(target_recipients)
        if not self.recipients:
            raise ValueError("A lista de destinatários principais não pode ser vazia.")

        self.subject = subject
        self.body_text = body_text
        self.body_html = body_html
        self.from_email = from_email
        self.reply_to = reply_to
        self.cc = _normalize_recipients(cc)
        self.bcc = _normalize_recipients(bcc)
        self.attachments = list(attachments) if attachments else []
        self.headers = dict(headers) if headers else {}

    @property
    def recipient_emails(self) -> list[str]:
        """Lista com apenas os endereços de e-mail dos destinatários principais."""
        return [r.email for r in self.recipients]

    @property
    def cc_emails(self) -> list[str]:
        """Lista com apenas os endereços em cópia (CC)."""
        return [r.email for r in self.cc]

    @property
    def bcc_emails(self) -> list[str]:
        """Lista com apenas os endereços em cópia oculta (BCC)."""
        return [r.email for r in self.bcc]

    @property
    def all_recipient_emails(self) -> list[str]:
        """Lista completa de endereços para o envelope SMTP (To + CC + BCC)."""
        return self.recipient_emails + self.cc_emails + self.bcc_emails


@runtime_checkable
class EmailSender(Protocol):
    """Porta que abstrai o provedor de envio de e-mails."""

    async def send(self, message: EmailMessage) -> None:
        """Envia o e-mail de forma assíncrona.

        Raises:
            EmailConnectionError: Falha ao conectar ou negociar com o servidor.
            EmailAuthenticationError: Falha nas credenciais SMTP.
            EmailDeliveryError: Rejeição pelo servidor de envio.
        """
        ...

    def send_sync(self, message: EmailMessage) -> None:
        """Envia o e-mail de forma síncrona.

        Raises:
            EmailConnectionError: Falha ao conectar ou negociar com o servidor.
            EmailAuthenticationError: Falha nas credenciais SMTP.
            EmailDeliveryError: Rejeição pelo servidor de envio.
        """
        ...
