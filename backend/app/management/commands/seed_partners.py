from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from app.models import OwnerProfile, Vehicle


class Command(BaseCommand):
    help = "Seed verified partners with demo cars and bikes."

    def handle(self, *args, **options):
        user_model = get_user_model()

        partners = [
            {
                "username": "royalwheels_admin",
                "password": "Royal@123",
                "email": "royalwheels@example.com",
                "owner_name": "Royal Wheels Admin",
                "business_name": "Royal Wheels Rentals",
                "phone": "+91 9000011111",
                "address": "Phagwara, Punjab",
                "license": "GST-RW-1022",
                "profile_photo": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=300",
                "vehicles": [
                    ("car", "XUV700", "Mahindra", 2024, "RW-CAR-1001", "diesel", 7, "Automatic", 4200),
                    ("car", "City", "Honda", 2023, "RW-CAR-1002", "petrol", 5, "Manual", 2800),
                    ("bike", "Hunter 350", "Royal Enfield", 2023, "RW-BIK-1001", "petrol", 2, "Manual", 1200),
                    ("bike", "Duke 250", "KTM", 2024, "RW-BIK-1002", "petrol", 2, "Manual", 1500),
                ],
            },
            {
                "username": "speedx_admin",
                "password": "SpeedX@123",
                "email": "speedx@example.com",
                "owner_name": "SpeedX Owner",
                "business_name": "SpeedX Mobility",
                "phone": "+91 9000022222",
                "address": "Jalandhar, Punjab",
                "license": "GST-SX-2044",
                "profile_photo": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=300",
                "vehicles": [
                    ("car", "Creta", "Hyundai", 2023, "SX-CAR-2001", "petrol", 5, "Automatic", 3200),
                    ("car", "Harrier", "Tata", 2024, "SX-CAR-2002", "diesel", 5, "Automatic", 3900),
                    ("bike", "Pulsar N250", "Bajaj", 2024, "SX-BIK-2001", "petrol", 2, "Manual", 1100),
                    ("bike", "Apache RTR 200", "TVS", 2023, "SX-BIK-2002", "petrol", 2, "Manual", 1050),
                ],
            },
            {
                "username": "kgrentals_admin",
                "password": "KG@12345",
                "email": "kg@example.com",
                "owner_name": "KG Rentals Owner",
                "business_name": "KG Rentals",
                "phone": "+91 9000033333",
                "address": "Law Gate, Phagwara",
                "license": "GST-KG-3099",
                "profile_photo": "https://images.unsplash.com/photo-1483721310020-03333e577078?w=300",
                "vehicles": [
                    ("car", "Verna", "Hyundai", 2023, "KG-CAR-3001", "petrol", 5, "Automatic", 3000),
                    ("car", "Baleno", "Maruti", 2024, "KG-CAR-3002", "petrol", 5, "Manual", 2300),
                    ("bike", "R15 V4", "Yamaha", 2023, "KG-BIK-3001", "petrol", 2, "Manual", 1300),
                    ("bike", "Classic 350", "Royal Enfield", 2024, "KG-BIK-3002", "petrol", 2, "Manual", 1400),
                ],
            },
        ]

        for partner in partners:
            user, _ = user_model.objects.update_or_create(
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

            for category, name, brand, year, reg_no, fuel, seats, transmission, rent in partner["vehicles"]:
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
                        "is_available": True,
                        "is_verified": True,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Seeded verified partners and vehicles."))
        self.stdout.write("Login IDs and passwords:")
        self.stdout.write("1) royalwheels_admin / Royal@123")
        self.stdout.write("2) speedx_admin / SpeedX@123")
        self.stdout.write("3) kgrentals_admin / KG@12345")
