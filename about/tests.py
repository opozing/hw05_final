from django.test import Client, TestCase
from django.urls import reverse


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_urls_available(self):
        """Страницы /about/ доступны любому пользователю."""
        response_urls = ("/about/author/", "/about/tech/")
        for url in response_urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)


class AboutViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_views_uses_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_path_names = {
            "about/author.html": reverse("about:author"),
            "about/tech.html": reverse("about:tech"),
        }

        for template, reverse_name in templates_path_names.items():
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
