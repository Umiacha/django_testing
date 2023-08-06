from datetime import datetime
import json
from random import randint
from typing import List, Dict

import pytest

from django.contrib.auth.models import User
from django.test import Client

from news.models import News, Comment
from news.forms import BAD_WORDS

# 1) Добавить аннотации типов (касается всех файлов).
# 2) Добавить комментарии ошибок в тестах.
# 3) Добавить ids в parametrize для улучшения читаемости.
# 4) Прогнать код через линтеры.

# Done?
# conftest: 1, docstrings for fixtures --> \/
# test_routes: 1, 2, 3, 4
# test_content: 1, 2, 3, 4
# test_logic: 1, 2, 3

@pytest.fixture
def author(django_user_model: User) -> User:
    """
    Return User model.
    """
    return django_user_model.objects.create(username='Автор')

@pytest.fixture
def author_client(author: User, client: Client) -> Client:
    """
    Return Client instance for author.
    """
    client.force_login(author)
    return client

@pytest.fixture
def news() -> News:
    """
    Generate and return post (News instance).
    """
    return News.objects.create(
        title='Title',
        text='Text',
        date=datetime.today()
    )

@pytest.fixture
def comment(author: User, news: News) -> Comment:
    """
    Generate and return comment
    for news created by author (Comment instance).
    """
    return Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария',
        created=datetime.now()
    )


@pytest.fixture
@pytest.mark.usefixtures('db')
def posts_for_pagination() -> List[News]:
    """
    Create News objects from JSON and return list of it
    """
    with open('/home/umiacha/yp/dev/django_testing/ya_news/news/fixtures/news.json') as news_fixture:
        news_dict: List[Dict[str, Dict[str, str]]] = json.load(news_fixture)
    return [News.objects.create(**news['fields']) for news in news_dict]


@pytest.fixture
def comments_for_post(news, author) -> List[Comment]:
    """
    Create and return as many Comment instances
    as specified in COMMENTS_FROM_AUTHOR.
    
    The value of COMMENTS_FROM_AUTHOR is quite
    random, so you can change it to another.
    """
    COMMENTS_FROM_AUTHOR: int = 7
    return [
        Comment.objects.create(
            news=news,
            author=author,
            text=f'Текст комментария {comm_counter}',
            created=datetime.now().replace(day=randint(1, 11))
        )
        for comm_counter in range(COMMENTS_FROM_AUTHOR)
    ]

@pytest.fixture
def comment_form_data() -> Dict[str, str]:
    """
    Return data for creating new Comment instance
    (or update existing).
    """
    return {'text': 'Текст коммента'}

@pytest.fixture
def bad_comment_form_data() -> List[Dict[str, str]]:
    """
    Return list of form_data with bad words from news.forms.
    """
    bad_data = []
    for word in BAD_WORDS:
        bad_data.append({'text': 'Ты %s, и что ты мне сделаешь?' % word})
    return bad_data
