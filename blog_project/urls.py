"""
URL configuration for blog_project project.
"""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ninja_extra import NinjaExtraAPI
from blog.api import router as blog_router
from ninja_jwt.controller import NinjaJWTDefaultController

api = NinjaExtraAPI(title="Blog API", version="1.0.0")
api.register_controllers(NinjaJWTDefaultController)
api.add_router("/blog", blog_router)


@require_http_methods(["GET"])
def root_view(request):
    """Корневой endpoint с информацией об API"""
    return JsonResponse({
        "message": "Blog API",
        "version": "1.0.0",
        "documentation": "/api/docs",
        "admin": "/admin/",
        "endpoints": {
            "auth": {
                "login": "/api/auth/login/",
                "refresh": "/api/auth/refresh/",
                "register": "/api/blog/register/"
            },
            "articles": {
                "list": "/api/blog/articles/",
                "detail": "/api/blog/articles/{id}/",
                "create": "/api/blog/articles/",
                "update": "/api/blog/articles/{id}/",
                "delete": "/api/blog/articles/{id}/"
            },
            "comments": {
                "list": "/api/blog/articles/{article_id}/comments/",
                "create": "/api/blog/comments/",
                "update": "/api/blog/comments/{id}/",
                "delete": "/api/blog/comments/{id}/"
            },
            "categories": {
                "list": "/api/blog/categories/",
                "create": "/api/blog/categories/"
            }
        }
    })


urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]

