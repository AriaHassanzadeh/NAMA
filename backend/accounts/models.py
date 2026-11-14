from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower, Trim


class User(AbstractUser):
    """Project user, established before the first migration."""

    email_verification_required = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower(Trim("email")), condition=~models.Q(email=""),
                name="accounts_user_email_ci_unique",
            ),
        ]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)


class EmailVerification(models.Model):
    """Only a digest is stored; each new message replaces the previous token."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="email_verification")
    email = models.EmailField(max_length=254)
    token_hash = models.CharField(max_length=64, unique=True)
    sent_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
