from typing import Dict, List

from django.contrib.auth import get_user_model
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
    NOTE_CHECK_SLUG: Dict[str, str] = {
        'title': 'Уникальный',
        'text': 'Для слага'
    }

    @classmethod
    def setUpTestData(cls):
        cls.anonim_client: Client = Client()
        cls.author_client: Client = Client()
        cls.another_user_client: Client = Client()
        cls.author: User = User.objects.create(
            username='Автор'
        )
        cls.another_user: User = User.objects.create(
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
        cls.note_check_slug: Note = Note.objects.create(
            author=cls.author,
            **cls.NOTE_CHECK_SLUG
        )

    def test_auth_user_can_create_note(self):
        url: str = reverse('notes:add')
        notes_before_post_ids = set(
            Note.objects.values_list('id', flat=True)
        )
        author_response: HttpResponseBase = self.author_client.post(
            url, data=self.NOTE_DATA
        )
        self.assertRedirects(
            response=author_response,
            expected_url=reverse('notes:success'),
            msg_prefix=(
                'Убедитесь, что после создания заметки '
                'автор перенаправляется на notes:success.'
            )
        )
        self.assertEqual(
            Note.objects.count(),
            len(notes_before_post_ids) + 1,
            'Убедитесь, что созданная пользователем заметка сохраняется.'
        )
        created_notes: List[Note] = list(
            Note.objects.exclude(id__in=notes_before_post_ids)
        )
        created_note: Note = created_notes[-1]
        self.assertEqual(
            created_note.title,
            self.NOTE_DATA['title'],
            ('Убедитесь, что заголовок сохраненной заметки '
             'совпадает с отправленным.')
        )
        self.assertEqual(
            created_note.text,
            self.NOTE_DATA['text'],
            ('Убедитесь, что текст сохраненной заметки '
             'совпадает с отправленным.')
        )
        self.assertEqual(
            created_note.author,
            self.author,
            ('Убедитесь, что автор сохраненной заметки '
             'совпадает с отправителем.')
        )

    def test_anonim_cant_create_note(self):
        url: str = reverse('notes:add')
        notes_in_db: int = Note.objects.count()
        anonim_response: HttpResponseBase = self.anonim_client.post(
            url, data=self.NOTE_DATA
        )
        self.assertRedirects(
            anonim_response,
            reverse('users:login') + f'?next={url}',
            msg_prefix=(
                'Убедитесь, что анонимный пользователь при попытке '
                'создать заметку перенаправляется на страницу авторизации.'
            )
        )
        self.assertEqual(
            Note.objects.count(),
            notes_in_db,
            ('Убедитесь, что отправленная '
             'анонимным пользователем заметка не сохраняется.')
        )

    def test_note_has_unique_slug(self):
        url: str = reverse('notes:add')
        notes_in_db: int = Note.objects.count()
        expected_error: str = self.note_check_slug.slug + WARNING
        second_note_response: HttpResponseBase = self.author_client.post(
            url, data=model_to_dict(self.note_check_slug)
        )
        self.assertFormError(
            second_note_response,
            'form',
            'slug',
            expected_error,
            ('Убедитесь, что при попытке создать пост '
             'с существующим slug, форма возвращается ошибку.')
        )
        self.assertEqual(
            Note.objects.count(),
            notes_in_db,
            'Убедитесь, что заметка с уже существующим slug не сохраняется.'
        )

    def test_create_slug_if_not_stated(self):
        url: str = reverse('notes:add')
        notes_before_post_ids = set(
            Note.objects.all().values_list('id', flat=True)
        )
        self.author_client.post(url, data=self.NOTE_DATA)
        created_note = list(
            Note.objects.exclude(id__in=notes_before_post_ids)
        )
        self.assertTrue(
            len(created_note) == 1,
            ('Убедитесь, что при запросе пользователя '
             'создается лишь одна заметка.')
        )
        self.assertEqual(
            model_to_dict(
                created_note[-1],
                fields=self.NOTE_DATA.keys()
            ),
            self.NOTE_DATA,
            ('Убедитесь, что при создании заметки без указания slug '
             'последний формируется автоматически '
             'при помощи pytils.slugify.')
        )

    def test_author_can_edit_note(self):
        url: str = reverse('notes:edit', args=(self.author_note.slug,))
        response: HttpResponseBase = self.author_client.post(
            url, data=self.NOTE_DATA
        )
        self.assertRedirects(
            response,
            expected_url=reverse('notes:success'),
            msg_prefix=(
                'Убедитесь, что после редактирования заметки '
                'автор перенаправляется на notes:success.'
            )
        )
        updated_note: Note = Note.objects.get(id=self.author_note.id)
        self.assertEqual(
            updated_note.title,
            self.NOTE_DATA['title'],
            ('Убедитесь, что заголовок заметки совпадает с тем, '
             'что был отправлен автором.')
        )
        self.assertEqual(
            updated_note.text,
            self.NOTE_DATA['text'],
            ('Убедитесь, что текст заметки совпадает с тем, '
             'что был отправлен автором.')
        )
        self.assertEqual(
            updated_note.slug,
            slugify(self.NOTE_DATA['title'])[:SLUG_MAX_LENGTH],
            ('Убедитесь, что slug заметки совпадает с тем, '
             'что должен был быть сгенерирован.')
        )
        self.assertEqual(
            updated_note.author,
            self.author_note.author,
            'Убедитесь, что автор заметки не изменился.'
        )

    def test_author_can_delete_note(self):
        deleting_note_id: int = self.author_note.id
        url: str = reverse(
            'notes:delete', args=(self.author_note.slug,)
        )
        response: HttpResponseBase = self.author_client.post(url)
        self.assertRedirects(
            response,
            expected_url=reverse('notes:success'),
            msg_prefix=(
                'Убедитесь, что после удаления заметки '
                'автор перенаправляется на notes:success.'
            )
        )
        self.assertFalse(
            Note.objects.filter(pk=deleting_note_id).exists(),
            ('Убедитесь, что при запросе автора на notes:delete '
             'заметка действительно удаляется.')
        )

    def test_another_user_cant_edit_note(self):
        url: str = reverse('notes:edit', args=(self.author_note.slug,))
        self.another_user_client.post(url, data=self.NOTE_DATA)
        editing_note: Note = Note.objects.get(id=self.author_note.id)
        self.assertEqual(
            editing_note.title,
            self.author_note.title,
            'Убедитесь, что заголовок заметки не был изменен.'
        )
        self.assertEqual(
            editing_note.text,
            self.author_note.text,
            'Убедитесь, что текст заметки не был изменен.'
        )
        self.assertEqual(
            editing_note.slug,
            self.author_note.slug,
            'Убедитесь, что slug заметки не был изменен.'
        )
        self.assertEqual(
            editing_note.author,
            self.author_note.author,
            'Убедитесь, что author заметки не был изменен.'
        )

    def test_another_user_cant_delete_note(self):
        deleting_note_id: int = self.author_note.id
        deleting_url: str = reverse(
            'notes:delete', args=(self.author_note.slug,)
        )
        self.another_user_client.post(deleting_url)
        self.assertTrue(
            Note.objects.filter(pk=deleting_note_id).exists(),
            ('Убедитесь, что заметка не удаляется '
             'по запросу не её автора.')
        )
