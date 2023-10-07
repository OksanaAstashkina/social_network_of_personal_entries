from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from posts.models import Post, User


class PostCacheTests(TestCase):
    def test_cache_index(self):
        user = User.objects.create(username='TestAuthor')
        Post.objects.create(text='Тестовый пост', author=user)
        response_1 = self.client.get(reverse('posts:index'))
        Post.objects.all().delete()
        response_2 = self.client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response_1.content, response_3.content)
