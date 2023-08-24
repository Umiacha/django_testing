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
        comments_list, key=lambda x: x.created
    )
    assert comments_list == sorted_comments, (
        'Убедитесь, что комментарии на странице новости '
        'отсортированы от старых к новым.'
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
    msg_additions: List[str],
):
    url: str = reverse('news:detail', args=(news.id,))
    response: HttpResponseBase = user_agent.get(url)
    context = response.context
    '''
    Сравнение нужно для anonim_client (ведь без сравнение с expected_result
    будет падать ошибка). А переносить сравнение
    с expected_result в проверку наличия формы
    (то бишь, ('form' in context) == expected_result) нельзя,
    иначе anonim_client в проверке будет доходить до isinstance.

    В таком случае я вижу только два варианта:
    1) разделить проверки наличия и класса формы на два assert;
    2) оставить только проверку класса формы,
    отлавливая KeyError (для anonim_client) через try-except.

    С точки зрения производительности я не вижу разницы
    между этими случаями, однако
    в соответствии с best practices (use exceptions for exceptional
    cases) я реализую первый вариант.
    '''
    assert ('form' in context) == expected_result, (
        'Убедитесь, что форма для создания комментария '
        '{} отображается {}авторизованному пользователю'
        .format(*msg_additions)
    )
    if expected_result:
        assert isinstance(context['form'], CommentForm), (
            'Убедитесь, что форма комментария это объект класса CommentForm.'
        )
