from http import HTTPStatus

from django.test import TestCase

from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.anonim_client = Client()
        cls.author_client = Client()
        cls.another_user_client = Client()
        author = User.objects.create(username='Автор')
        another_user = User.objects.create(username='Пользователь')
        cls.author_client.force_login(author)
        cls.another_user_client.force_login(another_user)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=author
        )
    
    
    def test_pages_availability(self):
        url_names = [
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup'
        ]
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                url = reverse(url_name)
                response = self.anonim_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
    
    
    def test_anoninum_cant_success_note_urls(self):
        url_names = [
            ('notes:list', None, 'notes'),
            ('notes:add', None, 'add'),
            ('notes:success', None, 'done'),
            ('notes:detail', (self.note.slug,), 'detail'),
            ('notes:edit', (self.note.slug,), 'edit'),
            ('notes:delete', (self.note.slug,), 'delete'),
        ]
        for url_name, args_for_url, redirect in url_names:
            with self.subTest(url_name=url_name, args_for_url=args_for_url, redirect=redirect):
                url = reverse(url_name, args=args_for_url)
                expected_url = reverse('users:login') + f'?next={url}'
                response = self.anonim_client.get(url)
                self.assertRedirects(response=response, expected_url=expected_url)
    
    
    def test_auth_user_can_success_url_notes(self):
        url_names = [
            'notes:list',
            'notes:success',
            'notes:add',
        ]
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                url = reverse(url_name)
                response = self.another_user_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
    
    
    def test_only_author_can_success_note(self):
        url_names = [
            'notes:detail',
            'notes:edit',
            'notes:delete',
        ]
        NOTE_SLUG = self.note.slug
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                url = reverse(url_name, args=(NOTE_SLUG,))
                author_response = self.author_client.get(url)
                self.assertEqual(author_response.status_code, HTTPStatus.OK)
                another_user_response = self.another_user_client.get(url)
                self.assertEqual(another_user_response.status_code, HTTPStatus.NOT_FOUND)
