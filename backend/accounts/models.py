from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Project user, established before the first migration."""
