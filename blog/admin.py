from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Article, Comment, Category, UserToken


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'published', 'created_at', 'updated_at')
    list_filter = ('published', 'category', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'content', 'author', 'category')
        }),
        ('Статус', {
            'fields': ('published',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'author', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username', 'article__title')
    readonly_fields = ('created_at', 'updated_at')


# Расширяем админку пользователей
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # Настройка полей для создания/редактирования пользователя
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email')}),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'is_active'),
        }),
    )


@admin.register(UserToken)
class UserTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_preview', 'created_at', 'expires_at', 'is_active', 'last_used')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('user__username', 'token')
    readonly_fields = ('token', 'created_at', 'last_used')
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'token', 'is_active')
        }),
        ('Даты', {
            'fields': ('created_at', 'expires_at', 'last_used')
        }),
    )
    
    def token_preview(self, obj):
        """Показывает первые 20 символов токена"""
        return obj.token[:20] + "..." if len(obj.token) > 20 else obj.token
    token_preview.short_description = "Токен (превью)"

