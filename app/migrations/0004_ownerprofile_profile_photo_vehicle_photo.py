from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0003_ownerprofile_is_verified_vehicle_is_verified"),
    ]

    operations = [
        migrations.AddField(
            model_name="ownerprofile",
            name="profile_photo",
            field=models.FileField(blank=True, null=True, upload_to="profile_photos/"),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="photo",
            field=models.FileField(blank=True, null=True, upload_to="vehicle_photos/"),
        ),
    ]
