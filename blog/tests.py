from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Article, Comment, Category
import json

User = get_user_model()


class ArticleAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        self.category = Category.objects.create(name='Технологии', slug='tech')
        self.article = Article.objects.create(
            title='Тестовая статья',
            slug='test-article',
            content='Содержание статьи',
            author=self.user1,
            category=self.category
        )

    def get_auth_token(self, username, password):
        """Получить JWT токен для авторизации"""
        response = self.client.post(
            '/api/auth/login/',
            json.dumps({'username': username, 'password': password}),
            content_type='application/json'
        )
        if response.status_code == 200:
            return response.json().get('access')
        return None

    def test_list_articles_success(self):
        """Тест успешного получения списка статей"""
        response = self.client.get('/api/blog/articles/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_list_articles_with_search(self):
        """Тест поиска статей"""
        response = self.client.get('/api/blog/articles/?search=Тестовая')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)

    def test_get_article_success(self):
        """Тест успешного получения статьи по ID"""
        response = self.client.get(f'/api/blog/articles/{self.article.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], 'Тестовая статья')

    def test_get_article_not_found(self):
        """Тест получения несуществующей статьи"""
        response = self.client.get('/api/blog/articles/999/')
        self.assertEqual(response.status_code, 404)

    def test_create_article_success(self):
        """Тест успешного создания статьи"""
        token = self.get_auth_token('user1', 'testpass123')
        self.assertIsNotNone(token)
        
        data = {
            'title': 'Новая статья',
            'content': 'Содержание новой статьи',
            'published': True
        }
        response = self.client.post(
            '/api/blog/articles/',
            json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Article.objects.count(), 2)

    def test_create_article_unauthorized(self):
        """Тест создания статьи без авторизации"""
        data = {
            'title': 'Новая статья',
            'content': 'Содержание новой статьи'
        }
        response = self.client.post(
            '/api/blog/articles/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_update_article_success(self):
        """Тест успешного обновления своей статьи"""
        token = self.get_auth_token('user1', 'testpass123')
        self.assertIsNotNone(token)
        
        data = {
            'title': 'Обновленная статья',
            'content': 'Новое содержание'
        }
        response = self.client.put(
            f'/api/blog/articles/{self.article.id}/',
            json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Обновленная статья')

    def test_update_article_other_user(self):
        """Тест попытки обновить чужую статью"""
        token = self.get_auth_token('user2', 'testpass123')
        self.assertIsNotNone(token)
        
        data = {
            'title': 'Взломанная статья',
            'content': 'Новое содержание'
        }
        response = self.client.put(
            f'/api/blog/articles/{self.article.id}/',
            json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_article_success(self):
        """Тест успешного удаления своей статьи"""
        token = self.get_auth_token('user1', 'testpass123')
        self.assertIsNotNone(token)
        
        response = self.client.delete(
            f'/api/blog/articles/{self.article.id}/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Article.objects.count(), 0)

    def test_delete_article_other_user(self):
        """Тест попытки удалить чужую статью"""
        token = self.get_auth_token('user2', 'testpass123')
        self.assertIsNotNone(token)
        
        response = self.client.delete(
            f'/api/blog/articles/{self.article.id}/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Article.objects.count(), 1)


class CommentAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        self.article = Article.objects.create(
            title='Тестовая статья',
            slug='test-article',
            content='Содержание статьи',
            author=self.user1
        )
        self.comment = Comment.objects.create(
            article=self.article,
            author=self.user1,
            content='Тестовый комментарий'
        )

    def get_auth_token(self, username, password):
        """Получить JWT токен для авторизации"""
        response = self.client.post(
            '/api/auth/login/',
            json.dumps({'username': username, 'password': password}),
            content_type='application/json'
        )
        if response.status_code == 200:
            return response.json().get('access')
        return None

    def test_list_comments_success(self):
        """Тест успешного получения списка комментариев"""
        response = self.client.get(f'/api/blog/articles/{self.article.id}/comments/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_create_comment_success(self):
        """Тест успешного создания комментария"""
        token = self.get_auth_token('user2', 'testpass123')
        self.assertIsNotNone(token)
        
        data = {
            'article_id': self.article.id,
            'content': 'Новый комментарий'
        }
        response = self.client.post(
            '/api/blog/comments/',
            json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 2)

    def test_create_comment_unauthorized(self):
        """Тест создания комментария без авторизации"""
        data = {
            'article_id': self.article.id,
            'content': 'Новый комментарий'
        }
        response = self.client.post(
            '/api/blog/comments/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_update_comment_success(self):
        """Тест успешного обновления своего комментария"""
        token = self.get_auth_token('user1', 'testpass123')
        self.assertIsNotNone(token)
        
        data = {
            'content': 'Обновленный комментарий'
        }
        response = self.client.put(
            f'/api/blog/comments/{self.comment.id}/',
            json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Обновленный комментарий')

    def test_update_comment_other_user(self):
        """Тест попытки обновить чужой комментарий"""
        token = self.get_auth_token('user2', 'testpass123')
        self.assertIsNotNone(token)
        
        data = {
            'content': 'Взломанный комментарий'
        }
        response = self.client.put(
            f'/api/blog/comments/{self.comment.id}/',
            json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_comment_success(self):
        """Тест успешного удаления своего комментария"""
        token = self.get_auth_token('user1', 'testpass123')
        self.assertIsNotNone(token)
        
        response = self.client.delete(
            f'/api/blog/comments/{self.comment.id}/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_comment_other_user(self):
        """Тест попытки удалить чужой комментарий"""
        token = self.get_auth_token('user2', 'testpass123')
        self.assertIsNotNone(token)
        
        response = self.client.delete(
            f'/api/blog/comments/{self.comment.id}/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Comment.objects.count(), 1)


class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_register_success(self):
        """Тест успешной регистрации"""
        data = {
            'username': 'newuser',
            'password': 'newpass123'
        }
        response = self.client.post(
            '/api/blog/register/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_duplicate_username(self):
        """Тест регистрации с существующим username"""
        data = {
            'username': 'testuser',
            'password': 'newpass123'
        }
        response = self.client.post(
            '/api/blog/register/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_register_missing_fields(self):
        """Тест регистрации без обязательных полей"""
        data = {
            'username': 'newuser'
        }
        response = self.client.post(
            '/api/blog/register/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_jwt_login_success(self):
        """Тест успешного входа через JWT"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(
            '/api/auth/login/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('access', data)

    def test_jwt_login_invalid_credentials(self):
        """Тест входа с неверными данными"""
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = self.client.post(
            '/api/auth/login/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)


class CategoryAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user1', password='testpass123')
        self.category = Category.objects.create(name='Технологии', slug='tech')

    def get_auth_token(self, username, password):
        """Получить JWT токен для авторизации"""
        response = self.client.post(
            '/api/auth/login/',
            json.dumps({'username': username, 'password': password}),
            content_type='application/json'
        )
        if response.status_code == 200:
            return response.json().get('access')
        return None

    def test_list_categories_success(self):
        """Тест успешного получения списка категорий"""
        response = self.client.get('/api/blog/categories/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_create_category_success(self):
        """Тест успешного создания категории"""
        token = self.get_auth_token('user1', 'testpass123')
        self.assertIsNotNone(token)
        
        data = {
            'name': 'Наука',
            'description': 'Категория о науке'
        }
        response = self.client.post(
            '/api/blog/categories/',
            json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.count(), 2)

    def test_create_category_unauthorized(self):
        """Тест создания категории без авторизации"""
        data = {
            'name': 'Наука',
            'description': 'Категория о науке'
        }
        response = self.client.post(
            '/api/blog/categories/',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
