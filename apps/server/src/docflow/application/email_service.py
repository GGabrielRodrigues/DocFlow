"""Serviço de aplicação para disparo de notificações por e-mail no DocFlow."""

from docflow.domain.ports.email import EmailMessage, EmailSender
from docflow.infra.email.renderer import EmailTemplateRenderer


class EmailNotificationService:
    """Orquestra a renderização e o envio de notificações por e-mail."""

    def __init__(
        self,
        sender: EmailSender,
        renderer: EmailTemplateRenderer | None = None,
    ) -> None:
        self.sender = sender
        self.renderer = renderer or EmailTemplateRenderer()

    async def send_user_invitation(
        self,
        *,
        recipient_email: str,
        user_name: str,
        institution_name: str,
        invite_url: str,
        role: str = "Funcionário",
        expires_in_hours: int = 48,
    ) -> EmailMessage:
        """Envia e-mail de convite para novo usuário de forma assíncrona."""
        subject, text_body, html_body = self.renderer.render_user_invitation(
            user_name=user_name,
            institution_name=institution_name,
            invite_url=invite_url,
            role=role,
            expires_in_hours=expires_in_hours,
        )
        message = EmailMessage(
            recipients=recipient_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
        )
        await self.sender.send(message)
        return message

    def send_user_invitation_sync(
        self,
        *,
        recipient_email: str,
        user_name: str,
        institution_name: str,
        invite_url: str,
        role: str = "Funcionário",
        expires_in_hours: int = 48,
    ) -> EmailMessage:
        """Envia e-mail de convite para novo usuário de forma síncrona."""
        subject, text_body, html_body = self.renderer.render_user_invitation(
            user_name=user_name,
            institution_name=institution_name,
            invite_url=invite_url,
            role=role,
            expires_in_hours=expires_in_hours,
        )
        message = EmailMessage(
            recipients=recipient_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
        )
        self.sender.send_sync(message)
        return message

    async def send_password_reset(
        self,
        *,
        recipient_email: str,
        user_name: str,
        reset_url: str,
        token: str | None = None,
        expires_in_minutes: int = 30,
    ) -> EmailMessage:
        """Envia e-mail de recuperação de senha com token de forma assíncrona."""
        subject, text_body, html_body = self.renderer.render_password_reset(
            user_name=user_name,
            reset_url=reset_url,
            token=token,
            expires_in_minutes=expires_in_minutes,
        )
        message = EmailMessage(
            recipients=recipient_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
        )
        await self.sender.send(message)
        return message

    def send_password_reset_sync(
        self,
        *,
        recipient_email: str,
        user_name: str,
        reset_url: str,
        token: str | None = None,
        expires_in_minutes: int = 30,
    ) -> EmailMessage:
        """Envia e-mail de recuperação de senha com token de forma síncrona."""
        subject, text_body, html_body = self.renderer.render_password_reset(
            user_name=user_name,
            reset_url=reset_url,
            token=token,
            expires_in_minutes=expires_in_minutes,
        )
        message = EmailMessage(
            recipients=recipient_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
        )
        self.sender.send_sync(message)
        return message

    async def send_document_validation(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        document_title: str,
        requester_name: str,
        validation_url: str,
        document_id: str | None = None,
        document_type: str | None = None,
        due_date: str | None = None,
    ) -> EmailMessage:
        """Envia notificação de documento para validação de forma assíncrona."""
        subject, text_body, html_body = self.renderer.render_document_validation(
            recipient_name=recipient_name,
            document_title=document_title,
            requester_name=requester_name,
            validation_url=validation_url,
            document_id=document_id,
            document_type=document_type,
            due_date=due_date,
        )
        message = EmailMessage(
            recipients=recipient_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
        )
        await self.sender.send(message)
        return message

    def send_document_validation_sync(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        document_title: str,
        requester_name: str,
        validation_url: str,
        document_id: str | None = None,
        document_type: str | None = None,
        due_date: str | None = None,
    ) -> EmailMessage:
        """Envia notificação de documento para validação de forma síncrona."""
        subject, text_body, html_body = self.renderer.render_document_validation(
            recipient_name=recipient_name,
            document_title=document_title,
            requester_name=requester_name,
            validation_url=validation_url,
            document_id=document_id,
            document_type=document_type,
            due_date=due_date,
        )
        message = EmailMessage(
            recipients=recipient_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
        )
        self.sender.send_sync(message)
        return message

    async def send_job_completed(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        job_title: str,
        job_type: str = "Processamento de Mídia",
        result_url: str | None = None,
        status: str = "Concluído",
        is_success: bool = True,
        duration: str | None = None,
        error_message: str | None = None,
    ) -> EmailMessage:
        """Envia notificação de conclusão de processamento de mídia/job de forma assíncrona."""
        subject, text_body, html_body = self.renderer.render_job_completed(
            recipient_name=recipient_name,
            job_title=job_title,
            job_type=job_type,
            result_url=result_url,
            status=status,
            is_success=is_success,
            duration=duration,
            error_message=error_message,
        )
        message = EmailMessage(
            recipients=recipient_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
        )
        await self.sender.send(message)
        return message

    def send_job_completed_sync(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        job_title: str,
        job_type: str = "Processamento de Mídia",
        result_url: str | None = None,
        status: str = "Concluído",
        is_success: bool = True,
        duration: str | None = None,
        error_message: str | None = None,
    ) -> EmailMessage:
        """Envia notificação de conclusão de processamento de mídia/job de forma síncrona."""
        subject, text_body, html_body = self.renderer.render_job_completed(
            recipient_name=recipient_name,
            job_title=job_title,
            job_type=job_type,
            result_url=result_url,
            status=status,
            is_success=is_success,
            duration=duration,
            error_message=error_message,
        )
        message = EmailMessage(
            recipients=recipient_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
        )
        self.sender.send_sync(message)
        return message
