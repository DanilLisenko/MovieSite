# Generated by Django 5.1.4 on 2025-01-18 12:49

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0003_remove_watchlist_added_at_watchlist_watched_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="watchlist",
            unique_together={("user", "movie")},
        ),
        migrations.AddField(
            model_name="watchlist",
            name="added_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name="watchlist",
            name="watchlist",
        ),
    ]
