from http import HTTPStatus
from typing import Dict, List

import pytest

from django.urls import reverse
from django.forms.models import model_to_dict
from django.test import Client
from django.http.response import HttpResponseBase

from pytest_django.asserts import assertRedirects, assertFormError

from news.models import News, Comment
from news.forms import WARNING

pytestmark = pytest.mark.django_db

# Объединить тесты для удаления и редактирования комментариев (возможно, через вызовы в третьем тесте).

@pytest.mark.parametrize(
    'user_agent, comments_posted, msg_additions',
    [
        (pytest.lazy_fixture('client'), 0, ['', '']),
        (pytest.lazy_fixture('author_client'), 1, ['не', 'не '])
    ],
    ids=['anonim_user', 'authorized_user']
)
def test_user_can_create_comment(news: News, comment_form_data: Dict[str, str], user_agent: Client, comments_posted: int, msg_additions: List[str]):
    url: str = reverse('news:detail', args=(news.id,))
    response: str = user_agent.post(url, data=comment_form_data)
    assert Comment.objects.count() == comments_posted, 'Убедитесь, что {}авторизованный пользователь {}может создать комментарий.'. format(*msg_additions)


def test_cancel_comment_with_bad_words(bad_comment_form_data: List[Dict[str, str]], news: News, author_client: Client):
    url: str = reverse('news:detail', args=(news.id,))
    for bad_data in bad_comment_form_data:
        response: HttpResponseBase = author_client.post(url, data=bad_data)
        assertFormError(response=response, form='form', field='text', errors=WARNING, msg_prefix='Убедитесь, что при попытке публикации комментария со словом из news.forms.BAD_WORDS форма возвращает ошибку.')
    assert Comment.objects.count() == 0, 'Убедитесь, что комментарии со словами из news.forms.BAD_WORDS не публикуются.'

@pytest.mark.parametrize(
    'url_name',
    ('news:edit', 'news:delete'),
    ids=['editing_comment', 'deleting_comment']
)
@pytest.mark.parametrize(
    'user_agent, can_update',
    [
        (pytest.lazy_fixture('author_client'), True),
        (pytest.lazy_fixture('admin_client'), False),
    ],
    ids=['comment_author', 'another_user']
)
def test_user_can_update_comment(comment: Comment, news: News, comment_form_data: Dict[str, str], user_agent: Client, can_update: bool, url_name: str):
    url: str = reverse(url_name, args=(comment.id,))
    response: HttpResponseBase = user_agent.post(url, data=comment_form_data)
    if can_update:
        expected_url: str = reverse('news:detail', args=(news.id,)) + '#comments'
        assertRedirects(response, expected_url, msg_prefix='Убедитесь, что при успешном обновлении состояния комментария авторизованный пользователь перенаправляется в раздел комментариев поста.')  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if url_name == 'news:edit':
            assert model_to_dict(Comment.objects.get(pk=comment.id))['text'] == comment_form_data['text'], 'Убедитесь, что текст комментария обновляется после редактирования.'
        else:
            assert Comment.objects.count() == 0, 'Убедитесь, что комментарий удаляется при отправке авторизованным пользователем соответствующего запроса.'
    else:
        assert response.status_code == HTTPStatus.NOT_FOUND, 'Убедитесь, что при попытке обновить состояние комментария другой пользователь получает ошибку 404.'
        if url_name == 'news:edit':
            assert model_to_dict(Comment.objects.get(pk=comment.id))['text'] == comment.text, 'Убедитесь, что комментарий не изменяется, если запрос отправляет не автор комментария.'
        else:
            assert Comment.objects.count() == 1, 'Убедитесь, что при комментарий не удаляется по запросу не автора комментария.'
