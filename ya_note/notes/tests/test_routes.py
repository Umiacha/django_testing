from http import HTTPStatus
from typing import List

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
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

    def test_pages_availability_for_everyone(self):
        urls_for_everyone: List[str] = [
            reverse('notes:home'),
            reverse('users:login'),
            reverse('users:signup'),
            reverse('users:logout')
        ]
        urls_for_auth_users: List[str] = [
            reverse('notes:list'),
            reverse('notes:success'),
            reverse('notes:add'),
        ]
        urls_for_author: List[str] = [
            reverse('notes:detail', args=(self.note.slug,)),
            reverse('notes:edit', args=(self.note.slug,)),
            reverse('notes:delete', args=(self.note.slug,)),
        ]
        for user_agent, is_auth, is_author in (
            (self.anonim_client, False, False),
            (self.another_user_client, True, False),
            (self.author_client, True, True)
        ):
            for url in urls_for_auth_users:
                with self.subTest(url=url, client=user_agent):
                    response: HttpResponseBase = user_agent.get(url)
                    if is_auth:
                        self.assertEqual(
                            response.status_code,
                            HTTPStatus.OK,
                            ''.join(
                                (f'Убедитесь, что страница {url} ',
                                 'доступна авторизованному пользователю.')
                            )
                        )
                    else:
                        self.assertEqual(
                            response.status_code,
                            HTTPStatus.FOUND,
                            ''.join(
                                ('Убедитесь, что анонимный пользователь ',
                                 f'перенаправляется со страницы {url}.')
                            )
                        )
            for url in urls_for_author:
                with self.subTest(url=url, client=user_agent):
                    response: HttpResponseBase = user_agent.get(url)
                    if is_auth and is_author:
                        self.assertEqual(
                            response.status_code,
                            HTTPStatus.OK,
                            ''.join(
                                (f'Убедитесь, что страница {url} ',
                                 'доступна автору заметки.')
                            )
                        )
                    elif is_auth:
                        self.assertEqual(
                            response.status_code,
                            HTTPStatus.NOT_FOUND,
                            ''.join(
                                (f'Убедитесь, что страница {url} ',
                                 'недоступна не автору заметки.')
                            )
                        )
                    else:
                        self.assertEqual(
                            response.status_code,
                            HTTPStatus.FOUND,
                            ''.join(
                                ('Убедитесь, что анонимный пользователь ',
                                 f'перенаправляется со страницы {url}.')
                            )
                        )
            for url in urls_for_everyone:
                with self.subTest(url=url, client=user_agent):
                    response: HttpResponseBase = user_agent.get(url)
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.OK,
                        f'Убедитесь, что любому пользователю доступна {url}.'
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
