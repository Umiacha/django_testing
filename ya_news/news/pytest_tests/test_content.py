import pytest

from django.urls import reverse

@pytest.mark.usefixtures('posts_for_pagination')
def test_news_count_on_mainpage(client):
    HOME_PAGE_URL_NAME = 'news:home'
    NEWS_ON_PAGE = 10
    url = reverse(HOME_PAGE_URL_NAME)
    response = client.get(url)
    news_list = response.context['object_list']
    assert len(news_list) == NEWS_ON_PAGE


@pytest.mark.usefixtures('posts_for_pagination')
def test_news_sorting(client):
    HOME_PAGE_URL_NAME = 'news:home'
    url = reverse(HOME_PAGE_URL_NAME)
    response = client.get(url)
    news_list = [news for news in response.context['object_list']]
    sorted_news = sorted(news_list, key=lambda post: post.date, reverse=True)
    assert sorted_news == news_list

@pytest.mark.django_db
@pytest.mark.usefixtures('comments_for_post')
def test_comments_sorting(client, news):
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    comments_list = [comment for comment in response.context['news'].comment_set.all()]
    sorted_comments = sorted(comments_list, key=lambda x: x.created)
    assert sorted_comments == comments_list


@pytest.mark.django_db
@pytest.mark.parametrize(
    'user_agent, expected_result',
    [
        (pytest.lazy_fixture('client'), False),
        (pytest.lazy_fixture('author_client'), True)
    ]
)
def test_page_contains_comment_form(news, user_agent, expected_result):
    url = reverse('news:detail', args=(news.id,))
    response = user_agent.get(url)
    assert ('form' in response.context) == expected_result
