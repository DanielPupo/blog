import unittest
from datetime import datetime
from unittest.mock import patch

import app as blog


POST = {
    "idPost": 1,
    "title": "Um título seguro",
    "content": "Texto puro <script>alert(1)</script>",
    "datePost": datetime(2026, 1, 2, 10, 30),
    "idUser": 7,
    "user": "daniel",
    "picture": "placeholder.svg",
}


class BlogRoutesTest(unittest.TestCase):
    def setUp(self):
        blog.app.config.update(TESTING=True, SECRET_KEY="test-secret", SESSION_COOKIE_SECURE=False)
        self.client = blog.app.test_client()
        self.posts_patch = patch.object(blog.db, "listar_posts", return_value=[POST])
        self.post_patch = patch.object(
            blog.db, "obter_post", side_effect=lambda post_id: POST if post_id == 1 else None
        )
        self.posts_patch.start()
        self.post_patch.start()

    def tearDown(self):
        patch.stopall()

    def test_home_has_security_headers_and_escaped_content(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        self.assertIn(b"&lt;script&gt;alert(1)&lt;/script&gt;", response.data)

    def test_article_has_metadata(self):
        response = self.client.get("/post/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<meta property="og:type" content="article">', response.data)
        self.assertIn("Um título seguro".encode(), response.data)

    def test_missing_article_is_404(self):
        self.assertEqual(self.client.get("/post/999").status_code, 404)

    def test_csrf_rejects_post_without_token(self):
        response = self.client.post("/login", data={"user": "x", "password": "y"})
        self.assertEqual(response.status_code, 400)

    def test_destructive_route_does_not_accept_get(self):
        self.assertEqual(self.client.get("/excluirpost/1").status_code, 405)

    def test_healthcheck_does_not_touch_database(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
