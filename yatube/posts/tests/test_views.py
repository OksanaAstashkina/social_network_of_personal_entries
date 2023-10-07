import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Comment, Follow, Post, Group, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user_author = User.objects.create(username='TestAuthor')
        cls.user_auth = User.objects.create(username='TestAuth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание группы'
        )
        Post.objects.bulk_create([
            Post(
                text='Тестовый пост',
                author=cls.user_author,
                group=cls.group,
                image=cls.uploaded
            )
            for _ in range(settings.NUMBER_OF_TEST_POSTS)
        ])
        cls.post = Post.objects.first()
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user_auth,
            post=cls.post)
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-group-2',
            description='Тестовое описание группы 2'
        )
        cls.reverse_index = reverse('posts:index')
        cls.reverse_group_list = reverse(
            'posts:group_list', kwargs={'slug': cls.group.slug})
        cls.reverse_profile = reverse(
            'posts:profile', kwargs={'username': cls.user_author.username})
        cls.reverse_post_detail = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.pk})
        cls.reverse_post_create = reverse('posts:post_create')
        cls.reverse_post_edit = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.pk})
        cls.reverse_add_comment = reverse(
            'posts:add_comment', kwargs={'post_id': cls.post.pk})
        cls.reverse_follow_index = reverse('posts:follow_index')
        cls.reverse_profile_follow = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.user_author.username}
        )
        cls.reverse_profile_unfollow = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.user_author.username}
        )

        cls.templates_pages_names = {
            cls.reverse_index: 'posts/index.html',
            cls.reverse_group_list: 'posts/group_list.html',
            cls.reverse_profile: 'posts/profile.html',
            cls.reverse_post_detail: 'posts/post_detail.html',
            cls.reverse_post_create: 'posts/create_post.html',
            cls.reverse_post_edit: 'posts/create_post.html',
            cls.reverse_follow_index: 'posts/follow.html'
        }

        cls.author_client = Client()
        cls.author_client.force_login(cls.user_author)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_auth)

        cls.response_index = cls.author_client.get(cls.reverse_index)
        cls.response_group_list = cls.author_client.get(cls.reverse_group_list)
        cls.response_profile = cls.author_client.get(cls.reverse_profile)
        cls.response_post_detail = cls.author_client.get(
            cls.reverse_post_detail)
        cls.response_post_create = cls.author_client.get(
            cls.reverse_post_create)
        cls.response_post_edit = cls.author_client.get(cls.reverse_post_edit)

        cls.responce_list = [
            cls.response_index,
            cls.response_group_list,
            cls.response_profile
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """Проверяем, использует ли URL-адрес соответствующий шаблон."""
        for reverse_page, template_page in self.templates_pages_names.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.author_client.get(reverse_page)
                self.assertTemplateUsed(response, template_page)

    def test_post_create_page_show_correct_context(self):
        """Проверяем,что шаблоны страниц с формой
         сформированы с правильным контекстом."""
        form_fields = {
            ('text', forms.fields.CharField, self.response_post_create),
            ('text', forms.fields.CharField, self.response_post_edit),
            ('group', forms.fields.ChoiceField, self.response_post_create),
            ('group', forms.fields.ChoiceField, self.response_post_edit),
            ('image', forms.fields.ImageField, self.response_post_create),
            ('image', forms.fields.ImageField, self.response_post_edit)
        }
        for value, expected, response in form_fields:
            with self.subTest(value=value, response=response):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_pages_show_correct_context(self):
        """Проверяем,что шаблон страницы с единственным постом (post_detail)
         сформирован с правильным контекстом."""
        get_post = self.response_post_detail.context.get('post')
        post_detail_params = {
            get_post.text: self.post.text,
            get_post.author.username: self.user_author.username,
            get_post.group.title: self.group.title,
            get_post.group.slug: self.group.slug,
            get_post.group.description: self.group.description,
            get_post.image: self.post.image
        }
        for get_param, self_param in post_detail_params.items():
            with self.subTest(get_param=get_param, self_param=self_param):
                self.assertEqual(get_param, self_param)

    def test_multiple_post_page_show_correct_context(self):
        """Проверяем,что шаблоны страниц с множеством постов
         сформированы с правильным контекстом."""
        for response in self.responce_list:
            with self.subTest(response=response):
                first_object = response.context['page_obj'][0]
                post_text_0 = first_object.text
                post_author_username_0 = first_object.author.username
                post_group_title_0 = first_object.group.title
                post_group_slug_0 = first_object.group.slug
                post_group_description_0 = first_object.group.description
                post_image_0 = first_object.image
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_author_username_0,
                                 self.user_author.username)
                self.assertEqual(post_group_title_0, self.group.title)
                self.assertEqual(post_group_slug_0, self.group.slug)
                self.assertEqual(post_group_description_0,
                                 self.group.description)
                self.assertEqual(post_image_0, self.post.image)

    def test_first_page_contains_ten_records(self):
        """Проверяем, что количество постов на первой странице равно 10."""
        for response in self.responce_list:
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_ON_PAGE
                )

    def test_second_page_contains_five_records(self):
        """Проверяем, что количество постов на второй странице равно 5."""
        response_index_page_2 = self.author_client.get(
            self.reverse_index + '?page=2')
        response_group_list_page_2 = self.author_client.get(
            self.reverse_group_list + '?page=2')
        response_profile_page_2 = self.author_client.get(
            self.reverse_profile + '?page=2')
        responce_list = [
            response_index_page_2,
            response_group_list_page_2,
            response_profile_page_2,
        ]
        for response in responce_list:
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']),
                    (settings.POSTS_ON_PAGE_2_TEST)
                )

    def test_post_added_on_pages_correctly(self):
        """Проверяем, что при создании поста он попадает на
         требуемые страницы."""
        for response in self.responce_list:
            with self.subTest(response=response):
                self.assertIn(self.post, response.context['page_obj'])

    def test_post_not_added_on_page_another_group(self):
        """Проверяем, что при создании поста он не попадает на
         страницу группы, к которой не принадлежит."""
        response_group_list_group_2 = self.author_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_2.slug}
            )
        )
        self.assertNotIn(
            self.post, response_group_list_group_2.context['page_obj']
        )

    def test_comment_added_on_post_page_correctly(self):
        """Проверяем, что после успешной отправки комментарий появляется
         на странице поста."""
        response = self.authorized_client.get(self.reverse_post_detail)
        self.assertIn(self.comment, response.context['comments'])

    def test_post_added_to_feed_of_subscribers(self):
        """Проверяем, что новая запись автора появляется в ленте тех,
         кто на него подписан."""
        Follow.objects.create(user=self.user_auth, author=self.user_author)
        post_new = Post.objects.create(text='Новый пост',
                                       author=self.user_author)
        response_feed_of_subscriber = self.authorized_client.get(
            self.reverse_follow_index
        )
        self.assertIn(
            post_new, response_feed_of_subscriber.context['page_obj']
        )

    def test_post_not_added_to_feed_of_not_subscribers(self):
        """Проверяем, что новая запись автора не появляется в ленте тех,
         кто на него не подписан."""
        user = User.objects.create(username='TestAuth_2')
        authorized_2_client = Client()
        authorized_2_client.force_login(user)
        post_new = Post.objects.create(text='Новый пост',
                                       author=self.user_author)
        response_feed_of_subscriber = authorized_2_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(
            post_new, response_feed_of_subscriber.context['page_obj']
        )

    def test_authorized_user_subscribes_to_author(self):
        """Проверка, что авторизованный пользователь может подписываться
         на других пользователей."""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_author.username}
            )
        )
        follower = Follow.objects.filter(
            user=self.user_auth, author=self.user_author).exists()
        self.assertTrue(follower)

    def test_authorized_user_unsubscribes_from_author(self):
        """Проверка, что авторизованный пользователь может удалять
         авторов из подписок."""
        Follow.objects.create(user=self.user_auth, author=self.user_author)
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_author.username}
            )
        )
        follower = Follow.objects.filter(
            user=self.user_auth, author=self.user_author).exists()
        self.assertFalse(follower)
