"""
Тесты для API блога
Используется pytest-django для тестирования всех эндпоинтов
"""
import pytest
import json
from django.contrib.auth import get_user_model
from django.test import Client
from .models import Article, Comment, Category

User = get_user_model()


# ==================== Фикстуры ====================

@pytest.fixture
def client():
    """Фикстура для тестового клиента Django"""
    return Client()


@pytest.fixture
def user1(db):
    """Фикстура для первого пользователя"""
    return User.objects.create_user(
        username='user1',
        password='testpass123',
        is_active=True
    )


@pytest.fixture
def user2(db):
    """Фикстура для второго пользователя"""
    return User.objects.create_user(
        username='user2',
        password='testpass123',
        is_active=True
    )


@pytest.fixture
def test_user(db):
    """Фикстура для тестового пользователя"""
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        is_active=True
    )


@pytest.fixture
def category(db):
    """Фикстура для категории"""
    return Category.objects.create(name='Технологии', slug='tech', description='Технологии')


@pytest.fixture
def article(db, user1, category):
    """Фикстура для опубликованной статьи"""
    return Article.objects.create(
        title='Тестовая статья',
        slug='test-article',
        content='Содержание статьи',
        author=user1,
        category=category,
        published=True
    )


@pytest.fixture
def unpublished_article(db, user1):
    """Фикстура для неопубликованной статьи"""
    return Article.objects.create(
        title='Неопубликованная статья',
        slug='unpublished-article',
        content='Содержание',
        author=user1,
        published=False
    )


@pytest.fixture
def article_no_category(db, user1):
    """Фикстура для статьи без категории"""
    return Article.objects.create(
        title='Статья без категории',
        slug='article-no-category',
        content='Содержание',
        author=user1,
        published=True
    )


@pytest.fixture
def comment(db, article_no_category, user1):
    """Фикстура для комментария"""
    return Comment.objects.create(
        article=article_no_category,
        author=user1,
        content='Тестовый комментарий'
    )


# ==================== Вспомогательные функции ====================

def get_auth_token(client, username, password):
    """Получить JWT токен для авторизации"""
    response = client.post(
        '/api/token/pair',
        json.dumps({'username': username, 'password': password}),
        content_type='application/json'
    )
    if response.status_code == 200:
        return response.json().get('access')
    return None


def get_authenticated_headers(client, user):
    """Получить заголовки с JWT токеном для аутентифицированного пользователя"""
    # Используем прямое создание токена через django-ninja-jwt
    from ninja_jwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    return {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}


# ==================== Тесты для регистрации ====================

@pytest.mark.django_db
def test_register_success(client):
    """Тест успешной регистрации пользователя"""
    data = {
        'username': 'newuser',
        'password': 'newpass123'
    }
    response = client.post(
        '/api/blog/register',
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 200
    response_data = response.json()
    assert 'message' in response_data
    assert User.objects.filter(username='newuser').exists()


def test_register_duplicate_username(client, test_user):
    """Тест регистрации с существующим username"""
    data = {
        'username': 'testuser',
        'password': 'newpass123'
    }
    response = client.post(
        '/api/blog/register',
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 400
    response_data = response.json()
    assert 'error' in response_data


def test_register_missing_fields(client):
    """Тест регистрации без обязательных полей"""
    data = {
        'username': 'newuser'
        # password отсутствует
    }
    response = client.post(
        '/api/blog/register',
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code in [400, 422]  # Django Ninja возвращает 422 для ошибок валидации


# ==================== Тесты для JWT аутентификации ====================

def test_jwt_login_invalid_credentials(client, test_user):
    """Тест входа с неверными данными"""
    data = {
        'username': 'testuser',
        'password': 'wrongpass'
    }
    response = client.post(
        '/api/token/pair',
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 401


def test_jwt_login_nonexistent_user(client):
    """Тест входа несуществующего пользователя"""
    data = {
        'username': 'nonexistent',
        'password': 'password'
    }
    response = client.post(
        '/api/token/pair',
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 401


# ==================== Тесты для статей ====================

def test_list_articles_success(client, article):
    """Тест успешного получения списка статей"""
    response = client.get('/api/blog/articles')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['title'] == 'Тестовая статья'


@pytest.mark.django_db
def test_list_articles_empty(client):
    """Тест получения пустого списка статей"""
    response = client.get('/api/blog/articles')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_articles_with_search(client, article):
    """Тест поиска статей"""
    response = client.get('/api/blog/articles?search=Тестовая')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['title'] == 'Тестовая статья'


def test_list_articles_search_no_results(client, article):
    """Тест поиска статей без результатов"""
    response = client.get('/api/blog/articles?search=Несуществующая')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_list_articles_filter_by_category(client, article, category):
    """Тест фильтрации статей по категории"""
    response = client.get(f'/api/blog/articles?category_id={category.id}')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['category_id'] == category.id


def test_get_article_success(client, article):
    """Тест успешного получения статьи по ID"""
    response = client.get(f'/api/blog/articles/{article.id}')
    assert response.status_code == 200
    data = response.json()
    assert data['title'] == 'Тестовая статья'
    assert data['id'] == article.id


@pytest.mark.django_db
def test_get_article_not_found(client):
    """Тест получения несуществующей статьи"""
    response = client.get('/api/blog/articles/999')
    assert response.status_code == 404


def test_get_article_unpublished(client, unpublished_article):
    """Тест получения неопубликованной статьи (должна вернуть 404)"""
    response = client.get(f'/api/blog/articles/{unpublished_article.id}')
    assert response.status_code == 404


def test_create_article_success(client, user1, category):
    """Тест успешного создания статьи"""
    headers = get_authenticated_headers(client, user1)
    
    data = {
        'title': 'Новая статья',
        'content': 'Содержание новой статьи',
        'published': True,
        'category_id': category.id
    }
    response = client.post(
        '/api/blog/articles',
        json.dumps(data),
        content_type='application/json',
        **headers
    )
    assert response.status_code == 200
    assert Article.objects.count() == 1
    response_data = response.json()
    assert response_data['title'] == 'Новая статья'


def test_create_article_unauthorized(client):
    """Тест создания статьи без авторизации"""
    data = {
        'title': 'Новая статья',
        'content': 'Содержание новой статьи'
    }
    response = client.post(
        '/api/blog/articles',
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 401


def test_create_article_missing_fields(client, user1):
    """Тест создания статьи без обязательных полей"""
    headers = get_authenticated_headers(client, user1)
    data = {
        'title': 'Новая статья'
        # content отсутствует
    }
    response = client.post(
        '/api/blog/articles',
        json.dumps(data),
        content_type='application/json',
        **headers
    )
    assert response.status_code in [400, 422]


def test_update_article_success(client, article, user1):
    """Тест успешного обновления своей статьи"""
    headers = get_authenticated_headers(client, user1)
    
    data = {
        'title': 'Обновленная статья',
        'content': 'Новое содержание'
    }
    response = client.put(
        f'/api/blog/articles/{article.id}',
        json.dumps(data),
        content_type='application/json',
        **headers
    )
    assert response.status_code == 200
    article.refresh_from_db()
    assert article.title == 'Обновленная статья'


def test_update_article_other_user(client, article, user2):
    """Тест попытки обновить чужую статью"""
    headers = get_authenticated_headers(client, user2)
    
    data = {
        'title': 'Взломанная статья',
        'content': 'Новое содержание'
    }
    response = client.put(
        f'/api/blog/articles/{article.id}',
        json.dumps(data),
        content_type='application/json',
        **headers
    )
    assert response.status_code == 403


def test_update_article_unauthorized(client, article):
    """Тест обновления статьи без авторизации"""
    data = {
        'title': 'Обновленная статья',
        'content': 'Новое содержание'
    }
    response = client.put(
        f'/api/blog/articles/{article.id}',
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 401


def test_delete_article_success(client, article, user1):
    """Тест успешного удаления своей статьи"""
    headers = get_authenticated_headers(client, user1)
    
    article_id = article.id
    response = client.delete(f'/api/blog/articles/{article_id}', **headers)
    assert response.status_code == 200
    assert not Article.objects.filter(id=article_id).exists()


def test_delete_article_other_user(client, article, user2):
    """Тест попытки удалить чужую статью"""
    headers = get_authenticated_headers(client, user2)
    
    response = client.delete(f'/api/blog/articles/{article.id}', **headers)
    assert response.status_code == 403
    assert Article.objects.filter(id=article.id).exists()


def test_delete_article_unauthorized(client, article):
    """Тест удаления статьи без авторизации"""
    response = client.delete(f'/api/blog/articles/{article.id}')
    assert response.status_code == 401


# ==================== Тесты для комментариев ====================

def test_list_comments_success(client, article_no_category, comment):
    """Тест успешного получения списка комментариев"""
    response = client.get(f'/api/blog/articles/{article_no_category.id}/comments')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['content'] == 'Тестовый комментарий'


def test_list_comments_empty(client, article):
    """Тест получения пустого списка комментариев"""
    response = client.get(f'/api/blog/articles/{article.id}/comments')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.django_db
def test_list_comments_article_not_found(client):
    """Тест получения комментариев для несуществующей статьи"""
    response = client.get('/api/blog/articles/999/comments')
    assert response.status_code == 404


def test_create_comment_success(client, article_no_category, user2):
    """Тест успешного создания комментария"""
    headers = get_authenticated_headers(client, user2)
    
    data = {
        'article_id': article_no_category.id,
        'content': 'Новый комментарий'
    }
    response = client.post(
        '/api/blog/comments',
        json.dumps(data),
        content_type='application/json',
        **headers
    )
    assert response.status_code == 200
    assert Comment.objects.count() == 1
    response_data = response.json()
    assert response_data['content'] == 'Новый комментарий'


def test_create_comment_unauthorized(client, article_no_category):
    """Тест создания комментария без авторизации"""
    data = {
        'article_id': article_no_category.id,
        'content': 'Новый комментарий'
    }
    response = client.post(
        '/api/blog/comments',
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 401


def test_create_comment_missing_fields(client, article_no_category, user1):
    """Тест создания комментария без обязательных полей"""
    headers = get_authenticated_headers(client, user1)
    data = {
        'article_id': article_no_category.id
        # content отсутствует
    }
    response = client.post(
        '/api/blog/comments',
        json.dumps(data),
        content_type='application/json',
        **headers
    )
    assert response.status_code in [400, 422]


def test_create_comment_article_not_found(client, user1):
    """Тест создания комментария для несуществующей статьи"""
    headers = get_authenticated_headers(client, user1)
    data = {
        'article_id': 999,
        'content': 'Комментарий'
    }
    response = client.post(
        '/api/blog/comments',
        json.dumps(data),
        content_type='application/json',
        **headers
    )
    assert response.status_code == 404


def test_update_comment_success(client, comment, user1):
    """Тест успешного обновления своего комментария"""
    headers = get_authenticated_headers(client, user1)
    
    data = {
        'content': 'Обновленный комментарий'
    }
    response = client.put(
        f'/api/blog/comments/{comment.id}',
        json.dumps(data),
        content_type='application/json',
        **headers
    )
    assert response.status_code == 200
    comment.refresh_from_db()
    assert comment.content == 'Обновленный комментарий'


def test_update_comment_other_user(client, comment, user2):
    """Тест попытки обновить чужой комментарий"""
    headers = get_authenticated_headers(client, user2)
    
    data = {
        'content': 'Взломанный комментарий'
    }
    response = client.put(
        f'/api/blog/comments/{comment.id}',
        json.dumps(data),
        content_type='application/json',
        **headers
    )
    assert response.status_code == 403


def test_update_comment_unauthorized(client, comment):
    """Тест обновления комментария без авторизации"""
    data = {
        'content': 'Обновленный комментарий'
    }
    response = client.put(
        f'/api/blog/comments/{comment.id}',
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 401


def test_delete_comment_success(client, comment, user1):
    """Тест успешного удаления своего комментария"""
    headers = get_authenticated_headers(client, user1)
    
    comment_id = comment.id
    response = client.delete(f'/api/blog/comments/{comment_id}', **headers)
    assert response.status_code == 200
    assert not Comment.objects.filter(id=comment_id).exists()


def test_delete_comment_other_user(client, comment, user2):
    """Тест попытки удалить чужой комментарий"""
    headers = get_authenticated_headers(client, user2)
    
    response = client.delete(f'/api/blog/comments/{comment.id}', **headers)
    assert response.status_code == 403
    assert Comment.objects.filter(id=comment.id).exists()


def test_delete_comment_unauthorized(client, comment):
    """Тест удаления комментария без авторизации"""
    response = client.delete(f'/api/blog/comments/{comment.id}')
    assert response.status_code == 401


# ==================== Тесты для категорий ====================

def test_list_categories_success(client, category):
    """Тест успешного получения списка категорий"""
    response = client.get('/api/blog/categories')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['name'] == 'Технологии'


@pytest.mark.django_db
def test_list_categories_empty(client):
    """Тест получения пустого списка категорий"""
    response = client.get('/api/blog/categories')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_create_category_success(client, user1):
    """Тест успешного создания категории"""
    headers = get_authenticated_headers(client, user1)
    
    data = {
        'name': 'Наука',
        'description': 'Категория о науке'
    }
    response = client.post(
        '/api/blog/categories',
        json.dumps(data),
        content_type='application/json',
        **headers
    )
    assert response.status_code == 200
    assert Category.objects.count() == 1
    response_data = response.json()
    assert response_data['name'] == 'Наука'


def test_create_category_unauthorized(client):
    """Тест создания категории без авторизации"""
    data = {
        'name': 'Наука',
        'description': 'Категория о науке'
    }
    response = client.post(
        '/api/blog/categories',
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 401


def test_create_category_missing_fields(client, user1):
    """Тест создания категории без обязательных полей"""
    headers = get_authenticated_headers(client, user1)
    data = {
        'description': 'Описание'
        # name отсутствует
    }
    response = client.post(
        '/api/blog/categories',
        json.dumps(data),
        content_type='application/json',
        **headers
    )
    assert response.status_code in [400, 422]

