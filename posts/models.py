from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        "Заголовок",
        max_length=200,
        help_text="Дайте краткий заголовок"
    )
    slug = models.SlugField(
        unique=True
    )
    description = models.TextField()

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        "Текст",
        help_text="Напишите текст",
    )

    pub_date = models.DateTimeField(
        "Дата публикации",
        auto_now_add=True,
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
        help_text="Ссылка на автора",
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
        verbose_name="Группа",
        help_text="Выбор группы",
    )

    image = models.ImageField(
        upload_to="posts/",
        blank=True,
        null=True,
        verbose_name="Изображение"
    )

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    text = models.TextField(
        "Комментарий",
        help_text="Напишите комменарий"
    )

    created = models.DateTimeField(
        "Дата комментирования",
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created"]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower")

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following")
