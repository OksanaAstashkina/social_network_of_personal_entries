import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm, CommentForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create(username='TestAuthor')
        cls.user_auth = User.objects.create(username='TestAuth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Существующий пост',
            author=cls.user_author,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user_auth,
            post=cls.post
        )
        cls.form = PostForm()
        cls.form = CommentForm()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_auth)

    def test_post_create(self):
        """Проверка, что валидная форма создает новый пост в БД."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.post.author,
                group=self.group,
                image='posts/small.gif',
            ).exists()
        )

    def test_post_edit(self):
        """Проверка, что валидная форма редактирует существующий пост в БД."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small_2.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Отредактированный пост',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.post.author,
                group=self.group,
                image='posts/small_2.gif',
                pk=self.post.pk,
            ).exists()
        )

    def test_add_comment(self):
        """Проверка, что валидная форма создает комментарий к посту в БД."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=self.user_auth,
                post=self.post,
            ).exists()
        )
