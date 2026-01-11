"""
URL configuration for blog_project project.
"""
from django.contrib import admin
from django.urls import path
from ninja_extra import NinjaExtraAPI
from blog.api import router as blog_router
from ninja_jwt.controller import NinjaJWTDefaultController

api = NinjaExtraAPI(title="Blog API", version="1.0.0")
api.register_controllers(NinjaJWTDefaultController)
api.add_router("/blog", blog_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]

