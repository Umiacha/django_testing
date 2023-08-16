from typing import Dict

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.contrib.auth.models import AbstractBaseUser
from django.http.response import HttpResponseBase

from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING

User: AbstractBaseUser = get_user_model()


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

    def test_auth_user_can_create_note(self):
        url: str = reverse('notes:add')
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
            0,
            ''.join(
                ('Убедитесь, что отправленная ',
                 'анонимным пользователем заметка не сохраняется.')
            )
        )
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
            1,
            'Убедитесь, что созданная пользователем заметка сохраняется.'
        )

    def test_note_has_unique_slug(self):
        url: str = reverse('notes:add')
        self.author_client.post(url, data=self.NOTE_DATA)
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
            1,
            'Убедитесь, что заметка с уже существующим slug не сохраняется.'
        )

    def test_create_slug_if_not_stated(self):
        url: str = reverse('notes:add')
        self.author_client.post(url, data=self.NOTE_DATA)
        result_slug: Note = Note.objects.first().slug
        expected_slug: str = slugify(self.NOTE_DATA['title'])[:100]
        self.assertEqual(
            result_slug,
            expected_slug,
            ''.join(
                ('Убедитесь, что при создании заметки без указания slug ',
                 'последний формируется автоматически ',
                 'при помощи pytils.slugify.')
            )
        )

    def test_only_author_can_update_note(self):
        author_note: Note = Note.objects.create(
            title='Заметка автора',
            text='Авторский текст',
            author=self.author
        )
        another_user_note: Note = Note.objects.create(
            title='Заметка пользователя',
            text='Текст заметки пользователя',
            author=self.another_user
        )
        for note_slug, can_update in [
            (author_note.slug, True), (another_user_note.slug, False)
        ]:
            with self.subTest(note_slug=note_slug, can_update=can_update):
                updating_note_id: int = Note.objects.get(slug=note_slug).id
                edit_url: str = reverse('notes:edit', args=(note_slug,))
                edit_response: HttpResponseBase = self.author_client.post(
                    edit_url, data=self.NOTE_DATA
                )
                if can_update:
                    self.assertRedirects(
                        edit_response,
                        reverse('notes:success'),
                        msg_prefix=''.join(
                            ('Убедитесь, что после редактирования заметки ',
                             'автор перенаправляется на notes:success.')
                        )
                    )
                    self.assertEqual(
                        model_to_dict(
                            Note.objects.get(pk=updating_note_id),
                            fields=self.NOTE_DATA.keys()
                        ), self.NOTE_DATA, ''.join(
                            ('Убедитесь, что поля записи обновляются ',
                             'после редактирования автором.')
                        )
                    )
                else:
                    self.assertEqual(
                        Note.objects.get(pk=updating_note_id),
                        Note.objects.get(slug=note_slug)
                    )
                updating_note_slug: str = Note.objects.get(
                    pk=updating_note_id
                ).slug
                delete_url: str = reverse(
                    'notes:delete', args=(updating_note_slug,)
                )
                delete_response: HttpResponseBase = self.author_client.post(
                    delete_url
                )
                if can_update:
                    self.assertRedirects(
                        response=delete_response,
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
                            ('Убедитесь, что при запросе на notes:delete ',
                             'заметка действительно удаляется.')
                        )
                    )
                else:
                    self.assertEqual(
                        Note.objects.filter(pk=updating_note_id).exists(),
                        True,
                        ''.join(
                            ('Убедитесь, что при запросе на удаление ',
                             'от не автора заметки последняя сохраняется.')
                        )
                    )
