from unittest.mock import patch

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
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
	def test_booking_page_renders_form_fields_without_server_fields(self):
		response = self.client.get('/booking/')

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'booking.html')
		for field in ('name="name"', 'name="phone"', 'name="email"', 'name="address"', 'name="passport_number"', 'name="lot_number"', 'name="service"', 'name="date"', 'name="message"'):
			self.assertContains(response, field, html=False)
		for destination in ('United Arab Emirates (UAE)', 'Saudi Arabia', 'Qatar', 'Kuwait', 'Bahrain', 'Oman', 'Malaysia'):
			self.assertContains(response, destination, html=False)
		self.assertNotContains(response, 'name="timestamp"', html=False)
		self.assertNotContains(response, 'name="status"', html=False)
		self.assertContains(response, 'name="passport_copy"', html=False)
		self.assertContains(response, 'enctype="multipart/form-data"', html=False)

	def test_booking_page_has_cache_header(self):
		response = self.client.get('/booking/')

		self.assertIn('public', response.headers['Cache-Control'])
		self.assertIn('Accept-Encoding', response.headers['Vary'])

	def test_invalid_date_does_not_save_booking(self):
		with patch('myapp.views.save_client_booking') as save_booking:
			response = self.client.post('/booking/', {
				'name': 'Test Client', 'phone': '9812345678', 'email': 'client@example.com',
				'passport_number': 'P1234567', 'address': 'Kathmandu', 'service': 'Medical', 'country': 'Qatar',
				'date': '2099-01-01', 'message': 'Please confirm.',
			})

		self.assertEqual(response.status_code, 200)
		save_booking.assert_not_called()
		self.assertContains(response, 'Please select the next available class date', html=False)

	def test_invalid_country_does_not_save_booking(self):
		with patch('myapp.views.save_client_booking') as save_booking:
			response = self.client.post('/booking/', {
				'name': 'Test Client', 'phone': '9812345678', 'email': 'client@example.com',
				'passport_number': 'P1234567', 'address': 'Kathmandu', 'service': 'Medical',
				'country': 'Unknown Country', 'date': next_class_date().isoformat(), 'message': 'Please confirm.',
			})

		self.assertEqual(response.status_code, 200)
		save_booking.assert_not_called()
		self.assertContains(response, 'Please select a valid destination country', html=False)

	@patch('myapp.views.default_storage.save', return_value='passport_uploads/test.pdf')
	@patch('myapp.views.save_client_booking', return_value=True)
	def test_passport_copy_is_saved_and_forwarded(self, save_booking, save_file):
		passport_copy = SimpleUploadedFile('passport.pdf', b'%PDF-test', content_type='application/pdf')
		response = self.client.post('/booking/', {
			'name': 'Test Client', 'phone': '9812345678', 'email': 'client@example.com',
			'passport_number': 'P1234567', 'address': 'Kathmandu', 'service': 'Medical',
			'country': 'Malaysia', 'date': next_class_date().isoformat(), 'message': 'Please confirm.',
			'passport_copy': passport_copy,
		})

		self.assertRedirects(response, '/booking/')
		save_file.assert_called_once()
		submitted = save_booking.call_args.args[0]
		self.assertEqual(submitted['passport_copy'], 'passport_uploads/test.pdf')

	@patch('myapp.views.default_storage.save')
	@patch('myapp.views.save_client_booking')
	def test_passport_copy_rejects_unsupported_type(self, save_booking, save_file):
		passport_copy = SimpleUploadedFile('passport.txt', b'not a passport', content_type='text/plain')
		response = self.client.post('/booking/', {
			'name': 'Test Client', 'phone': '9812345678', 'email': 'client@example.com',
			'passport_number': 'P1234567', 'address': 'Kathmandu', 'service': 'Medical',
			'country': 'Qatar', 'date': next_class_date().isoformat(), 'message': 'Please confirm.',
			'passport_copy': passport_copy,
		})

		self.assertEqual(response.status_code, 200)
		save_file.assert_not_called()
		save_booking.assert_not_called()
		self.assertContains(response, 'Passport copy must be a JPG, PNG, or PDF file', html=False)

	@patch('myapp.views.save_client_booking', return_value=False)
	def test_failed_sheet_save_still_redirects(self, save_booking):
		response = self.client.post('/booking/', {
			'name': 'Test Client', 'phone': '9812345678', 'email': 'client@example.com',
			'passport_number': 'P1234567', 'address': 'Kathmandu', 'service': 'Medical', 'country': 'Qatar',
			'date': next_class_date().isoformat(), 'message': 'Please confirm.',
		})

		self.assertRedirects(response, '/booking/')
		save_booking.assert_called_once()

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
	def test_booking_submits_required_fields_and_optional_lot(self, save_booking):
		response = self.client.post('/booking/', {
			'name': 'Test Client',
			'phone': '9812345678',
			'email': 'client@example.com',
			'passport_number': 'P1234567',
			'address': 'Kathmandu',
			'lot_number': '',
			'service': 'Biometric',
			'country': 'Malaysia',
			'date': next_class_date().isoformat(),
			'message': 'Please confirm.',
		})

		self.assertRedirects(response, '/booking/')
		submitted = save_booking.call_args.args[0]
		self.assertEqual(submitted['passport_number'], 'P1234567')
		self.assertEqual(submitted['address'], 'Kathmandu')
		self.assertEqual(submitted['lot_number'], '')
		self.assertEqual(submitted['service'], 'Biometric')
		self.assertEqual(submitted['country'], 'Malaysia')

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
			'country': 'Saudi Arabia',
			'date': next_class_date().isoformat(),
			'message': 'This is a demo entry.',
		})

		self.assertEqual(response.status_code, 200)
		save_booking.assert_not_called()
		self.assertContains(response, 'Demo or fake', html=False)

	@patch('myapp.views.save_client_booking')
	def test_requires_all_fields_except_lot(self, save_booking):
		response = self.client.post('/booking/', {
			'name': 'Test Client',
			'phone': '9812345678',
			'email': '',
			'passport_number': 'P1234567',
			'address': 'Kathmandu',
			'lot_number': '',
			'service': 'Biometric',
			'country': 'United Arab Emirates (UAE)',
			'date': next_class_date().isoformat(),
			'message': 'Please confirm.',
		})

		self.assertEqual(response.status_code, 200)
		save_booking.assert_not_called()
		self.assertContains(response, 'Please fill in all required fields', html=False)

	@patch('myapp.google_sheets.post_sheet_action', return_value=True)
	def test_booking_payload_orders_address_before_passport(self, post_sheet_action):
		from myapp.google_sheets import save_client_booking

		save_client_booking({
			'name': 'Shiv Kumar',
			'phone': '9824376881',
			'email': 'shivkumarmandal678@gmail.com',
			'passport_number': 'Bxxb',
			'address': 'Lahan',
			'lot_number': '',
			'service': 'Orientation',
			'country': 'Oman',
			'date': '2026-08-30',
			'message': 'Please process my booking.',
		})

		payload = post_sheet_action.call_args.args[1]
		self.assertEqual(payload['country'], 'Oman')
		self.assertEqual(list(payload.keys()), ['timestamp', 'name', 'phone', 'email', 'address', 'passport_number', 'lot_number', 'service', 'country', 'passport_copy', 'date', 'message', 'status'])

	def test_public_pages_are_english_only(self):
		response = self.client.get('/chatbot/')
		self.assertEqual(response.status_code, 200)
		content = response.content.decode('utf-8')
		self.assertNotRegex(content, r'[\u0900-\u097F]')
		self.assertNotIn('कृपया', content)
		self.assertNotIn('तपाईं', content)
		self.assertNotIn('सेवा', content)

