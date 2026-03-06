from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0004_ownerprofile_profile_photo_vehicle_photo"),
    ]

    operations = [
        migrations.CreateModel(
            name="VehicleImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("image", models.FileField(upload_to="vehicle_gallery/")),
                ("caption", models.CharField(blank=True, max_length=120)),
                ("vehicle", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="app.vehicle")),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
