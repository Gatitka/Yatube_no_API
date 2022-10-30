from typing import Any

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Group, Post, User, Follow
from .utils import my_paginator
from django.views.decorators.cache import cache_page

CACHE_TIME: int = 3


@cache_page(CACHE_TIME)
def index(request):
    """ Обработчик для главной страницы."""
    context = {
        'page_obj': my_paginator(
            request,
            Post.objects.select_related('group')
        )
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug: Any):
    """ Обработчик для страницы группы."""
    group = get_object_or_404(Group, slug=slug)
    items_list = group.posts.all()
    page_obj = my_paginator(request, items_list)
    context = {
        'page_obj': page_obj,
        'group': group
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username: str):
    """ Обработчик для страницы профиля автора."""
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    posts_count = author_posts.count()
    page_obj = my_paginator(request, author_posts)
    context = {
        'page_obj': page_obj,
        'author': author,
        'posts_count': posts_count,
    }
    if request.user in User.objects.all() and request.user != author:
        context['following'] = Follow.objects.filter(
            user=request.user,
            author=author).exists()
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id: int):
    """ Обработчик для страницы поста.
    Автор поста может перейти на страницу редакции поста,
    остальные пользователи могут только просматривать пост."""
    post = get_object_or_404(Post, id=post_id)
    posts_count = post.author.posts.count()
    comments = Comment.objects.filter(post_id=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'posts_count': posts_count,
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """ Обработчик для страницы создания поста.
    Авторизованные пользователи через форму могут создать новый пост."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id: int):
    """ Обработчик для страницы редактирования поста.
    Авторизованный пользователь, являющийся автором поста, может править пост.
    is_edit передается в HTML-шаблон, меняя его на редактирование."""
    post = get_object_or_404(Post, id=post_id)
    if request.user.id != post.author_id:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """ Обработчик добавления комментариев на post_detail."""
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = Post.objects.get(id=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    items_list = (
        Post.objects.filter(
            author__following__user=request.user
        )
    )
    page_obj = my_paginator(request, items_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user.username != username and Follow.objects.filter(
        user=request.user,
        author=User.objects.get(username=username)
    ).exists() is False:
        Follow.objects.create(
            user=request.user,
            author=User.objects.get(username=username)
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    cond = Follow.objects.filter(
        user=request.user,
        author=User.objects.get(username=username)
    ).exists()
    if cond is True:
        unfollow = Follow.objects.get(
            user=request.user,
            author=User.objects.get(username=username),
        )
        unfollow.delete()
    return redirect('posts:profile', username=username)
