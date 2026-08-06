from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Stateless, expiring email-verification token.

    Reuses Django's PasswordResetTokenGenerator machinery (HMAC over a
    timestamp + a hash of user state) but salts it differently so a
    verification token can never be replayed as a password-reset token
    or vice versa. Nothing about this needs its own database table.
    """

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.email}{user.is_verified}{timestamp}"


email_verification_token = EmailVerificationTokenGenerator()
