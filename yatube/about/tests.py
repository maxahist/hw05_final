from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url(self):
        """Проверяем доступ на страницы для всех пользователей"""
        path_list = [reverse('about:author'), reverse('about:tech')]
        for path in path_list:
            with self.subTest(reverse_name=path):
                response = self.guest_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_template(self):
        """Проверяем соответствие url-запросов и html-шаблонов"""
        templates = {reverse('about:author'): 'about/author.html',
                     reverse('about:tech'): 'about/tech.html'}

        for url, template in templates.items():
            with self.subTest(reverse_name=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
