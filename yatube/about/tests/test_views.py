from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_page_tech_page_accessible_by_name(self):
        """URL, генерируемые при помощи имени
        about:author, about:tech доступны."""
        response = self.guest_client.get(reverse('about:author'))
        self.assertEqual(response.status_code, 200)
        response = self.guest_client.get(reverse('about:tech'))
        self.assertEqual(response.status_code, 200)

    def test_author_page_tech_page_uses_correct_template(self):
        """При запросе к about:author применяется шаблон about/author.html.
        При запросе к about:tech применяется шаблон about/tech.html."""
        response = self.guest_client.get(reverse('about:author'))
        self.assertTemplateUsed(response, 'about/author.html')
        response = self.guest_client.get(reverse('about:tech'))
        self.assertTemplateUsed(response, 'about/tech.html')
