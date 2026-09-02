from django.db import migrations, models


CURATED_WEIGHTS = {
    "techcrunch-rss": (80, 40),
    "techcrunch-startups-rss": (80, 45),
    "techcrunch-venture-rss": (80, 45),
    "venturebeat-ai-rss": (75, 40),
    "mit-tech-review-rss": (85, 35),
    "hacker-news-frontpage-rss": (55, 35),
    "techcabal-rss": (75, 90),
    "disrupt-africa-rss": (70, 85),
    "rest-of-world-rss": (75, 60),
    "african-business-rss": (70, 80),
}


def apply_curated_weights(apps, schema_editor):
    Platform = apps.get_model("trend_sources", "Platform")
    for slug, (credibility, priority) in CURATED_WEIGHTS.items():
        Platform.objects.filter(slug=slug).update(
            credibility_weight=credibility,
            kuzana_priority_weight=priority,
        )


class Migration(migrations.Migration):
    dependencies = [("trend_sources", "0002_platform_credibility_weight")]

    operations = [
        migrations.AddField(
            model_name="platform",
            name="kuzana_priority_weight",
            field=models.PositiveSmallIntegerField(
                default=50,
                help_text=(
                    "Kuzana editorial priority from 0-100. Higher values make a source's "
                    "evidence more influential when deciding relevance for Kenyan founders."
                ),
            ),
        ),
        migrations.RunPython(apply_curated_weights, migrations.RunPython.noop),
    ]
