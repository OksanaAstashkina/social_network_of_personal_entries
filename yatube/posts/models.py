from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField("Название группы", max_length=200)
    slug = models.SlugField(
        "Наименование группы в адресной строке",
        max_length=20,
        unique=True,
        db_index=True)
    description = models.TextField("Описание группы")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"


class Post(CreatedModel):
    text = models.TextField(
        "Текст поста",
        help_text="Введите текст поста"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор поста"
    )
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
        verbose_name="Группа",
        help_text="Группа, к которой будет относиться пост"
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.text[:settings.LENGH_OF_TEXT]


class Comment(CreatedModel):
    text = models.TextField(
        "Текст комментария",
        help_text="Введите комментарий к посту"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор комментария"
    )
    post = models.ForeignKey(
        'Post',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Пост",
        help_text="Пост, к которому будет относиться комментарий"
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text[:settings.LENGH_OF_TEXT]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор"
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_follow_user_author"
            ),
            models.CheckConstraint(
                name="user_is_same_as_author",
                check=~models.Q(user=models.F("author")),
            ),
        ]
