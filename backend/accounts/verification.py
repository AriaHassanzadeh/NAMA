"""Single-use email verification without storing or logging bearer tokens."""
import hashlib
import logging
import re
import secrets
from datetime import timedelta
from smtplib import SMTPException
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import EmailVerification, User

logger = logging.getLogger(__name__)
VERIFICATION_TTL = timedelta(hours=24)
RESEND_COOLDOWN = timedelta(seconds=60)


def token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def send_verification(user_id):
    """Serialize issuance per user and invalidate older links on resend."""
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)
        if user.is_active or not user.email_verification_required or user.email_verified_at:
            return
        now = timezone.now()
        previous = EmailVerification.objects.filter(user=user).first()
        if previous and previous.sent_at > now - RESEND_COOLDOWN:
            return
        token = secrets.token_urlsafe(32)
        verification, _ = EmailVerification.objects.update_or_create(user=user, defaults={
            "email": user.email,
            "token_hash": token_digest(token), "sent_at": now,
            "expires_at": now + VERIFICATION_TTL, "consumed_at": None,
        })
        link = settings.ACCOUNT_VERIFICATION_ORIGIN.rstrip("/") + "/auth/verify#" + urlencode({"token": token})
        try:
            delivered = send_mail(
                "Verify your NAMA Analyze email",
                "Confirm your email address to sign in to NAMA Analyze.\n\n"
                + link + "\n\nThis link expires in 24 hours and works once. "
                "If you did not request this account, ignore this email.",
                settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False,
            )
        except (SMTPException, OSError):
            # Avoid exception details, recipients and bearer tokens in application logs.
            logger.warning("Verification email delivery failed.")
            delivered = 0
        if not delivered:
            # An undelivered message must not leave an apparently usable token.
            verification.delete()


def confirm_verification(token):
    if re.fullmatch(r"[A-Za-z0-9_-]{43}", token) is None:
        return False
    digest = token_digest(token)
    # First obtain the user ID without locking. All issuance/consumption then locks
    # User before EmailVerification, so resend and confirm have the same lock order.
    user_id = EmailVerification.objects.filter(token_hash=digest).values_list("user_id", flat=True).first()
    if user_id is None:
        return False
    with transaction.atomic():
        user = User.objects.select_for_update().filter(pk=user_id).first()
        if user is None:
            return False
        verification = EmailVerification.objects.select_for_update().filter(user=user, token_hash=digest).first()
        now = timezone.now()
        if not verification or verification.consumed_at or verification.expires_at <= now:
            return False
        if user.is_active or not user.email_verification_required or user.email_verified_at:
            return False
        if verification.email != user.email:
            return False
        verification.consumed_at = now
        verification.save(update_fields=["consumed_at"])
        user.email_verified_at = now
        user.is_active = True
        user.save(update_fields=["email_verified_at", "is_active"])
        return True
