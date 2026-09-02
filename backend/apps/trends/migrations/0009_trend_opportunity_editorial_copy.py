from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trends", "0008_trend_kuzana_editorial_fields")]

    operations = [
        migrations.AddField(
            model_name="trend",
            name="opportunity_headline",
            field=models.CharField(blank=True, default="", max_length=180),
        ),
        migrations.AddField(
            model_name="trend",
            name="founder_hook",
            field=models.CharField(blank=True, default="", max_length=240),
        ),
        migrations.AddField(
            model_name="trend",
            name="investor_hook",
            field=models.CharField(blank=True, default="", max_length=240),
        ),
        migrations.AddField(
            model_name="trend",
            name="creator_hook",
            field=models.CharField(blank=True, default="", max_length=240),
        ),
    ]
