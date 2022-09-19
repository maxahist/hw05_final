from django.test import TestCase

from ..models import Group, Post, User


class TestPostModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='заголовок',
            slug='слаг',
            description='описание'
        )
        cls.post = Post.objects.create(
            text='текст',
            author=cls.user
        )
        cls.post_len = Post.objects.create(
            text='a' * 20,
            author=cls.user
        )

    def test_verbose_name(self):
        """Проверяем 'человеческие названия' полей модели"""
        group = TestPostModel.group
        post = TestPostModel.post

        group_verboses = {
            'title': 'Заголовок',
            'description': 'Описание'
        }

        for field, value in group_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(group._meta.get_field(field).verbose_name,
                                 value)

        post_verboses = {
            'text': 'Текст',
            'pub_date': 'Дата',
            'author': 'Автор',
            'group': 'Жанр'
        }

        for field, value in post_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(post._meta.get_field(field).verbose_name,
                                 value)

    def test_str_display(self):
        """Проверяем работу __str__ метода в моделях"""
        group = TestPostModel.group
        post = TestPostModel.post
        expected_group = group.title
        expected_post = 'текст'
        self.assertEqual(expected_group, str(group))
        self.assertEqual(expected_post, str(post))
        self.assertEqual(str(TestPostModel.post_len),
                         TestPostModel.post_len.text[:15])
