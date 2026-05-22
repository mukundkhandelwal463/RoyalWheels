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
                "profile_photo": "http://localhost:8000/static/demo_images/mukund_profile_1779476381495.png",
                "vehicles": [
                    ("car", "XUV700", "Mahindra", 2024, "RW-CAR-1001", "diesel", 7, "Automatic", 4200, "http://localhost:8000/static/demo_images/xuv700_1779476133784.png"),
                    ("car", "City", "Honda", 2023, "RW-CAR-1002", "petrol", 5, "Manual", 2800, "http://localhost:8000/static/demo_images/honda_city_1779476148460.png"),
                    ("bike", "Hunter 350", "Royal Enfield", 2023, "RW-BIK-1001", "petrol", 2, "Manual", 1200, "http://localhost:8000/static/demo_images/hunter_350_1779476262818.png"),
                    ("bike", "Duke 250", "KTM", 2024, "RW-BIK-1002", "petrol", 2, "Manual", 1500, "http://localhost:8000/static/demo_images/duke_250_1779476286721.png"),
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
                "profile_photo": "http://localhost:8000/static/demo_images/arjun_profile_1779476397651.png",
                "vehicles": [
                    ("car", "Creta", "Hyundai", 2023, "SX-CAR-2001", "petrol", 5, "Automatic", 3200, "http://localhost:8000/static/demo_images/creta_1779476180113.png"),
                    ("car", "Harrier", "Tata", 2024, "SX-CAR-2002", "diesel", 5, "Automatic", 3900, "http://localhost:8000/static/demo_images/harrier_1779476212707.png"),
                    ("bike", "Pulsar N250", "Bajaj", 2024, "SX-BIK-2001", "petrol", 2, "Manual", 1100, "http://localhost:8000/static/demo_images/pulsar_n250_1779476301905.png"),
                    ("bike", "Apache RTR 200", "TVS", 2023, "SX-BIK-2002", "petrol", 2, "Manual", 1050, "http://localhost:8000/static/demo_images/apache_rtr_200_1779476316308.png"),
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
                "profile_photo": "http://localhost:8000/static/demo_images/karan_profile_1779476536598.png",
                "vehicles": [
                    ("car", "Verna", "Hyundai", 2023, "KG-CAR-3001", "petrol", 5, "Automatic", 3000, "http://localhost:8000/static/demo_images/verna_1779476227933.png"),
                    ("car", "Baleno", "Maruti", 2024, "KG-CAR-3002", "petrol", 5, "Manual", 2300, "http://localhost:8000/static/demo_images/baleno_1779476246195.png"),
                    ("bike", "R15 V4", "Yamaha", 2023, "KG-BIK-3001", "petrol", 2, "Manual", 1300, "http://localhost:8000/static/demo_images/r15_v4_1779476329902.png"),
                    ("bike", "Classic 350", "Royal Enfield", 2024, "KG-BIK-3002", "petrol", 2, "Manual", 1400, "http://localhost:8000/static/demo_images/classic_350_1779476366120.png"),
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

            for category, name, brand, year, reg_no, fuel, seats, transmission, rent, photo_url in partner["vehicles"]:
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

        self.stdout.write(self.style.SUCCESS("Seeded verified partners and vehicles."))
        self.stdout.write("Login IDs and passwords:")
        self.stdout.write("1) royalwheels_admin / Royal@123")
        self.stdout.write("2) speedx_admin / SpeedX@123")
        self.stdout.write("3) kgrentals_admin / KG@12345")
