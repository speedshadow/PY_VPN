from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from custompages.models import CustomPage

class DashboardAuthTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='admin', password='adminpass')

    def test_dashboard_login_required(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_dashboard_login_success(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

class CustomPageCRUDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='admin', password='adminpass')
        self.client.login(username='admin', password='adminpass')

    def test_create_custompage(self):
        resp = self.client.post(reverse('custompage_create'), {
            'title': 'About',
            'slug': 'about',
            'content': 'About page content',
            'is_active': True,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(CustomPage.objects.filter(slug='about').exists())

    def test_edit_custompage(self):
        page = CustomPage.objects.create(title='Privacy', slug='privacy', content='...', is_active=True)
        resp = self.client.post(reverse('custompage_edit', args=[page.pk]), {
            'title': 'Privacy Updated',
            'slug': 'privacy',
            'content': 'Updated content',
            'is_active': True,
        })
        self.assertEqual(resp.status_code, 302)
        page.refresh_from_db()
        self.assertEqual(page.title, 'Privacy Updated')

    def test_delete_custompage(self):
        page = CustomPage.objects.create(title='ToDelete', slug='todelete', content='...', is_active=True)
        resp = self.client.post(reverse('custompage_delete', args=[page.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(CustomPage.objects.filter(slug='todelete').exists())
