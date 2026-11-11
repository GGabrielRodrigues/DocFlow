"""Módulo de infraestrutura para envio e renderização de e-mails."""

from docflow.infra.email.memory import FakeEmailSender, InMemoryEmailSender
from docflow.infra.email.renderer import EmailTemplateRenderer
from docflow.infra.email.smtp import SMTPEmailSender

__all__ = [
    "EmailTemplateRenderer",
    "FakeEmailSender",
    "InMemoryEmailSender",
    "SMTPEmailSender",
]
