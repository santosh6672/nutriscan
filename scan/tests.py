from django.test import TestCase, RequestFactory, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import patch, MagicMock
from nutri.models import NutriUser
from .models import ProductScan
from .views import scan_product_ajax, scan_loading_view, process_scan, result
import json
import uuid
import os

class ScanViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = NutriUser.objects.create_user(
            username='testuser',
            password='testpass',
            age=30,
            weight=70,
            height=175,
            bmi=22.9,
            health_conditions='None',
            dietary_preferences='Vegetarian',
            goal='Maintain weight'
        )
        self.session = self.client.session
        self.session['user_id'] = self.user.id
        self.session.save()

    def add_session_to_request(self, request):
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
    def add_messages_to_request(self, request):
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

    @patch('nutri.views.FileSystemStorage.save')
    @patch('nutri.views.ScanForm')
    def test_scan_product_ajax_success(self, mock_form, mock_save):
        mock_form.return_value.is_valid.return_value = True
        mock_form.return_value.cleaned_data = {'image': SimpleUploadedFile('test.jpg', b'content')}
        mock_save.return_value = 'test_image.jpg'

        request = self.factory.post('/scan/ajax/')
        request.session = self.session
        self.add_session_to_request(request)
        
        response = scan_product_ajax(request)
        data = json.loads(response.content)
        
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['filename'], 'test_image.jpg')
        self.assertEqual(request.session['uploaded_filename'], 'test_image.jpg')

    # Add more tests for scan_product_ajax (error cases, invalid form, etc.)

    @patch('nutri.views.barcode_scanner.scan_barcode')
    @patch('nutri.views.product_lookup.fetch_product_data')
    @patch('nutri.views.nutrition.analyze_nutrition')
    def test_process_scan_success(self, mock_analyze, mock_fetch, mock_scan):
        mock_scan.return_value = '123456789'
        mock_fetch.return_value = {'product_name': 'Test Product', 'nutriments': {}}
        mock_analyze.return_value = '{"advisability": "Good", "summary": "Healthy product"}'
        self.session['uploaded_filename'] = 'test_image.jpg'
        self.session.save()

        request = self.factory.get('/process/scan/test_image.jpg/')
        request.session = self.session
        self.add_session_to_request(request)
        
        response = process_scan(request, 'test_image.jpg')
        data = json.loads(response.content)
        
        self.assertEqual(data['status'], 'success')
        self.assertEqual(request.session['latest_scan_results']['product']['product_name'], 'Test Product')
        self.assertEqual(request.session['latest_scan_results']['analysis']['advisability'], 'Good')

    # Add more tests for process_scan (no barcode, no product, etc.)

    @patch('nutri.views.FileSystemStorage.delete')
    def test_result_view_success(self, mock_delete):
        self.session['latest_scan_results'] = {
            'product': {'product_name': 'Test'},
            'analysis': {'summary': 'Good product.'},
            'nutrient_map': 'energy:Energy'
        }
        self.session['uploaded_filename'] = 'test_image.jpg'
        self.session.save()

        request = self.factory.get('/result/')
        request.session = self.session
        self.add_messages_to_request(request)
        
        response = result(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test')
        mock_delete.assert_called_with('test_image.jpg')

    # Add test for result view without scan results