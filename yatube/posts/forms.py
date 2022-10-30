from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """ Форма для создания и редактирования постов."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': ("Текст нового поста"),
            'group': ("Группа, к которой будет относиться пост"),
            'image': ("Добавить изображение")
        }
        error_messages = {
            'text': {
                'required': ("Введите текст поста"),
            },
        }


class CommentForm(forms.ModelForm):
    """ Форма для создания и редактирования постов."""
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': ("Текст нового комментария")
        }
        error_messages = {
            'text': {
                'required': ("Введите текст комментария"),
            },
        }
