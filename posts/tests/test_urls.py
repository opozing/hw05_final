from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get("/")
        self.assertEqual(response.status_code, 200)


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            username="sergey",
        )

        cls.user2 = User.objects.create(
            username="neseregey"
        )

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="testslug",
            description="testdescription"
        )

        cls.post = Post.objects.create(
            text="Тестовый пост",
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2.force_login(self.user2)

    def test_posts_url_authorized(self):
        """Доступность страниц posts/ авторизованному пользователю. Автору"""
        url_names = (
            reverse("posts:group_posts", kwargs={"slug": self.group.slug}),
            reverse("posts:new_post"),
            reverse("posts:profile", kwargs={"username": self.user}),
            reverse("posts:post", kwargs={"username": self.user,
                                          "post_id": self.post.id}),
            reverse("posts:post_edit", kwargs={"username": self.user,
                                               "post_id": self.post.id}),
        )

        for reverse_url in url_names:
            with self.subTest():
                response = self.authorized_client.get(reverse_url)
                self.assertEqual(response.status_code, 200)

    def test_edit_url_unauthorized(self):
        """
        Доступность страницы /edit/ авторизованному пользователю. Не автору
        """
        response = self.authorized_client2.get(reverse("posts:post_edit",
                                               kwargs={"username": self.user,
                                                       "post_id": self.post.id}
                                                       ))
        self.assertEqual(response.status_code, 302)

    def test_posts_url_unauthorized(self):
        """Доступность страниц posts/urls не авторизованному пользователю."""
        url_names = {
            reverse("posts:group_posts",
                    kwargs={"slug": self.group.slug}): 200,
            reverse("posts:new_post"): 302,
            reverse("posts:profile", kwargs={"username": self.user}): 200,
            reverse("posts:post", kwargs={"username": self.user,
                                          "post_id": self.post.id}): 200,
            reverse("posts:post_edit", kwargs={"username": self.user,
                                               "post_id": self.post.id}): 302,
        }

        for reverse_url, status in url_names.items():
            with self.subTest():
                response = self.guest_client.get(reverse_url)
                self.assertEqual(response.status_code, status)

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соответствующий шаблон."""
        templates_url_names = {
            "/": "index.html",
            f"/group/{self.group.slug}/": "group.html",
            "/new/": "new_post.html",
            f"/{self.user}/": "profile.html",
            f"/{self.user}/{self.post.id}/": "post.html",
            f"/{self.user}/{self.post.id}/edit/": "new_post.html",
        }

        for reverse_name, template in templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_edit_url_redirect_unauthorized(self):
        """Редирект со страницы /edit/ для тех у кого нет прав доступа."""
        clients = {
            self.guest_client:
            f"/auth/login/?next=/{self.user}/{self.post.id}/edit/",
            self.authorized_client2: f"/{self.user}/{self.post.id}/",
        }
        for client_type, url_redirect in clients.items():
            with self.subTest():
                response = client_type.get(reverse("posts:post_edit",
                                           kwargs={"username": self.user,
                                                   "post_id": self.post.id}))
                self.assertRedirects(response, url_redirect)

    def test_get_404_if_not_found(self):
        """Запрос к несуществующей странице возвращает код 404"""
        response = self.guest_client.get("/asda/")
        self.assertEqual(response.status_code, 404)
