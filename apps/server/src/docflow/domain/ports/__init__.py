"""Interfaces e portas do domínio DocFlow."""

from docflow.domain.ports.email import (
    EmailAttachment,
    EmailAuthenticationError,
    EmailConnectionError,
    EmailDeliveryError,
    EmailError,
    EmailMessage,
    EmailRecipient,
    EmailSender,
)

__all__ = [
    "EmailAttachment",
    "EmailAuthenticationError",
    "EmailConnectionError",
    "EmailDeliveryError",
    "EmailError",
    "EmailMessage",
    "EmailRecipient",
    "EmailSender",
]
