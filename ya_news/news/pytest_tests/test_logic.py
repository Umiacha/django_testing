from http import HTTPStatus

import pytest

from django.urls import reverse
from django.forms.models import model_to_dict

from pytest_django.asserts import assertRedirects  # , assertFormError

from news.models import Comment
from news.forms import WARNING

# Изменить assert в test_cancel_comment_with_bad_words на assertFormError (а то колхоз!).
# Объединить тесты для удаления и редактирования комментариев (возможно, через вызовы в третьем тесте).

@pytest.mark.django_db
@pytest.mark.parametrize(
    'user_agent, comments_posted',
    [
        (pytest.lazy_fixture('client'), 0),
        (pytest.lazy_fixture('author_client'), 1)
    ]
)
def test_user_can_create_comment(news, comment_form_data, user_agent, comments_posted):
    url = reverse('news:detail', args=(news.id,))
    response = user_agent.post(url, data=comment_form_data)
    assert Comment.objects.count() == comments_posted


@pytest.mark.django_db
def test_cancel_comment_with_bad_words(bad_comment_form_data, news, author_client):
    url = reverse('news:detail', args=(news.id,))
    for bad_data in bad_comment_form_data:
        response = author_client.post(url, data=bad_data)
        assert WARNING in response.context['form'].errors['text']
    assert Comment.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    'user_agent, can_edit',
    [
        (pytest.lazy_fixture('author_client'), True),
        (pytest.lazy_fixture('admin_client'), False),
    ]
)
def test_user_can_edit_comment(comment, news, comment_form_data, user_agent, can_edit):
    url = reverse('news:edit', args=(comment.id,))
    response = user_agent.post(url, data=comment_form_data)
    if can_edit:
        expected_url = reverse('news:detail', args=(news.id,)) + '#comments'
        assertRedirects(response, expected_url)
        assert model_to_dict(Comment.objects.get(pk=comment.id))['text'] == comment_form_data['text']
    else:
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert model_to_dict(Comment.objects.get(pk=comment.id))['text'] == comment.text


@pytest.mark.django_db
@pytest.mark.parametrize(
    'user_agent, can_delete',
    [
        (pytest.lazy_fixture('author_client'), True),
        (pytest.lazy_fixture('admin_client'), False),
    ]
)
def test_user_can_delete_comment(comment, news, comment_form_data, user_agent, can_delete):
    url = reverse('news:delete', args=(comment.id,))
    response = user_agent.post(url, data=comment_form_data)
    if can_delete:
        expected_url = reverse('news:detail', args=(news.id,)) + '#comments'
        assertRedirects(response, expected_url)
        assert Comment.objects.count() == 0
    else:
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert Comment.objects.count() == 1
