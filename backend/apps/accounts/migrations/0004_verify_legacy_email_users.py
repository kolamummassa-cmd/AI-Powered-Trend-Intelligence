from django.db import migrations


def verify_legacy_email_users(apps, schema_editor):
    """Activate accounts created before verification moved before user creation.

    After the code-first registration release, no unverified User rows are
    created. Therefore, existing unverified email accounts are legacy accounts
    that had already completed the former registration process.
    """

    User = apps.get_model("accounts", "User")
    User.objects.filter(auth_provider="email", is_verified=False).update(
        is_verified=True,
        email_verification_code="",
        email_verification_code_expires_at=None,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_user_email_verification_code_and_more"),
    ]

    operations = [
        migrations.RunPython(verify_legacy_email_users, migrations.RunPython.noop),
    ]
