from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Comment, Follow, Group, Post, User


class PostUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='author_user')
        cls.simple_user = User.objects.create_user(username='simple_user')
        cls.follow = Follow.objects.create(
            user=cls.simple_user,
            author=cls.author_user
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.post.author,
            text='Тест коммент'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostUrlTest.simple_user)
        self.author_post = Client()
        self.author_post.force_login(PostUrlTest.author_user)

    def test_valid_urls_guest_200_response(self):
        """ Доступность страниц index, group_list, profile,
        post_detail для неавторизованого пользоваеля."""
        pathnames_to_test = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.author_user.username}/',
            f'/posts/{self.post.id}/',
        )
        for pathname in pathnames_to_test:
            with self.subTest(pathname=pathname):
                response = self.guest_client.get(pathname)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK,
                    f'{pathname} not OK for GUEST')

    def test_valid_create_post_edit_url_guest_redirect(self):
        """ Доступность и редирект из post_create, post_edit, add_comment,
        follow_index, profile_follow, profile_unfollow
        для неавторизованого пользоваеля на login."""
        pathnames_to_test = {
            '/create/':
                '/auth/login/?next=/create/',
            f'/posts/{self.post.id}/edit/':
                f'/auth/login/?next=/posts/{self.post.id}/edit/',
            f'/posts/{self.post.id}/comment/':
                f'/auth/login/?next=/posts/{self.post.id}/comment/',
            '/follow/':
                '/auth/login/?next=/follow/',
            f'/profile/{self.author_user.username}/follow/':
                f'/auth/login/?next=/profile/'
                f'{self.author_user.username}/follow/',
            f'/profile/{self.author_user.username}/unfollow/':
                f'/auth/login/?next=/profile/'
                f'{self.author_user.username}/unfollow/',
        }
        for pathname, redirect in pathnames_to_test.items():
            with self.subTest(pathname=pathname):
                response = self.guest_client.get(pathname, follow=True)
                self.assertRedirects(
                    response, redirect)

    def test_invalid_url_404_response(self):
        """ Несуществующая страница возвращает 404"""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_valid_authorized_user_200_response(self):
        """ post_create, follow_index доступно
        для авторизованного пользователя."""
        pathnames_to_test = (
            '/create/',
            '/follow/',
        )
        for pathname in pathnames_to_test:
            with self.subTest(pathname=pathname):
                response = self.authorized_client.get(pathname)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_valid_authorized_user_redirect(self):
        """ Доступность и редирект из add_comment, profile_follow,
        profile_unfollow для авторизованого пользоваеля."""
        pathnames_to_test = {
            f'/posts/{self.post.id}/comment/':
                f'/posts/{self.post.id}/',
            f'/profile/{self.author_user.username}/follow/':
                f'/profile/{self.author_user.username}/',
            f'/profile/{self.author_user.username}/unfollow/':
                f'/profile/{self.author_user.username}/',
        }
        for pathname, redirect in pathnames_to_test.items():
            with self.subTest(pathname=pathname):
                response = self.authorized_client.get(pathname, follow=True)
                self.assertRedirects(
                    response, redirect)

    def test_valid_post_edit_url_authorized_not_author_redirect(self):
        """post_edit НЕ ДОСТУПЕН для авторизованного НЕАВТОРА,
        редайректит на post_detail."""
        response = self.authorized_client.get(
            f'/posts/{PostUrlTest.post.id}/edit/', follow=True)
        self.assertRedirects(response, (f'/posts/{PostUrlTest.post.id}/'))

    def test_valid_post_edit_url_for_authorized_author_redirect(self):
        """post_edit ДОСТУПЕН для авторизованного АВТОРА."""
        response = self.author_post.get(
            f'/posts/{PostUrlTest.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_use_correct_templates(self):
        """URL-адреса используют соответствующие HTML-шаблоны."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostUrlTest.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostUrlTest.post.author}/': 'posts/profile.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{PostUrlTest.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostUrlTest.post.id}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_post.get(address)
                self.assertTemplateUsed(response, template)
