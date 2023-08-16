from typing import List, Union, Tuple

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.http.response import HttpResponseBase
from django.db.models.query import QuerySet

from notes.models import Note
from notes.forms import NoteForm

User: AbstractBaseUser = get_user_model()


class TestContent(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first_user: AbstractBaseUser = User.objects.create(
            username='Первый'
        )
        cls.second_user: AbstractBaseUser = User.objects.create(
            username='Второй'
        )
        cls.first_user_client: Client = Client()
        cls.second_user_client: Client = Client()
        cls.first_user_client.force_login(cls.first_user)
        cls.second_user_client.force_login(cls.second_user)
        cls.first_user_note: Note = Note.objects.create(
            title='Заголовок первой заметки',
            text='Текст первой заметки',
            author=cls.first_user
        )
        cls.second_user_note: Note = Note.objects.create(
            title='Заголовок второй заметки',
            text='Текст второй заметки',
            author=cls.second_user
        )

    def test_note_in_context(self):
        url: str = reverse('notes:list')
        response: HttpResponseBase = self.first_user_client.get(url)
        notes_list: QuerySet[Note] = response.context['object_list']
        self.assertIn(
            self.first_user_note, notes_list,
            'Убедитесь, что заметка автора отображается ему на notes:list.'
        )
        self.assertNotIn(
            self.second_user_note,
            notes_list,
            ''.join(
                ('Убедитесь, что заметка другого пользователя ',
                 'не отображается другим пользователям.')
            )
        )

    def test_note_form_on_page(self):
        url_attrs: List[str, Union(Tuple[str])] = [
            ('notes:add', None),
            ('notes:edit', (self.first_user_note.slug,))
        ]
        for url_name, url_args in url_attrs:
            with self.subTest(url_name=url_name):
                url: str = reverse(url_name, args=url_args)
                response: HttpResponseBase = self.first_user_client.get(url)
                response_form: NoteForm = response.context['form']
                self.assertEqual(
                    isinstance(response_form, NoteForm),
                    True,
                    ''.join(
                        ('Убедитесь, что форма для создания заметки ',
                         f'отображается на {url_name}.')
                    )
                )
