from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trend_analysis", "0004_trendanalysis_kuzana_editorial_fields")]

    operations = [
        migrations.AddField(
            model_name="trendanalysis",
            name="opportunity_headline",
            field=models.CharField(blank=True, default="", max_length=180),
        ),
        migrations.AddField(
            model_name="trendanalysis",
            name="founder_hook",
            field=models.CharField(blank=True, default="", max_length=240),
        ),
        migrations.AddField(
            model_name="trendanalysis",
            name="investor_hook",
            field=models.CharField(blank=True, default="", max_length=240),
        ),
        migrations.AddField(
            model_name="trendanalysis",
            name="creator_hook",
            field=models.CharField(blank=True, default="", max_length=240),
        ),
    ]
