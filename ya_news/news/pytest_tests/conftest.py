from datetime import datetime
import json

from random import randint

import pytest

from news.models import News, Comment


@pytest.fixture
def author(django_user_model):
    """
    Return User model.
    """
    return django_user_model.objects.create(username='Автор')

@pytest.fixture
def author_client(author, client):
    """
    Return Client instance for author.
    """
    client.force_login(author)
    return client

@pytest.fixture
def news():
    """
    Generate and return post (News instance).
    """
    return News.objects.create(
        title='Title',
        text='Text',
        date=datetime.today()
    )

@pytest.fixture
def comment(author, news):
    """
    Generate and return comment
    for news created by author (Comment instance).
    """
    return Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария',
        created=datetime.now
    )


@pytest.fixture
def posts_for_pagination(db):
    """
    Create News objects from JSON and return list of it
    """
    with open('/home/umiacha/yp/dev/django_testing/ya_news/news/fixtures/news.json') as news_fixture:
        news_dict = json.load(news_fixture)
    return [News.objects.create(**news['fields']) for news in news_dict]


@pytest.fixture
def comments_for_post(news, author):
    COMMENTS_FROM_AUTHOR = 7
    return [
        Comment.objects.create(
            news=news,
            author=author,
            text=f'Текст комментария {comm_counter}',
            created=datetime.now().replace(day=randint(1, 11))
        )
        for comm_counter in range(COMMENTS_FROM_AUTHOR)
    ]
