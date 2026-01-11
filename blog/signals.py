from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
import structlog

logger = structlog.get_logger(__name__)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Логирование успешного входа пользователя"""
    logger.info(
        "user_logged_in",
        user_id=user.id,
        username=user.username,
        ip_address=get_client_ip(request)
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Логирование выхода пользователя"""
    logger.info(
        "user_logged_out",
        user_id=user.id if user else None,
        username=user.username if user else None,
        ip_address=get_client_ip(request)
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Логирование неудачной попытки входа"""
    logger.warning(
        "user_login_failed",
        username=credentials.get('username'),
        ip_address=get_client_ip(request)
    )


def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

