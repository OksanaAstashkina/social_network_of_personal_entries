from http import HTTPStatus

from django.test import TestCase, Client

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='TestAuthor')
        cls.user_auth = User.objects.create_user(username='TestAuth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user_author,
            group=cls.group,
        )
        cls.index = '/'
        cls.group_list = f'/group/{cls.group.slug}/'
        cls.profile = f'/profile/{cls.post.author.username}/'
        cls.post_detail = f'/posts/{cls.post.pk}/'
        cls.post_create = '/create/'
        cls.post_edit = f'/posts/{cls.post.pk}/edit/'
        cls.add_comment = f'/posts/{cls.post.pk}/comment/'
        cls.follow_index = '/follow/'
        cls.profile_follow = f'profile/{cls.post.author.username}/follow/'
        cls.profile_unfollow = f'profile/{cls.post.author.username}/unfollow/'

        cls.PUBLIC_URLS = {
            cls.index: ('posts/index.html', HTTPStatus.OK),
            cls.group_list: ('posts/group_list.html', HTTPStatus.OK),
            cls.profile: ('posts/profile.html', HTTPStatus.OK),
            cls.post_detail: ('posts/post_detail.html', HTTPStatus.OK)
        }
        cls.ADDITIONAL_URL_FOR_AUTHORIZED_USERS = {
            cls.post_create: ('posts/create_post.html', HTTPStatus.OK),
            cls.follow_index: ('posts/follow.html', HTTPStatus.OK)
        }
        cls.ADDITIONAL_URL_FOR_AUTHOR = {
            cls.post_edit: ('posts/create_post.html', HTTPStatus.OK)
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_auth)
        self.author_client = Client()
        self.author_client.force_login(self.user_author)

    def test_guest_urls_uses_correct_template(self):
        """Проверка использования URL-адресов соответствующих шаблонов
         и HTTP-статусов для неавторизованного пользователя."""
        for address, (template, status) in self.PUBLIC_URLS.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, status)

    def test_authorized_urls_uses_correct_template(self):
        """Проверка использования URL-адресов соответствующих шаблонов
         и HTTP-статусов для авторизованного пользователя."""
        for address, (template, status) in (
            self.ADDITIONAL_URL_FOR_AUTHORIZED_USERS.items()
        ):
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, status)

    def test_author_urls_uses_correct_template(self):
        """Проверка использования URL-адресов соответствующих шаблонов
         и HTTP-статусов для автора поста."""
        for address, (template, status) in (
            self.ADDITIONAL_URL_FOR_AUTHOR.items()
        ):
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, status)

    def test_post_create_url_redirect_anonymous_on_auth_login(self):
        """Проверка, что страницы по адресу /create/,
         /posts/<int:post_id>/edit/ и /posts/<int:post_id>/comment/
         перенаправят анонимного пользователя на страницу логина.'"""
        guest_redirects = {
            self.post_create: '/auth/login/?next=/create/',
            self.post_edit:
            f'/auth/login/?next=/posts/{self.post.pk}/edit/',
            self.add_comment:
            f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        }
        for address, redirect_address in guest_redirects.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)

    def test_post_edit_url_redirect_authorized_on_post_detail(self):
        """Проверка, что страница по адресу /posts/<int:post_id>/edit/
         перенаправит авторизованного пользователя (не автора поста)
         на страницу поста."""
        response = self.authorized_client.get(
            self.post_edit,
            follow=True
        )
        self.assertRedirects(response, self.post_detail)

    def test_not_auth_url_exists_at_desired_location(self):
        """Проверка несуществующей страницы."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
