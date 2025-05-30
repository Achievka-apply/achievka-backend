# Generated by Django 5.2.1 on 2025-05-30 11:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("universities", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="scholarship",
            name="university",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="scholarships",
                to="universities.university",
            ),
        ),
    ]
