"""
Кастомная аутентификация для проверки токена в заголовке или теле запроса
"""
from ninja.security import HttpBearer
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import UserToken
import structlog
import json

logger = structlog.get_logger(__name__)
User = get_user_model()


def _get_user_from_token(token):
    """
    Получает пользователя по токену
    """
    if not token:
        return None
        
    try:
        user_token = UserToken.objects.select_related('user').get(
            token=token,
            is_active=True
        )
        
        # Проверка истечения токена
        if user_token.is_expired():
            logger.warning("token_expired", token=token[:20] + "...")
            return None
        
        # Обновляем время последнего использования
        user_token.last_used = timezone.now()
        user_token.save(update_fields=['last_used'])
        
        logger.info("token_authenticated", user_id=user_token.user.id, username=user_token.user.username)
        return user_token.user
        
    except UserToken.DoesNotExist:
        logger.warning("token_not_found", token=token[:20] + "..." if token else None)
        return None
    except Exception as e:
        logger.error("token_auth_error", error=str(e))
        return None


class TokenAuthFromHeaderOrBody(HttpBearer):
    """
    Аутентификация, которая проверяет токен:
    1. В заголовке Authorization: Bearer <token>
    2. В теле запроса в поле 'token' (для POST/PUT/PATCH)
    """
    
    def authenticate(self, request, token):
        """
        Проверяет токен из заголовка Authorization
        """
        user = _get_user_from_token(token)
        if user:
            return user
        
        # Если токен не найден в заголовке, проверяем тело запроса
        return self._check_body_token(request)
    
    def _check_body_token(self, request):
        """
        Проверяет токен в теле запроса
        """
        # Проверяем тело запроса (для POST/PUT/PATCH)
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # Пытаемся получить токен из тела запроса
                if hasattr(request, 'body') and request.body:
                    try:
                        body_data = json.loads(request.body)
                        token = body_data.get('token')
                        if token:
                            user = _get_user_from_token(token)
                            if user:
                                return user
                    except (json.JSONDecodeError, AttributeError, ValueError):
                        pass
            except Exception as e:
                logger.warning("body_token_check_error", error=str(e))
        
        return None


def token_auth(request):
    """
    Функция-аутентификатор для Django Ninja, которая проверяет токен
    в заголовке Authorization или в теле запроса
    """
    # Проверяем заголовок Authorization
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split('Bearer ')[1].strip()
        user = _get_user_from_token(token)
        if user:
            return user
    
    # Проверяем тело запроса (для POST/PUT/PATCH)
    if request.method in ['POST', 'PUT', 'PATCH']:
        try:
            if hasattr(request, 'body') and request.body:
                try:
                    body_data = json.loads(request.body)
                    token = body_data.get('token')
                    if token:
                        user = _get_user_from_token(token)
                        if user:
                            return user
                except (json.JSONDecodeError, AttributeError, ValueError):
                    pass
        except Exception as e:
            logger.warning("body_token_check_error", error=str(e))
    
    return None

