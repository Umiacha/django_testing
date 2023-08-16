from http import HTTPStatus
from typing import List

from django.test import TestCase, Client

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.http.response import HttpResponseBase

from notes.models import Note

User: AbstractBaseUser = get_user_model()


class TestRoutes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.anonim_client: Client = Client()
        cls.author_client: Client = Client()
        cls.another_user_client: Client = Client()
        author: AbstractBaseUser = User.objects.create(
            username='Автор'
        )
        another_user: AbstractBaseUser = User.objects.create(
            username='Пользователь'
        )
        cls.author_client.force_login(author)
        cls.another_user_client.force_login(another_user)
        cls.note: Note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=author
        )

    def test_pages_availability(self):
        url_names: List[str] = [
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup'
        ]
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                url: str = reverse(url_name)
                response: HttpResponseBase = self.anonim_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    ''.join(
                        (f'Убедитесь, что страница {url_name} ',
                         'доступна анонимному пользователю.')
                    )
                )

    def test_anoninum_cant_success_note_urls(self):
        url_names: List[str] = [
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        ]
        for url_name, args_for_url in url_names:
            with self.subTest(url_name=url_name, args_for_url=args_for_url):
                url: str = reverse(url_name, args=args_for_url)
                expected_url: str = reverse('users:login') + f'?next={url}'
                response: HttpResponseBase = self.anonim_client.get(url)
                self.assertRedirects(
                    response=response,
                    expected_url=expected_url,
                    msg_prefix=''.join(
                        (f'Убедитесь, что {url_name} ',
                         'недоступна анонимному пользователя.')
                    )
                )

    def test_auth_user_can_success_url_notes(self):
        url_names: List[str] = [
            'notes:list',
            'notes:success',
            'notes:add',
        ]
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                url: str = reverse(url_name)
                response: HttpResponseBase = self.another_user_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    ''.join(
                        (f'Убедитесь, что страница {url_name} ',
                         'доступна авторизованному пользователю.')
                    )
                )

    def test_only_author_can_success_note(self):
        url_names: List[str] = [
            'notes:detail',
            'notes:edit',
            'notes:delete',
        ]
        NOTE_SLUG: str = self.note.slug
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                url: str = reverse(url_name, args=(NOTE_SLUG,))
                author_response: HttpResponseBase = self.author_client.get(url)
                self.assertEqual(
                    author_response.status_code,
                    HTTPStatus.OK,
                    ''.join(
                        (f'Убедитесь, что страница {url_name} ',
                         'доступна автору заметки.')
                    )
                )
                another_user_response = self.another_user_client.get(url)
                self.assertEqual(
                    another_user_response.status_code,
                    HTTPStatus.NOT_FOUND,
                    ''.join(
                        (f'Убедитесь, что страница {url_name} ',
                         'недоступна не автору заметки.')
                    )
                )
