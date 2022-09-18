from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        Group.objects.create(
            title='test_group',
            slug='slug',
            description='description'
        )
        Post.objects.create(
            author=cls.user,
            text='Текстт',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Tester')
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        Post.objects.create(
            author=self.user,
            text='Текст',
        )

    def test_guest_access(self):
        """Проверяем доступ к страницам, неавторизованому пользователю"""
        path_list = [reverse('posts:post_detail',
                             kwargs={'post_id': Post.objects.get(
                                 text='Текст').id}),
                     reverse('posts:profile', kwargs={'username': 'Tester'}),
                     reverse('posts:blog', kwargs={'slug': 'slug'})]

        for path in path_list:
            with self.subTest(reverse_name=path):
                response = self.guest_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_redirect(self):
        """Проверяем переадресацию неавторизованого пользователя"""
        path_list = [reverse('posts:post_edit',
                             kwargs={'post_id': Post.objects.get(
                                 text='Текст').id}),
                     reverse('posts:post_create')]
        for path in path_list:
            with self.subTest(reversed_name=path):
                response = self.guest_client.get(path, follow=True)
                self.assertRedirects(response, f'{reverse("users:login")}'
                                               f'?next={path}')

    def test_unexisting_page(self):
        """Проверяем доступ на несуществующую страницу"""
        response = self.guest_client.get('/unexisting/page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_and_create(self):
        """Проверяем доступ авторизованого пользователя на страницы создания
        и редактирования поста"""
        path_list = [reverse('posts:post_create'),
                     reverse('posts:post_edit',
                             kwargs={'post_id': Post.objects.get(
                                 text='Текст').id})]
        for path in path_list:
            with self.subTest(reversed_name=path):
                response = self.auth_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_templates(self):
        """Проверяем соответствие шаблонов и url-адресов"""
        templates = {
            reverse('posts:main'): 'posts/index.html',
            reverse('posts:blog',
                    kwargs={'slug': 'slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'auth'}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': Post.objects.get(
                text='Текст').id}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': Post.objects.get(
                text='Текст').id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }

        for url, template in templates.items():
            with self.subTest(reversed_name=url):
                response = self.auth_client.get(url)
                self.assertTemplateUsed(response, template)
