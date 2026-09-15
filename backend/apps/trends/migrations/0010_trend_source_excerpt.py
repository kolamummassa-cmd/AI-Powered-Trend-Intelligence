from django.db import migrations, models
from django.db.models import F


def copy_existing_source_summaries(apps, schema_editor):
    Trend = apps.get_model("trends", "Trend")
    # Until this migration, `summary` held the source text for every new
    # trend. Preserve it before future analysis runs replace summary with the
    # AI overview.
    Trend.objects.filter(source_excerpt="").update(source_excerpt=F("summary"))


class Migration(migrations.Migration):
    dependencies = [
        ("trends", "0009_trend_opportunity_editorial_copy"),
    ]

    operations = [
        migrations.AddField(
            model_name="trend",
            name="source_excerpt",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(copy_existing_source_summaries, migrations.RunPython.noop),
    ]
