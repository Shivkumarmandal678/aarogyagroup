from unittest.mock import patch

from django.test import TestCase


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


class BookingFormTests(TestCase):
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
			'date': '2026-09-01',
			'message': 'Please confirm.',
		})

		self.assertRedirects(response, '/booking/')
		submitted = save_booking.call_args.args[0]
		self.assertEqual(submitted['passport_number'], 'P1234567')
		self.assertEqual(submitted['address'], 'Kathmandu')
		self.assertEqual(submitted['lot_number'], 'LOT-7')
		self.assertEqual(submitted['service'], 'Biometric')

