"""Renderizador de templates de e-mail com Jinja2."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class EmailTemplateRenderer:
    """Gerencia o carregamento e renderização de templates de e-mail em HTML e texto puro."""

    def __init__(self, template_dir: Path | str | None = None) -> None:
        if template_dir is None:
            self.template_dir = Path(__file__).parent / "templates"
        else:
            self.template_dir = Path(template_dir)

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_html(self, template_name: str, context: dict[str, Any] | None = None) -> str:
        """Renderiza a versão HTML do template."""
        ctx = context or {}
        filename = f"{template_name}.html" if not template_name.endswith(".html") else template_name
        template = self.env.get_template(filename)
        return template.render(**ctx)

    def render_text(self, template_name: str, context: dict[str, Any] | None = None) -> str:
        """Renderiza a versão texto puro do template."""
        ctx = context or {}
        filename = f"{template_name}.txt" if not template_name.endswith(".txt") else template_name
        template = self.env.get_template(filename)
        return template.render(**ctx)

    def render(
        self,
        template_name: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        """Renderiza ambas as versões (texto puro, HTML) do template.

        Retorna:
            Uma tupla contendo (corpo_texto_puro, corpo_html).
        """
        ctx = context or {}
        base_name = template_name.removesuffix(".html").removesuffix(".txt")
        return (
            self.render_text(base_name, ctx),
            self.render_html(base_name, ctx),
        )

    def render_user_invitation(
        self,
        *,
        user_name: str,
        institution_name: str,
        invite_url: str,
        role: str = "Funcionário",
        expires_in_hours: int = 48,
    ) -> tuple[str, str, str]:
        """Renderiza o e-mail de convite para novo usuário.

        Retorna:
            (assunto, corpo_texto, corpo_html)
        """
        subject = f"Convite para acessar o DocFlow — {institution_name}"
        context = {
            "user_name": user_name,
            "institution_name": institution_name,
            "invite_url": invite_url,
            "role": role,
            "expires_in_hours": expires_in_hours,
        }
        text_body, html_body = self.render("user_invitation", context)
        return subject, text_body, html_body

    def render_password_reset(
        self,
        *,
        user_name: str,
        reset_url: str,
        token: str | None = None,
        expires_in_minutes: int = 30,
    ) -> tuple[str, str, str]:
        """Renderiza o e-mail de recuperação de senha com token.

        Retorna:
            (assunto, corpo_texto, corpo_html)
        """
        subject = "Recuperação de Senha — DocFlow"
        context = {
            "user_name": user_name,
            "reset_url": reset_url,
            "token": token,
            "expires_in_minutes": expires_in_minutes,
        }
        text_body, html_body = self.render("password_reset", context)
        return subject, text_body, html_body

    def render_document_validation(
        self,
        *,
        recipient_name: str,
        document_title: str,
        requester_name: str,
        validation_url: str,
        document_id: str | None = None,
        document_type: str | None = None,
        due_date: str | None = None,
    ) -> tuple[str, str, str]:
        """Renderiza a notificação de documento enviado para validação.

        Retorna:
            (assunto, corpo_texto, corpo_html)
        """
        subject = f"Documento para Validação: {document_title}"
        context = {
            "recipient_name": recipient_name,
            "document_title": document_title,
            "requester_name": requester_name,
            "validation_url": validation_url,
            "document_id": document_id,
            "document_type": document_type,
            "due_date": due_date,
        }
        text_body, html_body = self.render("document_validation", context)
        return subject, text_body, html_body

    def render_job_completed(
        self,
        *,
        recipient_name: str,
        job_title: str,
        job_type: str = "Processamento de Mídia",
        result_url: str | None = None,
        status: str = "Concluído",
        is_success: bool = True,
        duration: str | None = None,
        error_message: str | None = None,
    ) -> tuple[str, str, str]:
        """Renderiza a notificação de conclusão de processamento de mídia/job.

        Retorna:
            (assunto, corpo_texto, corpo_html)
        """
        prefix = "Concluído" if is_success else "Falha no processamento"
        subject = f"[{prefix}] {job_title} — DocFlow"
        context = {
            "recipient_name": recipient_name,
            "job_title": job_title,
            "job_type": job_type,
            "result_url": result_url,
            "status": status,
            "is_success": is_success,
            "duration": duration,
            "error_message": error_message,
        }
        text_body, html_body = self.render("job_completed", context)
        return subject, text_body, html_body
