from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trends", "0007_trend_retention_required")]

    operations = [
        migrations.AddField(model_name="trend", name="kuzana_relevance_score", field=models.PositiveSmallIntegerField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name="trend", name="kuzana_relevance_reason", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="trend", name="kuzana_theme", field=models.CharField(blank=True, choices=[("startups", "Startups"), ("funding", "Funding"), ("fintech", "Fintech & money"), ("sales_marketing", "Sales & marketing"), ("side_hustles", "Side hustles"), ("careers", "Careers"), ("technology", "Technology"), ("founder_story", "Founder story"), ("creator_economy", "Creator economy"), ("business_policy", "Business policy"), ("other", "Other")], default="", max_length=30)),
        migrations.AddField(model_name="trend", name="kuzana_geo_relevance", field=models.CharField(blank=True, choices=[("kenya", "Kenya"), ("east_africa", "East Africa"), ("africa", "Africa"), ("global_lesson", "Global lesson"), ("not_relevant", "Not relevant")], default="", max_length=20)),
        migrations.AddField(model_name="trend", name="kuzana_audience", field=models.CharField(blank=True, default="", max_length=100)),
        migrations.AddField(model_name="trend", name="kuzana_content_format", field=models.CharField(blank=True, default="", max_length=50)),
        migrations.AddField(model_name="trend", name="kuzana_practical_takeaway", field=models.TextField(blank=True, default="")),
    ]
