"""
Email Sender Module
Handles email composition and sending via generic SMTP servers.
"""

import logging
import smtplib
import os
from datetime import datetime
from typing import Optional, Union
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class EmailSender:
    """Sends digest emails via generic SMTP servers."""

    def __init__(
        self, 
        smtp_host: str, 
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        smtp_starttls: bool = True,
        from_email: Optional[str] = None,
        sender_name: str = "RSS Digest"
    ):
        """
        Initialize email sender with generic SMTP configuration.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP username (usually email address)
            smtp_password: SMTP password
            smtp_starttls: Whether to use STARTTLS encryption
            from_email: Sender email address (defaults to smtp_username)
            sender_name: Display name for sender
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_starttls = smtp_starttls
        self.from_email = from_email or smtp_username
        self.sender_name = sender_name
        
        logger.info(f"Email sender initialized with host: {smtp_host}:{smtp_port}")
        logger.info(f"Sender: {self.sender_name} <{self.from_email}>")

    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and configure SMTP connection."""
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            
            if self.smtp_starttls:
                server.starttls()
                logger.debug("STARTTLS encryption enabled")
            
            server.login(self.smtp_username, self.smtp_password)
            logger.debug("SMTP authentication successful")
            
            return server
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {str(e)}")
            logger.error("Please verify your SMTP credentials")
            raise
        except smtplib.SMTPConnectError as e:
            logger.error(f"Failed to connect to SMTP server {self.smtp_host}:{self.smtp_port}: {str(e)}")
            raise
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {str(e)}")
            raise

    def send_digest(
        self,
        recipient_email: str,
        digest_html: str,
        date_range: str,
        article_count: int,
        template_path: Optional[str] = None
    ) -> bool:
        """
        Send weekly digest email.

        Args:
            recipient_email: Recipient email address
            digest_html: HTML content of the digest
            date_range: Date range string for subject line
            article_count: Number of articles in digest
            template_path: Optional path to HTML template file

        Returns:
            True if sent successfully, False otherwise
        """
        server = None
        try:
            # Load template if provided
            if template_path:
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template = f.read()
                    # Replace placeholder with digest content
                    full_html = template.replace('{{DIGEST_CONTENT}}', digest_html)
                    full_html = full_html.replace('{{DATE_RANGE}}', date_range)
                except Exception as e:
                    logger.warning(f"Failed to load template: {str(e)}. Using plain HTML.")
                    full_html = self._create_simple_template(digest_html, date_range)
            else:
                full_html = self._create_simple_template(digest_html, date_range)

            # Create email
            subject = f"Your Weekly RSS Digest: {date_range} ({article_count} articles)"

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.from_email}>"
            msg['To'] = recipient_email

            # Attach HTML content
            html_part = MIMEText(full_html, 'html')
            msg.attach(html_part)

            # Send email via SMTP
            logger.info(f"Sending digest to {recipient_email} via {self.smtp_host}:{self.smtp_port}")
            server = self._create_smtp_connection()
            server.send_message(msg)
            
            logger.info("Email sent successfully via SMTP")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

    def send_test_email(self, recipient_email: str) -> bool:
        """
        Send a test email to verify configuration.

        Args:
            recipient_email: Recipient email address

        Returns:
            True if sent successfully, False otherwise
        """
        server = None
        try:
            test_content = """
            <h1>Test Email from RSS Digest</h1>
            <p>This is a test email to verify your SMTP configuration.</p>
            <p>If you received this, your email setup is working correctly!</p>
            <p><small>Sent at: {}</small></p>
            """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Test Email - RSS Digest"
            msg['From'] = f"{self.sender_name} <{self.from_email}>"
            msg['To'] = recipient_email

            html_part = MIMEText(test_content, 'html')
            msg.attach(html_part)

            # Send via SMTP
            logger.info(f"Sending test email to {recipient_email}")
            server = self._create_smtp_connection()
            server.send_message(msg)

            logger.info("Test email sent successfully via SMTP")
            return True

        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            return False
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

    def _create_simple_template(self, digest_html: str, date_range: str) -> str:
        """
        Create a simple HTML email template.

        Args:
            digest_html: The digest content
            date_range: Date range string

        Returns:
            Complete HTML email
        """
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSS Weekly Digest</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
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
        h3 {{
            color: #34495e;
            margin-top: 20px;
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
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🗞️ Your Weekly RSS Digest</h1>
        <p><strong>Week of {date_range}</strong></p>

        {digest_html}

        <div class="footer">
            <p>This digest was automatically generated from RSS feeds.</p>
            <p><small>Generated with ❤️ by your automated digest system</small></p>
        </div>
    </div>
</body>
</html>
"""

    def save_digest_html(self, digest_html: str, date_range: str, filepath: str) -> bool:
        """
        Save digest as HTML file for backup/review.

        Args:
            digest_html: The digest content
            date_range: Date range string
            filepath: Path to save the file

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            full_html = self._create_simple_template(digest_html, date_range)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_html)

            logger.info(f"Digest saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving digest HTML: {str(e)}")
            return False


def test_email_sender(
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    recipient: str,
    smtp_starttls: bool = True,
    from_email: Optional[str] = None
) -> None:
    """
    Test email sender functionality with generic SMTP.

    Args:
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        smtp_username: SMTP username
        smtp_password: SMTP password
        recipient: Test recipient email address
        smtp_starttls: Whether to use STARTTLS
        from_email: Sender email (defaults to smtp_username)
    """
    sender = EmailSender(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        smtp_starttls=smtp_starttls,
        from_email=from_email
    )

    print("\n=== Email Sender Test ===")
    print(f"SMTP Server: {smtp_host}:{smtp_port}")
    print(f"Sending test email to: {recipient}")

    success = sender.send_test_email(recipient)

    if success:
        print("✅ Test email sent successfully!")
        print("Check your inbox to confirm receipt.")
    else:
        print("❌ Failed to send test email. Check logs for details.")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    load_dotenv()

    # New generic SMTP configuration
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("RECIPIENT_EMAIL")
    smtp_starttls = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
    from_email = os.getenv("FROM_EMAIL")

    # Backward compatibility: check for old Gmail variables
    if not smtp_host and os.getenv("SMTP_PASSWORD"):
        logger.warning("Using deprecated Gmail configuration. Please update to new SMTP variables.")
        smtp_host = "smtp.gmail.com"
        smtp_port = "587"
        smtp_username = os.getenv("FROM_EMAIL")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = smtp_username

    if all([smtp_host, smtp_port, smtp_username, smtp_password, recipient]):
        test_email_sender(
            smtp_host=smtp_host,
            smtp_port=int(smtp_port),
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            recipient=recipient,
            smtp_starttls=smtp_starttls,
            from_email=from_email
        )
    else:
        print("Please set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, and RECIPIENT_EMAIL in .env file")
