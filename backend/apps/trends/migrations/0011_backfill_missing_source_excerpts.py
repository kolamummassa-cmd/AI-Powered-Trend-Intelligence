from django.db import migrations


def add_source_fallbacks(apps, schema_editor):
    Trend = apps.get_model("trends", "Trend")
    for trend in Trend.objects.filter(source_excerpt="").iterator():
        trend.source_excerpt = (
            f"Source report: {trend.title}. Open the recorded source to read the full article."
        )
        trend.save(update_fields=["source_excerpt"])


class Migration(migrations.Migration):
    dependencies = [
        ("trends", "0010_trend_source_excerpt"),
    ]

    operations = [
        migrations.RunPython(add_source_fallbacks, migrations.RunPython.noop),
    ]
