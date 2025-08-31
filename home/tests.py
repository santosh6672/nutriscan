# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse
from django.urls import resolve

class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_view_status_code(self):
        """
        Test that the home view returns a 200 OK status code.
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_view_uses_correct_template(self):
        """
        Test that the home view uses the 'home/home.html' template.
        """
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'home/home.html')

    def test_home_view_url_resolves_to_home_view(self):
        """
        Test that the '/' URL resolves to the home_view.
        """
        from home.views import home_view # Assuming your app is named 'home'
        found = resolve('/')
        self.assertEqual(found.func, home_view)