from decimal import Decimal
import json
import hashlib
import hmac

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from .models import Booking, Expense, OwnerProfile, Vehicle


class OwnerProfitTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="owner1",
            password="TestPass123!",
        )
        self.owner = OwnerProfile.objects.create(
            user=self.user,
            business_name="City Rentals",
        )
        self.vehicle = Vehicle.objects.create(
            owner=self.owner,
            category=Vehicle.Category.CAR,
            name="Creta",
            brand="Hyundai",
            model_year=2023,
            registration_number="KA01AB1234",
            rent_per_day=Decimal("1800.00"),
        )

    def test_owner_profit_calculation(self):
        Booking.objects.create(
            customer_name="Asha",
            customer_phone="9999999999",
            owner=self.owner,
            vehicle=self.vehicle,
            start_date="2026-02-01",
            end_date="2026-02-03",
            total_price=Decimal("5400.00"),
            status=Booking.Status.COMPLETED,
        )
        Booking.objects.create(
            customer_name="Rahul",
            customer_phone="8888888888",
            owner=self.owner,
            vehicle=self.vehicle,
            start_date="2026-02-04",
            end_date="2026-02-04",
            total_price=Decimal("1800.00"),
            status=Booking.Status.CANCELLED,
        )
        Expense.objects.create(
            owner=self.owner,
            title="Service",
            amount=Decimal("1200.00"),
        )

        self.assertEqual(self.owner.total_revenue, Decimal("5400.00"))
        self.assertEqual(self.owner.total_expenses, Decimal("1200.00"))
        self.assertEqual(self.owner.total_profit, Decimal("4200.00"))


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    DEBUG=True,
)
class OtpFlowTests(TestCase):
    def test_email_otp_send_and_verify(self):
        send_response = self.client.post(
            reverse("otp_send"),
            data=json.dumps({"purpose": "customer_signup", "channel": "email", "target": "a@example.com"}),
            content_type="application/json",
        )
        self.assertEqual(send_response.status_code, 200)
        send_payload = send_response.json()
        self.assertTrue(send_payload.get("otp_id"))
        self.assertTrue(send_payload.get("debug_otp"))

        verify_response = self.client.post(
            reverse("otp_verify"),
            data=json.dumps({"otp_id": send_payload["otp_id"], "otp_code": str(send_payload["debug_otp"])}),
            content_type="application/json",
        )
        self.assertEqual(verify_response.status_code, 200)
        verify_payload = verify_response.json()
        self.assertTrue(verify_payload.get("verified"))


@override_settings(
    RAZORPAY_KEY_ID="rzp_test_dummy",
    RAZORPAY_KEY_SECRET="dummy_secret",
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    DEBUG=True,
)
class RazorpayVerifyTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="owner2",
            password="TestPass123!",
        )
        self.owner = OwnerProfile.objects.create(
            user=self.user,
            business_name="Test Rentals",
            is_verified=True,
        )
        self.vehicle = Vehicle.objects.create(
            owner=self.owner,
            category=Vehicle.Category.CAR,
            name="Swift",
            brand="Maruti",
            model_year=2023,
            registration_number="KA02AB1234",
            rent_per_day=Decimal("1000.00"),
            is_verified=True,
        )
        self.booking = Booking.objects.create(
            customer_name="Dev",
            customer_phone="9999999999",
            customer_email="dev@example.com",
            customer_address="Addr",
            customer_lpu_id="lpu123",
            customer_license_number="lic123",
            customer_age=22,
            owner=self.owner,
            vehicle=self.vehicle,
            rental_unit=Booking.RentalUnit.DAY,
            start_date="2026-03-01",
            end_date="2026-03-02",
            total_price=Decimal("2000.00"),
            razorpay_order_id="order_test_123",
        )

    def test_verify_marks_booking_paid(self):
        payment_id = "pay_test_456"
        signature = hmac.new(
            b"dummy_secret",
            b"order_test_123|pay_test_456",
            hashlib.sha256,
        ).hexdigest()

        response = self.client.post(
            reverse("razorpay_verify_payment"),
            data=json.dumps(
                {
                    "booking_id": self.booking.id,
                    "razorpay_order_id": "order_test_123",
                    "razorpay_payment_id": payment_id,
                    "razorpay_signature": signature,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, Booking.PaymentStatus.PAID)
        self.assertEqual(self.booking.advance_paid, self.booking.total_price)
