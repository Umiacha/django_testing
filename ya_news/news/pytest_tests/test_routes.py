from http import HTTPStatus
from typing import Union

from django.http.response import HttpResponseBase
from django.test import Client
from django.urls import reverse
import pytest
from pytest_django.asserts import assertRedirects

from news.models import Comment


@pytest.mark.usefixtures('news')
@pytest.mark.django_db
@pytest.mark.parametrize(
    'url_name',
    [
        reverse('news:home'),
        reverse('users:login'),
        reverse('users:logout'),
        reverse('users:signup'),
        reverse('news:detail', args=(1,)),
    ],
    ids=['home', 'login', 'logout', 'signup', 'news_detail']
)
def test_page_availability_for_anonymous(
    client: Client,
    url_name: str
):
    """
    'news:detail' test work with page of 'news' fixture.
    Fixture's page id specified explicitly in parameters because of
    test's parametrizing happens at collection time.
    """
    response: HttpResponseBase = client.get(url_name)
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
        (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
    ],
    ids=['author', 'another_user']
)
def test_update_comment_by_user(
    url_name: str,
    user_agent: Client,
    response_code: Union[int, str],
    comment: Comment
):
    url: str = reverse(url_name, args=(comment.id,))
    response: HttpResponseBase = user_agent.get(url)
    assert response.status_code == response_code


@pytest.mark.parametrize(
    'url_name',
    ('news:delete', 'news:edit'),
    ids=['delete_comment', 'edit_comment']
)
def test_anonim_update_comment_redirect(
    url_name: str,
    comment: Comment,
    client: Client
):
    REDIRECT_ERROR: str = (
        'Убедитесь, что при попытке редактирования',
        'или удаления комментария анонимный пользователь',
        'перенаправляется на страницу регистрации.'
    )
    url: str = reverse(url_name, args=(comment.id,))
    login_url: str = reverse('users:login')
    expected_url_for_anonim: str = f'{login_url}?next={url}'
    response: HttpResponseBase = client.get(url)
    assertRedirects(
        response,
        expected_url_for_anonim,
        msg_prefix=''.join(REDIRECT_ERROR)
    )
