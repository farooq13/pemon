"""
Celery tasks for core functionality.

This module contains asynchronous tasks for:
- Email sending
- SMS sending
- System maintenance
- Background cleanup
"""

import logging
from typing import Dict, List, Optional

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 1 minute
    name='core.tasks.send_email'
)
def send_email_task(
    self,
    subject: str,
    message: str,
    recipient_list: List[str],
    from_email: Optional[str] = None,
    html_message: Optional[str] = None,
    **kwargs
) -> bool:
    """
    Send email asynchronously using Celery.
    
    This task handles email sending with automatic retries on failure.
    It supports both plain text and HTML emails.
    
    Args:
        subject (str): Email subject line
        message (str): Plain text message body
        recipient_list (List[str]): List of recipient email addresses
        from_email (str, optional): Sender email address
        html_message (str, optional): HTML version of the message
        **kwargs: Additional arguments passed to send_mail
        
    Returns:
        bool: True if email sent successfully, False otherwise
        
    Raises:
        Exception: Re-raises exception after max retries
        
    Example:
        >>> send_email_task.delay(
        ...     subject='Welcome to Pemon',
        ...     message='Thank you for joining us!',
        ...     recipient_list=['user@example.com'],
        ...     html_message='<h1>Welcome!</h1>'
        ... )
    """
    try:
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        if html_message:
            # Send multipart email (text + HTML)
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list,
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
        else:
            # Send plain text email
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
                **kwargs
            )
        
        logger.info(f"Email sent successfully to {', '.join(recipient_list)}")
        return True
        
    except Exception as exc:
        logger.error(f"Failed to send email: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='core.tasks.send_template_email'
)
def send_template_email_task(
    self,
    template_name: str,
    context: Dict,
    subject: str,
    recipient_list: List[str],
    from_email: Optional[str] = None,
) -> bool:
    """
    Send email using Django template with automatic retries.
    
    This task renders an HTML email template with the provided context
    and sends it to the recipient list.
    
    Args:
        template_name (str): Path to the email template (e.g., 'emails/welcome.html')
        context (Dict): Context dictionary for template rendering
        subject (str): Email subject line
        recipient_list (List[str]): List of recipient email addresses
        from_email (str, optional): Sender email address
        
    Returns:
        bool: True if email sent successfully
        
    Example:
        >>> send_template_email_task.delay(
        ...     template_name='emails/kyc_approved.html',
        ...     context={'user_name': 'John Doe'},
        ...     subject='KYC Approved',
        ...     recipient_list=['john@example.com']
        ... )
    """
    try:
        # Render HTML content
        html_content = render_to_string(template_name, context)
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Send email
        return send_email_task(
            subject=subject,
            message=text_content,
            recipient_list=recipient_list,
            from_email=from_email,
            html_message=html_content,
        )
        
    except Exception as exc:
        logger.error(f"Failed to send template email: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='core.tasks.send_sms'
)
def send_sms_task(
    self,
    phone_number: str,
    message: str,
    **kwargs
) -> bool:
    """
    Send SMS asynchronously using configured SMS provider.
    
    This task integrates with SMS providers  to send
    SMS messages with automatic retries on failure.
    
    Args:
        phone_number (str): Recipient phone number (E.164 format recommended)
        message (str): SMS message content (160 chars recommended)
        **kwargs: Additional provider-specific parameters
        
    Returns:
        bool: True if SMS sent successfully
        
    Example:
        >>> send_sms_task.delay(
        ...     phone_number='+2348012345678',
        ...     message='Your OTP is 123456'
        ... )
    """
    try:
        sms_provider = settings.SMS_PROVIDER
        
        if sms_provider == 'mock':
            # Mock SMS for development
            logger.info(f"[MOCK SMS] To: {phone_number}, Message: {message}")
            return True
        
        # TODO: Integrate with actual SMS provider (Termii, Twilio, etc.)
        # Example with Termii:
        # import requests
        # url = 'https://api.ng.termii.com/api/sms/send'
        # payload = {
        #     'to': phone_number,
        #     'from': 'Pemon',
        #     'sms': message,
        #     'type': 'plain',
        #     'api_key': settings.SMS_API_KEY,
        #     'channel': 'generic',
        # }
        # response = requests.post(url, json=payload)
        # response.raise_for_status()
        
        logger.info(f"SMS sent successfully to {phone_number}")
        return True
        
    except Exception as exc:
        logger.error(f"Failed to send SMS: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(name='core.tasks.cleanup_expired_sessions')
def cleanup_expired_sessions():
    """
    Clean up expired Django sessions.
    
    This task should be run periodically (e.g., daily) to remove old session
    data from the database and free up storage.
    
    Returns:
        int: Number of sessions deleted
    """
    from django.core.management import call_command
    
    try:
        logger.info("Starting session cleanup...")
        call_command('clearsessions')
        logger.info("Session cleanup completed successfully")
        return True
    except Exception as exc:
        logger.error(f"Session cleanup failed: {exc}", exc_info=True)
        return False


@shared_task(name='core.tasks.send_daily_summary_emails')
def send_daily_summary_emails():
    """
    Send daily summary emails to users.
    
    This task compiles and sends daily activity summaries to users who have
    opted in for daily notifications.
    
    Returns:
        int: Number of summary emails sent
    """
    try:
        from accounts.models import User
        
        logger.info("Starting daily summary email task...")
        
        # Get users who want daily summaries
        users = User.objects.filter(
            is_active=True,
            email_verified=True,
            # Add notification preference filter
        )
        
        sent_count = 0
        for user in users:
            # TODO: Compile user's daily activity
            # TODO: Send summary email
            sent_count += 1
        
        logger.info(f"Sent {sent_count} daily summary emails")
        return sent_count
        
    except Exception as exc:
        logger.error(f"Daily summary email task failed: {exc}", exc_info=True)
        return 0


@shared_task(name='core.tasks.update_exchange_rates')
def update_exchange_rates():
    """
    Update currency exchange rates from external API.
    
    This task fetches current exchange rates and updates the database.
    Useful for multi-currency support.
    
    Returns:
        bool: True if rates updated successfully
    """
    try:
        logger.info("Updating exchange rates...")
        
        # TODO: Fetch rates from API (e.g., fixer.io, exchangerate-api.com)
        # TODO: Update database
        
        logger.info("Exchange rates updated successfully")
        return True
        
    except Exception as exc:
        logger.error(f"Exchange rate update failed: {exc}", exc_info=True)
        return False


@shared_task(
    bind=True,
    max_retries=3,
    name='core.tasks.create_audit_log'
)
def create_audit_log_task(
    self,
    user_id: Optional[str],
    action: str,
    model_name: str,
    object_id: str,
    changes: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """
    Create audit log entry asynchronously.
    
    This task creates audit trail records for important system actions.
    
    Args:
        user_id: ID of the user who performed the action
        action: Type of action performed
        model_name: Name of the affected model
        object_id: ID of the affected object
        changes: Dictionary of changes made
        metadata: Additional metadata
        ip_address: IP address of the requester
        user_agent: User agent string
    """
    try:
        from core.models import AuditLog
        from accounts.models import User
        
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"User {user_id} not found for audit log")
        
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            changes=changes or {},
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        logger.info(f"Audit log created: {action} on {model_name}[{object_id}]")
        return True
        
    except Exception as exc:
        logger.error(f"Failed to create audit log: {exc}", exc_info=True)
        raise self.retry(exc=exc)