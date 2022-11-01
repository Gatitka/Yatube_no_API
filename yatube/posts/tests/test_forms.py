import os
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_post = User.objects.create_user(username='author_post')
        cls.simple_user = User.objects.create_user(username='simple_user')
        cls.group_1 = Group.objects.create(
            title='1 Тестовая группа setUpClass',
            slug='test-slug-1',
            description='1 Тестовое описание setUpClass',
        )
        cls.post_1 = Post.objects.create(
            author=cls.author_post,
            text='1 Тестовый setUPClass пост',
            group_id=cls.group_1.id,
        )

        cls.group_2 = Group.objects.create(
            title='2 Тестовая группа setUpClass',
            slug='test-slug-2',
            description='2 Тестовое описание setUpClass',
        )
        cls.post_2 = Post.objects.create(
            author=PostPagesTest.author_post,
            text='2 Тестовый setUpClass пост для редакции'
            # group отсутствует для теста
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(PostPagesTest.simple_user)
        self.auth_author_post = Client()
        self.auth_author_post.force_login(PostPagesTest.author_post)

    def test_post_create_page_form_works(self):
        """ Проверка формы создания поста PostForm в post_create."""
        post_count_old = Post.objects.count()
        post_create_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='post_create.gif',
            content=post_create_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Пост создан через create',
            'group': self.group_1.id,
            'image': uploaded,
        }
        response_post = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response_post,
            reverse(
                'posts:profile',
                kwargs={'username': 'simple_user'}
            )
        )
        self.assertEqual(Post.objects.count(), post_count_old + 1)
        new_post = Post.objects.first()
        self.assertEqual(new_post.text, 'Пост создан через create')
        self.assertEqual(new_post.group_id, self.group_1.id)
        self.assertEqual(new_post.image, 'posts/post_create.gif')

    def test_post_create_page_form_dont_save_guest_posts(self):
        """Проверка, что форма PostForm в post_create не сохраняет посты
        неавторизованных пользователей."""
        post_count_old = Post.objects.count()
        guest_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='guest.gif',
            content=guest_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Пост создан через create',
            'group': self.group_1.id,
            'image': uploaded,
        }
        response_post = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response_post, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), post_count_old)
        self.assertFalse(os.path.isfile('posts/post_create.gif'))

    def test_post_edit_page_form_works(self):
        """ Проверка формы PostForm в post_edit.
        Редактируем post_2 - присваиваем группу group_2."""
        post_count_old = Post.objects.count()
        post_edit_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='post_edit.gif',
            content=post_edit_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group_2.id,
            'text': '2 Тестовый setUpClass пост для редакции',
            'image': uploaded,
        }
        response_post = self.auth_author_post.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post_2.id}
            ),
            data=form_data,
        )
        self.assertRedirects(
            response_post,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post_2.id}
            )
        )
        self.assertEqual(Post.objects.count(), post_count_old)
        post = Post.objects.get(id=self.post_2.id)
        self.assertEqual(post.text, '2 Тестовый setUpClass пост для редакции')
        self.assertEqual(post.group.id, self.group_2.id)
        self.assertEqual(post.image, 'posts/post_edit.gif')

    def test_cant_create_empty_text_field_post(self):
        """ Проверка выпадающих ошибок при заполнении формы."""
        tasks_count = Post.objects.count()
        form_data = {
            'text': '',
            'group': self.group_2.id,
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), tasks_count)
        self.assertFormError(
            response,
            'form',
            'text',
            'Введите текст поста'
        )
        self.assertEqual(response.status_code, 200)

    def test_auth_client_comment_form_works(self):
        """ Проверка формы создания комментария post_detail для авторизованых
        пользователей."""
        post_count_old = Post.objects.count()
        form_data = {
            'text': '1 Тестовый комментарий',
        }
        response_post = self.auth_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post_2.id}
            ),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response_post,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post_2.id}
            )
        )
        self.assertEqual(Post.objects.count(), post_count_old)
        new_comment = response_post.context['comments'][0]
        self.assertEqual(new_comment.text, '1 Тестовый комментарий')
        self.assertEqual(new_comment.post.id, self.post_2.id)
        self.assertEqual(new_comment.author.id, PostPagesTest.simple_user.id)

    def test_post_detail_page_form_dont_save_guest_comments(self):
        """Проверка, что форма CommentForm в post_detail не сохраняет посты
        неавторизованных пользователей."""
        post_count_old = Post.objects.count()
        form_data = {
            'text': 'Новый коммент',
        }
        response_post = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post_2.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response_post,
                             '/auth/login/?next=%2Fposts%2F2%2Fcomment%2F')
        self.assertEqual(Post.objects.count(), post_count_old)
