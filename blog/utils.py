import structlog
from django.utils.text import slugify

logger = structlog.get_logger(__name__)


def generate_slug(text, model_class=None, instance=None):
    """Генерирует уникальный slug из текста"""
    base_slug = slugify(text)
    slug = base_slug
    
    if model_class and instance:
        # Проверяем уникальность, исключая текущий экземпляр
        counter = 1
        while model_class.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
    elif model_class:
        # Проверяем уникальность для нового объекта
        counter = 1
        while model_class.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
    
    return slug


def log_user_action(action, user, details=None):
    """Логирование действий пользователя"""
    logger.info(
        "user_action",
        action=action,
        user_id=user.id if user else None,
        username=user.username if user else None,
        details=details or {}
    )


def log_crud_operation(operation, model_name, user, object_id=None, details=None):
    """Логирование CRUD операций"""
    logger.info(
        "crud_operation",
        operation=operation,
        model=model_name,
        user_id=user.id if user else None,
        username=user.username if user else None,
        object_id=object_id,
        details=details or {}
    )

