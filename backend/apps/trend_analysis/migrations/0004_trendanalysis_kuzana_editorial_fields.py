from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trend_analysis", "0003_trendanalysisfeedback")]

    operations = [
        migrations.AddField(model_name="trendanalysis", name="kuzana_relevance_score", field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name="trendanalysis", name="kuzana_relevance_reason", field=models.TextField(default="")),
        migrations.AddField(model_name="trendanalysis", name="kuzana_theme", field=models.CharField(blank=True, default="", max_length=30)),
        migrations.AddField(model_name="trendanalysis", name="kuzana_geo_relevance", field=models.CharField(blank=True, default="", max_length=20)),
        migrations.AddField(model_name="trendanalysis", name="kuzana_audience", field=models.CharField(blank=True, default="", max_length=100)),
        migrations.AddField(model_name="trendanalysis", name="kuzana_content_format", field=models.CharField(blank=True, default="", max_length=50)),
        migrations.AddField(model_name="trendanalysis", name="kuzana_practical_takeaway", field=models.TextField(default="")),
    ]
