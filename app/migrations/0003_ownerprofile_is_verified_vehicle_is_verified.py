from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_ownerprofile_profile_photo_url_vehicle_photo_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="ownerprofile",
            name="is_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="is_verified",
            field=models.BooleanField(default=False),
        ),
    ]
