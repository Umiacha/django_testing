from typing import List

from django.conf import settings
from django.http.response import HttpResponseBase
from django.test import Client
from django.urls import reverse
from _pytest.mark.structures import MarkDecorator
import pytest

from news.forms import CommentForm
from news.models import News, Comment


HOME_PAGE_URL_NAME: str = 'news:home'

pytestmark: MarkDecorator = pytest.mark.django_db


@pytest.mark.usefixtures('posts_for_pagination')
def test_news_count_on_mainpage(anonim_client: Client):
    url: str = reverse(HOME_PAGE_URL_NAME)
    response: HttpResponseBase = anonim_client.get(url)
    news_list = response.context['object_list']
    assert len(news_list) == settings.NEWS_COUNT_ON_HOME_PAGE, (
        'Убедитесь, что количество отображаемых'
        'на главной странице постов не превышает'
        f'{settings.NEWS_COUNT_ON_HOME_PAGE}.'
    )


@pytest.mark.usefixtures('posts_for_pagination')
def test_news_sorting_on_mainpage(
    anonim_client: Client,
):
    url: str = reverse(HOME_PAGE_URL_NAME)
    response: HttpResponseBase = anonim_client.get(url)
    # Get QuerySet and transform it to List for comparing.
    news_list: List[News] = response.context['object_list'][::1]
    sorted_news: List[News] = sorted(
        news_list,
        key=lambda post: post.date,
        reverse=True
    )
    assert news_list == sorted_news, (
        'Убедитесь, что список новостей на главной странице отсортированы '
        'от новых к старым.'
    )


@pytest.mark.usefixtures('comments_for_post')
def test_comments_sorting(anonim_client: Client, news: News):
    url: str = reverse('news:detail', args=(news.id,))
    response: HttpResponseBase = anonim_client.get(url)
    # Get QuerySet and transform it to List for comparing.
    comments_list: List[News] = response.context['news'].comment_set.all()[::1]
    sorted_comments: List[Comment] = sorted(
        comments_list, key=lambda comment_obj: comment_obj.created
    )
    assert comments_list == sorted_comments, (
        'Убедитесь, что комментарии на странице новости '
        'отсортированы от старых к новым.'
    )


def test_page_contains_comment_form_for_auth_user(
    news: News,
    author_client: Client,
):
    url: str = reverse('news:detail', args=(news.id,))
    response: HttpResponseBase = author_client.get(url)
    context = response.context
    assert (
        'form' in context
        and isinstance(context['form'], CommentForm)
    ), (
        'Убедитесь, что форма для создания комментария '
        'отображается авторизованному пользователю'
    )


def test_page_not_contain_comment_form_for_anonim(
    news: News,
    anonim_client: Client,
):
    url: str = reverse('news:detail', args=(news.id,))
    response: HttpResponseBase = anonim_client.get(url)
    context = response.context
    assert 'form' not in context, (
        'Убедитесь, что форма для создания комментария '
        'не отображается неавторизованному пользователю'
    )
