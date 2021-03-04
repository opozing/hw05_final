import shutil
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


class PostFormsTests(TestCase):
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

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create(
            username="sergey"
        )

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="testslug",
            description="testdescription",
        )

        cls.post = Post.objects.create(
            text="Тестовый не изменен",
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post_create_by_form(self):
        """Новый пост создается с помощъю формы, редирект"""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый пост1",
            "author": self.user,
            "group": self.group.id,
            "image": self.uploaded,
        }

        response = self.authorized_client.post(
            reverse("posts:new_post"),
            data=form_data,
            follow=True,
        )

        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse("posts:index"))
        self.assertTrue(Post.objects.filter(
            text="Тестовый пост1",
            author=self.user,
            group=self.group.id,
            image="posts/small.gif"
        ).exists())

    def test_post_edit_save_to_database(self):
        """При редактировании поста /edit/ изменяется соответствующая запись"""
        posts_count = Post.objects.count()
        post_old_text = Post.objects.get().text
        form_data = {
            "text": "Тестовый пост изменен",
            "author": self.user,
            "group": self.group.id,
        }

        response = self.authorized_client.post(
            reverse("posts:post_edit",
                    kwargs={"username": self.user,
                            "post_id": self.post.id}),
            data=form_data, follow=True,)
        self.assertNotEqual(response.context.get("post").text,
                            self.post.text)
        self.assertEqual(response.context.get("post").text,
                         form_data["text"])
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertNotEqual(post_old_text, Post.objects.get().text)
