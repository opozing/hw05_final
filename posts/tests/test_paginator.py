import time

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username="sergey",
        )

        for i in range(12):
            Post.objects.create(
                text=f"Тестовый пост{str(i)}",
                author=cls.user
            )
            time.sleep(0.001)

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """На первой странице должно быть десять постов."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_two_records(self):
        """На второй странице должно быть два поста."""
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 2)

    def test_posts_page1_content_is_right(self):
        """Содержимое постов на странице 1 соответствует ожиданиям."""
        response = self.guest_client.get(reverse("posts:index") + "?page=1")
        context_get = response.context.get("page")[0]
        self.assertEqual(context_get.text, "Тестовый пост11")
        self.assertEqual(context_get.author.username, "sergey")

    def test_posts_page2_content_is_right(self):
        """Содержимое постов на странице 2 соответствует ожиданиям."""
        response = self.guest_client.get(reverse("posts:index") + "?page=2")
        context_get = response.context.get("page")[0]
        self.assertEqual(context_get.text, "Тестовый пост1")
        self.assertEqual(context_get.author.username, "sergey")
