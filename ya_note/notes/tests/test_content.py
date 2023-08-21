from typing import List, Tuple, Union

from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.http.response import HttpResponseBase
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestContent(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author: User = User.objects.create(
            username='Автор'
        )
        cls.another_user: User = User.objects.create(
            username='Пользователь'
        )
        cls.author_client: Client = Client()
        cls.another_user_client: Client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_user_client.force_login(cls.another_user)
        cls.author_note: Note = Note.objects.create(
            title='Заголовок заметки автора',
            text='Текст заметки автора',
            author=cls.author
        )

    def test_note_in_context(self):
        url: str = reverse('notes:list')
        for user_agent, user, error_msg, note_assert in [
            (self.author_client, self.author,
             'Убедитесь, что заметка автора отображается ему на notes:list.',
             self.assertIn),
            (self.another_user_client,
             self.another_user,
             ('Убедитесь, что заметка другого пользователя '
              'не отображается другим пользователям на notes:list.'),
             self.assertNotIn)
        ]:
            with self.subTest(
                user_agent=user_agent,
                user=user,
                error_msg=error_msg
            ):
                response: HttpResponseBase = user_agent.get(url)
                notes_list: QuerySet[Note] = response.context['object_list']
                note_assert(
                    self.author_note,
                    notes_list,
                    error_msg
                )

    def test_note_form_on_page(self):
        url_attrs: List[str, Union(Tuple[str])] = [
            ('notes:add', None),
            ('notes:edit', (self.author_note.slug,))
        ]
        for url_name, url_args in url_attrs:
            with self.subTest(url_name=url_name):
                url: str = reverse(url_name, args=url_args)
                response: HttpResponseBase = self.author_client.get(url)
                response_form: NoteForm = response.context['form']
                self.assertIsInstance(
                    response_form,
                    NoteForm,
                    ('Убедитесь, что форма для создания заметки '
                     f'отображается на {url_name}.')
                )
