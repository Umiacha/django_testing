from http import HTTPStatus

import pytest
from typing import Union

from pytest_django.asserts import assertRedirects

from django.urls import reverse
from django.test import Client
from django.http.response import HttpResponseBase

from news.models import News, Comment


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url_name, page_args',
    [
        ('news:home', None),
        ('users:login', None),
        ('users:logout', None),
        ('users:signup', None),
        ('news:detail', pytest.lazy_fixture('news'))
    ],
    ids=['home', 'login', 'logout', 'signup', 'news_detail']
)
def test_page_availability_for_anonymous(
    client: Client,
    url_name: str,
    page_args: Union[None, News]
):
    if page_args is None:
        url: str = reverse(url_name)
    else:
        url: str = reverse(url_name, args=(page_args.id,))
    response: HttpResponseBase = client.get(url)
    assert response.status_code == HTTPStatus.OK, (
        f'Убедитесь, что страница {url_name} доступна',
        'для неаутентифицированного пользователя.'
    )


@pytest.mark.parametrize(
    'url_name',
    ('news:delete', 'news:edit'),
    ids=['delete_comment', 'edit_comment']
)
@pytest.mark.parametrize(
    'user_agent, response_code',
    [
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK),
        (pytest.lazy_fixture('client'), HTTPStatus.FOUND),
        (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
    ],
    ids=['author', 'anonimous_user', 'another_user']
)
def test_update_comment_by_user(
    url_name: str,
    user_agent: Client,
    response_code: Union[int, str],
    comment: Comment
):
    url: str = reverse(url_name, args=(comment.id,))
    login_url: str = reverse('users:login')
    expected_url_for_anonim: str = f'{login_url}?next={url}'
    response: HttpResponseBase = user_agent.get(url)
    if response.status_code == HTTPStatus.FOUND == response_code:
        REDIRECT_ERROR = (
            'Убедитесь, что при попытке редактирования',
            'или удаления комментария анонимный пользователь',
            'перенаправляется на страницу регистрации.'
        )
        assertRedirects(
            response,
            expected_url_for_anonim,
            msg_prefix=''.join(REDIRECT_ERROR)
        )
    assert response.status_code == response_code
