from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0005_vehicleimage"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="customer_address",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="customer_age",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="customer_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="booking",
            name="customer_license_number",
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name="booking",
            name="customer_lpu_id",
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name="booking",
            name="driving_license_doc",
            field=models.FileField(blank=True, null=True, upload_to="booking_docs/licenses/"),
        ),
        migrations.AddField(
            model_name="booking",
            name="student_id_doc",
            field=models.FileField(blank=True, null=True, upload_to="booking_docs/student_ids/"),
        ),
    ]
