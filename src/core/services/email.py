"""
Email service for sending emails.
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Union

from jinja2 import Environment, FileSystemLoader

from src.config import settings


class EmailService:
    """Service for sending emails."""
    
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        default_sender: str = None,
        templates_dir: str = None,
    ):
        """
        Initialize email service.
        
        Args:
            smtp_host: SMTP host
            smtp_port: SMTP port
            smtp_user: SMTP username
            smtp_password: SMTP password
            default_sender: Default sender email
            templates_dir: Directory with email templates
        """
        # Set SMTP settings
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "25"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.default_sender = default_sender or os.getenv("SMTP_SENDER", "noreply@example.com")
        
        # Set Jinja2 environment for email templates
        self.templates_dir = templates_dir or os.path.join(os.getcwd(), "src", "templates", "email")
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True,
        )
    
    def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        sender: str = None,
        cc: Union[str, List[str]] = None,
        bcc: Union[str, List[str]] = None,
        is_html: bool = False,
    ) -> bool:
        """
        Send email.
        
        Args:
            to: Recipient(s)
            subject: Email subject
            body: Email body
            sender: Sender email
            cc: Carbon copy recipient(s)
            bcc: Blind carbon copy recipient(s)
            is_html: Whether body is HTML
        
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = sender or self.default_sender
            msg["Subject"] = subject
            
            # Set recipients
            if isinstance(to, list):
                msg["To"] = ", ".join(to)
            else:
                msg["To"] = to
            
            # Set CC recipients
            if cc:
                if isinstance(cc, list):
                    msg["Cc"] = ", ".join(cc)
                else:
                    msg["Cc"] = cc
            
            # Set BCC recipients
            if bcc:
                if isinstance(bcc, list):
                    msg["Bcc"] = ", ".join(bcc)
                else:
                    msg["Bcc"] = bcc
            
            # Set message body
            msg.attach(MIMEText(body, "html" if is_html else "plain"))
            
            # Get all recipients
            all_recipients = []
            if isinstance(to, list):
                all_recipients.extend(to)
            else:
                all_recipients.append(to)
            
            if cc:
                if isinstance(cc, list):
                    all_recipients.extend(cc)
                else:
                    all_recipients.append(cc)
            
            if bcc:
                if isinstance(bcc, list):
                    all_recipients.extend(bcc)
                else:
                    all_recipients.append(bcc)
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                # Start TLS if available
                if self.smtp_user and self.smtp_password:
                    smtp.starttls()
                    smtp.login(self.smtp_user, self.smtp_password)
                
                # Send email
                smtp.send_message(msg, from_addr=sender or self.default_sender, to_addrs=all_recipients)
            
            return True
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return False
    
    def send_template_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        template_name: str,
        context: Dict[str, any] = None,
        sender: str = None,
        cc: Union[str, List[str]] = None,
        bcc: Union[str, List[str]] = None,
    ) -> bool:
        """
        Send email using template.
        
        Args:
            to: Recipient(s)
            subject: Email subject
            template_name: Template name
            context: Template context
            sender: Sender email
            cc: Carbon copy recipient(s)
            bcc: Blind carbon copy recipient(s)
        
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Get template
            template = self.jinja_env.get_template(f"{template_name}.html")
            
            # Render template
            html_content = template.render(**(context or {}))
            
            # Send email
            return self.send_email(
                to=to,
                subject=subject,
                body=html_content,
                sender=sender,
                cc=cc,
                bcc=bcc,
                is_html=True,
            )
        except Exception as e:
            logging.error(f"Error sending template email: {e}")
            return False