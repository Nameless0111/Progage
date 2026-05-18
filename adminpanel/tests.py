import csv
import io
import json

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import Category, Course


class AdminExportDataTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='Admin12345',
            role='admin',
        )
        category = Category.objects.create(name='Python')
        Course.objects.create(
            title='Python Basics',
            description='Intro course',
            instructor=self.admin,
            category=category,
            level='beginner',
        )
        self.client.force_login(self.admin)

    def test_json_export_downloads_payload(self):
        response = self.client.get(reverse('adminpanel:export_data', args=['json']))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertIn('attachment; filename="admin_export_', response['Content-Disposition'])

        payload = json.loads(response.content.decode('utf-8'))
        self.assertEqual(payload['stats']['users'], 1)
        self.assertEqual(payload['courses'][0]['title'], 'Python Basics')
        self.assertEqual(payload['users'][0]['username'], 'admin')

    def test_csv_export_downloads_payload(self):
        response = self.client.get(reverse('adminpanel:export_data', args=['csv']))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment; filename="admin_export_', response['Content-Disposition'])

        content = response.content.decode('utf-8-sig')
        rows = list(csv.DictReader(io.StringIO(content)))
        self.assertIn(
            {'section': 'stats', 'key': 'users', 'value': '1'},
            rows,
        )
        self.assertTrue(any(row['section'] == 'course' and row['key'] == 'Python Basics' for row in rows))
