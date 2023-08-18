from http import HTTPStatus
from typing import Dict, List

from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.http.response import HttpResponseBase
from django.test import Client
from django.urls import reverse
import pytest
from pytest_django.asserts import assertFormError, assertRedirects

from news.models import Comment, News
from news.forms import WARNING

pytestmark = pytest.mark.django_db


def test_user_can_create_comment(
    news: News,
    author: User,
    comment_form_data: Dict[str, str],
    author_client: Client,
):
    COMMENTS_POSTED: int = Comment.objects.filter(news=news).count()
    url: str = reverse('news:detail', args=(news.id,))
    author_client.post(url, data=comment_form_data)
    assert Comment.objects.count() == COMMENTS_POSTED + 1, (
        'Убедитесь, что авторизованный пользователь ',
        'может создать комментарий.'
    )
    comment: Comment = Comment.objects.first()
    comment_form_data.update(
        {
            'id': COMMENTS_POSTED + 1,
            'author': author.id,
            'news': news.id
        }
    )
    assert model_to_dict(comment) == comment_form_data, (
        'Убедитесь, что поля создаваемого комментария',
        'корректно формируются.'
    )


def test_anonim_cant_create_comment(
    news: News,
    comment_form_data: Dict[str, str],
    client: Client,
):
    COMMENTS_POSTED: int = Comment.objects.filter(news=news).count()
    url: str = reverse('news:detail', args=(news.id,))
    client.post(url, data=comment_form_data)
    assert Comment.objects.count() == COMMENTS_POSTED, (
        'Убедитесь, что неавторизованный пользователь ',
        'не может создать комментарий.'
    )


def test_cancel_comment_with_bad_words(
    bad_comment_form_data: List[Dict[str, str]],
    news: News,
    author_client: Client
):
    COMMENTS_POSTED: int = Comment.objects.filter(news=news).count()
    url: str = reverse('news:detail', args=(news.id,))
    for bad_data in bad_comment_form_data:
        response: HttpResponseBase = author_client.post(
            url, data=bad_data
        )
        FORM_ERROR = (
            'Убедитесь, что при попытке публикации комментария ',
            'со словом из news.forms.BAD_WORDS форма возвращает ошибку.'
        )
        assertFormError(
            response=response,
            form='form',
            field='text',
            errors=WARNING,
            msg_prefix=''.join(FORM_ERROR)
        )
    assert Comment.objects.count() == COMMENTS_POSTED, (
        'Убедитесь, что комментарии со словами ',
        'из news.forms.BAD_WORDS не публикуются.'
    )


@pytest.mark.parametrize(
    'url_name',
    ('news:edit', 'news:delete'),
    ids=['editing_comment', 'deleting_comment']
)
def test_author_can_update_comment(
    comment: Comment,
    news: News,
    comment_form_data: Dict[str, str],
    author_client: Client,
    url_name: str
):
    url: str = reverse(url_name, args=(comment.id,))
    response: HttpResponseBase = author_client.post(
        url, data=comment_form_data
    )
    expected_url: str = reverse(
        'news:detail', args=(news.id,)
    ) + '#comments'
    REDIRECT_ERROR = (
        'Убедитесь, что при успешном обновлении комментария ',
        'автор перенаправляется в раздел комментариев поста.'
    )
    assertRedirects(
        response,
        expected_url,
        msg_prefix=''.join(REDIRECT_ERROR)
    )
    if url_name == 'news:edit':
        assert model_to_dict(
            Comment.objects.get(pk=comment.id)
        )['text'] == comment_form_data['text'], (
            'Убедитесь, что текст комментария ',
            'обновляется после редактирования.'
        )
    else:
        assert Comment.objects.count() == 0, (
            'Убедитесь, что комментарий удаляется при отправке ',
            'авторизованным пользователем соответствующего запроса.'
        )


@pytest.mark.parametrize(
    'url_name',
    ('news:edit', 'news:delete'),
    ids=['editing_comment', 'deleting_comment']
)
def test_another_user_cant_update_comment(
    comment: Comment,
    comment_form_data: Dict[str, str],
    url_name: str,
    admin_client: Client
):
    url: str = reverse(url_name, args=(comment.id,))
    response: HttpResponseBase = admin_client.post(url, data=comment_form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND, (
        'Убедитесь, что при попытке обновить комментарий ',
        'другой пользователь получает ошибку 404.'
    )
    if url_name == 'news:edit':
        assert model_to_dict(
            Comment.objects.get(pk=comment.id)
        )['text'] == comment.text, (
            'Убедитесь, что комментарий не изменяется, ',
            'если запрос отправляет не автор комментария.'
        )
    else:
        assert Comment.objects.count() == 1, (
            'Убедитесь, что при комментарий не удаляется ',
            'по запросу не автора комментария.'
        )
