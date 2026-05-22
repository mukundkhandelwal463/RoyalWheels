"""
Seed the database with realistic demo data:
  - Django superuser (admin panel)
  - 3 rental-partner owners with cars & bikes
  - 3 customer profiles
  - 8 bookings across different statuses
  - A few expense records

Usage:
    python manage.py seed_demo          # create demo data
    python manage.py seed_demo --flush  # delete old demo data first, then create
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import Booking, CustomerProfile, Expense, OwnerProfile, Vehicle

User = get_user_model()

# ─────────────────────────────────────────────────────────────
# Static demo data
# ─────────────────────────────────────────────────────────────

SUPERUSER = {
    "username": "admin",
    "email": "admin@royalwheels.com",
    "password": "admin123",
}

PARTNERS = [
    {
        "username": "royalwheels_admin",
        "password": "Royal@123",
        "email": "royalwheels@example.com",
        "owner_name": "Mukund Khandelwal",
        "business_name": "Royal Wheels Rentals",
        "phone": "+91 6376447286",
        "address": "Law Gate, Phagwara, Punjab 144401",
        "license": "GST-RW-1022",
        "profile_photo": "http://localhost:8000/static/demo_images/mukund_profile_1779476381495.png",
        "vehicles": [
            # (category, name, brand, year, reg_no, fuel, seats, transmission, rent, photo_url)
            ("car", "XUV700",     "Mahindra",   2024, "PB-08-AA-1001", "diesel",   7, "Automatic", 4200,
             "http://localhost:8000/static/demo_images/xuv700_1779476133784.png"),
            ("car", "City",       "Honda",      2023, "PB-08-AA-1002", "petrol",   5, "CVT",       2800,
             "http://localhost:8000/static/demo_images/honda_city_1779476148460.png"),
            ("car", "Fortuner",   "Toyota",     2024, "PB-08-AA-1003", "diesel",   7, "Automatic", 6500,
             "http://localhost:8000/static/demo_images/fortuner_1779476164762.png"),
            ("bike", "Hunter 350", "Royal Enfield", 2023, "PB-08-BB-1001", "petrol", 2, "Manual", 1200,
             "http://localhost:8000/static/demo_images/hunter_350_1779476262818.png"),
            ("bike", "Duke 250",   "KTM",        2024, "PB-08-BB-1002", "petrol", 2, "Manual", 1500,
             "http://localhost:8000/static/demo_images/duke_250_1779476286721.png"),
        ],
    },
    {
        "username": "speedx_admin",
        "password": "SpeedX@123",
        "email": "speedx@example.com",
        "owner_name": "Arjun Mehta",
        "business_name": "SpeedX Mobility",
        "phone": "+91 9000022222",
        "address": "Model Town, Jalandhar, Punjab 144001",
        "license": "GST-SX-2044",
        "profile_photo": "http://localhost:8000/static/demo_images/arjun_profile_1779476397651.png",
        "vehicles": [
            ("car", "Creta",    "Hyundai", 2023, "PB-03-CC-2001", "petrol", 5, "Automatic", 3200,
             "http://localhost:8000/static/demo_images/creta_1779476180113.png"),
            ("car", "Harrier",  "Tata",    2024, "PB-03-CC-2002", "diesel", 5, "Automatic", 3900,
             "http://localhost:8000/static/demo_images/harrier_1779476212707.png"),
            ("bike", "Pulsar N250",    "Bajaj", 2024, "PB-03-DD-2001", "petrol", 2, "Manual", 1100,
             "http://localhost:8000/static/demo_images/pulsar_n250_1779476301905.png"),
            ("bike", "Apache RTR 200", "TVS",   2023, "PB-03-DD-2002", "petrol", 2, "Manual", 1050,
             "http://localhost:8000/static/demo_images/apache_rtr_200_1779476316308.png"),
        ],
    },
    {
        "username": "kgrentals_admin",
        "password": "KG@12345",
        "email": "kg@example.com",
        "owner_name": "Karan Gill",
        "business_name": "KG Rentals",
        "phone": "+91 9000033333",
        "address": "Bus Stand Road, Phagwara, Punjab 144401",
        "license": "GST-KG-3099",
        "profile_photo": "http://localhost:8000/static/demo_images/karan_profile_1779476536598.png",
        "vehicles": [
            ("car", "Verna",   "Hyundai",       2023, "PB-08-EE-3001", "petrol", 5, "Automatic", 3000,
             "http://localhost:8000/static/demo_images/verna_1779476227933.png"),
            ("car", "Baleno",  "Maruti Suzuki", 2024, "PB-08-EE-3002", "petrol", 5, "Manual",    2300,
             "http://localhost:8000/static/demo_images/baleno_1779476246195.png"),
            ("bike", "R15 V4",     "Yamaha",        2023, "PB-08-FF-3001", "petrol", 2, "Manual", 1300,
             "http://localhost:8000/static/demo_images/r15_v4_1779476329902.png"),
            ("bike", "Classic 350", "Royal Enfield", 2024, "PB-08-FF-3002", "petrol", 2, "Manual", 1400,
             "http://localhost:8000/static/demo_images/classic_350_1779476366120.png"),
        ],
    },
]

CUSTOMERS = [
    {
        "name": "Rahul Sharma",
        "email": "mukundkhandelwal463@gmail.com",
        "phone": "6376447286",
        "password": "Demo@123",
        "age": 22,
        "address": "Room 305, Boys Hostel, LPU, Phagwara",
        "lpu_id": "12305678",
        "license_number": "RJ-14-2023-0045678",
    },
    {
        "name": "Priya Singh",
        "email": "priya@example.com",
        "phone": "9876543210",
        "password": "Demo@123",
        "age": 21,
        "address": "Room 112, Girls Hostel, LPU, Phagwara",
        "lpu_id": "12409876",
        "license_number": "PB-08-2022-0098765",
    },
    {
        "name": "Amit Verma",
        "email": "amit@example.com",
        "phone": "9988776655",
        "password": "Demo@123",
        "age": 24,
        "address": "Flat 12, Kapurthala Road, Phagwara",
        "lpu_id": "",
        "license_number": "PB-03-2021-0012345",
    },
]


class Command(BaseCommand):
    help = "Seed the database with demo admin, partners, vehicles, customers and bookings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo data before seeding.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        self._create_superuser()
        owners = self._create_partners()
        customers = self._create_customers()
        self._create_bookings(owners, customers)
        self._create_expenses(owners)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  Demo data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("  Django Admin Panel (http://localhost:8000/admin/)"))
        self.stdout.write(f"    Username: {SUPERUSER['username']}")
        self.stdout.write(f"    Password: {SUPERUSER['password']}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("  Rental Partner Logins (admin-login page):"))
        for p in PARTNERS:
            self.stdout.write(f"    {p['business_name']:25s} → {p['username']} / {p['password']}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("  Customer Logins (login page):"))
        for c in CUSTOMERS:
            self.stdout.write(f"    {c['name']:25s} → {c['email']} / {c['password']}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("  Demo OTP Phone: 6376447286 (OTP always 123456 in dev mode)"))
        self.stdout.write("")

    # ────────────────────────────────────────────

    def _flush(self):
        self.stdout.write("Flushing existing demo data...")
        demo_usernames = [p["username"] for p in PARTNERS] + [SUPERUSER["username"]]
        demo_emails = [c["email"] for c in CUSTOMERS]
        Booking.objects.filter(customer_email__in=demo_emails).delete()
        CustomerProfile.objects.filter(email__in=demo_emails).delete()
        for username in demo_usernames:
            try:
                user = User.objects.get(username=username)
                OwnerProfile.objects.filter(user=user).delete()
                user.delete()
            except User.DoesNotExist:
                pass
        self.stdout.write(self.style.SUCCESS("  Flushed."))

    def _create_superuser(self):
        user, created = User.objects.update_or_create(
            username=SUPERUSER["username"],
            defaults={
                "email": SUPERUSER["email"],
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "first_name": "Admin",
                "last_name": "RoyalWheels",
            },
        )
        user.set_password(SUPERUSER["password"])
        user.save(update_fields=["password"])
        self.stdout.write(self.style.SUCCESS(f"  ✓ Superuser '{user.username}' ready"))

    def _create_partners(self):
        owners = []
        for partner in PARTNERS:
            user, _ = User.objects.update_or_create(
                username=partner["username"],
                defaults={
                    "email": partner["email"],
                    "first_name": partner["owner_name"],
                    "is_active": True,
                },
            )
            user.set_password(partner["password"])
            user.save(update_fields=["password"])

            profile, _ = OwnerProfile.objects.update_or_create(
                user=user,
                defaults={
                    "business_name": partner["business_name"],
                    "phone_number": partner["phone"],
                    "address": partner["address"],
                    "license_number": partner["license"],
                    "profile_photo_url": partner["profile_photo"],
                    "is_verified": True,
                },
            )

            for veh in partner["vehicles"]:
                (category, name, brand, year, reg_no, fuel,
                 seats, transmission, rent, photo_url) = veh
                Vehicle.objects.update_or_create(
                    registration_number=reg_no,
                    defaults={
                        "owner": profile,
                        "category": category,
                        "name": name,
                        "brand": brand,
                        "model_year": year,
                        "fuel_type": fuel,
                        "seats": seats,
                        "transmission": transmission,
                        "rent_per_day": rent,
                        "photo_url": photo_url,
                        "is_available": True,
                        "is_verified": True,
                    },
                )

            car_count = sum(1 for v in partner["vehicles"] if v[0] == "car")
            bike_count = sum(1 for v in partner["vehicles"] if v[0] == "bike")
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Partner '{partner['business_name']}' — "
                    f"{car_count} cars, {bike_count} bikes"
                )
            )
            owners.append(profile)
        return owners

    def _create_customers(self):
        customers = []
        for cust in CUSTOMERS:
            profile, _ = CustomerProfile.objects.update_or_create(
                email=cust["email"],
                defaults={
                    "name": cust["name"],
                    "phone": cust["phone"],
                    "password": make_password(cust["password"]),
                    "age": cust["age"],
                    "address": cust["address"],
                    "lpu_id": cust["lpu_id"] or None,
                    "license_number": cust["license_number"],
                },
            )
            self.stdout.write(self.style.SUCCESS(f"  ✓ Customer '{profile.name}' ({profile.email})"))
            customers.append(profile)
        return customers

    def _create_bookings(self, owners, customers):
        today = timezone.localdate()
        vehicles = list(Vehicle.objects.filter(owner__in=owners, is_verified=True))
        if not vehicles:
            self.stdout.write(self.style.WARNING("  ⚠ No vehicles found. Skipping bookings."))
            return

        bookings_data = [
            # customer_idx, status, payment_status, days_offset_start, days_duration, payment_method
            (0, "confirmed", "paid",    -5,  3, "razorpay"),
            (0, "completed", "paid",   -15,  2, "razorpay"),
            (0, "pending",   "pending",  2,  4, "cash"),
            (1, "confirmed", "paid",    -3,  5, "razorpay"),
            (1, "cancelled", "pending", -8,  2, "cash"),
            (1, "pending",   "pending",  1,  3, "cash"),
            (2, "completed", "paid",   -20,  7, "razorpay"),
            (2, "confirmed", "cod",     -1,  3, "cash"),
        ]

        count = 0
        for cust_idx, status, pay_status, start_offset, duration, pay_method in bookings_data:
            cust = customers[cust_idx]
            vehicle = random.choice(vehicles)
            start_date = today + timedelta(days=start_offset)
            end_date = start_date + timedelta(days=duration)
            total_price = vehicle.rent_per_day * Decimal(duration)

            advance = total_price if pay_status == "paid" else Decimal("0.00")

            booking, created = Booking.objects.get_or_create(
                customer_email=cust.email,
                vehicle=vehicle,
                start_date=start_date,
                end_date=end_date,
                defaults={
                    "customer_name": cust.name,
                    "customer_phone": cust.phone,
                    "customer_address": cust.address,
                    "customer_lpu_id": cust.lpu_id or "",
                    "customer_license_number": cust.license_number,
                    "customer_age": cust.age,
                    "owner": vehicle.owner,
                    "rental_unit": "day",
                    "total_price": total_price,
                    "advance_paid": advance,
                    "payment_status": pay_status,
                    "payment_method": pay_method,
                    "status": status,
                },
            )
            if created:
                count += 1
                # Mark completed bookings with return time
                if status == "completed":
                    booking.picked_up_at = timezone.make_aware(
                        timezone.datetime.combine(start_date, timezone.datetime.min.time())
                    ) + timedelta(hours=10)
                    booking.returned_at = timezone.make_aware(
                        timezone.datetime.combine(end_date, timezone.datetime.min.time())
                    ) + timedelta(hours=18)
                    booking.save(update_fields=["picked_up_at", "returned_at"])
                elif status == "confirmed":
                    booking.picked_up_at = timezone.make_aware(
                        timezone.datetime.combine(start_date, timezone.datetime.min.time())
                    ) + timedelta(hours=9)
                    booking.save(update_fields=["picked_up_at"])

        self.stdout.write(self.style.SUCCESS(f"  ✓ Created {count} demo bookings"))

    def _create_expenses(self, owners):
        today = timezone.localdate()
        expenses_data = [
            ("Fuel Restock",        2500,  -3),
            ("Vehicle Servicing",   8500,  -7),
            ("Tyre Replacement",    4200, -12),
            ("Office Rent",        15000, -30),
            ("Insurance Premium",  12000, -20),
        ]
        count = 0
        for owner in owners[:2]:  # Only first two partners get expenses
            for title, amount, days_offset in expenses_data:
                _, created = Expense.objects.get_or_create(
                    owner=owner,
                    title=title,
                    spent_on=today + timedelta(days=days_offset),
                    defaults={"amount": amount, "notes": f"Demo expense for {owner.business_name}"},
                )
                if created:
                    count += 1

        self.stdout.write(self.style.SUCCESS(f"  ✓ Created {count} demo expenses"))
