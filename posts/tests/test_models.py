from django.contrib.auth.models import User
from django.test import TestCase

from posts.models import Group, Post


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        user = User.objects.create_user(
            username="sergey",
        )

        cls.post = Post.objects.create(
            text="Тестовый текстnnnnnnnnnnnnnnnnnnnnnnn",
            author=user,
        )

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="testgroup",
            description="testdescription"
        )

    def test_field_values_post_text(self):
        """help_text и verbose_name в post_text совпадает с ожидаемым."""
        field_values = {
            "Напишите текст": self.post._meta.get_field("text").help_text,
            "Текст": self.post._meta.get_field("text").verbose_name,
        }
        for value, field in field_values.items():
            with self.subTest():
                self.assertEquals(field, value)

    def test_field_values_group_title(self):
        """help_text и verbose_name в group_title совпадает с ожидаемым."""
        field_values = {
            "Дайте краткий заголовок": self.group._meta.get_field("title").
            help_text,
            "Заголовок": self.group._meta.get_field("title").verbose_name,
        }
        for value, field in field_values.items():
            with self.subTest():
                self.assertEquals(field, value)

    def test_objects_name_is_title_field(self):
        """В поле __str__  объекта group записано значение поля group.title"""
        self.assertEquals(self.group.title, str(self.group))

    def test_object_name_is_text_field(self):
        """В поле __str__  объекта post записано значение поля post.text."""
        self.assertEquals(self.post.text[:15], str(self.post))
