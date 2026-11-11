"""Implementação em memória (Fake) da porta EmailSender para testes."""

from docflow.domain.ports.email import (
    EmailDeliveryError,
    EmailMessage,
    EmailSender,
)


class InMemoryEmailSender(EmailSender):
    """Adaptador de envio de e-mails em memória para testes automatizados rápidos."""

    def __init__(
        self,
        should_fail: bool = False,
        failure_error: Exception | None = None,
    ) -> None:
        self.sent_messages: list[EmailMessage] = []
        self.should_fail = should_fail
        self.failure_error = failure_error

    def _record(self, message: EmailMessage) -> None:
        if self.should_fail:
            if self.failure_error is not None:
                raise self.failure_error
            raise EmailDeliveryError("Falha simulada no envio de e-mail.")
        self.sent_messages.append(message)

    async def send(self, message: EmailMessage) -> None:
        """Grava a mensagem na lista em memória de forma assíncrona."""
        self._record(message)

    def send_sync(self, message: EmailMessage) -> None:
        """Grava a mensagem na lista em memória de forma síncrona."""
        self._record(message)

    def clear(self) -> None:
        """Limpa o histórico de e-mails enviados."""
        self.sent_messages.clear()

    @property
    def count(self) -> int:
        """Retorna o número de mensagens enviadas."""
        return len(self.sent_messages)

    def get_last_message(self) -> EmailMessage | None:
        """Retorna a última mensagem enviada ou None se nenhuma tiver sido enviada."""
        return self.sent_messages[-1] if self.sent_messages else None

    def has_sent_to(self, email: str) -> bool:
        """Verifica se alguma mensagem foi enviada para o endereço indicado."""
        email_clean = email.strip().lower()
        for msg in self.sent_messages:
            if any(r.lower() == email_clean for r in msg.all_recipient_emails):
                return True
        return False

    def filter_by_recipient(self, email: str) -> list[EmailMessage]:
        """Retorna todas as mensagens enviadas para o endereço indicado."""
        email_clean = email.strip().lower()
        return [
            msg
            for msg in self.sent_messages
            if any(r.lower() == email_clean for r in msg.all_recipient_emails)
        ]

    def filter_by_subject(self, fragment: str) -> list[EmailMessage]:
        """Retorna todas as mensagens cujo assunto contém o fragmento indicado."""
        frag = fragment.lower()
        return [msg for msg in self.sent_messages if frag in msg.subject.lower()]


# Alias explícito para atender a ambas nomenclaturas comuns em testes
FakeEmailSender = InMemoryEmailSender
