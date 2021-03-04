import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post


@override_settings(MEDIA_ROOT=settings.MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create_user(
            username="sergey",
        )

        cls.user2 = User.objects.create_user(
            username="sergey2"
        )

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="testslug",
            description="testdescription"
        )

        cls.group2 = Group.objects.create(
            title="Тестовая группа 2",
            slug="testslug2",
            description="testdescription2"
        )

        cls.post = Post.objects.create(
            text="Тестовый пост",
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.user2
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2.force_login(self.user2)

    def test_comment_create(self):
        """Авторизированный юзер может комментировать посты"""
        comments = {
            'post': self.post,
            'author': self.user,
            'text': 'One Two',
        }
        self.authorized_client.post(reverse('posts:add_comment',
                                    kwargs={'username': self.user.username,
                                            'post_id': self.post.id}),
                                    data=comments)
        response = self.authorized_client.get(
            reverse('posts:post', kwargs={'username': self.user.username,
                                          'post_id': self.post.id}))
        self.assertEqual(response.context.get('comments')[0].text, 'One Two')

    def test_no_comment_unauthorized(self):
        """Неавториизированный юзер не может комментировать."""
        comment = {'post': self.post,
                   'author': self.user,
                   'text': "One Two"}
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id}), data=comment)
        self.assertEqual(response.status_code, 302)

    def test_follow_new_post_view(self):
        """Новый пост юзера появляется у тех, кто на него подписан."""
        response = self.authorized_client2.get(reverse('posts:follow_index'))
        self.assertEqual(response.context["page"][0].text, self.post.text)

    def test_unfollow_new_post_unview(self):
        """Новый пост юзера не появляется у тех, кто на него не подписан."""
        post2 = Post.objects.create(text="Тестовый пост", author=self.user2)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(post2, response.context["page"])

    def test_follow(self):
        """Авторизованный юзер может подписываться на других авторов."""
        self.authorized_client2.get(reverse('posts:profile_follow',
                                    kwargs={'username': self.user}))
        self.assertTrue(Follow.objects.filter(user=self.user2,
                                              author=self.user))

    def test_unfollow(self):
        """Авторизованный юзер может отписываться."""
        self.authorized_client2.get(reverse('posts:profile_unfollow',
                                    kwargs={'username': self.user}))
        self.assertFalse(Follow.objects.filter(user=self.user2,
                                               author=self.user))

    def test_cache_index_page(self):
        """Проверка работы кеша главной страницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        cached_response_content = response.content
        post = Post.objects.all().last()
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(cached_response_content, response.content)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(cached_response_content, response.content)

    def test_views_uses_correct_templates(self):
        """URL-адреса используют соответствующие шаблоны."""
        templates_path_names = {
            reverse("posts:index"): "index.html",
            reverse("posts:group_posts",
                    kwargs={"slug": self.group.slug}): "group.html",
            reverse("posts:new_post"): "new_post.html",
            reverse("posts:profile",
                    kwargs={"username": self.user}): "profile.html",
            reverse("posts:post",
                    kwargs={"username": self.user,
                            "post_id": self.post.id}): "post.html",
            reverse("posts:post_edit",
                    kwargs={"username": self.user,
                            "post_id": self.post.id}): "new_post.html",
        }

        for reverse_name, template in templates_path_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_index_get_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:index"))
        context_get = response.context["page"][0]
        self.assertEqual(context_get.text, self.post.text)
        self.assertEqual(context_get.pub_date, self.post.pub_date)
        self.assertEqual(context_get.author.username,
                         self.post.author.username)
        self.assertEqual(context_get.group.title, self.post.group.title)
        self.assertEqual(context_get.image, self.post.image)

    def test_posts_group_get_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:group_posts",
                                              kwargs={"slug": self.group.slug})
                                              )
        context_page = response.context["page"][0]
        self.assertEqual(context_page.text, self.post.text)
        self.assertEqual(context_page.pub_date, self.post.pub_date)
        self.assertEqual(context_page.author.username,
                         self.post.author.username)
        self.assertEqual(context_page.group.title, self.post.group.title)
        self.assertEqual(context_page.image, self.post.image)

        context_group = response.context["group"]
        self.assertEqual(context_group.title, self.group.title)
        self.assertEqual(context_group.slug, self.group.slug)
        self.assertEqual(context_group.description, self.group.description)

    def test_posts_new_get_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:new_post"))
        form_fields = {
            "group": forms.fields.ChoiceField,
            "text": forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest():
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_in_right_group(self):
        """Созданный пост попал в нужную группу"""
        response_groups = {
            "group_with_post": (reverse("posts:group_posts",
                                kwargs={"slug": self.group.slug})),
            "group_without_post": (reverse("posts:group_posts",
                                   kwargs={"slug": self.group2.slug})),
        }

        for group_name, reverse_group in response_groups.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_group)
                posts_in_group = response.context.get("page")
                if group_name == "group_with_post":
                    self.assertIn(self.post, posts_in_group)
                else:
                    self.assertNotIn(self.post, posts_in_group)

    def test_posts_profile_get_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse("posts:profile",
                                         kwargs={"username": self.user}))
        context_page = response.context["page"][0]

        self.assertEqual(response.context["author"], self.post.author)
        self.assertEqual(context_page.text, self.post.text)
        self.assertEqual(context_page.pub_date, self.post.pub_date)
        self.assertEqual(context_page.author, self.post.author)
        self.assertEqual(context_page.group, self.post.group)
        self.assertEqual(context_page.image, self.post.image)

    def test_posts_post_view_get_correct_context(self):
        """Шаблон post_view сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post", kwargs={
                                              "username": self.user,
                                              "post_id": self.post.id}))
        context_chosen = response.context["post"]

        self.assertEqual(context_chosen.text, self.post.text)
        self.assertEqual(context_chosen.pub_date, self.post.pub_date)
        self.assertEqual(context_chosen.author, self.post.author)
        self.assertEqual(context_chosen.group, self.post.group)
        self.assertEqual(context_chosen.image, self.post.image)

    def test_posts_post_edit_get_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            "posts:post_edit", kwargs={"username": self.user,
                                       "post_id": self.post.id}))
        form_fields = {
            "group": forms.fields.ChoiceField,
            "text": forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest():
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

        context_chosen = response.context["post"]
        self.assertEqual(context_chosen.text, self.post.text)
        self.assertEqual(context_chosen.pub_date, self.post.pub_date)
        self.assertEqual(context_chosen.author, self.post.author)
        self.assertEqual(context_chosen.group, self.post.group)
        self.assertEqual(context_chosen.image, self.post.image)

    def test_posts_post_edit_no_empty_field(self):
        """Форма post_edit не получает пустое поле text"""
        response = self.authorized_client.get(reverse(
            "posts:post_edit", kwargs={"username": self.user,
                                       "post_id": self.post.id}))
        field = response.context["post"].text
        self.assertEqual(field, self.post.text)
