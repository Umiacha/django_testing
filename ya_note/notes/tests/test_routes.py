from http import HTTPStatus
from typing import List, Tuple

from django.contrib.auth import get_user, get_user_model
from django.http.response import HttpResponseBase
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.anonim_client: Client = Client()
        cls.author_client: Client = Client()
        cls.another_user_client: Client = Client()
        author: User = User.objects.create(
            username='Автор'
        )
        another_user: User = User.objects.create(
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
        urls_clients_codes: List[Tuple[str, Tuple[Client, int]]] = [
            (reverse('notes:detail', args=(self.note.slug,)),
             (self.anonim_client, HTTPStatus.FOUND),
             (self.another_user_client, HTTPStatus.NOT_FOUND),
             (self.author_client, HTTPStatus.OK)),
            (reverse('notes:edit', args=(self.note.slug,)),
             (self.anonim_client, HTTPStatus.FOUND),
             (self.another_user_client, HTTPStatus.NOT_FOUND),
             (self.author_client, HTTPStatus.OK)),
            (reverse('notes:delete', args=(self.note.slug,)),
             (self.anonim_client, HTTPStatus.FOUND),
             (self.another_user_client, HTTPStatus.NOT_FOUND),
             (self.author_client, HTTPStatus.OK)),
            (reverse('notes:list'),
             (self.anonim_client, HTTPStatus.FOUND),
             (self.another_user_client, HTTPStatus.OK)),
            (reverse('notes:success'),
             (self.anonim_client, HTTPStatus.FOUND),
             (self.another_user_client, HTTPStatus.OK)),
            (reverse('notes:add'),
             (self.anonim_client, HTTPStatus.FOUND),
             (self.another_user_client, HTTPStatus.OK)),
            (reverse('notes:home'),
             (self.anonim_client, HTTPStatus.OK)),
            (reverse('users:login'),
             (self.anonim_client, HTTPStatus.OK)),
            (reverse('users:signup'),
             (self.anonim_client, HTTPStatus.OK)),
            (reverse('users:logout'),
             (self.anonim_client, HTTPStatus.OK)),
        ]
        for url, *clients_and_codes in urls_clients_codes:
            with self.subTest(
                url=url,
                clients_and_codes=clients_and_codes
            ):
                for user_client, expected_code in clients_and_codes:
                    response: HttpResponseBase = user_client.get(url)
                    self.assertEqual(
                        response.status_code,
                        expected_code,
                        (f'Убедитесь, что {get_user(user_client)} '
                         f'имеет доступ к {url}.')
                    )

    def test_anoninum_redirects_from_note_urls(self):
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
                    msg_prefix=(
                        f'Убедитесь, что {url_name} '
                        'недоступна анонимному пользователя.'
                    )
                )
