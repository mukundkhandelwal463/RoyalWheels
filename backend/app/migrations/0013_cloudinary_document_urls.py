from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0012_customer_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="driving_license_doc_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="student_id_doc_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="customerprofile",
            name="driving_license_doc_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="customerprofile",
            name="student_id_doc_url",
            field=models.URLField(blank=True),
        ),
    ]
