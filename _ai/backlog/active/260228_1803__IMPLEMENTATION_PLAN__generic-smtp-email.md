---
filename: "_ai/backlog/active/260228_1803__IMPLEMENTATION_PLAN__generic-smtp-email.md"
title: "Replace Gmail SMTP with Generic SMTP Configuration"
createdAt: 2026-02-28 18:03
createdBy: Cascade [Penguin Alpha]
updatedAt: 2026-02-28 18:03
updatedBy: Cascade [Penguin Alpha]
status: draft
priority: high
tags: [smtp, email, configuration, refactoring]
estimatedComplexity: moderate
documentType: IMPLEMENTATION_PLAN
---

## Problem Statement

The current RSS Digest project is hardcoded to use Gmail SMTP for sending emails. The user wants to replace this with a generic SMTP configuration that can work with any SMTP provider, making the system more flexible and provider-agnostic.

## Implementation Notes

### Current Project Structure
- **Project Root**: `/home/marc/devel/rss-digest`
- **Email Module**: `src/email_sender.py` - Currently Gmail-specific
- **Environment Config**: `.env.example` - Gmail App Password instructions
- **Dependencies**: `pyproject.toml` - Uses Python standard library `smtplib`

### Relevant Files
- `src/email_sender.py` - Main email sending logic (301 lines)
- `.env.example` - Environment variables template
- `README.md` - Documentation with Gmail-specific instructions

### Testing Commands
```bash
# Test email sending after changes
uv run python src/email_sender.py

# Full integration test
uv run python src/main.py --test --dry-run
```

## Phase 1: Update Environment Configuration

**Objective**: Replace Gmail-specific environment variables with generic SMTP configuration

**Tasks**:
1. Update `.env.example` with generic SMTP variables
2. Update environment variable loading logic
3. Maintain backward compatibility warnings

**Deliverables**:
- Updated `.env.example` with generic SMTP settings
- Environment variable validation

**Changes**:

[MODIFY] `.env.example`
```env
# ==============================================================================
# Generic SMTP Configuration
# ==============================================================================
# SMTP server configuration for sending emails
# Examples:
# - Gmail: smtp.gmail.com:587
# - Outlook: smtp-mail.outlook.com:587
# - Custom SMTP: your-smtp-server.com:587
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# SMTP authentication credentials
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-smtp-password

# Email security settings
# Set to 'true' if your SMTP server requires STARTTLS (most do)
SMTP_STARTTLS=true

# Email configuration
# The email address where you want to receive the digest
RECIPIENT_EMAIL=your-email@example.com

# Sender email address (should match SMTP_USERNAME for most providers)
FROM_EMAIL=your-email@example.com

# Optional: Display name for emails (defaults to "RSS Digest")
EMAIL_SENDER_NAME=RSS Digest
```

## Phase 2: Refactor EmailSender Class

**Objective**: Make EmailSender class provider-agnostic while maintaining functionality

**Tasks**:
1. Update EmailSender constructor to accept generic SMTP config
2. Modify SMTP connection logic to use configurable host/port
3. Add STARTTLS support configuration
4. Update error messages to be provider-neutral

**Deliverables**:
- Updated `EmailSender` class with generic SMTP support
- Backward compatibility for existing Gmail users

**Changes**:

[MODIFY] `src/email_sender.py`
```python
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
```

## Phase 3: Update Main Application Integration

**Objective**: Update main.py to use new SMTP configuration

**Tasks**:
1. Update environment variable loading
2. Modify EmailSender instantiation
3. Add configuration validation

**Deliverables**:
- Updated main.py with generic SMTP support
- Configuration validation logic

**Changes**:

[MODIFY] `src/main.py` (environment loading section)
```python
def load_environment():
    """Load and validate environment variables."""
    load_dotenv()
    
    # Required LLM configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Required SMTP configuration
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    
    missing_vars = []
    for var, value in [
        ("SMTP_HOST", smtp_host),
        ("SMTP_PORT", smtp_port),
        ("SMTP_USERNAME", smtp_username),
        ("SMTP_PASSWORD", smtp_password),
        ("RECIPIENT_EMAIL", recipient_email)
    ]:
        if not value:
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Optional configuration with defaults
    openai_base_url = os.getenv("OPENAI_BASE_URL", "")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    smtp_starttls = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
    from_email = os.getenv("FROM_EMAIL", smtp_username)
    sender_name = os.getenv("EMAIL_SENDER_NAME", "RSS Digest")
    
    try:
        smtp_port = int(smtp_port)
    except ValueError:
        raise ValueError("SMTP_PORT must be a valid integer")
    
    return {
        "openai_api_key": openai_api_key,
        "openai_base_url": openai_base_url,
        "llm_model": llm_model,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_username": smtp_username,
        "smtp_password": smtp_password,
        "smtp_starttls": smtp_starttls,
        "from_email": from_email,
        "sender_name": sender_name,
        "recipient_email": recipient_email
    }
```

## Phase 4: Update Documentation

**Objective**: Update README and documentation to reflect generic SMTP support

**Tasks**:
1. Update README.md with generic SMTP instructions
2. Add examples for common SMTP providers
3. Update troubleshooting section
4. Maintain Gmail setup as example

**Deliverables**:
- Updated README.md with provider-agnostic instructions
- SMTP provider examples

**Changes**:

[MODIFY] `README.md` (Email Configuration section)
```markdown
### Email Configuration

Choose your SMTP provider and configure accordingly:

**Option 1: Gmail (Recommended for simplicity)**
- Enable 2-Factor Authentication: https://myaccount.google.com/security
- Generate App Password: https://myaccount.google.com/apppasswords
- Set SMTP_HOST=smtp.gmail.com, SMTP_PORT=587

**Option 2: Outlook/Hotmail**
- Use your Microsoft account credentials
- Set SMTP_HOST=smtp-mail.outlook.com, SMTP_PORT=587

**Option 3: European Email Providers**
See detailed configurations below for popular European providers.

**Option 4: Custom SMTP Provider**
- Use your provider's SMTP server details
- Common ports: 587 (STARTTLS), 465 (SSL), 25 (unencrypted)

Environment variables:
```bash
# Generic SMTP configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_STARTTLS=true
FROM_EMAIL=your-email@example.com
RECIPIENT_EMAIL=recipient@example.com
EMAIL_SENDER_NAME=RSS Digest
```

## European Email Provider Configurations

Below are SMTP configurations for popular European email providers that prioritize privacy and GDPR compliance:

### German Providers

**Posteo (Germany) - Privacy-focused, €1/month**
```bash
SMTP_HOST=posteo.de
SMTP_PORT=587
SMTP_USERNAME=yourname@posteo.de
SMTP_PASSWORD=your-app-password
SMTP_STARTTLS=true
```
- Requires app password generation
- No ads, privacy-focused
- Carbon-neutral hosting

**Mailbox.org (Germany) - €1/month**
```bash
SMTP_HOST=smtp.mailbox.org
SMTP_PORT=587
SMTP_USERNAME=your-email@mailbox.org
SMTP_PASSWORD=your-password
SMTP_STARTTLS=true
```
- Includes office suite
- Strong privacy features
- Based in Germany

**GMX (Germany) - Free tier available**
```bash
SMTP_HOST=mail.gmx.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmx.com
SMTP_PASSWORD=your-password
SMTP_STARTTLS=true
```
- Free with ads option
- Large user base in Germany
- Part of United Internet Group

### Swiss Providers

**ProtonMail (Switzerland) - Requires paid plan for SMTP**
```bash
SMTP_HOST=smtp.protonmail.ch
SMTP_PORT=587
SMTP_USERNAME=your-email@proton.me
SMTP_PASSWORD=your-mail-password
SMTP_STARTTLS=true
```
- End-to-end encryption
- Paid plan required for SMTP access
- Based in Switzerland (outside EU but strong privacy)

### Other European Providers

**Tutanota (Germany) - Limited SMTP access**
```bash
# Note: Tutanota primarily uses web interface
# SMTP available only with specific business plans
# Check current offerings at tutanota.com
```

**Inbox.eu (Latvia)**
```bash
SMTP_HOST=smtp.inbox.eu
SMTP_PORT=587
SMTP_USERNAME=your-email@inbox.eu
SMTP_PASSWORD=your-password
SMTP_STARTTLS=true
```

**Web.de (Germany)**
```bash
SMTP_HOST=smtp.web.de
SMTP_PORT=587
SMTP_USERNAME=your-email@web.de
SMTP_PASSWORD=your-password
SMTP_STARTTLS=true
```

### Choosing a European Provider

**For Privacy**: Posteo, ProtonMail, Tutanota
**For Free Service**: GMX, Web.de
**For Features**: Mailbox.org (includes office suite)
**For Business**: Mailbox.org, ProtonMail Business

**Note**: Some providers may require:
- App passwords instead of main password
- Paid subscriptions for SMTP access
- Specific account settings to enable external clients

Always verify current settings in your provider's documentation as configurations may change.
```

## Phase 5: Testing and Validation

**Objective**: Ensure all changes work correctly and maintain backward compatibility

**Tasks**:
1. Test with different SMTP configurations
2. Validate error handling
3. Test configuration validation
4. Update test functions

**Deliverables**:
- Updated test functions
- Validation scripts

**Changes**:

[MODIFY] `src/email_sender.py` (test function)
```python
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
```

## Phase 6: Implementation Report

**Objective**: Document the completed changes and create implementation report

**Tasks**:
1. Generate final report of all changes
2. Document technical decisions
3. Provide usage examples
4. Create migration guide

**Deliverables**:
- Implementation report at `_ai/backlog/reports/260228_1803__IMPLEMENTATION_REPORT__generic-smtp-email.md`

## Verification Steps

1. **Configuration Validation**:
   ```bash
   # Test environment loading
   uv run python -c "from src.main import load_environment; print(load_environment())"
   ```

2. **Email Testing**:
   ```bash
   # Test SMTP connection
   uv run python src/email_sender.py
   ```

3. **Full Integration Test**:
   ```bash
   # Test with dry run
   uv run python src/main.py --test --dry-run
   ```

4. **Documentation Validation**:
   - Verify README.md updates
   - Check .env.example completeness
   - Validate configuration examples

## Technical Decisions

1. **Backward Compatibility**: Maintained support for existing Gmail configuration with deprecation warnings
2. **Security**: Added STARTTLS configuration option for secure connections
3. **Error Handling**: Enhanced error messages to be provider-agnostic
4. **Configuration**: Separated SMTP username from sender email for flexibility
5. **Validation**: Added comprehensive environment variable validation

## Migration Guide

### For Existing Gmail Users
No immediate action required - existing configuration will work with deprecation warnings. To migrate:

1. Update `.env` file:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-gmail@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_STARTTLS=true
   ```

### For New SMTP Providers
1. Set the 5 required SMTP variables in `.env`
2. Test configuration with `uv run python src/email_sender.py`
3. Run full digest with `uv run python src/main.py --test`
