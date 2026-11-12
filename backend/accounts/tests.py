from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient


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
