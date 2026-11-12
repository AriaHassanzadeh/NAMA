from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import OperationalError
from django.test import TestCase
from rest_framework.test import APIClient


class HealthTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def test_ready_checks_real_postgres(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "ok"})
        self.assertIn("no-store", response["Cache-Control"])

    def test_database_failure_is_503_without_connection_details(self):
        with patch("health.views.connection.cursor", side_effect=OperationalError("password=secret host=private")):
            response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable", "database": "unavailable"})
        self.assertNotIn(b"secret", response.content)
        self.assertNotIn(b"private", response.content)
        self.assertIn("no-store", response["Cache-Control"])

    def test_health_does_not_accept_writes(self):
        for method in (self.client.post, self.client.put, self.client.patch, self.client.delete):
            with self.subTest(method=method.__name__):
                self.assertEqual(method("/api/v1/health/", {}, format="json").status_code, 405)

    def test_head_has_no_body(self):
        response = self.client.head("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_custom_user_can_be_saved_and_password_is_hashed(self):
        user = get_user_model().objects.create_user(username="test-user", password="test-only-password")
        self.assertEqual(user._meta.label, "accounts.User")
        self.assertTrue(user.check_password("test-only-password"))
        self.assertNotEqual(user.password, "test-only-password")
