from django.test import TestCase
from http import HTTPStatus


class ViewTestClass(TestCase):
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.assertTemplateUsed(response, ('core/404.html'))

    def test_csrf_failure_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.assertTemplateUsed(response, ('core/404.html'))

    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.assertTemplateUsed(response, ('core/404.html'))
