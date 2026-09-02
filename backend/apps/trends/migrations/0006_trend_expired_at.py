from django.db import migrations, models


def backfill_expired_at(apps, schema_editor):
    Trend = apps.get_model("trends", "Trend")
    Trend.objects.filter(status="expired", expired_at__isnull=True).update(
        expired_at=models.F("last_seen_at")
    )


class Migration(migrations.Migration):
    dependencies = [("trends", "0005_trend_active_dedup_key_alter_trend_dedup_key")]

    operations = [
        migrations.AddField(
            model_name="trend",
            name="expired_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(backfill_expired_at, migrations.RunPython.noop),
    ]
