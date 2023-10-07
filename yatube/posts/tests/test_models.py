from django.conf import settings
from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    def test_models_have_correct_object_names(self):
        """Проверка, что метод __str__ выводит ожидаемое значение."""
        object_name = {
            str(self.post): self.post.text[:settings.LENGH_OF_TEXT],
            str(self.group): self.group.title
        }
        for field, expected_value in object_name.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)

    def test_models_verbose_name(self):
        """Проверка, что verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст поста',
            'created': 'Дата публикации',
            'author': 'Автор поста',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_models_help_text(self):
        """Проверка, что help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value)
