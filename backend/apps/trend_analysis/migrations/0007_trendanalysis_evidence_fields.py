from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trend_analysis", "0006_trendanalysis_action_summary_and_more")]

    operations = [
        migrations.AddField(
            model_name="trendanalysis",
            name="evidence_score",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="trendanalysis",
            name="evidence_source_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="trendanalysis",
            name="verified_source_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="trendanalysis",
            name="evidence_summary",
            field=models.TextField(default=""),
        ),
    ]
