# Generated by Django 5.2.1 on 2025-06-14 00:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_newsletter"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="has_subscription",
            field=models.BooleanField(default=False),
        ),
    ]
