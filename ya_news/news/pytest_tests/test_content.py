from typing import List

import pytest
from _pytest.mark.structures import MarkDecorator

from django.urls import reverse
from django.test import Client
from django.http.response import HttpResponseBase

from news.models import News, Comment

pytestmark: MarkDecorator = pytest.mark.django_db

@pytest.mark.usefixtures('posts_for_pagination')
def test_news_count_and_sorting_on_mainpage(client: Client):
    HOME_PAGE_URL_NAME: str = 'news:home'
    NEWS_ON_PAGE: int = 10
    url: str = reverse(HOME_PAGE_URL_NAME)
    response: HttpResponseBase = client.get(url)
    news_list: List[News] = [news for news in response.context['object_list']]
    assert len(news_list) == NEWS_ON_PAGE, f'Убедитесь, что количество отображаемых на главной странице постов не превышает {NEWS_ON_PAGE}.'
    sorted_news: List[News] = sorted(news_list, key=lambda post: post.date, reverse=True)
    assert sorted_news == news_list, 'Убедитесь, что посты на главной странице выводятся в порядке от новых к старым.'

@pytest.mark.usefixtures('comments_for_post')
def test_comments_sorting(client: Client, news: News):
    url: str = reverse('news:detail', args=(news.id,))
    response: HttpResponseBase = client.get(url)
    comments_list: List[Comment] = [comment for comment in response.context['news'].comment_set.all()]
    sorted_comments: List[Comment] = sorted(comments_list, key=lambda x: x.created)
    assert sorted_comments == comments_list, 'Убедитесь, что комментарии на странице новости отсортированы от старых к новым.'

@pytest.mark.parametrize(
    'user_agent, expected_result, msg_additions',
    [
        (pytest.lazy_fixture('client'), False, ['', '']),
        (pytest.lazy_fixture('author_client'), True, ['не ', 'не'])
    ]
)
def test_page_contains_comment_form(news: News, user_agent: Client, expected_result: bool, msg_additions: List[str]):
    url: str = reverse('news:detail', args=(news.id,))
    response: HttpResponseBase = user_agent.get(url)
    assert ('form' in response.context) == expected_result, 'Убедитесь, что форма создания комментария {}отображается на странице новости для {}авторизованного пользователя'.format(*msg_additions)
