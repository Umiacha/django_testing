from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first_user = User.objects.create(username='Первый')
        cls.second_user = User.objects.create(username='Второй')
        cls.first_user_client = Client()
        cls.second_user_client = Client()
        cls.first_user_client.force_login(cls.first_user)
        cls.second_user_client.force_login(cls.second_user)
        cls.first_user_note = Note.objects.create(
            title='Заголовок первой заметки',
            text='Текст первой заметки',
            author=cls.first_user
        )
        cls.second_user_note = Note.objects.create(
            title='Заголовок второй заметки',
            text='Текст второй заметки',
            author=cls.second_user
        )
    
    
    def test_note_in_context(self):
        url = reverse('notes:list')
        response = self.first_user_client.get(url)
        notes_list = response.context['object_list']
        self.assertIn(self.first_user_note, notes_list)
        self.assertNotIn(self.second_user_note, notes_list)
    
    
    def test_note_form_on_page(self):
        url_attrs = [
            ('notes:add', None),
            ('notes:edit', (self.first_user_note.slug,))
        ]
        for url_name, url_args in url_attrs:
            with self.subTest(url_name=url_name):
                url = reverse(url_name, args=url_args)
                response = self.first_user_client.get(url)
                response_form = response.context['form']
                self.assertEqual(isinstance(response_form, NoteForm), True)
