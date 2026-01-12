# Блог - Backend API

Backend для блога на Django и Django Ninja с PostgreSQL.

## Технологии

- Python 3.12+ (поддерживается Python 3.14)
- Django 6.0+
- Django Ninja 1.5.0+
- Django Ninja Extra 0.30.0+
- Django Ninja JWT 5.4.3+
- PostgreSQL 15
- Docker & Docker Compose
- Structlog для логирования
- Pytest для тестирования

## Функциональность

### 1. Регистрация и аутентификация
- Регистрация пользователей через username и password
- JWT аутентификация через django-ninja-jwt
- Авторизация через Bearer токен в заголовке

### 2. CRUD для статей
- Создание, просмотр, обновление, удаление статей
- Пользователь может редактировать/удалять только свои статьи
- Поиск по статьям
- Фильтрация по категориям

### 3. CRUD для комментариев
- Создание, просмотр, обновление, удаление комментариев
- Пользователь может редактировать/удалять только свои комментарии

### 4. Админ-панель
- Управление пользователями, статьями, комментариями, категориями
- Доступ: `/admin/`

### 5. Логирование
- Логирование ошибок, предупреждений, информационных сообщений
- Логирование входа/выхода пользователя
- Логирование всех CRUD операций
- Используется structlog для структурированного логирования

### 6. Тестирование
- Минимум 2 теста на каждую API ручку
- Используется unittest и pytest-django
- Проверка успешных и неудачных случаев

## Установка и запуск

### Локальная разработка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd blog
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` и сгенерируйте SECRET_KEY:

**Генерация SECRET_KEY:**

```bash
# Способ 1: Используя утилиту проекта
python generate_secret_key.py

# Способ 2: Через Django
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Способ 3: Через Django shell
python manage.py shell
# Затем: from django.core.management.utils import get_random_secret_key
#       print(get_random_secret_key())
```

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=ваш-сгенерированный-ключ-здесь
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_HOST=localhost
DB_NAME=blog_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_PORT=5432
```

**Важно:** Используйте уникальный SECRET_KEY для каждого проекта!

5. Запустите PostgreSQL через Docker Compose:
```bash
docker-compose up -d db
```

6. Выполните миграции:
```bash
python manage.py migrate
```

7. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

8. Запустите сервер:
```bash
python manage.py runserver
```

### Docker

1. Запустите все сервисы:
```bash
docker-compose up -d
```

2. Выполните миграции:
```bash
docker-compose exec web python manage.py migrate
```

3. Создайте суперпользователя:
```bash
docker-compose exec web python manage.py createsuperuser
```

## API Endpoints

### Информация об API

- `GET /` - Информация об API и доступных endpoints (JSON)

### Аутентификация

- `POST /api/auth/login/` - Вход (получение JWT токена)
- `POST /api/auth/refresh/` - Обновление токена
- `POST /api/blog/register/` - Регистрация нового пользователя

### Статьи

- `GET /api/blog/articles/` - Список статей (публичные)
- `GET /api/blog/articles/{id}/` - Получить статью по ID
- `POST /api/blog/articles/` - Создать статью (требуется авторизация)
- `PUT /api/blog/articles/{id}/` - Обновить статью (только автор)
- `DELETE /api/blog/articles/{id}/` - Удалить статью (только автор)

### Комментарии

- `GET /api/blog/articles/{article_id}/comments/` - Список комментариев к статье
- `POST /api/blog/comments/` - Создать комментарий (требуется авторизация)
- `PUT /api/blog/comments/{id}/` - Обновить комментарий (только автор)
- `DELETE /api/blog/comments/{id}/` - Удалить комментарий (только автор)

### Категории

- `GET /api/blog/categories/` - Список категорий
- `POST /api/blog/categories/` - Создать категорию (требуется авторизация)

## Использование API

### Регистрация
```bash
curl -X POST http://localhost:8000/api/blog/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

### Вход
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

### Создание статьи (с токеном)
```bash
curl -X POST http://localhost:8000/api/blog/articles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title": "Моя статья", "content": "Содержание статьи", "published": true}'
```

## Тестирование

Запуск тестов:
```bash
pytest
```

Или с покрытием:
```bash
pytest --cov=blog --cov-report=html
```

Запуск конкретного теста:
```bash
pytest blog/tests.py::ArticleAPITestCase::test_create_article_success
```

## Логирование

Логи сохраняются в:
- Консоль (stdout)
- Файл `blog.log`

Уровни логирования:
- INFO - информационные сообщения
- WARNING - предупреждения
- ERROR - ошибки

Логируются:
- Вход/выход пользователей
- Все CRUD операции
- Ошибки и предупреждения

## Структура проекта

```
blog/
├── blog_project/          # Настройки проекта
│   ├── settings.py        # Конфигурация
│   ├── urls.py            # URL маршруты
│   └── ...
├── blog/                  # Приложение блога
│   ├── models.py          # Модели данных
│   ├── api.py             # API endpoints
│   ├── admin.py           # Админ-панель
│   ├── schemas.py         # Схемы для API
│   ├── utils.py           # Утилиты
│   ├── signals.py         # Сигналы для логирования
│   └── tests.py           # Тесты
├── docker-compose.yml     # Docker Compose конфигурация
├── Dockerfile             # Docker образ
├── requirements.txt       # Зависимости
└── README.md             # Документация
```

## Разработка

### Добавление новых функций

1. Создайте миграции для изменений моделей:
```bash
python manage.py makemigrations
python manage.py migrate
```

2. Добавьте тесты для новой функциональности
3. Обновите документацию

## Лицензия

MIT

