from core.models import CreatedModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

SYMB_NUMB = 15


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return self.title[:SYMB_NUMB]

    class Meta():
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Post(CreatedModel):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True,
        help_text='Можно добавить картинку'
    )

    class Meta():
        ordering = ['-pub_date', ]
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return self.text[:SYMB_NUMB]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )

    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self):
        return self.text[:SYMB_NUMB]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    def __str__(self):
        return f'{self.user} -> {self.author}'
