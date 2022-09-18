from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовый Заголовок',
            slug='slug',
            description='Тестовое описание'
        )
        cls.group_change = Group.objects.create(
            title='Измененный Заголовок',
            slug='changed_slug',
            description='Измененное описание'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        Post.objects.create(
            author=self.user,
            text='Тестовый'
        )
        cache.clear()

    def test_create_form(self):
        """ Проверяем создание поста авторизованым пользователем,
        отображение поста в базе данных, перенаправление на другую
        страницу после создания"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': CreateFormTest.group.id
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': 'auth'}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.latest(
            'pub_date').text == 'Тестовый текст')

    def test_guest_client_create_form(self):
        """Проверяем создание поста неавторизованым пользователем"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': CreateFormTest.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             f'{reverse("users:login")}?next='
                             f'{reverse("posts:post_create")}')
        self.assertEqual(Post.objects.count(), post_count)

    def test_post_edit_form(self):
        """ Проверяем редактирование поста авторизованым пользователем,
        отображение изменений в посте, перенаправление на другую
        страницу после редактирования"""
        post_count = Post.objects.count()
        group_new = Group.objects.get(slug='changed_slug')
        group_count = Post.objects.filter(group=group_new).count()
        form_data = {
            'text': 'Абракадабра',
            'group': CreateFormTest.group_change.id
        }
        post = Post.objects.get(text='Тестовый')
        post_id = post.id
        response = self.auth_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': post_id}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text='Абракадабра'
            ).exists()
        )
        self.assertTrue(
            Post.objects.filter(
                group=CreateFormTest.group_change.id
            ).exists()
        )
        self.assertEqual(group_count + 1, Post.objects.filter(
            group=group_new).count())

    def test_guest_client_edit_post(self):
        """Проверяем редактирование поста неавторизованым пользователем"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'not'
        }
        post = Post.objects.get(text='Тестовый')
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        path = reverse("posts:post_edit", kwargs={"post_id": post.id})
        self.assertRedirects(response,
                             f'{reverse("users:login")}?next={path}')

        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text='not'
            ).exists()
        )

    def test_creation_post_with_image(self):
        """Проверяем создание поста с картинкой через форму"""
        post_count = Post.objects.count()
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

        form = {
            'text': 'Тест Изображения',
            'image': uploaded,
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form,
            follow=True)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(Post.objects.latest('pub_date').image,
                         'posts/image.gif')

    def test_guest_client_comment(self):
        """Проверка создания комментария неавторизованым пользователем"""
        comment_count = Comment.objects.count()
        self.guest_client.post(reverse('posts:add_comment',
                                       kwargs={'post_id': 1}),
                               data={'text': 'Гостевой коммент'},
                               follow=True)
        self.assertEqual(Comment.objects.count(), comment_count)
