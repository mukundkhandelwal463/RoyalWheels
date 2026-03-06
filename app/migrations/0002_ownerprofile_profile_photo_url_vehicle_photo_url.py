from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="ownerprofile",
            name="profile_photo_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="photo_url",
            field=models.URLField(blank=True),
        ),
    ]
