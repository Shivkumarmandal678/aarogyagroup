from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from datetime import datetime

from myapp.views import is_valid_class_date, next_class_date


class DashboardAccessTests(TestCase):
	def setUp(self):
		self.staff = {
			'Username': 'reception',
			'Email': 'reception@example.com',
			'Role': 'Staff',
			'Profile_Image': '',
		}

	@patch('myapp.views.authenticate_user')
	def test_login_redirects_to_role_dashboard(self, authenticate_user):
		authenticate_user.return_value = self.staff

		response = self.client.post('/admin-login/', {
			'username': 'reception',
			'password': 'secret',
		})

		self.assertRedirects(response, '/staff-dashboard/')

	def test_staff_cannot_open_admin_dashboard(self):
		session = self.client.session
		session['admin_user'] = {
			'username': 'reception',
			'role': 'Staff',
		}
		session.save()

		response = self.client.get('/admin-dashboard/')

		self.assertRedirects(response, '/staff-dashboard/')

	def test_user_dashboard_renders(self):
		session = self.client.session
		session['admin_user'] = {
			'username': 'client',
			'role': 'User',
		}
		session.save()

		response = self.client.get('/user-dashboard/')

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'user_dashboard.html')

	@patch('myapp.views.get_all_client_bookings', return_value=[])
	def test_admin_can_open_any_role_dashboard(self, get_bookings):
		session = self.client.session
		session['admin_user'] = {
			'username': 'admin',
			'role': 'Admin',
		}
		session.save()

		response = self.client.get('/doctor-dashboard/')

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'dashboard_base.html')
		get_bookings.assert_called_once()


class SitemapTests(TestCase):
	def test_sitemap_lists_public_pages(self):
		response = self.client.get('/sitemap.xml')
		body = b''.join(response.streaming_content).decode() if hasattr(response, 'streaming_content') else response.content.decode()

		self.assertEqual(response.status_code, 200)
		self.assertIn('/about/', body)
		self.assertIn('/service/', body)
		self.assertIn('/booking/', body)
		self.assertIn('<changefreq>daily</changefreq>', body)
		self.assertIn('<lastmod>', body)


class PerformanceHeaderTests(TestCase):
	def test_public_pages_send_cache_headers(self):
		response = self.client.get('/')

		self.assertEqual(response.status_code, 200)
		self.assertIn('Cache-Control', response.headers)
		self.assertIn('public', response.headers['Cache-Control'])


class BookingFormTests(TestCase):
	def test_next_class_date_obeys_ten_am_cutoff(self):
		before_cutoff = timezone.make_aware(datetime(2026, 9, 1, 9, 59))
		after_cutoff = timezone.make_aware(datetime(2026, 9, 1, 10, 0))

		self.assertEqual(next_class_date(before_cutoff).isoformat(), '2026-09-01')
		self.assertEqual(next_class_date(after_cutoff).isoformat(), '2026-09-03')

	def test_only_next_class_date_is_accepted(self):
		current = timezone.make_aware(datetime(2026, 9, 1, 11, 0))

		self.assertTrue(is_valid_class_date('2026-09-03', current))
		self.assertFalse(is_valid_class_date('2026-09-02', current))

	@patch('myapp.views.save_client_booking', return_value=True)
	def test_booking_submits_requested_fields(self, save_booking):
		response = self.client.post('/booking/', {
			'name': 'Test Client',
			'phone': '9812345678',
			'email': 'client@example.com',
			'passport_number': 'P1234567',
			'address': 'Kathmandu',
			'lot_number': 'LOT-7',
			'service': 'Biometric',
			'date': next_class_date().isoformat(),
			'message': 'Please confirm.',
		})

		self.assertRedirects(response, '/booking/')
		submitted = save_booking.call_args.args[0]
		self.assertEqual(submitted['passport_number'], 'P1234567')
		self.assertEqual(submitted['address'], 'Kathmandu')
		self.assertEqual(submitted['lot_number'], 'LOT-7')
		self.assertEqual(submitted['service'], 'Biometric')

	@patch('myapp.views.save_client_booking')
	def test_demo_submission_is_blocked(self, save_booking):
		response = self.client.post('/booking/', {
			'name': 'Demo Account',
			'phone': '9812345678',
			'email': 'demo@example.com',
			'passport_number': 'P1234567',
			'address': 'Kathmandu',
			'lot_number': 'LOT-7',
			'service': 'Biometric',
			'date': next_class_date().isoformat(),
			'message': 'This is a demo entry.',
		})

		self.assertEqual(response.status_code, 200)
		save_booking.assert_not_called()
		self.assertContains(response, 'Demo or fake', html=False)

	def test_public_pages_are_english_only(self):
		response = self.client.get('/chatbot/')
		self.assertEqual(response.status_code, 200)
		content = response.content.decode('utf-8')
		self.assertNotRegex(content, r'[\u0900-\u097F]')
		self.assertNotIn('कृपया', content)
		self.assertNotIn('तपाईं', content)
		self.assertNotIn('सेवा', content)

