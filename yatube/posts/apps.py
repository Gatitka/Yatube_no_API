from django.apps import AppConfig


class PostsConfig(AppConfig):
    """Приложение для управления постами."""
    name = 'posts'
    verbose_name: str = "Посты"
