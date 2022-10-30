import shutil
import tempfile
import time

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.utils import POST_NUMB
from posts.views import CACHE_TIME

from ..models import Group, Post, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='author_user')
        cls.simple_user = User.objects.create_user(username='simple_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        paginator_posts_list = []
        for i in range(12):
            new_post = Post(
                author=cls.simple_user,
                text=f'Текст {i}',
                group=cls.group,
            )
            paginator_posts_list.append(new_post)
        Post.objects.bulk_create(paginator_posts_list)
        time.sleep(1)
        post_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='post.gif',
            content=post_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=PostViewsTest.author_user,
            text='Тестовый setUPClass пост',
            group_id=PostViewsTest.group.id,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTest.simple_user)
        self.author_post = Client()
        self.author_post.force_login(PostViewsTest.author_user)
        post_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='post1.gif',
            content=post_gif,
            content_type='image/gif'
        )
        self.post_dlt = Post.objects.create(
            author=PostViewsTest.author_user,
            text='Для удаления setUPClass пост',
            group_id=PostViewsTest.group.id,
            image=uploaded
        )
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}):
                        'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.post.author}):
                        'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}):
                        'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}):
                        'posts/create_post.html',
        }
        time.sleep(CACHE_TIME + 1)
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_post.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def get_response_context_check(self, request_data, compare_to, context):
        """ Вспомогательная функция вычленяет context данные, получаемые
        авторизованным пользователем при запросе к введенному адресу
        url_name с параметром из **kwargs. Так же собирает их в один словарь
        context_objects для дальнейшей проверки методом subTest."""
        response = self.authorized_client.get(request_data)
        context_objects = {
            response.context[context][0].text:
                compare_to.text,
            response.context[context][0].group.slug:
                compare_to.group.slug,
            response.context[context][0].author.id:
                compare_to.author.id,
            response.context[context][0].image:
                compare_to.image,
        }
        for response_name, reverse_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)
        return response

    def test_post_index_page_show_correct_context(self):
        """Шаблон posts/index.html сформирован с правильным контекстом."""
        # time.sleep(CACHE_TIME + 1)
        self.get_response_context_check(
            reverse('posts:index'),
            Post.objects.latest('pub_date'),
            'page_obj',
        )

    def test_group_list_page_show_correct_context(self):
        """Шаблон posts/group_list.html сформирован
        с правильным контекстом."""
        response = self.get_response_context_check(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            Post.objects.filter(group_id=self.group.id).latest('pub_date'),
            'page_obj'
        )
        self.assertEqual(
            response.context['group'].slug, self.group.slug)

    def test_profile_page_show_correct_context(self):
        """Шаблон posts/profile.html сформирован с правильным контекстом."""
        response = self.get_response_context_check(
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author}
            ),
            Post.objects.filter(
                author_id=self.post.author.id).latest('pub_date'),
            'page_obj'
        )
        self.assertEqual(
            response.context['author'], self.post.author)
        self.assertEqual(
            response.context['posts_count'],
            PostViewsTest.author_user.posts.count())

    def test_post_detail_page_show_correct_context(self):
        """Шаблон posts/post_detail.html сформирован
        с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}))
        text = response.context['post'].text
        posts_count = response.context['posts_count']
        self.assertEqual(text, self.post.text)
        self.assertEqual(posts_count,
                         PostViewsTest.author_user.posts.count())

    def test_post_create_page_show_correct_context(self):
        """Шаблон posts/post_create.html сформирован с правильным контекстом
        в post_create. Проверка отображения добавленного объекта на страницах:
        index, group_list, profile.
        Проверка на отсутствие в другой группе будет в test_forms."""
        response_get = self.authorized_client.get(
            reverse('posts:post_create'))
        self.assertIn('form', response_get.context.keys())
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_get.context.get(
                    'form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_created_post_show_in_urls(self):
        """ Проверка, что созданный пост показывается на страницах
        index, group_list, profile."""
        self.authorized_client.post(
            reverse('posts:post_create'),
            data={
                'text': 'Пост создан через create',
                'group': PostViewsTest.group.id
            }
        )
        request_data_list = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username':
                            f'{PostViewsTest.simple_user.username}'}),
        )
        for request_data in request_data_list:
            with self.subTest(request_data=request_data):
                self.get_response_context_check(
                    request_data,
                    Post.objects.latest('pub_date'),
                    'page_obj'
                )

    def test_post_edit_page_show_correct_context(self):
        """Шаблон posts/post_create.html сформирован
        с правильным контекстом в post_edit."""
        response = self.author_post.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}))
        self.assertIn('form', response.context.keys())
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertEqual(response.context['post'], PostViewsTest.post)
        self.assertEqual(response.context['is_edit'], True)

    def test_first_page_contains_ten_records(self):
        """ Проверка паджинатора количество постов на
        первой странице равно 10."""
        request_data_list = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username':
                            self.simple_user.username}),
        )
        time.sleep(CACHE_TIME + 1)
        for request_data in request_data_list:
            with self.subTest(request_data=request_data):
                response = self.authorized_client.get(request_data)
                self.assertEqual(
                    len(response.context['page_obj'].object_list), POST_NUMB)

    def test_second_page_paginator(self):
        """ Проверка паджинатора количество постов на второй странице."""
        request_data_list = {
            reverse('posts:index') + '?page=2': 4,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2': 4,
            reverse('posts:profile',
                    kwargs={'username':
                            self.simple_user.username}) + '?page=2': 2,
        }
        time.sleep(CACHE_TIME + 1)
        for request_data, delay in request_data_list.items():
            with self.subTest(request_data=request_data):
                response = self.authorized_client.get(request_data)
                self.assertEqual(
                    len(response.context['page_obj'].object_list), delay)

    def test_index_cache(self):
        """ Проверка кэширования главной страницы."""
        fst_response = self.authorized_client.get(reverse('posts:index'))
        self.post_dlt.delete()
        snd_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(fst_response.content, snd_response.content)
        cache.clear()
        trd_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(trd_response.content, snd_response.content)

    def test_following_unfollowing(self):
        """Проверка profile_follow, profile_unfollow на корректную подписку,
        отписку авторизованным пользователем."""
        self.assertFalse(
            Follow.objects.filter(
                user=PostViewsTest.simple_user.id,
                author=PostViewsTest.author_user.id
            ).exists()
        )
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author_user}))
        self.assertTrue(
            Follow.objects.filter(
                user=PostViewsTest.simple_user.id,
                author=PostViewsTest.author_user.id
            ).exists()
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author_user}))
        self.assertFalse(
            Follow.objects.filter(
                user=PostViewsTest.simple_user.id,
                author=PostViewsTest.author_user.id
            ).exists()
        )

    def test_new_post_show_in_follow_page_correctly(self):
        """ Проверка follow_index на отображение правильного контекста.
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        Follow.objects.create(
            user=PostViewsTest.simple_user,
            author=PostViewsTest.author_user
        )
        # подписки author_user -> simple_user нет
        self.get_response_context_check(
            reverse('posts:follow_index'),
            Post.objects.filter(author=self.author_user).latest('pub_date'),
            'page_obj',
        )
        response = self.author_post.get(
            reverse('posts:follow_index'))
        self.assertNotIn(
            Post.objects.filter(author=self.author_user).latest('pub_date'),
            response.context['page_obj']
        )
