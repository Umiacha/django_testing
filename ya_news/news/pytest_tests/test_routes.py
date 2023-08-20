from http import HTTPStatus

from django.http.response import HttpResponseBase
from django.test import Client
from django.urls import reverse
import pytest
from pytest_django.asserts import assertRedirects

from news.models import Comment


@pytest.mark.usefixtures('news', 'comment')
@pytest.mark.django_db
@pytest.mark.parametrize(
    'url, anonim_code, auth_code, author_code',
    [
        (reverse('news:home'),
         HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
        (reverse('users:login'),
         HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
        (reverse('users:logout'),
         HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
        (reverse('users:signup'),
         HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
        (reverse('news:detail', args=(1,)),
         HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
        (reverse('news:edit', args=(1,)),
         HTTPStatus.FOUND, HTTPStatus.NOT_FOUND, HTTPStatus.OK),
        (reverse('news:delete', args=(1,)),
         HTTPStatus.FOUND, HTTPStatus.NOT_FOUND, HTTPStatus.OK),
    ],
    ids=['home', 'login', 'logout', 'signup', 'news_detail',
         'news_edit', 'news_delete']
)
def test_pages_availability(
    url: str,
    auth_code: int,
    author_code: int,
    anonim_code: int,
    admin_client: Client,
    author_client: Client,
    anonim_client: Client,
):
    anonim_response: HttpResponseBase = anonim_client.get(url)
    assert anonim_response.status_code == anonim_code, ''.join(
        ('Убедитесь, что анонимный пользователь при переходе ',
         f'на {url} получает код ответа {anonim_code}.')
    )
    auth_response: HttpResponseBase = admin_client.get(url)
    assert auth_response.status_code == auth_code, ''.join(
        ('Убедитесь, что авторизованный пользователь при переходе ',
         f'на {url} получает код ответа {auth_code}.')
    )
    author_response: HttpResponseBase = author_client.get(url)
    assert author_response.status_code == author_code, ''.join(
        ('Убедитесь, что пользователь-автор при переходе ',
         f'на {url} получает код ответа {author_code}.')
    )


@pytest.mark.parametrize(
    'url_name',
    ('news:delete', 'news:edit'),
    ids=['delete_comment', 'edit_comment']
)
def test_anonim_update_comment_redirect(
    url_name: str,
    comment: Comment,
    anonim_client: Client
):
    REDIRECT_ERROR: str = (
        'Убедитесь, что при попытке редактирования',
        'или удаления комментария анонимный пользователь',
        'перенаправляется на страницу регистрации.'
    )
    url: str = reverse(url_name, args=(comment.id,))
    login_url: str = reverse('users:login')
    expected_url_for_anonim: str = f'{login_url}?next={url}'
    response: HttpResponseBase = anonim_client.get(url)
    assertRedirects(
        response,
        expected_url_for_anonim,
        msg_prefix=''.join(REDIRECT_ERROR)
    )
