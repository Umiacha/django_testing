from typing import Dict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.forms.models import model_to_dict
from django.http.response import HttpResponseBase
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()
SLUG_MAX_LENGTH: int = Note._meta.get_field('slug').max_length


class TestLogic(TestCase):
    NOTE_DATA: Dict[str, str] = {
        'title': 'Заголовок',
        'text': 'Текст',
    }

    @classmethod
    def setUpTestData(cls):
        cls.anonim_client: Client = Client()
        cls.author_client: Client = Client()
        cls.another_user_client: Client = Client()
        cls.author: AbstractBaseUser = User.objects.create(
            username='Автор'
        )
        cls.another_user: AbstractBaseUser = User.objects.create(
            username='Пользователь'
        )
        cls.author_client.force_login(cls.author)
        cls.another_user_client.force_login(cls.another_user)
        cls.author_note: Note = Note.objects.create(
            title='Заметка автора',
            text='Авторский текст',
            author=cls.author
        )
        cls.another_user_note: Note = Note.objects.create(
            title='Заметка пользователя',
            text='Текст заметки пользователя',
            author=cls.another_user
        )

    def test_auth_user_can_create_note(self):
        url: str = reverse('notes:add')
        NOTES_IN_DB = Note.objects.count()
        author_response: HttpResponseBase = self.author_client.post(
            url, data=self.NOTE_DATA
        )
        self.assertRedirects(
            author_response,
            reverse('notes:success'),
            msg_prefix=''.join(
                ('Убедитесь, что после создания заметки ',
                 'автор перенаправляется на notes:success.')
            )
        )
        self.assertEqual(
            Note.objects.count(),
            NOTES_IN_DB + 1,
            'Убедитесь, что созданная пользователем заметка сохраняется.'
        )
        self.assertEqual(
            model_to_dict(Note.objects.last(), fields=self.NOTE_DATA.keys()),
            self.NOTE_DATA,
            ''.join(
                ('Убедитесь, что поля заголовка и текста созданной заметки ',
                 'совпадают с отправленными в форме.')
            )
        )

    def test_anonim_cant_create_note(self):
        url: str = reverse('notes:add')
        NOTES_IN_DB = Note.objects.count()
        anonim_response: HttpResponseBase = self.anonim_client.post(
            url, data=self.NOTE_DATA
        )
        self.assertRedirects(
            anonim_response,
            reverse('users:login') + '?next=/add/',
            msg_prefix=''.join(
                ('Убедитесь, что анонимный пользователь при попытке ',
                 'создать заметку перенаправляется на страницу авторизации.')
            )
        )
        self.assertEqual(
            Note.objects.count(),
            NOTES_IN_DB,
            ''.join(
                ('Убедитесь, что отправленная ',
                 'анонимным пользователем заметка не сохраняется.')
            )
        )

    def test_note_has_unique_slug(self):
        url: str = reverse('notes:add')
        Note.objects.create(
            author=self.author,
            **self.NOTE_DATA
        )
        NOTES_IN_DB = Note.objects.count()
        first_note: Note = Note.objects.first()
        expected_error: str = first_note.slug + WARNING
        second_note_response: HttpResponseBase = self.author_client.post(
            url, data=model_to_dict(first_note)
        )
        self.assertFormError(
            second_note_response,
            'form',
            'slug',
            expected_error,
            ''.join(
                ('Убедитесь, что при попытке создать пост ',
                 'с существующим slug, форма возвращается ошибку.')
            )
        )
        self.assertEqual(
            Note.objects.count(),
            NOTES_IN_DB,
            'Убедитесь, что заметка с уже существующим slug не сохраняется.'
        )

    def test_create_slug_if_not_stated(self):
        url: str = reverse('notes:add')
        self.author_client.post(url, data=self.NOTE_DATA)
        result_slug: Note = Note.objects.last().slug
        expected_slug: str = slugify(self.NOTE_DATA['title'])[:SLUG_MAX_LENGTH]
        self.assertEqual(
            result_slug,
            expected_slug,
            ''.join(
                ('Убедитесь, что при создании заметки без указания slug ',
                 'последний формируется автоматически ',
                 'при помощи pytils.slugify.')
            )
        )

    def test_author_can_update_note(self):
        editing_url: str = reverse('notes:edit', args=(self.author_note.slug,))
        updating_note_id: int = self.author_note.id
        response: HttpResponseBase = self.author_client.post(
            editing_url, data=self.NOTE_DATA
        )
        self.assertRedirects(
            response,
            expected_url=reverse('notes:success'),
            msg_prefix=''.join(
                ('Убедитесь, что после редактирования заметки ',
                 'автор перенаправляется на notes:success.')
            )
        )
        self.assertEqual(
            model_to_dict(
                Note.objects.get(pk=updating_note_id),
                fields=self.NOTE_DATA.keys()
            ),
            self.NOTE_DATA,
            ''.join(
                ('Убедитесь, что поля записи обновляются ',
                 'после редактирования автором.')
            )
        )
        deleting_url: str = reverse(
            'notes:delete', args=(Note.objects.get(pk=updating_note_id).slug,)
        )
        response: HttpResponseBase = self.author_client.post(deleting_url)
        self.assertRedirects(
            response,
            expected_url=reverse('notes:success'),
            msg_prefix=''.join(
                ('Убедитесь, что после удаления заметки ',
                 'автор перенаправляется на notes:success.')
            )
        )
        self.assertEqual(
            Note.objects.filter(pk=updating_note_id).exists(),
            False,
            ''.join(
                ('Убедитесь, что при запросе автора на notes:delete ',
                 'заметка действительно удаляется.')
            )
        )

    def test_another_user_cant_update_note(self):
        editing_url: str = reverse('notes:edit', args=(self.author_note.slug,))
        updating_note_id: int = self.author_note.id
        self.another_user_client.post(editing_url, data=self.NOTE_DATA)
        self.assertEqual(
            Note.objects.get(pk=updating_note_id),
            Note.objects.get(slug=self.author_note.slug),
            ''.join(
                ('Убедитесь, что заметка не изменяется ',
                 'по запросу не автора поста.')
            )
        )
        deleting_url: str = reverse(
            'notes:delete', args=(self.author_note.slug,)
        )
        self.another_user_client.post(deleting_url)
        self.assertEqual(
            Note.objects.filter(pk=updating_note_id).exists(),
            True,
            ''.join(
                ('Убедитесь, что заметка не удаляется ',
                 'по запросу не её автора.')
            )
        )
