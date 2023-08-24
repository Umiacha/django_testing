from http import HTTPStatus
from typing import Dict, List, Tuple

from django.contrib.auth import get_user
from django.http.response import HttpResponseBase
from django.test import Client
from django.urls import reverse
import pytest
from pytest_django.asserts import assertRedirects

from news.models import Comment


@pytest.mark.usefixtures('news', 'comment')
@pytest.mark.django_db
@pytest.mark.parametrize(
    'url, user_statuses_and_codes',
    [
        (reverse('news:home'),
         (('аноним', HTTPStatus.OK),)),
        (reverse('users:login'),
         (('аноним', HTTPStatus.OK),)),
        (reverse('users:logout'),
         (('аноним', HTTPStatus.OK),)),
        (reverse('users:signup'),
         (('аноним', HTTPStatus.OK),)),
        (reverse('news:detail', args=(1,)),
         (('аноним', HTTPStatus.OK),)),
        (reverse('news:edit', args=(1,)),
         (('аноним', HTTPStatus.FOUND),
          ('авторизованный', HTTPStatus.NOT_FOUND),
          ('автор', HTTPStatus.OK))),
        (reverse('news:delete', args=(1,)),
         (('аноним', HTTPStatus.FOUND),
          ('авторизованный', HTTPStatus.NOT_FOUND),
          ('автор', HTTPStatus.OK))),
    ],
    ids=['home', 'login', 'logout', 'signup', 'news_detail',
         'news_edit', 'news_delete']
)
def test_pages_availability(
    url: str,
    user_statuses_and_codes: List[Tuple[Tuple[str, int]]],
    anonim_client: Client,
    admin_client: Client,
    author_client: Client
):
    user_clients: Dict[str, Client] = {
        'аноним': anonim_client,
        'авторизованный': admin_client,
        'автор': author_client,
    }
    for user_status, expected_code in user_statuses_and_codes:
        user_client: Client = user_clients[user_status]
        response: HttpResponseBase = user_client.get(url)
        assert response.status_code == expected_code, (
            f'Убедитесь, что пользователь {get_user(user_client)} '
            f'имеет доступ к {url}.'
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
    url: str = reverse(url_name, args=(comment.id,))
    login_url: str = reverse('users:login')
    expected_url_for_anonim: str = f'{login_url}?next={url}'
    response: HttpResponseBase = anonim_client.get(url)
    assertRedirects(
        response,
        expected_url_for_anonim,
        msg_prefix=(
            'Убедитесь, что при попытке редактирования '
            'или удаления комментария анонимный пользователь '
            'перенаправляется на страницу регистрации.'
        )
    )
