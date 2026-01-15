from ninja import Router
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, authenticate
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from typing import List
from datetime import timedelta
from .authentication import TokenAuthFromHeaderOrBody
from .models import Article, Comment, Category, UserToken
from .schemas import (
    ArticleSchema, ArticleCreateSchema, ArticleUpdateSchema,
    CommentSchema, CommentCreateSchema, CommentUpdateSchema,
    CategorySchema, CategoryCreateSchema, UserRegisterSchema,
    UserLoginSchema, TokenResponseSchema, ChangePasswordSchema
)
from .utils import generate_slug, log_crud_operation, log_user_action, generate_token
import structlog

logger = structlog.get_logger(__name__)
User = get_user_model()
router = Router()
auth = TokenAuthFromHeaderOrBody()

# Настройки токенов
TOKEN_LENGTH = getattr(settings, 'TOKEN_LENGTH', 256)
TOKEN_LIFETIME_DAYS = getattr(settings, 'TOKEN_LIFETIME_DAYS', 7)


@router.post("/register", response={200: dict, 400: dict}, auth=None)
def register(request, data: UserRegisterSchema):
    """Регистрация пользователя"""
    if User.objects.filter(username=data.username).exists():
        logger.warning("register_failed", reason="username_exists", username=data.username)
        return 400, {"error": "Пользователь с таким username уже существует"}
    
    user = User.objects.create_user(username=data.username, password=data.password)
    log_user_action("register", user)
    logger.info("user_registered", user_id=user.id, username=data.username)
    
    return {"message": "Пользователь успешно зарегистрирован", "user_id": user.id}


@router.post("/login", response={200: TokenResponseSchema, 401: dict}, auth=None)
def login(request, data: UserLoginSchema):
    """Вход пользователя и получение токена длиной 256 символов"""
    # Сначала проверяем существование пользователя
    try:
        user = User.objects.get(username=data.username)
    except User.DoesNotExist:
        logger.warning("login_failed", username=data.username, reason="user_not_found")
        return 401, {"error": "Неверное имя пользователя или пароль"}
    
    if not user.is_active:
        logger.warning("login_failed", username=data.username, reason="inactive")
        return 401, {"error": "Аккаунт пользователя неактивен"}
    
    # Проверяем пароль
    user = authenticate(username=data.username, password=data.password)
    if not user:
        logger.warning("login_failed", username=data.username, reason="invalid_password")
        return 401, {"error": "Неверное имя пользователя или пароль"}
    
    # Генерируем уникальный токен заданной длины
    token = generate_token(TOKEN_LENGTH)
    
    # Проверяем уникальность токена (на случай коллизии)
    while UserToken.objects.filter(token=token).exists():
        token = generate_token(TOKEN_LENGTH)
    
    # Создаем токен с заданным временем жизни
    expires_at = timezone.now() + timedelta(days=TOKEN_LIFETIME_DAYS)
    user_token = UserToken.objects.create(
        user=user,
        token=token,
        expires_at=expires_at
    )
    
    log_user_action("login", user)
    logger.info("user_logged_in", user_id=user.id, username=user.username, token_id=user_token.id)
    
    return {
        "token": token,
        "expires_at": expires_at,
        "user_id": user.id,
        "username": user.username
    }


@router.post("/change-password", response={200: dict, 400: dict, 401: dict}, auth=auth)
def change_password(request, data: ChangePasswordSchema):
    """Смена пароля для авторизованного пользователя"""
    user = request.user
    
    # Проверяем старый пароль
    if not user.check_password(data.old_password):
        logger.warning("change_password_failed", user_id=user.id, reason="invalid_old_password")
        return 401, {"error": "Неверный текущий пароль"}
    
    # Устанавливаем новый пароль
    user.set_password(data.new_password)
    user.save()
    
    log_user_action("change_password", user)
    logger.info("password_changed", user_id=user.id, username=user.username)
    
    return {"message": "Пароль успешно изменен"}


@router.get("/articles", response=List[ArticleSchema], auth=None)
def list_articles(request, search: str = None, category_id: int = None):
    """Список всех статей"""
    articles = Article.objects.filter(published=True).select_related('author', 'category')
    
    if search:
        articles = articles.filter(Q(title__icontains=search) | Q(content__icontains=search))
    
    if category_id:
        articles = articles.filter(category_id=category_id)
    
    result = []
    for article in articles:
        result.append({
            'id': article.id,
            'title': article.title,
            'slug': article.slug,
            'content': article.content,
            'author_id': article.author.id,
            'author_username': article.author.username,
            'category_id': article.category.id if article.category else None,
            'category_name': article.category.name if article.category else None,
            'created_at': article.created_at,
            'updated_at': article.updated_at,
            'published': article.published,
        })
    
    logger.info("articles_listed", count=len(result))
    return result


@router.get("/articles/{article_id}", response=ArticleSchema, auth=None)
def get_article(request, article_id: int):
    """Получить статью по ID"""
    article = get_object_or_404(Article, id=article_id, published=True)
    
    return {
        'id': article.id,
        'title': article.title,
        'slug': article.slug,
        'content': article.content,
        'author_id': article.author.id,
        'author_username': article.author.username,
        'category_id': article.category.id if article.category else None,
        'category_name': article.category.name if article.category else None,
        'created_at': article.created_at,
        'updated_at': article.updated_at,
        'published': article.published,
    }


@router.post("/articles", response=ArticleSchema, auth=auth)
def create_article(request, data: ArticleCreateSchema):
    """Создать статью"""
    user = request.user
    
    slug = data.slug or generate_slug(data.title, Article)
    
    article = Article.objects.create(
        title=data.title,
        slug=slug,
        content=data.content,
        author=user,
        category_id=data.category_id if data.category_id else None,
        published=data.published
    )
    
    log_crud_operation("create", "Article", user, article.id, {"title": article.title})
    logger.info("article_created", article_id=article.id, author_id=user.id)
    
    return {
        'id': article.id,
        'title': article.title,
        'slug': article.slug,
        'content': article.content,
        'author_id': article.author.id,
        'author_username': article.author.username,
        'category_id': article.category.id if article.category else None,
        'category_name': article.category.name if article.category else None,
        'created_at': article.created_at,
        'updated_at': article.updated_at,
        'published': article.published,
    }


@router.put("/articles/{article_id}", response={200: ArticleSchema, 403: dict}, auth=auth)
def update_article(request, article_id: int, data: ArticleUpdateSchema):
    """Обновить статью"""
    user = request.user
    article = get_object_or_404(Article, id=article_id)
    
    if article.author != user:
        logger.warning("article_update_denied", article_id=article_id, user_id=user.id)
        return 403, {"error": "Вы можете редактировать только свои статьи"}
    
    if data.title is not None:
        article.title = data.title
        if data.slug:
            article.slug = generate_slug(data.slug, Article, article)
        else:
            article.slug = generate_slug(data.title, Article, article)
    
    if data.content is not None:
        article.content = data.content
    
    if data.category_id is not None:
        article.category_id = data.category_id
    
    if data.published is not None:
        article.published = data.published
    
    article.save()
    
    log_crud_operation("update", "Article", user, article.id, {"title": article.title})
    logger.info("article_updated", article_id=article.id, author_id=user.id)
    
    return {
        'id': article.id,
        'title': article.title,
        'slug': article.slug,
        'content': article.content,
        'author_id': article.author.id,
        'author_username': article.author.username,
        'category_id': article.category.id if article.category else None,
        'category_name': article.category.name if article.category else None,
        'created_at': article.created_at,
        'updated_at': article.updated_at,
        'published': article.published,
    }


@router.delete("/articles/{article_id}", response={200: dict, 403: dict}, auth=auth)
def delete_article(request, article_id: int):
    """Удалить статью"""
    user = request.user
    article = get_object_or_404(Article, id=article_id)
    
    if article.author != user:
        logger.warning("article_delete_denied", article_id=article_id, user_id=user.id)
        return 403, {"error": "Вы можете удалять только свои статьи"}
    
    article_title = article.title
    article.delete()
    
    log_crud_operation("delete", "Article", user, article_id, {"title": article_title})
    logger.info("article_deleted", article_id=article_id, author_id=user.id)
    
    return {"message": "Статья успешно удалена"}


@router.get("/articles/{article_id}/comments", response=List[CommentSchema], auth=None)
def list_comments(request, article_id: int):
    """Список комментариев к статье"""
    article = get_object_or_404(Article, id=article_id)
    comments = Comment.objects.filter(article=article).select_related('author', 'article')
    
    result = []
    for comment in comments:
        result.append({
            'id': comment.id,
            'article_id': comment.article.id,
            'article_title': comment.article.title,
            'author_id': comment.author.id,
            'author_username': comment.author.username,
            'content': comment.content,
            'created_at': comment.created_at,
            'updated_at': comment.updated_at,
        })
    
    logger.info("comments_listed", article_id=article_id, count=len(result))
    return result


@router.post("/comments", response=CommentSchema, auth=auth)
def create_comment(request, data: CommentCreateSchema):
    """Создать комментарий"""
    user = request.user
    article = get_object_or_404(Article, id=data.article_id)
    
    comment = Comment.objects.create(
        article=article,
        author=user,
        content=data.content
    )
    
    log_crud_operation("create", "Comment", user, comment.id, {"article_id": article.id})
    logger.info("comment_created", comment_id=comment.id, author_id=user.id, article_id=article.id)
    
    return {
        'id': comment.id,
        'article_id': comment.article.id,
        'article_title': comment.article.title,
        'author_id': comment.author.id,
        'author_username': comment.author.username,
        'content': comment.content,
        'created_at': comment.created_at,
        'updated_at': comment.updated_at,
    }


@router.put("/comments/{comment_id}", response={200: CommentSchema, 403: dict}, auth=auth)
def update_comment(request, comment_id: int, data: CommentUpdateSchema):
    """Обновить комментарий"""
    user = request.user
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.author != user:
        logger.warning("comment_update_denied", comment_id=comment_id, user_id=user.id)
        return 403, {"error": "Вы можете редактировать только свои комментарии"}
    
    comment.content = data.content
    comment.save()
    
    log_crud_operation("update", "Comment", user, comment.id, {"article_id": comment.article.id})
    logger.info("comment_updated", comment_id=comment.id, author_id=user.id)
    
    return {
        'id': comment.id,
        'article_id': comment.article.id,
        'article_title': comment.article.title,
        'author_id': comment.author.id,
        'author_username': comment.author.username,
        'content': comment.content,
        'created_at': comment.created_at,
        'updated_at': comment.updated_at,
    }


@router.delete("/comments/{comment_id}", response={200: dict, 403: dict}, auth=auth)
def delete_comment(request, comment_id: int):
    """Удалить комментарий"""
    user = request.user
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.author != user:
        logger.warning("comment_delete_denied", comment_id=comment_id, user_id=user.id)
        return 403, {"error": "Вы можете удалять только свои комментарии"}
    
    comment_id_val = comment.id
    article_id = comment.article.id
    comment.delete()
    
    log_crud_operation("delete", "Comment", user, comment_id_val, {"article_id": article_id})
    logger.info("comment_deleted", comment_id=comment_id_val, author_id=user.id)
    
    return {"message": "Комментарий успешно удален"}


@router.get("/categories", response=List[CategorySchema], auth=None)
def list_categories(request):
    """Список всех категорий"""
    categories = Category.objects.all()
    result = []
    for category in categories:
        result.append({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description,
            'created_at': category.created_at,
        })
    return result


@router.post("/categories", response=CategorySchema, auth=auth)
def create_category(request, data: CategoryCreateSchema):
    """Создать категорию (только для авторизованных пользователей)"""
    user = request.user
    
    slug = data.slug or generate_slug(data.name, Category)
    
    category = Category.objects.create(
        name=data.name,
        slug=slug,
        description=data.description or ""
    )
    
    log_crud_operation("create", "Category", user, category.id, {"name": category.name})
    logger.info("category_created", category_id=category.id, user_id=user.id)
    
    return {
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'description': category.description,
        'created_at': category.created_at,
    }

