from datetime import datetime

import pytest

from news.models import News, Comment


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')

@pytest.fixture
def author_client(author, client):
    client.force_login(author)
    return client

@pytest.fixture
def news():
    return News.objects.create(
        title='Title',
        text='Text',
        date=datetime.today()
    )

@pytest.fixture
def comment(author, news):
    return Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария',
        created=datetime.now
    )
