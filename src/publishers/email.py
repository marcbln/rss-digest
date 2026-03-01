"""
Email Publisher - Publishes DigestResult via email.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional
import markdown

from src.core.interfaces import BasePublisher
from src.core.models import DigestResult

logger = logging.getLogger(__name__)


class EmailPublisher(BasePublisher):
    """Publishes digests via email."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        recipient_email: str,
        smtp_starttls: bool = True,
        from_email: Optional[str] = None,
        sender_name: str = "RSS Digest"
    ):
        """
        Initialize email publisher.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP username
            smtp_password: SMTP password
            recipient_email: Recipient email address
            smtp_starttls: Whether to use STARTTLS encryption
            from_email: Sender email address (defaults to smtp_username)
            sender_name: Display name for sender
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.recipient_email = recipient_email
        self.smtp_starttls = smtp_starttls
        self.from_email = from_email or smtp_username
        self.sender_name = sender_name

        logger.info(f"EmailPublisher initialized with host: {smtp_host}:{smtp_port}")

    def publish(
        self,
        digest: DigestResult,
        template_path: Optional[str] = "templates/email_template.html",
        subject_override: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Publish digest via email.

        Args:
            digest: The DigestResult to publish
            template_path: Path to HTML email template
            subject_override: Optional custom subject line
            **kwargs: Additional options

        Returns:
            True if sent successfully
        """
        try:
            # Convert Markdown body to HTML
            html_content = markdown.markdown(digest.markdown_body)

            # Build date range string
            date_range = f"{digest.date.strftime('%b %d, %Y')}"

            # Load template and inject content
            full_html = self._load_template(template_path, html_content, date_range)

            # Create subject
            if subject_override:
                subject = f"{subject_override}: {date_range} ({digest.sources_analyzed} articles)"
            else:
                subject = f"{digest.title}: {date_range} ({digest.sources_analyzed} articles)"

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.from_email}>"
            msg['To'] = self.recipient_email

            # Attach HTML content
            html_part = MIMEText(full_html, 'html')
            msg.attach(html_part)

            # Send email
            logger.info(f"Sending digest to {self.recipient_email}")
            server = self._create_smtp_connection()
            server.send_message(msg)
            server.quit()

            logger.info("Email sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and configure SMTP connection."""
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            if self.smtp_starttls:
                server.starttls()

            server.login(self.smtp_username, self.smtp_password)
            return server

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            raise
        except smtplib.SMTPConnectError as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            raise
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            raise

    def _load_template(self, template_path: Optional[str], digest_html: str, date_range: str) -> str:
        """Load email template and inject content."""
        if template_path and Path(template_path).exists():
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read()
                full_html = template.replace('{{DIGEST_CONTENT}}', digest_html)
                full_html = full_html.replace('{{DATE_RANGE}}', date_range)
                return full_html
            except Exception as e:
                logger.warning(f"Failed to load template: {e}. Using simple template.")

        return self._create_simple_template(digest_html, date_range)

    def _create_simple_template(self, digest_html: str, date_range: str) -> str:
        """Create a simple HTML email template."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSS Digest</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #e3120b;
            border-bottom: 3px solid #e3120b;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2c3e50;
            margin-top: 30px;
        }}
        a {{
            color: #e3120b;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🗞️ Your RSS Digest</h1>
        <p><strong>{date_range}</strong></p>

        {digest_html}

        <div class="footer">
            <p>This digest was automatically generated.</p>
        </div>
    </div>
</body>
</html>
"""
