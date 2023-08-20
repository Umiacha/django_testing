from http import HTTPStatus
from typing import List, Tuple

from django.contrib.auth import get_user_model
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
        urls_and_codes: List[Tuple(str, int, int, int)] = [
            (reverse('notes:detail', args=(self.note.slug,)),
             HTTPStatus.FOUND, HTTPStatus.NOT_FOUND, HTTPStatus.OK),
            (reverse('notes:edit', args=(self.note.slug,)),
             HTTPStatus.FOUND, HTTPStatus.NOT_FOUND, HTTPStatus.OK),
            (reverse('notes:delete', args=(self.note.slug,)),
             HTTPStatus.FOUND, HTTPStatus.NOT_FOUND, HTTPStatus.OK),
            (reverse('notes:list'),
             HTTPStatus.FOUND, HTTPStatus.OK, HTTPStatus.OK),
            (reverse('notes:success'),
             HTTPStatus.FOUND, HTTPStatus.OK, HTTPStatus.OK),
            (reverse('notes:add'),
             HTTPStatus.FOUND, HTTPStatus.OK, HTTPStatus.OK),
            (reverse('notes:home'),
             HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
            (reverse('users:login'),
             HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
            (reverse('users:signup'),
             HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
            (reverse('users:logout'),
             HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
        ]
        for url, anonim_code, auth_code, author_code in urls_and_codes:
            with self.subTest(
                url=url,
                anonim_code=anonim_code,
                auth_code=auth_code,
                author_code=author_code
            ):
                anonim_response: HttpResponseBase = self.anonim_client.get(url)
                self.assertEqual(
                    anonim_response.status_code,
                    anonim_code,
                    ''.join(
                        ('Убедитесь, что анонимный пользователь ',
                         f'при переходе на {url} получает ',
                         f'код ответа {anonim_code}')
                    )
                )
                auth_response: HttpResponseBase = (
                    self.another_user_client.get(url)
                )
                self.assertEqual(
                    auth_response.status_code,
                    auth_code,
                    ''.join(
                        ('Убедитесь, что авторизованный пользователь ',
                         f'при переходе на {url} получает ',
                         f'код ответа {auth_code}')
                    )
                )
                author_response: HttpResponseBase = self.author_client.get(url)
                self.assertEqual(
                    author_response.status_code,
                    author_code,
                    ''.join(
                        ('Убедитесь, что пользователь-автор ',
                         f'при переходе на {url} получает ',
                         f'код ответа {author_code}')
                    )
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
                    msg_prefix=''.join(
                        (f'Убедитесь, что {url_name} ',
                         'недоступна анонимному пользователя.')
                    )
                )
