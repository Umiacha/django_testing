from http import HTTPStatus

import pytest

from pytest_django.asserts import assertRedirects

from django.urls import reverse

# Объединить в один тесты маршрутов для удаления и редактирования комментариев.

@pytest.mark.django_db
@pytest.mark.parametrize(
    'url_name',
    ('news:home', 'users:login', 'users:logout', 'users:signup')
)
def test_page_availability_for_anonymous(client, url_name):
    url = reverse(url_name)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

@pytest.mark.django_db
def test_post_page_availability_for_anonymous(client, news):
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

@pytest.mark.parametrize(
    'url_name',
    ('news:delete', 'news:edit')
)
def test_update_comment_availability_for_author(author_client, comment, url_name):
    url = reverse(url_name, args=(comment.id,))
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK

@pytest.mark.parametrize(
    'url_name',
    ('news:delete', 'news:edit')
)
def test_update_comment_anonim_redirect(client, comment, url_name, login_url_name='users:login'):
    url = reverse(url_name, args=(comment.id,))
    login_url = reverse(login_url_name)
    response = client.get(url)
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)

@pytest.mark.parametrize(
    'url_name',
    ('news:delete', 'news:edit')
)
def test_update_comment_by_another_user(admin_client, comment, url_name):
    url = reverse(url_name, args=(comment.id,))
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
