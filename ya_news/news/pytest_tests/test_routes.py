from http import HTTPStatus
from typing import Dict, List, Tuple, Union

from django.contrib.auth import get_user
from django.http.response import HttpResponseBase
from django.test import Client
from django.urls import reverse
import pytest
from pytest_django.asserts import assertRedirects

from news.models import Comment, News


@pytest.mark.usefixtures('news', 'comment')
@pytest.mark.django_db
@pytest.mark.parametrize(
    'url_name, url_obj, user_statuses_and_codes',
    [
        ('news:home', None,
         (('аноним', HTTPStatus.OK),)),
        ('users:login', None,
         (('аноним', HTTPStatus.OK),)),
        ('users:logout', None,
         (('аноним', HTTPStatus.OK),)),
        ('users:signup', None,
         (('аноним', HTTPStatus.OK),)),
        ('news:detail', pytest.lazy_fixture('news'),
         (('аноним', HTTPStatus.OK),)),
        ('news:edit', pytest.lazy_fixture('news'),
         (('аноним', HTTPStatus.FOUND),
          ('авторизованный', HTTPStatus.NOT_FOUND),
          ('автор', HTTPStatus.OK))),
        ('news:delete', pytest.lazy_fixture('news'),
         (('аноним', HTTPStatus.FOUND),
          ('авторизованный', HTTPStatus.NOT_FOUND),
          ('автор', HTTPStatus.OK))),
    ],
    ids=['home', 'login', 'logout', 'signup', 'news_detail',
         'news_edit', 'news_delete']
)
def test_pages_availability(
    url_name: str,
    url_obj: Union[News, None],
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
    url_args: Union[int, None] = (url_obj.id,) if url_obj else None
    url = reverse(url_name, args=url_args)
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
