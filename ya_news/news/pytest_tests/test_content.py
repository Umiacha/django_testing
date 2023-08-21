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
def test_news_sorting_on_mainpage(anonim_client: Client):
    url: str = reverse(HOME_PAGE_URL_NAME)
    response: HttpResponseBase = anonim_client.get(url)
    news_list = response.context['object_list']
    sorted_news: List[News] = sorted(
        news_list,
        key=lambda post: post.date,
        reverse=True
    )
    try:
        for result, expected in zip(news_list, sorted_news):
            assert result == expected
    except AssertionError:
        raise AssertionError(
            ('Убедитесь, что посты на главной странице '
             'выводятся в порядке от новых к старым.')
        )


@pytest.mark.usefixtures('comments_for_post')
def test_comments_sorting(anonim_client: Client, news: News):
    url: str = reverse('news:detail', args=(news.id,))
    response: HttpResponseBase = anonim_client.get(url)
    comments_list = response.context['news'].comment_set.all()
    sorted_comments: List[Comment] = sorted(
        comments_list, key=lambda x: x.created
    )
    try:
        for result, expected in zip(comments_list, sorted_comments):
            assert result == expected
    except AssertionError:
        raise AssertionError(
            ('Убедитесь, что комментарии на странице новости '
             'отсортированы от старых к новым.')
        )


@pytest.mark.parametrize(
    'user_agent, expected_result, msg_additions',
    [
        (pytest.lazy_fixture('anonim_client'), False, ['', '']),
        (pytest.lazy_fixture('author_client'), True, ['не ', 'не'])
    ],
    ids=['anonim_user', 'authorized_user']
)
def test_page_contains_comment_form(
    news: News,
    user_agent: Client,
    expected_result: bool,
    msg_additions: List[str]
):
    url: str = reverse('news:detail', args=(news.id,))
    response: HttpResponseBase = user_agent.get(url)
    context = response.context
    '''
    Но почему "избыточно"? Оператор and проходит логическое выражение
    слева-направо и возвращает первое ложное высказывание, либо
    (если все True) -- последнее высказывание.
    Как раз таки благодаря "ленивости" and при
    тестировании запроса анонимного пользователя мы не доходим до
    isinstance и не получаем KeyError, а при проверке пользователя до
    isinstance мы доходить (и проходить его) должны. Или я неправильно понял?
    '''
    assert (
        'form' in context
        and isinstance(context['form'], CommentForm)
    ) == expected_result, (
        'Убедитесь, что форма создания комментария {}отображается '
        .format(msg_additions[0]),
        'на странице новости для {}авторизованного пользователя'
        .format(msg_additions[1])
    )
