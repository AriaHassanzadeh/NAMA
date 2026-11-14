from datetime import timedelta
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from .models import EmailVerification
from .verification import token_digest


class SessionAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="session-user", password="test-only-password")

    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf_token(self):
        response = self.client.get("/api/v1/auth/csrf/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)
        self.assertIn("no-store", response["Cache-Control"])
        return response.json()["csrfToken"]

    def test_anonymous_login_requires_csrf_even_with_valid_credentials(self):
        response = self.client.post("/api/v1/auth/login/", {"username": self.user.username, "password": "test-only-password"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("sessionid", self.client.cookies)

    def test_session_login_me_and_csrf_protected_logout(self):
        token = self.csrf_token()
        response = self.client.post("/api/v1/auth/login/", {"username": self.user.username, "password": "test-only-password"}, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], self.user.username)
        self.assertNotIn("password", response.content.decode())
        self.assertTrue(response.cookies["sessionid"]["httponly"])
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/logout/", {}, format="json").status_code, 403)
        response = self.client.post("/api/v1/auth/logout/", {}, format="json", HTTP_X_CSRFTOKEN=response.json()["csrfToken"])
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 403)

    def test_invalid_credentials_do_not_identify_existing_user(self):
        token = self.csrf_token()
        failures = []
        for username in (self.user.username, "unknown-user"):
            response = self.client.post("/api/v1/auth/login/", {"username": username, "password": "wrong"}, format="json", HTTP_X_CSRFTOKEN=token)
            self.assertEqual(response.status_code, 400)
            failures.append(response.json())
        self.assertEqual(failures[0], failures[1])

    def test_login_attempts_are_bounded(self):
        token = self.csrf_token()
        for _ in range(10):
            self.client.post("/api/v1/auth/login/", {"username": "missing", "password": "wrong"}, format="json", HTTP_X_CSRFTOKEN=token)
        response = self.client.post("/api/v1/auth/login/", {"username": "missing", "password": "wrong"}, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response)


class VerifiedEmailAPITests(TestCase):
    password = "Unrelated-River!6842"

    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)
        self.token = self.client.get("/api/v1/auth/csrf/").json()["csrfToken"]

    def post(self, path, data, **extra):
        return self.client.post("/api/v1/auth/" + path, data, format="json", HTTP_X_CSRFTOKEN=self.token, **extra)

    def signup(self, email="builder@example.com", **extra):
        return self.post("signup/", {"email": email, "password": self.password, **extra})

    def latest_token(self):
        link = next(line for line in mail.outbox[-1].body.splitlines() if line.startswith("http"))
        self.assertEqual(urlsplit(link).path, "/auth/verify")
        self.assertEqual(urlsplit(link).query, "")
        return parse_qs(urlsplit(link).fragment)["token"][0]

    def test_signup_stores_hashes_and_requires_verification_before_session_login(self):
        response = self.signup("Builder@EXAMPLE.COM", display_name="Aria")
        self.assertEqual(response.status_code, 202)
        self.assertIn("no-store", response["Cache-Control"])
        user = get_user_model().objects.get(email="builder@example.com")
        self.assertFalse(user.is_active)
        self.assertTrue(user.email_verification_required)
        self.assertIsNone(user.email_verified_at)
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))
        token = self.latest_token()
        verification = EmailVerification.objects.get(user=user)
        self.assertEqual(verification.token_hash, token_digest(token))
        self.assertNotIn(token, response.content.decode())
        self.assertNotIn(self.password, response.content.decode())
        self.assertNotIn("sessionid", self.client.cookies)
        failure = self.post("login/", {"email": user.email, "password": self.password})
        self.assertEqual(failure.status_code, 400)
        self.assertEqual(failure.json(), self.post("login/", {"email": "missing@example.com", "password": self.password}).json())
        self.assertEqual(self.post("verification/confirm/", {"token": token}).status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.email_verified_at)
        self.assertNotIn("sessionid", self.client.cookies)
        login = self.post("login/", {"email": "BUILDER@example.com", "password": self.password})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()["user"]["email"], user.email)
        self.assertEqual(login.json()["user"]["display_name"], "Aria")
        self.assertTrue(login.cookies["sessionid"]["httponly"])

    def test_all_public_unsafe_verification_operations_require_csrf(self):
        for path, data in (("signup/", {"email": "missing@example.com", "password": self.password}), ("verification/resend/", {"email": "missing@example.com"}), ("verification/confirm/", {"token": "invalid"})):
            response = self.client.post("/api/v1/auth/" + path, data, format="json")
            self.assertEqual(response.status_code, 403)
        self.assertFalse(get_user_model().objects.exists())

    def test_password_policy_and_input_validation_do_not_create_accounts(self):
        for index, password in enumerate(("short", "password", "123456789012", "similar@example.com")):
            response = self.post("signup/", {"email": f"similar{index}@example.com", "password": password})
            self.assertEqual(response.status_code, 400)
            self.assertIn("password", response.json())
        self.assertEqual(self.signup("not-an-email").status_code, 400)
        self.assertFalse(get_user_model().objects.exists())

    def test_duplicate_signup_is_generic_and_does_not_modify_or_resend(self):
        first = self.signup()
        user = get_user_model().objects.get()
        password_hash = user.password
        for _ in range(2):
            duplicate = self.post("signup/", {"email": "BUILDER@EXAMPLE.COM", "password": "Different-Password!2486", "display_name": "Overwrite"})
            self.assertEqual(duplicate.status_code, first.status_code)
            self.assertEqual(duplicate.json(), first.json())
        user.refresh_from_db()
        self.assertEqual(user.password, password_hash)
        self.assertEqual(user.first_name, "")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_confirmation_expires_and_can_only_be_used_once(self):
        self.signup()
        token = self.latest_token()
        verification = EmailVerification.objects.get()
        EmailVerification.objects.filter(pk=verification.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        expired = self.post("verification/confirm/", {"token": token})
        invalid = self.post("verification/confirm/", {"token": "not-a-valid-link"})
        self.assertEqual(expired.status_code, 400)
        self.assertEqual(expired.json(), invalid.json())
        EmailVerification.objects.filter(pk=verification.pk).update(expires_at=timezone.now() + timedelta(hours=1))
        self.assertEqual(self.post("verification/confirm/", {"token": token}).status_code, 200)
        replay = self.post("verification/confirm/", {"token": token})
        self.assertEqual(replay.status_code, 400)
        self.assertEqual(replay.json(), invalid.json())

    def test_resend_is_generic_cooldown_limited_and_invalidates_older_link(self):
        self.signup()
        old = self.latest_token()
        pending = self.post("verification/resend/", {"email": "builder@example.com"})
        missing = self.post("verification/resend/", {"email": "missing@example.com"})
        self.assertEqual(pending.status_code, 202)
        self.assertEqual(pending.json(), missing.json())
        self.assertEqual(len(mail.outbox), 1)
        EmailVerification.objects.update(sent_at=timezone.now() - timedelta(seconds=61))
        self.assertEqual(self.post("verification/resend/", {"email": "BUILDER@example.com"}).status_code, 202)
        self.assertEqual(len(mail.outbox), 2)
        newest = self.latest_token()
        self.assertNotEqual(newest, old)
        self.assertEqual(self.post("verification/confirm/", {"token": old}).status_code, 400)
        self.assertEqual(self.post("verification/confirm/", {"token": newest}).status_code, 200)
        self.assertEqual(self.post("verification/resend/", {"email": "builder@example.com"}).status_code, 202)
        self.assertEqual(len(mail.outbox), 2)

    def test_email_address_rate_limit_spans_different_client_ips(self):
        for index in range(5):
            response = self.post("verification/resend/", {"email": "Missing@Example.com"}, REMOTE_ADDR=f"127.0.0.{index + 1}")
            self.assertEqual(response.status_code, 202)
        response = self.post("verification/resend/", {"email": "missing@example.com"}, REMOTE_ADDR="127.0.0.20")
        self.assertEqual(response.status_code, 429)

    def test_delivery_mode_depends_only_on_configuration(self):
        with override_settings(EMAIL_BACKEND="django.core.mail.backends.filebased.EmailBackend"):
            response = self.post("verification/resend/", {"email": "missing@example.com"})
            self.assertEqual(response.json()["delivery_mode"], "local")
        with override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"):
            response = self.post("verification/resend/", {"email": "missing@example.com"})
            self.assertEqual(response.json()["delivery_mode"], "smtp")

    def test_old_link_cannot_verify_a_replacement_email_address(self):
        self.signup()
        token = self.latest_token()
        user = get_user_model().objects.get()
        user.email = "replacement@example.com"
        user.save(update_fields=["email"])
        self.assertEqual(self.post("verification/confirm/", {"token": token}).status_code, 400)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertIsNone(user.email_verified_at)

    def test_delivery_failure_is_generic_and_does_not_log_the_token(self):
        with patch("accounts.verification.send_mail", side_effect=OSError("private delivery details")):
            with self.assertLogs("accounts.verification", level="WARNING") as captured:
                response = self.signup()
        self.assertEqual(response.status_code, 202)
        self.assertFalse(EmailVerification.objects.exists())
        self.assertTrue(get_user_model().objects.exists())
        self.assertEqual(len(captured.output), 1)
        self.assertNotIn("private delivery details", captured.output[0])

    def test_login_identity_rate_limit_spans_different_client_ips(self):
        for index in range(10):
            response = self.post("login/", {"email": "missing@example.com", "password": self.password}, REMOTE_ADDR=f"127.0.0.{index + 1}")
            self.assertEqual(response.status_code, 400)
        self.assertEqual(self.post("login/", {"email": "MISSING@example.com", "password": self.password}, REMOTE_ADDR="127.0.0.20").status_code, 429)

    def test_preserved_padded_legacy_email_supports_login_and_duplicate_signup(self):
        model = get_user_model()
        user = model.objects.create_user(username="legacy-owner", email="owner@example.com", password=self.password)
        model.objects.filter(pk=user.pk).update(email=" OWNER@EXAMPLE.COM ")
        self.assertEqual(self.signup("owner@example.com").status_code, 202)
        self.assertEqual(model.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)
        response = self.post("login/", {"email": "Owner@example.com", "password": self.password})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["id"], user.pk)
        user.refresh_from_db()
        self.assertEqual(user.email, " OWNER@EXAMPLE.COM ")

    def test_database_email_uniqueness_is_case_insensitive_and_allows_legacy_blanks(self):
        model = get_user_model()
        model.objects.create_user(username="first", email="OWNER@example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            model.objects.bulk_create([model(username="second", email="owner@EXAMPLE.com")])
        model.objects.create_user(username="blank-one")
        model.objects.create_user(username="blank-two")
        self.assertEqual(model.objects.filter(email="").count(), 2)


class EmailMigrationSafetyTests(TransactionTestCase):
    """Exercise the preflight on the temporary test database, never user data."""

    migrate_from = [("accounts", "0001_initial")]
    migrate_to = [("accounts", "0002_emailverification_user_email_verification_required_and_more")]

    def test_preflight_rejects_duplicates_without_changing_accounts(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_user = executor.loader.project_state(self.migrate_from).apps.get_model("accounts", "User")
        first = old_user.objects.create(username="legacy-first", email="Owner@example.com")
        second = old_user.objects.create(username="legacy-second", email=" OWNER@EXAMPLE.COM ")
        try:
            with self.assertRaisesMessage(RuntimeError, "duplicate nonblank email"):
                MigrationExecutor(connection).migrate(self.migrate_to)
            self.assertEqual(old_user.objects.get(pk=first.pk).email, "Owner@example.com")
            self.assertTrue(old_user.objects.filter(pk=second.pk).exists())
        finally:
            old_user.objects.filter(pk=second.pk).delete()
            MigrationExecutor(connection).migrate(self.migrate_to)
