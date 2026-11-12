from django.test import SimpleTestCase
from rest_framework.test import APIClient


class EntryOptionsTests(SimpleTestCase):
    endpoint = "/api/v1/demo/entry-options/"

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def test_public_get_returns_explicit_demo_ideas(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload), {"source_kind", "label", "idea_examples"})
        self.assertEqual(payload["source_kind"], "demo")
        self.assertEqual(payload["label"], "داده‌های نمایشی؛ بدون اتصال به بازار واقعی")
        self.assertEqual(
            [example["id"] for example in payload["idea_examples"]],
            ["minimal-womenswear", "sportswear-shop", "casualwear-brand"],
        )
        for example in payload["idea_examples"]:
            self.assertEqual(set(example), {"id", "text", "icon"})
            self.assertTrue(example["text"])
            self.assertIn(example["icon"], {"shirt", "bolt"})

    def test_demo_response_is_not_cached(self):
        response = self.client.get(self.endpoint)
        self.assertIn("no-store", response["Cache-Control"])

    def test_demo_endpoint_rejects_writes(self):
        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.endpoint, {}, format="json")
                self.assertEqual(response.status_code, 405)
                self.assertIn("no-store", response["Cache-Control"])

    def test_head_returns_no_body(self):
        response = self.client.head(self.endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
