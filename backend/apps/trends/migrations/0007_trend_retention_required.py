from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trends", "0006_trend_expired_at")]

    operations = [
        migrations.AddField(
            model_name="trend",
            name="retention_required",
            field=models.BooleanField(default=False),
        ),
    ]
