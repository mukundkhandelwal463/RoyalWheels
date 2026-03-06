from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="OwnerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("business_name", models.CharField(max_length=150)),
                ("phone_number", models.CharField(blank=True, max_length=20)),
                ("address", models.TextField(blank=True)),
                ("license_number", models.CharField(blank=True, max_length=50)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="owner_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["business_name"],
            },
        ),
        migrations.CreateModel(
            name="Expense",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=120)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("spent_on", models.DateField(default=django.utils.timezone.localdate)),
                ("notes", models.TextField(blank=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expenses", to="app.ownerprofile")),
            ],
            options={
                "ordering": ["-spent_on", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Vehicle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.CharField(choices=[("car", "Car"), ("bike", "Bike")], max_length=10)),
                ("name", models.CharField(max_length=120)),
                ("brand", models.CharField(max_length=80)),
                ("model_year", models.PositiveIntegerField()),
                ("registration_number", models.CharField(max_length=25, unique=True)),
                ("fuel_type", models.CharField(choices=[("petrol", "Petrol"), ("diesel", "Diesel"), ("electric", "Electric"), ("cng", "CNG"), ("hybrid", "Hybrid")], default="petrol", max_length=10)),
                ("seats", models.PositiveSmallIntegerField(default=2)),
                ("transmission", models.CharField(blank=True, max_length=20)),
                ("rent_per_day", models.DecimalField(decimal_places=2, max_digits=10)),
                ("is_available", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="vehicles", to="app.ownerprofile")),
            ],
            options={
                "ordering": ["category", "brand", "name"],
            },
        ),
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer_name", models.CharField(max_length=120)),
                ("customer_phone", models.CharField(max_length=20)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("total_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("advance_paid", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("confirmed", "Confirmed"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="pending", max_length=15)),
                ("picked_up_at", models.DateTimeField(blank=True, null=True)),
                ("returned_at", models.DateTimeField(blank=True, null=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bookings", to="app.ownerprofile")),
                ("vehicle", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="app.vehicle")),
            ],
            options={
                "ordering": ["-start_date", "-created_at"],
            },
        ),
    ]
