import shutil
import tempfile
import time

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Comment, Follow, Group, Post


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Tester')
        cls.group = Group.objects.create(
            title='Тестовый Заголовок',
            slug='slug',
            description='Тестовое описание'
        )
        Post.objects.bulk_create(
            Post(text=f'text for post {i}', author=cls.user, id=i,
                 group=cls.group) for i in range(13)
        )
        Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.feed_user = User.objects.create_user(username='feed')
        self.feed_client = Client()
        self.feed_client.force_login(self.feed_user)

        Post.objects.create(
            author=self.user,
            text='Тестовый текст тт',
        )
        Post.objects.create(
            author=self.user,
            text='Тестовый текст второй'
        )
        cache.clear()

    def test_templates(self):
        """Проверяем соответсвие шаблонам"""
        templates = {
            reverse('posts:main'): 'posts/index.html',
            reverse('posts:blog', kwargs={'slug': 'slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'Tester'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': Post.objects.get(
                text='Тестовый текст').id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': Post.objects.get(
                text='Тестовый текст тт').id}):
                'posts/create_post.html'
        }

        for url, template in templates.items():
            with self.subTest(reverse_name=url):
                response = self.auth_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_create_post_context(self):
        """Проверяем соотвествие полей в форме при создание поста"""
        response = self.auth_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, form in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, form)

    def test_edit_post_context(self):
        """Проверяем соответсвие полей в форме при редактировании поста"""
        response = (self.auth_client.
                    get(reverse('posts:post_edit',
                                kwargs={'post_id': Post.objects.get(
                                    text='Тестовый текст тт').id})))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, form in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, form)

    def test_post_detail_context(self):
        """Проверяем соответствие полей на страние
        детальной информации поста"""
        response = (self.auth_client.
                    get(reverse('posts:post_detail',
                                kwargs={'post_id': Post.objects.get(
                                    text='Тестовый текст').id})))
        self.assertEqual(response.context.get('post').author.username,
                         'Tester')
        self.assertEqual(response.context.get('post').text,
                         'Тестовый текст')
        self.assertEqual(response.context.get('post').group.title,
                         'Тестовый Заголовок')

    def test_main_first_page(self):
        """Проверяем Paginator на первой странице main"""
        response = self.auth_client.get(reverse('posts:main'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_main_second_page(self):
        """Проверяем Paginator на второй странице main"""
        response = self.auth_client.get(reverse('posts:main') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 6)

    def test_group_first_page(self):
        """Проверяем Paginator на первой странице группы"""
        response = self.auth_client.get(reverse('posts:blog',
                                                kwargs={'slug': 'slug'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_second_page(self):
        """Проверяем Paginator на второй странице группы"""
        response = self.auth_client.get(reverse('posts:blog',
                                                kwargs={'slug': 'slug'})
                                        + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_profile_first_page(self):
        """Проверяем Paginator на первой странице профиля"""
        response = self.auth_client.get(reverse('posts:profile',
                                                kwargs={'username': 'Tester'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_second_page(self):
        """Проверяем Paginator на второй странице профиля"""
        response = self.auth_client.get(reverse('posts:profile',
                                                kwargs={'username': 'Tester'})
                                        + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_post_appear(self):
        """Проверяем появление поста на главной странице,
        на странице группы и на страницы пользователя"""
        post = Post.objects.latest('pub_date')
        response = self.auth_client.get(reverse('posts:main'))
        self.assertEqual(response.context['page_obj'][0].id, post.id)

        group = Group.objects.get(slug='slug')
        post = Post.objects.filter(group=group).latest('pub_date')
        response = self.auth_client.get(reverse('posts:blog',
                                                kwargs={'slug': 'slug'}))
        self.assertEqual(response.context['page_obj'][0].id, post.id)

        author = User.objects.get(username='auth')
        post = Post.objects.filter(author=author).latest('pub_date')
        response = self.auth_client.get(reverse('posts:profile',
                                                kwargs={'username': 'auth'}))
        self.assertEqual(response.context['page_obj'][0].id, post.id)

    def test_image_existence(self):
        """Првереям наличие фото в словаре контекста"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='image.gif',
            content=small_gif,
            content_type='image/gif'
        )

        post = Post.objects.create(
            author=ViewTest.user,
            group=ViewTest.group,
            text='Тест Изображения',
            image=uploaded
        )
        path_list = [reverse('posts:main'),
                     reverse('posts:profile',
                             kwargs={'username': ViewTest.user.username}),
                     reverse('posts:blog',
                             kwargs={'slug': ViewTest.group.slug})
                     ]

        for path in path_list:
            with self.subTest(reverse_name=path):
                response = self.auth_client.get(path)
                self.assertTrue(response.context['page_obj'][0].image)

        post_detail_path = reverse('posts:post_detail',
                                   kwargs={'post_id': post.id})
        response = self.auth_client.get(post_detail_path)
        self.assertTrue(response.context['post'].image)

    def test_comment_appear(self):
        """Проверка появления комментария на странице поста"""
        post = Post.objects.get(id=1)
        comment = Comment.objects.create(
            post=post,
            text='Комментарий',
            author=self.user,
        )
        response = self.auth_client.get(reverse('posts:post_detail',
                                                kwargs={'post_id': post.id}))
        self.assertEqual(response.context['post_comments'][0].text, comment.text)

    def test_index_cache(self):
        """Проверяем работу кэширования страницы"""
        Post.objects.create(
            author=self.user,
            text='кэш'
        )
        self.auth_client.get(reverse('posts:main'))
        Post.objects.get(text='кэш').delete()
        response = self.auth_client.get(reverse('posts:main'))
        self.assertIn('кэш', response.content.decode())
        cache.clear()
        response = self.auth_client.get(reverse('posts:main'))
        self.assertNotIn('кэш', response.content.decode())

    def test_following(self):
        """Проверяем работу подписки на / отписки от пользователя"""
        response = self.auth_client.get(reverse('posts:profile_follow',
                                                kwargs={'username': ViewTest.user}),
                                        follow=True)
        self.assertRedirects(response, reverse('posts:main'))
        self.assertTrue(Follow.objects.filter(user=self.user,
                                              author=ViewTest.user).exists())

        response = self.auth_client.get(reverse('posts:profile_unfollow',
                                                kwargs={'username': ViewTest.user}),
                                        follow=True)
        self.assertRedirects(response, reverse('posts:main'))
        self.assertFalse(Follow.objects.filter(user=self.user,
                                               author=ViewTest.user).exists())

    def test_following_feed(self):
        """Проверяем отображение поста в ленте подписок"""
        post = Post.objects.create(
            author=ViewTest.user,
            text='Лента подписок'
        )
        self.auth_client.get(reverse('posts:profile_follow',
                                     kwargs={'username': ViewTest.user}))
        response = self.auth_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'][0].id, post.id)

        response = self.feed_client.get(reverse('posts:follow_index'))
        self.assertFalse(response.context['page_obj'])
