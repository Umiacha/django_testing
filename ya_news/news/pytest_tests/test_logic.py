from http import HTTPStatus
from typing import Dict, List

from django.contrib.auth.models import User
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
    comments_posted: int = Comment.objects.filter(news=news).count()
    url: str = reverse('news:detail', args=(news.id,))
    author_client.post(url, data=comment_form_data)
    assert Comment.objects.count() == comments_posted + 1, (
        'Убедитесь, что авторизованный пользователь ',
        'может создать комментарий.'
    )
    created_comment: Comment = Comment.objects.get(
        text=comment_form_data['text']
    )
    assert created_comment.id == comments_posted + 1, ''.join(
        ('Убедитесь, что id комментария формируется правильно.')
    )
    assert created_comment.text == comment_form_data['text'], ''.join(
        ('Убедитесь, что текст комментария формируется правильно.')
    )
    assert created_comment.author == author, ''.join(
        ('Убедитесь, что поле author_id комментария формируется правильно.')
    )
    assert created_comment.news == news, ''.join(
        ('Убедитесь, что news_id комментария формируется правильно.')
    )


def test_anonim_cant_create_comment(
    news: News,
    comment_form_data: Dict[str, str],
    anonim_client: Client,
):
    comments_posted: int = Comment.objects.filter(news=news).count()
    url: str = reverse('news:detail', args=(news.id,))
    anonim_client.post(url, data=comment_form_data)
    assert Comment.objects.count() == comments_posted, (
        'Убедитесь, что неавторизованный пользователь ',
        'не может создать комментарий.'
    )


def test_cancel_comment_with_bad_words(
    bad_comment_form_data: List[Dict[str, str]],
    news: News,
    author_client: Client
):
    comments_posted: int = Comment.objects.filter(news=news).count()
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
    assert Comment.objects.count() == comments_posted, (
        'Убедитесь, что комментарии со словами ',
        'из news.forms.BAD_WORDS не публикуются.'
    )


def test_author_can_delete_comment(
    comment: Comment,
    news: News,
    comment_form_data: Dict[str, str],
    author_client: Client,
):
    url: str = reverse('news:delete', args=(comment.id,))
    response: HttpResponseBase = author_client.post(
        url, data=comment_form_data
    )
    expected_url: str = reverse(
        'news:detail', args=(news.id,)
    ) + '#comments'
    DELETE_ERROR: str = (
        'Убедитесь, что при успешном обновлении комментария ',
        'автор перенаправляется в раздел комментариев поста.'
    )
    assertRedirects(
        response,
        expected_url,
        msg_prefix=''.join(DELETE_ERROR)
    )
    assert Comment.objects.count() == 0, (
        'Убедитесь, что комментарий удаляется при отправке ',
        'авторизованным пользователем соответствующего запроса.'
    )


def test_author_can_edit_comment(
    comment: Comment,
    author_client: Client,
    comment_form_data: Dict[str, str],
    news: News
):
    url: str = reverse('news:edit', args=(comment.id,))
    response: HttpResponseBase = author_client.post(
        url, data=comment_form_data
    )
    expected_url: str = reverse(
        'news:detail', args=(news.id,)
    ) + '#comments'
    EDIT_ERROR = (
        'Убедитесь, что при успешном редактировании комментария ',
        'автор перенаправляется в раздел комментариев поста.'
    )
    assertRedirects(
        response,
        expected_url,
        msg_prefix=''.join(EDIT_ERROR)
    )
    edited_comment: Comment = Comment.objects.get(pk=comment.id)
    assert edited_comment.id == comment.id, ''.join(
        ('Убедитесь, что id комментария совпадает с таковым до обновления.')
    )
    assert edited_comment.text == comment_form_data['text'], ''.join(
        ('Убедитесь, что текст комментария обновляется.')
    )
    assert edited_comment.author == comment.author, ''.join(
        ('Убедитесь, что author_id комментария ',
         'совпадает с таковым до обновления.')
    )
    assert edited_comment.news == comment.news, ''.join(
        ('Убедитесь, что news_id комментария ',
         'совпадает с таковым до обновления.')
    )


def test_another_user_cant_delete_comment(
    comment: Comment,
    comment_form_data: Dict[str, str],
    admin_client: Client,
    news: News,
):
    url: str = reverse('news:delete', args=(comment.id,))
    response: HttpResponseBase = admin_client.post(url, data=comment_form_data)
    comments_posted: int = Comment.objects.filter(news=news).count()
    assert response.status_code == HTTPStatus.NOT_FOUND, (
        'Убедитесь, что при попытке обновить комментарий ',
        'другой пользователь получает ошибку 404.'
    )
    assert Comment.objects.filter(news=news).count() == comments_posted, (
        'Убедитесь, что комментарий не удаляется ',
        'по запросу не автора комментария.'
    )


def test_another_user_cant_edit_comment(
    comment: Comment,
    admin_client: Client,
    comment_form_data: Dict[str, str],
):
    url: str = reverse('news:edit', args=(comment.id,))
    response: HttpResponseBase = admin_client.post(url, data=comment_form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND, (
        'Убедитесь, что при попытке отредактировать комментарий ',
        'другой пользователь получает ошибку 404.'
    )
    edited_comment: Comment = Comment.objects.get(pk=comment.id)
    assert edited_comment.id == comment.id, ''.join(
        ('Убедитесь, что id комментария совпадает с таковым до обновления.')
    )
    assert edited_comment.text == comment.text, ''.join(
        ('Убедитесь, что текст комментария совпадает с таковым до обновления.')
    )
    assert edited_comment.author == comment.author, ''.join(
        ('Убедитесь, что author_id комментария ',
         'совпадает с таковым до обновления.')
    )
    assert edited_comment.news == comment.news, ''.join(
        ('Убедитесь, что news_id комментария ',
         'совпадает с таковым до обновления.')
    )
